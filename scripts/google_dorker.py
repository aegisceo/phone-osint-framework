#!/usr/bin/env python3
import os
import time
import json
from googlesearch import search
from urllib.parse import quote
import logging

class GoogleDorker:
    def __init__(self, phone_number, phone_data, enriched_identity=None):
        self.phone = phone_number
        self.phone_data = phone_data
        self.enriched_identity = enriched_identity or {}
        self.logger = logging.getLogger(__name__)
        
    def build_dorks(self):
        """
        Build intelligent Google dorks using ALL enriched identity data
        Leverages names, emails, usernames, companies, and locations for comprehensive searches
        """
        dorks = []
        
        # Extract all available identity data
        primary_name = self.enriched_identity.get('primary_names', [None])[0]
        primary_email = self.enriched_identity.get('known_email')
        all_emails = self.enriched_identity.get('emails', [])
        usernames = self.enriched_identity.get('usernames', [])
        companies = self.enriched_identity.get('companies', [])
        locations = self.enriched_identity.get('locations', [])

        # Log what we're working with
        enrichment_summary = []
        if primary_name: enrichment_summary.append(f"name: {primary_name}")
        if primary_email: enrichment_summary.append(f"email: {primary_email}")
        if usernames: enrichment_summary.append(f"{len(usernames)} usernames")
        if companies: enrichment_summary.append(f"{len(companies)} companies")
        if locations: enrichment_summary.append(f"{len(locations)} locations")
        
        if enrichment_summary:
            self.logger.info(f"🎯 Google dorking with enriched data: {', '.join(enrichment_summary)}")
        else:
            self.logger.warning("⚠️ No enriched data available - using phone-only searches")

        # PRIORITY 1: Name + Email + Additional Context (HIGHEST VALUE)
        if primary_name and primary_email:
            dorks.extend([
                f'"{primary_name}" "{primary_email}"',
                f'"{primary_name}" site:linkedin.com',
                f'"{primary_email}" site:github.com',
            ])

        # PRIORITY 2: Name + Username combinations
        elif primary_name and usernames:
            username = usernames[0].get('username', '') if isinstance(usernames[0], dict) else str(usernames[0])
            dorks.extend([
                f'"{primary_name}" "{username}" site:github.com',
                f'"{primary_name}" site:linkedin.com',
                f'"{username}" "{primary_name}"',
            ])

        # PRIORITY 3: Name + Company combinations
        elif primary_name and companies:
            company = str(companies[0])
            dorks.extend([
                f'"{primary_name}" "{company}" site:linkedin.com',
                f'"{primary_name}" site:linkedin.com',
                f'"{primary_name}" "{self.phone}"',
            ])

        # PRIORITY 4: Name-only searches with location context
        elif primary_name:
            if locations:
                location = locations[0].get('location', '') if isinstance(locations[0], dict) else str(locations[0])
                dorks.extend([
                    f'"{primary_name}" "{location}" site:linkedin.com',
                    f'"{primary_name}" site:linkedin.com',
                ])
            else:
                dorks.extend([
                    f'"{primary_name}" "{self.phone}"',
                    f'"{primary_name}" site:linkedin.com',
                ])

        # PRIORITY 5: Username-based searches (if no name but have social media presence)
        elif usernames:
            for username_data in usernames[:2]:  # Top 2 usernames
                username = username_data.get('username', '') if isinstance(username_data, dict) else str(username_data)
                if username:
                    dorks.append(f'"{username}" "{self.phone}"')
                    dorks.append(f'"{username}" site:github.com')
                    dorks.append(f'"{username}" site:linkedin.com')

        # PRIORITY 6: Email-only searches
        elif primary_email:
            dorks.extend([
                f'"{primary_email}" "{self.phone}"',
                f'"{primary_email}" site:linkedin.com',
            ])

        # FALLBACK: Phone-only searches
        if not dorks:
            self.logger.warning(f"⚠️ No enriched data - using phone-only searches")
            dorks.extend([
                f'"{self.phone}"',
                f'"{self.phone}" site:linkedin.com',
                f'"{self.phone}" filetype:pdf',
            ])

        # Limit total dorks to manage API quotas
        dorks = dorks[:6]  # Increased from 5 to 6 for enriched searches
        self.logger.info(f"📊 Built {len(dorks)} enriched Google dorks")

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
                urls = list(search(dork, num=10, stop=10, pause=2))
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