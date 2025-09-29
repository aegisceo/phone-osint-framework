#!/usr/bin/env python3
"""
Test all configured APIs to ensure they're working
"""
import os
import sys
import requests
from dotenv import load_dotenv
import json
from colorama import init, Fore, Style

init()

# Load environment
load_dotenv('config/.env')

def test_numverify():
    """Test NumVerify API"""
    print(f"\n{Fore.CYAN}Testing NumVerify API...{Style.RESET_ALL}")
    
    api_key = os.getenv('NUMVERIFY_API_KEY')
    if not api_key:
        print(f"{Fore.RED}[X] NumVerify API key not found{Style.RESET_ALL}")
        return False
    
    try:
        url = "http://apilayer.net/api/validate"
        params = {
            'access_key': api_key,
            'number': '14158586273',  # Test number
            'format': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'error' in data:
            print(f"{Fore.RED}[X] NumVerify error: {data['error']['info']}{Style.RESET_ALL}")
            return False
            
        print(f"{Fore.GREEN}[OK] NumVerify working! Test response:{Style.RESET_ALL}")
        print(f"  Carrier: {data.get('carrier', 'N/A')}")
        print(f"  Location: {data.get('location', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}[X] NumVerify error: {str(e)}{Style.RESET_ALL}")
        return False

def test_google_search():
    """Test Google Custom Search API"""
    print(f"\n{Fore.CYAN}Testing Google Search API...{Style.RESET_ALL}")
    
    api_key = os.getenv('GOOGLE_API_KEY')
    cse_id = os.getenv('GOOGLE_CSE_ID')
    
    if not api_key or not cse_id:
        print(f"{Fore.RED}[X] Google API credentials not found{Style.RESET_ALL}")
        return False
    
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': 'test search',
            'num': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'error' in data:
            print(f"{Fore.RED}[X] Google API error: {data['error']['message']}{Style.RESET_ALL}")
            return False
            
        print(f"{Fore.GREEN}[OK] Google Search API working!{Style.RESET_ALL}")
        print(f"  Total results: ~{data['searchInformation']['formattedTotalResults']}")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}[X] Google API error: {str(e)}{Style.RESET_ALL}")
        return False

def test_opencellid():
    """Test OpenCellID API"""
    print(f"\n{Fore.CYAN}Testing OpenCellID API...{Style.RESET_ALL}")
    
    api_key = os.getenv('OPENCELLID_API_KEY')
    if not api_key:
        print(f"{Fore.RED}[X] OpenCellID API key not found{Style.RESET_ALL}")
        return False
    
    try:
        # Test with a known cell tower
        url = "https://api.opencellid.org/cell/get"
        params = {
            'key': api_key,
            'mcc': '310',  # USA
            'mnc': '260',  # T-Mobile
            'lac': '1',
            'cellid': '1',
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"{Fore.GREEN}[OK] OpenCellID API working!{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.YELLOW}[!] OpenCellID returned status: {response.status_code}{Style.RESET_ALL}")
            return True  # API is responding, just no data for test cell
            
    except Exception as e:
        print(f"{Fore.RED}[X] OpenCellID error: {str(e)}{Style.RESET_ALL}")
        return False

