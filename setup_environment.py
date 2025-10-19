#!/usr/bin/env python3
"""
Setup script for LMS API Backend
Creates virtual environment and installs dependencies
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr}")
        return False

def setup_virtual_environment():
    """Setup virtual environment and install dependencies"""
    
    print("🚀 Setting up LMS API Backend Environment")
    print("=" * 50)
    
    # Check if we're already in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Already in virtual environment")
        venv_path = sys.prefix
    else:
        # Create virtual environment
        venv_name = "lms_venv"
        if not run_command(f"python -m venv {venv_name}", "Creating virtual environment"):
            return False
        
        venv_path = Path(venv_name).absolute()
        print(f"📁 Virtual environment created at: {venv_path}")
        
        # Activation instructions
        if os.name == 'nt':  # Windows
            activate_script = venv_path / "Scripts" / "activate.bat"
            print(f"\n⚠️  Please activate the virtual environment manually:")
            print(f"   {activate_script}")
            print(f"   Then run this script again.")
            return False
        else:  # Unix/Linux/Mac
            activate_script = venv_path / "bin" / "activate"
            print(f"\n⚠️  Please activate the virtual environment manually:")
            print(f"   source {activate_script}")
            print(f"   Then run this script again.")
            return False
    
    # Install dependencies
    print("\n📦 Installing Python Dependencies")
    print("=" * 50)
    
    # Upgrade pip first
    if not run_command("python -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    # Install additional AWS dependencies
    if not run_command("pip install boto3-stubs[essential]", "Installing AWS type stubs"):
        print("⚠️  AWS type stubs installation failed (optional)")
    
    print("\n✅ Environment setup complete!")
    return True

def verify_installation():
    """Verify that all required packages are installed"""
    
    print("\n🧪 Verifying Installation")
    print("=" * 50)
    
    required_packages = [
        'boto3',
        'pinecone',
        'supabase',
        'fastapi',
        'pydantic',
        'python-dotenv'
    ]
    
    all_good = True
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Not installed")
            all_good = False
    
    return all_good

def check_aws_cli():
    """Check if AWS CLI is configured"""
    
    print("\n🔧 Checking AWS Configuration")
    print("=" * 50)
    
    try:
        result = subprocess.run("aws sts get-caller-identity", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ AWS CLI is configured")
            return True
        else:
            print("❌ AWS CLI not configured or no permissions")
            return False
    except:
        print("❌ AWS CLI not found")
        return False

def main():
    """Main setup function"""
    
    # Setup environment
    if not setup_virtual_environment():
        return
    
    # Verify installation
    if not verify_installation():
        print("\n❌ Some packages failed to install. Please check the errors above.")
        return
    
    # Check AWS CLI
    aws_ok = check_aws_cli()
    
    print("\n🎉 Setup Summary")
    print("=" * 50)
    print("✅ Virtual environment ready")
    print("✅ Python dependencies installed")
    print(f"{'✅' if aws_ok else '❌'} AWS CLI {'configured' if aws_ok else 'needs configuration'}")
    
    print("\n📋 Next Steps:")
    print("1. Run: python setup_pinecone.py")
    print("2. Start implementing: Task 1 - Serverless Project Setup")
    print("3. Deploy with: sam build && sam deploy --guided")

if __name__ == "__main__":
    main()