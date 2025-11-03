#!/usr/bin/env python3
"""
Shared API utilities for rate limiting and error handling
"""

import time
import random
import requests
import logging
import json
from typing import Dict, Optional
from pathlib import Path


class RateLimitedAPIClient:
    """
    Rate-limited API client with exponential backoff for handling API quotas
    """

    def __init__(self, base_delay: float = 2.0, max_retries: int = 3):
        self.base_delay = base_delay
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
        self.last_request_time = 0

    def make_request_with_backoff(self, url: str, params: Dict = None, headers: Dict = None,
                                timeout: int = 15, proxies: Dict = None) -> Optional[requests.Response]:
        """
        Make HTTP request with exponential backoff and rate limiting
        Now supports proxy routing for better reliability
        """
        if params is None:
            params = {}
        if headers is None:
            headers = {}

        # Enhanced rate limiting: longer delays to avoid 429 errors
        time_since_last = time.time() - self.last_request_time
        min_delay = max(self.base_delay, 5.0)  # Minimum 5 seconds between requests
        if time_since_last < min_delay:
            sleep_time = min_delay - time_since_last
            self.logger.info(f"Rate limiting: sleeping {sleep_time:.2f}s (enhanced to avoid 429)")
            time.sleep(sleep_time)

        for attempt in range(self.max_retries + 1):
            try:
                self.last_request_time = time.time()
                response = requests.get(url, params=params, headers=headers, timeout=timeout, proxies=proxies)

                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Too Many Requests
                    if attempt < self.max_retries:
                        # Exponential backoff with jitter
                        wait_time = (2 ** attempt) * self.base_delay + random.uniform(0, 1)
                        self.logger.warning(f"Rate limited (429). Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{self.max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(f"Rate limit exceeded. Max retries reached for: {url}")
                        return None
                elif response.status_code == 403:  # Forbidden
                    self.logger.warning(f"Access forbidden (403) for: {url}")
                    return None
                else:
                    # For other error codes, return the response to let caller handle
                    response.raise_for_status()
                    return response

            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) * self.base_delay
                    self.logger.warning(f"Request timeout. Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{self.max_retries + 1})")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Request timeout. Max retries reached for: {url}")
                    return None
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) * self.base_delay
                    self.logger.warning(f"Request error: {e}. Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{self.max_retries + 1})")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Request failed after {self.max_retries + 1} attempts: {e}")
                    return None

        return None


class GoogleAPIClient(RateLimitedAPIClient):
    """
    Specialized client for Google Custom Search API with enhanced rate limiting
    """

    def __init__(self, api_key: str, cse_id: str):
        # Google allows 100 queries per day for free tier, so we need more aggressive rate limiting
        super().__init__(base_delay=3.0, max_retries=3)  # 3 second minimum between requests
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def search(self, query: str, num_results: int = 10) -> Optional[Dict]:
        """
        Perform Google Custom Search with caching and enhanced rate limiting
        """
        if not self.api_key or not self.cse_id:
            self.logger.warning("Google Custom Search API not configured")
            return None

        # Check cache first
        try:
            from .query_cache import get_query_cache
            cache = get_query_cache()
            
            # Check if we should skip due to quota concerns
            if cache.should_skip_query('google'):
                self.logger.warning("🚫 Skipping Google query - approaching daily quota limit")
                return None
            
            # Try cached result first
            cached = cache.get_cached_result(query, 'google')
            if cached:
                self.logger.info(f"📦 Using cached result for: {query}")
                return cached
                
        except Exception as e:
            self.logger.debug(f"Cache check failed: {e}")

        params = {
            'key': self.api_key,
            'cx': self.cse_id,
            'q': query,
            'num': num_results
        }

        self.logger.info(f"Google search (rate-limited): {query}")
        response = self.make_request_with_backoff(self.base_url, params=params)

        if response and response.status_code == 200:
            try:
                result_data = response.json()
                
                # Cache successful result
                try:
                    cache.cache_result(query, 'google', result_data)
                    cache.track_quota_usage('google')
                except:
                    pass  # Don't break on cache failure
                    
                return result_data
            except ValueError as e:
                self.logger.error(f"Invalid JSON in Google response: {e}")
                return None

        return None


