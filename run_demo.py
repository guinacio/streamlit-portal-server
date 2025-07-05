#!/usr/bin/env python3
"""
Demo startup script for Streamlit Portal

This script helps you easily start the portal and demo applications
"""

import subprocess
import sys
import time
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console and ensure unbuffered output
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Force Python to use unbuffered output for immediate print statements
os.environ["PYTHONUNBUFFERED"] = "1"

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import streamlit
        import pandas
        import bcrypt
        import requests
        import PIL
        import plotly
        import fastapi
        import uvicorn
        print("✅ All dependencies are installed", flush=True)
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}", flush=True)
        print("Please run: uv sync", flush=True)
        print("Or if using pip: pip install -r requirements.txt", flush=True)
        return False

def start_app(script_path, port, app_name):
    """Start a Streamlit app on specified port"""
    try:
        print(f"🚀 Starting {app_name} on port {port}...", flush=True)
        
        # Use the virtual environment's Python executable
        venv_python = Path(".venv/Scripts/python.exe")
        if not venv_python.exists():
            # Try Unix-style path as fallback
            venv_python = Path(".venv/bin/python")
            if not venv_python.exists():
                print("❌ Virtual environment not found. Please run: uv sync", flush=True)
                return None
        
        # Convert paths to absolute paths
        script_path = Path(script_path).resolve()
        venv_python = venv_python.resolve()
        
        # Determine working directory
        if "demo_apps" in str(script_path):
            # For demo apps, run from the demo_apps directory
            working_dir = script_path.parent
            script_name = script_path.name
        else:
            # For other apps, run from current directory
            working_dir = Path.cwd()
            script_name = str(script_path)
        
        # Create the command
        cmd = [
            str(venv_python), "-m", "streamlit", "run", 
            script_name, 
            "--server.port", str(port),
            "--server.headless", "true",
            "--logger.level", "error"
        ]
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(working_dir)
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"✅ {app_name} started successfully on port {port}", flush=True)
            return process
        else:
            print(f"❌ Failed to start {app_name}", flush=True)
            return None
            
    except Exception as e:
        print(f"❌ Error starting {app_name}: {e}", flush=True)
        return None

def start_proxy_server():
    """Start the FastAPI proxy server"""
    try:
        print("🚀 Starting Proxy Server on port 8000...", flush=True)
        
        # Use the virtual environment's Python executable
        venv_python = Path(".venv/Scripts/python.exe")
        if not venv_python.exists():
            # Try Unix-style path as fallback
            venv_python = Path(".venv/bin/python")
            if not venv_python.exists():
                print("❌ Virtual environment not found. Please run: uv sync", flush=True)
                return None
        
        # Create the command to run the proxy server with venv python
        cmd = [str(venv_python), "proxy_server.py"]
        
        # Set up environment with UTF-8 encoding
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        if sys.platform == "win32":
            env["PYTHONLEGACYWINDOWSSTDIO"] = "1"
        
        # Start the process and capture output for debugging
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Proxy Server started successfully on port 8000", flush=True)
            return process
        else:
            # Get the error output
            stdout, stderr = process.communicate()
            print("❌ Failed to start Proxy Server", flush=True)
            if stderr:
                print(f"   Error: {stderr.strip()}", flush=True)
            if stdout:
                print(f"   Output: {stdout.strip()}", flush=True)
            return None
            
    except Exception as e:
        print(f"❌ Error starting Proxy Server: {e}", flush=True)
        return None

def main():
    print("🎯 Streamlit Portal Demo Launcher", flush=True)
    print("=" * 50, flush=True)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check if required files exist
    demo_app1 = Path("demo_apps/demo_app_1.py")
    demo_app2 = Path("demo_apps/demo_app_2.py")
    proxy_server = Path("proxy_server.py")
    
    if not demo_app1.exists():
        print(f"❌ Demo app 1 not found: {demo_app1}", flush=True)
        return
    
    if not demo_app2.exists():
        print(f"❌ Demo app 2 not found: {demo_app2}", flush=True)
        return
    
    if not proxy_server.exists():
        print(f"❌ Proxy server not found: {proxy_server}", flush=True)
        return
    
    # Create directories if they don't exist
    os.makedirs("app_images", exist_ok=True)
    
    print("\n📱 Starting demo applications...", flush=True)
    
    # Start demo apps and proxy server
    processes = []
    
    # Start demo app 1 (Analytics Dashboard)
    process1 = start_app(str(demo_app1), 8502, "Analytics Dashboard")
    if process1:
        processes.append(process1)
    
    # Start demo app 2 (ML Playground)
    process2 = start_app(str(demo_app2), 8503, "ML Playground")
    if process2:
        processes.append(process2)
    
    # Start proxy server
    print("\n🔒 Starting security components...", flush=True)
    proxy_process = start_proxy_server()
    if proxy_process:
        processes.append(proxy_process)
    
    # Start the main portal
    print("\n🚀 Starting Streamlit Portal...", flush=True)
    try:
        # Use the virtual environment's Python executable
        venv_python = Path(".venv/Scripts/python.exe")
        if not venv_python.exists():
            # Try Unix-style path as fallback
            venv_python = Path(".venv/bin/python")
            if not venv_python.exists():
                print("❌ Virtual environment not found. Please run: uv sync", flush=True)
                return
        
        portal_cmd = [
            str(venv_python), "-m", "streamlit", "run", 
            "app.py",
            "--server.port", "8501"
        ]
        
        print("🌐 Portal will be available at: http://localhost:8501", flush=True)
        print("🔒 Proxy Server running at: http://localhost:8000", flush=True)
        print("\n📋 Default login credentials:", flush=True)
        print("   Username: admin", flush=True)
        print("   Password: admin123", flush=True)
        print("\n🎮 Demo apps will be running on:", flush=True)
        print("   📊 Analytics Dashboard: http://localhost:8502", flush=True)
        print("   🤖 ML Playground: http://localhost:8503", flush=True)
        print("\n⚠️  After logging in, go to Admin Panel to configure the demo apps!", flush=True)
        print("\n🛑 Press Ctrl+C to stop all applications", flush=True)
        
        # Run the portal (this will block)
        subprocess.run(portal_cmd)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down applications...", flush=True)
        
        # Terminate all processes
        for process in processes:
            if process and process.poll() is None:
                process.terminate()
                
        print("✅ All applications stopped", flush=True)
    
    except Exception as e:
        print(f"❌ Error starting portal: {e}", flush=True)

def quick_setup():
    """Quick setup instructions"""
    print("🔧 Quick Setup Instructions:", flush=True)
    print("1. Login to portal with admin/admin123", flush=True)
    print("2. Go to Admin Panel → Manage Apps", flush=True)
    print("3. Add these demo apps:", flush=True)
    print("   - Port 8502: Analytics Dashboard (Analytics category)", flush=True)
    print("   - Port 8503: ML Playground (ML/AI category)", flush=True)
    print("4. Go to Admin Panel → Manage Users", flush=True)
    print("5. Create test users with groups (e.g., 'analysts', 'developers')", flush=True)
    print("6. Go to Admin Panel → Groups & Permissions", flush=True)
    print("7. Set which groups can access which apps", flush=True)
    print("8. Logout and test with different users!", flush=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        quick_setup()
    else:
        main() 