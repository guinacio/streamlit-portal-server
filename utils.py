import requests
import os
import hashlib
from PIL import Image
import streamlit as st
from typing import List, Dict, Optional
import base64
from io import BytesIO
import time
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_port(port: int, timeout: float = 1.0) -> bool:
    """Check if a port is running a web service"""
    try:
        url = f"http://localhost:{port}"
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout, requests.RequestException):
        return False

def check_multiple_ports(ports: List[int]) -> Dict[int, bool]:
    """Check multiple ports and return their status"""
    return {port: check_port(port) for port in ports}

@st.cache_data(ttl=30)  # Cache for 30 seconds
def check_app_ports_cached(ports: List[int]) -> Dict[int, bool]:
    """Check multiple ports with caching - cached for 30 seconds"""
    if not ports:
        return {}
    
    # Only check unique ports
    unique_ports = list(set(ports))
    results = {}
    
    for port in unique_ports:
        results[port] = check_port(port, timeout=0.5)  # Faster timeout
    
    return results

def save_uploaded_image(uploaded_file, upload_dir: str = "app_images") -> Optional[str]:
    """Save uploaded image and return the file path"""
    if uploaded_file is None:
        return None
        
    # Create upload directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    file_extension = uploaded_file.name.split('.')[-1]
    file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
    filename = f"{file_hash}.{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    try:
        # Resize and save image
        image = Image.open(uploaded_file)
        # Resize to reasonable dimensions while maintaining aspect ratio
        image.thumbnail((400, 300), Image.Resampling.LANCZOS)
        image.save(file_path, optimize=True, quality=85)
        return file_path
    except Exception as e:
        st.error(f"Error saving image: {e}")
        return None

def get_image_base64(image_path: str) -> Optional[str]:
    """Convert image to base64 for embedding in HTML"""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            return encoded_string
    except Exception:
        return None

