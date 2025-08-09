import os
import subprocess
import sys
import platform
from pathlib import Path
class AppInstaller:
    def __init__(self):
        self.project_dir = Path(__file__).resolve().parent
        self.app_name = "sms004"
        self.log_dir = self.project_dir / "logs"
        self.venv_path = self.project_dir / "venv" / "Scripts" / "python.exe"

    def start_service(self):
        """Start the Windows service"""
        print(f"\n🚀 Starting service '{self.app_name}'...")

        try:
            result = subprocess.run(['sc', 'start', self.app_name], capture_output=True, text=True, check=True)
            if "START_PENDING" in result.stdout or "RUNNING" in result.stdout:
                print("✅ Service started successfully")
                return True
            else:
                print("⚠️ Service did not start as expected")
                print(result.stdout)
                return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start service: {e}")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")
            return False
        
    def print_header(self):
        """Print installation header"""
        print("="*60)
        print("     Django Application Installation Script")
        print("         Using NSSM for Windows Service")
        print("="*60)
        print(f"Operating System: {platform.system()} {platform.release()}")
        print(f"Python Version: {sys.version.split()[0]}")
        print(f"Project Directory: {self.project_dir}")
        print("-"*60)

    def install_dependencies(self):
        """Install Python dependencies"""
        print("\n📦 Installing Python dependencies...")

        dependencies = ['django', 'waitress']
        for dep in dependencies:
            try:
                print(f"Installing {dep}...")
                subprocess.run([self.venv_path, '-m', 'pip', 'install', dep], 
                             check=True, capture_output=True)
                print(f" {dep} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f" Failed to install {dep}: {e}")
                return False

        return True

    def collect_static(self):
        """Collect static files"""
        print("\n📂 Collecting static files...")

        try:
            subprocess.run([self.venv_path, 'manage.py', 'collectstatic', '--noinput'], 
                        cwd=str(self.project_dir), check=True, capture_output=True)
            print("Static files collected successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to collect static files: {e}")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")
            return False
        
        return True

    def create_browser_watcher_task(self):
        """Create PowerShell watcher to open browser on new IP"""
        print("\n🕵️ Creating browser auto-launch script...")

        script_path = self.project_dir / "open_sms_in_browser.ps1"

        content = r'''
$knownIpPath = "$env:LOCALAPPDATA\last_opened_ip.txt"

function Get-CurrentIp {
    Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object {
            $_.IPAddress -notlike "169.254.*" -and
            $_.IPAddress -ne "127.0.0.1" -and
            $_.IPAddress -match "^192\.168\.|^10\.|^172\.(1[6-9]|2[0-9]|3[0-1])\."
        } |
        Select-Object -First 1 -ExpandProperty IPAddress
}

while ($true) {
    $ip = Get-CurrentIp
    if ($ip) {
        $lastIp = ""
        if (Test-Path $knownIpPath) {
            $lastIp = Get-Content $knownIpPath -Raw
        }

        if ($ip -ne $lastIp) {
            Start-Process "http://$ip:8000"
            Set-Content -Path $knownIpPath -Value $ip
        }
    }

    Start-Sleep -Seconds 15
}
'''
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"📄 PowerShell script created at: {script_path}")

        # Register with Windows Task Scheduler
        print("📅 Registering scheduled task to auto-run it at login...")

        try:
            subprocess.run([
                "schtasks", "/Create",
                "/TN", "OpenSMSBrowser",
                "/TR", f'"powershell.exe" -ExecutionPolicy Bypass -File "{script_path}"',
                "/SC", "ONLOGON",
                "/RL", "HIGHEST",
                "/F"  # Force replace if task exists
            ], check=True)
            print("✅ Scheduled task registered successfully.")
        except subprocess.CalledProcessError as e:
            print("⚠️ Failed to register scheduled task.")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")

    def create_service_runner(self):
        """Create a service runner script"""
        print("\nCreating service runner script...")
        
        # Create logs directory
        self.log_dir.mkdir(exist_ok=True)
        
        # Create the service runner script
        service_script = self.project_dir / "run_service.py"
        script_content = f'''
#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line
from waitress import serve

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{self.get_settings_module()}')
django.setup()

# Import your Django WSGI application
from {self.get_project_name()}.wsgi import application

if __name__ == '__main__':
    # Run with Waitress WSGI server
    print("Starting Django application with Waitress...")
    serve(application, host='0.0.0.0', port=8000)
'''
        
        with open(service_script, 'w') as f:
            f.write(script_content)
        
        print(f"Service runner created at {service_script}")
        return True

    def get_settings_module(self):
        """Try to determine the settings module name"""
        # Look for settings.py or common Django project structure
        possible_settings = [f"{self.get_project_name()}.settings", "settings","schoolmanager.settings"]
        
        # Check if manage.py exists and try to extract settings from it
        manage_py = self.project_dir / "manage.py"
        if manage_py.exists():
            try:
                with open(manage_py, 'r') as f:
                    content = f.read()
                    if 'DJANGO_SETTINGS_MODULE' in content:
                        # Extract the settings module from manage.py
                        import re
                        match = re.search(r"DJANGO_SETTINGS_MODULE['\"],\s*['\"]([^'\"]+)['\"]\)", content)
                        if match:
                            return match.group(1)
            except:
                pass
        
        return possible_settings[0]  # Default fallback

    def get_project_name(self):
        """Try to determine the project name"""
        # Look for the Django project directory
        for item in self.project_dir.iterdir():
            if item.is_dir() and (item / "wsgi.py").exists():
                return item.name
        
        # Fallback to directory name
        return self.project_dir.name

    def install_nssm_and_create_service(self):
        """Install NSSM and register the service"""
        print("\n Installing NSSM and setting up service...")

        # Check for NSSM
        nssm_path = str(self.project_dir / 'nssm' / 'win64' / 'nssm.exe')
        if not os.path.exists(nssm_path):
            print(f"NSSM not found at {nssm_path}. Please download and place it there.")
            return False

        try:
            result = subprocess.run([nssm_path, "remove", self.app_name, "confirm"], 
                                  check=False, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Removed existing {self.app_name} service")
            else:
                print(f"ℹ️ No existing service to remove")
        except Exception as e:
            print(f"⚠️ Error removing existing service: {e}")

        # Create service runner script
        if not self.create_service_runner():
            return False
   
        self.create_browser_watcher_task()

        service_script = str(self.project_dir / "run_service.py")
        
        # Set up the service using NSSM with better error handling
        try:
            # Install the service
            subprocess.run([nssm_path, "install", self.app_name, self.venv_path], check=True, capture_output=True, text=True)
            subprocess.run([nssm_path, "set", self.app_name, "AppParameters", f'"{service_script}"'], check=True, capture_output=True, text=True)

            print(f"Created {self.app_name} service with NSSM")
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to create the service with NSSM: {e}")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")
            return False
        
        # Configure service with individual error handling
        configurations = [
            ("AppDirectory", f'"{self.project_dir}"', "working directory"),
            ("Start", "SERVICE_AUTO_START", "auto-start"),
            ("AppStdout", str(self.log_dir / f"{self.app_name}.log"), "stdout logging"),
            ("AppStderr", str(self.log_dir / f"{self.app_name}_error.log"), "stderr logging"),
            ("Description", f"Django Application - {self.app_name}", "service description"),
            ("DisplayName", f"Django App - {self.app_name}", "display name"),
            ("AppStdoutCreationDisposition", "4", "stdout file creation"),
            ("AppStderrCreationDisposition", "4", "stderr file creation"),
            ("AppRotateFiles", "1", "log rotation"),
            ("AppRotateOnline", "1", "online log rotation"),
        ]
        
        for param, value, description in configurations:
            try:
                result = subprocess.run([nssm_path, "set", self.app_name, param, value], 
                                      check=True, capture_output=True, text=True)
                print(f"Set {description}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to set {description}: {e}")
                # Continue with other configurations even if one fails
                if e.stdout:
                    print(f"   STDOUT: {e.stdout}")
                if e.stderr:
                    print(f"   STDERR: {e.stderr}")
        
        return True

    def test_service_manually(self):
        """Test the service script manually before starting as a service"""
        print(f"\n🧪 Testing service script manually...")
        
        service_script = self.project_dir / "run_service.py"
        if not service_script.exists():
            print(f"Service script not found at {service_script}")
            return False
        
        try:
            # Test the script for 10 seconds
            print("Testing script (will timeout after 10 seconds)...")
            result = subprocess.run([self.venv_path, str(service_script)], 
                                  cwd=str(self.project_dir),
                                  timeout=10, 
                                  capture_output=True, 
                                  text=True)
            
        except subprocess.TimeoutExpired:
            print("Script started successfully (timed out as expected)")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Script failed to start: {e}")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")
            return False
        except Exception as e:
            print(f"Unexpected error testing script: {e}")
            return False
        
        return True

    def check_service_status(self):
        """Check the current status of the service"""
        print(f"\n📊 Checking service status...")
        
        try:
            result = subprocess.run(['sc', 'query', self.app_name], 
                                  capture_output=True, text=True, check=True)
            
            if "RUNNING" in result.stdout:
                print(f"Service is RUNNING")
                return True
            elif "STOPPED" in result.stdout:
                print(f"⚠️ Service is STOPPED")
                return False
            elif "START_PENDING" in result.stdout:
                print(f"🔄 Service is START_PENDING")
                return False
            else:
                print(f"❓ Service status unknown")
                print(f"Status output: {result.stdout}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"Failed to check service status: {e}")
            return False

    def run_installation(self):
        """Run the complete installation process"""
        self.print_header()

        # Step-by-step installation
        if not self.install_dependencies():
            print("\nInstallation failed at step: Installing dependencies")
            return False
        
        if not self.collect_static():
            print("\nInstallation failed at step: Collecting static files")
            return False

        if not self.install_nssm_and_create_service():
            print("\nInstallation failed at step: Installing NSSM and creating service")
            return False

        # Create troubleshooting script
        self.create_troubleshooting_script()

        # Don't fail the entire installation if service start fails
        # Instead, provide troubleshooting information
        service_started = self.start_service()
        
        if service_started:
            print("\n🎉 INSTALLATION COMPLETED SUCCESSFULLY! 🎉")
            print(f"Your Django app is now running as a service!")
            print(f"📋 Service name: {self.app_name}")
            print(f"🌐 Access your app at: http://localhost:8000")
            print(f"📝 Check logs at: {self.log_dir}")
            print(f"🔧 Manage service with: sc start/stop/query {self.app_name}")
        else:
            print("\n⚠️ INSTALLATION COMPLETED WITH WARNINGS ⚠️")
            print(f"Service was created but failed to start automatically.")
            print(f"📋 Service name: {self.app_name}")
            print(f"📝 Check logs at: {self.log_dir}")
            print("\n🔧 Manual troubleshooting steps:")
            print(f"1. Test script manually: python {self.project_dir}/run_service.py")
            print(f"2. Check Django settings: python manage.py check --deploy")
            print(f"3. Check database: python manage.py migrate")
            print(f"4. Try starting service: sc start {self.app_name}")
            print(f"5. Check service logs in: {self.log_dir}")
            print(f"6. Check Windows Event Viewer for service errors")
            
        return True

    def create_troubleshooting_script(self):
        """Create a troubleshooting script for the user"""
        troubleshoot_script = self.project_dir / "troubleshoot_service.py"
        
        script_content = f'''#!/usr/bin/env python3
"""
Troubleshooting script for {self.app_name} Django service
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
        print(f"Error testing Django: {{e}}")

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
        print(f"Error testing database: {{e}}")

def test_service_script():
    """Test the service script"""
    print("Testing service script...")
    try:
        result = subprocess.run([self.venv_path, "run_service.py"], 
                              timeout=10, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        print("Service script started successfully")
    except Exception as e:
        print(f"Service script failed: {{e}}")

def check_service_status():
    """Check service status"""
    print("Checking service status...")
    try:
        result = subprocess.run(["sc", "query", "{self.app_name}"], 
                              capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error checking service: {{e}}")

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
    
    print("\\n" + "="*50)
    print("Troubleshooting complete!")
    print("="*50)

if __name__ == "__main__":
    main()
'''
        
        with open(troubleshoot_script, 'w') as f:
            f.write(script_content)
        
        print(f"📋 Created troubleshooting script: {troubleshoot_script}")
        return True

def main():
    installer = AppInstaller()
    try:
        success = installer.run_installation()
        if not success:
            print("\nInstallation failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during installation: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()