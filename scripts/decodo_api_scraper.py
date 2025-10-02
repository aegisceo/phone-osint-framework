#!/usr/bin/env python3
"""
Decodo Scraping API Integration for Multi-Source OSINT
Uses Decodo's managed scraping API - they handle proxies, CAPTCHA, anti-bot
Targets multiple high-value sources instead of just Yandex
"""
import os
import json
import logging
import requests
import time
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlencode

class DecodaAPIScraper:
    """
    Multi-source OSINT scraper using Decodo Scraping API
    Targets high-value sources with phone data instead of just Yandex
    Managed service - no proxy/CAPTCHA handling needed
    """

    def __init__(self, phone_number, enriched_identity=None, config_file='config/decodo_api_config.json'):
        self.phone = phone_number
        self.clean_phone = ''.join(filter(str.isdigit, phone_number))
        self.enriched_identity = enriched_identity or {}
        self.logger = logging.getLogger(__name__)

        self.config = self._load_config(config_file)
        self.api_endpoint = 'https://scraper-api.decodo.com/v2/scrape'

        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

    def _load_config(self, config_file: str) -> Dict:
        """Load Decodo API configuration"""
        default_config = {
            'username': '',  # Decodo API username
            'password': '',  # Decodo API password
            'timeout': 60,   # Request timeout in seconds
            'parse': False,  # Return raw HTML (True = structured data, limited support)
        }

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                self.logger.error(f"Error loading API config: {e}")

        return default_config

    def _build_target_urls(self) -> List[Dict]:
        """
        Build URLs for high-value OSINT sources
        Returns list of {url, source_name, priority} dicts
        """
        targets = []

        # Format phone for different sites
        # +13053932786 -> various formats
        if len(self.clean_phone) == 11 and self.clean_phone.startswith('1'):
            # US number
            area_code = self.clean_phone[1:4]
            prefix = self.clean_phone[4:7]
            line = self.clean_phone[7:11]

            # Priority 1: FastPeopleSearch (high success, minimal blocking)
            targets.append({
                'url': f'https://www.fastpeoplesearch.com/phone/{area_code}-{prefix}-{line}',
                'source': 'fastpeoplesearch',
                'priority': 1
            })

            # Priority 2: TrueCaller web results
            targets.append({
                'url': f'https://www.truecaller.com/search/us/{self.phone}',
                'source': 'truecaller',
                'priority': 2
            })

            # Priority 3: 411.com
            targets.append({
                'url': f'https://www.411.com/phone/{area_code}-{prefix}-{line}',
                'source': '411',
                'priority': 3
            })

        # International format - use more generic services
        else:
            area_code = self.clean_phone[:3] if len(self.clean_phone) >= 10 else ''
            prefix = self.clean_phone[3:6] if len(self.clean_phone) >= 10 else ''
            line = self.clean_phone[6:10] if len(self.clean_phone) >= 10 else ''

        # Priority 4: Google search for phone (works internationally)
        targets.append({
            'url': f'https://www.google.com/search?q="{self.phone}"',
            'source': 'google',
            'priority': 4
        })

        # Add name-based search if we have it
        if self.enriched_identity.get('primary_names'):
            primary_name = self.enriched_identity['primary_names'][0]
            targets.append({
                'url': f'https://www.google.com/search?q="{primary_name}"+"{self.phone}"',
                'source': 'google_name',
                'priority': 2  # Higher priority with name
            })

        # Sort by priority and limit to 3 targets max (API cost control)
        targets.sort(key=lambda x: x['priority'])
        return targets[:3]

    def _scrape_url(self, target_url: str, source_name: str, max_retries: int = 2) -> Optional[str]:
        """
        Scrape target URL using Decodo API

        Args:
            target_url: URL to scrape
            source_name: Name of source for logging
            max_retries: Number of retry attempts

        Returns:
            HTML response or None if failed
        """
        # Decodo API parameters
        task_params = {
            'url': target_url,
            'parse': self.config.get('parse', False),
        }

        for attempt in range(max_retries):
            try:
                self.request_count += 1

                self.logger.info(f"Decodo API request {self.request_count}: {source_name} (attempt {attempt + 1})")

                response = requests.post(
                    self.api_endpoint,
                    json=task_params,
                    auth=(self.config['username'], self.config['password']),
                    timeout=self.config.get('timeout', 60)
                )

                if response.status_code == 200:
                    self.success_count += 1
                    # Parse JSON response
                    try:
                        data = response.json()
                        if 'results' in data and len(data['results']) > 0:
                            html = data['results'][0].get('content', '')
                            self.logger.info(f"API success! {source_name}: {len(html)} chars")
                            return html
                        else:
                            self.logger.warning(f"No content in API response for {source_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to parse API response: {e}")
                        return None

                elif response.status_code == 401:
                    self.logger.error("Authentication failed - check Decodo API credentials")
                    return None

                elif response.status_code == 402:
                    self.logger.error("Payment required - Decodo account out of credits")
                    return None

                elif response.status_code == 429:
                    self.logger.warning(f"Rate limited, waiting before retry...")
                    time.sleep(30)

                else:
                    self.logger.warning(f"Unexpected status code: {response.status_code}")
                    self.logger.debug(f"Response: {response.text[:500]}")

            except requests.exceptions.Timeout:
                self.logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")

            except Exception as e:
                self.logger.error(f"API error: {type(e).__name__}: {e}")

            # Wait before retry
            if attempt < max_retries - 1:
                delay = 10 * (attempt + 1)
                self.logger.info(f"Waiting {delay}s before retry...")
                time.sleep(delay)

        self.error_count += 1
        return None

    def _parse_html(self, html: str, source_name: str) -> Dict:
        """
        Extract OSINT data from HTML based on source
        Returns dict with extracted info
        """
        import re

        data = {
            'source': source_name,
            'names': [],
            'addresses': [],
            'relatives': [],
            'emails': [],
            'raw_text': ''
        }

        try:
            soup = BeautifulSoup(html, 'lxml')

            # Extract all text for email/phone pattern matching
            text = soup.get_text()
            data['raw_text'] = text[:5000]  # Limit size

            # Email pattern
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            data['emails'] = list(set(emails))[:10]  # Dedupe and limit

            # Source-specific parsing
            if 'fastpeoplesearch' in source_name:
                # FastPeopleSearch shows name, age, addresses
                name_elem = soup.find(['h1', 'h2'], class_=lambda x: x and 'name' in x.lower() if x else False)
                if name_elem:
                    data['names'].append(name_elem.get_text(strip=True))

                # Addresses
                address_elems = soup.find_all(class_=lambda x: x and 'address' in x.lower() if x else False)
                for elem in address_elems[:5]:
                    addr = elem.get_text(strip=True)
                    if addr and len(addr) > 10:
                        data['addresses'].append(addr)

            elif 'truecaller' in source_name:
                # TrueCaller shows caller name, carrier
                name_pattern = r'"name"\s*:\s*"([^"]+)"'
                names = re.findall(name_pattern, text)
                data['names'].extend(names[:3])

            elif 'google' in source_name:
                # Google search results - extract from search result titles/snippets
                search_results = soup.find_all(['h3', 'div'], class_=lambda x: x and any(term in x.lower() for term in ['result', 'title', 'snippet']) if x else False)
                for result in search_results[:10]:
                    result_text = result.get_text(strip=True)
                    # Look for name patterns (capitalized words)
                    name_matches = re.findall(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', result_text)
                    data['names'].extend(name_matches[:5])

            # Dedupe and limit
            data['names'] = list(set(data['names']))[:10]
            data['addresses'] = list(set(data['addresses']))[:5]

            self.logger.info(f"Extracted from {source_name}: {len(data['names'])} names, {len(data['emails'])} emails")

        except Exception as e:
            self.logger.error(f"Error parsing {source_name} HTML: {e}")

        return data

    def search(self) -> Dict:
        """
        Execute multi-source OSINT scraping via Decodo API

        Returns:
            Aggregated results from all sources
        """
        all_results = {
            'names': [],
            'addresses': [],
            'emails': [],
            'relatives': [],
            'sources_checked': [],
            'metadata': {
                'api_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'source': 'decodo_multi_source'
            }
        }

        targets = self._build_target_urls()
        self.logger.info(f"Scraping {len(targets)} high-value sources via Decodo API")

        for i, target in enumerate(targets):
            self.logger.info(f"Target {i+1}/{len(targets)}: {target['source']}")
            self.logger.info(f"  URL: {target['url'][:100]}...")

            # Scrape via API
            html = self._scrape_url(target['url'], target['source'])

            if html:
                # Parse and extract data
                extracted = self._parse_html(html, target['source'])

                # Aggregate results
                all_results['names'].extend(extracted['names'])
                all_results['addresses'].extend(extracted['addresses'])
                all_results['emails'].extend(extracted['emails'])
                all_results['relatives'].extend(extracted['relatives'])
                all_results['sources_checked'].append({
                    'source': target['source'],
                    'url': target['url'],
                    'success': True,
                    'data_found': len(extracted['names']) > 0 or len(extracted['emails']) > 0
                })
            else:
                all_results['sources_checked'].append({
                    'source': target['source'],
                    'url': target['url'],
                    'success': False,
                    'data_found': False
                })

            # Brief delay between targets (API handles most rate limiting)
            if i < len(targets) - 1:
                time.sleep(2)

        # Dedupe and limit results
        all_results['names'] = list(set(all_results['names']))[:20]
        all_results['addresses'] = list(set(all_results['addresses']))[:10]
        all_results['emails'] = list(set(all_results['emails']))[:15]

        # Add metadata
        all_results['metadata'] = {
            'api_requests': self.request_count,
            'successful_requests': self.success_count,
            'failed_requests': self.error_count,
            'sources_checked': len(targets),
            'successful_sources': len([s for s in all_results['sources_checked'] if s['success']]),
            'source': 'decodo_multi_source',
            'cost_estimate': f"~{self.success_count} API requests (${self.success_count * 0.001:.3f})"
        }

        # Summary
        self.logger.info(f"\nDecodo API scraping complete:")
        self.logger.info(f"  - API requests: {self.request_count}")
        self.logger.info(f"  - Successful: {self.success_count}")
        self.logger.info(f"  - Failed: {self.error_count}")
        self.logger.info(f"  - Names found: {len(all_results['names'])}")
        self.logger.info(f"  - Emails found: {len(all_results['emails'])}")
        self.logger.info(f"  - Addresses found: {len(all_results['addresses'])}")

        return all_results


def setup_decodo_api(username: str, password: str) -> DecodaAPIScraper:
    """
    Quick setup for Decodo API integration

    Args:
        username: Your Decodo API username
        password: Your Decodo API password

    Returns:
        Configured DecodaAPIScraper instance
    """
    config = {
        'username': username,
        'password': password,
        'timeout': 60,
        'parse': False,
    }

    # Save config
    os.makedirs('config', exist_ok=True)
    with open('config/decodo_api_config.json', 'w') as f:
        json.dump(config, f, indent=2)

    return DecodaAPIScraper('+10000000000')  # Dummy number for testing


if __name__ == '__main__':
    # Setup wizard
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Decodo Scraping API Setup")
    print("=" * 60)
    print()
    print("Get your API credentials from: https://decodo.com/dashboard")
    print("Trial: 7 days, 1,000 requests (requires credit card)")
    print()

    username = input("Decodo API Username: ").strip()
    password = input("Decodo API Password: ").strip()

    print("\nSetting up Decodo API integration...")
    scraper = setup_decodo_api(username, password)

    print("\n✓ Decodo API configured successfully!")
    print("\nTest with:")
    print("  ./venv/bin/python phone_osint_master.py +13053932786")
    print("\nThe framework will automatically use Decodo API for Yandex scraping.")
