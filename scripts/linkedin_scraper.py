#!/usr/bin/env python3
"""
LinkedIn Profile Scraping Solution
Multiple approaches to extract emails from LinkedIn profiles
"""

import os
import time
import requests
import logging
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

class LinkedInScraper:
    """
    Specialized LinkedIn profile scraper with multiple approach strategies
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def scrape_linkedin_profiles(self, profile_urls: List[str], target_name: str) -> Dict:
        """
        Main method to scrape LinkedIn profiles using best available approach
        """
        
        results = {
            'found': False,
            'emails': [],
            'profiles_scraped': 0,
            'profiles_blocked': 0,
            'method_used': None
        }
        
        self.logger.info(f"🔍 LinkedIn scraping for {len(profile_urls)} profiles")
        
        # Approach 1: Try Google Cache/Archive approach (often works)
        cache_results = self._scrape_via_google_cache(profile_urls, target_name)
        if cache_results['found']:
            results.update(cache_results)
            results['method_used'] = 'google_cache'
            return results
        
        # Approach 2: Try enhanced Selenium with anti-detection
        selenium_results = self._scrape_via_selenium(profile_urls, target_name)
        if selenium_results['found']:
            results.update(selenium_results)
            results['method_used'] = 'selenium_enhanced'
            return results
        
        # Approach 3: Try public LinkedIn data extraction (from search results)
        public_results = self._extract_from_search_snippets(profile_urls, target_name)
        if public_results['found']:
            results.update(public_results)
            results['method_used'] = 'search_snippets'
            return results
            
        self.logger.warning("❌ All LinkedIn scraping approaches failed")
        return results

    def _scrape_via_google_cache(self, profile_urls: List[str], target_name: str) -> Dict:
        """
        Try scraping LinkedIn via Google Cache (often has more accessible content)
        """
        results = {'found': False, 'emails': []}
        
        self.logger.info("🔍 Trying Google Cache approach for LinkedIn profiles")
        
        try:
            from ..api_utils import GoogleAPIClient
            google_client = GoogleAPIClient(
                os.getenv('GOOGLE_API_KEY'), 
                os.getenv('GOOGLE_CSE_ID')
            )
            
            for profile_url in profile_urls[:3]:  # Limit to top 3
                # Search for cached version
                cache_query = f'cache:{profile_url}'
                
                cache_data = google_client.search(cache_query, num_results=1)
                if cache_data and 'items' in cache_data:
                    for item in cache_data['items']:
                        snippet = item.get('snippet', '')
                        title = item.get('title', '')
                        
                        # Extract emails from cached content
                        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
                        found_emails = email_pattern.findall(f"{title} {snippet}")
                        
                        for email in found_emails:
                            if self._is_target_email(email, target_name):
                                results['emails'].append(email.lower())
                                self.logger.info(f"✅ Found email in Google cache: {email}")
        
        except Exception as e:
            self.logger.debug(f"Google cache approach failed: {e}")
        
        results['found'] = len(results['emails']) > 0
        return results

    def _scrape_via_selenium(self, profile_urls: List[str], target_name: str) -> Dict:
        """
        Try scraping via Selenium with enhanced anti-detection
        """
        results = {'found': False, 'emails': []}
        
        self.logger.info("🔍 Trying enhanced Selenium approach for LinkedIn")
        
        driver = None
        try:
            from .chrome_config import get_stealth_chrome_options
            
            # Enhanced Chrome options for LinkedIn
            options = get_stealth_chrome_options()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=options)
            
            # Execute script to hide webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            for profile_url in profile_urls[:2]:  # Limit to 2 for performance
                try:
                    self.logger.info(f"🔍 Selenium scraping: {profile_url}")
                    driver.get(profile_url)
                    
                    # Wait for page load
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                    
                    # Check if login wall
                    if 'authwall' in driver.current_url or 'login' in driver.current_url:
                        self.logger.warning("❌ LinkedIn login wall encountered")
                        results['profiles_blocked'] += 1
                        continue
                    
                    # Extract emails from page content
                    page_source = driver.page_source
                    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
                    found_emails = email_pattern.findall(page_source)
                    
                    for email in found_emails:
                        if self._is_target_email(email, target_name):
                            results['emails'].append(email.lower())
                            self.logger.info(f"✅ Selenium found email: {email}")
                    
                    results['profiles_scraped'] += 1
                    time.sleep(5)  # Polite delay
                    
                except Exception as e:
                    self.logger.debug(f"Selenium error for {profile_url}: {e}")
                    continue
            
        except Exception as e:
            self.logger.warning(f"Selenium approach failed: {e}")
        finally:
            if driver:
                driver.quit()
        
        results['found'] = len(results['emails']) > 0
        return results

    def _extract_from_search_snippets(self, profile_urls: List[str], target_name: str) -> Dict:
        """
        Extract emails from LinkedIn search result snippets (sometimes contains contact info)
        """
        results = {'found': False, 'emails': []}
        
        self.logger.info("🔍 Trying search snippet extraction for LinkedIn")
        
        # We already have the profile URLs from search results
        # The original search may have contained email snippets we can extract
        self.logger.info("💡 Search snippet data already processed in profile discovery phase")
        
        return results

    def _is_target_email(self, email: str, target_name: str) -> bool:
        """Check if email likely belongs to target"""
        email_lower = email.lower()
        
        if not target_name:
            return True
            
        name_parts = target_name.lower().split()
        for part in name_parts:
            if len(part) > 2 and part in email_lower:
                return True
        return False

# Factory function for integration
def scrape_linkedin_profiles(profile_urls: List[str], target_name: str) -> Dict:
    """
    Main function to scrape LinkedIn profiles using best available method
    """
    scraper = LinkedInScraper() 
    return scraper.scrape_linkedin_profiles(profile_urls, target_name)

# Alternative: Enhanced profile analysis without scraping
def analyze_linkedin_profiles(profile_urls: List[str], target_name: str) -> Dict:
    """
    Analyze LinkedIn profile URLs for intelligence without direct scraping
    Generates targeted email patterns based on username analysis
    """
    
    results = {
        'found': False,
        'emails': [],
        'usernames_discovered': [],
        'profile_analysis': [],
        'method': 'url_analysis'
    }
    
    logger = logging.getLogger(__name__)
    logger.info(f"🔍 Analyzing {len(profile_urls)} LinkedIn profile URLs for intelligence")
    
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    for profile_url in profile_urls:
        try:
            # Extract username from LinkedIn URL
            # Format: https://www.linkedin.com/in/ryan-lindley-77175b8
            username_match = re.search(r'/in/([^/?]+)', profile_url)
            if username_match:
                linkedin_username = username_match.group(1)
                results['usernames_discovered'].append({
                    'username': linkedin_username,
                    'platform': 'linkedin',
                    'url': profile_url,
                    'confidence': 0.9  # High confidence - direct from LinkedIn
                })
                
                # Generate targeted email patterns based on LinkedIn username
                email_patterns = generate_email_patterns_from_username(linkedin_username, target_name)
                results['emails'].extend(email_patterns)
                
                logger.info(f"🎯 LinkedIn username discovered: {linkedin_username}")
                logger.info(f"📧 Generated {len(email_patterns)} targeted email patterns")
        
        except Exception as e:
            logger.debug(f"URL analysis error for {profile_url}: {e}")
            continue
    
    results['found'] = len(results['emails']) > 0 or len(results['usernames_discovered']) > 0
    
    if results['found']:
        logger.info(f"✅ LinkedIn analysis: {len(results['usernames_discovered'])} usernames, {len(results['emails'])} email patterns")
    
    return results

def generate_email_patterns_from_username(linkedin_username: str, target_name: str) -> List[Dict]:
    """
    Generate targeted email patterns based on discovered LinkedIn username
    Much more accurate than generic name-based patterns
    """
    
    email_patterns = []
    personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com']
    
    # Clean the LinkedIn username (remove numbers, hyphens)
    clean_username = re.sub(r'[-0-9]+$', '', linkedin_username)  # Remove trailing numbers/hyphens
    
    # Pattern 1: Use LinkedIn username directly
    for domain in personal_domains:
        email_patterns.append({
            'email': f"{linkedin_username}@{domain}",
            'confidence': 0.8,  # High confidence - based on actual username
            'source': 'linkedin_username_analysis',
            'method': 'direct_username',
            'linkedin_username': linkedin_username
        })
    
    # Pattern 2: Use cleaned username  
    if clean_username != linkedin_username:
        for domain in personal_domains:
            email_patterns.append({
                'email': f"{clean_username}@{domain}",
                'confidence': 0.7,  # Good confidence - cleaned version
                'source': 'linkedin_username_analysis', 
                'method': 'cleaned_username',
                'linkedin_username': linkedin_username
            })
    
    return email_patterns

if __name__ == "__main__":
    # Test the LinkedIn analysis approach
    test_urls = [
        'https://www.linkedin.com/in/ryan-lindley-77175b8',
        'https://www.linkedin.com/in/rlindley-cyber'
    ]
    
    results = analyze_linkedin_profiles(test_urls, "Ryan Lindley")
    print(f"LinkedIn Analysis Results: {results}")
