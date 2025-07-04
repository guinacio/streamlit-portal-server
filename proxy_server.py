import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
import secrets
from datetime import datetime, timedelta
from database import StreamlitPortalDB

app = FastAPI(title="Streamlit Portal Proxy", description="Cookie-based secure proxy for Streamlit apps")
db = StreamlitPortalDB()

# In-memory session store (use Redis in production)
active_sessions = {}

def cleanup_expired_sessions():
    """Remove expired sessions"""
    current_time = datetime.now()
    expired_keys = [
        session_id for session_id, session_data in active_sessions.items()
        if session_data['expires_at'] < current_time
    ]
    for key in expired_keys:
        del active_sessions[key]

def create_secure_session(user_id: int, app_id: int) -> str:
    """Create a secure session for user-app combination"""
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=2)  # 2-hour session
    
    active_sessions[session_id] = {
        'user_id': user_id,
        'app_id': app_id,
        'expires_at': expires_at,
        'created_at': datetime.now()
    }
    
    return session_id

def validate_session_cookie(request: Request, app_id: int) -> dict:
    """Validate session cookie for specific app"""
    session_cookie = request.cookies.get(f"portal_session_{app_id}")
    
    if not session_cookie:
        return None
    
    session_data = active_sessions.get(session_cookie)
    if not session_data:
        return None
    
    # Check if session expired
    if session_data['expires_at'] < datetime.now():
        del active_sessions[session_cookie]
        return None
    
    # Check if session is for the correct app
    if session_data['app_id'] != app_id:
        return None
    
    return session_data

