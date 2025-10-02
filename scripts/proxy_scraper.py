#!/usr/bin/env python3
"""
Free Proxy Scraper
Collects and validates free proxies from public sources
WARNING: Free proxies are unreliable - use for testing only
"""
import requests
import logging
import time
from bs4 import BeautifulSoup
from typing import List, Dict
import concurrent.futures

class ProxyScraper:
    """Scrapes and validates free proxies from public sources"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_free_proxy_list(self) -> List[str]:
        """Scrape from free-proxy-list.net"""
        proxies = []

        try:
            url = 'https://free-proxy-list.net/'
            self.logger.info(f"Scraping proxies from {url}")

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table', id='list')

                if table:
                    rows = table.find_all('tr')[1:]  # Skip header

                    for row in rows[:50]:  # Limit to first 50
                        cols = row.find_all('td')
                        if len(cols) >= 7:
                            ip = cols[0].text.strip()
                            port = cols[1].text.strip()
                            https = cols[6].text.strip()

                            # Prefer HTTPS proxies
                            if https == 'yes':
                                proxies.append(f"{ip}:{port}")

                    self.logger.info(f"Found {len(proxies)} HTTPS proxies")

        except Exception as e:
            self.logger.error(f"Error scraping free-proxy-list.net: {e}")

        return proxies

    def scrape_proxy_scrape(self) -> List[str]:
        """Scrape from proxyscrape.com API"""
        proxies = []

        try:
            url = 'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all'
            self.logger.info(f"Fetching proxies from proxyscrape.com")

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                proxy_list = response.text.strip().split('\n')
                proxies = [p.strip() for p in proxy_list if p.strip()]
                self.logger.info(f"Found {len(proxies)} proxies from proxyscrape")

        except Exception as e:
            self.logger.error(f"Error scraping proxyscrape.com: {e}")

        return proxies

    def validate_proxy(self, proxy: str, timeout: int = 5) -> bool:
        """Test if a proxy works"""
        test_url = 'http://httpbin.org/ip'

        try:
            proxies_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }

            response = requests.get(
                test_url,
                proxies=proxies_dict,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            if response.status_code == 200:
                self.logger.debug(f"✓ Proxy working: {proxy}")
                return True

        except Exception as e:
            self.logger.debug(f"✗ Proxy failed: {proxy} - {type(e).__name__}")

        return False

    def validate_proxies(self, proxies: List[str], max_workers: int = 20) -> List[str]:
        """Validate proxies concurrently"""
        self.logger.info(f"Validating {len(proxies)} proxies...")

        working_proxies = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {executor.submit(self.validate_proxy, proxy): proxy for proxy in proxies}

            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        working_proxies.append(proxy)
                except Exception as e:
                    self.logger.debug(f"Validation error for {proxy}: {e}")

        self.logger.info(f"Found {len(working_proxies)} working proxies out of {len(proxies)}")
        return working_proxies

    def get_working_proxies(self, validate: bool = True) -> List[str]:
        """
        Main method: scrape and optionally validate proxies
        """
        all_proxies = []

        # Scrape from multiple sources
        all_proxies.extend(self.scrape_free_proxy_list())
        time.sleep(2)
        all_proxies.extend(self.scrape_proxy_scrape())

        # Remove duplicates
        unique_proxies = list(set(all_proxies))
        self.logger.info(f"Collected {len(unique_proxies)} unique proxies")

        # Validate if requested
        if validate:
            working_proxies = self.validate_proxies(unique_proxies)
            return working_proxies
        else:
            return unique_proxies


def main():
    """CLI for proxy scraping"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    scraper = ProxyScraper()
    proxies = scraper.get_working_proxies(validate=True)

    if proxies:
        # Save to file
        output_file = 'config/proxies.txt'

        with open(output_file, 'w') as f:
            for proxy in proxies:
                f.write(proxy + '\n')

        print(f"\n✓ Saved {len(proxies)} working proxies to {output_file}")
        print("\nSample proxies:")
        for proxy in proxies[:5]:
            print(f"  - {proxy}")
    else:
        print("\n✗ No working proxies found")


if __name__ == '__main__':
    main()
