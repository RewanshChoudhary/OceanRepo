#!/usr/bin/env python3
"""
Platform-Independent Scheduler for Schema Matcher
Handles scheduling of automated schema matching across different platforms
Supports cron-like scheduling without requiring cron or systemd
"""

import os
import sys
import time
import threading
import platform
import signal
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import argparse
import subprocess
from croniter import croniter

class PlatformScheduler:
    """Cross-platform scheduler for automated tasks"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.script_dir = Path(__file__).parent
        self.project_dir = self.script_dir.parent
        self.config_file = config_file or self.project_dir / "config" / "schema_matcher_config.yaml"
        
        # Load configuration
        self.config = self.load_config()
        
        # Set up logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Scheduler state
        self.running = False
        self.scheduler_thread = None
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_file}")
            return self.get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'scheduling': {
                'enabled': True,
                'cron_schedule': '0 2 * * *'  # Daily at 2 AM
            },
            'logging': {
                'level': 'INFO',
                'file': str(self.project_dir / "logs" / "scheduler.log")
            }
        }
    
    def setup_logging(self):
        """Set up logging"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_file = Path(log_config.get('file', self.project_dir / "logs" / "scheduler.log"))
        
        # Create log directory
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def parse_cron_schedule(self, cron_expr: str) -> croniter:
        """Parse cron expression and return croniter object"""
        try:
            return croniter(cron_expr, datetime.now())
        except Exception as e:
            self.logger.error(f"Invalid cron expression '{cron_expr}': {e}")
            # Default to daily at 2 AM
            return croniter('0 2 * * *', datetime.now())
    
    def get_next_run_time(self, cron_expr: str) -> datetime:
        """Get next scheduled run time"""
        cron = self.parse_cron_schedule(cron_expr)
        return cron.get_next(datetime)
    
    def run_schema_matcher(self) -> bool:
        """Execute schema matcher"""
        automation_script = self.script_dir / "run_schema_matcher.py"
        
        if not automation_script.exists():
            self.logger.error(f"Automation script not found: {automation_script}")
            return False
        
        self.logger.info("Executing scheduled schema matching...")
        
        try:
            # Run the automation script
            result = subprocess.run([
                sys.executable,
                str(automation_script),
                '--config', str(self.config_file)
            ], capture_output=True, text=True, cwd=str(self.project_dir))
            
            if result.returncode == 0:
                self.logger.info("Scheduled schema matching completed successfully")
                return True
            else:
                self.logger.error(f"Schema matching failed with exit code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Error output: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing schema matcher: {e}")
            return False
    
    def scheduler_loop(self, cron_expr: str):
        """Main scheduler loop"""
        self.logger.info(f"Scheduler started with cron expression: {cron_expr}")
        self.logger.info(f"Platform: {platform.system()} {platform.release()}")
        
        cron = self.parse_cron_schedule(cron_expr)
        
        while self.running:
            try:
                # Get next run time
                next_run = cron.get_next(datetime)
                self.logger.info(f"Next scheduled run: {next_run}")
                
                # Wait until next run time
                while self.running:
                    now = datetime.now()
                    if now >= next_run:
                        break
                    
                    # Sleep for short intervals to allow graceful shutdown
                    sleep_time = min(60, (next_run - now).total_seconds())
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                
                if not self.running:
                    break
                
                # Execute the schema matcher
                self.logger.info("=== Scheduled execution starting ===")
                success = self.run_schema_matcher()
                
                if success:
                    self.logger.info("=== Scheduled execution completed successfully ===")
                else:
                    self.logger.error("=== Scheduled execution failed ===")
                
                # Move to next iteration
                cron = self.parse_cron_schedule(cron_expr)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                # Wait before retrying
                time.sleep(60)
    
    def start(self):
        """Start the scheduler"""
        scheduling_config = self.config.get('scheduling', {})
        
        if not scheduling_config.get('enabled', True):
            self.logger.info("Scheduling is disabled in configuration")
            return False
        
        cron_expr = scheduling_config.get('cron_schedule', '0 2 * * *')
        
        if self.running:
            self.logger.warning("Scheduler is already running")
            return False
        
        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self.scheduler_loop,
            args=(cron_expr,),
            daemon=True
        )
        self.scheduler_thread.start()
        
        self.logger.info("Scheduler started successfully")
        return True
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
        
        self.logger.info("Stopping scheduler...")
        self.running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Scheduler stopped")
    
    def status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        scheduling_config = self.config.get('scheduling', {})
        cron_expr = scheduling_config.get('cron_schedule', '0 2 * * *')
        
        status = {
            'running': self.running,
            'enabled': scheduling_config.get('enabled', True),
            'cron_schedule': cron_expr,
            'platform': f"{platform.system()} {platform.release()}",
            'config_file': str(self.config_file)
        }
        
        if status['enabled']:
            try:
                next_run = self.get_next_run_time(cron_expr)
                status['next_run'] = next_run.isoformat()
            except Exception as e:
                status['error'] = str(e)
        
        return status

