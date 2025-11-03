#!/usr/bin/env python3
"""
Email Discovery & Intelligence Engine
Comprehensive email enumeration using multiple sources and techniques
"""

import os
import re
import requests
import logging
import time
import random
from typing import Dict, List, Set, Optional
from urllib.parse import quote
from pathlib import Path
from dotenv import load_dotenv
from .api_utils import GoogleAPIClient, BingAPIClient, YandexAPIClient, UnifiedSearchClient
from .email_validator import EmailValidator

load_dotenv('config/.env')

class EmailHunter:
    """
    Advanced email discovery engine using multiple techniques and sources
    Designed to discover email addresses associated with phone numbers and names
    """

    def __init__(self, phone_number: str, identity_data: Dict = None):
        self.phone = phone_number
        self.identity_data = identity_data or {}
        self.logger = logging.getLogger(__name__)

        # API credentials
        self.hunter_api_key = os.getenv('HUNTER_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_cse_id = os.getenv('GOOGLE_CSE_ID')
        # Support both SERPAPI_KEY and BING_API_KEY (backward compat)
        self.serpapi_key = os.getenv('SERPAPI_KEY') or os.getenv('BING_API_KEY')
        
        # Log API availability for debugging
        api_status = []
        if self.google_api_key: api_status.append("Google")
        if self.serpapi_key: api_status.append("SerpAPI") 
        if self.hunter_api_key: api_status.append("Hunter.io")
        self.logger.info(f"🎯 Available APIs: {', '.join(api_status) if api_status else 'None configured'}")
        self.yandex_api_key = os.getenv('YANDEX_API_KEY')
        self.yandex_user_id = os.getenv('YANDEX_USER_ID')
        self.hibp_api_key = os.getenv('HAVEIBEENPWNED_API_KEY')

        # Multi-engine search client with enhanced Google (IPRoyal proxy support)
        # Try proxy-enhanced Google client first, fallback to standard
        google_client = None
        if self.google_api_key and self.google_cse_id:
            try:
                from .proxy_enhanced_google import create_enhanced_google_client
                google_client = create_enhanced_google_client(self.google_api_key, self.google_cse_id, use_iproyal=True)
                self.logger.info("🚀 Using IPRoyal-enhanced Google client for massive capacity")
            except Exception as e:
                # Fallback to standard Google client
                self.logger.warning(f"IPRoyal integration failed, using standard Google: {e}")
                google_client = GoogleAPIClient(self.google_api_key, self.google_cse_id)
        
        bing_client = BingAPIClient(self.serpapi_key) if self.serpapi_key else None  # BingAPIClient is alias for SerpApiClient
        yandex_client = YandexAPIClient(self.yandex_api_key, self.yandex_user_id) if self.yandex_api_key else None
        self.search_client = UnifiedSearchClient(google_client, bing_client, yandex_client, enable_ddg_fallback=True)

        # Clean phone number for processing
        self.clean_phone = re.sub(r'[^\d]', '', phone_number)

        # Extract potential domains and search terms from identity data
        self.search_terms = self._extract_search_terms()

    def _extract_search_terms(self) -> List[str]:
        """Extract search terms from identity data and phone number"""
        terms = []

        # Add phone number variations
        if len(self.clean_phone) == 11 and self.clean_phone.startswith('1'):
            terms.extend([
                self.clean_phone,
                self.clean_phone[1:],  # Without country code
                f"{self.clean_phone[1:4]}{self.clean_phone[4:7]}{self.clean_phone[7:]}",
                f"{self.clean_phone[1:4]}-{self.clean_phone[4:7]}-{self.clean_phone[7:]}"
            ])

        # Add identity terms
        if self.identity_data:
            if self.identity_data.get('first_name'):
                terms.append(self.identity_data['first_name'].lower())
            if self.identity_data.get('last_name'):
                terms.append(self.identity_data['last_name'].lower())
            if self.identity_data.get('first_name') and self.identity_data.get('last_name'):
                first = self.identity_data['first_name'].lower()
                last = self.identity_data['last_name'].lower()
                terms.extend([
                    f"{first}.{last}",
                    f"{first}{last}",
                    f"{first}_{last}",
                    f"{first[0]}{last}",  # j.doe, jdoe
                    f"{first}{last[0]}"   # john.d, johnd
                ])

        return list(set(terms))  # Remove duplicates

    def hunt_with_hunter_io(self, domain: str = None) -> Dict:
        """Hunt for emails using Hunter.io API (business domains only)"""
        if not self.hunter_api_key:
            self.logger.warning("Hunter.io API key not configured")
            return {'found': False, 'emails': [], 'error': 'No API key'}

        results = {
            'found': False,
            'emails': [],
            'method': 'hunter.io',
            'domains_searched': []
        }

        # Hunter.io API limitation: Cannot search consumer email providers
        # (They return 400 Bad Request for gmail.com, yahoo.com, etc.)
        consumer_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'icloud.com', 'protonmail.com']

        if domain and domain in consumer_domains:
            self.logger.info(f"Hunter.io API limitation: Cannot search consumer domain {domain}")
            return results

        # If no specific domain provided, we can't do Hunter.io domain search
        # Hunter.io requires a specific business domain to search
        if not domain:
            self.logger.info("Hunter.io requires a specific business domain - no domain-wide search for consumer emails")
            return results

        search_domains = [domain]

        for search_domain in search_domains:
            try:
                # Search for emails on domain
                url = "https://api.hunter.io/v2/domain-search"
                params = {
                    'domain': search_domain,
                    'api_key': self.hunter_api_key,
                    'limit': 100
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                if data.get('data', {}).get('emails'):
                    domain_emails = []
                    for email_data in data['data']['emails']:
                        email = email_data.get('value', '')
                        if email and self._is_potential_match(email):
                            domain_emails.append({
                                'email': email,
                                'confidence': email_data.get('confidence', 0),
                                'sources': email_data.get('sources', []),
                                'domain': search_domain
                            })

                    if domain_emails:
                        results['emails'].extend(domain_emails)
                        results['found'] = True
                        self.logger.info(f"Hunter.io found {len(domain_emails)} potential emails on {search_domain}")

                results['domains_searched'].append(search_domain)

                # Rate limiting
                time.sleep(1)

            except Exception as e:
                self.logger.warning(f"Hunter.io search error for {search_domain}: {e}")
                continue

        return results

    def hunt_with_email_verification(self, email_candidates: List[str]) -> Dict:
        """Verify if email addresses exist using Hunter.io email verification"""
        if not self.hunter_api_key:
            return {'found': False, 'verified_emails': [], 'error': 'No API key'}

        results = {
            'found': False,
            'verified_emails': [],
            'method': 'email_verification'
        }

        for email in email_candidates:
            try:
                url = "https://api.hunter.io/v2/email-verifier"
                params = {
                    'email': email,
                    'api_key': self.hunter_api_key
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                if data.get('data', {}).get('result') in ['deliverable', 'risky']:
                    results['verified_emails'].append({
                        'email': email,
                        'result': data['data']['result'],
                        'score': data['data'].get('score', 0),
                        'regexp': data['data'].get('regexp', False),
                        'gibberish': data['data'].get('gibberish', False),
                        'disposable': data['data'].get('disposable', False)
                    })
                    results['found'] = True
                    self.logger.info(f"Verified email: {email} ({data['data']['result']})")

                # Rate limiting
                time.sleep(1)

            except Exception as e:
                self.logger.warning(f"Email verification error for {email}: {e}")
                continue

        return results

    def hunt_with_google_dorking(self) -> Dict:
        """Use Google Custom Search API to find real emails associated with phone number and name"""
        results = {
            'found': False,
            'emails': [],
            'method': 'google_dorking',
            'queries_executed': 0,
            'results_parsed': 0
        }

        google_api_key = os.getenv('GOOGLE_API_KEY')
        google_cse_id = os.getenv('GOOGLE_CSE_ID')

        if not google_api_key or not google_cse_id:
            self.logger.warning("Google Custom Search API credentials not configured")
            return results

        try:
            search_queries = []
            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

            # PRIORITY-BASED QUERY BUILDING - NAME FIRST!
            full_name = None
            first_name = self.identity_data.get('first_name')
            last_name = self.identity_data.get('last_name')

            if first_name and last_name:
                full_name = f"{first_name} {last_name}"

            # PRIORITY 1: Name-based email searches (MOST EFFECTIVE)
            if full_name:
                self.logger.info(f"🎯 Email hunting with NAME: {full_name}")
                search_queries.extend([
                    f'"{full_name}" email',
                    f'"{full_name}" contact email',
                    f'"{full_name}" "@" email',
                ])
                # Only add ONE phone+name combo query
                search_queries.append(f'"{full_name}" {self.phone}')

            # PRIORITY 2: Phone-based searches (ONLY if no name, fallback only)
            else:
                self.logger.warning(f"⚠️ No name available - falling back to limited phone searches")
                phone_clean = re.sub(r'[^\d]', '', self.phone)
                if len(phone_clean) >= 10:
                    # Just use the most common format - don't waste queries on all variations
                    formatted = f"({phone_clean[-10:-7]}) {phone_clean[-7:-4]}-{phone_clean[-4:]}"
                    search_queries.extend([
                        f'"{formatted}" email',
                        f'"{self.phone}" contact'
                    ])

            # Limit to 4 queries maximum (down from 6)
            search_queries = search_queries[:4]
            self.logger.info(f"Google Custom Search: executing {len(search_queries)} queries (NAME-prioritized)")

            discovered_emails = set()

            for query in search_queries:
                try:
                    # Email queries: use 'email' type for Google priority
                    data = self.search_client.search(query, query_type='email', num_results=10)
                    if data is None:
                        self.logger.warning(f"Search failed for query: {query}")
                        continue

                    results['queries_executed'] += 1

                    # Parse search results for email addresses
                    if 'items' in data:
                        for item in data['items']:
                            # Check title and snippet for emails
                            text_to_search = f"{item.get('title', '')} {item.get('snippet', '')}"
                            found_emails = email_pattern.findall(text_to_search)

                            for email in found_emails:
                                email = email.lower()
                                # Validate that this email might be related to our target
                                if self._is_potential_match(email):
                                    discovered_emails.add(email)
                                    results['results_parsed'] += 1

                except Exception as e:
                    self.logger.warning(f"Google search error for query '{query}': {e}")
                    continue

            # Convert discovered emails to result format
            for email in discovered_emails:
                results['emails'].append({
                    'email': email,
                    'confidence': 0.7,  # Good confidence for Google search results
                    'source': 'google_custom_search'
                })

            results['found'] = len(results['emails']) > 0

            if results['found']:
                self.logger.info(f"Google Custom Search found {len(results['emails'])} real emails")
            else:
                self.logger.info("Google Custom Search found no matching emails")

        except Exception as e:
            self.logger.error(f"Google dorking error: {e}")

        return results

    def hunt_with_phone_breach_search(self) -> Dict:
        """Search for phone number in Have I Been Pwned and breach intelligence databases"""
        results = {
            'found': False,
            'emails': [],
            'method': 'phone_breach_search',
            'sources_checked': []
        }

        hibp_api_key = os.getenv('HAVEIBEENPWNED_API_KEY')

        try:
            phone_variations = []
            phone_clean = re.sub(r'[^\d]', '', self.phone)

            if len(phone_clean) >= 10:
                phone_variations.extend([
                    self.phone,
                    phone_clean,
                    phone_clean[-10:],  # Last 10 digits
                    f"({phone_clean[-10:-7]}) {phone_clean[-7:-4]}-{phone_clean[-4:]}",
                    f"{phone_clean[-10:-7]}-{phone_clean[-7:-4]}-{phone_clean[-4:]}",
                    f"{phone_clean[-10:-7]}.{phone_clean[-7:-4]}.{phone_clean[-4:]}"
                ])

            self.logger.info(f"Searching breach databases for {len(phone_variations)} phone variations")

            # Method 1: Use HIBP API with enhanced email pattern generation
            if hibp_api_key:
                self.logger.info("Checking Have I Been Pwned API...")
                results['sources_checked'].append('haveibeenpwned')

                # Enhanced potential email generation combining phone + name data
                potential_emails = []
                
                # Get name data for better email patterns
                first_name = self.identity_data.get('first_name', '').lower().strip()
                last_name = self.identity_data.get('last_name', '').lower().strip()
                
                if len(phone_clean) >= 10:
                    area_code = phone_clean[-10:-7]
                    number_part = phone_clean[-7:]

                    # Personal email domains (where breach data is most common)
                    personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
                    
                    # Pattern 1: Phone-based emails (common for older accounts)
                    for domain in personal_domains:
                        potential_emails.extend([
                            f"{phone_clean}@{domain}",
                            f"{area_code}{number_part}@{domain}",
                            f"{phone_clean[-4:]}@{domain}"  # Last 4 digits
                        ])
                    
                    # Pattern 2: Name + phone number combinations (if name available)
                    if first_name and last_name:
                        name_patterns = [
                            f"{first_name}.{last_name}",
                            f"{first_name}{last_name}",
                            f"{first_name[0]}{last_name}"
                        ]
                        for pattern in name_patterns:
                            for domain in personal_domains[:3]:  # Top 3 domains
                                potential_emails.append(f"{pattern}@{domain}")
                                potential_emails.append(f"{pattern}{area_code[-2:]}@{domain}")  # Add area code suffix

                # Check each potential email against HIBP
                for email in potential_emails[:8]:  # Limit to avoid rate limiting
                    try:
                        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
                        headers = {
                            'hibp-api-key': hibp_api_key,
                            'User-Agent': 'Phone-OSINT-Framework'
                        }

                        response = requests.get(url, headers=headers, timeout=10)

                        if response.status_code == 200:
                            # Email found in breaches
                            breach_data = response.json()
                            results['emails'].append({
                                'email': email,
                                'confidence': 0.8,  # High confidence - found in actual breaches
                                'breaches': len(breach_data),
                                'source': 'hibp_breach_database'
                            })
                            results['found'] = True
                            self.logger.info(f"Found breached email: {email} ({len(breach_data)} breaches)")
                        elif response.status_code == 404:
                            # Email not found in breaches (doesn't mean it doesn't exist)
                            pass

                        # Rate limiting for HIBP API
                        time.sleep(1.5)

                    except Exception as e:
                        self.logger.warning(f"HIBP check error for {email}: {e}")
                        continue
            else:
                self.logger.warning("Have I Been Pwned API key not configured")

            # Method 2: Intelligence X-style search (placeholder for future integration)
            self.logger.info("Breach database search completed")
            results['sources_checked'].append('pattern_validation')

        except Exception as e:
            self.logger.error(f"Phone breach search error: {e}")

        return results

    def hunt_with_public_records_scraping(self) -> Dict:
        """Scrape search engine results for partially revealed public records"""
        results = {
            'found': False,
            'emails': [],
            'method': 'public_records_scraping',
            'sites_scraped': []
        }

        try:
            # Target sites that commonly leak partial data in search results
            # Based on your expertise with Intelius, InstantCheckmate, TruthFinder, etc.
            target_sites = [
                'whitepages.com',
                'spokeo.com',
                'intelius.com',
                'instantcheckmate.com',
                'truthfinder.com',
                'beenverified.com',
                'peoplefinder.com',
                'addresses.com',
                'fastpeoplesearch.com'
            ]

            google_api_key = os.getenv('GOOGLE_API_KEY')
            google_cse_id = os.getenv('GOOGLE_CSE_ID')

            if not google_api_key or not google_cse_id:
                self.logger.warning("Google Custom Search API not configured for public records scraping")
                return results

            # PRIORITY-BASED SEARCH - NAME FIRST!
            full_name = None
            first_name = self.identity_data.get('first_name')
            last_name = self.identity_data.get('last_name')

            if first_name and last_name:
                full_name = f"{first_name} {last_name}"

            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            discovered_emails = set()

            # Search targeted sites with NAME (much more effective than phone)
            if full_name:
                self.logger.info(f"🎯 Public records scraping with NAME: {full_name}")
                for site in target_sites[:3]:  # Limit to 3 sites max
                    try:
                        # Query: NAME + site + email indicators
                        query = f'"{full_name}" site:{site} "@"'

                        # People search: use 'people' type for Yandex priority
                        data = self.search_client.search(query, query_type='people', num_results=5)
                        if data is None:
                            self.logger.warning(f"Public records scraping error for {site}: Search failed")
                            continue

                        results['sites_scraped'].append(site)

                        if 'items' in data:
                            for item in data['items']:
                                # Extract from title and snippet (the "partially revealed" data)
                                text_content = f"{item.get('title', '')} {item.get('snippet', '')}"

                                # Look for email addresses in the leaked snippets
                                found_emails = email_pattern.findall(text_content)

                                for email in found_emails:
                                    email = email.lower()
                                    # Validate this looks like a real email (not a pattern)
                                    if '@' in email and '.' in email.split('@')[1]:
                                        # Additional validation: not obviously fake
                                        if not any(fake in email for fake in ['example', 'test', 'sample', 'noreply']):
                                            discovered_emails.add(email)

                    except Exception as e:
                        self.logger.warning(f"Public records scraping error for {site}: {e}")
                        continue

            # Fallback: Phone-based searches (only if no name)
            else:
                self.logger.warning(f"⚠️ No name for public records - using limited phone search")
                # Just search ONE site with ONE phone format
                formatted = f"({self.clean_phone[-10:-7]}) {self.clean_phone[-7:-4]}-{self.clean_phone[-4:]}"
                query = f'"{formatted}" site:whitepages.com "@"'

                try:
                    # Fallback phone search: use 'people' type
                    data = self.search_client.search(query, query_type='people', num_results=5)
                    if data and 'items' in data:
                        results['sites_scraped'].append('whitepages.com')
                        for item in data['items']:
                            text_content = f"{item.get('title', '')} {item.get('snippet', '')}"
                            found_emails = email_pattern.findall(text_content)
                            for email in found_emails:
                                email = email.lower()
                                if '@' in email and '.' in email.split('@')[1]:
                                    if not any(fake in email for fake in ['example', 'test', 'sample', 'noreply']):
                                        discovered_emails.add(email)
                except Exception as e:
                    self.logger.warning(f"Phone-based public records search failed: {e}")

            # Convert discovered emails to result format
            for email in discovered_emails:
                results['emails'].append({
                    'email': email,
                    'confidence': 0.75,  # Good confidence - found in search results
                    'source': 'public_records_scraping',
                    'method': 'search_engine_partial_reveal'
                })

            results['found'] = len(results['emails']) > 0

            if results['found']:
                self.logger.info(f"Public records scraping found {len(results['emails'])} emails from {len(results['sites_scraped'])} sites")
            else:
                self.logger.info(f"No emails found via public records scraping of {len(results['sites_scraped'])} sites")

        except Exception as e:
            self.logger.error(f"Public records scraping error: {e}")

        return results

    def hunt_with_employment_intelligence(self) -> Dict:
        """Use employment intelligence to generate contextual email patterns"""
        results = {
            'found': False,
            'emails': [],
            'method': 'employment_intelligence',
            'employment_data': {}
        }

        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from scripts.employment_hunter import EmploymentHunter

            # Initialize employment hunter
            emp_hunter = EmploymentHunter(self.phone, self.identity_data)
            employment_results = emp_hunter.hunt_comprehensive()

            results['employment_data'] = employment_results

            if employment_results['found']:
                # Get contextual email candidates
                contextual_emails = employment_results.get('contextual_emails', [])

                # Add to results with enhanced metadata
                for email_data in contextual_emails:
                    results['emails'].append({
                        'email': email_data['email'],
                        'confidence': email_data['confidence'],
                        'source': email_data['source'],
                        'method': email_data['method'],
                        'context': email_data.get('company_domain', email_data.get('inferred_from', ''))
                    })

                results['found'] = len(contextual_emails) > 0

                if results['found']:
                    employers = len(employment_results['employment_data'].get('employers', []))
                    domains = len(employment_results['employment_data'].get('company_domains', []))
                    self.logger.info(f"Employment intelligence found {employers} employers, {domains} domains, generated {len(contextual_emails)} contextual emails")

        except Exception as e:
            self.logger.error(f"Employment intelligence hunting error: {e}")

        return results

    def _is_potential_match(self, email: str) -> bool:
        """Check if an email might be associated with our target (improved filtering)"""
        email_lower = email.lower()
        
        # Skip obviously fake/generic emails
        fake_patterns = [
            'example', 'test', 'sample', 'noreply', 'no-reply', 'admin', 'info@', 
            'contact@', 'support@', 'hello@', 'webmaster@', 'postmaster@'
        ]
        if any(fake in email_lower for fake in fake_patterns):
            return False

        # Get target identity info
        first_name = self.identity_data.get('first_name', '').lower().strip()
        last_name = self.identity_data.get('last_name', '').lower().strip()
        
        # HIGH CONFIDENCE: Email contains target's name parts
        if first_name and first_name in email_lower:
            return True
        if last_name and len(last_name) > 3 and last_name in email_lower:  # Avoid short names
            return True
            
        # MEDIUM CONFIDENCE: Check against generated search terms
        for term in self.search_terms:
            if len(term) > 3 and term.lower() in email_lower:  # Avoid short terms
                return True

        # LOW CONFIDENCE: Phone number patterns in email (uncommon but possible)  
        if len(self.clean_phone) >= 10:
            phone_parts = [
                self.clean_phone[-4:],      # Last 4 digits
                self.clean_phone[-7:-4],    # Area code part
                self.clean_phone[-10:-7],   # Area code
            ]
            if any(part in email_lower and len(part) >= 3 for part in phone_parts):
                return True

        # For personal investigations, be more inclusive with common personal domains
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        domain = email_lower.split('@')[-1] if '@' in email_lower else ''
        
        # If it's from a personal domain and contains reasonable name-like parts, consider it
        if domain in personal_domains:
            # Check if email username part looks name-like
            username = email_lower.split('@')[0] if '@' in email_lower else ''
            if any(char.isalpha() for char in username) and len(username) >= 4:
                # Additional check: does it have name-like structure? 
                if '.' in username or '_' in username:  # john.doe, john_doe patterns
                    return True

        return False

    def hunt_comprehensive(self, skip_pattern_generation=False, skip_public_records=False) -> Dict:
        """
        Run comprehensive email hunting using all available methods
        
        Args:
            skip_pattern_generation: If True, skip Phase 3 pattern generation (when we have verified emails)
            skip_public_records: If True, skip public records scraping (when we have verified emails)
        """
        self.logger.info(f"🎯 Starting comprehensive email hunting for: {self.phone}")
        self.skip_pattern_generation = skip_pattern_generation
        self.skip_public_records = skip_public_records

        all_results = {
            'found': False,
            'emails': [],
            'verified_emails': [],
            'methods_used': [],
            'confidence_score': 0.0,
            'search_summary': {},
            'discovery_note': 'Focused on finding real emails linked to phone/name, not generated patterns'
        }

        # Method 0: Add known email from user input (highest priority)
        if self.identity_data.get('known_email'):
            known_email = self.identity_data['known_email'].strip().lower()
            if known_email and '@' in known_email:
                all_results['emails'].append({
                    'email': known_email,
                    'confidence': 1.0,  # Highest confidence - user provided
                    'source': 'user_provided',
                    'method': 'manual_entry'
                })
                all_results['methods_used'].append('user_provided')
                all_results['found'] = True
                self.logger.info(f"✅ User-provided email added: {known_email}")

        # PHASE 1: Discover Real Data (profiles, usernames, emails from actual sources)
        self.logger.info("=" * 70)
        self.logger.info("🔍 PHASE 1: DISCOVERING REAL DATA FROM ACTUAL SOURCES")
        self.logger.info("🚫 NO PATTERN GUESSING - ONLY REAL DISCOVERED DATA")
        self.logger.info("=" * 70)
        
        # Method 1: LinkedIn/GitHub profile discovery and username extraction
        # This discovers REAL usernames from actual profile URLs
        linkedin_results = self.hunt_with_personal_google_search()
        all_results['search_summary']['linkedin_discovery'] = linkedin_results
        if linkedin_results['found']:
            all_results['emails'].extend(linkedin_results['emails'])
            all_results['methods_used'].append('linkedin_discovery')
            
            # Count REAL discovered usernames (not patterns!)
            real_usernames = self.identity_data.get('usernames', [])
            self.logger.info(f"✅ Profile discovery: {len(real_usernames)} REAL usernames extracted from URLs")
            self.logger.info(f"📝 Real usernames: {real_usernames[:5]}")

        # Method 2: theHarvester email discovery (find actual emails from search engines)
        # SKIP FOR NOW - theHarvester is searching by domain which doesn't work for personal investigations
        self.logger.info("⏭️ Skipping theHarvester domain search - not effective for personal email discovery")
        # harvester_results = self.hunt_with_theharvester()  # DISABLED

        # Method 3: Phone breach database search (EXCELLENT for personal emails)
        breach_results = self.hunt_with_phone_breach_search()
        all_results['search_summary']['phone_breach_search'] = breach_results
        if breach_results['found']:
            all_results['emails'].extend(breach_results['emails'])
            all_results['methods_used'].append('phone_breach_search')
            self.logger.info(f"✅ Breach search found {len(breach_results['emails'])} emails")

        # Method 4: Enhanced social media bio scraping (discovers more usernames + emails)
        social_results = self.hunt_with_social_media_bios()
        all_results['search_summary']['social_media_bios'] = social_results
        if social_results['found']:
            all_results['emails'].extend(social_results['emails'])
            all_results['methods_used'].append('social_media_bios')
            self.logger.info(f"✅ Social media bios found {len(social_results['emails'])} personal emails")

        # PHASE 2: Expand on REAL discovered usernames (NO PATTERN GUESSING!)
        real_usernames = [u for u in self.identity_data.get('usernames', []) if u and len(u) > 2]
        
        if real_usernames and len(real_usernames) > 0:
            self.logger.info("=" * 70)
            self.logger.info("🔍 PHASE 2: EXPANDING REAL DISCOVERED USERNAMES")
            self.logger.info(f"📝 Found {len(real_usernames)} VERIFIED usernames from actual profiles:")
            for i, username in enumerate(real_usernames[:10], 1):
                self.logger.info(f"   {i}. {username}")
            self.logger.info("=" * 70)
            
            # USER PROMPT: Ask which usernames to drill down on
            usernames_to_search = self._prompt_username_selection(real_usernames)
            
            if usernames_to_search:
                self.logger.info(f"🎯 User selected {len(usernames_to_search)} usernames for deep search")
                
                # Sherlock: Search SELECTED REAL usernames across 400+ platforms
                for username in usernames_to_search:
                    self.logger.info(f"🔍 Sherlock searching REAL username: {username}")
                    # Call Sherlock directly with this specific username
                    sherlock_result = self._search_username_with_sherlock(username)
                    if sherlock_result.get('found'):
                        self.logger.info(f"✅ {username} found on {sherlock_result.get('platforms_count', 0)} platforms")
                
                # Maigret: Search SELECTED REAL usernames (if user wants comprehensive search)
                if self._confirm_maigret_search(len(usernames_to_search)):
                    self.logger.info("🎨 Running Maigret comprehensive search (this will take several minutes)...")
                    maigret_results = self.hunt_with_maigret()
                    all_results['search_summary']['maigret'] = maigret_results
                    if maigret_results.get('found'):
                        all_results['methods_used'].append('maigret')
                        self.logger.info(f"✅ Maigret found {maigret_results.get('total_profiles_found', 0)} total profiles")
                else:
                    self.logger.info("⏭️ Skipping Maigret (user declined - saves time)")
            else:
                self.logger.info("⏭️ User skipped username expansion - proceeding to next phase")
        else:
            self.logger.info("=" * 70)
            self.logger.info("ℹ️ PHASE 2 SKIPPED: No real usernames discovered from profiles")
            self.logger.info("=" * 70)

        # Company-based email discovery (if employers were discovered)
        if self.identity_data.get('companies'):
            company_results = self.hunt_with_company_correlation()
            all_results['search_summary']['company_correlation'] = company_results
            if company_results['found']:
                all_results['emails'].extend(company_results['emails'])
                all_results['methods_used'].append('company_correlation')
                self.logger.info(f"✅ Company correlation found {len(company_results['emails'])} work emails")

        # Method 5: Public records scraping (CONDITIONAL - skip if we have verified emails)
        if self.skip_public_records:
            self.logger.info("🎯 Public records scraping: SKIPPED (have verified emails from breach data)")
        else:
            scraping_results = self.hunt_with_public_records_scraping()
            all_results['search_summary']['public_records'] = scraping_results
            if scraping_results['found']:
                all_results['emails'].extend(scraping_results['emails'])
                all_results['methods_used'].append('public_records_scraping')
                self.logger.info(f"✅ Public records found {len(scraping_results['emails'])} emails")

        # PHASE 3: Pattern Generation (CONDITIONAL - skip if we have verified emails from breach data)
        if self.skip_pattern_generation:
            self.logger.info("=" * 70)
            self.logger.info("⏭️ PHASE 3 SKIPPED: Pattern generation (have verified emails from breach data)")
            self.logger.info("=" * 70)
        else:
            real_emails_found = len([e for e in all_results['emails'] if e.get('source') != 'personal_pattern_generation'])
            
            if real_emails_found < 5:  # Only generate patterns if we have few real emails
                self.logger.info("=" * 70)
                self.logger.info("🔍 PHASE 3: PATTERN GENERATION (LAST RESORT)")
                self.logger.info(f"📝 Only {real_emails_found} real emails found - generating patterns as fallback")
                self.logger.info("=" * 70)
                
                if self.identity_data.get('first_name') and self.identity_data.get('last_name'):
                    pattern_results = self.hunt_with_personal_email_patterns()
                    if pattern_results['found']:
                        all_results['emails'].extend(pattern_results['emails'])
                        all_results['methods_used'].append('personal_patterns')
                        all_results['search_summary']['personal_patterns'] = pattern_results
                        self.logger.info(f"✅ Generated {len(pattern_results['emails'])} pattern-based email candidates (for validation)")
            else:
                self.logger.info(f"✅ PHASE 3 SKIPPED: Found {real_emails_found} real emails - pattern generation not needed!")

        # REVOLUTIONARY VALIDATION: Use Holehe to validate emails by checking platform existence
        if all_results['emails']:
            self.logger.info(f"🔍 Advanced validation of {len(all_results['emails'])} email candidates...")

            # Separate by source type
            pattern_emails = [e for e in all_results['emails'] if e.get('source') == 'personal_pattern_generation']
            discovered_emails_list = [e for e in all_results['emails'] if e.get('source') != 'personal_pattern_generation']

            self.logger.info(f"📊 Breakdown: {len(discovered_emails_list)} discovered, {len(pattern_emails)} pattern-generated")

            # Simplified validation for debugging (temporarily disable Holehe)
            self.logger.info("🔄 Using simplified DNS validation for debugging")
            validator = EmailValidator()

            # Get all unique emails for validation
            all_unique_emails = []
            email_lookup = {}  # Map email -> original entry
            
            for email_entry in all_results['emails']:
                email = email_entry['email']
                all_unique_emails.append(email)
                email_lookup[email] = email_entry

            # Batch DNS validation
            if all_unique_emails:
                self.logger.info(f"🔍 Validating {len(all_unique_emails)} emails via DNS...")
                validation_results = validator.validate_batch(all_unique_emails[:20], check_smtp=False)  # Limit to 20 for performance
                validation_map = {r['email']: r for r in validation_results}

                # Update emails with validation status  
                validated_emails = []
                for email, email_entry in email_lookup.items():
                    validation = validation_map.get(email, {})
                    
                    email_entry['validation'] = {
                        'valid': validation.get('valid', False),
                        'status': validation.get('status', 'unknown'),
                        'confidence': validation.get('confidence', 0.0),
                        'mx_records': len(validation.get('mx_records', []))
                    }
                    
                    # Only keep emails that pass basic validation OR are from high-confidence sources
                    if (validation.get('valid') or 
                        email_entry.get('source') in ['social_media_bio', 'theharvester', 'personal_google_search']):
                        validated_emails.append(email_entry)

                # KEEP ALL EMAILS - just mark validation status (don't overwrite!)
                # all_results['emails'] already has all discovered emails
                # Just update each with validation info
                self.logger.info(f"📧 Validation complete: {len(validated_emails)} emails passed filters out of {len(all_unique_emails)} total")
            else:
                self.logger.warning("No emails to validate")

            # Calculate validation stats
            verified_count = len(all_results.get('verified_emails', []))
            total_count = len(all_results['emails'])
            self.logger.info(f"📧 Advanced validation complete: {verified_count} verified via platforms, {total_count} total candidates")

        # Calculate overall results
        total_emails = len(all_results['emails']) + len(all_results['verified_emails'])
        all_results['found'] = total_emails > 0

        # Calculate confidence score based on discovery method quality (enhanced with OSINT tools)
        if all_results['found']:
            confidence = 0.0

            # HIGHEST confidence: Holehe-validated emails (confirmed to exist on platforms)
            if 'holehe_validation' in all_results['methods_used']:
                confidence += 1.0
                self.logger.info("🔥 HIGHEST CONFIDENCE: Emails validated via Holehe platform existence")

            # HIGH confidence: theHarvester discoveries (real emails from multiple search engines)
            if 'theharvester' in all_results['methods_used']:
                confidence += 0.9
                self.logger.info("🎯 HIGH CONFIDENCE: Real emails discovered via theHarvester")

            # HIGH confidence: Sherlock username discoveries (leads to targeted searches)
            if 'sherlock' in all_results['methods_used']:
                confidence += 0.8
                self.logger.info("🎯 HIGH CONFIDENCE: Usernames discovered via Sherlock")

            # HIGH confidence: Social media bio scraping (emails from actual profiles)
            if 'social_media_bios' in all_results['methods_used']:
                confidence += 0.8

            # GOOD confidence: Verified emails (any source)
            if all_results.get('verified_emails'):
                confidence += 0.7

            # GOOD confidence: Public records scraping (real data leakage)
            if 'public_records_scraping' in all_results['methods_used']:
                confidence += 0.7

            # MEDIUM confidence: Breach database findings
            if 'phone_breach_search' in all_results['methods_used']:
                confidence += 0.6

            # MEDIUM confidence: Personal Google search
            if 'google_dorking' in all_results['methods_used']:
                confidence += 0.5

            # LOWER confidence: Correlation methods (educated guesses)
            if 'username_correlation' in all_results['methods_used']:
                confidence += 0.4
            if 'company_correlation' in all_results['methods_used']:
                confidence += 0.4

            # BASELINE: Pattern generation (still valuable as fallback)
            if 'personal_patterns' in all_results['methods_used']:
                confidence += 0.3

            # Bonus for multiple discovery methods (comprehensive investigation)
            method_count = len(all_results['methods_used'])
            if method_count >= 4:
                confidence += 0.3
            elif method_count >= 2:
                confidence += 0.15

            all_results['confidence_score'] = min(confidence, 1.0)

        # Summary logging
        if all_results['found']:
            self.logger.info(f"🎯 EMAIL HUNTING COMPLETE: {total_emails} emails found, confidence: {all_results['confidence_score']:.2f}")
        else:
            self.logger.warning("❌ Email hunting unsuccessful")

        return all_results

    def hunt_with_personal_email_patterns(self) -> Dict:
        """Generate personal email addresses using comprehensive patterns for individual investigations"""
        results = {
            'found': False,
            'emails': [],
            'method': 'personal_patterns',
            'note': 'Generated comprehensive personal email patterns - higher success rate for individuals'
        }

        first_name = self.identity_data.get('first_name', '').lower().strip()
        last_name = self.identity_data.get('last_name', '').lower().strip()

        if not first_name or not last_name:
            return results

        # Remove common prefixes/suffixes and clean names
        first_clean = re.sub(r'^(mr|ms|mrs|dr|prof)\.?\s*', '', first_name)
        last_clean = re.sub(r'\s*(jr|sr|ii|iii|iv)\.?$', '', last_name)

        # Enhanced personal email patterns (most common for individuals)
        patterns = [
            f"{first_clean}.{last_clean}",         # john.doe (most common)
            f"{first_clean}{last_clean}",          # johndoe
            f"{first_clean}_{last_clean}",         # john_doe
            f"{first_clean[0]}.{last_clean}",      # j.doe
            f"{first_clean}{last_clean[0]}",       # johnd
            f"{first_clean[0]}{last_clean}",       # jdoe
            f"{last_clean}.{first_clean}",         # doe.john (less common)
            f"{first_clean}{last_clean}123",       # johndoe123 (common variation)
            f"{first_clean}.{last_clean}1",        # john.doe1
        ]

        # Personal email domains (prioritized by popularity for individuals)
        personal_domains = [
            'gmail.com',    # #1 personal email provider
            'yahoo.com',    # #2 personal email provider
            'hotmail.com',  # Still widely used
            'outlook.com',  # Microsoft's newer offering
            'icloud.com',   # Apple users
            'aol.com',      # Older users still use this
        ]

        # Generate comprehensive combinations
        for pattern in patterns:
            for domain in personal_domains:
                email = f"{pattern}@{domain}"
                # Higher confidence for more common patterns
                confidence = 0.6 if domain in ['gmail.com', 'yahoo.com'] and '.' in pattern else 0.4
                
                results['emails'].append({
                    'email': email,
                    'confidence': confidence,
                    'source': 'personal_pattern_generation',
                    'method': 'personal_patterns',
                    'pattern': pattern,
                    'domain': domain
                })

        results['found'] = len(results['emails']) > 0
        self.logger.info(f"Generated {len(results['emails'])} personal email patterns for validation")
        return results

    def hunt_with_personal_google_search(self) -> Dict:
        """Enhanced Google search specifically targeting personal email discovery"""
        results = {
            'found': False,
            'emails': [],
            'method': 'personal_google_search',
            'queries_executed': 0,
            'results_parsed': 0
        }

        # Get name information
        first_name = self.identity_data.get('first_name', '').strip()
        last_name = self.identity_data.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()

        if not full_name:
            self.logger.warning("No name available for personal Google email search")
            return results

        # Strategy change: Find the person's ACTUAL profiles, then scrape them
        # Google snippets contain contextual emails (other people writing about target)
        # We need to find their actual profile pages and scrape those directly
        
        # OPTIMIZED: Only highest-value profile searches to reduce API load
        priority_profile_queries = [
            # TOP PRIORITY: LinkedIn (most likely to have contact info)
            f'site:linkedin.com/in "{full_name}"',
            
            # HIGH PRIORITY: GitHub (developers list emails)
            f'site:github.com "{full_name}"',
        ]
        
        self.logger.info(f"🎯 Profile-focused search: Finding actual profiles to scrape")
        target_profile_urls = []
        discovered_emails = set()
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

        # Phase 1: Find target's actual profile URLs (OPTIMIZED - reduced from 6 to 2 queries)
        for query in priority_profile_queries:
            try:
                data = self.search_client.search(query, query_type='general', num_results=5)
                if data is None:
                    continue

                results['queries_executed'] += 1
                
                # Collect profile URLs for scraping
                if 'items' in data:
                    for item in data['items']:
                        page_url = item.get('link', '')
                        if self._is_profile_page(page_url):
                            target_profile_urls.append(page_url)
                            self.logger.info(f"🎯 Found profile to scrape: {page_url}")
                            
            except Exception as e:
                self.logger.warning(f"Profile search error for query '{query}': {e}")
                continue

        # Phase 2: Scrape target's actual profile pages for emails  
        self.logger.info(f"🎯 Found {len(target_profile_urls)} profile pages to scrape")
        
        if target_profile_urls:
            self.logger.info(f"🔍 PROCESSING: {len(target_profile_urls)} profiles")
            
            # Separate LinkedIn from other profiles  
            linkedin_profiles = [url for url in target_profile_urls if 'linkedin.com' in url.lower()]
            other_profiles = [url for url in target_profile_urls if 'linkedin.com' not in url.lower()]
            
            # LinkedIn-specific approach (username extraction + targeted patterns)
            if linkedin_profiles:
                self.logger.info(f"🎯 LinkedIn profiles found: {len(linkedin_profiles)} - using username extraction approach")
                linkedin_results = self._analyze_linkedin_profiles(linkedin_profiles, full_name)
                
                if linkedin_results.get('found'):
                    # Add LinkedIn username-based email patterns
                    linkedin_emails = linkedin_results.get('emails', [])
                    for email_data in linkedin_emails:
                        results['emails'].append(email_data)  # These are already in dict format
                        self.logger.info(f"🎯 LinkedIn-targeted email: {email_data['email']} (from username: {email_data.get('linkedin_username', 'unknown')})")
                    
                    # Add discovered usernames to identity data for Phase 2!
                    linkedin_usernames = linkedin_results.get('usernames_discovered', [])
                    if 'usernames' not in self.identity_data:
                        self.identity_data['usernames'] = []
                    
                    # Extract just the username strings
                    for username_obj in linkedin_usernames:
                        if isinstance(username_obj, dict):
                            self.identity_data['usernames'].append(username_obj.get('username'))
                        else:
                            self.identity_data['usernames'].append(username_obj)
                    
                    results['found'] = True
                    self.logger.info(f"✅ LinkedIn analysis: {len(linkedin_usernames)} usernames discovered → {len(linkedin_emails)} targeted emails")
                    self.logger.info(f"📝 Usernames added to identity for Phase 2 expansion: {[u.get('username') if isinstance(u, dict) else u for u in linkedin_usernames[:5]]}")
            
            # Other profiles - try Scrapy or enhanced requests
            if other_profiles:
                scrapy_results = self._try_scrapy_scraping(other_profiles, full_name)
                if scrapy_results.get('found'):
                    scrapy_emails = scrapy_results.get('emails', [])
                    for email in scrapy_emails:
                        discovered_emails.add(email)
                        self.logger.info(f"🕷️ Scrapy found email: {email}")
                else:
                    # Fallback scraping for non-LinkedIn sites
                    for i, profile_url in enumerate(other_profiles[:3], 1):
                        self.logger.info(f"🔍 Scraping non-LinkedIn profile {i}: {profile_url}")
                        scraped_emails = self._scrape_page_for_emails(profile_url, full_name)
                        for email in scraped_emails:
                            if self._email_matches_target(email, full_name):
                                discovered_emails.add(email)
        else:
            self.logger.warning("❌ No profile pages found to process")

        # Phase 3: Fallback - search snippets with more targeted queries
        if not discovered_emails:
            self.logger.info("🔄 No emails found in profiles, using targeted snippet search...")
            # OPTIMIZED: Only most effective direct email query
            direct_email_queries = [
                f'"{full_name}" inurl:contact',  # Contact pages (highest success rate)
            ]
            
            for query in direct_email_queries:
                try:
                    data = self.search_client.search(query, query_type='email', num_results=5)
                    if data is None:
                        continue

                    results['queries_executed'] += 1
                    
                    if 'items' in data:
                        for item in data['items']:
                            # More aggressive email extraction from snippets
                            text_to_search = f"{item.get('title', '')} {item.get('snippet', '')}"
                            found_emails = email_pattern.findall(text_to_search)

                            for email in found_emails:
                                email = email.lower().strip()
                                # Be more inclusive for snippet-found emails  
                                if self._is_personal_email(email) and self._email_matches_target(email, full_name):
                                    discovered_emails.add(email)
                                    results['results_parsed'] += 1
                                    self.logger.info(f"✅ Found target email in snippet: {email}")

                except Exception as e:
                    self.logger.warning(f"Direct email search error for query '{query}': {e}")
                    continue

        # Convert discovered emails to result format
        for email in discovered_emails:
            results['emails'].append({
                'email': email,
                'confidence': 0.8,  # High confidence for Google search results
                'source': 'personal_google_search',
                'method': 'google_personal'
            })

        results['found'] = len(results['emails']) > 0
        return results

    def hunt_with_social_media_emails(self) -> Dict:
        """Hunt for emails mentioned in social media profiles and bios"""
        results = {
            'found': False,
            'emails': [],
            'method': 'social_media_extraction',
            'note': 'Extracted from social media profiles and bios'
        }

        first_name = self.identity_data.get('first_name', '').strip()
        last_name = self.identity_data.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()

        if not full_name:
            return results

        # Social media email discovery queries (simplified for Google Custom Search API)
        social_queries = [
            # Bio and contact info searches (broken into separate queries)
            f'"{full_name}" site:twitter.com email',
            f'"{full_name}" site:instagram.com contact',
            f'"{full_name}" site:github.com',
            f'"{full_name}" site:about.me email',
        ]

        discovered_emails = set()
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

        for query in social_queries:
            try:
                data = self.search_client.search(query, query_type='general', num_results=10)
                if data is None:
                    continue

                # Parse results for emails
                if 'items' in data:
                    for item in data['items']:
                        text_to_search = f"{item.get('title', '')} {item.get('snippet', '')}"
                        found_emails = email_pattern.findall(text_to_search)

                        for email in found_emails:
                            email = email.lower().strip()
                            if self._is_personal_email(email) and self._is_potential_match(email):
                                discovered_emails.add(email)

            except Exception as e:
                self.logger.warning(f"Social media email search error: {e}")
                continue

        # Convert to result format
        for email in discovered_emails:
            results['emails'].append({
                'email': email,
                'confidence': 0.7,
                'source': 'social_media_profiles',
                'method': 'social_extraction'
            })

        results['found'] = len(results['emails']) > 0
        return results

    def hunt_with_social_media_bios(self) -> Dict:
        """Enhanced social media bio scraping - the most promising source for personal emails"""
        results = {
            'found': False,
            'emails': [],
            'method': 'social_media_bio_scraping',
            'platforms_scraped': [],
            'note': 'Direct scraping of social media profiles where people often list personal contact info'
        }

        first_name = self.identity_data.get('first_name', '').strip()
        last_name = self.identity_data.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()

        if not full_name:
            return results

        self.logger.info(f"🎯 Social media bio scraping for: {full_name}")
        
        # Target social media platforms where people actually list emails in bios
        platform_searches = [
            # Twitter - many people list contact emails in bio
            {
                'search_query': f'site:twitter.com "{full_name}"',
                'platform': 'twitter',
                'bio_selectors': ['[data-testid="UserDescription"]', '.css-1dbjc4n .r-37j5jr']
            },
            # GitHub - developers often list emails in profile or README
            {
                'search_query': f'site:github.com "{full_name}"',  
                'platform': 'github',
                'bio_selectors': ['.p-note', '.user-profile-bio', '.f4']
            },
            # About.me - specifically designed for contact info
            {
                'search_query': f'site:about.me "{full_name}"',
                'platform': 'about_me', 
                'bio_selectors': ['.bio-text', '.about-text', '.description']
            }
        ]

        discovered_emails = set()
        
        # Use requests for direct scraping (faster than Selenium for simple content)
        for platform_data in platform_searches:
            try:
                # First, find the actual profile pages
                data = self.search_client.search(
                    platform_data['search_query'], 
                    query_type='general', 
                    num_results=3
                )
                
                if data and 'items' in data:
                    results['platforms_scraped'].append(platform_data['platform'])
                    
                    for item in data['items']:
                        profile_url = item.get('link', '')
                        
                        # Scrape this profile page for emails
                        self.logger.debug(f"Scraping {platform_data['platform']} profile: {profile_url}")
                        
                        # Enhanced scraping for social media profiles
                        page_emails = self._scrape_social_profile(profile_url, platform_data)
                        
                        for email in page_emails:
                            if self._email_matches_target(email, full_name):
                                discovered_emails.add(email)
                                self.logger.info(f"🎉 Found personal email on {platform_data['platform']}: {email}")
                
            except Exception as e:
                self.logger.warning(f"Error scraping {platform_data['platform']}: {e}")
                continue

        # Convert to result format
        for email in discovered_emails:
            results['emails'].append({
                'email': email,
                'confidence': 0.9,  # High confidence - found in actual bio/profile
                'source': 'social_media_bio',
                'method': 'bio_scraping'
            })

        results['found'] = len(results['emails']) > 0
        return results

    def _scrape_social_profile(self, url: str, platform_data: Dict) -> List[str]:
        """Scrape social media profile page for emails with platform-specific logic"""
        emails_found = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Platform-specific email extraction
                platform = platform_data['platform']
                email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
                
                if platform == 'github':
                    # GitHub: Look in bio, README, and commit emails
                    bio_elements = soup.find_all(['div', 'span', 'p'], class_=['p-note', 'user-profile-bio'])
                    for element in bio_elements:
                        emails = email_pattern.findall(element.get_text())
                        emails_found.extend([e.lower() for e in emails])
                        
                elif platform == 'twitter':  
                    # Twitter: Look in bio text  
                    bio_elements = soup.select('[data-testid="UserDescription"]')
                    for element in bio_elements:
                        emails = email_pattern.findall(element.get_text())
                        emails_found.extend([e.lower() for e in emails])
                        
                elif platform == 'about_me':
                    # About.me: Look in description and contact sections
                    bio_elements = soup.find_all(['div', 'p'], class_=['bio', 'description', 'about'])
                    for element in bio_elements:
                        emails = email_pattern.findall(element.get_text()) 
                        emails_found.extend([e.lower() for e in emails])
                
                # Also look for mailto links anywhere on the page
                mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
                for link in mailto_links:
                    href = link.get('href', '')
                    email_match = re.search(r'mailto:([^?&\s]+)', href, re.I)
                    if email_match:
                        emails_found.append(email_match.group(1).lower())
                        
        except Exception as e:
            self.logger.debug(f"Error scraping social profile {url}: {e}")
            
        return list(set(emails_found))  # Remove duplicates

    def _try_scrapy_scraping(self, profile_urls: List[str], target_name: str) -> Dict:
        """Try to use Scrapy for robust profile scraping (fallback to requests if not available)"""
        
        try:
            from .scrapy_integration import scrape_profiles_with_scrapy
            self.logger.info(f"🕷️ Attempting Scrapy-based profile scraping for {len(profile_urls)} profiles")
            return scrape_profiles_with_scrapy(profile_urls, target_name)
            
        except ImportError:
            self.logger.info("🔄 Scrapy not available - install with: pip install scrapy scrapy-splash")
            return {'found': False, 'error': 'Scrapy not installed'}
        except Exception as e:
            self.logger.warning(f"Scrapy scraping failed: {e}")
            return {'found': False, 'error': str(e)}

    def _prompt_username_selection(self, discovered_usernames: List[str]) -> List[str]:
        """
        Prompt user to select which REAL discovered usernames to search with Sherlock/Maigret
        Prevents wasting time on pattern guesses
        """
        
        if not discovered_usernames:
            return []
        
        # Non-interactive mode: Auto-select top 3 most likely real usernames
        # (Username with hyphens or numbers are usually real LinkedIn/GitHub usernames)
        auto_select = []
        for username in discovered_usernames[:5]:  # Max 5
            # Real usernames often have hyphens, numbers, or are shorter handles
            if '-' in username or any(c.isdigit() for c in username) or len(username) < 15:
                auto_select.append(username)
        
        if len(auto_select) > 0:
            self.logger.info(f"🤖 AUTO-SELECTED {len(auto_select)} high-confidence usernames for deep search")
            return auto_select[:3]  # Limit to top 3
        
        # Fallback: just use first 2
        return discovered_usernames[:2]
    
    def _confirm_maigret_search(self, username_count: int) -> bool:
        """
        Confirm if user wants to run Maigret (time-intensive)
        
        Args:
            username_count: Number of usernames to search
            
        Returns:
            Bool - whether to run Maigret
        """
        # Auto-decision based on username count
        if username_count <= 2:
            self.logger.info(f"🤖 AUTO-ENABLING Maigret: {username_count} usernames (manageable)")
            return True
        else:
            self.logger.info(f"⏭️ AUTO-SKIPPING Maigret: {username_count} usernames (would take too long)")
            return False
    
    def _search_username_with_sherlock(self, username: str) -> Dict:
        """Search a single VERIFIED username with Sherlock"""
        try:
            from .sherlock_integration import SherlockIntegration
            
            sherlock = SherlockIntegration(target_name=username)
            if not sherlock.check_sherlock_available():
                return {'found': False, 'error': 'Sherlock not installed'}
            
            # Search this specific real username
            result = sherlock.run_sherlock_scan(username, Path('./temp_sherlock'))
            
            return {
                'found': result.get('found', False),
                'platforms_count': len(result.get('all_profiles_found', [])),
                'profiles': result.get('all_profiles_found', [])
            }
            
        except Exception as e:
            self.logger.warning(f"Sherlock search failed for {username}: {e}")
            return {'found': False, 'error': str(e)}
    
    def hunt_with_maigret(self) -> Dict:
        """Use Maigret to discover usernames across 2500+ sites (broader than Sherlock)"""
        
        results = {
            'found': False,
            'total_profiles_found': 0,
            'successful_searches': 0,
            'results_by_username': {}
        }
        
        try:
            from .maigret_integration import enhance_username_discovery_with_maigret
            
            # Get discovered usernames from identity data
            usernames = self.identity_data.get('usernames', [])
            
            if not usernames:
                self.logger.info("ℹ️ No usernames available for Maigret search")
                results['note'] = 'No usernames to search'
                return results
            
            # Limit to first 3 usernames to save time (Maigret is comprehensive but slower)
            usernames_to_search = usernames[:3]
            self.logger.info(f"🔍 Maigret searching {len(usernames_to_search)} username(s) across 2500+ sites...")
            
            maigret_results = enhance_username_discovery_with_maigret(usernames_to_search)
            
            if maigret_results.get('total_profiles_found', 0) > 0:
                results['found'] = True
                results['total_profiles_found'] = maigret_results['total_profiles_found']
                results['successful_searches'] = maigret_results['successful_searches']
                
                # Store detailed results by username
                for username_result in maigret_results.get('results', []):
                    username = username_result.get('username')
                    if username:
                        results['results_by_username'][username] = {
                            'sites_found': username_result.get('sites_found', 0),
                            'total_checked': username_result.get('total_sites_checked', 0),
                            'profiles': username_result.get('profiles', [])
                        }
        
        except ImportError:
            self.logger.info("🔄 Maigret not available - install with: pip install maigret")
            results['error'] = 'Maigret not installed'
        except Exception as e:
            self.logger.warning(f"Maigret search failed: {e}")
            results['error'] = str(e)
        
        return results
    
    # REMOVED: hunt_with_sherlock() - Was generating pattern guesses
    # Now using _search_username_with_sherlock() for REAL usernames only

    def hunt_with_theharvester(self) -> Dict:
        """Use theHarvester for advanced email discovery from search engines"""
        
        results = {
            'found': False,
            'emails': [],
            'method': 'theharvester_email_discovery',
            'note': 'Advanced email harvesting using multiple search engines'
        }
        
        full_name = None
        if self.identity_data.get('first_name') and self.identity_data.get('last_name'):
            full_name = f"{self.identity_data['first_name']} {self.identity_data['last_name']}"
        
        if not full_name:
            return results
            
        try:
            from .theharvester_integration import enhance_email_discovery_with_theharvester
            
            # Use a temporary output directory for theHarvester results
            temp_output = Path('./temp_harvester_output')
            temp_output.mkdir(exist_ok=True)
            
            harvester_data = enhance_email_discovery_with_theharvester(full_name, temp_output)
            
            if harvester_data.get('found'):
                discovered_emails = harvester_data.get('emails', [])
                results['emails'] = discovered_emails
                results['found'] = True
                
                # Cleanup temp directory
                import shutil
                shutil.rmtree(temp_output, ignore_errors=True)
                
        except ImportError:
            self.logger.warning("theHarvester integration not available - install theHarvester for better email discovery")
            results['error'] = 'theHarvester not installed'
        except Exception as e:
            self.logger.warning(f"theHarvester scan failed: {e}")
            results['error'] = str(e)
            
        return results

    def validate_with_holehe(self, email_candidates: List[str]) -> Dict:
        """Validate email candidates using Holehe platform verification"""
        
        results = {
            'validated_emails': [],
            'method': 'holehe_validation',
            'note': 'Validates emails by checking existence on 120+ platforms'
        }
        
        try:
            from .holehe_integration import validate_emails_with_holehe
            
            # Use a temporary output directory
            temp_output = Path('./temp_holehe_output')
            temp_output.mkdir(exist_ok=True)
            
            # Extract just the email strings
            email_strings = []
            for email_entry in email_candidates:
                if isinstance(email_entry, dict):
                    email_strings.append(email_entry.get('email', ''))
                else:
                    email_strings.append(str(email_entry))
            
            holehe_data = validate_emails_with_holehe(email_strings, temp_output)
            
            # Convert back to email entry format with validation data
            for email_validation in holehe_data.get('emails_found_on_platforms', []):
                email = email_validation['email']
                platform_count = email_validation['platform_count']
                platforms = email_validation['platforms']
                
                # Find the original email entry to enhance
                for email_entry in email_candidates:
                    if isinstance(email_entry, dict) and email_entry.get('email') == email:
                        # Enhance with Holehe validation data
                        email_entry['holehe_validation'] = {
                            'platform_matches': platform_count,
                            'platforms': platforms[:3],  # Top 3 platforms
                            'validated': True
                        }
                        # Boost confidence for validated emails
                        email_entry['confidence'] = min(email_entry.get('confidence', 0.4) + 0.4, 1.0)
                        results['validated_emails'].append(email_entry)
            
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_output, ignore_errors=True)
                
        except ImportError:
            self.logger.warning("Holehe integration not available - install Holehe for email validation")
            results['error'] = 'Holehe not installed'
        except Exception as e:
            self.logger.warning(f"Holehe validation failed: {e}")
            results['error'] = str(e)
            
        return results

    def _analyze_linkedin_profiles(self, linkedin_urls: List[str], target_name: str) -> Dict:
        """
        Analyze LinkedIn profile URLs to extract usernames and generate targeted email patterns
        Alternative to direct scraping when profiles are blocked
        """
        
        results = {
            'found': False,
            'emails': [],
            'usernames_discovered': [],
            'method': 'linkedin_url_analysis'
        }
        
        self.logger.info(f"🎯 Analyzing {len(linkedin_urls)} LinkedIn URLs for username intelligence")
        
        for linkedin_url in linkedin_urls:
            try:
                # Extract username from LinkedIn URL
                username_match = re.search(r'/in/([^/?]+)', linkedin_url)
                
                if username_match:
                    linkedin_username = username_match.group(1)
                    
                    # Add to discovered usernames
                    results['usernames_discovered'].append({
                        'username': linkedin_username,
                        'platform': 'linkedin',
                        'url': linkedin_url,
                        'confidence': 0.9
                    })
                    
                    # Generate targeted email patterns based on this real username
                    username_patterns = self._generate_linkedin_email_patterns(linkedin_username, target_name)
                    results['emails'].extend(username_patterns)
                    
                    self.logger.info(f"🎯 Extracted LinkedIn username: {linkedin_username} → {len(username_patterns)} email patterns")
                else:
                    self.logger.debug(f"Could not extract username from: {linkedin_url}")
                    
            except Exception as e:
                self.logger.debug(f"LinkedIn URL analysis error: {e}")
                continue
        
        results['found'] = len(results['emails']) > 0
        return results

    def _generate_linkedin_email_patterns(self, linkedin_username: str, target_name: str) -> List[Dict]:
        """Generate email patterns based on discovered LinkedIn username"""
        
        email_patterns = []
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        
        # Pattern 1: Direct LinkedIn username
        for domain in personal_domains:
            email_patterns.append({
                'email': f"{linkedin_username}@{domain}",
                'confidence': 0.8,  # High confidence - real username
                'source': 'linkedin_username_generation',
                'method': 'direct_linkedin_username',
                'linkedin_username': linkedin_username
            })
        
        # Pattern 2: Clean username (remove trailing numbers/hyphens)
        clean_username = re.sub(r'[-0-9]+$', '', linkedin_username)
        if clean_username != linkedin_username and len(clean_username) > 3:
            for domain in personal_domains:
                email_patterns.append({
                    'email': f"{clean_username}@{domain}",
                    'confidence': 0.7,  # Good confidence - cleaned version
                    'source': 'linkedin_username_generation',
                    'method': 'cleaned_linkedin_username', 
                    'linkedin_username': linkedin_username
                })
        
        # Pattern 3: Convert hyphens to dots (common email format)
        dot_username = linkedin_username.replace('-', '.')
        if dot_username != linkedin_username:
            for domain in personal_domains:
                email_patterns.append({
                    'email': f"{dot_username}@{domain}",
                    'confidence': 0.6,  # Medium confidence - format conversion
                    'source': 'linkedin_username_generation',
                    'method': 'linkedin_username_dots',
                    'linkedin_username': linkedin_username
                })
        
        return email_patterns

    def _is_personal_email(self, email: str) -> bool:
        """Check if email is from a personal provider (not business)"""
        personal_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
            'icloud.com', 'aol.com', 'protonmail.com', 'yandex.com',
            'mail.com', 'gmx.com', 'live.com', 'msn.com'
        ]
        domain = email.split('@')[-1].lower() if '@' in email else ''
        return domain in personal_domains

    def _is_profile_page(self, url: str) -> bool:
        """Check if URL is likely a personal profile page worth scraping"""
        if not url:
            return False
            
        profile_indicators = [
            'github.com',
            'about.me', 
            'gravatar.com',
            'orcid.org',
            'researchgate.net',
            'stackoverflow.com/users',
            'linkedin.com/in',
            # Add more as needed
        ]
        
        return any(indicator in url.lower() for indicator in profile_indicators)

    def _scrape_page_for_emails(self, url: str, target_name: str) -> List[str]:
        """Scrape a profile page for email addresses with enhanced LinkedIn handling"""
        emails_found = []
        
        # Skip LinkedIn scraping for now - requires more sophisticated approach
        if 'linkedin.com' in url.lower():
            self.logger.warning(f"⏭️ Skipping LinkedIn scraping: {url} (requires advanced anti-bot measures)")
            self.logger.info("💡 LinkedIn email extraction needs Scrapy or Selenium with session management")
            return []
        
        try:
            # Enhanced headers for non-LinkedIn sites
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Cache-Control': 'max-age=0',
                'DNT': '1',
            }
            
            self.logger.debug(f"🔍 Attempting to scrape: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Enhanced email extraction patterns for different obfuscation methods
                email_patterns = [
                    # Standard email format
                    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                    # Obfuscated formats common in profiles
                    re.compile(r'\b[A-Za-z0-9._%+-]+\s*\[?at\]?\s*[A-Za-z0-9.-]+\s*\[?dot\]?\s*[A-Za-z]{2,}\b'),
                    re.compile(r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Za-z]{2,}\b'),
                ]
                
                # GitHub-specific: Check for email in commit history links
                if 'github.com' in url.lower():
                    # Look for email in meta tags, JSON data, etc.
                    github_email_patterns = [
                        r'"email":"([^"]+@[^"]+)"',  # JSON format
                        r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})',  # mailto links
                        r'<meta[^>]*email[^>]*content="([^"]*@[^"]*)"[^>]*>',  # Meta tags
                    ]
                    
                    for pattern_str in github_email_patterns:
                        pattern = re.compile(pattern_str, re.IGNORECASE)
                        matches = pattern.findall(content)
                        for match in matches:
                            if '@' in match and '.' in match:
                                emails_found.append(match.lower().strip())
                
                # Standard email extraction
                for pattern in email_patterns:
                    page_emails = pattern.findall(content)
                    for email in page_emails:
                        # Clean up obfuscated formats
                        clean_email = email.lower().strip()
                        clean_email = re.sub(r'\s*\[?at\]?\s*', '@', clean_email)
                        clean_email = re.sub(r'\s*\[?dot\]?\s*', '.', clean_email)
                        
                        if '@' in clean_email and '.' in clean_email.split('@')[1]:
                            emails_found.append(clean_email)
                
                # Filter and dedupe
                valid_emails = []
                for email in set(emails_found):
                    if self._is_personal_email(email) and self._email_matches_target(email, target_name):
                        valid_emails.append(email)
                        
                if valid_emails:
                    self.logger.info(f"✅ Scraped {len(valid_emails)} emails from {url}: {valid_emails}")
                else:
                    self.logger.debug(f"No target emails found on {url}")
                    
                return valid_emails
            else:
                self.logger.debug(f"Failed to scrape {url}: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.debug(f"Error scraping {url}: {e}")
            
        return emails_found

    def _email_matches_target(self, email: str, target_name: str) -> bool:
        """Check if email likely belongs to the target person (more specific than _is_potential_match)"""
        email_lower = email.lower()
        target_parts = target_name.lower().split() if target_name else []
        
        # Check if email contains target's name parts
        for part in target_parts:
            if len(part) > 2 and part in email_lower:
                return True
                
        return False

    def hunt_with_username_correlation(self) -> Dict:
        """Hunt for emails using discovered usernames from social media"""
        results = {
            'found': False,
            'emails': [],
            'method': 'username_correlation',
            'note': 'Email discovery based on discovered social media usernames'
        }

        usernames = self.identity_data.get('usernames', [])
        if not usernames:
            return results

        self.logger.info(f"🎯 Username-based email hunting with {len(usernames)} discovered usernames")
        
        # Common email patterns using discovered usernames
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        
        for username_data in usernames[:5]:  # Limit to top 5 usernames
            if isinstance(username_data, dict):
                username = username_data.get('username', '')
                platform = username_data.get('platform', 'unknown')
            else:
                username = str(username_data)
                platform = 'unknown'
            
            if username:
                # Generate email patterns based on username
                for domain in personal_domains:
                    email = f"{username}@{domain}"
                    results['emails'].append({
                        'email': email,
                        'confidence': 0.5,  # Medium confidence - username-based guess
                        'source': 'username_correlation',
                        'method': f'username_from_{platform}',
                        'discovered_username': username
                    })

        results['found'] = len(results['emails']) > 0
        return results

    def hunt_with_company_correlation(self) -> Dict:
        """Hunt for emails using discovered company/employer information"""
        results = {
            'found': False,
            'emails': [],
            'method': 'company_correlation',
            'note': 'Email discovery based on discovered company/employer information'
        }

        companies = self.identity_data.get('companies', [])
        first_name = self.identity_data.get('first_name', '').lower().strip()
        last_name = self.identity_data.get('last_name', '').lower().strip()

        if not companies or not (first_name and last_name):
            return results

        self.logger.info(f"🎯 Company-based email hunting with {len(companies)} discovered employers")
        
        # Generate work email patterns
        name_patterns = [
            f"{first_name}.{last_name}",
            f"{first_name}{last_name}",
            f"{first_name[0]}.{last_name}",
            f"{first_name}.{last_name[0]}"
        ]
        
        for company in companies[:3]:  # Limit to top 3 companies
            # Try to convert company name to domain
            company_clean = str(company).lower().replace(' ', '').replace(',', '').replace('.', '')
            potential_domains = [
                f"{company_clean}.com",
                f"{company_clean}.org",
                f"{company_clean}.net"
            ]
            
            for domain in potential_domains:
                for pattern in name_patterns:
                    email = f"{pattern}@{domain}"
                    results['emails'].append({
                        'email': email,
                        'confidence': 0.4,  # Lower confidence - company domain guess
                        'source': 'company_correlation',
                        'method': 'employer_domain_guess',
                        'company': company,
                        'domain_guess': domain
                    })

        results['found'] = len(results['emails']) > 0
        return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python email_hunter.py <phone_number>")
        sys.exit(1)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    phone = sys.argv[1]
    hunter = EmailHunter(phone)
    results = hunter.hunt_comprehensive()

    print(f"\n🎯 Email Hunting Results for {phone}:")
    print(f"Found: {results['found']}")
    print(f"Total Emails: {len(results['emails']) + len(results['verified_emails'])}")
    print(f"Confidence: {results['confidence_score']:.2f}")
    print(f"Methods: {', '.join(results['methods_used'])}")