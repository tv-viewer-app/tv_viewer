#!/usr/bin/env python3
"""
Test that Supabase security fixes are working correctly.
This tests the RLS policy validation constraints.

Run after applying scripts/supabase_security_fix.sql
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import requests


def test_channel_status_validation():
    """Test that channel_status RLS policies validate data."""
    print("\n" + "="*80)
    print("Test 1: channel_status validation")
    print("="*80)
    
    url = f"{config.SUPABASE_URL}/rest/v1/channel_status"
    headers = {
        'apikey': config.SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {config.SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    # Test 1: Valid data should succeed
    print("\n✓ Test 1a: Valid data (should succeed)")
    valid_data = {
        'url_hash': 'a' * 64,  # Valid SHA-256 format
        'status': 'working',
        'response_time_ms': 500
    }
    response = requests.post(url, json=valid_data, headers=headers, timeout=10)
    print(f"  Status: {response.status_code} (expected: 201)")
    if response.status_code != 201:
        print(f"  Error: {response.text}")
    
    # Test 2: Invalid url_hash (too short) should fail
    print("\n✗ Test 1b: Invalid url_hash — too short (should fail)")
    invalid_hash = {
        'url_hash': 'abc123',  # Too short
        'status': 'working'
    }
    response = requests.post(url, json=invalid_hash, headers=headers, timeout=10)
    print(f"  Status: {response.status_code} (expected: 403 or 400)")
    if response.status_code in [400, 403]:
        print(f"  ✓ Correctly rejected: {response.text[:100]}")
    else:
        print(f"  ⚠ Unexpected: {response.text}")
    
    # Test 3: Invalid status value should fail
    print("\n✗ Test 1c: Invalid status value (should fail)")
    invalid_status = {
        'url_hash': 'b' * 64,
        'status': 'invalid_status'  # Not in enum
    }
    response = requests.post(url, json=invalid_status, headers=headers, timeout=10)
    print(f"  Status: {response.status_code} (expected: 403 or 400)")
    if response.status_code in [400, 403]:
        print(f"  ✓ Correctly rejected: {response.text[:100]}")
    
    # Test 4: Excessive response_time should fail
    print("\n✗ Test 1d: Excessive response_time_ms (should fail)")
    excessive_time = {
        'url_hash': 'c' * 64,
        'status': 'working',
        'response_time_ms': 999999  # Over 60s limit
    }
    response = requests.post(url, json=excessive_time, headers=headers, timeout=10)
    print(f"  Status: {response.status_code} (expected: 403 or 400)")
    if response.status_code in [400, 403]:
        print(f"  ✓ Correctly rejected: {response.text[:100]}")


def test_analytics_events_validation():
    """Test that analytics_events RLS policies validate data."""
    print("\n" + "="*80)
    print("Test 2: analytics_events validation")
    print("="*80)
    
    url = f"{config.SUPABASE_URL}/rest/v1/analytics_events"
    headers = {
        'apikey': config.SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {config.SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    # Test 1: Valid event should succeed
    print("\n✓ Test 2a: Valid event (should succeed)")
    valid_event = {
        'event_type': 'app_start',
        'event_data': {'version': '2.3.3'},
        'user_id': 'test_user_123'
    }
    response = requests.post(url, json=valid_event, headers=headers, timeout=10)
    print(f"  Status: {response.status_code} (expected: 201)")
    
    # Test 2: Excessive event_type length should fail
    print("\n✗ Test 2b: Excessive event_type length (should fail)")
    long_type = {
        'event_type': 'x' * 200,  # Over 100 char limit
        'user_id': 'test'
    }
    response = requests.post(url, json=long_type, headers=headers, timeout=10)
    print(f"  Status: {response.status_code} (expected: 403 or 400)")
    if response.status_code in [400, 403]:
        print(f"  ✓ Correctly rejected")


def test_materialized_view_access():
    """Test that materialized views are NOT accessible to anon."""
    print("\n" + "="*80)
    print("Test 3: Materialized views should be blocked")
    print("="*80)
    
    views = [
        'mv_daily_active_users',
        'mv_top_channels',
        'mv_client_platforms',
        'mv_favorite_channels',
        'mv_crash_summary',
        'mv_engagement'
    ]
    
    headers = {
        'apikey': config.SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {config.SUPABASE_ANON_KEY}'
    }
    
    for view in views:
        url = f"{config.SUPABASE_URL}/rest/v1/{view}"
        response = requests.get(url, headers=headers, timeout=10)
        status = "✓" if response.status_code in [401, 403, 404] else "✗"
        print(f"  {status} {view}: {response.status_code} (expected: 403/404)")


def main():
    print("\n" + "="*80)
    print("Supabase Security Fix — Validation Tests")
    print("="*80)
    print("\nThese tests verify that the security fixes are working correctly.")
    print("Run AFTER applying scripts/supabase_security_fix.sql\n")
    
    try:
        test_channel_status_validation()
        test_analytics_events_validation()
        test_materialized_view_access()
        
        print("\n" + "="*80)
        print("✓ Test suite completed")
        print("="*80)
        print("\nNote: Some tests intentionally fail to verify constraints work.")
        print("Check that invalid data is correctly rejected (403/400 status).\n")
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
