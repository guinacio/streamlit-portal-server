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

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import streamlit
        import pandas
        import bcrypt
        import requests
        import PIL
        import plotly
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def start_app(script_path, port, app_name):
    """Start a Streamlit app on specified port"""
    try:
        print(f"🚀 Starting {app_name} on port {port}...")
        
        # Create the command
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            script_path, 
            "--server.port", str(port),
            "--server.headless", "true",
            "--logger.level", "error"
        ]
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"✅ {app_name} started successfully on port {port}")
            return process
        else:
            print(f"❌ Failed to start {app_name}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting {app_name}: {e}")
        return None

def main():
    print("🎯 Streamlit Portal Demo Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check if demo apps exist
    demo_app1 = Path("demo_apps/demo_app_1.py")
    demo_app2 = Path("demo_apps/demo_app_2.py")
    
    if not demo_app1.exists():
        print(f"❌ Demo app 1 not found: {demo_app1}")
        return
    
    if not demo_app2.exists():
        print(f"❌ Demo app 2 not found: {demo_app2}")
        return
    
    # Create directories if they don't exist
    os.makedirs("app_images", exist_ok=True)
    
    print("\n📱 Starting demo applications...")
    
    # Start demo apps
    processes = []
    
    # Start demo app 1 (Analytics Dashboard)
    process1 = start_app(str(demo_app1), 8502, "Analytics Dashboard")
    if process1:
        processes.append(process1)
    
    # Start demo app 2 (ML Playground)
    process2 = start_app(str(demo_app2), 8503, "ML Playground")
    if process2:
        processes.append(process2)
    
    # Start the main portal
    print("\n🚀 Starting Streamlit Portal...")
    try:
        portal_cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "app.py",
            "--server.port", "8501"
        ]
        
        print("🌐 Portal will be available at: http://localhost:8501")
        print("\n📋 Default login credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n🎮 Demo apps will be running on:")
        print("   📊 Analytics Dashboard: http://localhost:8502")
        print("   🤖 ML Playground: http://localhost:8503")
        print("\n⚠️  After logging in, go to Admin Panel to configure the demo apps!")
        print("\n🛑 Press Ctrl+C to stop all applications")
        
        # # Run the portal (this will block)
        # subprocess.run(portal_cmd)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down applications...")
        
        # Terminate demo apps
        for process in processes:
            if process and process.poll() is None:
                process.terminate()
                
        print("✅ All applications stopped")
    
    except Exception as e:
        print(f"❌ Error starting portal: {e}")

def quick_setup():
    """Quick setup instructions"""
    print("🔧 Quick Setup Instructions:")
    print("1. Login to portal with admin/admin123")
    print("2. Go to Admin Panel → Manage Apps")
    print("3. Add these demo apps:")
    print("   - Port 8502: Analytics Dashboard (Analytics category)")
    print("   - Port 8503: ML Playground (ML/AI category)")
    print("4. Go to Admin Panel → Manage Users")
    print("5. Create test users with groups (e.g., 'analysts', 'developers')")
    print("6. Go to Admin Panel → Groups & Permissions")
    print("7. Set which groups can access which apps")
    print("8. Logout and test with different users!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        quick_setup()
    else:
        main() 