#!/usr/bin/env python3
"""
LookML Filter Link Visualizer - Launcher Script

This script launches the Streamlit + PyVis application for visualizing
LookML dashboard filter links.

Usage:
    python run_app.py

Requirements:
    - streamlit
    - pyvis
    - plotly
    - pandas
    - numpy
    - pyyaml

Author: AI Assistant
Date: 2024
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'pyvis',
        'plotly',
        'pandas',
        'numpy',
        'yaml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("📦 Install them with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main launcher function"""
    print("🔗 LookML Filter Link Visualizer")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("streamlit_app.py").exists():
        print("❌ streamlit_app.py not found in current directory")
        print("Please run this script from the project directory")
        return
    
    # Check requirements
    if not check_requirements():
        return
    
    print("✅ All requirements satisfied")
    print("🚀 Starting Streamlit application...")
    print("📱 The app will open in your browser at http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the application")
    print()
    
    try:
        # Launch Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error launching application: {e}")

if __name__ == "__main__":
    main()
