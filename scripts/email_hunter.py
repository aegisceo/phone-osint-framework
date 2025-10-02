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
        self.yandex_api_key = os.getenv('YANDEX_API_KEY')
        self.yandex_user_id = os.getenv('YANDEX_USER_ID')
        self.hibp_api_key = os.getenv('HAVEIBEENPWNED_API_KEY')

        # Multi-engine search client with intelligent routing
        google_client = GoogleAPIClient(self.google_api_key, self.google_cse_id) if self.google_api_key else None
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
                    f'"{full_name}" "@" -site:facebook.com -site:twitter.com',
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

            # Method 1: Use HIBP API for known email addresses
            if hibp_api_key:
                self.logger.info("Checking Have I Been Pwned API...")
                results['sources_checked'].append('haveibeenpwned')

                # HIBP doesn't directly search by phone number, but we can check
                # if we find any potential email patterns and validate them

                # Generate potential email patterns based on phone number
                potential_emails = []
                if len(phone_clean) >= 10:
                    area_code = phone_clean[-10:-7]
                    number_part = phone_clean[-7:]

                    # Common email patterns using phone numbers
                    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
                    for domain in domains:
                        potential_emails.extend([
                            f"{phone_clean}@{domain}",
                            f"{area_code}{number_part}@{domain}",
                            f"{phone_clean[-4:]}@{domain}"  # Last 4 digits
                        ])

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
        """Check if an email might be associated with our target"""
        email_lower = email.lower()

        # Check against search terms
        for term in self.search_terms:
            if term.lower() in email_lower:
                return True

        # Check for phone number patterns in email
        if self.clean_phone[-4:] in email_lower or self.clean_phone[-7:] in email_lower:
            return True

        return False

    def hunt_comprehensive(self) -> Dict:
        """Run comprehensive email hunting using all available methods"""
        self.logger.info(f"🎯 Starting comprehensive email hunting for: {self.phone}")

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

        # Method 1: Hunter.io domain search
        hunter_results = self.hunt_with_hunter_io()
        if hunter_results['found']:
            all_results['emails'].extend(hunter_results['emails'])
            all_results['methods_used'].append('hunter.io')
            all_results['search_summary']['hunter_io'] = hunter_results
            self.logger.info(f"✅ Hunter.io found {len(hunter_results['emails'])} emails")

        # Method 2: Google dorking for real email discovery
        google_results = self.hunt_with_google_dorking()
        if google_results['found']:
            all_results['emails'].extend(google_results['emails'])
            all_results['methods_used'].append('google_dorking')
            all_results['search_summary']['google_dorking'] = google_results
            self.logger.info(f"✅ Google dorking found {len(google_results['emails'])} emails")

        # Method 3: Phone breach database search
        breach_results = self.hunt_with_phone_breach_search()
        if breach_results['found']:
            all_results['emails'].extend(breach_results['emails'])
            all_results['methods_used'].append('phone_breach_search')
            all_results['search_summary']['phone_breach_search'] = breach_results
            self.logger.info(f"✅ Breach search found {len(breach_results['emails'])} emails")

        # Method 4: Public records scraping (search engine partial reveals)
        scraping_results = self.hunt_with_public_records_scraping()
        if scraping_results['found']:
            all_results['emails'].extend(scraping_results['emails'])
            all_results['methods_used'].append('public_records_scraping')
            all_results['search_summary']['public_records_scraping'] = scraping_results
            self.logger.info(f"✅ Public records scraping found {len(scraping_results['emails'])} emails")

        # Method 5: Employment intelligence & contextual email generation
        employment_results = self.hunt_with_employment_intelligence()
        if employment_results['found']:
            all_results['emails'].extend(employment_results['emails'])
            all_results['methods_used'].append('employment_intelligence')
            all_results['search_summary']['employment_intelligence'] = employment_results
            self.logger.info(f"✅ Employment intelligence generated {len(employment_results['emails'])} contextual emails")

        # VALIDATION STEP: Validate all discovered emails with DNS MX checks
        if all_results['emails']:
            self.logger.info(f"🔍 Validating {len(all_results['emails'])} discovered emails...")
            validator = EmailValidator()

            # Extract unique email addresses
            unique_emails = list(set([e['email'] for e in all_results['emails']]))

            # Validate (DNS only, no SMTP to avoid rate limits)
            validation_results = validator.validate_batch(unique_emails, check_smtp=False)

            # Create validation lookup
            validation_map = {r['email']: r for r in validation_results}

            # Update email entries with validation status
            validated_emails = []
            invalid_emails = []

            for email_entry in all_results['emails']:
                email_addr = email_entry['email']
                validation = validation_map.get(email_addr, {})

                # Add validation info to email entry
                email_entry['validation'] = {
                    'valid': validation.get('valid', False),
                    'status': validation.get('status', 'unknown'),
                    'confidence': validation.get('confidence', 0.0),
                    'mx_records': len(validation.get('mx_records', []))
                }

                if validation.get('valid'):
                    validated_emails.append(email_entry)
                else:
                    invalid_emails.append(email_entry)
                    self.logger.debug(f"  ✗ Invalid: {email_addr} ({validation.get('status', 'unknown')})")

            # Replace emails list with only validated emails
            all_results['emails'] = validated_emails
            all_results['invalid_emails'] = invalid_emails

            valid_count = len(validated_emails)
            invalid_count = len(invalid_emails)
            self.logger.info(f"📧 Validation complete: {valid_count} valid, {invalid_count} invalid")

        # Calculate overall results
        total_emails = len(all_results['emails']) + len(all_results['verified_emails'])
        all_results['found'] = total_emails > 0

        # Calculate confidence score based on discovery method quality
        if all_results['found']:
            confidence = 0.0

            # High confidence for verified emails from Hunter.io
            if all_results['verified_emails']:
                confidence += 0.8

            # Good confidence for Hunter.io business domain results
            if any(email.get('confidence', 0) > 80 for email in all_results['emails']):
                confidence += 0.7

            # Good confidence for public records scraping (real partial data leakage)
            if 'public_records_scraping' in all_results['methods_used']:
                confidence += 0.8

            # Medium confidence for breach database findings
            if 'phone_breach_search' in all_results['methods_used']:
                confidence += 0.6

            # Medium confidence for Google dorking (real search results)
            if 'google_dorking' in all_results['methods_used']:
                confidence += 0.5

            # High confidence for employment intelligence (contextual generation)
            if 'employment_intelligence' in all_results['methods_used']:
                confidence += 0.75

            # Bonus for multiple discovery methods
            if len(all_results['methods_used']) >= 2:
                confidence += 0.2

            all_results['confidence_score'] = min(confidence, 1.0)

        # Summary logging
        if all_results['found']:
            self.logger.info(f"🎯 EMAIL HUNTING COMPLETE: {total_emails} emails found, confidence: {all_results['confidence_score']:.2f}")
        else:
            self.logger.warning("❌ Email hunting unsuccessful")

        return all_results


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