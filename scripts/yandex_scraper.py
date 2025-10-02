#!/usr/bin/env python3
"""
Yandex Search Scraper for OSINT
Handles anti-bot measures, proxy rotation, and CAPTCHA detection
"""
import os
import time
import json
import random
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode
from typing import List, Dict, Optional
import re

class YandexScraper:
    """
    Yandex search scraper with built-in anti-detection measures
    """

    def __init__(self, phone_number, enriched_identity=None, proxy_list=None):
        self.phone = phone_number
        self.enriched_identity = enriched_identity or {}
        # Load proxies from config/proxies.txt if not explicitly provided
        self.proxy_list = proxy_list if proxy_list is not None else load_free_proxy_list()
        self.logger = logging.getLogger(__name__)

        # Anti-bot headers that mimic Russian browser (matching Russian SOCKS5 proxies)
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',  # Russian primary
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

        self.session = requests.Session()
        self.current_proxy_index = 0
        self.results_cache = {}

    def _get_random_user_agent(self) -> str:
        """Rotate user agents to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        ]
        return random.choice(user_agents)

    def _rotate_proxy(self) -> Optional[Dict]:
        """Get next proxy from pool (supports both HTTP and SOCKS5 formats)"""
        if not self.proxy_list:
            return None

        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)

        # If proxy already has protocol prefix (socks5h://, http://), use as-is
        if '://' in proxy:
            return {
                'http': proxy,
                'https': proxy
            }

        # Otherwise assume HTTP proxy format (legacy)
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }

    def _build_search_queries(self) -> List[str]:
        """
        Build targeted Yandex search queries
        Yandex is particularly good for Russian/Eastern European data
        """
        queries = []
        primary_name = None
        primary_email = None

        # Extract enriched identity data
        if self.enriched_identity.get('primary_names'):
            primary_name = self.enriched_identity['primary_names'][0]
        if self.enriched_identity.get('known_email'):
            primary_email = self.enriched_identity['known_email']

        # Priority 1: Name + Phone (best for Yandex)
        if primary_name:
            self.logger.info(f"Building Yandex queries with name: {primary_name}")
            queries.extend([
                f'"{primary_name}" "{self.phone}"',
                f'"{primary_name}" телефон {self.phone}',  # Russian for "telephone"
                f'"{primary_name}" site:vk.com',  # VKontakte (Russian social network)
                f'"{primary_name}" site:ok.ru',   # Odnoklassniki (Russian social network)
            ])

        # Priority 2: Email + Phone
        if primary_email:
            queries.extend([
                f'"{primary_email}" "{self.phone}"',
                f'"{primary_email}" site:vk.com',
            ])

        # Priority 3: Phone only (fallback)
        if not primary_name and not primary_email:
            self.logger.warning("No enriched data - using phone-only queries")
            queries.extend([
                f'"{self.phone}"',
                f'{self.phone} site:vk.com',
                f'{self.phone} site:ok.ru',
            ])

        # Limit to prevent rate limiting
        return queries[:5]

    def _detect_captcha(self, html: str) -> bool:
        """Detect if Yandex served a CAPTCHA page"""
        captcha_indicators = [
            'captcha',
            'SmartCaptcha',
            'showcaptcha',
            'Checking your browser',
            'Проверка браузера',  # "Browser check" in Russian
        ]

        html_lower = html.lower()
        for indicator in captcha_indicators:
            if indicator.lower() in html_lower:
                self.logger.warning(f"CAPTCHA detected: {indicator}")
                return True
        return False

    def _parse_yandex_results(self, html: str, query: str) -> List[Dict]:
        """Parse Yandex search results HTML"""
        results = []

        try:
            # Use lxml parser - more lenient with malformed HTML
            soup = BeautifulSoup(html, 'lxml')

            # Yandex search results are in divs with class 'serp-item' or 'organic'
            search_items = soup.find_all(['li', 'div'], class_=re.compile(r'serp-item|organic|search-result'))

            for item in search_items:
                try:
                    # Find title link
                    title_elem = item.find('a', href=True)
                    if not title_elem:
                        continue

                    url = title_elem.get('href', '')
                    title = title_elem.get_text(strip=True)

                    # Find snippet/description
                    snippet_elem = item.find(['div', 'span'], class_=re.compile(r'snippet|text-container|abstract'))
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                    # Skip if no meaningful data
                    if not url or not title:
                        continue

                    # Fix relative URLs
                    if url.startswith('/'):
                        url = 'https://yandex.com' + url

                    results.append({
                        'url': url,
                        'title': title,
                        'snippet': snippet,
                        'query': query,
                        'timestamp': time.time()
                    })

                except Exception as e:
                    self.logger.debug(f"Error parsing search item: {e}")
                    continue

            self.logger.info(f"Parsed {len(results)} results from Yandex")

        except Exception as e:
            self.logger.error(f"Error parsing Yandex HTML: {e}")

        return results

    def _search_yandex(self, query: str, max_retries: int = 3) -> List[Dict]:
        """
        Execute a single Yandex search with retry logic
        """
        results = []

        # Build Yandex search URL
        params = {
            'text': query,
            'lr': '84',  # Location: Moscow (can be changed)
        }
        search_url = f"https://yandex.com/search/?{urlencode(params)}"

        for attempt in range(max_retries):
            try:
                # Prepare headers with rotation
                headers = self.base_headers.copy()
                headers['User-Agent'] = self._get_random_user_agent()

                # Get proxy if available
                proxies = self._rotate_proxy()

                self.logger.info(f"Searching Yandex (attempt {attempt + 1}): {query}")
                self.logger.debug(f"URL: {search_url}")
                if proxies:
                    self.logger.debug(f"Using proxy: {list(proxies.values())[0]}")

                # Make request
                response = self.session.get(
                    search_url,
                    headers=headers,
                    proxies=proxies,
                    timeout=15,
                    allow_redirects=True
                )

                # Check response
                if response.status_code == 200:
                    # Check for CAPTCHA
                    if self._detect_captcha(response.text):
                        self.logger.warning(f"CAPTCHA encountered, attempt {attempt + 1}/{max_retries}")
                        time.sleep(random.uniform(10, 20))  # Longer delay for CAPTCHA
                        continue

                    # Parse results
                    results = self._parse_yandex_results(response.text, query)

                    if results:
                        self.logger.info(f"Successfully retrieved {len(results)} results")
                        return results
                    else:
                        self.logger.warning("No results found in response")

                elif response.status_code == 429:
                    self.logger.warning(f"Rate limited (429), waiting before retry...")
                    time.sleep(random.uniform(30, 60))

                else:
                    self.logger.warning(f"Unexpected status code: {response.status_code}")

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error: {e}")

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")

            # Random delay between retries
            if attempt < max_retries - 1:
                delay = random.uniform(5, 15)
                self.logger.info(f"Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

        self.logger.warning(f"Failed to get results after {max_retries} attempts")
        return results

    def search(self) -> Dict:
        """
        Execute all Yandex searches and categorize results
        """
        all_results = {
            'social_media': [],
            'russian_social': [],  # VK, OK, etc.
            'documents': [],
            'forums': [],
            'other': []
        }

        queries = self._build_search_queries()
        self.logger.info(f"Executing {len(queries)} Yandex searches")

        for i, query in enumerate(queries):
            self.logger.info(f"Query {i+1}/{len(queries)}: {query}")

            # Execute search
            results = self._search_yandex(query)

            # Categorize results
            for result in results:
                url_lower = result['url'].lower()

                # Russian social networks
                if any(site in url_lower for site in ['vk.com', 'ok.ru', 'mail.ru']):
                    all_results['russian_social'].append(result)

                # International social media
                elif any(site in url_lower for site in ['facebook.', 'linkedin.', 'twitter.', 'instagram.']):
                    all_results['social_media'].append(result)

                # Documents
                elif '.pdf' in url_lower or 'document' in url_lower:
                    all_results['documents'].append(result)

                # Forums
                elif any(term in url_lower for term in ['forum', 'thread', 'topic', 'discuss']):
                    all_results['forums'].append(result)

                # Other
                else:
                    all_results['other'].append(result)

            # Rate limiting delay between queries (important!)
            if i < len(queries) - 1:
                delay = random.uniform(8, 15)
                self.logger.info(f"Waiting {delay:.1f}s before next query...")
                time.sleep(delay)

        # Summary
        total = sum(len(v) for v in all_results.values())
        self.logger.info(f"Yandex search complete: {total} total results")
        self.logger.info(f"  - Russian social: {len(all_results['russian_social'])}")
        self.logger.info(f"  - International social: {len(all_results['social_media'])}")
        self.logger.info(f"  - Forums: {len(all_results['forums'])}")
        self.logger.info(f"  - Documents: {len(all_results['documents'])}")
        self.logger.info(f"  - Other: {len(all_results['other'])}")

        return all_results


def load_free_proxy_list() -> List[str]:
    """
    Load free proxy list (you can extend this with proxy scraping)
    For now returns empty list - add your own proxies here
    """
    # TODO: Implement proxy scraping from free proxy sites
    # Or load from a file: config/proxies.txt
    proxy_file = 'config/proxies.txt'

    if os.path.exists(proxy_file):
        try:
            with open(proxy_file, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
            return proxies
        except Exception as e:
            logging.warning(f"Could not load proxies: {e}")

    return []