def is_app_public(app_id: int, db) -> bool:
    """Check if an app has public access (accessible to all users)"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM app_permissions WHERE app_id = ? AND group_name = "__public__"', (app_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception:
        return False

def render_app_card(app_info: Dict, is_running: bool, db=None, server_ip: str = None, user_id: int = None) -> str:
    """Render an app card with secure access links"""
    status_color = "#28a745" if is_running else "#dc3545"
    status_text = "Running" if is_running else "Offline"
    status_icon = "🟢" if is_running else "🔴"
    
    # Check if app has public access
    public_indicator = ""
    if db and is_app_public(app_info['id'], db):
        public_indicator = '''
            <span class="public-indicator" title="Public Access - Available to all users">
                🌐 Public
            </span>
        '''
    
    # Handle image
    image_html = ""
    if app_info.get('image_path') and os.path.exists(app_info['image_path']):
        image_b64 = get_image_base64(app_info['image_path'])
        if image_b64:
            image_html = f'''
                <div class="app-image">
                    <img src="data:image/png;base64,{image_b64}" alt="{app_info['name']}" />
                </div>
            '''
    else:
        # Default placeholder
        image_html = '''
            <div class="app-image-placeholder">
                <div class="placeholder-icon">📱</div>
            </div>
        '''
    
    launch_button = ""
    if is_running and user_id:
        # Get portal session token from Streamlit session state
        portal_session_token = st.session_state.get('portal_session_token')
        
        if portal_session_token:
            try:
                # Generate secure access token tied to portal session (1-hour expiration)
                access_token = db.generate_access_token_with_session(user_id, app_info['id'], portal_session_token, hours=1)
                ip = server_ip or get_server_ip()
                
                # SECURITY: Use hidden form field for auth_token (form action strips query params)
                base_url = f"http://{ip}:8000/app/{app_info['id']}/"
                
                # Use hidden form field to pass auth_token (prevents URL stripping issue)
                launch_button = f'''
                    <div class="launch-btn-container">
                        <form action="{base_url}" method="get" target="_blank" onsubmit="setTimeout(function(){{window.location.reload();}}, 500);">
                            <input type="hidden" name="auth_token" value="{access_token}">
                            <button type="submit" class="launch-btn-form">
                                🚀 Launch App
                            </button>
                        </form>
                    </div>
                '''
                
            except ValueError as e:
                # Portal session invalid - user needs to log in again
                launch_button = '''
                    <div class="launch-btn-disabled" title="Please refresh the page and log in again">
                        🔒 Session Expired
                    </div>
                '''
        else:
            # No portal session - shouldn't happen but handle gracefully
            launch_button = '''
                <div class="launch-btn-disabled" title="Please refresh the page and log in again">
                    🔒 Login Required
                </div>
            '''
    
    description = app_info.get('description', 'No description available')
    if len(description) > 120:
        description = description[:120] + "..."
    
    # Remove port display from card to prevent guessing
    card_html = f'''
        <div class="app-card">
            {image_html}
            <div class="app-content">
                <div class="app-header">
                    <h3 class="app-title">{app_info['name']}</h3>
                    <div class="app-indicators">
                        {public_indicator}
                        <span class="app-status" style="color: {status_color}">
                            {status_icon} {status_text}
                        </span>
                    </div>
                </div>
                <div class="app-info">
                    <p class="app-description">{description}</p>
                    <div class="app-details">
                        <span class="app-category">{app_info.get('category', 'General')}</span>
                    </div>
                </div>
                {launch_button}
            </div>
        </div>
    '''
    return card_html

def get_custom_css() -> str:
    """Return custom CSS for the portal"""
    return """
    <style>
    .main-header {
        background: #2c3e50;
        padding: 2rem;
        border-radius: 4px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stats-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        flex: 1;
        min-width: 200px;
        text-align: center;
        border-left: 4px solid #34495e;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 0;
    }
    
    .stat-label {
        color: #7f8c8d;
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
    }
    
    .apps-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
        gap: 1.5rem;
        margin-top: 2rem;
    }
    
    .app-card {
        background: white;
        border-radius: 6px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        overflow: hidden;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid #ecf0f1;
    }
    
    .app-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    }
    
    .app-image {
        height: 150px;
        overflow: hidden;
        background: #f8f9fa;
    }
    
    .app-image img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .app-image-placeholder {
        height: 150px;
        background: #ecf0f1;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #95a5a6;
    }
    
    .placeholder-icon {
        font-size: 3rem;
        opacity: 0.7;
    }
    
    .app-content {
        padding: 1.5rem;
    }
    
    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1rem;
    }
    
    .app-title {
        margin: 0;
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        flex: 1;
    }
    
    .app-indicators {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.25rem;
        margin-left: 1rem;
    }
    
    .app-status {
        font-size: 0.85rem;
        font-weight: 500;
        white-space: nowrap;
    }
    
    .public-indicator {
        background: #e8f5e8;
        color: #2d5a2d;
        padding: 0.2rem 0.5rem;
        border-radius: 3px;
        font-size: 0.75rem;
        font-weight: 500;
        border: 1px solid #c3e6c3;
        white-space: nowrap;
    }
    
    .app-description {
        color: #7f8c8d;
        font-size: 0.9rem;
        line-height: 1.4;
        margin: 0 0 1rem 0;
    }
    
    .app-details {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .app-port {
        background: #ecf0f1;
        color: #34495e;
        padding: 0.25rem 0.75rem;
        border-radius: 3px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .app-category {
        background: #e8f4f8;
        color: #2980b9;
        padding: 0.25rem 0.75rem;
        border-radius: 3px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .launch-btn {
        display: inline-block;
        background: #27ae60;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 4px;
        text-decoration: none;
        font-weight: 500;
        text-align: center;
        transition: all 0.3s ease;
        width: 100%;
        box-sizing: border-box;
    }
    
    .launch-btn:hover {
        background: #219a52;
        transform: translateY(-1px);
        box-shadow: 0 3px 10px rgba(39, 174, 96, 0.3);
    }
    
    .launch-btn-form {
        display: inline-block;
        background: #27ae60;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 4px;
        border: none;
        font-weight: 500;
        text-align: center;
        transition: all 0.3s ease;
        width: 100%;
        box-sizing: border-box;
        cursor: pointer;
        font-family: inherit;
        font-size: inherit;
    }
    
    .launch-btn-form:hover {
        background: #219a52;
        transform: translateY(-1px);
        box-shadow: 0 3px 10px rgba(39, 174, 96, 0.3);
    }
    
    .launch-btn-container {
        width: 100%;
    }
    
    .launch-btn-disabled {
        display: inline-block;
        background: #e0e0e0;
        color: #757575;
        padding: 0.75rem 1.5rem;
        border-radius: 4px;
        text-decoration: none;
        font-weight: 500;
        text-align: center;
        transition: all 0.3s ease;
        width: 100%;
        box-sizing: border-box;
        cursor: not-allowed;
        opacity: 0.7;
    }
    
    .user-info {
        background: white;
        padding: 1rem;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    .user-info h4 {
        margin: 0 0 0.5rem 0;
        color: #2c3e50;
    }
    
    .user-role {
        background: #34495e;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 3px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
    }
    
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 6px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-header h2 {
        color: #2c3e50;
        margin: 0;
    }
    
    .admin-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 4px;
        margin: 1rem 0;
        border-left: 4px solid #e74c3c;
    }
    
    .admin-section h3 {
        color: #e74c3c;
        margin-top: 0;
    }
    
    .search-container {
        margin-bottom: 2rem;
    }
    
    .category-filter {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    
    .category-btn {
        padding: 0.5rem 1rem;
        border: 2px solid #34495e;
        background: white;
        color: #34495e;
        border-radius: 3px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 0.9rem;
    }
    
    .category-btn.active {
        background: #34495e;
        color: white;
    }
    
    .no-apps {
        text-align: center;
        padding: 3rem;
        color: #7f8c8d;
    }
    
    .no-apps-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    .refresh-info {
        background: #e8f4f8;
        color: #2980b9;
        padding: 0.5rem 1rem;
        border-radius: 3px;
        font-size: 0.8rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .stSelectbox > div > div {
        background-color: white;
    }
    
    .stTextInput > div > div > input {
        border-radius: 4px;
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 4px;
    }
    
    .stButton > button {
        border-radius: 4px;
        background: #2c3e50;
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: #34495e;
        transform: translateY(-1px);
        box-shadow: 0 3px 10px rgba(44, 62, 80, 0.3);
    }
    
    .unregistered-port-card {
        background: #fef9e7;
        border: 1px solid #f39c12;
        border-radius: 4px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .port-scan-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 4px;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }
    
    .scan-button {
        background: #2980b9;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 4px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .scan-button:hover {
        background: #3498db;
        transform: translateY(-1px);
        box-shadow: 0 3px 10px rgba(41, 128, 185, 0.3);
    }
    </style>
    """    

def display_user_info(user_info: Dict):
    """Display user information in sidebar"""
    with st.sidebar:
        st.html(f"""
        <div class="user-info">
            <h3>👤 {user_info['full_name'] or user_info['username']}</h3>
            <p><strong>Role:</strong> {user_info['role'].title()}</p>
            <p><strong>Email:</strong> {user_info.get('email', 'Not provided')}</p>
        </div>
        """)
        
        # Logout button
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            # Invalidate portal session if it exists
            portal_session_token = st.session_state.get('portal_session_token')
            if portal_session_token:
                from database import StreamlitPortalDB
                db = StreamlitPortalDB()
                db.invalidate_portal_session(portal_session_token)
            
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Clear cookie using JavaScript
            st.html("""
            <script>
                // Clear portal session cookie (multiple attempts for compatibility)
                document.cookie = "portal_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
                document.cookie = "portal_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; domain=localhost";
            </script>
            """)
            
            st.rerun()

def display_stats(total_apps: int, running_apps: int, total_users: int = None):
    """Display statistics cards"""
    stats_html = f"""
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-value">{total_apps}</div>
            <div class="stat-label">Total Apps</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{running_apps}</div>
            <div class="stat-label">Running Apps</div>
        </div>
    """
    
    if total_users is not None:
        stats_html += f"""
        <div class="stat-card">
            <div class="stat-value">{total_users}</div>
            <div class="stat-label">Total Users</div>
        </div>
        """
    
    stats_html += "</div>"
    st.html(stats_html)

def filter_apps_by_category(apps: List[Dict], selected_category: str) -> List[Dict]:
    """Filter apps by category"""
    if selected_category == "All":
        return apps
    return [app for app in apps if app.get('category', 'General') == selected_category]

def get_unique_categories(apps: List[Dict]) -> List[str]:
    """Get unique categories from apps"""
    categories = set()
    for app in apps:
        categories.add(app.get('category', 'General'))
    return sorted(list(categories))

def search_apps(apps: List[Dict], search_term: str) -> List[Dict]:
    """Search apps by name or description"""
    if not search_term:
        return apps
    
    search_term = search_term.lower()
    filtered_apps = []
    
    for app in apps:
        if (search_term in app['name'].lower() or 
            search_term in app.get('description', '').lower() or
            search_term in app.get('category', '').lower()):
            filtered_apps.append(app)
    
    return filtered_apps

def scan_port_range(start_port: int, end_port: int, registered_ports: List[int] = None, max_workers: int = 50) -> List[int]:
    """Scan a range of ports to find running web services, excluding already registered ports"""
    if registered_ports is None:
        registered_ports = []
    
    running_ports = []
    ports_to_scan = [port for port in range(start_port, end_port + 1) if port not in registered_ports]
    
    def check_single_port(port: int) -> Optional[int]:
        """Check if a single port is running a web service"""
        try:
            # First check if the port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)  # Very short timeout for port check
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:  # Port is open
                # Now check if it's a web service
                try:
                    response = requests.get(f"http://localhost:{port}", timeout=0.5)
                    if response.status_code == 200:
                        return port
                except:
                    pass  # Not a web service or other error
        except:
            pass
        return None
    
    # Use ThreadPoolExecutor for faster scanning
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_port = {executor.submit(check_single_port, port): port for port in ports_to_scan}
        
        for future in as_completed(future_to_port):
            result = future.result()
            if result is not None:
                running_ports.append(result)
    
    return sorted(running_ports)

@st.cache_data(ttl=60)  # Cache for 1 minute
def scan_unregistered_ports_cached(port_range_start: int = 8502, port_range_end: int = 8600, registered_ports: List[int] = None) -> List[int]:
    """Cached version of port scanning for unregistered apps"""
    return scan_port_range(port_range_start, port_range_end, registered_ports)

def display_unregistered_ports(unregistered_ports: List[int]):
    """Display found unregistered ports in a nice format"""
    if not unregistered_ports:
        st.info("🎉 No unregistered apps found running on ports 8502-8600")
        return
    
    st.warning(f"⚠️ Found {len(unregistered_ports)} unregistered app(s) running:")
    
    for port in unregistered_ports:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.write(f"**Port {port}**")
        
        with col2:
            try:
                # Try to get some basic info about the app
                response = requests.get(f"http://localhost:{port}", timeout=2)
                if "streamlit" in response.text.lower():
                    st.write("🎯 Likely a Streamlit app")
                else:
                    st.write("🌐 Web application")
            except:
                st.write("🔗 Web service")
        
        with col3:
            # Streamlit buttons can't directly be links, so use HTML button instead
            st.html(f'''
                <a href="http://localhost:{port}" target="_blank" class="launch-btn">
                    🌐 Open
                </a>
            ''')

def get_server_ip() -> str:
    """Get the local server's IP address (not localhost)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't have to be reachable
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"