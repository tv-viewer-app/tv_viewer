#!/usr/bin/env python3
"""
Apply Supabase security fixes via REST API.

NOTE: This script requires service_role key (not anon key) to execute DDL statements.
      The anon key can only read data, not modify schema.

RECOMMENDED: Run scripts/supabase_security_fix.sql in the Supabase SQL Editor instead.

If you have the service_role key:
    export SUPABASE_SERVICE_KEY="your-service-role-key"
    python scripts/apply_security_fix.py
"""

import os
import sys
import requests

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_service_key():
    """Get service role key from environment."""
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    if not key:
        print("❌ ERROR: SUPABASE_SERVICE_KEY not set in environment")
        print("\nTo run this script, you need the service_role key (not anon key).")
        print("The anon key cannot execute DDL statements.\n")
        print("RECOMMENDED APPROACH:")
        print("  1. Open Supabase SQL Editor: https://supabase.com/dashboard/project/YOUR_PROJECT_REF/sql")
        print("  2. Copy/paste contents of scripts/supabase_security_fix.sql")
        print("  3. Run the migration")
        print("\nIf you have the service_role key:")
        print("  export SUPABASE_SERVICE_KEY='your-service-role-key'")
        print("  python scripts/apply_security_fix.py")
        sys.exit(1)
    return key


def execute_sql(sql_statements, service_key):
    """Execute SQL statements via Supabase REST API."""
    url = f"{config.SUPABASE_URL}/rest/v1/rpc"
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    results = []
    for i, sql in enumerate(sql_statements, 1):
        if not sql.strip() or sql.strip().startswith('--'):
            continue
            
        print(f"\n[{i}/{len(sql_statements)}] Executing: {sql[:80]}...")
        
        # Try to execute via pg_stat_statements or direct query
        # Note: Most ALTER/DROP/CREATE statements need service_role
        try:
            response = requests.post(
                url,
                headers=headers,
                json={'query': sql},
                timeout=30
            )
            
            if response.status_code == 200:
                print("  ✓ Success")
                results.append(('success', sql))
            else:
                print(f"  ✗ Failed: {response.status_code} - {response.text}")
                results.append(('failed', sql, response.text))
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append(('error', sql, str(e)))
    
    return results


def main():
    print("=" * 80)
    print("Supabase Security Fix - Apply Migration")
    print("=" * 80)
    
    # Check for service key
    service_key = get_service_key()
    
    # Read SQL file
    sql_file = os.path.join(os.path.dirname(__file__), 'supabase_security_fix.sql')
    if not os.path.exists(sql_file):
        print(f"❌ ERROR: {sql_file} not found")
        sys.exit(1)
    
    print(f"\n📄 Reading {sql_file}...")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Split into individual statements (simple split on semicolon)
    # This is basic - production would use a proper SQL parser
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    print(f"   Found {len(statements)} SQL statements")
    
    # Warn user
    print("\n⚠️  WARNING: This will modify your Supabase database schema.")
    print("   The migration includes:")
    print("     • ALTER FUNCTION statements (6 functions)")
    print("     • REVOKE/GRANT statements (6 materialized views)")
    print("     • DROP/CREATE POLICY statements (8 policies)")
    print("\n   Recommended: Review scripts/supabase_security_fix.sql first")
    
    response = input("\nProceed with migration? [y/N]: ")
    if response.lower() != 'y':
        print("Aborted.")
        sys.exit(0)
    
    # Execute
    print("\n🚀 Applying security fixes...")
    results = execute_sql(statements, service_key)
    
    # Summary
    success_count = sum(1 for r in results if r[0] == 'success')
    failed_count = len(results) - success_count
    
    print("\n" + "=" * 80)
    print(f"✓ Completed: {success_count} successful, {failed_count} failed")
    
    if failed_count > 0:
        print("\n❌ Some statements failed. Check the output above for details.")
        print("   You may need to run the SQL manually in Supabase SQL Editor.")
        sys.exit(1)
    else:
        print("\n✅ All security fixes applied successfully!")
        print("\nNext steps:")
        print("  1. Verify in Supabase Dashboard that policies are updated")
        print("  2. Test that the app still works with anonymous telemetry")
        print("  3. Check that materialized views are no longer in REST API")
        sys.exit(0)


if __name__ == '__main__':
    main()
