import os
import subprocess
import sys
import platform
import argparse
from pathlib import Path


class DjangoServiceManager:
    def __init__(self):
        self.project_dir = Path(__file__).resolve().parent
        self.app_name = "sms004"
        self.log_dir = self.project_dir / "logs"
        self.venv_path = self.project_dir / "venv" / "Scripts" / "python.exe"
        self.nssm_path = self.project_dir / 'nssm' / 'win64' / 'nssm.exe'

    def print_header(self, operation="Installation"):
        """Print operation header"""
        print("="*60)
        print(f"     Django Application {operation} Script")
        print("         Using NSSM for Windows Service")
        print("="*60)
        print(f"Operating System: {platform.system()} {platform.release()}")
        print(f"Python Version: {sys.version.split()[0]}")
        print(f"Project Directory: {self.project_dir}")
        print("-"*60)

    def check_environment(self):
        """Check if virtual environment and required files exist"""
        print("\n🔍 Checking environment...")

        # Check virtual environment
        if not self.venv_path.exists():
            print(f"❌ Virtual environment not found at: {self.venv_path}")
            print("Please create a virtual environment first:")
            print(f"  python -m venv venv")
            return False
        print(f"✅ Virtual environment found")

        # Check NSSM
        if not self.nssm_path.exists():
            print(f"❌ NSSM not found at: {self.nssm_path}")
            print("Please download NSSM and place it in the nssm/win64/ directory")
            return False
        print(f"✅ NSSM found")

        # Check manage.py
        manage_py = self.project_dir / "manage.py"
        if not manage_py.exists():
            print(f"❌ manage.py not found. Are you in a Django project directory?")
            return False
        print(f"✅ Django project detected")

        return True

    def install_requirements(self):
        """Install dependencies from requirements.txt or fallback to basic ones"""
        print("\n📦 Installing Python dependencies...")

        requirements_file = self.project_dir / "requirements.txt"
        
        if requirements_file.exists():
            print(f"Found requirements.txt, installing from file...")
            try:
                subprocess.run([self.venv_path, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                             cwd=str(self.project_dir), check=True, capture_output=True)
                print("✅ Requirements installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install requirements: {e}")
                if e.stdout:
                    print(f"STDOUT: {e.stdout}")
                if e.stderr:
                    print(f"STDERR: {e.stderr}")
                return False
        else:
            print("No requirements.txt found, installing basic dependencies...")
            dependencies = ['django', 'waitress']
            for dep in dependencies:
                try:
                    print(f"Installing {dep}...")
                    subprocess.run([self.venv_path, '-m', 'pip', 'install', dep], 
                                 check=True, capture_output=True)
                    print(f"✅ {dep} installed successfully")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to install {dep}: {e}")
                    return False

        return True

    def run_migrations(self):
        """Run Django database migrations"""
        print("\n🗄️ Running database migrations...")
        
        try:
            # First, make migrations in case there are new ones
            print("Creating migrations...")
            subprocess.run([self.venv_path, 'manage.py', 'makemigrations'], 
                          cwd=str(self.project_dir), check=True, capture_output=True)
            
            # Run migrations
            print("Applying migrations...")
            result = subprocess.run([self.venv_path, 'manage.py', 'migrate'], 
                                  cwd=str(self.project_dir), check=True, capture_output=True, text=True)
            print("✅ Database migrations completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to run migrations: {e}")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")
            return False

    def collect_static(self):
        """Collect static files"""
        print("\n📂 Collecting static files...")

        try:
            subprocess.run([self.venv_path, 'manage.py', 'collectstatic', '--noinput'], 
                          cwd=str(self.project_dir), check=True, capture_output=True)
            print("✅ Static files collected successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to collect static files: {e}")
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
            ], check=True, capture_output=True)
            print("✅ Scheduled task registered successfully.")
        except subprocess.CalledProcessError as e:
            print("⚠️ Failed to register scheduled task.")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")

    def create_service_runner(self):
        """Create a service runner script"""
        print("\n🔧 Creating service runner script...")
        
        # Create logs directory
        self.log_dir.mkdir(exist_ok=True)
        
        # Create the service runner script
        service_script = self.project_dir / "run_service.py"
        script_content = f'''#!/usr/bin/env python
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
        
        print(f"✅ Service runner created at {service_script}")
        return True

    def get_settings_module(self):
        """Try to determine the settings module name"""
        # Look for settings.py or common Django project structure
        possible_settings = [f"{self.get_project_name()}.settings", "settings", "schoolmanager.settings"]
        
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

    def remove_existing_service(self):
        """Remove existing service if it exists"""
        try:
            result = subprocess.run([str(self.nssm_path), "remove", self.app_name, "confirm"], 
                                  check=False, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Removed existing {self.app_name} service")
                return True
            else:
                print(f"ℹ️ No existing service to remove")
                return True
        except Exception as e:
            print(f"⚠️ Error removing existing service: {e}")
            return False

    def create_service(self):
        """Create the Windows service using NSSM"""
        print(f"\n🔧 Creating Windows service '{self.app_name}'...")

        # Remove existing service first
        self.remove_existing_service()

        # Create service runner script
        if not self.create_service_runner():
            return False
   
        # Create browser watcher task
        self.create_browser_watcher_task()

        service_script = str(self.project_dir / "run_service.py")
        
        # Set up the service using NSSM
        try:
            # Install the service
            subprocess.run([str(self.nssm_path), "install", self.app_name, str(self.venv_path)], 
                          check=True, capture_output=True, text=True)
            subprocess.run([str(self.nssm_path), "set", self.app_name, "AppParameters", f'"{service_script}"'], 
                          check=True, capture_output=True, text=True)

            print(f"✅ Created {self.app_name} service with NSSM")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create the service with NSSM: {e}")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")
            return False
        
        # Configure service
        configurations = [
            ("AppDirectory", f'"{self.project_dir}"', "working directory"),
            ("Start", "SERVICE_AUTO_START", "auto-start"),
            ("AppStdout", str(self.log_dir / f"{self.app_name}.log"), "stdout logging"),
            ("AppStderr", str(self.log_dir / f"{self.app_name}_error.log"), "stderr logging"),
            ("Description", f"Django School Management System - {self.app_name}", "service description"),
            ("DisplayName", f"Django SMS - {self.app_name}", "display name"),
            ("AppStdoutCreationDisposition", "4", "stdout file creation"),
            ("AppStderrCreationDisposition", "4", "stderr file creation"),
            ("AppRotateFiles", "1", "log rotation"),
            ("AppRotateOnline", "1", "online log rotation"),
        ]
        
        for param, value, description in configurations:
            try:
                subprocess.run([str(self.nssm_path), "set", self.app_name, param, value], 
                              check=True, capture_output=True, text=True)
                print(f"✅ Set {description}")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Failed to set {description}: {e}")
        
        return True

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

    def stop_service(self):
        """Stop the Windows service"""
        print(f"\n⏹️ Stopping service '{self.app_name}'...")

        try:
            result = subprocess.run(['sc', 'stop', self.app_name], capture_output=True, text=True, check=True)
            if "STOP_PENDING" in result.stdout or "STOPPED" in result.stdout:
                print("✅ Service stopped successfully")
                return True
            else:
                print("⚠️ Service did not stop as expected")
                print(result.stdout)
                return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to stop service: {e}")
            return False

    def check_service_status(self):
        """Check the current status of the service"""
        print(f"\n📊 Checking service status...")
        
        try:
            result = subprocess.run(['sc', 'query', self.app_name], 
                                  capture_output=True, text=True, check=True)
            
            if "RUNNING" in result.stdout:
                print(f"✅ Service is RUNNING")
                return "RUNNING"
            elif "STOPPED" in result.stdout:
                print(f"⚠️ Service is STOPPED")
                return "STOPPED"
            elif "START_PENDING" in result.stdout:
                print(f"🔄 Service is START_PENDING")
                return "START_PENDING"
            else:
                print(f"❓ Service status unknown")
                print(f"Status output: {result.stdout}")
                return "UNKNOWN"
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Service does not exist or failed to check status")
            return "NOT_EXISTS"

    def install(self):
        """Run the complete installation process"""
        self.print_header("Installation")

        # Environment checks
        if not self.check_environment():
            print("\n❌ Environment check failed. Installation aborted.")
            return False

        # Step-by-step installation
        steps = [
            ("Installing dependencies", self.install_requirements),
            ("Running database migrations", self.run_migrations),
            ("Collecting static files", self.collect_static),
            ("Creating Windows service", self.create_service),
        ]

        for step_name, step_func in steps:
            print(f"\n{'='*20} {step_name} {'='*20}")
            if not step_func():
                print(f"\n❌ Installation failed at step: {step_name}")
                return False

        # Try to start service
        service_started = self.start_service()
        
        if service_started:
            print("\n🎉 INSTALLATION COMPLETED SUCCESSFULLY! 🎉")
            print(f"✅ Your Django School Management System is now running as a service!")
            print(f"📋 Service name: {self.app_name}")
            print(f"🌐 Access your app at: http://localhost:8000")
            print(f"🌐 Or from network at: http://[YOUR-IP]:8000")
            print(f"📝 Check logs at: {self.log_dir}")
            print(f"🔧 Manage service with: sc start/stop/query {self.app_name}")
        else:
            print("\n⚠️ INSTALLATION COMPLETED WITH WARNINGS ⚠️")
            print(f"Service was created but failed to start automatically.")
            print(f"Try: sc start {self.app_name}")
            
        return True

    def uninstall(self):
        """Completely remove the service and related components"""
        self.print_header("Uninstallation")
        
        print("🗑️ Starting uninstallation process...")

        # Stop service first
        status = self.check_service_status()
        if status == "RUNNING":
            self.stop_service()

        # Remove service
        if status != "NOT_EXISTS":
            try:
                result = subprocess.run([str(self.nssm_path), "remove", self.app_name, "confirm"], 
                                      check=True, capture_output=True, text=True)
                print(f"✅ Removed Windows service '{self.app_name}'")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Failed to remove service: {e}")

        # Remove scheduled task
        try:
            subprocess.run(["schtasks", "/Delete", "/TN", "OpenSMSBrowser", "/F"], 
                          check=True, capture_output=True)
            print("✅ Removed browser auto-launch scheduled task")
        except subprocess.CalledProcessError:
            print("ℹ️ No scheduled task to remove")

        # Remove created files
        files_to_remove = [
            self.project_dir / "run_service.py",
            self.project_dir / "open_sms_in_browser.ps1",
            self.project_dir / "troubleshoot_service.py"
        ]

        for file_path in files_to_remove:
            try:
                if file_path.exists():
                    file_path.unlink()
                    print(f"✅ Removed {file_path.name}")
            except Exception as e:
                print(f"⚠️ Failed to remove {file_path.name}: {e}")

        # Ask about logs
        try:
            keep_logs = input("\n🗂️ Keep log files? (y/N): ").strip().lower()
            if keep_logs != 'y':
                if self.log_dir.exists():
                    import shutil
                    shutil.rmtree(self.log_dir)
                    print("✅ Removed log directory")
        except KeyboardInterrupt:
            print("\nKeeping log files...")

        print("\n✅ UNINSTALLATION COMPLETED!")
        print("The Django service has been completely removed.")
        return True

    def update(self):
        """Update the service with new code changes"""
        self.print_header("Update")
        
        print("🔄 Starting update process...")

        # Check if service exists
        status = self.check_service_status()
        if status == "NOT_EXISTS":
            print("❌ Service doesn't exist. Please install first.")
            return False

        # Stop service
        if status == "RUNNING":
            if not self.stop_service():
                print("⚠️ Failed to stop service, continuing anyway...")

        # Update steps
        steps = [
            ("Installing/updating dependencies", self.install_requirements),
            ("Running database migrations", self.run_migrations),
            ("Collecting static files", self.collect_static),
            ("Updating service runner", self.create_service_runner),
        ]

        for step_name, step_func in steps:
            print(f"\n{'='*15} {step_name} {'='*15}")
            if not step_func():
                print(f"\n❌ Update failed at step: {step_name}")
                return False

        # Restart service
        if not self.start_service():
            print("⚠️ Failed to restart service after update")
            print("Try manually: sc start", self.app_name)
            return False

        print("\n🎉 UPDATE COMPLETED SUCCESSFULLY! 🎉")
        print("Your Django service has been updated and restarted.")
        return True


def main():
    parser = argparse.ArgumentParser(description='Django Service Manager')
    parser.add_argument('action', choices=['install', 'uninstall', 'update', 'status'], 
                       help='Action to perform')
    
    # If no arguments provided, default to install
    if len(sys.argv) == 1:
        sys.argv.append('install')
    
    args = parser.parse_args()
    
    manager = DjangoServiceManager()
    
    try:
        if args.action == 'install':
            success = manager.install()
        elif args.action == 'uninstall':
            success = manager.uninstall()
        elif args.action == 'update':
            success = manager.update()
        elif args.action == 'status':
            manager.check_service_status()
            success = True
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n👋 {args.action.title()} interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during {args.action}: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()