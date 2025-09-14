#!/usr/bin/env python3
"""
Platform-Independent Automated Schema Matcher Runner
Runs the schema matcher with proper error handling, logging, and notifications
Works on Linux, macOS, and Windows
"""

import os
import sys
import json
import yaml
import logging
import subprocess
import smtplib
import platform
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
import argparse

class AutomationRunner:
    """Handles automated execution of schema matcher"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.script_dir = Path(__file__).parent
        self.project_dir = self.script_dir.parent
        self.config_file = config_file or self.project_dir / "config" / "schema_matcher_config.yaml"
        
        # Load configuration
        self.config = self.load_config()
        
        # Set up directories
        self.setup_directories()
        
        # Set up logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Default configuration if file doesn't exist
            return {
                'scan_directories': [str(self.project_dir / "data")],
                'output': {
                    'format': 'all',
                    'directory': str(self.project_dir / "reports"),
                    'filename_template': 'schema_matches_{timestamp}'
                },
                'logging': {
                    'level': 'INFO',
                    'file': str(self.project_dir / "logs" / "automation.log"),
                    'console_logging': False
                },
                'notifications': {
                    'email': {'enabled': False}
                },
                'matching': {
                    'similarity_threshold': 0.6
                },
                'performance': {
                    'timeout_seconds': 300
                }
            }
    
    def setup_directories(self):
        """Create necessary directories"""
        directories = [
            self.project_dir / "logs",
            self.project_dir / "reports",
            Path(self.config.get('output', {}).get('directory', self.project_dir / "reports"))
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def setup_logging(self):
        """Set up logging configuration"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_file = Path(log_config.get('file', self.project_dir / "logs" / "automation.log"))
        console_logging = log_config.get('console_logging', False)
        
        # Create log directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        handlers = [logging.FileHandler(log_file, encoding='utf-8')]
        
        if console_logging:
            handlers.append(logging.StreamHandler(sys.stdout))
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        missing_deps = []
        
        # Check Python executable
        if not sys.executable:
            missing_deps.append("Python interpreter")
        
        # Check required Python packages
        required_packages = ['pandas', 'psycopg2', 'pymongo', 'yaml']
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_deps.append(f"Python package: {package}")
        
        # Check schema matcher script
        schema_script = self.project_dir / "scripts" / "schema_matcher.py"
        if not schema_script.exists():
            missing_deps.append(f"Schema matcher script: {schema_script}")
        
        if missing_deps:
            self.logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
            self.send_notification(
                "Schema Matcher Error - Missing Dependencies",
                f"The following dependencies are missing:\n\n" + "\n".join(f"- {dep}" for dep in missing_deps)
            )
            return False
        
        return True
    
    def send_notification(self, subject: str, body: str):
        """Send email notification if configured"""
        email_config = self.config.get('notifications', {}).get('email', {})
        
        if not email_config.get('enabled', False):
            return
        
        try:
            # Get email configuration
            smtp_server = email_config.get('smtp_server', 'localhost')
            smtp_port = email_config.get('smtp_port', 587)
            username = email_config.get('username', '')
            password = os.getenv('EMAIL_PASSWORD', email_config.get('password', ''))
            from_address = email_config.get('from_address', 'schema-matcher@localhost')
            to_addresses = email_config.get('to_addresses', [])
            
            if not to_addresses:
                self.logger.warning("No email recipients configured")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_address
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = subject
            
            # Add system info to body
            system_info = f"\n\nSystem Info:\n"
            system_info += f"- Platform: {platform.system()} {platform.release()}\n"
            system_info += f"- Python: {sys.version}\n"
            system_info += f"- Timestamp: {datetime.now().isoformat()}\n"
            
            body_with_info = body + system_info
            msg.attach(MIMEText(body_with_info, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if username and password:
                    server.starttls()
                    server.login(username, password)
                
                server.send_message(msg)
            
            self.logger.info(f"Email notification sent: {subject}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
    
    def run_schema_matcher(self, directory: str) -> bool:
        """Run schema matcher for a specific directory"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_template = self.config.get('output', {}).get('filename_template', 'schema_matches_{timestamp}')
        output_filename = output_template.format(timestamp=timestamp)
        
        output_dir = Path(self.config.get('output', {}).get('directory', self.project_dir / "reports"))
        output_file = output_dir / f"{output_filename}.json"
        
        # Schema matcher script path
        schema_script = self.project_dir / "scripts" / "schema_matcher.py"
        
        self.logger.info(f"Starting schema matching for directory: {directory}")
        self.logger.info(f"Output file: {output_file}")
        
        # Build command
        cmd = [
            sys.executable,
            str(schema_script),
            directory,
            '--output-format', self.config.get('output', {}).get('format', 'all'),
            '--output-file', str(output_file),
            '--similarity-threshold', str(self.config.get('matching', {}).get('similarity_threshold', 0.6)),
            '--log-level', self.config.get('logging', {}).get('level', 'INFO'),
            '--log-file', str(Path(self.config.get('logging', {}).get('file', self.project_dir / "logs" / "schema_matcher.log"))),
            '--no-console-logging'
        ]
        
        try:
            # Run with timeout
            timeout = self.config.get('performance', {}).get('timeout_seconds', 300)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_dir)
            )
            
            if result.returncode == 0:
                self.logger.info("Schema matching completed successfully")
                
                # Check results
                match_count = self.count_matches(output_file)
                self.logger.info(f"Found {match_count} total schema matches")
                
                if match_count > 0:
                    self.send_notification(
                        "Schema Matcher Success",
                        f"Schema matching completed successfully with {match_count} matches found.\n"
                        f"Directory: {directory}\n"
                        f"Report: {output_file}"
                    )
                else:
                    self.logger.warning("No schema matches found")
                    if self.config.get('notifications', {}).get('email', {}).get('send_on_no_matches', False):
                        self.send_notification(
                            "Schema Matcher - No Matches Found",
                            f"Schema matching completed but no matches were found.\n"
                            f"Directory: {directory}"
                        )
                
                return True
            else:
                error_msg = f"Schema matching failed with exit code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nError output: {result.stderr}"
                
                self.logger.error(error_msg)
                
                if self.config.get('notifications', {}).get('email', {}).get('send_on_errors', True):
                    self.send_notification(
                        "Schema Matcher Error",
                        f"Schema matching failed for directory: {directory}\n\n"
                        f"Exit code: {result.returncode}\n"
                        f"Error: {result.stderr or 'No error details available'}"
                    )
                
                return False
                
        except subprocess.TimeoutExpired:
            error_msg = f"Schema matching timed out after {timeout} seconds"
            self.logger.error(error_msg)
            self.send_notification("Schema Matcher Timeout", error_msg)
            return False
        except Exception as e:
            error_msg = f"Unexpected error running schema matcher: {e}"
            self.logger.error(error_msg)
            self.send_notification("Schema Matcher Error", error_msg)
            return False
    
    def count_matches(self, output_file: Path) -> int:
        """Count the number of matches in the output file"""
        try:
            if not output_file.exists():
                return 0
            
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            total_matches = 0
            for file_info in data.get('matches', {}).values():
                total_matches += len(file_info.get('potential_matches', []))
            
            return total_matches
        except Exception as e:
            self.logger.warning(f"Could not count matches in {output_file}: {e}")
            return 0
    
    def run(self, directories: Optional[List[str]] = None) -> bool:
        """Run automated schema matching"""
        self.logger.info("=== Starting Automated Schema Matcher ===")
        self.logger.info(f"Platform: {platform.system()} {platform.release()}")
        self.logger.info(f"Python: {sys.version}")
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Use provided directories or default from config
        if not directories:
            directories = self.config.get('scan_directories', [str(self.project_dir / "data")])
        
        # Process each directory
        overall_success = True
        processed_dirs = 0
        
        for directory in directories:
            dir_path = Path(directory)
            if dir_path.exists() and dir_path.is_dir():
                self.logger.info(f"Processing directory: {directory}")
                if not self.run_schema_matcher(directory):
                    overall_success = False
                processed_dirs += 1
            else:
                self.logger.warning(f"Directory not found or not accessible: {directory}")
        
        # Final status
        if overall_success and processed_dirs > 0:
            self.logger.info("=== Automated Schema Matcher completed successfully ===")
            return True
        else:
            self.logger.error("=== Automated Schema Matcher completed with errors ===")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Automated Schema Matcher Runner')
    parser.add_argument('directories', nargs='*', 
                       help='Directories to scan (default: from config file)')
    parser.add_argument('--config', '-c', 
                       help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose console output')
    
    args = parser.parse_args()
    
    try:
        # Create runner
        runner = AutomationRunner(args.config)
        
        # Enable console logging if verbose
        if args.verbose:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logging.getLogger().addHandler(console_handler)
        
        # Run automation
        success = runner.run(args.directories)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nAutomation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()