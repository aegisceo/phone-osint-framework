#!/usr/bin/env python3
"""
Phone Number Breach Database Integration
Search for phone numbers directly in breach databases
"""

import os
import requests
import logging
import hashlib
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv('config/.env')

class ComprehensiveBreachSearcher:
    """
    Search multiple breach databases using ALL available parameters
    Supports: phone, email, username, name, IP, domain, address
    """
    
    def __init__(self, phone_number: str = None, search_params: Dict = None):
        self.phone = phone_number
        self.search_params = search_params or {}
        self.logger = logging.getLogger(__name__)
        
        # API Keys
        self.leakcheck_key = os.getenv('LEAKCHECK_API_KEY')
        self.intelx_key = os.getenv('INTELX_API_KEY')
        self.dehashed_key = os.getenv('DEHASHED_API_KEY')  # DeHashed v2 uses API key only (no username)
        
        # Build comprehensive search parameters
        self._build_search_parameters()
    
    def _build_search_parameters(self):
        """Build list of ALL possible search parameters from discovered data"""
        
        params = {
            'phone': [],
            'emails': [],
            'usernames': [],
            'names': [],
            'ips': [],
            'domains': [],
            'addresses': []
        }
        
        # Add phone numbers (DeHashed stores WITHOUT country code - last 10 digits only)
        if self.phone:
            phone_clean = ''.join(filter(str.isdigit, self.phone))
            # For DeHashed: ONLY use last 10 digits (no country code)
            if len(phone_clean) >= 10:
                params['phone'].append(phone_clean[-10:])  # Last 10 digits (e.g., 6199303063)
            # Also try without leading 1 if it's 11 digits
            if len(phone_clean) == 11 and phone_clean.startswith('1'):
                params['phone'].append(phone_clean[1:])  # Remove leading 1
        
        # Extract from search_params
        params['emails'] = self.search_params.get('emails', [])
        params['usernames'] = self.search_params.get('usernames', [])
        params['names'] = self.search_params.get('names', [])
        params['ips'] = self.search_params.get('ips', [])
        params['addresses'] = self.search_params.get('addresses', [])
        
        # Extract domains from emails
        for email in params['emails']:
            if '@' in email:
                domain = email.split('@')[1]
                if domain not in params['domains']:
                    params['domains'].append(domain)
        
        self.all_search_params = params
        
        # Log what we're searching with
        total_params = sum(len(v) for v in params.values())
        self.logger.info(f"🔍 Built {total_params} search parameters:")
        for param_type, values in params.items():
            if values:
                self.logger.info(f"   {param_type}: {len(values)} items")
        
    def search_all_databases(self) -> Dict:
        """Search all available breach databases for phone number"""
        
        results = {
            'found': False,
            'databases_checked': [],
            'breaches_found': [],
            'associated_emails': [],
            'associated_usernames': [],
            'total_records': 0
        }
        
        self.logger.info(f"🔍 Searching breach databases for phone: {self.phone}")
        
        # LeakCheck - Most comprehensive for phone numbers
        if self.leakcheck_key:
            leakcheck_results = self.search_leakcheck()
            if leakcheck_results.get('found'):
                results['found'] = True
                results['breaches_found'].extend(leakcheck_results.get('breaches', []))
                results['associated_emails'].extend(leakcheck_results.get('emails', []))
                results['total_records'] += leakcheck_results.get('records_found', 0)
            results['databases_checked'].append('leakcheck')
        
        # Intelligence X - Dark web and paste aggregation
        if self.intelx_key:
            intelx_results = self.search_intelx()
            if intelx_results.get('found'):
                results['found'] = True
                results['breaches_found'].extend(intelx_results.get('breaches', []))
                results['associated_emails'].extend(intelx_results.get('emails', []))
                results['total_records'] += intelx_results.get('records_found', 0)
            results['databases_checked'].append('intelligence_x')
        
        # DeHashed - Comprehensive breach aggregator
        if self.dehashed_username and self.dehashed_key:
            dehashed_results = self.search_dehashed()
            if dehashed_results.get('found'):
                results['found'] = True
                results['breaches_found'].extend(dehashed_results.get('breaches', []))
                results['associated_emails'].extend(dehashed_results.get('emails', []))
                results['associated_usernames'].extend(dehashed_results.get('usernames', []))
                results['total_records'] += dehashed_results.get('records_found', 0)
            results['databases_checked'].append('dehashed')
        
        # Deduplicate
        results['associated_emails'] = list(set(results['associated_emails']))
        results['associated_usernames'] = list(set(results['associated_usernames']))
        
        if results['found']:
            self.logger.warning(f"🚨 Phone number found in {len(results['breaches_found'])} breaches!")
            self.logger.info(f"📧 Associated emails: {len(results['associated_emails'])}")
            self.logger.info(f"👤 Associated usernames: {len(results['associated_usernames'])}")
        else:
            self.logger.info(f"✅ Phone number not found in {len(results['databases_checked'])} breach databases")
        
        return results
    
    def search_leakcheck(self) -> Dict:
        """
        Search LeakCheck.io using multiple parameters
        LeakCheck supports: email, username, phone, hash, domain searches
        """
        results = {'found': False, 'breaches': [], 'emails': [], 'records_found': 0, 'searches_performed': 0}
        
        if not self.leakcheck_key:
            return results
        
        try:
            # LeakCheck API endpoint
            url = "https://leakcheck.io/api/public"
            
            # Search by phone numbers
            for phone in self.all_search_params.get('phone', []):
                params = {
                    'key': self.leakcheck_key,
                    'check': phone,
                    'type': 'phone'
                }
                
                self.logger.info(f"🔍 LeakCheck searching phone: {phone}")
                response = requests.get(url, params=params, timeout=15)
                results['searches_performed'] += 1
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('found'):
                        self._process_leakcheck_results(data, results, 'phone', phone)
                
                time.sleep(1)  # Rate limiting
            
            # Search by emails (top 3)
            for email in self.all_search_params.get('emails', [])[:3]:
                params = {
                    'key': self.leakcheck_key,
                    'check': email,
                    'type': 'email'
                }
                
                self.logger.info(f"🔍 LeakCheck searching email: {email}")
                response = requests.get(url, params=params, timeout=15)
                results['searches_performed'] += 1
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('found'):
                        self._process_leakcheck_results(data, results, 'email', email)
                
                time.sleep(1)  # Rate limiting
            
            # Search by usernames (top 3 REAL ones)
            for username in self.all_search_params.get('usernames', [])[:3]:
                params = {
                    'key': self.leakcheck_key,
                    'check': username,
                    'type': 'username'
                }
                
                self.logger.info(f"🔍 LeakCheck searching username: {username}")
                response = requests.get(url, params=params, timeout=15)
                results['searches_performed'] += 1
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('found'):
                        self._process_leakcheck_results(data, results, 'username', username)
                
                time.sleep(1)  # Rate limiting
            
            if results['found']:
                self.logger.warning(f"🚨 LeakCheck: Found {results['records_found']} records across {results['searches_performed']} searches!")
            else:
                self.logger.info(f"✅ LeakCheck: No breaches found ({results['searches_performed']} searches)")
                
        except Exception as e:
            self.logger.error(f"LeakCheck error: {e}")
        
        return results
    
    def _process_leakcheck_results(self, data: Dict, results: Dict, search_type: str, search_value: str):
        """Process LeakCheck API response and extract data"""
        
        for record in data.get('result', []):
            breach_info = {
                'source': record.get('source', 'Unknown'),
                'email': record.get('email'),
                'username': record.get('login'),
                'phone': record.get('phone'),
                'database': 'leakcheck',
                'search_type': search_type,
                'search_value': search_value
            }
            results['breaches'].append(breach_info)
            results['found'] = True
            results['records_found'] += 1
            
            # Collect associated data
            if record.get('email') and record.get('email') not in results['emails']:
                results['emails'].append(record.get('email'))
    
    def search_intelx(self) -> Dict:
        """
        Search Intelligence X for phone number
        IntelX aggregates dark web, paste sites, and breaches
        """
        results = {'found': False, 'breaches': [], 'emails': [], 'records_found': 0}
        
        if not self.intelx_key:
            return results
        
        try:
            # Clean phone number
            phone_clean = ''.join(filter(str.isdigit, self.phone))
            
            # Intelligence X search endpoint
            url = "https://2.intelx.io/phonebook/search"
            headers = {
                'x-key': self.intelx_key,
                'User-Agent': 'Phone-OSINT-Framework'
            }
            
            payload = {
                'term': phone_clean,
                'maxresults': 100,
                'media': 0,
                'target': 1  # Phone number search
            }
            
            self.logger.info(f"🔍 Intelligence X searching for: {phone_clean}")
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('selectors'):
                    results['found'] = True
                    results['records_found'] = len(data['selectors'])
                    
                    # Extract associated data
                    for selector in data['selectors']:
                        breach_info = {
                            'source': selector.get('bucket', 'Unknown'),
                            'email': selector.get('selectorvalue') if selector.get('selectortypeid') == 1 else None,
                            'phone': phone_clean,
                            'database': 'intelligence_x',
                            'date': selector.get('added')
                        }
                        results['breaches'].append(breach_info)
                        
                        # Collect emails
                        if selector.get('selectortypeid') == 1:  # Email type
                            results['emails'].append(selector.get('selectorvalue'))
                    
                    self.logger.warning(f"🚨 Intelligence X: Phone found in {results['records_found']} records!")
                else:
                    self.logger.info("✅ Intelligence X: Phone not found")
            
            elif response.status_code == 402:
                self.logger.error("❌ Intelligence X: No credits remaining")
            else:
                self.logger.warning(f"⚠️ Intelligence X: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Intelligence X error: {e}")
        
        return results
    
    def search_dehashed(self) -> Dict:
        """
        Search DeHashed using ALL available parameters
        DeHashed supports: email, username, phone, ip_address, name, vin, address, domain
        """
        results = {'found': False, 'breaches': [], 'emails': [], 'usernames': [], 'records_found': 0}
        
        if not self.dehashed_key:
            self.logger.debug("DeHashed API key not configured")
            return results
        
        try:
            # Build comprehensive query from ALL available data
            query_parts = []
            
            # DeHashed API v2 endpoint (POST with JSON body and header auth)
            url = "https://api.dehashed.com/v2/search"
            headers = {
                'Dehashed-Api-Key': self.dehashed_key,
                'Content-Type': 'application/json'
            }
            
            # DeHashed does NOT support OR queries - search each parameter separately
            all_entries = []
            seen_ids = set()
            total_found = 0
            searches_performed = 0
            
            # Search by phone numbers
            for phone in self.all_search_params.get('phone', []):
                query = f'phone:{phone}'  # Without quotes
                self.logger.info(f"🔍 DeHashed searching: {query}")
                
                try:
                    payload = {'query': query, 'page': 1, 'size': 100, 'de_dupe': True}
                    response = requests.post(url, json=payload, headers=headers, timeout=20)
                    searches_performed += 1
                    
                    if response.status_code == 200:
                        data = response.json()
                        balance = data.get('balance', 0)
                        total = data.get('total', 0)
                        
                        if total > 0:
                            self.logger.warning(f"   🚨 FOUND {total} records for phone {phone}")
                            for entry in data.get('entries', []):
                                entry_id = entry.get('id')
                                if entry_id and entry_id not in seen_ids:
                                    all_entries.append(entry)
                                    seen_ids.add(entry_id)
                                    total_found += 1
                        else:
                            self.logger.info(f"   ✅ No records for phone {phone}")
                        
                        self.logger.info(f"   💰 Credits remaining: {balance}")
                    elif response.status_code == 403:
                        self.logger.error("   ❌ Insufficient credits - stopping DeHashed search")
                        break
                except Exception as search_error:
                    self.logger.warning(f"   ⚠️ Phone search error: {search_error}")
                
                time.sleep(0.2)  # Rate limiting
            
            # Search by names
            for name in self.all_search_params.get('names', [])[:2]:  # Limit to 2 names
                query = f'name:"{name}"'
                self.logger.info(f"🔍 DeHashed searching: {query}")
                
                try:
                    payload = {'query': query, 'page': 1, 'size': 100, 'de_dupe': True}
                    response = requests.post(url, json=payload, headers=headers, timeout=20)
                    searches_performed += 1
                    
                    if response.status_code == 200:
                        data = response.json()
                        balance = data.get('balance', 0)
                        total = data.get('total', 0)
                        
                        if total > 0:
                            self.logger.warning(f"   🚨 FOUND {total} records for name {name}")
                            # Only take first 10 to avoid overwhelming results
                            for entry in data.get('entries', [])[:10]:
                                entry_id = entry.get('id')
                                if entry_id and entry_id not in seen_ids:
                                    all_entries.append(entry)
                                    seen_ids.add(entry_id)
                                    total_found += 1
                        else:
                            self.logger.info(f"   ✅ No records for name {name}")
                        
                        self.logger.info(f"   💰 Credits remaining: {balance}")
                    elif response.status_code == 403:
                        self.logger.error("   ❌ Insufficient credits - stopping DeHashed search")
                        break
                except Exception as search_error:
                    self.logger.warning(f"   ⚠️ Name search error: {search_error}")
                
                time.sleep(0.2)  # Rate limiting
            
            # Process all collected entries
            if all_entries:
                results['found'] = True
                results['records_found'] = len(all_entries)
                
                self.logger.warning(f"🔥 DeHashed: Found {len(all_entries)} total records across {searches_performed} searches")
                
                # Extract data from all collected entries (DeHashed v2 returns arrays for each field)
                for entry in all_entries:
                    breach_info = {
                        'source': entry.get('database_name', 'Unknown'),
                        'email': entry.get('email', [])[0] if entry.get('email') else None,
                        'username': entry.get('username', [])[0] if entry.get('username') else None,
                        'phone': entry.get('phone', [])[0] if entry.get('phone') else None,
                        'name': entry.get('name', [])[0] if entry.get('name') else None,
                        'password': bool(entry.get('password')),  # Boolean, don't expose actual password
                        'database': 'dehashed',
                        'id': entry.get('id')
                    }
                    results['breaches'].append(breach_info)
                    
                    # Collect associated data (fields are arrays in v2)
                    if entry.get('email'):
                        for email in entry.get('email', []):
                            if email and email not in results['emails']:
                                results['emails'].append(email)
                    if entry.get('username'):
                        for username in entry.get('username', []):
                            if username and username not in results['usernames']:
                                results['usernames'].append(username)
                
                self.logger.warning(f"📧 Discovered emails: {results['emails']}")
                self.logger.warning(f"👤 Discovered usernames: {results['usernames']}")
            else:
                self.logger.info("✅ DeHashed: No records found in any searches")
                
        except Exception as e:
            self.logger.error(f"DeHashed error: {e}")
        
        return results


