#!/usr/bin/env python3
import requests
import hashlib
import os
import logging
from dotenv import load_dotenv

load_dotenv('config/.env')

class BreachChecker:
    def __init__(self, phone_number):
        self.phone = phone_number
        self.hibp_key = os.getenv('HAVEIBEENPWNED_API_KEY')
        self.logger = logging.getLogger(__name__)

    def check_hibp(self, email=None):
        """Check Have I Been Pwned for email address"""
        if not self.hibp_key:
            self.logger.warning("HIBP API key not configured")
            return {'found': False, 'breaches': [], 'error': 'No API key'}

        if not email:
            # HIBP doesn't support phone number searches directly
            return {'found': False, 'breaches': [], 'note': 'No email provided for HIBP check'}

        try:
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
            headers = {
                'hibp-api-key': self.hibp_key,
                'User-Agent': 'PhoneOSINT-Framework'
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                breaches = response.json()
                return {
                    'found': True,
                    'email': email,
                    'breach_count': len(breaches),
                    'breaches': [breach['Name'] for breach in breaches[:5]]  # Limit to 5 for display
                }
            elif response.status_code == 404:
                return {
                    'found': False,
                    'email': email,
                    'message': 'Email not found in breaches'
                }
            else:
                return {
                    'found': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }

        except Exception as e:
            self.logger.error(f"HIBP check error: {e}")
            return {'found': False, 'error': str(e)}

    def check_all_sources(self, emails=None):
        """Check all breach sources"""
        results = {
            'found': False,
            'sources_checked': ['haveibeenpwned'],
            'breaches': [],
            'emails_checked': []
        }

        if emails:
            for email in emails:
                hibp_result = self.check_hibp(email)
                results['emails_checked'].append(hibp_result)
                if hibp_result.get('found'):
                    results['found'] = True
                    results['breaches'].extend(hibp_result.get('breaches', []))
        else:
            # No emails provided, just return basic structure
            results['note'] = 'No emails provided for breach checking'

        return results