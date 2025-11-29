#!/usr/bin/env python3
"""
Test different username formats for Supabase connection pooling.
"""
import psycopg2

PASSWORD = "pyxzat-pofza3-Zykzyt"
PROJECT_REF = "vbnqnnixrwcmxukzjdrd"
HOST = "aws-0-eu-central-1.pooler.supabase.com"
PORT = 6543

# Different username formats to try
USERNAME_FORMATS = [
    f"postgres.{PROJECT_REF}",
    f"postgres",
    f"{PROJECT_REF}",
    f"postgres.{PROJECT_REF}@default",
]

print("="*60)
print("Testing Different Username Formats")
print("="*60)
print(f"Host: {HOST}:{PORT}")
print(f"Project Reference: {PROJECT_REF}")
print()

for username in USERNAME_FORMATS:
    conn_string = f"postgresql://{username}:{PASSWORD}@{HOST}:{PORT}/postgres"
    print(f"Testing: {username}")
    print(f"  Connection string: postgresql://{username}:***@{HOST}:{PORT}/postgres")
    
    try:
        conn = psycopg2.connect(conn_string, connect_timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"  ✅ SUCCESS! Connected!")
        print(f"  ✅ Use this in your .streamlit/secrets.toml:")
        print(f"  db_url = \"{conn_string}\"")
        cursor.close()
        conn.close()
        break
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "Tenant or user not found" in error_msg:
            print(f"  ❌ Username format incorrect")
        elif "password authentication failed" in error_msg:
            print(f"  ❌ Password incorrect (but username format might be right)")
        else:
            print(f"  ❌ Error: {error_msg[:80]}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:80]}")
    print()

print("="*60)
print("If all formats failed, you need to get the exact connection string")
print("from your Supabase Dashboard:")
print("  Project Settings > Database > Connection string > Connection pooling")
print("="*60)

