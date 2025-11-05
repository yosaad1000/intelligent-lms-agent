#!/usr/bin/env python3
"""
Test SAM setup locally
"""

import subprocess
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_sam_build():
    """Test SAM build locally"""
    
    print("🧪 Testing SAM Build")
    print("=" * 50)
    
    try:
        # Test SAM build
        result = subprocess.run("sam build", shell=True, capture_output=True, text=True, check=True)
        print("✅ SAM build successful")
        
        # Test SAM validate
        result = subprocess.run("sam validate", shell=True, capture_output=True, text=True, check=True)
        print("✅ SAM template validation successful")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ SAM build/validation failed")
        print(f"   Error: {e.stderr}")
        return False

def test_local_api():
    """Test local API with SAM local"""
    
    print("\n🧪 Testing Local API")
    print("=" * 50)
    
    try:
        print("🔄 Starting SAM local API...")
        print("   This will start a local API server")
        print("   Press Ctrl+C to stop when you're done testing")
        
        # Start SAM local API
        subprocess.run("sam local start-api --port 3001", shell=True, check=True)
        
    except KeyboardInterrupt:
        print("\n✅ Local API testing stopped")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Local API failed: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 Testing LMS API Backend Setup")
    print("=" * 50)
    
    # Test SAM build
    if test_sam_build():
        print("\n✅ SAM setup is working correctly!")
        print("\n📋 Options:")
        print("1. Test local API: python test_sam_setup.py --local")
        print("2. Deploy to AWS: python deploy.py")
        print("3. Continue with development")
        
        # Check if user wants to test local API
        import sys
        if '--local' in sys.argv:
            test_local_api()
    else:
        print("\n❌ SAM setup has issues. Please fix them before proceeding.")

if __name__ == "__main__":
    main()