class SerpApiClient(RateLimitedAPIClient):
    """
    SerpApi Bing Search client - Replacement for deprecated Microsoft Bing API v7
    - 100-250 queries/month free tier (Microsoft retired their API Aug 2025)
    - Direct drop-in replacement for Bing Search API
    - Excellent for LinkedIn/employment searches (different index than Google)
    - Enhanced with IPRoyal proxy support for better reliability
    - Docs: https://serpapi.com/bing-search-api
    """

    def __init__(self, api_key: str):
        super().__init__(base_delay=0.5, max_retries=3)
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search.json"
        self.logger = logging.getLogger(__name__)
        self.proxy = None
        self._initialize_proxy()
    
    def _initialize_proxy(self):
        """Initialize IPRoyal whitelisted proxy for SerpAPI (improves reliability)"""
        try:
            config_path = Path(__file__).parent.parent / 'config' / 'iproyal_config.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                if config.get('enabled') and config.get('mode') == 'whitelisted':
                    proxy_host = config.get('proxy_host', 'geo.iproyal.com')
                    proxy_port = config.get('proxy_port', 51222)
                    
                    # HTTP proxy format for SerpAPI requests
                    self.proxy = {
                        'http': f'http://{proxy_host}:{proxy_port}',
                        'https': f'http://{proxy_host}:{proxy_port}'
                    }
                    self.logger.info(f"✅ SerpAPI using IPRoyal proxy: {proxy_host}:{proxy_port}")
        except Exception as e:
            self.logger.debug(f"IPRoyal proxy not configured for SerpAPI: {e}")
            self.proxy = None

    def search(self, query: str, num_results: int = 10) -> Optional[Dict]:
        """
        Perform SerpApi Bing Search with rate limiting
        Returns results in standardized format matching Google's response
        """
        if not self.api_key:
            self.logger.warning("SerpApi not configured")
            return None

        params = {
            'engine': 'bing',        # Use Bing search engine
            'q': query,              # Query string
            'api_key': self.api_key, # Authentication
            'num': num_results,      # Number of results
        }

        self.logger.info(f"SerpApi Bing search (rate-limited): {query}")
        
        # Use proxy if available for better reliability and speed
        response = self.make_request_with_backoff(self.base_url, params=params, proxies=self.proxy)

        if response and response.status_code == 200:
            try:
                data = response.json()

                # Convert SerpApi format to Google-compatible format
                items = []
                organic_results = data.get('organic_results', [])

                for result in organic_results:
                    item = {
                        'link': result.get('link', ''),
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'displayLink': result.get('displayed_link', '')
                    }
                    items.append(item)

                # Return in Google-compatible format
                return {
                    'items': items,
                    'searchInformation': {
                        'totalResults': len(items)
                    }
                }

            except Exception as e:
                self.logger.error(f"Error parsing SerpApi response: {e}")
                return None
        elif response and response.status_code == 401:
            self.logger.error("SerpApi authentication failed - check API key")
            return None
        elif response and response.status_code == 403:
            self.logger.error("SerpApi quota exhausted")
            return None

        return None

# Backward compatibility alias (Microsoft deprecated Bing API v7 in Aug 2025)
BingAPIClient = SerpApiClient


class YandexAPIClient(RateLimitedAPIClient):
    """
    Yandex XML Search API client - OSINT GOLD MINE
    - 10,000 queries/day free tier (100x better than Google!)
    - Better for people search (less aggressive privacy filtering)
    - Excellent LinkedIn/social media indexing
    - Great for international/Eastern European OSINT
    """

    def __init__(self, api_key: str, user_id: str):
        super().__init__(base_delay=1.0, max_retries=3)  # Yandex is less restrictive
        self.api_key = api_key
        self.user_id = user_id
        self.base_url = "https://yandex.com/search/xml"

    def search(self, query: str, num_results: int = 10) -> Optional[Dict]:
        """
        Perform Yandex XML Search with rate limiting
        Returns results in standardized format matching Google's response
        """
        if not self.api_key or not self.user_id:
            self.logger.warning("Yandex Search API not configured")
            return None

        # Yandex XML API parameters
        params = {
            'user': self.user_id,
            'key': self.api_key,
            'query': query,
            'l10n': 'en',
            'sortby': 'rlv',  # Sort by relevance
            'filter': 'none',  # No filtering (we want everything for OSINT)
            'maxpassages': 3,
            'groupby': f'attr=d.mode=deep.groups-on-page={num_results}.docs-in-group=1'
        }

        self.logger.info(f"Yandex search (rate-limited): {query}")
        response = self.make_request_with_backoff(self.base_url, params=params)

        if response and response.status_code == 200:
            try:
                # Parse Yandex XML response and convert to Google-compatible JSON format
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)

                # Extract search results from XML
                items = []
                for group in root.findall('.//group'):
                    doc = group.find('.//doc')
                    if doc is not None:
                        url_elem = doc.find('url')
                        title_elem = doc.find('title')
                        snippet_elem = doc.find('.//passage')

                        if url_elem is not None:
                            item = {
                                'link': url_elem.text,
                                'title': title_elem.text if title_elem is not None else '',
                                'snippet': snippet_elem.text if snippet_elem is not None else ''
                            }
                            items.append(item)

                # Return in Google-compatible format
                return {
                    'items': items,
                    'searchInformation': {
                        'totalResults': len(items)
                    }
                }

            except Exception as e:
                self.logger.error(f"Error parsing Yandex XML response: {e}")
                return None

        return None


