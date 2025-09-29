#!/usr/bin/env python3
"""
FastPeopleSearch Integration for Aggressive Name Hunting
Advanced scraping module for extracting owner names from public records
"""

import requests
import logging
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FastPeopleHunter:
    """
    Advanced FastPeopleSearch integration for phone number owner identification
    THE GRAIL: Maximum name extraction through multiple techniques
    """

    def __init__(self, phone_number: str):
        self.phone = phone_number
        self.clean_phone = self._clean_phone_number(phone_number)
        self.logger = logging.getLogger(__name__)

        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]

        # Search patterns for different phone formats
        self.search_formats = self._generate_search_formats()

    def _clean_phone_number(self, phone: str) -> str:
        """Clean phone number for searching"""
        return re.sub(r'[^\d]', '', phone)

    def _generate_search_formats(self) -> List[str]:
        """Generate different phone number formats for searching"""
        clean = self.clean_phone
        formats = []

        if len(clean) == 11 and clean.startswith('1'):
            # US number with country code
            area = clean[1:4]
            prefix = clean[4:7]
            suffix = clean[7:11]

            formats.extend([
                f"{area}{prefix}{suffix}",           # 5551234567
                f"{area}-{prefix}-{suffix}",         # 555-123-4567
                f"({area}) {prefix}-{suffix}",       # (555) 123-4567
                f"{area}.{prefix}.{suffix}",         # 555.123.4567
                f"+1{area}{prefix}{suffix}",         # +15551234567
                f"1-{area}-{prefix}-{suffix}",       # 1-555-123-4567
                f"1 {area} {prefix} {suffix}",       # 1 555 123 4567
            ])
        elif len(clean) == 10:
            # US number without country code
            area = clean[0:3]
            prefix = clean[3:6]
            suffix = clean[6:10]

            formats.extend([
                f"{area}{prefix}{suffix}",           # 5551234567
                f"{area}-{prefix}-{suffix}",         # 555-123-4567
                f"({area}) {prefix}-{suffix}",       # (555) 123-4567
                f"{area}.{prefix}.{suffix}",         # 555.123.4567
            ])

        return formats

    def hunt_with_requests(self) -> Dict:
        """
        Hunt for names using requests library (faster but less reliable)
        """
        self.logger.info("🎯 Starting FastPeopleSearch requests-based name hunting...")
        results = {
            'found': False,
            'names': [],
            'addresses': [],
            'relatives': [],
            'method': 'requests',
            'confidence': 0.0
        }

        session = requests.Session()

        for format_phone in self.search_formats[:3]:  # Try top 3 formats
            try:
                # Longer random delay to avoid detection
                time.sleep(random.uniform(3, 8))

                # Enhanced headers to appear more human-like
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'max-age=0',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Linux"',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1',
                    'Referer': 'https://www.google.com/',
                    'DNT': '1',
                    'Connection': 'keep-alive'
                }

                # Search URL
                search_url = f"https://www.fastpeoplesearch.com/name/{quote(format_phone)}"

                self.logger.info(f"🔍 Searching FastPeopleSearch with format: {format_phone}")

                response = session.get(search_url, headers=headers, timeout=15)
                response.raise_for_status()

                # Parse results
                soup = BeautifulSoup(response.content, 'html.parser')
                parsed_data = self._parse_fastpeople_results(soup)

                if parsed_data['found']:
                    results.update(parsed_data)
                    results['search_format'] = format_phone
                    self.logger.info(f"💰 JACKPOT! Names found via requests: {parsed_data['names']}")
                    break

            except Exception as e:
                self.logger.warning(f"FastPeopleSearch requests error for {format_phone}: {e}")
                continue

        return results

    def hunt_with_selenium(self) -> Dict:
        """
        Hunt for names using Selenium (slower but more reliable)
        """
        self.logger.info("🎯 Starting FastPeopleSearch Selenium-based name hunting...")
        results = {
            'found': False,
            'names': [],
            'addresses': [],
            'relatives': [],
            'method': 'selenium',
            'confidence': 0.0
        }

        driver = None
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={random.choice(self.user_agents)}')

            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)

            for format_phone in self.search_formats[:3]:  # Try top 3 formats
                try:
                    search_url = f"https://www.fastpeoplesearch.com/name/{quote(format_phone)}"

                    self.logger.info(f"🔍 Selenium searching with format: {format_phone}")
                    driver.get(search_url)

                    # Wait for page to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )

                    # Random delay to mimic human behavior
                    time.sleep(random.uniform(2, 4))

                    # Parse results from page source
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    parsed_data = self._parse_fastpeople_results(soup)

                    if parsed_data['found']:
                        results.update(parsed_data)
                        results['search_format'] = format_phone
                        self.logger.info(f"🔥 SELENIUM JACKPOT! Names found: {parsed_data['names']}")
                        break

                except TimeoutException:
                    self.logger.warning(f"Selenium timeout for {format_phone}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Selenium error for {format_phone}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Selenium setup error: {e}")
        finally:
            if driver:
                driver.quit()

        return results

    def _parse_fastpeople_results(self, soup: BeautifulSoup) -> Dict:
        """
        Parse FastPeopleSearch results from HTML
        """
        results = {
            'found': False,
            'names': [],
            'addresses': [],
            'relatives': [],
            'confidence': 0.0
        }

        try:
            # Look for common FastPeopleSearch result patterns
            name_selectors = [
                '.name-link',
                '.result-name',
                '.person-name',
                'h3 a',
                '.search-result .name',
                '[data-name]'
            ]

            found_names = set()

            for selector in name_selectors:
                name_elements = soup.select(selector)
                for element in name_elements:
                    name_text = element.get_text(strip=True)
                    if name_text and len(name_text) > 2:
                        # Clean and validate name
                        cleaned_name = self._clean_name(name_text)
                        if cleaned_name:
                            found_names.add(cleaned_name)

            # Look for addresses
            address_selectors = [
                '.address',
                '.location',
                '.address-line',
                '[data-address]'
            ]

            found_addresses = set()
            for selector in address_selectors:
                addr_elements = soup.select(selector)
                for element in addr_elements:
                    addr_text = element.get_text(strip=True)
                    if addr_text and len(addr_text) > 5:
                        found_addresses.add(addr_text)

            # Look for relatives/associates
            relative_selectors = [
                '.relatives',
                '.associates',
                '.related-names',
                '.family-members'
            ]

            found_relatives = set()
            for selector in relative_selectors:
                rel_elements = soup.select(selector)
                for element in rel_elements:
                    rel_text = element.get_text(strip=True)
                    if rel_text and len(rel_text) > 2:
                        cleaned_rel = self._clean_name(rel_text)
                        if cleaned_rel:
                            found_relatives.add(cleaned_rel)

            if found_names:
                results.update({
                    'found': True,
                    'names': list(found_names),
                    'addresses': list(found_addresses),
                    'relatives': list(found_relatives),
                    'confidence': min(len(found_names) * 0.3, 1.0)
                })

        except Exception as e:
            self.logger.error(f"Error parsing FastPeopleSearch results: {e}")

        return results

    def _clean_name(self, name: str) -> Optional[str]:
        """
        Clean and validate extracted names
        """
        if not name:
            return None

        # Remove unwanted characters and extra whitespace
        cleaned = re.sub(r'[^\w\s\-\.]', '', name).strip()

        # Skip if too short or contains numbers
        if len(cleaned) < 3 or re.search(r'\d', cleaned):
            return None

        # Skip common false positives
        false_positives = {
            'search', 'results', 'name', 'phone', 'address', 'related',
            'view', 'profile', 'details', 'more', 'info', 'contact'
        }

        if cleaned.lower() in false_positives:
            return None

        # Title case for proper names
        return ' '.join(word.capitalize() for word in cleaned.split())

    def hunt_comprehensive(self) -> Dict:
        """
        Run comprehensive name hunting using all available methods
        """
        self.logger.info(f"🚀 Starting comprehensive FastPeopleSearch hunting for: {self.phone}")

        all_results = {
            'found': False,
            'names': [],
            'addresses': [],
            'relatives': [],
            'methods_used': [],
            'best_confidence': 0.0,
            'search_summary': {}
        }

        # Try requests method first (faster)
        requests_results = self.hunt_with_requests()
        if requests_results['found']:
            all_results.update({
                'found': True,
                'names': requests_results['names'],
                'addresses': requests_results['addresses'],
                'relatives': requests_results['relatives'],
                'best_confidence': requests_results['confidence']
            })
            all_results['methods_used'].append('requests')
            all_results['search_summary']['requests'] = requests_results

            self.logger.info(f"💰 REQUESTS SUCCESS: {len(requests_results['names'])} names found")

        # If requests failed or low confidence, try Selenium
        if not requests_results['found'] or requests_results['confidence'] < 0.5:
            self.logger.info("📡 Escalating to Selenium-based hunting...")
            selenium_results = self.hunt_with_selenium()

            if selenium_results['found']:
                # Merge results
                all_names = set(all_results['names'] + selenium_results['names'])
                all_addresses = set(all_results['addresses'] + selenium_results['addresses'])
                all_relatives = set(all_results['relatives'] + selenium_results['relatives'])

                all_results.update({
                    'found': True,
                    'names': list(all_names),
                    'addresses': list(all_addresses),
                    'relatives': list(all_relatives),
                    'best_confidence': max(all_results['best_confidence'], selenium_results['confidence'])
                })
                all_results['methods_used'].append('selenium')
                all_results['search_summary']['selenium'] = selenium_results

                self.logger.info(f"🔥 SELENIUM ENHANCEMENT: Total {len(all_names)} names found")

        # Final summary
        if all_results['found']:
            self.logger.info(f"🎯 FASTPEOPLE HUNT COMPLETE: {len(all_results['names'])} names, confidence: {all_results['best_confidence']:.2f}")
        else:
            self.logger.warning("❌ FastPeopleSearch hunting unsuccessful")

        return all_results


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python fastpeople_hunter.py <phone_number>")
        sys.exit(1)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    phone = sys.argv[1]
    hunter = FastPeopleHunter(phone)
    results = hunter.hunt_comprehensive()

    print(f"\n🎯 FastPeopleSearch Results for {phone}:")
    print(f"Found: {results['found']}")
    print(f"Names: {results['names']}")
    print(f"Confidence: {results['best_confidence']:.2f}")
    print(f"Methods: {', '.join(results['methods_used'])}")