def install_system_service():
    """Install as system service (platform-specific)"""
    script_path = Path(__file__).absolute()
    project_dir = script_path.parent.parent
    
    system = platform.system().lower()
    
    if system == 'linux':
        install_systemd_service(script_path, project_dir)
    elif system == 'darwin':  # macOS
        install_launchd_service(script_path, project_dir)
    elif system == 'windows':
        install_windows_service(script_path, project_dir)
    else:
        print(f"Service installation not supported on {system}")
        return False
    
    return True

def install_systemd_service(script_path: Path, project_dir: Path):
    """Install systemd service on Linux"""
    service_content = f"""[Unit]
Description=Marine Data Schema Matcher Scheduler
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={project_dir}
ExecStart={sys.executable} {script_path} --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path("/etc/systemd/system/schema-matcher-scheduler.service")
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        # Reload systemd and enable service
        os.system("sudo systemctl daemon-reload")
        os.system("sudo systemctl enable schema-matcher-scheduler.service")
        
        print(f"Systemd service installed: {service_file}")
        print("Start with: sudo systemctl start schema-matcher-scheduler")
        print("Check status: sudo systemctl status schema-matcher-scheduler")
        
    except PermissionError:
        print("Error: Need sudo privileges to install systemd service")
        print(f"Try: sudo python3 {script_path} --install-service")

def install_launchd_service(script_path: Path, project_dir: Path):
    """Install launchd service on macOS"""
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.marine-platform.schema-matcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{script_path}</string>
        <string>--daemon</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{project_dir}</string>
    <key>KeepAlive</key>
    <true/>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
    
    plist_file = Path.home() / "Library/LaunchAgents/com.marine-platform.schema-matcher.plist"
    plist_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(plist_file, 'w') as f:
        f.write(plist_content)
    
    # Load the service
    os.system(f"launchctl load {plist_file}")
    
    print(f"LaunchAgent installed: {plist_file}")
    print(f"Start with: launchctl start com.marine-platform.schema-matcher")

def install_windows_service(script_path: Path, project_dir: Path):
    """Install Windows service"""
    print("Windows service installation requires additional dependencies.")
    print("Consider using Task Scheduler instead:")
    print(f"1. Open Task Scheduler")
    print(f"2. Create Basic Task")
    print(f"3. Set trigger as desired")
    print(f"4. Set action to start program: {sys.executable}")
    print(f"5. Add arguments: {script_path} --daemon")
    print(f"6. Set start in: {project_dir}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Schema Matcher Scheduler')
    parser.add_argument('--config', '-c', help='Path to configuration file')
    parser.add_argument('--daemon', '-d', action='store_true', help='Run as daemon')
    parser.add_argument('--status', '-s', action='store_true', help='Show status')
    parser.add_argument('--install-service', action='store_true', help='Install as system service')
    parser.add_argument('--run-once', action='store_true', help='Run schema matcher once and exit')
    
    args = parser.parse_args()
    
    try:
        if args.install_service:
            install_system_service()
            return
        
        scheduler = PlatformScheduler(args.config)
        
        if args.status:
            status = scheduler.status()
            print(json.dumps(status, indent=2))
            return
        
        if args.run_once:
            success = scheduler.run_schema_matcher()
            sys.exit(0 if success else 1)
        
        if args.daemon:
            # Set up signal handlers for graceful shutdown
            def signal_handler(signum, frame):
                scheduler.logger.info(f"Received signal {signum}, shutting down...")
                scheduler.stop()
                sys.exit(0)
            
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            
            # Start scheduler
            if scheduler.start():
                scheduler.logger.info("Scheduler running in daemon mode. Press Ctrl+C to stop.")
                try:
                    while scheduler.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    scheduler.logger.info("Keyboard interrupt received")
                finally:
                    scheduler.stop()
            else:
                sys.exit(1)
        else:
            print("Schema Matcher Scheduler")
            print("Use --daemon to run as daemon")
            print("Use --status to check status")
            print("Use --install-service to install as system service")
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()