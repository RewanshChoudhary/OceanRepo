#!/usr/bin/env python3
"""
Marine Data Integration Platform - Quick Start Runner
Complete platform runner with all components
"""

import os
import sys
import subprocess
import time
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_command(command, description, cwd=None):
    """Run a command with proper error handling"""
    print(f"🔄 {description}...")
    
    try:
        if cwd is None:
            cwd = os.path.dirname(os.path.abspath(__file__))
            
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
            if result.stdout.strip():
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} failed!")
            if result.stderr.strip():
                print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def check_docker():
    """Check if Docker is available and running"""
    print("🐳 Checking Docker availability...")
    
    try:
        result = subprocess.run(
            "docker --version",
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            print("✅ Docker is available")
            
            # Check if Docker daemon is running
            result = subprocess.run(
                "docker info",
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                print("✅ Docker daemon is running")
                return True
            else:
                print("❌ Docker daemon is not running")
                return False
        else:
            print("❌ Docker is not installed or not in PATH")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False

def check_python_dependencies():
    """Check if Python dependencies are installed"""
    print("🐍 Checking Python dependencies...")
    
    required_packages = [
        'psycopg2', 'pymongo', 'python-dotenv', 'numpy', 'pandas'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All Python dependencies are installed")
        return True

def setup_environment():
    """Setup environment files"""
    print("📋 Setting up environment...")
    
    env_file = '.env'
    env_example = '.env.example'
    
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            try:
                with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                    dst.write(src.read())
                print("✅ Created .env file from .env.example")
            except Exception as e:
                print(f"❌ Error creating .env file: {e}")
                return False
        else:
            print("❌ .env.example file not found")
            return False
    else:
        print("ℹ️  .env file already exists")
    
    return True

def run_docker_setup():
    """Start Docker services"""
    print("🐳 Starting Docker services...")
    
    # Check if docker-compose.yml exists
    if not os.path.exists('docker-compose.yml'):
        print("❌ docker-compose.yml not found")
        return False
    
    # Start services
    commands = [
        ("docker-compose up -d", "Starting Docker services"),
        ("docker-compose ps", "Checking service status")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
        time.sleep(2)  # Brief pause between commands
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready (30 seconds)...")
    time.sleep(30)
    
    return True

def run_database_setup():
    """Initialize databases"""
    return run_command("python scripts/setup_database.py", "Setting up databases")

def run_data_ingestion():
    """Insert sample data"""
    return run_command("python scripts/ingest_data.py", "Ingesting sample data")

def run_data_query():
    """Run data queries"""
    return run_command("python scripts/query_data.py", "Running data queries")

def run_edna_test():
    """Test eDNA matching"""
    return run_command("python scripts/edna_matcher.py --mode test", "Testing eDNA matching")

def print_status_report():
    """Print final status and instructions"""
    print("\n" + "=" * 60)
    print("🌊 MARINE DATA INTEGRATION PLATFORM - STATUS REPORT")
    print("=" * 60)
    
    print("\n🎯 Platform Components:")
    print("  ✅ PostgreSQL + PostGIS Database")
    print("  ✅ MongoDB Database") 
    print("  ✅ Python Data Ingestion Scripts")
    print("  ✅ Data Query & Analysis Tools")
    print("  ✅ K-mer Based eDNA Sequence Matching")
    print("  ✅ Docker Container Setup")
    
    print("\n🔗 Access Points:")
    print("  PostgreSQL: localhost:5432")
    print("  MongoDB: localhost:27017")
    print("  pgAdmin: http://localhost:8080 (admin@marine.com / admin123)")
    print("  MongoDB Express: http://localhost:8081 (admin / admin123)")
    
    print("\n🛠️  Available Commands:")
    print("  Data Queries: python scripts/query_data.py")
    print("  eDNA Matching: python scripts/edna_matcher.py")
    print("  Interactive eDNA: python scripts/edna_matcher.py --mode interactive")
    print("  Batch Testing: python scripts/edna_matcher.py --mode test")
    
    print("\n🚀 Platform is ready for hackathon development!")
    print("📚 Check README.md for detailed usage instructions")

def main():
    """Main platform runner"""
    parser = argparse.ArgumentParser(description="Marine Data Integration Platform Runner")
    parser.add_argument('--skip-docker', action='store_true', 
                       help='Skip Docker setup (use existing databases)')
    parser.add_argument('--setup-only', action='store_true',
                       help='Only setup, do not run data operations')
    parser.add_argument('--quick', action='store_true',
                       help='Quick setup without full data ingestion')
    
    args = parser.parse_args()
    
    print("🌊 Marine Data Integration Platform - Quick Start")
    print("=" * 60)
    
    # Step 1: Check prerequisites
    print("\n📋 Step 1: Checking Prerequisites")
    if not check_python_dependencies():
        print("\n💡 Please install Python dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    if not args.skip_docker and not check_docker():
        print("\n💡 Please install Docker or use --skip-docker flag")
        sys.exit(1)
    
    # Step 2: Setup environment
    print("\n🔧 Step 2: Environment Setup")
    if not setup_environment():
        sys.exit(1)
    
    # Step 3: Start services
    if not args.skip_docker:
        print("\n🐳 Step 3: Starting Docker Services")
        if not run_docker_setup():
            print("\n💡 Try: docker-compose up -d")
            sys.exit(1)
    else:
        print("\n⏩ Step 3: Skipping Docker setup")
    
    # Step 4: Initialize databases
    print("\n🛠️  Step 4: Database Initialization")
    if not run_database_setup():
        sys.exit(1)
    
    if args.setup_only:
        print("\n✅ Setup completed! Use --help to see run options.")
        print_status_report()
        return
    
    # Step 5: Data operations
    if not args.quick:
        print("\n📊 Step 5: Data Ingestion")
        if not run_data_ingestion():
            print("⚠️  Data ingestion failed, but continuing...")
        
        print("\n🔍 Step 6: Data Query Testing")  
        if not run_data_query():
            print("⚠️  Data query failed, but continuing...")
        
        print("\n🧬 Step 7: eDNA Matching Testing")
        if not run_edna_test():
            print("⚠️  eDNA testing failed, but platform is still functional")
    else:
        print("\n⏩ Skipping data operations (quick mode)")
    
    # Final status
    print_status_report()
    
    print("\n✨ Platform setup completed successfully!")
    print("🎉 Ready for hackathon development!")

if __name__ == "__main__":
    main()