# Integration function
def search_phone_in_breaches(phone_number: str) -> Dict:
    """
    Search phone number across multiple breach databases
    
    Returns emails, usernames, and breach information associated with the phone
    """
    searcher = PhoneBreachSearcher(phone_number)
    return searcher.search_all_databases()


if __name__ == "__main__":
    import sys
    
    phone = sys.argv[1] if len(sys.argv) > 1 else input("Enter phone number: ")
    
    results = search_phone_in_breaches(phone)
    
    print("\n" + "="*60)
    print(f"Phone Breach Search Results: {phone}")
    print("="*60)
    
    if results['found']:
        print(f"\n🚨 FOUND in {len(results['breaches_found'])} breaches!")
        print(f"📊 Databases checked: {', '.join(results['databases_checked'])}")
        print(f"📧 Associated emails: {len(results['associated_emails'])}")
        
        if results['associated_emails']:
            print("\nEmails:")
            for email in results['associated_emails'][:10]:
                print(f"  - {email}")
        
        if results['associated_usernames']:
            print(f"\n👤 Associated usernames: {len(results['associated_usernames'])}")
            for username in results['associated_usernames'][:10]:
                print(f"  - {username}")
    else:
        print(f"\n✅ Phone number NOT found in breach databases")
        print(f"📊 Databases checked: {', '.join(results['databases_checked'])}")

