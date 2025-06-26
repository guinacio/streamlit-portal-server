#!/usr/bin/env python3
"""
Setup script for Streamlit Portal
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call(["uv", "sync"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    os.makedirs("app_images", exist_ok=True)
    os.makedirs("demo_apps", exist_ok=True)
    print("✅ Directories created!")

def check_files():
    """Check if all required files exist"""
    required_files = [
        "app.py",
        "database.py", 
        "utils.py",
        "requirements.txt",
        "demo_apps/demo_app_1.py",
        "demo_apps/demo_app_2.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files found!")
    return True

def main():
    print("🚀 Streamlit Portal Setup")
    print("=" * 50)
    
    # Check files
    if not check_files():
        print("\n❌ Setup incomplete. Please ensure all files are present.")
        return
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run the demo: python run_demo.py")
    print("2. Or run manually: streamlit run app.py")
    print("3. Open browser to: http://localhost:8501")
    print("4. Login with: admin / admin123")
    print("\n🔧 For quick setup help: python run_demo.py --help")

if __name__ == "__main__":
    main() 