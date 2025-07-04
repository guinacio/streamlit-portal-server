import streamlit as st
import pandas as pd
from typing import Dict, List
import os
from datetime import datetime

# Import our custom modules
from database import StreamlitPortalDB
from utils import (
    check_port, check_multiple_ports, check_app_ports_cached, save_uploaded_image, render_app_card,
    get_custom_css, display_user_info, display_stats, filter_apps_by_category,
    get_unique_categories, search_apps, scan_unregistered_ports_cached, display_unregistered_ports,
    get_server_ip
)

# Page configuration
st.set_page_config(
    page_title="Streamlit Portal",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_database():
    return StreamlitPortalDB()

db = init_database()

# Apply custom CSS
st.html(get_custom_css())

def login_page():
    """Display login page"""
    st.html("""
    <div class="login-container">
        <div class="login-header">
            <h2>🚀 Streamlit Portal</h2>
            <p>Please log in to access your applications</p>
        </div>
    </div>
    """)

    cols = st.columns(3)

    with cols[1]:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("🔐 Login", use_container_width=True)
            
        if submit_button:
            if username and password:
                user = db.authenticate_user(username, password)
                if user:
                    # Create portal session and set secure cookie
                    portal_session_token = db.create_portal_session(user['id'])
                    
                    # Store both user info and portal session in session state
                    st.session_state.user = user
                    st.session_state.portal_session_token = portal_session_token
                    
                    # Set simple session cookie (used for session restoration in portal only)
                    st.html(f"""
                    <script>
                        // Set portal session cookie for portal session restoration
                        document.cookie = "portal_session={portal_session_token}; path=/; max-age=86400; SameSite=Lax";
                    </script>
                    """)
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter both username and password")
    
    # Show default credentials
    # st.markdown("""
    # ---
    # **Default Admin Credentials:**
    # - Username: `admin`
    # - Password: `admin123`
    # """)

def admin_panel():
    """Admin panel for managing apps and users"""
    st.html('''
    <div class="admin-section">
        <h1>🔧 Admin Panel</h1>
    </div>
    ''')
    
    tab1, tab2, tab3 = st.tabs(["📱 Manage Apps", "👥 Manage Users", "🔐 Groups & Permissions"])
    
    with tab1:
        manage_apps_tab()
    
    with tab2:
        manage_users_tab()
    
    with tab3:
        manage_permissions_tab()
    
    

def manage_apps_tab():
    """Tab for managing applications"""
    st.subheader("Add/Edit Application")
    
    # Get existing apps for editing
    existing_apps = db.get_all_apps()
    app_options = ["Create New App"] + [f"{app['name']} (Port {app['port']})" for app in existing_apps]
    
    selected_app = st.selectbox("Select Application", app_options)
    
    # Initialize form values
    if selected_app == "Create New App":
        port = 8501
        name = ""
        description = ""
        category = "General"
        image_path = ""
        app_id = None
    else:
        # Parse selected app
        app_info = next((app for app in existing_apps if f"{app['name']} (Port {app['port']})" == selected_app), None)
        if app_info:
            port = app_info['port']
            name = app_info['name']
            description = app_info['description'] or ""
            category = app_info['category'] or "General"
            image_path = app_info['image_path'] or ""
            app_id = app_info['id']
    
    with st.form("app_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            port = st.number_input("Port", min_value=1, max_value=65535, value=port)
            name = st.text_input("App Name", value=name)
            category = st.selectbox("Category", 
                                  ["General", "Analytics", "ML/AI", "Dashboard", "Tools", "Games", "Other"], 
                                  index=["General", "Analytics", "ML/AI", "Dashboard", "Tools", "Games", "Other"].index(category) if category in ["General", "Analytics", "ML/AI", "Dashboard", "Tools", "Games", "Other"] else 0)
        
        with col2:
            description = st.text_area("Description", value=description, height=100)
            uploaded_file = st.file_uploader("App Image", type=['png', 'jpg', 'jpeg'], help="Upload an image for this app")
        
        submitted = st.form_submit_button("💾 Save Application")
        
        if submitted:
            if name and port:
                # Handle image upload
                if uploaded_file:
                    image_path = save_uploaded_image(uploaded_file)
                
                success = db.create_app(
                    port=port,
                    name=name,
                    description=description,
                    image_path=image_path,
                    category=category,
                    created_by=st.session_state.user['id']
                )
                
                if success:
                    st.success(f"Application '{name}' saved successfully!")
                    st.rerun()
                else:
                    st.error("Error saving application. Port might already be in use.")
            else:
                st.error("Please fill in all required fields")
    
    # Display existing apps
    if existing_apps:
        st.subheader("Existing Applications")
        for app in existing_apps:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{app['name']}** (Port {app['port']})")
                if app['description']:
                    st.caption(app['description'][:100] + "..." if len(app['description']) > 100 else app['description'])
            
            with col2:
                status = "🟢 Running" if check_port(app['port']) else "🔴 Offline"
                st.write(status)
            
            with col3:
                st.write(f"Category: {app['category']}")
            
            with col4:
                if st.button(f"🗑️ Delete", key=f"delete_{app['id']}"):
                    if db.delete_app(app['id']):
                        st.success("App deleted successfully!")
                        st.rerun()
    
    # Scan for unregistered apps section
    st.divider()
    st.subheader("🔍 Scan for Unregistered Apps")
    st.write("Check for applications running on unregistered ports (8502-8600)")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🔍 Scan for Unregistered Apps", key="scan_ports"):
            # Clear cache to force fresh scan
            scan_unregistered_ports_cached.clear()
            st.session_state.scanning_complete = True
            st.rerun()
    
    with col2:
        if st.button("🔄 Clear Cache", key="clear_scan_cache"):
            scan_unregistered_ports_cached.clear()
            if 'scanning_complete' in st.session_state:
                del st.session_state.scanning_complete
            st.success("Cache cleared!")
    
    # Display scan results if scan was completed
    if st.session_state.get('scanning_complete', False):
        # Get registered ports
        registered_ports = [app['port'] for app in existing_apps]
        
        # Scan for unregistered ports
        with st.spinner("Scanning ports 8502-8600 for unregistered apps..."):
            unregistered_ports = scan_unregistered_ports_cached(8502, 8600, registered_ports)
        
        # Display results
        display_unregistered_ports(unregistered_ports)
        
        # Add note about cache
        st.info("💡 **Tip:** Results are cached for 1 minute. Use 'Clear Cache' to force a fresh scan.")

def manage_users_tab():
    """Tab for managing users"""
    st.subheader("Add/Edit User")
    
    # Get existing users for editing
    existing_users = db.get_all_users()
    user_options = ["Create New User"] + [f"{user['username']} ({user['full_name'] or 'No Name'})" for user in existing_users]
    
    selected_user = st.selectbox("Select User", user_options)
    
    # Initialize form values
    if selected_user == "Create New User":
        username = ""
        full_name = ""
        email = ""
        password = ""
        role = "user"
        groups = ""
        user_id = None
        is_editing = False
    else:
        # Parse selected user
        user_info = next((user for user in existing_users 
                         if f"{user['username']} ({user['full_name'] or 'No Name'})" == selected_user), None)
        if user_info:
            username = user_info['username']
            full_name = user_info['full_name'] or ""
            email = user_info['email'] or ""
            password = ""  # Don't show existing password
            role = user_info['role']
            user_groups = db.get_user_groups(user_info['id'])
            groups = ', '.join(user_groups)
            user_id = user_info['id']
            is_editing = True
    
    with st.form("user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", value=username, disabled=is_editing)
            full_name = st.text_input("Full Name", value=full_name)
            email = st.text_input("Email", value=email)
        
        with col2:
            if is_editing:
                password = st.text_input("New Password (leave empty to keep current)", type="password", value="")
                st.caption("Leave password empty to keep the current password")
            else:
                password = st.text_input("Password", type="password", value=password)
            role = st.selectbox("Role", ["user", "admin"], index=0 if role == "user" else 1)
            groups = st.text_input("Groups (comma-separated)", value=groups, 
                                 help="e.g., developers, analysts, managers")
        
        # Submit button text changes based on mode
        submit_text = "💾 Update User" if is_editing else "👤 Create User"
        submitted = st.form_submit_button(submit_text, use_container_width=True)
        
        if submitted:
            if is_editing:
                # Update existing user
                if full_name or email or role or password or groups:
                    # Update user basic info
                    update_success = True
                    if password:  # Only update password if provided
                        update_success = db.update_user(user_id, username=None, password=password, 
                                                       full_name=full_name, email=email, role=role)
                    else:
                        update_success = db.update_user(user_id, username=None, password=None, 
                                                       full_name=full_name, email=email, role=role)
                    
                    # Update groups
                    if update_success and groups is not None:
                        group_list = [g.strip() for g in groups.split(',') if g.strip()]
                        db.set_user_groups(user_id, group_list)
                    
                    if update_success:
                        st.success(f"User '{username}' updated successfully!")
                        st.rerun()
                    else:
                        st.error("Error updating user.")
                else:
                    st.error("Please fill in at least one field to update")
            else:
                # Create new user
                if username and password:
                    success = db.create_user(username, password, full_name, email, role)
                    if success:
                        # Add user to groups
                        user = db.get_user_by_username(username)
                        if user and groups:
                            group_list = [g.strip() for g in groups.split(',') if g.strip()]
                            for group in group_list:
                                db.add_user_to_group(user['id'], group)
                        
                        st.success(f"User '{username}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Error creating user. Username might already exist.")
                else:
                    st.error("Please fill in username and password")
    
    # Display existing users with edit/delete options
    if existing_users:
        st.divider()
        st.subheader("Existing Users")
        
        for user in existing_users:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{user['username']}** ({user['full_name'] or 'No Name'})")
                    if user['email']:
                        st.caption(f"📧 {user['email']}")
                
                with col2:
                    st.write(f"Role: **{user['role'].title()}**")
                    user_groups = db.get_user_groups(user['id'])
                    if user_groups:
                        st.caption(f"Groups: {', '.join(user_groups)}")
                    else:
                        st.caption("No groups assigned")
                
                with col3:
                    status = "🟢 Active" if user['is_active'] else "🔴 Inactive"
                    st.write(status)
                    if user['last_login']:
                        last_login = pd.to_datetime(user['last_login']).strftime('%Y-%m-%d %H:%M')
                        st.caption(f"Last login: {last_login}")
                    else:
                        st.caption("Never logged in")
                
                with col4:
                    # Prevent deleting the admin user or current user
                    can_delete = (user['username'] != 'admin' and 
                                user['id'] != st.session_state.user['id'])
                    
                    if can_delete:
                        if st.button(f"🗑️", key=f"delete_user_{user['id']}", 
                                   help="Delete user", use_container_width=True):
                            if db.delete_user(user['id']):
                                st.success(f"User '{user['username']}' deleted successfully!")
                                st.rerun()
                            else:
                                st.error("Error deleting user")
                    else:
                        st.button(f"🔒", key=f"protected_user_{user['id']}", 
                                disabled=True, help="Protected user", use_container_width=True)
                
                st.divider()

def manage_permissions_tab():
    """Tab for managing group permissions"""
    st.subheader("App Permissions")
    
    apps = db.get_all_apps()
    all_groups = db.get_all_groups()
    
    if not apps:
        st.info("No apps configured yet. Please add some apps first.")
        return
    
    selected_app = st.selectbox("Select App", [f"{app['name']} (Port {app['port']})" for app in apps])
    
    if selected_app:
        app_info = next((app for app in apps if f"{app['name']} (Port {app['port']})" == selected_app), None)
        
        if app_info:
            # Get current permissions
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT group_name FROM app_permissions WHERE app_id = ?', (app_info['id'],))
            current_groups = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            st.write(f"Configure access permissions for **{app_info['name']}**")
            
            # Add special "Public" option to groups list
            available_groups = ["🌐 Public (All Users)"] + all_groups
            
            # Map current groups to include Public option if present
            display_current_groups = []
            has_public_access = "__public__" in current_groups
            
            if has_public_access:
                display_current_groups.append("🌐 Public (All Users)")
            
            # Add other groups (excluding the special __public__ marker)
            display_current_groups.extend([g for g in current_groups if g != "__public__"])
            
            # Multi-select for groups
            selected_groups = st.multiselect(
                "Select groups that can access this app:",
                options=available_groups,
                default=display_current_groups,
                help="🌐 Public (All Users) = Anyone can access this app, regardless of group membership"
            )
            
            # Show current access level
            if "🌐 Public (All Users)" in selected_groups:
                st.success("🌐 **Public Access**: This app is accessible to ALL users")
            elif selected_groups:
                group_names = [g for g in selected_groups if g != "🌐 Public (All Users)"]
                if group_names:
                    st.info(f"🔒 **Group Access**: Only users in groups: {', '.join(group_names)}")
            else:
                st.warning("⚠️ **No Access**: This app is not accessible to any users")
            
            if st.button("💾 Update Permissions"):
                # Convert display groups back to database groups
                db_groups = []
                
                if "🌐 Public (All Users)" in selected_groups:
                    db_groups.append("__public__")
                
                # Add regular groups (excluding Public option)
                regular_groups = [g for g in selected_groups if g != "🌐 Public (All Users)"]
                db_groups.extend(regular_groups)
                
                success = db.set_app_permissions(app_info['id'], db_groups)
                if success:
                    if "__public__" in db_groups:
                        st.success("✅ Permissions updated! App is now **publicly accessible** to all users.")
                    else:
                        st.success("✅ Permissions updated successfully!")
                    st.rerun()
                else:
                    st.error("Error updating permissions")
            
            # Show helpful information
            if not all_groups:
                st.info("💡 **Tip**: Create users with groups first to enable group-based permissions, or use Public access for apps everyone should access.")

def main_dashboard():
    """Main dashboard for users"""
    # Header
    st.html("""
    <div class="main-header">
        <h1>🚀 Streamlit Portal</h1>
        <p>Your gateway to all Streamlit applications</p>
    </div>
    """)
    
    # Get user's accessible apps first
    accessible_apps = db.get_accessible_apps(st.session_state.user['id'])
    
    # Only check ports for apps this user can access (much faster!)
    app_ports = [app['port'] for app in accessible_apps]
    
    if app_ports:
        # Use cached port checking - only check relevant ports
        port_status = check_app_ports_cached(app_ports)
        
        # Add running status to apps
        for app in accessible_apps:
            app['is_running'] = port_status.get(app['port'], False)
        
        # Show cache info
        st.html("""
        <div class="refresh-info">
            ℹ️ Port status is cached for 30 seconds for better performance. 
            Refresh the page to check again.
        </div>
        """)
    else:
        # No apps to check
        for app in accessible_apps:
            app['is_running'] = False
    
    # Statistics
    total_users = len(db.get_all_users()) if st.session_state.user['role'] == 'admin' else None
    display_stats(len(accessible_apps), len([app for app in accessible_apps if app['is_running']]), total_users)
    
    # Refresh button for cache control
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Refresh Status"):
            check_app_ports_cached.clear()
            st.rerun()
    
    with col1:
        search_term = st.text_input("🔍 Search apps...", placeholder="Search by name, description, or category")
    
    with col2:
        categories = ["All"] + get_unique_categories(accessible_apps)
        selected_category = st.selectbox("Filter by Category", categories)
    
    # Filter apps
    filtered_apps = search_apps(accessible_apps, search_term)
    filtered_apps = filter_apps_by_category(filtered_apps, selected_category)
    
    # Display apps
    if filtered_apps:
        # Create grid of app cards
        cols = st.columns(3)
        server_ip = get_server_ip()
        for i, app in enumerate(filtered_apps):
            with cols[i % 3]:
                card_html = render_app_card(app, app['is_running'], db, server_ip=server_ip, user_id=st.session_state.user['id'])
                st.html(card_html)
    else:
        if search_term or selected_category != "All":
            st.html("""
            <div class="no-apps">
                <div class="no-apps-icon">🔍</div>
                <h3>No apps found</h3>
                <p>Try adjusting your search criteria</p>
            </div>
            """)
        else:
            st.html("""
            <div class="no-apps">
                <div class="no-apps-icon">📱</div>
                <h3>No apps available</h3>
                <p>Contact your administrator to get access to applications</p>
            </div>
            """)

def main():
    """Main application logic"""
    # Check for existing portal session if not logged in
    if 'user' not in st.session_state:
        # Try to restore session from cookie for portal session restoration
        st.html("""
        <script>
            // Function to get cookie value
            function getCookie(name) {
                let value = "; " + document.cookie;
                let parts = value.split("; " + name + "=");
                if (parts.length == 2) return parts.pop().split(";").shift();
                return null;
            }
            
            // Check for portal session cookie and set in session storage for Streamlit
            const portalSession = getCookie("portal_session");
            if (portalSession) {
                sessionStorage.setItem("portal_session_restore", portalSession);
            }
        </script>
        """)
        
        # Try to restore from session storage (set by JavaScript above)
        # Note: This is a simplified approach - in production you might want to use a more robust method
        portal_session_from_storage = st.session_state.get('portal_session_restore')
        
        if portal_session_from_storage:
            # Validate the portal session
            user_info = db.validate_portal_session(portal_session_from_storage)
            if user_info:
                # Restore user session
                st.session_state.user = {
                    'id': user_info['id'],
                    'username': user_info['username'],
                    'full_name': user_info['full_name'],
                    'email': user_info['email'],
                    'role': user_info['role']
                }
                st.session_state.portal_session_token = portal_session_from_storage
                st.rerun()
    
    # Check if user is logged in
    if 'user' not in st.session_state:
        login_page()
        return
    
    # Display user info in sidebar
    display_user_info(st.session_state.user)
    
    # Navigation
    if st.session_state.user['role'] == 'admin':
        page = st.sidebar.selectbox("Navigation", ["🏠 Dashboard", "🔧 Admin Panel"])
        
        if page == "🏠 Dashboard":
            main_dashboard()
        else:
            admin_panel()
    else:
        main_dashboard()

if __name__ == "__main__":
    main() 