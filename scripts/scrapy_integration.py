#!/usr/bin/env python3
"""
Scrapy Integration for Professional Profile Scraping
Robust LinkedIn, GitHub, and social media scraping with anti-detection
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional
from pathlib import Path

class ScrapyProfileScraper:
    """
    Professional-grade profile scraping using Scrapy for LinkedIn, GitHub, social media
    Much more robust than requests + BeautifulSoup approach
    """

    def __init__(self, target_name: str):
        self.target_name = target_name
        self.logger = logging.getLogger(__name__)
        self.results_dir = Path('./temp_scrapy_output')
        self.results_dir.mkdir(exist_ok=True)

    def check_scrapy_available(self) -> bool:
        """Check if Scrapy is installed"""
        try:
            import scrapy
            return True
        except ImportError:
            return False

    def create_scrapy_spider(self, profile_urls: List[str]) -> str:
        """
        Dynamically create a Scrapy spider for profile scraping
        Returns path to the generated spider file
        """
        
        spider_code = '''
import scrapy
import re
import json
from scrapy import Request
import time

class ProfileSpider(scrapy.Spider):
    name = "profile_email_scraper"
    
    # Anti-detection settings
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,  # Ignore robots.txt for OSINT
        'COOKIES_ENABLED': True,
        'SESSION_PERSISTENCE': True,
        
        # Anti-bot measures  
        'DOWNLOAD_DELAY': 3,  # 3 seconds between requests
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,  # Randomize delay (0.5-1.5x)
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        
        # Handle JavaScript-heavy sites
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        
        # Output format
        'FEEDS': {
            'profile_emails.json': {'format': 'json', 'overwrite': True},
        }
    }
    
    def __init__(self, profile_urls=None, target_name=None, *args, **kwargs):
        super(ProfileSpider, self).__init__(*args, **kwargs)
        self.profile_urls = profile_urls or []
        self.target_name = target_name or ""
        self.email_pattern = re.compile(r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b')
        
    def start_requests(self):
        """Generate initial requests for profile URLs"""
        for url in self.profile_urls:
            # Different handling for different platforms
            if 'linkedin.com' in url:
                yield self.create_linkedin_request(url)
            elif 'github.com' in url:
                yield self.create_github_request(url)
            else:
                yield self.create_generic_request(url)
    
    def create_linkedin_request(self, url):
        """Create LinkedIn-specific request with anti-detection"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        
        return Request(
            url=url,
            headers=headers,
            callback=self.parse_linkedin,
            meta={'dont_cache': True, 'platform': 'linkedin'}
        )
    
    def create_github_request(self, url):
        """Create GitHub-specific request"""
        return Request(
            url=url,
            callback=self.parse_github,
            meta={'platform': 'github'}
        )
    
    def create_generic_request(self, url):
        """Create generic request for other platforms"""
        return Request(
            url=url,
            callback=self.parse_generic,
            meta={'platform': 'generic'}
        )
    
    def parse_linkedin(self, response):
        """Parse LinkedIn profile for email addresses"""
        platform = 'linkedin'
        emails_found = []
        
        # LinkedIn often returns login wall - handle gracefully
        if 'authwall' in response.url or 'login' in response.text.lower():
            self.logger.warning(f"LinkedIn login wall encountered: {response.url}")
            return {'url': response.url, 'platform': platform, 'emails': [], 'blocked': True}
        
        # Extract emails from visible profile text
        profile_text = response.text
        emails = self.email_pattern.findall(profile_text)
        
        # Filter for personal emails only
        for email in emails:
            if self.is_personal_email(email) and self.matches_target(email):
                emails_found.append(email.lower())
        
        return {
            'url': response.url,
            'platform': platform,  
            'emails': list(set(emails_found)),
            'blocked': False
        }
    
    def parse_github(self, response):
        """Parse GitHub profile for email addresses"""
        platform = 'github'
        emails_found = []
        
        # GitHub email extraction patterns
        github_patterns = [
            r'"email":"([^"]+@[^"]+)"',  # JSON format
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,})',  # mailto links
        ]
        
        content = response.text
        for pattern_str in github_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.findall(content)
            for match in matches:
                if '@' in match and '.' in match:
                    emails_found.append(match.lower())
        
        # Also check standard email pattern
        emails = self.email_pattern.findall(content)
        for email in emails:
            if self.is_personal_email(email) and self.matches_target(email):
                emails_found.append(email.lower())
        
        return {
            'url': response.url,
            'platform': platform,
            'emails': list(set(emails_found)),
            'blocked': False
        }
    
    def parse_generic(self, response):
        """Parse generic profile page"""
        platform = 'generic'
        emails_found = []
        
        emails = self.email_pattern.findall(response.text)
        for email in emails:
            if self.is_personal_email(email) and self.matches_target(email):
                emails_found.append(email.lower())
        
        return {
            'url': response.url,
            'platform': platform,
            'emails': list(set(emails_found)),
            'blocked': False
        }
    
    def is_personal_email(self, email: str) -> bool:
        """Check if email is from personal provider"""
        personal_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'icloud.com', 'aol.com', 'protonmail.com'
        ]
        domain = email.split('@')[-1].lower() if '@' in email else ''
        return domain in personal_domains
    
    def matches_target(self, email: str) -> bool:
        """Check if email might belong to target"""
        if not self.target_name:
            return True
            
        email_lower = email.lower()
        name_parts = self.target_name.lower().split()
        
        for part in name_parts:
            if len(part) > 2 and part in email_lower:
                return True
        return False

