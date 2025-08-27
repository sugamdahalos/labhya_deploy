#!/usr/bin/env python3
"""
Labhya GPU Agent Startup Script
Python equivalent of start_agent.bat for cross-platform compatibility
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python():
    """Check if Python is available and version is adequate"""
    try:
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("Error: Python 3.8+ is required")
            print(f"Current version: {version.major}.{version.minor}.{version.micro}")
            return False
        return True
    except Exception:
        print("Error: Unable to check Python version")
        return False

def check_files():
    """Check if required files exist"""
    required_files = ['combined_agent.py', 'requirements.txt']
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"Error: Missing required files: {', '.join(missing_files)}")
        print("Please run this script from the agent directory")
        return False
    
    return True

def install_requirements():
    """Install Python requirements if needed"""
    flag_file = Path('requirements_installed.flag')
    
    if not flag_file.exists():
        print("Installing Python dependencies...")
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                flag_file.touch()
                print("Dependencies installed successfully!")
            else:
                print("Warning: Failed to install some dependencies")
                print(f"Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error installing dependencies: {e}")
            return False
        print()
    
    return True

def get_mode():
    """Get the operation mode from user"""
    try:
        mode = input("Run in GUI mode? (y/n, default: y): ").lower().strip()
        return mode not in ['n', 'no']
    except (EOFError, KeyboardInterrupt):
        return True  # Default to GUI

def run_gui():
    """Run the GUI launcher"""
    print("Starting GUI launcher...")
    try:
        subprocess.run([sys.executable, 'launcher.py'])
        return True
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return True
    except Exception as e:
        print(f"Error running GUI: {e}")
        return False

def run_headless():
    """Run in headless mode"""
    print("Starting in headless mode...")
    print("Set these environment variables before running:")
    print("  LABHYA_API_URL=http://your-server.com:8000")
    print("  LABHYA_AGENT_EMAIL=your-email@example.com")
    print("  LABHYA_AGENT_PASSWORD=your-password")
    print()
    
    # Check system requirements first
    try:
        subprocess.run([sys.executable, 'combined_agent.py', '--check'])
        print()
        
        try:
            confirm = input("Continue with agent startup? (y/n): ").lower().strip()
            if confirm in ['y', 'yes']:
                subprocess.run([sys.executable, 'combined_agent.py'])
        except (EOFError, KeyboardInterrupt):
            print("\nStartup cancelled by user")
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error running headless mode: {e}")

def main():
    """Main startup function"""
    print("Labhya GPU Agent Startup")
    print("=" * 40)
    print()
    
    # Check Python version
    if not check_python():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Check required files
    if not check_files():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Get operation mode
    gui_mode = get_mode()
    
    if gui_mode:
        success = run_gui()
    else:
        run_headless()
        success = True
    
    if not success:
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStartup interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
