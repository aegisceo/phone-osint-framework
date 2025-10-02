#!/usr/bin/env python3
"""
Scraper Comparison Test
Compares Decodo Proxies vs Decodo API vs Direct Scraping for Yandex
"""
import os
import json
import time
import logging
from typing import Dict, List
from datetime import datetime
from pathlib import Path

class ScraperComparison:
    """
    A/B/C test framework for comparing scraping methods
    """

    def __init__(self, phone_number, enriched_identity=None):
        self.phone = phone_number
        self.enriched_identity = enriched_identity or {}
        self.logger = logging.getLogger(__name__)

        self.results = {
            'phone_number': phone_number,
            'timestamp': datetime.now().isoformat(),
            'methods': {}
        }

    def test_direct_scraping(self) -> Dict:
        """
        Test 1: Direct scraping with our yandex_scraper.py (no paid proxies)
        """
        self.logger.info("=" * 60)
        self.logger.info("TEST 1: Direct Scraping (No Proxies)")
        self.logger.info("=" * 60)

        start_time = time.time()

        try:
            from scripts.yandex_scraper import YandexScraper

            scraper = YandexScraper(
                phone_number=self.phone,
                enriched_identity=self.enriched_identity,
                proxy_list=[]  # No proxies
            )

            results = scraper.search()

            elapsed = time.time() - start_time

            # Count results
            total_results = sum(len(v) for v in results.values())

            return {
                'success': True,
                'method': 'direct_scraping',
                'elapsed_time': elapsed,
                'total_results': total_results,
                'russian_social': len(results.get('russian_social', [])),
                'social_media': len(results.get('social_media', [])),
                'forums': len(results.get('forums', [])),
                'documents': len(results.get('documents', [])),
                'cost_estimate': '$0 (free)',
                'results': results,
                'notes': 'High risk of blocking, CAPTCHAs'
            }

        except Exception as e:
            self.logger.error(f"Direct scraping failed: {e}")
            return {
                'success': False,
                'method': 'direct_scraping',
                'error': str(e),
                'elapsed_time': time.time() - start_time
            }

    def test_decodo_proxies(self) -> Dict:
        """
        Test 2: Scraping with Decodo Residential Proxies
        """
        self.logger.info("=" * 60)
        self.logger.info("TEST 2: Decodo Residential Proxies")
        self.logger.info("=" * 60)

        start_time = time.time()

        try:
            from scripts.yandex_scraper import YandexScraper
            from scripts.decodo_proxy_manager import DecodaProxyManager

            # Get Decodo proxies
            proxy_manager = DecodaProxyManager()
            proxies = proxy_manager.export_for_yandex()

            if not proxies:
                return {
                    'success': False,
                    'method': 'decodo_proxies',
                    'error': 'Decodo proxies not configured',
                    'elapsed_time': time.time() - start_time
                }

            self.logger.info(f"Using {len(proxies)} Decodo proxy sessions")

            scraper = YandexScraper(
                phone_number=self.phone,
                enriched_identity=self.enriched_identity,
                proxy_list=proxies
            )

            results = scraper.search()

            elapsed = time.time() - start_time
            total_results = sum(len(v) for v in results.values())

            return {
                'success': True,
                'method': 'decodo_proxies',
                'elapsed_time': elapsed,
                'total_results': total_results,
                'russian_social': len(results.get('russian_social', [])),
                'social_media': len(results.get('social_media', [])),
                'forums': len(results.get('forums', [])),
                'documents': len(results.get('documents', [])),
                'proxy_count': len(proxies),
                'cost_estimate': '~$0.01-0.05 (100MB trial)',
                'results': results,
                'notes': 'Manual anti-bot handling, proxy rotation'
            }

        except Exception as e:
            self.logger.error(f"Decodo proxy scraping failed: {e}")
            return {
                'success': False,
                'method': 'decodo_proxies',
                'error': str(e),
                'elapsed_time': time.time() - start_time
            }

    def test_decodo_api(self) -> Dict:
        """
        Test 3: Decodo Scraping API (fully managed)
        """
        self.logger.info("=" * 60)
        self.logger.info("TEST 3: Decodo Scraping API")
        self.logger.info("=" * 60)

        start_time = time.time()

        try:
            from scripts.decodo_api_scraper import DecodaAPIScraper

            scraper = DecodaAPIScraper(
                phone_number=self.phone,
                enriched_identity=self.enriched_identity
            )

            results = scraper.search()

            elapsed = time.time() - start_time
            total_results = sum(len(v) for k, v in results.items() if k != 'metadata')

            metadata = results.get('metadata', {})

            return {
                'success': True,
                'method': 'decodo_api',
                'elapsed_time': elapsed,
                'total_results': total_results,
                'russian_social': len(results.get('russian_social', [])),
                'social_media': len(results.get('social_media', [])),
                'forums': len(results.get('forums', [])),
                'documents': len(results.get('documents', [])),
                'api_requests': metadata.get('api_requests', 0),
                'successful_requests': metadata.get('successful_requests', 0),
                'failed_requests': metadata.get('failed_requests', 0),
                'cost_estimate': f"~${metadata.get('successful_requests', 0) * 0.05:.2f} (1000 req trial)",
                'results': results,
                'notes': 'Fully managed, automatic CAPTCHA/anti-bot handling'
            }

        except Exception as e:
            self.logger.error(f"Decodo API scraping failed: {e}")
            return {
                'success': False,
                'method': 'decodo_api',
                'error': str(e),
                'elapsed_time': time.time() - start_time
            }

    def run_comparison(self, methods: List[str] = None) -> Dict:
        """
        Run comparison tests

        Args:
            methods: List of methods to test
                     ['direct', 'proxies', 'api'] or None for all

        Returns:
            Comparison results dict
        """
        if methods is None:
            methods = ['direct', 'proxies', 'api']

        self.logger.info(f"\nStarting scraper comparison for: {self.phone}")
        self.logger.info(f"Testing methods: {', '.join(methods)}\n")

        # Test each method
        if 'direct' in methods:
            self.results['methods']['direct_scraping'] = self.test_direct_scraping()
            time.sleep(10)  # Pause between tests

        if 'proxies' in methods:
            self.results['methods']['decodo_proxies'] = self.test_decodo_proxies()
            time.sleep(10)

        if 'api' in methods:
            self.results['methods']['decodo_api'] = self.test_decodo_api()

        # Generate comparison report
        self._generate_comparison_report()

        return self.results

    def _generate_comparison_report(self):
        """Generate comparison summary"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("COMPARISON RESULTS")
        self.logger.info("=" * 60 + "\n")

        for method_name, result in self.results['methods'].items():
            self.logger.info(f"Method: {method_name.upper().replace('_', ' ')}")
            self.logger.info("-" * 40)

            if result.get('success'):
                self.logger.info(f"  Status: ✓ Success")
                self.logger.info(f"  Time: {result['elapsed_time']:.2f}s")
                self.logger.info(f"  Total Results: {result['total_results']}")
                self.logger.info(f"  Russian Social: {result.get('russian_social', 0)}")
                self.logger.info(f"  Social Media: {result.get('social_media', 0)}")
                self.logger.info(f"  Forums: {result.get('forums', 0)}")
                self.logger.info(f"  Documents: {result.get('documents', 0)}")
                self.logger.info(f"  Cost: {result.get('cost_estimate', 'N/A')}")
                self.logger.info(f"  Notes: {result.get('notes', '')}")
            else:
                self.logger.info(f"  Status: ✗ Failed")
                self.logger.info(f"  Error: {result.get('error', 'Unknown')}")

            self.logger.info()

        # Winner determination
        successful = {k: v for k, v in self.results['methods'].items() if v.get('success')}

        if successful:
            # Best by total results
            best_results = max(successful.items(), key=lambda x: x[1].get('total_results', 0))
            self.logger.info(f"🏆 Most Results: {best_results[0]} ({best_results[1]['total_results']} results)")

            # Best by speed
            best_speed = min(successful.items(), key=lambda x: x[1].get('elapsed_time', float('inf')))
            self.logger.info(f"⚡ Fastest: {best_speed[0]} ({best_speed[1]['elapsed_time']:.2f}s)")

            # Best value (results per dollar estimate)
            for name, data in successful.items():
                cost_str = data.get('cost_estimate', '$0').replace('~', '').replace('$', '').split()[0]
                try:
                    cost = float(cost_str)
                    if cost > 0:
                        data['value_score'] = data['total_results'] / cost
                    else:
                        data['value_score'] = data['total_results'] * 1000  # Free gets high score
                except:
                    data['value_score'] = 0

            best_value = max(successful.items(), key=lambda x: x[1].get('value_score', 0))
            self.logger.info(f"💰 Best Value: {best_value[0]}")

        self.logger.info("\n" + "=" * 60 + "\n")

    def save_results(self, output_dir: str = 'results/comparisons'):
        """Save comparison results to file"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/comparison_{self.phone}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)

        self.logger.info(f"Results saved to: {filename}")
        return filename


if __name__ == '__main__':
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage: python scraper_comparison.py <phone_number> [methods]")
        print("  phone_number: Phone number to investigate")
        print("  methods: Comma-separated list (direct,proxies,api) or 'all'")
        print()
        print("Example:")
        print("  python scraper_comparison.py +13053932786")
        print("  python scraper_comparison.py +13053932786 proxies,api")
        sys.exit(1)

    phone = sys.argv[1]

    # Parse methods
    if len(sys.argv) > 2 and sys.argv[2] != 'all':
        methods = sys.argv[2].split(',')
    else:
        methods = ['direct', 'proxies', 'api']

    # Run comparison
    comparison = ScraperComparison(phone)
    results = comparison.run_comparison(methods=methods)

    # Save results
    output_file = comparison.save_results()

    print(f"\n✓ Comparison complete!")
    print(f"Results saved to: {output_file}")