'''

        spider_file = self.results_dir / 'profile_spider.py'
        with open(spider_file, 'w') as f:
            f.write(spider_code)
            
        return str(spider_file)

    def scrape_profiles_with_scrapy(self, profile_urls: List[str]) -> Dict:
        """
        Use Scrapy to scrape profile URLs for email addresses
        Much more robust than requests approach
        """
        
        if not self.check_scrapy_available():
            return {
                'found': False,
                'error': 'Scrapy not installed - pip install scrapy scrapy-splash',
                'emails': []
            }
        
        self.logger.info(f"🕷️ Using Scrapy to scrape {len(profile_urls)} profiles (robust approach)")
        
        # Create dynamic spider
        spider_file = self.create_scrapy_spider(profile_urls)
        
        # Run Scrapy spider
        try:
            import subprocess
            
            cmd = [
                'scrapy', 'runspider', spider_file,
                '-a', f'profile_urls={json.dumps(profile_urls)}',
                '-a', f'target_name={self.target_name}',
                '-o', str(self.results_dir / 'scrapy_results.json'),
                '--nolog'  # Suppress Scrapy logs (we have our own logging)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                # Parse Scrapy results
                results_file = self.results_dir / 'scrapy_results.json'
                if results_file.exists():
                    with open(results_file, 'r') as f:
                        scrapy_results = json.load(f)
                    
                    # Extract emails from all scraped profiles
                    all_emails = []
                    for result_item in scrapy_results:
                        emails = result_item.get('emails', [])
                        platform = result_item.get('platform', 'unknown')
                        url = result_item.get('url', '')
                        
                        if emails:
                            self.logger.info(f"✅ Scrapy found {len(emails)} emails on {platform}: {emails}")
                            all_emails.extend(emails)
                        else:
                            blocked = result_item.get('blocked', False)
                            if blocked:
                                self.logger.warning(f"❌ {platform} blocked scraping: {url}")
                            else:
                                self.logger.info(f"ℹ️ No emails found on {platform}: {url}")
                    
                    return {
                        'found': len(all_emails) > 0,
                        'emails': list(set(all_emails)),  # Remove duplicates
                        'profiles_scraped': len(scrapy_results),
                        'method': 'scrapy'
                    }
            else:
                self.logger.error(f"Scrapy execution failed: {result.stderr}")
                return {'found': False, 'error': result.stderr, 'emails': []}
                
        except subprocess.TimeoutExpired:
            self.logger.warning("Scrapy scraping timed out after 2 minutes")
            return {'found': False, 'error': 'Timeout', 'emails': []}
        except Exception as e:
            self.logger.error(f"Scrapy scraping error: {e}")
            return {'found': False, 'error': str(e), 'emails': []}
        finally:
            # Cleanup temporary files
            try:
                import shutil
                shutil.rmtree(self.results_dir, ignore_errors=True)
            except:
                pass

# Integration function for email_hunter.py
def scrape_profiles_with_scrapy(profile_urls: List[str], target_name: str) -> Dict:
    """
    Scrape profile URLs using Scrapy (much more robust than requests)
    Returns emails found across all profiles
    """
    scraper = ScrapyProfileScraper(target_name)
    return scraper.scrape_profiles_with_scrapy(profile_urls)

# Installation and setup functions
def get_scrapy_status() -> Dict:
    """Check Scrapy installation status and provide setup guide"""
    
    try:
        import scrapy
        scrapy_available = True
        scrapy_version = scrapy.__version__
    except ImportError:
        scrapy_available = False
        scrapy_version = None
    
    return {
        'scrapy_available': scrapy_available,
        'version': scrapy_version,
        'install_command': 'pip install scrapy scrapy-splash',
        'benefits': [
            'JavaScript rendering for modern sites',
            'Smart anti-bot detection avoidance', 
            'Session management and cookies',
            'Parallel scraping for speed',
            'LinkedIn-friendly scraping',
            'Professional-grade reliability'
        ],
        'vs_current': {
            'current': 'requests + BeautifulSoup (basic, easily blocked)',
            'scrapy': 'Industry standard web scraping (robust, anti-detection)'
        }
    }

if __name__ == "__main__":
    # Test Scrapy integration
    status = get_scrapy_status()
    print(f"Scrapy Integration Status: {json.dumps(status, indent=2)}")
    
    if status['scrapy_available']:
        print("✅ Ready for enhanced profile scraping!")
    else:
        print("❌ Install Scrapy: pip install scrapy scrapy-splash")
