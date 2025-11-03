#!/usr/bin/env python3
"""
TruePeopleSearch Scraper
Free people search with phone numbers, addresses, and associates
Handles CAPTCHA challenges using undetected-chromedriver
"""

import re
import time
import logging
from typing import Dict, List, Optional
from pathlib import Path

class TruePeopleSearchScraper:
    """
    Scraper for TruePeopleSearch.com - free people search
    
    Features:
    - Phone number lookup
    - Address history
    - Associated people/relatives
    - Age/DOB information
    - CAPTCHA handling with undetected-chromedriver
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://www.truepeoplesearch.com"
        
    def check_dependencies(self) -> Dict:
        """Check if required dependencies are installed"""
        dependencies = {
            'selenium': False,
            'undetected_chromedriver': False,
            'ready': False
        }
        
        try:
            import selenium
            dependencies['selenium'] = True
        except ImportError:
            self.logger.warning("Selenium not installed: pip install selenium")
        
        try:
            import undetected_chromedriver
            dependencies['undetected_chromedriver'] = True
        except ImportError:
            self.logger.warning("Undetected-chromedriver not installed: pip install undetected-chromedriver")
        
        dependencies['ready'] = all([dependencies['selenium'], dependencies['undetected_chromedriver']])
        return dependencies
    
    def search_by_phone(self, phone_number: str) -> Dict:
        """
        Search TruePeopleSearch by phone number
        
        Args:
            phone_number: Phone number to search (various formats accepted)
            
        Returns:
            Dict containing:
            - found: Boolean indicating if results were found
            - name: Primary name associated with phone
            - addresses: List of current and previous addresses
            - associates: List of associated people/relatives
            - age: Estimated age
            - additional_phones: Other phone numbers associated
            - error: Error message if search failed
        """
        
        results = {
            'found': False,
            'name': None,
            'names': [],  # For unified_name_hunter compatibility
            'addresses': [],
            'current_address': None,
            'previous_addresses': [],
            'associates': [],
            'relatives': [],  # Alias for associates
            'age': None,
            'additional_phones': [],
            'source': 'truepeoplesearch.com'
        }
        
        # Check dependencies
        deps = self.check_dependencies()
        if not deps['ready']:
            results['error'] = 'Missing dependencies - install selenium and undetected-chromedriver'
            self.logger.error(results['error'])
            return results
        
        # Clean phone number
        clean_phone = re.sub(r'[^\d]', '', phone_number)
        if len(clean_phone) == 11 and clean_phone.startswith('1'):
            clean_phone = clean_phone[1:]
        
        if len(clean_phone) != 10:
            results['error'] = f'Invalid phone number format: {phone_number}'
            self.logger.error(results['error'])
            return results
        
        # Format for URL: 123-456-7890
        formatted_phone = f"{clean_phone[:3]}-{clean_phone[3:6]}-{clean_phone[6:]}"
        search_url = f"{self.base_url}/results?phoneno={formatted_phone}"
        
        self.logger.info(f"🔍 Searching TruePeopleSearch for: {formatted_phone}")
        
        driver = None
        try:
            # Import here to avoid errors if not installed
            import undetected_chromedriver as uc
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Initialize undetected Chrome (bypasses most anti-bot measures)
            options = uc.ChromeOptions()
            options.headless = False  # Keep visible to handle manual CAPTCHA if needed
            
            # Add robust stealth and stability options
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            self.logger.info("🚀 Launching undetected Chrome browser...")
            
            # Try to initialize driver with version handling
            try:
                driver = uc.Chrome(options=options, use_subprocess=False)
            except Exception as driver_error:
                # Handle version mismatch specifically
                error_msg = str(driver_error)
                if 'version' in error_msg.lower() or 'chrome' in error_msg.lower():
                    self.logger.error("❌ ChromeDriver version mismatch detected")
                    self.logger.error("🔧 Fix: Update Chrome browser to latest version")
                    self.logger.error("   Method 1: Navigate to chrome://settings/help in Chrome")
                    self.logger.error("   Method 2: Undetected-chromedriver will auto-download correct version on next run")
                    results['error'] = f'ChromeDriver version mismatch - update Chrome browser'
                    return results
                else:
                    # Other error - re-raise
                    raise driver_error
            
            # Wrap all scraping in try/finally for robust cleanup
            try:
                # Navigate to search URL
                driver.get(search_url)
                self.logger.info(f"📄 Loaded: {search_url}")
                
                # Wait for page load
                time.sleep(3)
                
                # Check for CAPTCHA
                if self._detect_captcha(driver):
                    self.logger.warning("🛡️ CAPTCHA detected - waiting for manual solve...")
                    self.logger.info("💡 Please solve the CAPTCHA in the browser window...")
                    
                    # Wait up to 60 seconds for CAPTCHA resolution
                    captcha_solved = self._wait_for_captcha_solve(driver, timeout=60)
                    
                    if not captcha_solved:
                        results['error'] = 'CAPTCHA not solved within timeout'
                        self.logger.error(results['error'])
                        return results
                    
                    self.logger.info("✅ CAPTCHA solved - continuing...")
                
                # Wait for results to load
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "card"))
                    )
                except:
                    self.logger.warning("No results card found - may be no matches")
                    results['error'] = 'No results found for this phone number'
                    return results
                
                # Extract data from page
                page_source = driver.page_source
                
                # Extract name
                name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', page_source)
                if name_match:
                    results['name'] = name_match.group(1).strip()
                    results['names'] = [results['name']]  # List format for unified_name_hunter
                    results['found'] = True
                    self.logger.info(f"✅ Name found: {results['name']}")
                
                # Extract age
                age_match = re.search(r'Age:\s*(\d+)', page_source, re.IGNORECASE)
                if age_match:
                    results['age'] = int(age_match.group(1))
                    self.logger.info(f"📅 Age: {results['age']}")
                
                # Extract addresses
                address_matches = re.findall(
                    r'<div[^>]*class="[^"]*address[^"]*"[^>]*>([^<]+(?:<[^>]+>[^<]*</[^>]+>[^<]*)*)</div>',
                    page_source,
                    re.IGNORECASE
                )
                
                for addr in address_matches:
                    # Clean HTML tags
                    clean_addr = re.sub(r'<[^>]+>', ' ', addr)
                    clean_addr = re.sub(r'\s+', ' ', clean_addr).strip()
                    if clean_addr and len(clean_addr) > 10:
                        addr_type = 'current' if 'current' in addr.lower() else 'previous'
                        results['addresses'].append({
                            'address': clean_addr,
                            'type': addr_type
                        })
                        
                        # Populate current/previous address fields for unified_name_hunter
                        if addr_type == 'current' and not results['current_address']:
                            results['current_address'] = clean_addr
                        elif addr_type == 'previous':
                            results['previous_addresses'].append(clean_addr)
                
                if results['addresses']:
                    self.logger.info(f"🏠 Addresses found: {len(results['addresses'])}")
                
                # Extract associates/relatives
                associate_matches = re.findall(
                    r'<a[^>]*>([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)</a>',
                    page_source
                )
                
                # Filter and deduplicate associates
                seen_associates = set()
                for associate in associate_matches:
                    cleaned = associate.strip()
                    if (cleaned and 
                        cleaned != results['name'] and
                        cleaned not in seen_associates and
                        len(cleaned.split()) >= 2):  # At least first and last name
                        results['associates'].append(cleaned)
                        seen_associates.add(cleaned)
                
                # Populate relatives field (alias for unified_name_hunter)
                results['relatives'] = results['associates'].copy()
                
                if results['associates']:
                    self.logger.info(f"👥 Associates/Relatives found: {len(results['associates'])}")
                
                # Extract additional phone numbers
                phone_matches = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', page_source)
                for phone in phone_matches:
                    clean = re.sub(r'[^\d]', '', phone)
                    if clean != clean_phone and clean not in results['additional_phones']:
                        formatted = f"{clean[:3]}-{clean[3:6]}-{clean[6:]}"
                        results['additional_phones'].append(formatted)
                
                if results['additional_phones']:
                    self.logger.info(f"📞 Additional phones: {len(results['additional_phones'])}")
            
            except Exception as e:
                self.logger.error(f"❌ TruePeopleSearch scraping error: {e}")
                results['error'] = str(e)
                
            finally:
                # Always cleanup driver, suppress cleanup errors
                if driver:
                    try:
                        driver.quit()
                        self.logger.info("🔒 Browser closed")
                    except Exception as cleanup_error:
                        # Suppress cleanup errors (common on Windows with handle issues)
                        self.logger.debug(f"Driver cleanup error (ignored): {cleanup_error}")
        
        except Exception as outer_error:
            # Catch any errors from imports or driver initialization
            self.logger.error(f"❌ TruePeopleSearch error: {outer_error}")
            results['error'] = str(outer_error)
        
        return results
    
    def _detect_captcha(self, driver) -> bool:
        """Detect if CAPTCHA is present on the page"""
        try:
            page_source = driver.page_source.lower()
            
            # Common CAPTCHA indicators
            captcha_indicators = [
                'recaptcha',
                'captcha',
                'cf-challenge',
                'cloudflare',
                'please verify you are human'
            ]
            
            return any(indicator in page_source for indicator in captcha_indicators)
        except:
            return False
    
    def _wait_for_captcha_solve(self, driver, timeout: int = 60) -> bool:
        """
        Wait for CAPTCHA to be solved (manual or automated)
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Maximum seconds to wait
            
        Returns:
            True if CAPTCHA was solved, False if timeout
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if not self._detect_captcha(driver):
                return True
            
            time.sleep(2)  # Check every 2 seconds
        
        return False

