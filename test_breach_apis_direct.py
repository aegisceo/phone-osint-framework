#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct API test for DeHashed and HIBP
Tests authentication and basic queries
"""

import os
import sys
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv('config/.env')

print("="*70)
print("BREACH API DIAGNOSTIC TEST")
print("="*70)

# Get API credentials
dehashed_username = os.getenv('DEHASHED_USERNAME')
dehashed_key = os.getenv('DEHASHED_API_KEY')
hibp_key = os.getenv('HAVEIBEENPWNED_API_KEY')

print(f"\nLoaded Credentials:")
print(f"   DeHashed Username: {dehashed_username}")
print(f"   DeHashed API Key: {dehashed_key[:20]}... (length: {len(dehashed_key) if dehashed_key else 0})")
print(f"   HIBP API Key: {hibp_key[:20]}... (length: {len(hibp_key) if hibp_key else 0})")

# Test 1: DeHashed
print("\n" + "="*70)
print("TEST 1: DeHashed API")
print("="*70)

if dehashed_key:  # No username needed for v2 API
    print("\nTesting DeHashed v2 API with correct format...")
    
    # Correct endpoint from documentation
    endpoint = "https://api.dehashed.com/v2/search"
    
    print(f"\nTesting endpoint: {endpoint}")
    print(f"   Auth: Header-based (Dehashed-Api-Key)")
    print(f"   Method: POST with JSON body")
    print(f"   Query: email:test@example.com")
    
    headers = {
        'Dehashed-Api-Key': dehashed_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'query': 'email:test@example.com',
        'page': 1,
        'size': 10,
        'de_dupe': True
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Body (first 500 chars): {response.text[:500]}")
        
        if response.status_code == 200:
            print("   [SUCCESS] DeHashed API works!")
            try:
                data = response.json()
                print(f"   Response keys: {list(data.keys())}")
                print(f"   Credits remaining: {data.get('balance', 'unknown')}")
                print(f"   Records found: {data.get('total', 0)}")
            except:
                print("   [WARNING] Response is not JSON")
        elif response.status_code == 401:
            print("   [ERROR] 401 Unauthorized - Invalid API key or no subscription")
        elif response.status_code == 403:
            print("   [ERROR] 403 Forbidden - Insufficient credits")
            print("   ACTION: Purchase search credits at https://app.dehashed.com")
        elif response.status_code == 404:
            print("   [ERROR] 404 Not Found - Check endpoint URL")
        else:
            print(f"   [WARNING] HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Try with phone number + name (your actual use case)
    print("\nTesting DeHashed with phone + name...")
    
    payload = {
        'query': 'phone:"16199303063" OR name:"Ryan Lindley"',
        'page': 1,
        'size': 100,
        'de_dupe': True
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        
        print(f"   Query: {payload['query']}")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response (first 500 chars): {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   [SUCCESS] Found {data.get('total', 0)} records")
                print(f"   Credits remaining: {data.get('balance', 'unknown')}")
                if data.get('entries'):
                    entry = data['entries'][0]
                    print(f"   First result:")
                    print(f"      Email: {entry.get('email', 'none')}")
                    print(f"      Username: {entry.get('username', 'none')}")
                    print(f"      Database: {entry.get('database_name', 'unknown')}")
            except Exception as parse_error:
                print(f"   [WARNING] Parse error: {parse_error}")
        elif response.status_code == 403:
            print("   [BLOCKED] 403 Forbidden - ZERO CREDITS!")
            print("   You need to purchase search credits at https://app.dehashed.com")
        
    except Exception as e:
        print(f"   [ERROR] {e}")
else:
    print("\n[ERROR] DeHashed credentials not found in .env file")

# Test 2: HIBP
print("\n" + "="*70)
print("TEST 2: Have I Been Pwned API")
print("="*70)

if hibp_key:
    # Test with a known breached email (from Adobe breach for testing)
    test_email = "test@example.com"  # Generic test
    
    print(f"\nTesting HIBP with email: {test_email}")
    print(f"   API Key: {hibp_key[:20]}...")
    
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{test_email}"
    headers = {
        'hibp-api-key': hibp_key,
        'User-Agent': 'Phone-OSINT-Framework-Diagnostic'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            breaches = response.json()
            print(f"   [SUCCESS] Email found in {len(breaches)} breaches")
            if breaches:
                print(f"   First breach: {breaches[0].get('Name', 'Unknown')}")
        elif response.status_code == 404:
            print(f"   [SUCCESS] API working - email not in breaches (clean)")
        elif response.status_code == 401:
            print(f"   [ERROR] 401 Unauthorized - Invalid API key")
            print(f"   Response: {response.text[:200]}")
        elif response.status_code == 429:
            print(f"   [WARNING] 429 Rate limited - too many requests")
        else:
            print(f"   [WARNING] HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test with actual email from your investigation
    print(f"\nTesting HIBP with your LinkedIn-based email...")
    test_email2 = "rlindley-cyber@gmail.com"
    
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{test_email2}"
    
    try:
        # Wait for rate limit
        import time
        time.sleep(1.6)
        
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"   Email: {test_email2}")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            breaches = response.json()
            print(f"   [FOUND] Email in {len(breaches)} breaches:")
            for breach in breaches[:3]:
                print(f"      - {breach.get('Name', 'Unknown')}")
        elif response.status_code == 404:
            print(f"   [CLEAN] Email clean (no breaches)")
        else:
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   [ERROR] {e}")
    
else:
    print("\n[ERROR] HIBP API key not found in .env file")

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
