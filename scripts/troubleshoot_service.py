#!/usr/bin/env python3
"""
Troubleshooting script for sms004 Django service
"""

import subprocess
import sys
from pathlib import Path

def test_django():
    """Test Django configuration"""
    print("Testing Django configuration...")
    try:
        result = subprocess.run([self.venv_path, "manage.py", "check", "--deploy"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Django configuration is OK")
        else:
            print("Django configuration issues:")
            print(result.stdout)
            print(result.stderr)
    except Exception as e:
        print(f"Error testing Django: {e}")

def test_database():
    """Test database connection"""
    print("Testing database connection...")
    try:
        result = subprocess.run([self.venv_path, "manage.py", "migrate", "--check"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Database connection is OK")
        else:
            print("Database issues:")
            print(result.stdout)
            print(result.stderr)
    except Exception as e:
        print(f"Error testing database: {e}")

def test_service_script():
    """Test the service script"""
    print("Testing service script...")
    try:
        result = subprocess.run([self.venv_path, "run_service.py"], 
                              timeout=10, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        print("Service script started successfully")
    except Exception as e:
        print(f"Service script failed: {e}")

def check_service_status():
    """Check service status"""
    print("Checking service status...")
    try:
        result = subprocess.run(["sc", "query", "sms004"], 
                              capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error checking service: {e}")

def main():
    print("="*50)
    print("Django Service Troubleshooting")
    print("="*50)
    
    test_django()
    print()
    test_database()
    print()
    test_service_script()
    print()
    check_service_status()
    
    print("\n" + "="*50)
    print("Troubleshooting complete!")
    print("="*50)

if __name__ == "__main__":
    main()
