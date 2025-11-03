#!/usr/bin/env python3
import requests
import json
import time
import logging
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class SocialMediaScanner:
    def __init__(self, phone_number, discovered_emails=None, enriched_identity=None):
        self.phone = phone_number
        self.emails = discovered_emails or []
        self.enriched_identity = enriched_identity or {}
        self.logger = logging.getLogger(__name__)
        self.setup_selenium()
        
    def setup_selenium(self):
        """Setup headless Chrome for dynamic content"""
        try:
            from .chrome_config import get_stealth_chrome_options
            options = get_stealth_chrome_options()
            
            # Add social scanner specific options
            options.add_argument('--remote-debugging-port=9222')
            
            self.driver = webdriver.Chrome(options=options)
            self.selenium_available = True
        except Exception as e:
            self.logger.warning(f"Selenium setup failed: {e}. Using fallback methods.")
            self.driver = None
            self.selenium_available = False
        
    def check_facebook(self):
        """Check Facebook using phone number and discovered emails"""
        self.logger.info("Checking Facebook...")
        results = {
            'platform': 'facebook',
            'found': False,
            'profiles': [],
            'search_urls': []
        }

        # Facebook search by phone number
        phone_search_url = f"https://www.facebook.com/search/top?q={self.phone}"
        results['search_urls'].append({'type': 'phone', 'url': phone_search_url})

        # Facebook search by discovered emails
        for email in self.emails[:3]:  # Limit to first 3 emails
            email_search_url = f"https://www.facebook.com/search/top?q={email}"
            results['search_urls'].append({'type': 'email', 'url': email_search_url, 'email': email})

        # Additional metadata
        results['note'] = f"Manual verification required. {len(self.emails)} emails available for search."

        return results
    
    def _scrape_linkedin_profile(self, profile_url: str) -> dict:
        """Scrape LinkedIn public profile for comprehensive data (login-wall limited)"""
        data = {
            'emails': [],
            'location': None,
            'headline': None,
            'full_name': None,
            'company': None,
            'job_title': None,
            'scraped': False
        }

        if not self.selenium_available:
            return data

        try:
            self.driver.get(profile_url)
            time.sleep(3)

            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # LinkedIn often shows limited data without login, but try anyway
            # Extract full name
            name_elem = soup.find('h1', {'class': re.compile(r'.*top-card.*name.*')})
            if name_elem:
                data['full_name'] = name_elem.get_text().strip()

            # Extract headline/job title
            headline_elem = soup.find('div', {'class': re.compile(r'.*top-card.*headline.*')})
            if headline_elem:
                data['headline'] = headline_elem.get_text().strip()

            # Extract location
            location_elem = soup.find('span', {'class': re.compile(r'.*top-card.*location.*')})
            if location_elem:
                data['location'] = location_elem.get_text().strip()

            # Try to extract company/job title from headline
            if data['headline']:
                # Pattern: "Job Title at Company"
                job_match = re.search(r'(.+?)\s+at\s+(.+)', data['headline'])
                if job_match:
                    data['job_title'] = job_match.group(1).strip()
                    data['company'] = job_match.group(2).strip()

            data['scraped'] = True

            if data['full_name']:
                self.logger.info(f"🎯 LinkedIn: {data['full_name']} - {data['headline']}")

            return data

        except Exception as e:
            self.logger.warning(f"LinkedIn scrape error: {e}")
            data['error'] = str(e)
            return data

    def check_linkedin(self):
        """Check LinkedIn using public search methods"""
        self.logger.info("Checking LinkedIn...")
        results = {
            'platform': 'linkedin',
            'found': False,
            'profiles': [],
            'usernames_discovered': [],
            'search_urls': []
        }

        # Get primary name if available
        primary_name = None
        if self.enriched_identity.get('primary_names'):
            primary_name = self.enriched_identity['primary_names'][0]

        # LinkedIn search by name (via Google - more effective than LinkedIn direct)
        if primary_name and self.selenium_available:
            try:
                search_query = f"site:linkedin.com/in/ {primary_name}"
                search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                self.driver.get(search_url)
                time.sleep(3)

                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                # Extract LinkedIn profile URLs from Google results
                linkedin_urls = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if 'linkedin.com/in/' in href:
                        # Extract clean profile URL
                        match = re.search(r'(https://[a-z]{2,3}\.linkedin\.com/in/[^/?&]+)', href)
                        if match:
                            linkedin_urls.append(match.group(1))

                # Dedupe and limit
                linkedin_urls = list(set(linkedin_urls))[:3]

                # Attempt to scrape each profile (likely login-walled)
                for profile_url in linkedin_urls:
                    username = profile_url.split('/in/')[-1]
                    self.logger.info(f"🔍 Attempting LinkedIn profile scrape: {username} (login-wall limited)")
                    scrape_result = self._scrape_linkedin_profile(profile_url)

                    # Track discovered username
                    results['usernames_discovered'].append({
                        'platform': 'linkedin',
                        'username': username,
                        'profile_url': profile_url
                    })

                    # Store profile data if we got anything
                    if scrape_result.get('full_name') or scrape_result.get('headline'):
                        results['found'] = True
                        results['profiles'].append({
                            'username': username,
                            'full_name': scrape_result.get('full_name'),
                            'headline': scrape_result.get('headline'),
                            'location': scrape_result.get('location'),
                            'company': scrape_result.get('company'),
                            'job_title': scrape_result.get('job_title')
                        })

                    time.sleep(2)

            except Exception as e:
                self.logger.warning(f"LinkedIn search/scrape error: {e}")

        # Generate search URLs for manual checking
        if primary_name:
            search_url = f"https://www.linkedin.com/search/results/all/?keywords={primary_name.replace(' ', '%20')}"
            results['search_urls'].append({'type': 'name_search', 'url': search_url})

        results['note'] = f"LinkedIn login-wall restricts scraping. Found {len(results['usernames_discovered'])} profiles, {len(results['profiles'])} with data. Manual verification recommended."
        return results
    
    def check_telegram(self):
        """Check Telegram via API"""
        self.logger.info("Checking Telegram...")
        results = {
            'platform': 'telegram',
            'found': False,
            'username': None
        }
        
        # This would require Telegram API setup
        # Placeholder for implementation
        
        return results
    
    def check_whatsapp(self):
        """Check WhatsApp (limited check)"""
        self.logger.info("Checking WhatsApp...")
        results = {
            'platform': 'whatsapp',
            'found': False,
            'business_account': False
        }
        
        # WhatsApp Business API check could go here
        # Requires API access
        
        return results
    
    def _extract_emails_from_text(self, text: str) -> list:
        """Extract email addresses from text content"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return list(set(emails))  # Dedupe

    def _scrape_twitter_profile(self, username: str) -> dict:
        """Scrape Twitter profile for comprehensive data extraction using 2025 data-testid selectors"""
        data = {
            'emails': [],
            'phone_numbers': [],
            'location': None,
            'bio_text': '',
            'website': None,
            'full_name': None,
            'follower_count': None,
            'scraped': False
        }

        if not self.selenium_available:
            return data

        try:
            url = f"https://twitter.com/{username}"
            self.driver.get(url)
            time.sleep(3)

            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract bio using CORRECT 2025 data-testid selectors
            bio_elem = soup.find('div', {'data-testid': 'UserDescription'})
            if bio_elem:
                data['bio_text'] = bio_elem.get_text().strip()

            # Extract user full name
            name_elem = soup.find('div', {'data-testid': 'UserName'})
            if name_elem:
                # UserName contains both display name and @handle
                name_parts = name_elem.get_text().strip().split('@')
                if name_parts:
                    data['full_name'] = name_parts[0].strip()

            # Extract location
            location_elem = soup.find('span', {'data-testid': 'UserLocation'})
            if location_elem:
                data['location'] = location_elem.get_text().strip()

            # Extract website
            website_elem = soup.find('a', {'data-testid': 'UserUrl'})
            if website_elem:
                data['website'] = website_elem.get('href')

            # Extract follower count
            follower_elem = soup.find('a', href=re.compile(r'/verified_followers$|/followers$'))
            if follower_elem:
                follower_text = follower_elem.get_text()
                data['follower_count'] = follower_text

            # Extract emails and phone numbers from bio
            data['emails'] = self._extract_emails_from_text(data['bio_text'])

            # Phone number pattern
            phone_pattern = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
            phones = re.findall(phone_pattern, data['bio_text'])
            data['phone_numbers'] = [''.join(p) for p in phones]

            data['scraped'] = True

            if data['emails']:
                self.logger.info(f"🎯 Twitter @{username}: {len(data['emails'])} emails, location: {data['location']}")

            return data

        except Exception as e:
            self.logger.warning(f"Twitter scrape error for {username}: {e}")
            data['error'] = str(e)
            return data

    def check_twitter_x(self):
        """Check Twitter/X and scrape profiles for emails"""
        self.logger.info("Checking Twitter/X...")
        results = {
            'platform': 'twitter_x',
            'found': False,
            'profiles': [],
            'emails_discovered': [],
            'usernames_discovered': [],
            'search_urls': []
        }

        # Get primary name if available
        primary_name = None
        if self.enriched_identity.get('primary_names'):
            primary_name = self.enriched_identity['primary_names'][0]

        # Try to find profile by name
        if primary_name and self.selenium_available:
            try:
                # Search Twitter for name
                search_url = f"https://twitter.com/search?q={primary_name.replace(' ', '%20')}&f=user"
                self.driver.get(search_url)
                time.sleep(3)

                # Get potential usernames from search results
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                # Find profile links
                profile_links = soup.find_all('a', href=re.compile(r'^/[^/]+$'))
                usernames = []
                for link in profile_links[:3]:  # Top 3 results
                    username = link['href'].strip('/')
                    if username and not username.startswith('search'):
                        usernames.append(username)

                # Scrape each profile for comprehensive data
                for username in usernames:
                    self.logger.info(f"🔍 Scraping Twitter profile: @{username}")
                    scrape_result = self._scrape_twitter_profile(username)

                    # Always track discovered username
                    results['usernames_discovered'].append({
                        'platform': 'twitter',
                        'username': username,
                        'profile_url': f"https://twitter.com/{username}"
                    })

                    # Store comprehensive profile data
                    profile_data = {
                        'username': username,
                        'full_name': scrape_result.get('full_name'),
                        'emails': scrape_result.get('emails', []),
                        'phone_numbers': scrape_result.get('phone_numbers', []),
                        'location': scrape_result.get('location'),
                        'website': scrape_result.get('website'),
                        'follower_count': scrape_result.get('follower_count'),
                        'bio_preview': scrape_result.get('bio_text', '')[:200]
                    }

                    if scrape_result.get('emails') or scrape_result.get('phone_numbers') or scrape_result.get('location'):
                        results['emails_discovered'].extend(scrape_result.get('emails', []))
                        results['found'] = True
                        results['profiles'].append(profile_data)

                    time.sleep(2)  # Rate limit

            except Exception as e:
                self.logger.warning(f"Twitter search/scrape error: {e}")

        # Generate search URLs for manual checking
        if primary_name:
            search_url = f"https://twitter.com/search?q={primary_name.replace(' ', '%20')}"
            results['search_urls'].append({'type': 'name_search', 'url': search_url})

        results['note'] = f"Scraped {len(results['profiles'])} profiles, found {len(results['emails_discovered'])} emails, {len(results['usernames_discovered'])} usernames"
        return results

    def _scrape_instagram_profile(self, username: str) -> dict:
        """Scrape Instagram profile for comprehensive data extraction"""
        data = {
            'emails': [],
            'phone_numbers': [],
            'location': None,
            'bio_text': '',
            'website': None,
            'full_name': None,
            'category': None,  # Business category
            'scraped': False
        }

        if not self.selenium_available:
            return data

        try:
            url = f"https://www.instagram.com/{username}/"
            self.driver.get(url)
            time.sleep(3)

            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract bio
            bio_selectors = [
                'div[class*="biography"]',
                'h1[class*="_aacl"]',
                'div[class*="_aa_c"]',
                'span[class*="_aade"]'
            ]

            for selector in bio_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    data['bio_text'] += elem.get_text() + " "

            # Extract full name
            name_elem = soup.find('span', {'class': re.compile(r'.*_aacl.*')})
            if name_elem:
                data['full_name'] = name_elem.get_text().strip()

            # Extract website/link
            link_elem = soup.find('a', {'class': re.compile(r'.*external_link.*')})
            if link_elem:
                data['website'] = link_elem.get('href')

            # Extract emails and phone numbers
            data['emails'] = self._extract_emails_from_text(data['bio_text'])

            phone_pattern = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
            phones = re.findall(phone_pattern, data['bio_text'])
            data['phone_numbers'] = [''.join(p) for p in phones]

            data['scraped'] = True

            if data['emails']:
                self.logger.info(f"🎯 Instagram @{username}: {len(data['emails'])} emails, name: {data['full_name']}")

            return data

        except Exception as e:
            self.logger.warning(f"Instagram scrape error for {username}: {e}")
            data['error'] = str(e)
            return data

    def check_instagram(self):
        """Check Instagram and scrape profiles for emails"""
        self.logger.info("Checking Instagram...")
        results = {
            'platform': 'instagram',
            'found': False,
            'profiles': [],
            'emails_discovered': [],
            'usernames_discovered': [],
            'search_urls': []
        }

        # Get primary name if available
        primary_name = None
        if self.enriched_identity.get('primary_names'):
            primary_name = self.enriched_identity['primary_names'][0]

        # Try to find profile by name
        if primary_name and self.selenium_available:
            try:
                # Google search for Instagram profile (Instagram search requires login)
                search_query = f"site:instagram.com {primary_name}"
                search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                self.driver.get(search_url)
                time.sleep(3)

                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                # Extract Instagram profile URLs from Google results
                instagram_urls = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if 'instagram.com/' in href and '/p/' not in href:  # Profile, not post
                        # Extract clean username from URL
                        import re
                        match = re.search(r'instagram\.com/([^/\?]+)', href)
                        if match:
                            username = match.group(1)
                            if username not in ['explore', 'accounts', 'directory']:
                                instagram_urls.append(username)

                # Dedupe and limit
                instagram_urls = list(set(instagram_urls))[:3]

                # Scrape each profile
                for username in instagram_urls:
                    self.logger.info(f"🔍 Scraping Instagram profile: @{username}")
                    scrape_result = self._scrape_instagram_profile(username)

                    # Always track discovered username
                    results['usernames_discovered'].append({
                        'platform': 'instagram',
                        'username': username,
                        'profile_url': f"https://www.instagram.com/{username}/"
                    })

                    # Store comprehensive profile data
                    profile_data = {
                        'username': username,
                        'full_name': scrape_result.get('full_name'),
                        'emails': scrape_result.get('emails', []),
                        'phone_numbers': scrape_result.get('phone_numbers', []),
                        'website': scrape_result.get('website'),
                        'bio_preview': scrape_result.get('bio_text', '')[:200]
                    }

                    if scrape_result.get('emails') or scrape_result.get('phone_numbers') or scrape_result.get('full_name'):
                        results['emails_discovered'].extend(scrape_result.get('emails', []))
                        results['found'] = True
                        results['profiles'].append(profile_data)

                    time.sleep(2)

            except Exception as e:
                self.logger.warning(f"Instagram search/scrape error: {e}")

        # Generate search URLs for manual checking
        if primary_name:
            search_url = f"https://www.google.com/search?q=site:instagram.com+{primary_name.replace(' ', '+')}"
            results['search_urls'].append({'type': 'name_search', 'url': search_url})

        results['note'] = f"Scraped {len(results['profiles'])} profiles, found {len(results['emails_discovered'])} emails, {len(results['usernames_discovered'])} usernames"
        return results

    def _scrape_github_profile(self, username: str) -> dict:
        """Scrape GitHub profile for comprehensive data extraction"""
        data = {
            'emails': [],
            'location': None,
            'bio_text': '',
            'website': None,
            'full_name': None,
            'company': None,
            'twitter_username': None,
            'scraped': False
        }

        if not self.selenium_available:
            return data

        try:
            url = f"https://github.com/{username}"
            self.driver.get(url)
            time.sleep(2)

            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract full name
            name_elem = soup.find('span', {'class': 'p-name'}) or soup.find('span', {'itemprop': 'name'})
            if name_elem:
                data['full_name'] = name_elem.get_text().strip()

            # Extract location
            location_elem = soup.find('span', {'class': 'p-label'})
            if location_elem:
                data['location'] = location_elem.get_text().strip()

            # Extract company
            company_elem = soup.find('span', {'class': 'p-org'})
            if company_elem:
                data['company'] = company_elem.get_text().strip()

            # Extract website
            website_elem = soup.find('a', {'class': 'Link--primary'}) or soup.find('a', {'itemprop': 'url'})
            if website_elem:
                data['website'] = website_elem.get('href')

            # Extract Twitter username
            twitter_elem = soup.find('a', {'href': re.compile(r'twitter\.com')})
            if twitter_elem:
                twitter_match = re.search(r'twitter\.com/([^/?]+)', twitter_elem.get('href', ''))
                if twitter_match:
                    data['twitter_username'] = twitter_match.group(1)

            # Extract bio
            bio_selectors = [
                'div[class*="user-profile-bio"]',
                'div[data-bio-text]',
                'article[class*="markdown-body"]',
                'div[class*="vcard-detail"]'
            ]

            for selector in bio_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    data['bio_text'] += elem.get_text() + " "

            # Extract emails
            data['emails'] = self._extract_emails_from_text(data['bio_text'])

            data['scraped'] = True

            if data['emails']:
                self.logger.info(f"🎯 GitHub {username}: {len(data['emails'])} emails, company: {data['company']}")

            return data

        except Exception as e:
            self.logger.warning(f"GitHub scrape error for {username}: {e}")
            data['error'] = str(e)
            return data

    def check_github(self):
        """Check GitHub and scrape profiles for emails"""
        self.logger.info("Checking GitHub...")
        results = {
            'platform': 'github',
            'found': False,
            'profiles': [],
            'emails_discovered': [],
            'usernames_discovered': [],
            'search_urls': []
        }

        # Get primary name if available
        primary_name = None
        if self.enriched_identity.get('primary_names'):
            primary_name = self.enriched_identity['primary_names'][0]

        # Search by name first
        if primary_name and self.selenium_available:
            try:
                search_url = f"https://github.com/search?q={primary_name.replace(' ', '+')}&type=users"
                self.driver.get(search_url)
                time.sleep(3)

                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                # Extract GitHub usernames from search results
                usernames = []
                for link in soup.find_all('a', {'data-hovercard-type': 'user'}):
                    href = link.get('href', '')
                    if href.startswith('/') and len(href.split('/')) == 2:
                        username = href.strip('/')
                        usernames.append(username)

                # Dedupe and limit
                usernames = list(set(usernames))[:3]

                # Scrape each profile
                for username in usernames:
                    self.logger.info(f"🔍 Scraping GitHub profile: {username}")
                    scrape_result = self._scrape_github_profile(username)

                    # Always track discovered username
                    results['usernames_discovered'].append({
                        'platform': 'github',
                        'username': username,
                        'profile_url': f"https://github.com/{username}"
                    })

                    # Store comprehensive profile data
                    profile_data = {
                        'username': username,
                        'full_name': scrape_result.get('full_name'),
                        'company': scrape_result.get('company'),
                        'location': scrape_result.get('location'),
                        'emails': scrape_result.get('emails', []),
                        'website': scrape_result.get('website'),
                        'twitter_username': scrape_result.get('twitter_username'),
                        'bio_preview': scrape_result.get('bio_text', '')[:200]
                    }

                    if scrape_result.get('emails') or scrape_result.get('company') or scrape_result.get('location'):
                        results['emails_discovered'].extend(scrape_result.get('emails', []))
                        results['found'] = True
                        results['profiles'].append(profile_data)

                    time.sleep(2)

            except Exception as e:
                self.logger.warning(f"GitHub search/scrape error: {e}")

        # Also search by discovered emails
        for email in self.emails[:3]:
            github_search_url = f"https://github.com/search?q={email}&type=users"
            results['search_urls'].append({'type': 'email', 'url': github_search_url, 'email': email})

        results['note'] = f"Scraped {len(results['profiles'])} profiles, found {len(results['emails_discovered'])} emails, {len(results['usernames_discovered'])} usernames"
        return results

    def scan_all_platforms(self):
        """Scan all configured platforms with comprehensive data aggregation"""
        results = {
            'summary': {
                'total_platforms': 0,
                'emails_used': len(self.emails),
                'search_urls_generated': 0,
                'total_usernames_found': 0,
                'total_emails_discovered': 0,
                'total_locations_found': 0,
                'total_companies_found': 0
            },
            'aggregated_data': {
                'all_emails': [],
                'all_usernames': [],
                'all_locations': [],
                'all_companies': [],
                'all_phone_numbers': [],
                'all_websites': []
            }
        }

        platforms = [
            ('facebook', self.check_facebook),
            ('linkedin', self.check_linkedin),
            ('twitter_x', self.check_twitter_x),
            ('instagram', self.check_instagram),
            ('github', self.check_github),
            ('telegram', self.check_telegram),
            ('whatsapp', self.check_whatsapp),
        ]

        total_search_urls = 0

        for platform_name, checker_func in platforms:
            try:
                platform_results = checker_func()
                results[platform_name] = platform_results

                # Aggregate discovered data
                if 'emails_discovered' in platform_results:
                    results['aggregated_data']['all_emails'].extend(platform_results['emails_discovered'])

                if 'usernames_discovered' in platform_results:
                    results['aggregated_data']['all_usernames'].extend(platform_results['usernames_discovered'])

                # Extract locations, companies, etc from profiles
                if 'profiles' in platform_results:
                    for profile in platform_results['profiles']:
                        if profile.get('location'):
                            results['aggregated_data']['all_locations'].append({
                                'platform': platform_name,
                                'location': profile['location']
                            })
                        if profile.get('company'):
                            results['aggregated_data']['all_companies'].append({
                                'platform': platform_name,
                                'company': profile['company']
                            })
                        if profile.get('website'):
                            results['aggregated_data']['all_websites'].append({
                                'platform': platform_name,
                                'website': profile['website']
                            })
                        if profile.get('phone_numbers'):
                            results['aggregated_data']['all_phone_numbers'].extend(profile['phone_numbers'])

                # Count search URLs
                if 'search_urls' in platform_results:
                    total_search_urls += len(platform_results['search_urls'])

                time.sleep(1)  # Rate limiting
            except Exception as e:
                self.logger.error(f"Error checking {platform_name}: {e}")
                results[platform_name] = {'error': str(e)}

        # Dedupe aggregated data
        results['aggregated_data']['all_emails'] = list(set(results['aggregated_data']['all_emails']))
        results['aggregated_data']['all_phone_numbers'] = list(set(results['aggregated_data']['all_phone_numbers']))

        # Update summary counts
        results['summary']['total_platforms'] = len(platforms)
        results['summary']['search_urls_generated'] = total_search_urls
        results['summary']['total_usernames_found'] = len(results['aggregated_data']['all_usernames'])
        results['summary']['total_emails_discovered'] = len(results['aggregated_data']['all_emails'])
        results['summary']['total_locations_found'] = len(results['aggregated_data']['all_locations'])
        results['summary']['total_companies_found'] = len(results['aggregated_data']['all_companies'])

        if self.driver:
            self.driver.quit()

        self.logger.info(f"🎯 Social media scan complete: {len(platforms)} platforms scanned")
        self.logger.info(f"   📧 {results['summary']['total_emails_discovered']} emails discovered")
        self.logger.info(f"   👤 {results['summary']['total_usernames_found']} usernames found")
        self.logger.info(f"   📍 {results['summary']['total_locations_found']} locations found")
        self.logger.info(f"   🏢 {results['summary']['total_companies_found']} companies found")

        return results