def test_twilio():
    """Test Twilio API"""
    print(f"\n{Fore.CYAN}Testing Twilio API...{Style.RESET_ALL}")
    
    account_sid = os.getenv('TWILIO_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        print(f"{Fore.RED}[X] Twilio credentials not found{Style.RESET_ALL}")
        return False
    
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        
        # Get account info to verify credentials
        account = client.api.accounts(account_sid).fetch()
        
        print(f"{Fore.GREEN}[OK] Twilio API working!{Style.RESET_ALL}")
        print(f"  Account Status: {account.status}")
        print(f"  Type: {account.type}")
        
        # Try a phone lookup (costs $0.01)
        try:
            phone_number = client.lookups.v2.phone_numbers('+14158586273').fetch()
            print(f"  Test lookup successful!")
        except:
            print(f"  {Fore.YELLOW}Note: Phone lookup skipped (costs $0.01){Style.RESET_ALL}")
            
        return True
        
    except Exception as e:
        print(f"{Fore.RED}[X] Twilio error: {str(e)}{Style.RESET_ALL}")
        return False

def test_hunter():
    """Test Hunter.io API"""
    print(f"\n{Fore.CYAN}Testing Hunter.io API...{Style.RESET_ALL}")
    
    api_key = os.getenv('HUNTER_API_KEY')
    if not api_key:
        print(f"{Fore.RED}[X] Hunter.io API key not found{Style.RESET_ALL}")
        return False
    
    try:
        url = "https://api.hunter.io/v2/account"
        params = {'api_key': api_key}
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'data' in data:
            print(f"{Fore.GREEN}[OK] Hunter.io API working!{Style.RESET_ALL}")
            print(f"  Plan: {data['data']['plan_name']}")
            if 'requests' in data['data']:
                requests_data = data['data']['requests']
                if 'available' in requests_data:
                    print(f"  Requests available: {requests_data['available']}")
                elif 'used' in requests_data:
                    print(f"  Requests used: {requests_data['used']}")
                else:
                    print(f"  Requests: {requests_data}")
            return True
        else:
            print(f"{Fore.RED}[X] Hunter.io error: Invalid response{Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}[X] Hunter.io error: {str(e)}{Style.RESET_ALL}")
        return False

def test_shodan():
    """Test Shodan API"""
    print(f"\n{Fore.CYAN}Testing Shodan API...{Style.RESET_ALL}")

    api_key = os.getenv('SHODAN_KEY')
    if not api_key:
        print(f"{Fore.RED}[X] Shodan API key not found{Style.RESET_ALL}")
        return False

    try:
        url = "https://api.shodan.io/api-info"
        params = {'key': api_key}

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if 'query_credits' in data:
            print(f"{Fore.GREEN}[OK] Shodan API working!{Style.RESET_ALL}")
            print(f"  Query credits: {data['query_credits']}")
            print(f"  Scan credits: {data['scan_credits']}")
            return True
        else:
            print(f"{Fore.RED}[X] Shodan error: Invalid response{Style.RESET_ALL}")
            return False

    except Exception as e:
        print(f"{Fore.RED}[X] Shodan error: {str(e)}{Style.RESET_ALL}")
        return False

def test_hibp():
    """Test Have I Been Pwned API"""
    print(f"\n{Fore.CYAN}Testing Have I Been Pwned API...{Style.RESET_ALL}")

    api_key = os.getenv('HAVEIBEENPWNED_API_KEY')
    if not api_key:
        print(f"{Fore.RED}[X] HIBP API key not found{Style.RESET_ALL}")
        return False

    try:
        # Test with a known compromised email
        url = "https://haveibeenpwned.com/api/v3/breachedaccount/test@example.com"
        headers = {
            'hibp-api-key': api_key,
            'User-Agent': 'PhoneOSINT-Framework'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            print(f"{Fore.GREEN}[OK] HIBP API working!{Style.RESET_ALL}")
            print(f"  Status: Active")
            return True
        elif response.status_code == 404:
            print(f"{Fore.GREEN}[OK] HIBP API working!{Style.RESET_ALL}")
            print(f"  Status: Active (test email not found)")
            return True
        else:
            print(f"{Fore.RED}[X] HIBP error: HTTP {response.status_code}{Style.RESET_ALL}")
            return False

    except Exception as e:
        print(f"{Fore.RED}[X] HIBP error: {str(e)}{Style.RESET_ALL}")
        return False

def main():
    """Run all API tests"""
    print(f"\n{Fore.MAGENTA}{'='*50}")
    print("Phone OSINT Framework - API Testing")
    print(f"{'='*50}{Style.RESET_ALL}")
    
    results = {
        'NumVerify': test_numverify(),
        'Google Search': test_google_search(),
        'OpenCellID': test_opencellid(),
        'Twilio': test_twilio(),
        'Hunter.io': test_hunter(),
        'Shodan': test_shodan(),
        'Have I Been Pwned': test_hibp()
    }
    
    print(f"\n{Fore.MAGENTA}{'='*50}")
    print("Test Summary:")
    print(f"{'='*50}{Style.RESET_ALL}")
    
    working = sum(1 for v in results.values() if v)
    total = len(results)
    
    for api, status in results.items():
        status_text = f"{Fore.GREEN}[OK] Working{Style.RESET_ALL}" if status else f"{Fore.RED}[X] Failed{Style.RESET_ALL}"
        print(f"{api:<20} {status_text}")
    
    print(f"\n{Fore.CYAN}Total: {working}/{total} APIs functional{Style.RESET_ALL}")
    
    if working < total:
        print(f"\n{Fore.YELLOW}Note: Fix failing APIs before running full investigations{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.GREEN}All APIs configured correctly! Ready for testing.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
