"""
Streamlit Portal Security Library

This library provides secure access validation for Streamlit apps
that are part of the Streamlit Portal ecosystem.

Usage:
    from portal_security import require_portal_access
    
    # At the top of your Streamlit app (after page config)
    require_portal_access(app_id=1)  # Use your app's ID from the database
    
    # Your app code continues here...

"""

import streamlit as st
from datetime import datetime
import sys
import os

# Add the portal server directory to the path to import database module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import StreamlitPortalDB
except ImportError:
    st.error("⚠️ Portal security library requires access to the portal database.")
    st.stop()


def require_portal_access(app_id: int, db_path: str = "portal.db"):
    """
    Validate that the current Streamlit app is being accessed through the portal
    with a valid access token OR portal session.
    
    Args:
        app_id (int): The app ID from the portal database
        db_path (str): Path to the portal database file
        
    Raises:
        st.stop(): Stops the app execution if access is denied
    """
    
    # Initialize database connection
    try:
        db = StreamlitPortalDB(db_path)
    except Exception as e:
        st.error(f"🔴 **Security Error**: Cannot connect to portal database")
        st.write(f"Technical details: {str(e)}")
        st.stop()
    
    # Get query parameters
    query_params = st.query_params
    
    # Check for portal session token (new method - preferred)
    portal_session_token = query_params.get("portal_session")
    
    if portal_session_token:
        # Validate portal session directly
        user_info = db.validate_portal_session(portal_session_token)
        if user_info:
            # Check if user has access to this app
            accessible_apps = db.get_accessible_apps(user_info['id'])
            app_accessible = any(app['id'] == app_id for app in accessible_apps)
            
            if app_accessible:
                # Success! Add security indicator
                app_info = db.get_app_by_id(app_id)
                app_name = app_info['name'] if app_info else f"App {app_id}"
                
                st.markdown(
                    f"""
                    <div style="
                        position: fixed; 
                        top: 10px; 
                        right: 10px; 
                        background: rgba(40, 167, 69, 0.1); 
                        color: #28a745; 
                        padding: 5px 10px; 
                        border-radius: 4px; 
                        font-size: 12px; 
                        z-index: 999;
                        border: 1px solid rgba(40, 167, 69, 0.3);
                    ">
                        🔒 Portal Session Access to {app_name}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                return
            else:
                _show_access_denied("User does not have access to this application")
                return
        else:
            _show_access_denied("Invalid or expired portal session")
            return
    
    # Fallback to legacy token method (for compatibility)
    access_token = query_params.get("token")
    
    if not access_token:
        _show_access_denied("No access token or portal session provided")
        return
    
    # Validate the token (legacy method)
    try:
        is_valid = db.validate_access_token(access_token, app_id)
        
        if not is_valid:
            _show_access_denied("Invalid or expired access token")
            return
            
        # Get app info for display
        app_info = db.get_app_by_id(app_id)
        app_name = app_info['name'] if app_info else f"App {app_id}"
        
        # Success! Add a small security indicator
        st.markdown(
            f"""
            <div style="
                position: fixed; 
                top: 10px; 
                right: 10px; 
                background: rgba(40, 167, 69, 0.1); 
                color: #28a745; 
                padding: 5px 10px; 
                border-radius: 4px; 
                font-size: 12px; 
                z-index: 999;
                border: 1px solid rgba(40, 167, 69, 0.3);
            ">
                🔒 Legacy Token Access to {app_name}
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    except Exception as e:
        _show_access_denied(f"Security validation error: {str(e)}")
        return


def _show_access_denied(reason: str = "Access denied"):
    """
    Display a consistent access denied message and stop the app.
    
    Args:
        reason (str): The reason for access denial
    """
    
    st.markdown(
        """
        <div style="text-align: center; padding: 50px;">
            <h1 style="color: #dc3545;">🚫 Access Denied</h1>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.error("**Unauthorized Access Attempt**")
        st.warning("This application can only be accessed through the Streamlit Portal with a valid access token.")
        
        with st.expander("Technical Details"):
            st.write(f"**Reason:** {reason}")
            st.write(f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.write("**Required:** Valid portal access token")
        
        st.info("**How to get access:**")
        st.markdown("""
        1. 🌐 Go to the **Streamlit Portal**
        2. 🔐 **Log in** with your credentials  
        3. 🎯 Find this app in your dashboard
        4. 🚀 Click the **"Launch App"** button
        """)
        
        st.markdown("---")
        
        # Portal link (try to detect the portal URL)
        portal_url = "http://localhost:8501"  # Default portal URL
        st.markdown(
            f"""
            <div style="text-align: center;">
                <a href="{portal_url}" target="_blank" style="
                    display: inline-block;
                    background-color: #007bff;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                ">
                    🏠 Return to Portal
                </a>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    st.stop()


def get_current_user_info(app_id: int, db_path: str = "portal.db"):
    """
    Get information about the current user accessing the app.
    
    Args:
        app_id (int): The app ID from the portal database
        db_path (str): Path to the portal database file
        
    Returns:
        dict: User information if available, None if not accessible
    """
    
    try:
        db = StreamlitPortalDB(db_path)
        query_params = st.query_params
        access_token = query_params.get("token")
        
        if not access_token:
            return None
            
        # Get the user ID from the token
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id FROM access_tokens 
            WHERE token = ? AND app_id = ? AND expires_at > ?
        ''', (access_token, app_id, datetime.now()))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return None
            
        user_id = result[0]
        user_info = db.get_user_by_id(user_id)
        conn.close()
        
        return user_info
        
    except Exception:
        return None


# Decorator version for easier use
def portal_protected(app_id: int, db_path: str = "portal.db"):
    """
    Decorator to protect a Streamlit app function with portal authentication.
    
    Usage:
        @portal_protected(app_id=1)
        def main():
            st.title("My Protected App")
            # Your app code here
            
        if __name__ == "__main__":
            main()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            require_portal_access(app_id, db_path)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    st.title("Portal Security Library Test")
    st.write("This is a test of the portal security library.")
    
    # Test the security (this will show access denied since no token)
    require_portal_access(app_id=1)