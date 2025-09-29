#!/usr/bin/env python3
import os
import time
import json
from googlesearch import search
from urllib.parse import quote
import logging

class GoogleDorker:
    def __init__(self, phone_number, phone_data):
        self.phone = phone_number
        self.phone_data = phone_data
        self.logger = logging.getLogger(__name__)
        
    def build_dorks(self):
        """Build targeted Google dorks"""
        dorks = [
            f'"{self.phone}"',
            f'"{self.phone}" site:linkedin.com',
            f'"{self.phone}" site:facebook.com',
            f'"{self.phone}" filetype:pdf',
            f'"{self.phone}" "contact"',
            f'"{self.phone}" "phone"',
            f'"{self.phone}" site:*.gov',
            f'"{self.phone}" site:court*',
        ]
        
        # Add carrier-specific searches
        if self.phone_data.get('carrier'):
            carrier = self.phone_data['carrier']
            dorks.extend([
                f'"{self.phone}" "{carrier}"',
                f'"{self.phone}" site:{carrier.lower().replace(" ", "")}.com'
            ])
        
        # Add location-specific searches
        if self.phone_data.get('location'):
            location = self.phone_data['location']
            dorks.extend([
                f'"{self.phone}" "{location}"',
                f'"{self.phone}" site:*.{location.lower()[:2]}'
            ])
            
        return dorks
    
    def search(self):
        """Execute all dorks and categorize results"""
        results = {
            'social_media': [],
            'documents': [],
            'business': [],
            'government': [],
            'other': []
        }
        
        dorks = self.build_dorks()
        
        for dork in dorks:
            self.logger.info(f"Searching: {dork}")
            try:
                urls = list(search(dork, num_results=10, sleep_interval=2))
                for url in urls:
                    self.categorize_result(url, results, dork)
                time.sleep(5)  # Rate limiting
            except Exception as e:
                self.logger.error(f"Search error: {e}")
                
        return results
    
    def categorize_result(self, url, results, dork):
        """Categorize URL into appropriate bucket"""
        url_lower = url.lower()
        
        if any(site in url_lower for site in ['facebook.', 'linkedin.', 'twitter.', 'instagram.']):
            if url not in results['social_media']:
                results['social_media'].append({
                    'url': url,
                    'dork': dork,
                    'timestamp': time.time()
                })
        elif '.pdf' in url_lower or 'document' in url_lower:
            results['documents'].append({
                'url': url,
                'dork': dork,
                'timestamp': time.time()
            })
        elif any(term in url_lower for term in ['business', 'company', 'corp', 'llc']):
            results['business'].append({
                'url': url,
                'dork': dork,
                'timestamp': time.time()
            })
        elif '.gov' in url_lower:
            results['government'].append({
                'url': url,
                'dork': dork,
                'timestamp': time.time()
            })
        else:
            results['other'].append({
                'url': url,
                'dork': dork,
                'timestamp': time.time()
            })