#!/usr/bin/env python3
"""
Proxy-Enhanced Google API Client
Integrates IPRoyal residential proxies with Google Custom Search for massive capacity increase
"""

import os
import time
import random
import requests
import logging
from typing import Dict, Optional
from .api_utils import RateLimitedAPIClient

class ProxyGoogleClient(RateLimitedAPIClient):
    """
    Google Custom Search API client with IPRoyal proxy rotation
    Each proxy gets independent 100 queries/day quota = massive capacity increase
    """

    def __init__(self, api_key: str, cse_id: str, use_iproyal: bool = True):
        # More conservative rate limiting with proxies
        super().__init__(base_delay=3.0, max_retries=3)
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.use_iproyal = use_iproyal
        self.iproyal_manager = None
        self.proxy_rotation_enabled = False
        
        # Initialize IPRoyal integration
        if self.use_iproyal:
            self._initialize_iproyal()

    def _initialize_iproyal(self):
        """Initialize IPRoyal whitelisted proxy (much simpler)"""
        try:
            # Load IPRoyal config
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'iproyal_config.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                if config.get('mode') == 'whitelisted':
                    # Simple whitelisted setup - no authentication needed
                    self.proxy_host = config.get('proxy_host', 'geo.iproyal.com')
                    self.proxy_port = config.get('proxy_port', 51222)
                    self.proxy_rotation_enabled = True
                    
                    self.logger.info(f"✅ IPRoyal whitelisted proxy enabled: {self.proxy_host}:{self.proxy_port}")
                    self.logger.info(f"🎯 Automatic geo-rotation for massive Google quota increase!")
                else:
                    self.logger.warning("IPRoyal config found but not in whitelisted mode")
            else:
                self.logger.warning("IPRoyal config not found - using direct connection")
                
        except Exception as e:
            self.logger.warning(f"IPRoyal initialization failed: {e}")
            self.proxy_rotation_enabled = False

    def search_with_proxy_rotation(self, query: str, num_results: int = 10) -> Optional[Dict]:
        """
        Perform Google search with automatic IPRoyal proxy rotation
        Each proxy gets independent quota = massive capacity increase
        """
        if not self.api_key or not self.cse_id:
            self.logger.warning("Google Custom Search API not configured")
            return None

        params = {
            'key': self.api_key,
            'cx': self.cse_id,
            'q': query,
            'num': num_results
        }

        # Try with IPRoyal whitelisted proxy first (much simpler)
        if self.proxy_rotation_enabled and hasattr(self, 'proxy_host') and hasattr(self, 'proxy_port'):
            # Simple whitelisted proxy format
            proxy_dict = {
                'http': f"socks5://{self.proxy_host}:{self.proxy_port}",
                'https': f"socks5://{self.proxy_host}:{self.proxy_port}"
            }
            
            self.logger.debug(f"Using IPRoyal whitelisted proxy: {self.proxy_host}:{self.proxy_port}")
            
            # Make request with proxy
            try:
                start_time = time.time()
                response = requests.get(
                    self.base_url, 
                    params=params, 
                    proxies=proxy_dict,
                    timeout=15
                )

                if response.status_code == 200:
                    response_time = time.time() - start_time
                    self.logger.info(f"✅ IPRoyal proxy search successful ({response_time:.2f}s)")
                    return response.json()
                elif response.status_code == 429:
                    self.logger.warning(f"🔄 IPRoyal proxy also rate limited - falling back to direct")
                    # With whitelisted approach, we don't rotate - just fallback to direct
                else:
                    self.logger.warning(f"IPRoyal proxy request failed: {response.status_code}")

            except Exception as e:
                self.logger.debug(f"IPRoyal proxy error: {e}")

        # Fallback to direct connection
        self.logger.debug("Using direct Google API connection (no proxy)")
        response = self.make_request_with_backoff(self.base_url, params=params)
        
        if response and response.status_code == 200:
            try:
                return response.json()
            except ValueError as e:
                self.logger.error(f"Invalid JSON in Google response: {e}")
                return None

        return None


    def search(self, query: str, num_results: int = 10) -> Optional[Dict]:
        """
        Main search method with automatic proxy rotation
        """
        return self.search_with_proxy_rotation(query, num_results)

# Factory function for easy integration
def create_enhanced_google_client(api_key: str, cse_id: str, use_iproyal: bool = True) -> ProxyGoogleClient:
    """Create Google client with optional IPRoyal proxy enhancement"""
    return ProxyGoogleClient(api_key, cse_id, use_iproyal)
