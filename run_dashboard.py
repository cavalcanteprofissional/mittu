#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Dashboard Script
====================

Easy script to start the Streamlit dashboard.

Usage:
    python run_dashboard.py
"""

import subprocess
import sys
import os


def main():
    """Start the Streamlit dashboard."""
    print("🚀 Starting Project Management Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the dashboard")
    print("-" * 50)
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Start Streamlit dashboard
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboard.py", "--server.port", "8501"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install dependencies with: poetry install")
        sys.exit(1)


if __name__ == "__main__":
    main()