# Factory function for easy integration
def search_truepeoplesearch(phone_number: str) -> Dict:
    """
    Search TruePeopleSearch for phone number information
    
    Args:
        phone_number: Phone number to search
        
    Returns:
        Dict with search results
    """
    scraper = TruePeopleSearchScraper()
    return scraper.search_by_phone(phone_number)

if __name__ == "__main__":
    # Test the scraper
    import sys
    
    if len(sys.argv) > 1:
        phone = sys.argv[1]
    else:
        phone = input("Enter phone number to search: ")
    
    results = search_truepeoplesearch(phone)
    
    print("\nTruePeopleSearch Results:")
    print("="*60)
    
    if results.get('found'):
        print(f"✅ Name: {results.get('name')}")
        print(f"📅 Age: {results.get('age', 'Unknown')}")
        
        if results.get('addresses'):
            print(f"\n🏠 Addresses ({len(results['addresses'])}):")
            for addr in results['addresses']:
                print(f"   [{addr['type']}] {addr['address']}")
        
        if results.get('associates'):
            print(f"\n👥 Associates ({len(results['associates'])}):")
            for associate in results['associates'][:5]:
                print(f"   - {associate}")
            if len(results['associates']) > 5:
                print(f"   ...and {len(results['associates']) - 5} more")
        
        if results.get('additional_phones'):
            print(f"\n📞 Additional Phones:")
            for phone in results['additional_phones']:
                print(f"   - {phone}")
    else:
        print(f"❌ No results found")
        if results.get('error'):
            print(f"Error: {results['error']}")
