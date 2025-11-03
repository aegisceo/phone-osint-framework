#!/usr/bin/env python3
import requests
import hashlib
import os
import logging
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv('config/.env')

class BreachChecker:
    def __init__(self, phone_number):
        self.phone = phone_number
        self.hibp_key = os.getenv('HAVEIBEENPWNED_API_KEY')
        self.logger = logging.getLogger(__name__)
        self.last_request_time = 0
        
    def _rate_limit(self):
        """HIBP requires 1.5 seconds between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < 1.5:
            wait_time = 1.5 - elapsed
            self.logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
        self.last_request_time = time.time()

    def check_hibp(self, email: Optional[str] = None, include_details: bool = True) -> Dict:
        """
        Check Have I Been Pwned for email address
        
        Args:
            email: Email address to check
            include_details: If True, return detailed breach information
        
        Returns:
            Dict with breach information
        """
        if not self.hibp_key:
            self.logger.warning("⚠️ HIBP API key not configured in .env file")
            return {
                'found': False, 
                'breaches': [], 
                'error': 'No API key configured',
                'email': email
            }

        if not email:
            return {
                'found': False, 
                'breaches': [], 
                'note': 'No email provided',
                'email': None
            }

        try:
            # Rate limiting (HIBP requirement)
            self._rate_limit()
            
            # Construct URL
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
            if include_details:
                url += "?truncateResponse=false"
            
            headers = {
                'hibp-api-key': self.hibp_key,
                'User-Agent': 'Phone-OSINT-Framework-v2'
            }

            self.logger.debug(f"🔍 Checking HIBP for: {email}")
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                breaches = response.json()
                
                # Extract breach details
                breach_details = []
                for breach in breaches:
                    breach_details.append({
                        'name': breach.get('Name'),
                        'title': breach.get('Title', breach.get('Name')),
                        'domain': breach.get('Domain'),
                        'breach_date': breach.get('BreachDate'),
                        'added_date': breach.get('AddedDate'),
                        'pwn_count': breach.get('PwnCount', 0),
                        'description': breach.get('Description', '')[:200] if include_details else '',
                        'data_classes': breach.get('DataClasses', [])
                    })
                
                self.logger.info(f"🚨 HIBP: {email} found in {len(breaches)} breaches!")
                
                return {
                    'found': True,
                    'email': email,
                    'breach_count': len(breaches),
                    'breaches': breach_details,
                    'all_breach_names': [b['name'] for b in breach_details],
                    'total_affected': sum(b.get('pwn_count', 0) for b in breach_details)
                }
                
            elif response.status_code == 404:
                self.logger.info(f"✅ HIBP: {email} clean (no breaches found)")
                return {
                    'found': False,
                    'email': email,
                    'message': 'Email not found in any breaches',
                    'clean': True
                }
                
            elif response.status_code == 401:
                self.logger.error(f"❌ HIBP: Invalid API key (HTTP 401)")
                return {
                    'found': False,
                    'email': email,
                    'error': 'Invalid API key - check HAVEIBEENPWNED_API_KEY in .env'
                }
                
            elif response.status_code == 429:
                self.logger.warning(f"⚠️ HIBP: Rate limited (HTTP 429)")
                return {
                    'found': False,
                    'email': email,
                    'error': 'Rate limited - too many requests'
                }
                
            else:
                self.logger.error(f"❌ HIBP: HTTP {response.status_code} - {response.text[:100]}")
                return {
                    'found': False,
                    'email': email,
                    'error': f'HTTP {response.status_code}: {response.text[:100]}'
                }

        except requests.exceptions.Timeout:
            self.logger.error(f"⏱️ HIBP: Timeout checking {email}")
            return {'found': False, 'email': email, 'error': 'Request timeout'}
        except Exception as e:
            self.logger.error(f"❌ HIBP check error for {email}: {e}")
            return {'found': False, 'email': email, 'error': str(e)}

    def check_all_sources(self, emails: Optional[List[str]] = None) -> Dict:
        """
        Check all breach sources for multiple emails
        
        Args:
            emails: List of email addresses to check
            
        Returns:
            Dict with comprehensive breach information
        """
        results = {
            'found': False,
            'sources_checked': ['haveibeenpwned'],
            'total_breaches': 0,
            'emails_checked': 0,
            'breached_emails': [],
            'clean_emails': [],
            'error_emails': [],
            'detailed_results': []
        }

        if not emails:
            self.logger.info("ℹ️ No emails provided for breach checking")
            results['note'] = 'No emails provided for breach checking'
            return results
        
        # Filter out invalid emails
        valid_emails = [e for e in emails if e and '@' in e and '.' in e]
        
        if not valid_emails:
            self.logger.warning("⚠️ No valid emails to check")
            results['note'] = 'No valid emails provided'
            return results
            
        self.logger.info(f"🔍 Checking {len(valid_emails)} emails against HIBP database...")
        
        for email in valid_emails:
            hibp_result = self.check_hibp(email, include_details=True)
            results['detailed_results'].append(hibp_result)
            results['emails_checked'] += 1
            
            if hibp_result.get('found'):
                results['found'] = True
                results['total_breaches'] += hibp_result.get('breach_count', 0)
                results['breached_emails'].append({
                    'email': email,
                    'breach_count': hibp_result.get('breach_count', 0),
                    'breaches': hibp_result.get('all_breach_names', []),
                    'breach_details': hibp_result.get('breaches', [])
                })
            elif hibp_result.get('clean'):
                results['clean_emails'].append(email)
            else:
                # Error occurred
                results['error_emails'].append({
                    'email': email,
                    'error': hibp_result.get('error', 'Unknown error')
                })
        
        # Summary logging
        if results['found']:
            self.logger.warning(f"🚨 BREACH ALERT: {len(results['breached_emails'])} emails compromised in {results['total_breaches']} total breaches")
            for breached in results['breached_emails']:
                self.logger.warning(f"  - {breached['email']}: {breached['breach_count']} breaches - {', '.join(breached['breaches'][:3])}")
        else:
            self.logger.info(f"✅ All {len(results['clean_emails'])} emails are clean (no breaches found)")
        
        if results['error_emails']:
            self.logger.warning(f"⚠️ Errors checking {len(results['error_emails'])} emails")
            
        return results