class DuckDuckGoClient(RateLimitedAPIClient):
    """
    DuckDuckGo HTML scraping client - NO API KEY NEEDED
    Emergency fallback when all APIs exhausted
    """

    def __init__(self):
        super().__init__(base_delay=2.0, max_retries=2)
        self.base_url = "https://html.duckduckgo.com/html/"

    def search(self, query: str, num_results: int = 10) -> Optional[Dict]:
        """
        Scrape DuckDuckGo HTML results (no API key needed)
        Returns results in standardized format matching Google's response
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        params = {'q': query}

        self.logger.info(f"DuckDuckGo scraping (no API): {query}")
        response = self.make_request_with_backoff(
            self.base_url,
            params=params,
            headers=headers,
            timeout=15
        )

        if response and response.status_code == 200:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Parse DDG HTML results
                items = []
                result_divs = soup.find_all('div', class_='result')[:num_results]

                for div in result_divs:
                    link_elem = div.find('a', class_='result__a')
                    snippet_elem = div.find('a', class_='result__snippet')

                    if link_elem:
                        item = {
                            'link': link_elem.get('href', ''),
                            'title': link_elem.get_text(strip=True),
                            'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                        }
                        items.append(item)

                # Return in Google-compatible format
                return {
                    'items': items,
                    'searchInformation': {
                        'totalResults': len(items)
                    }
                }

            except Exception as e:
                self.logger.error(f"Error parsing DuckDuckGo HTML: {e}")
                return None

        return None


class FastPeopleSearchClient(RateLimitedAPIClient):
    """
    Specialized client for FastPeopleSearch with anti-bot headers
    """

    def __init__(self):
        super().__init__(base_delay=4.0, max_retries=2)  # More conservative for scraping

    def search(self, phone_query: str) -> Optional[str]:
        """
        Search FastPeopleSearch with proper headers to avoid 403 errors
        """
        # Enhanced headers to avoid bot detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

        url = f"https://www.fastpeoplesearch.com/name/{phone_query}"

        self.logger.info(f"FastPeopleSearch request: {phone_query}")
        response = self.make_request_with_backoff(url, headers=headers, timeout=20)

        if response and response.status_code == 200:
            return response.text

        return None


class NumVerifyClient(RateLimitedAPIClient):
    """
    Specialized client for NumVerify API with timeout handling
    """

    def __init__(self, api_key: str):
        super().__init__(base_delay=1.0, max_retries=2)
        self.api_key = api_key

    def validate(self, phone_number: str) -> Optional[Dict]:
        """
        Validate phone number with NumVerify API
        """
        if not self.api_key:
            self.logger.warning("NumVerify API key not configured")
            return None

        url = "http://apilayer.net/api/validate"
        params = {
            'access_key': self.api_key,
            'number': phone_number,
            'country_code': '',
            'format': '1'
        }

        self.logger.info(f"NumVerify validation: {phone_number}")
        response = self.make_request_with_backoff(url, params=params, timeout=15)

        if response and response.status_code == 200:
            try:
                return response.json()
            except ValueError as e:
                self.logger.error(f"Invalid JSON in NumVerify response: {e}")
                return None

        return None


class UnifiedSearchClient:
    """
    Intelligent multi-engine search client with automatic failover
    Routes queries to the best search engine for each use case

    Query Routing Strategy:
    - 'linkedin': SerpApi/Bing first (excellent LinkedIn indexing)
    - 'people': SerpApi/Bing first (good people search)
    - 'employment': SerpApi/Bing first (great for company pages)
    - 'email': Google first (historically best email indexing)
    - 'general': SerpApi/Bing first (100-250/month free vs Google's 100/day)

    Failover Chain: SerpApi (Bing) → Google → DuckDuckGo
    (Yandex removed - requires non-US billing)
    (Microsoft Bing API v7 deprecated Aug 2025 - using SerpApi replacement)
    """

    def __init__(self, google_client=None, bing_client=None, yandex_client=None, enable_ddg_fallback=True):
        self.google = google_client
        self.bing = bing_client
        self.yandex = yandex_client  # Keep for future if accessible
        self.ddg = DuckDuckGoClient() if enable_ddg_fallback else None
        self.logger = logging.getLogger(__name__)

        # Track quota exhaustion
        self.google_exhausted = False
        self.bing_exhausted = False
        self.yandex_exhausted = False

    def search(self, query: str, query_type: str = 'general', num_results: int = 10) -> Optional[Dict]:
        """
        Intelligent search with automatic engine selection and failover

        Args:
            query: Search query string
            query_type: Type of query for intelligent routing
                       ('linkedin', 'people', 'employment', 'email', 'general')
            num_results: Number of results to return

        Returns:
            Standardized results dict with 'items' list
        """

        # Determine primary and fallback engines based on query type
        if query_type in ['linkedin', 'people', 'employment']:
            # SerpApi (Bing index) excels at LinkedIn/professional network searches
            primary = self._try_bing
            secondary = self._try_google
            self.logger.info(f"🎯 Query type '{query_type}': Using SerpApi/Bing (excellent LinkedIn indexing)")
        elif query_type == 'email':
            # Google historically best for email discovery
            primary = self._try_google
            secondary = self._try_bing
            self.logger.info(f"🎯 Query type '{query_type}': Using Google (optimal for email search)")
        else:
            # Default: SerpApi first (100-250/month vs Google's 100/day)
            primary = self._try_bing
            secondary = self._try_google
            self.logger.info(f"🎯 Query type '{query_type}': Using SerpApi/Bing (100-250/month quota)")

        # Try primary engine
        result = primary(query, num_results)
        if result and result.get('items'):
            return result

        # Try secondary API engine
        self.logger.warning(f"⚠️ Primary engine failed, trying secondary API")
        result = secondary(query, num_results)
        if result and result.get('items'):
            return result

        # Emergency: Try DuckDuckGo scraping
        if self.ddg:
            self.logger.warning(f"🚨 All APIs failed/exhausted, using DuckDuckGo scraping")
            return self._try_duckduckgo(query, num_results)

        self.logger.error(f"❌ All search engines failed for query: {query}")
        return None

    def _try_bing(self, query: str, num_results: int) -> Optional[Dict]:
        """Try SerpApi Bing search (backward compatible method name)"""
        if self.bing_exhausted:
            self.logger.warning("SerpApi/Bing quota exhausted, skipping")
            return None

        if not self.bing:
            self.logger.warning("SerpApi/Bing client not configured")
            return None

        try:
            result = self.bing.search(query, num_results)
            if result:
                self.logger.info(f"✅ SerpApi/Bing search successful: {len(result.get('items', []))} results")
                return result
            else:
                self.logger.warning("SerpApi/Bing search returned no results")
                return None
        except Exception as e:
            # Check for 403 quota exhaustion
            if '403' in str(e) or 'quota' in str(e).lower():
                self.logger.error("SerpApi quota exhausted")
                self.bing_exhausted = True
            self.logger.error(f"SerpApi/Bing search error: {e}")
            return None

    def _try_yandex(self, query: str, num_results: int) -> Optional[Dict]:
        """Try Yandex search (kept for future if accessible from US)"""
        if self.yandex_exhausted:
            self.logger.warning("Yandex quota exhausted, skipping")
            return None

        if not self.yandex:
            self.logger.warning("Yandex client not configured")
            return None

        try:
            result = self.yandex.search(query, num_results)
            if result:
                self.logger.info(f"✅ Yandex search successful: {len(result.get('items', []))} results")
                return result
            else:
                # Check if quota exhausted (would need to parse Yandex error)
                self.logger.warning("Yandex search returned no results")
                return None
        except Exception as e:
            self.logger.error(f"Yandex search error: {e}")
            return None

    def _try_google(self, query: str, num_results: int) -> Optional[Dict]:
        """Try Google search"""
        if self.google_exhausted:
            self.logger.warning("Google quota exhausted, skipping")
            return None

        if not self.google:
            self.logger.warning("Google client not configured")
            return None

        try:
            result = self.google.search(query, num_results)
            if result:
                self.logger.info(f"✅ Google search successful: {len(result.get('items', []))} results")
                return result
            else:
                self.logger.warning("Google search returned no results")
                return None
        except Exception as e:
            # Check for 429 rate limit error
            if '429' in str(e):
                self.logger.error("Google API quota exhausted (429 error)")
                self.google_exhausted = True
            self.logger.error(f"Google search error: {e}")
            return None

    def _try_duckduckgo(self, query: str, num_results: int) -> Optional[Dict]:
        """Try DuckDuckGo scraping (emergency fallback)"""
        if not self.ddg:
            self.logger.warning("DuckDuckGo fallback not enabled")
            return None

        try:
            result = self.ddg.search(query, num_results)
            if result:
                self.logger.info(f"✅ DuckDuckGo scraping successful: {len(result.get('items', []))} results")
                return result
            else:
                self.logger.warning("DuckDuckGo scraping returned no results")
                return None
        except Exception as e:
            self.logger.error(f"DuckDuckGo scraping error: {e}")
            return None