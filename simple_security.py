"""
Simple Security Library for Streamlit Apps

This library provides basic protection against direct port access
for Streamlit apps in the Portal ecosystem.

Usage:
    from simple_security import require_portal_access
    
    # At the top of your Streamlit app (after page config)
    require_portal_access()
    
    # Your app code continues here...
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import requests


def require_portal_access(app_id: int):
    """
    Validate that the app is being accessed through the portal with a valid session.
    
    This prevents both direct port access and iframe URL sharing by validating
    the session token against the proxy server's session store.
    """
    
    # Get query parameters
    query_params = st.query_params
    
    # Check for portal session parameter
    portal_session = query_params.get("portal_session")
    
    if not portal_session:
        _show_access_denied("Direct access not permitted")
        return
    
    # Validate the session token against the proxy server
    try:
        validation_url = f"http://localhost:8000/validate-session/{app_id}/{portal_session}"
        response = requests.get(validation_url, timeout=5)
        
        if response.status_code != 200:
            _show_access_denied("Session validation failed")
            return
        
        result = response.json()
        
        if not result.get("valid", False):
            _show_access_denied("Invalid session")
            return
            
    except requests.RequestException as e:
        _show_access_denied("Unable to validate session")
        return
    except Exception as e:
        _show_access_denied("Session validation error")
        return
    
    # Additional JavaScript check for iframe context
    components.html("""
    <script>
    if (window.self === window.top) {
        // Direct access detected - not in iframe - redirect to portal
        window.location.href = 'http://localhost:8501';
    }
    </script>
    """, height=0)
    
    # Success! Show a small security indicator
    st.markdown(
        """
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
            🔒 Portal Access
        </div>
        """, 
        unsafe_allow_html=True
    )


def _show_access_denied(reason: str = "Access denied"):
    """
    Display a simple access denied message.
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
        st.error("**Access Not Authorized**")
        st.warning("You don't have permission to access this application.")
        
        st.markdown("**To access this application:**")
        st.markdown("""
        1. 🌐 Contact your administrator for access
        2. 🔐 Ensure you have the proper credentials
        3. 🎯 Access through the appropriate portal
        """)
        
        # Portal link
        st.markdown(
            """
            <div style="text-align: center; margin-top: 20px;">
                <a href="http://localhost:8501" target="_blank" style="
                    display: inline-block;
                    background-color: #007bff;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                ">
                    🏠 Return to Portal
                </a>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    st.stop()


# For backward compatibility
def portal_protected(app_id: int):
    """
    Decorator version for protecting functions
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            require_portal_access(app_id)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    st.title("Simple Security Test")
    st.write("This is a test of the simple security library.")
    
    # Test the security (this will show access denied for direct access)
    require_portal_access(app_id=999)  # Test app ID
    
    st.success("If you see this, you accessed through the portal with a valid session!")