def create_iframe_page(app_info: dict, request: Request, user_id: int = 0) -> str:
    """Create an HTML page with iframe embedding the Streamlit app"""
    
    # Get the portal URL for the back button
    portal_host = request.headers.get('host', 'localhost:8000').replace(':8000', ':8501')
    portal_url = f"http://{portal_host}"
    
    # Create a short-lived validation token for the Streamlit app
    validation_token = secrets.token_urlsafe(16)
    
    # Store the validation token with very short expiration (1 minute)
    # and mark it as single-use
    active_sessions[f"iframe_{validation_token}"] = {
        'user_id': user_id,
        'app_id': app_info['id'],
        'expires_at': datetime.now() + timedelta(minutes=1),  # Very short-lived
        'session_type': 'iframe_access',
        'single_use': True,
        'used': False
    }
    
    streamlit_url = f"http://localhost:{app_info['port']}?portal_session={validation_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{app_info['name']} - Streamlit Portal</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background-color: #f0f2f6;
            }}
            
            .header {{
                background-color: #262730;
                color: white;
                padding: 10px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .app-title {{
                font-size: 18px;
                font-weight: 600;
            }}
            
            .session-info {{
                font-size: 12px;
                color: #28a745;
                background: rgba(40, 167, 69, 0.1);
                padding: 4px 8px;
                border-radius: 3px;
                border: 1px solid rgba(40, 167, 69, 0.3);
            }}
            
            .portal-link {{
                color: #ff6b6b;
                text-decoration: none;
                font-size: 14px;
                padding: 5px 10px;
                border: 1px solid #ff6b6b;
                border-radius: 4px;
                transition: all 0.3s ease;
            }}
            
            .portal-link:hover {{
                background-color: #ff6b6b;
                color: white;
            }}
            
            .iframe-container {{
                width: 100%;
                height: calc(100vh - 60px);
                border: none;
                overflow: hidden;
            }}
            
            iframe {{
                width: 100%;
                height: 100%;
                border: none;
                background-color: white;
            }}
            
            .loading {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="app-title">🎯 {app_info['name']}</div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <div class="session-info">🔒 Secure Session Active</div>
                <a href="{portal_url}" class="portal-link">← Back to Portal</a>
            </div>
        </div>
        
        <div class="loading" id="loading">
            <div>Loading {app_info['name']}...</div>
            <div style="margin-top: 10px; font-size: 12px;">Establishing secure connection</div>
        </div>
        
        <div class="iframe-container">
            <iframe 
                src="{streamlit_url}" 
                allowfullscreen
                onload="document.getElementById('loading').style.display='none'"
            ></iframe>
        </div>
        
        <script>
            // Hide loading indicator after 10 seconds regardless
            setTimeout(function() {{
                document.getElementById('loading').style.display = 'none';
            }}, 10000);
            
            // Auto-refresh session every 30 minutes to keep it active
            setInterval(function() {{
                fetch('/refresh-session/{app_info['id']}', {{
                    method: 'POST',
                    credentials: 'include'
                }}).catch(() => {{}});
            }}, 30 * 60 * 1000);
        </script>
    </body>
    </html>
    """
    
    return html_content

@app.get("/app/{app_id}/")
async def serve_app(request: Request, response: Response, app_id: int):
    """Serve the Streamlit app with cookie-based authentication"""
    
    cleanup_expired_sessions()
    
    # Check if there's an auth_token in query params (initial access)
    auth_token = request.query_params.get("auth_token")
    
    if auth_token:
        # First-time access with token - validate that it was generated by an active portal session
        # This method doesn't rely on cookies - it checks the database directly
        
        # Validate that the token was generated by a currently active portal session
        if not db.validate_access_token_with_active_portal_session(auth_token, app_id):
            return HTMLResponse(
                content=create_access_denied_page_with_reason(
                    app_id,
                    "Access Denied", 
                    "Invalid or expired access credentials."
                ),
                status_code=403
            )
        
        # Get user info from the valid token
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id FROM access_tokens 
            WHERE token = ? AND app_id = ? AND expires_at > ?
        ''', (auth_token, app_id, datetime.now()))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=403, detail="Token validation failed")
        
        user_id = result[0]
        
        # IMPORTANT: Invalidate the auth token so it can't be reused
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM access_tokens WHERE token = ?', (auth_token,))
        conn.commit()
        conn.close()
        
        # Create secure session
        session_id = create_secure_session(user_id, app_id)
        
        # Set secure cookie
        response.set_cookie(
            key=f"portal_session_{app_id}",
            value=session_id,
            max_age=7200,  # 2 hours
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        # Get app info
        app_info = db.get_app_by_id(app_id)
        if not app_info:
            raise HTTPException(status_code=404, detail="App not found")
        
        # Redirect to clean URL without the auth_token and portal_session parameters
        clean_url = f"/app/{app_id}/"
        response = RedirectResponse(url=clean_url, status_code=302)
        response.set_cookie(
            key=f"portal_session_{app_id}",
            value=session_id,
            max_age=7200,  # 2 hours
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        return response
    
    else:
        # Subsequent access - validate session cookie
        session_data = validate_session_cookie(request, app_id)
        
        if not session_data:
            # No valid session - show access denied
            return HTMLResponse(
                content=create_access_denied_page(app_id),
                status_code=403
            )
        
        # Valid session - serve the app
        app_info = db.get_app_by_id(app_id)
        if not app_info:
            raise HTTPException(status_code=404, detail="App not found")
        
        html_content = create_iframe_page(app_info, request, session_data['user_id'])
        return HTMLResponse(content=html_content, status_code=200)

@app.post("/refresh-session/{app_id}")
async def refresh_session(request: Request, app_id: int):
    """Refresh an active session to prevent expiration"""
    session_data = validate_session_cookie(request, app_id)
    
    if session_data:
        # Extend session by 2 hours
        session_cookie = request.cookies.get(f"portal_session_{app_id}")
        active_sessions[session_cookie]['expires_at'] = datetime.now() + timedelta(hours=2)
        return {"status": "refreshed"}
    
    return {"status": "invalid"}

@app.get("/validate-session/{app_id}/{session_token}")
async def validate_app_session(request: Request, app_id: int, session_token: str):
    """Validate a session token for Streamlit apps - single use only"""
    cleanup_expired_sessions()
    
    # Check if the iframe session token exists and is valid
    session_key = f"iframe_{session_token}"
    iframe_session_data = active_sessions.get(session_key)
    
    if not iframe_session_data:
        return {"valid": False, "reason": "Session not found"}
    
    # Check if session expired
    if iframe_session_data['expires_at'] < datetime.now():
        del active_sessions[session_key]
        return {"valid": False, "reason": "Session expired"}
    
    # Check if session is for the correct app
    if iframe_session_data['app_id'] != app_id:
        return {"valid": False, "reason": "App mismatch"}
    
    # CRITICAL: Always check if it's single-use and already used
    if iframe_session_data.get('single_use', False) and iframe_session_data.get('used', False):
        del active_sessions[session_key]
        return {"valid": False, "reason": "Session already used"}
    
    # CRITICAL: Mark as used immediately to prevent reuse
    if iframe_session_data.get('single_use', False):
        active_sessions[session_key]['used'] = True
    
    return {
        "valid": True,
        "user_id": iframe_session_data['user_id'],
        "app_id": iframe_session_data['app_id'],
        "expires_at": iframe_session_data['expires_at'].isoformat()
    }

def create_access_denied_page(app_id: int) -> str:
    """Create a simple access denied page"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Access Denied - Streamlit Portal</title>
        <style>
            body {{
                margin: 0;
                padding: 50px;
                font-family: Arial, sans-serif;
                background-color: #f8f9fa;
                text-align: center;
            }}
            .container {{
                max-width: 500px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            }}
            .error-icon {{
                font-size: 4rem;
                color: #dc3545;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #dc3545;
                margin-bottom: 20px;
            }}
            .portal-btn {{
                display: inline-block;
                background: #007bff;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">🚫</div>
            <h1>Access Denied</h1>
            <p>You don't have permission to access this application.</p>
            <p>Please contact your administrator for access.</p>
            
            <a href="http://localhost:8501" class="portal-btn">🏠 Return to Portal</a>
        </div>
    </body>
    </html>
    """

def create_access_denied_page_with_reason(app_id: int, title: str, message: str) -> str:
    """Create a simple access denied page with basic reason"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Streamlit Portal</title>
        <style>
            body {{
                margin: 0;
                padding: 50px;
                font-family: Arial, sans-serif;
                background-color: #f8f9fa;
                text-align: center;
            }}
            .container {{
                max-width: 500px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            }}
            .error-icon {{
                font-size: 4rem;
                color: #dc3545;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #dc3545;
                margin-bottom: 20px;
            }}
            .portal-btn {{
                display: inline-block;
                background: #007bff;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">🚫</div>
            <h1>{title}</h1>
            <p>{message}</p>
            <p>Please contact your administrator for access.</p>
            
            <a href="http://localhost:8501" class="portal-btn">🏠 Return to Portal</a>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "streamlit-portal-cookie-proxy", "version": "6.0"}

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "Streamlit Portal - Cookie-Based Proxy v6.0", 
        "status": "running",
        "security": "cookie-based session management",
        "features": [
            "Secure session cookies",
            "Non-shareable URLs", 
            "Automatic session expiration",
            "Session refresh capability"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Streamlit Portal Cookie-Based Proxy v6.0...")
    print("📡 Proxy will be available at: http://localhost:8000")
    print("🔒 Enhanced security features:")
    print("   • Cookie-based session management")
    print("   • Non-shareable URLs") 
    print("   • 2-hour session expiration")
    print("   • Automatic session refresh")
    print("   • In-memory session store")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")