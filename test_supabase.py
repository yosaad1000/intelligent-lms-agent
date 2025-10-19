#!/usr/bin/env python3
"""
Test Supabase connection
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test Supabase connection"""
    
    print("🧪 Testing Supabase Connection")
    print("=" * 50)
    
    try:
        # Initialize Supabase client
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            print("❌ Missing Supabase credentials in .env file")
            return False
        
        supabase: Client = create_client(url, key)
        
        # Test connection by querying users table
        response = supabase.table('users').select('user_id, email, name').limit(5).execute()
        
        print(f"✅ Supabase connection successful")
        print(f"📊 Found {len(response.data)} users in database")
        
        if response.data:
            print("👥 Sample users:")
            for user in response.data[:3]:  # Show first 3 users
                print(f"   - {user.get('name', 'N/A')} ({user.get('email', 'N/A')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    if test_supabase_connection():
        print("\n✅ All connections tested successfully!")
        print("\n🚀 Ready to start Task 1: Serverless Project Setup")
    else:
        print("\n❌ Please check your Supabase configuration")