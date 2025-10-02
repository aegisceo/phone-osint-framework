#!/usr/bin/env python3
"""
Employment Intelligence & Email Domain Discovery
Discovers employment information and company domains for contextual email generation
"""

import os
import re
import requests
import logging
import time
from typing import Dict, List, Set, Optional
from urllib.parse import quote
from dotenv import load_dotenv
from .api_utils import GoogleAPIClient, BingAPIClient, YandexAPIClient, UnifiedSearchClient

load_dotenv('config/.env')

class EmploymentHunter:
    """
    Advanced employment intelligence engine using targeted Google dorking
    Discovers employment information and company email domains
    """

    def __init__(self, phone_number: str, identity_data: Dict = None):
        self.phone = phone_number
        self.identity_data = identity_data or {}
        self.logger = logging.getLogger(__name__)

        # API credentials
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_cse_id = os.getenv('GOOGLE_CSE_ID')
        # Support both SERPAPI_KEY and BING_API_KEY (backward compat)
        self.serpapi_key = os.getenv('SERPAPI_KEY') or os.getenv('BING_API_KEY')
        self.yandex_api_key = os.getenv('YANDEX_API_KEY')
        self.yandex_user_id = os.getenv('YANDEX_USER_ID')

        # Multi-engine search client with intelligent routing
        google_client = GoogleAPIClient(self.google_api_key, self.google_cse_id) if self.google_api_key else None
        bing_client = BingAPIClient(self.serpapi_key) if self.serpapi_key else None  # BingAPIClient is alias for SerpApiClient
        yandex_client = YandexAPIClient(self.yandex_api_key, self.yandex_user_id) if self.yandex_api_key else None
        self.search_client = UnifiedSearchClient(google_client, bing_client, yandex_client, enable_ddg_fallback=True)

        # Clean phone number for processing
        self.clean_phone = re.sub(r'[^\d]', '', phone_number)

    def search_employment_with_google(self) -> Dict:
        """Use targeted Google dorking to find employment information - PRIORITIZE NAME+EMAIL!"""
        results = {
            'found': False,
            'employers': [],
            'company_domains': [],
            'job_titles': [],
            'method': 'google_employment_dorking',
            'queries_executed': 0
        }

        if not self.google_api_key or not self.google_cse_id:
            self.logger.warning("Google Custom Search API not configured for employment hunting")
            return results

        try:
            search_queries = []
            full_name = None
            known_email = None
            email_domain = None

            # Extract identity data
            if self.identity_data.get('first_name') and self.identity_data.get('last_name'):
                full_name = f"{self.identity_data['first_name']} {self.identity_data['last_name']}"
            if self.identity_data.get('known_email'):
                known_email = self.identity_data['known_email']
                # Extract domain from email (e.g., rlindley.619@gmail.com -> gmail.com)
                if '@' in known_email:
                    email_domain = known_email.split('@')[1]

            # REALITY-BASED EMPLOYMENT SEARCHES - NO PHONE NUMBERS!
            # LinkedIn doesn't show phone numbers, focus on what actually appears there

            if not full_name:
                self.logger.error(f"❌ Cannot perform employment hunting without a name!")
                self.logger.error(f"   LinkedIn profiles require NAME-based searches, phone searches yield nothing")
                return results

            self.logger.info(f"🎯 Employment hunting with NAME: {full_name}")

            # Query 1: Direct LinkedIn profile search (most likely to find actual profile)
            search_queries.append(f'site:linkedin.com/in/ "{full_name}"')

            # Query 2: LinkedIn with common job title indicators (catches profile snippets)
            search_queries.append(f'site:linkedin.com "{full_name}" "Engineer" OR "Developer" OR "Manager" OR "Director" OR "Analyst"')

            # Query 3: Resume/CV PDFs (often publicly indexed)
            search_queries.append(f'"{full_name}" filetype:pdf "resume" OR "cv" OR "curriculum vitae"')

            # Query 4: Professional bios and about pages
            search_queries.append(f'"{full_name}" "about" OR "bio" OR "profile" -site:facebook.com -site:twitter.com')

            # Query 5: Email domain company connection (if work email)
            if email_domain and email_domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'icloud.com']:
                # Might be a corporate email
                search_queries.append(f'"{full_name}" site:{email_domain}')
                self.logger.info(f"🎯 Detected potential work email domain: {email_domain}")

            # Limit to 5 queries total
            search_queries = search_queries[:5]
            self.logger.info(f"Employment hunting: {len(search_queries)} NAME-BASED queries (NO phone searches - they don't work!)")

            # Patterns to extract employment information
            company_patterns = [
                r'works?\s+(?:at|for)\s+([A-Za-z][A-Za-z0-9\s&.,]+?)(?:\s|$|\.|,)',
                r'employed\s+(?:at|by)\s+([A-Za-z][A-Za-z0-9\s&.,]+?)(?:\s|$|\.|,)',
                r'([A-Za-z][A-Za-z0-9\s&.,]+?)\s+(?:employee|staff|team member)',
                r'@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'  # Email domains
            ]

            job_title_patterns = [
                r'(?:Senior|Junior|Lead|Principal|Chief)?\s*(?:Software|Data|Systems|Network|Security|Marketing|Sales|Operations|HR|Finance)?\s*(?:Engineer|Developer|Analyst|Manager|Director|Officer|Specialist|Consultant|Coordinator)',
                r'(?:VP|Vice President|CEO|CTO|CFO|COO|President|Director|Manager)\s+(?:of|at)?'
            ]

            discovered_companies = set()
            discovered_domains = set()
            discovered_titles = set()

            for query in search_queries:
                try:
                    # Employment searches: use 'employment' type for Yandex priority (better LinkedIn/company indexing)
                    data = self.search_client.search(query, query_type='employment', num_results=10)
                    if data is None:
                        self.logger.warning(f"Employment search failed for query: {query}")
                        continue

                    results['queries_executed'] += 1

                    if 'items' in data:
                        for item in data['items']:
                            # Extract from title and snippet
                            text_content = f"{item.get('title', '')} {item.get('snippet', '')}"

                            # Look for company information
                            for pattern in company_patterns:
                                matches = re.findall(pattern, text_content, re.IGNORECASE)
                                for match in matches:
                                    if '@' in match:  # It's a domain
                                        domain = match.lower()
                                        if not any(generic in domain for generic in ['gmail', 'yahoo', 'hotmail', 'outlook']):
                                            discovered_domains.add(domain)
                                    else:  # It's a company name
                                        company = match.strip(' .,')
                                        if len(company) > 2 and len(company) < 50:  # Reasonable company name
                                            discovered_companies.add(company)

                            # Look for job titles
                            for pattern in job_title_patterns:
                                matches = re.findall(pattern, text_content, re.IGNORECASE)
                                for match in matches:
                                    title = match.strip(' .,')
                                    if len(title) > 3:
                                        discovered_titles.add(title)

                except Exception as e:
                    self.logger.warning(f"Employment search error for query '{query}': {e}")
                    continue

            # Convert to result format
            results['employers'] = list(discovered_companies)
            results['company_domains'] = list(discovered_domains)
            results['job_titles'] = list(discovered_titles)
            results['found'] = len(discovered_companies) > 0 or len(discovered_domains) > 0

            if results['found']:
                self.logger.info(f"Employment hunting found: {len(results['employers'])} companies, {len(results['company_domains'])} domains")
            else:
                self.logger.info("No employment information discovered")

        except Exception as e:
            self.logger.error(f"Employment hunting error: {e}")

        return results

    def generate_contextual_email_patterns(self, employment_data: Dict) -> List[Dict]:
        """Extract discovered email addresses only - NO pattern generation/guessing"""
        email_candidates = []

        # DISABLED: Pattern generation creates noise and false positives
        # Only return emails that were actually discovered in search results

        self.logger.info("Email pattern generation disabled - using discovered emails only")
        return email_candidates

    def hunt_comprehensive(self) -> Dict:
        """Run comprehensive employment-based email hunting"""
        self.logger.info(f"🎯 Starting employment intelligence hunting for: {self.phone}")

        all_results = {
            'found': False,
            'employment_data': {},
            'contextual_emails': [],
            'methods_used': [],
            'confidence_score': 0.0,
            'summary': {}
        }

        # Step 1: Discover employment information
        employment_data = self.search_employment_with_google()
        all_results['employment_data'] = employment_data

        if employment_data['found']:
            all_results['methods_used'].append('google_employment_dorking')
            all_results['found'] = True

        # Step 2: Generate contextual email patterns
        if employment_data['found']:
            contextual_emails = self.generate_contextual_email_patterns(employment_data)
            all_results['contextual_emails'] = contextual_emails

            if contextual_emails:
                all_results['methods_used'].append('contextual_email_generation')

        # Calculate confidence
        if all_results['found']:
            confidence = 0.0

            # High confidence for discovered employment data
            if employment_data['found']:
                confidence += 0.8

            # Bonus for multiple data points
            data_points = len(employment_data.get('employers', [])) + len(employment_data.get('company_domains', []))
            if data_points >= 2:
                confidence += 0.2

            all_results['confidence_score'] = min(confidence, 1.0)

        # Summary
        employers_count = len(employment_data.get('employers', []))
        domains_count = len(employment_data.get('company_domains', []))
        emails_count = len(all_results['contextual_emails'])

        all_results['summary'] = {
            'employers_discovered': employers_count,
            'company_domains_discovered': domains_count,
            'contextual_emails_generated': emails_count,
            'queries_executed': employment_data.get('queries_executed', 0)
        }

        if all_results['found']:
            self.logger.info(f"🎯 EMPLOYMENT HUNTING COMPLETE: {employers_count} employers, {domains_count} domains, {emails_count} contextual emails")
        else:
            self.logger.warning("❌ Employment hunting unsuccessful")

        return all_results


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python employment_hunter.py <phone_number>")
        sys.exit(1)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    phone = sys.argv[1]

    # Test with sample identity data
    identity_data = {
        'first_name': 'Richard',
        'last_name': 'Lindley'
    }

    hunter = EmploymentHunter(phone, identity_data)
    results = hunter.hunt_comprehensive()

    print(f"\n🎯 Employment Intelligence Results for {phone}:")
    print(f"Found: {results['found']}")
    print(f"Employers: {results['summary']['employers_discovered']}")
    print(f"Company Domains: {results['summary']['company_domains_discovered']}")
    print(f"Contextual Emails: {results['summary']['contextual_emails_generated']}")
    print(f"Confidence: {results['confidence_score']:.2f}")
    print(f"Methods: {', '.join(results['methods_used'])}")