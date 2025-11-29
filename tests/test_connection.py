#!/usr/bin/env python3
"""
Test script to verify Supabase database connection.
This helps diagnose connection issues and find the correct connection string.
"""
import psycopg2
import sys

# Connection strings to test
# Your credentials
PASSWORD = "pyxzat-pofza3-Zykzyt"
PROJECT_REF = "vbnqnnixrwcmxukzjdrd"

CONNECTION_STRINGS = [
    {
        "name": "Direct Connection (Current - DNS fails)",
        "url": f"postgresql://postgres:{PASSWORD}@db.{PROJECT_REF}.supabase.co:5432/postgres"
    },
    {
        "name": "Connection Pooling - Transaction (EU Central)",
        "url": f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
    },
    {
        "name": "Connection Pooling - Session (EU Central)",
        "url": f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-eu-central-1.pooler.supabase.com:5432/postgres"
    },
    {
        "name": "Connection Pooling - Transaction (US East)",
        "url": f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    },
    {
        "name": "Connection Pooling - Session (US East)",
        "url": f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    },
    {
        "name": "Connection Pooling - Transaction (US West)",
        "url": f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    },
    {
        "name": "Connection Pooling - Session (US West)",
        "url": f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-us-west-1.pooler.supabase.com:5432/postgres"
    }
]

def test_connection(name, connection_string):
    """Test a database connection."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {connection_string.split('@')[1] if '@' in connection_string else 'hidden'}")
    print(f"{'='*60}")
    
    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ SUCCESS! Connected to database.")
        print(f"   PostgreSQL version: {version[0][:50]}...")
        cursor.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "could not translate host name" in error_msg or "nodename nor servname provided" in error_msg:
            print(f"❌ DNS Resolution Failed")
            print(f"   Error: {error_msg}")
        elif "password authentication failed" in error_msg:
            print(f"❌ Authentication Failed")
            print(f"   Error: Password may be incorrect")
        elif "Connection refused" in error_msg:
            print(f"❌ Connection Refused")
            print(f"   Error: Server is not accepting connections on this port")
        else:
            print(f"❌ Connection Failed")
            print(f"   Error: {error_msg}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def main():
    print("="*60)
    print("Supabase Database Connection Tester")
    print("="*60)
    print("\nThis script tests different connection methods to find one that works.")
    print("If all fail, you may need to:")
    print("1. Get the correct connection string from Supabase Dashboard")
    print("2. Check if your project is paused and resume it")
    print("3. Wait a few minutes for DNS to propagate")
    
    success_count = 0
    for conn_info in CONNECTION_STRINGS:
        if test_connection(conn_info["name"], conn_info["url"]):
            success_count += 1
            print(f"\n✅ Found working connection: {conn_info['name']}")
            print(f"\nUpdate your .streamlit/secrets.toml with:")
            print(f'db_url = "{conn_info["url"]}"')
            break
    
    print(f"\n{'='*60}")
    if success_count == 0:
        print("❌ All connection attempts failed.")
        print("\nNext steps:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to: Project Settings > Database > Connection string")
        print("4. Copy the 'Connection pooling' connection string")
        print("5. Update .streamlit/secrets.toml with the new connection string")
        sys.exit(1)
    else:
        print("✅ Connection test completed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()

