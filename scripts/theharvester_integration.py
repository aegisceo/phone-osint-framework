#!/usr/bin/env python3
"""
theHarvester Integration for Advanced Email Discovery
Much more effective than Google Custom Search for finding actual emails
"""

import os
import json
import subprocess
import logging
import time
from typing import Dict, List
from pathlib import Path

class TheHarvesterIntegration:
    """
    Integration wrapper for theHarvester email discovery tool
    Specialized for finding actual email addresses vs pattern generation
    """

    def __init__(self, target_domain: str = None, target_name: str = None):
        self.target_domain = target_domain
        self.target_name = target_name
        self.logger = logging.getLogger(__name__)
        
    def check_theharvester_available(self) -> bool:
        """Check if theHarvester is installed and available"""
        try:
            # Check if theHarvester exists in framework directory
            harvester_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'theHarvester', 'theHarvester.py')
            if os.path.exists(harvester_path):
                result = subprocess.run(['python', harvester_path, '-h'], capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            
            # Check system theharvester command
            result = subprocess.run(['theharvester', '-h'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def harvest_domain_emails(self, domain: str, output_dir: Path) -> Dict:
        """Harvest emails from a specific domain using theHarvester"""
        
        if not self.check_theharvester_available():
            return {
                'found': False,
                'error': 'theHarvester not installed',
                'install_instructions': 'pip install theHarvester or clone from https://github.com/laramies/theHarvester'
            }
        
        self.logger.info(f"🔍 Running theHarvester for domain: {domain}")
        
        # Create harvester output directory
        harvester_dir = output_dir / "theharvester_results"
        harvester_dir.mkdir(exist_ok=True)
        
        output_file = harvester_dir / f"{domain.replace('.', '_')}_harvest.json"
        
        # Build theHarvester command - use the installed version in our directory  
        harvester_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'theHarvester', 'theHarvester.py')
        
        cmd = [
            'python', harvester_path,
            '-d', domain,
            '-l', '50',            # Limit results
            '-b', 'duckduckgo',    # Use supported engine
            '-f', str(output_file) # JSON output
        ]
        
        try:
            self.logger.info(f"🎨 theHarvester scan starting (live output below)...")
            self.logger.info("=" * 70)
            
            result = subprocess.run(
                cmd,
                capture_output=False,  # Show colorful output in terminal!
                timeout=90  # 1.5 minute timeout
            )
            
            self.logger.info("=" * 70)
            
            if result.returncode == 0:
                # Parse theHarvester output
                emails_found = []
                
                # theHarvester creates XML and HTML files, need to parse
                if output_file.exists():
                    with open(output_file, 'r') as f:
                        harvest_data = json.load(f)
                    
                    # Extract emails from theHarvester results
                    if 'emails' in harvest_data:
                        emails_found = harvest_data['emails']
                    
                self.logger.info(f"✅ theHarvester found {len(emails_found)} emails for {domain}")
                return {
                    'found': len(emails_found) > 0,
                    'domain': domain,
                    'emails': emails_found,
                    'method': 'theHarvester'
                }
            else:
                self.logger.warning(f"theHarvester failed for {domain} (check output above)")
                return {'found': False, 'error': 'theHarvester failed - see output above'}
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"theHarvester scan timed out for {domain}")
            return {'found': False, 'error': 'Scan timed out'}
        except Exception as e:
            self.logger.error(f"theHarvester error for {domain}: {e}")
            return {'found': False, 'error': str(e)}

    def harvest_name_based_emails(self, name: str, output_dir: Path) -> Dict:
        """Use theHarvester to search for emails associated with a person's name"""
        
        if not self.check_theharvester_available():
            return {
                'found': False,
                'error': 'theHarvester not installed'
            }
        
        # For name-based searches, we'll search common domains where people have emails
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        all_results = {
            'found': False,
            'emails': [],
            'domains_searched': [],
            'method': 'theHarvester_name_search'
        }
        
        # Since theHarvester works on domains, we'll search each major email provider
        # This is more effective than Google Custom Search for actual email discovery
        for domain in personal_domains:
            try:
                self.logger.info(f"🔍 Searching {domain} for emails related to {name}")
                
                # Build search query combining name + domain
                # theHarvester will search for emails in this domain
                domain_results = self.harvest_domain_emails(domain, output_dir)
                
                if domain_results.get('found'):
                    domain_emails = domain_results.get('emails', [])
                    all_results['domains_searched'].append(domain)
                    
                    # Filter emails that might belong to our target
                    for email in domain_emails:
                        if self._email_matches_name(email, name):
                            all_results['emails'].append({
                                'email': email,
                                'confidence': 0.8,  # High confidence - found by theHarvester
                                'source': 'theHarvester',
                                'domain': domain
                            })
                
                # Rate limiting between domain searches
                time.sleep(5)
                
            except Exception as e:
                self.logger.warning(f"theHarvester search failed for {domain}: {e}")
                continue
        
        all_results['found'] = len(all_results['emails']) > 0
        return all_results

    def _email_matches_name(self, email: str, target_name: str) -> bool:
        """Check if email might belong to the target name"""
        if not email or not target_name:
            return False
            
        email_lower = email.lower()
        name_parts = target_name.lower().split()
        
        # Check if any name part appears in the email username
        for part in name_parts:
            if len(part) > 2 and part in email_lower:
                return True
                
        return False

# Integration functions for main framework
def enhance_email_discovery_with_sherlock(target_name: str, output_dir: Path) -> Dict:
    """
    Enhance email discovery using Sherlock username enumeration
    Returns usernames that can be used for email pattern generation
    """
    from .sherlock_integration import run_sherlock_username_hunt
    
    sherlock_results = run_sherlock_username_hunt(target_name, output_dir)
    
    # Extract usernames for email generation
    discovered_usernames = []
    if sherlock_results.get('found'):
        for username in sherlock_results.get('successful_usernames', []):
            discovered_usernames.append({
                'username': username,
                'source': 'sherlock',
                'platforms': len(sherlock_results['scan_summary'].get(username, {}).get('profiles_found', []))
            })
    
    return {
        'found': len(discovered_usernames) > 0,
        'usernames': discovered_usernames,
        'total_profiles': len(sherlock_results.get('all_profiles_found', [])),
        'method': 'sherlock_enhancement'
    }

def enhance_email_discovery_with_theharvester(target_name: str, output_dir: Path) -> Dict:
    """
    Use theHarvester to find actual emails (better than Google Custom Search for email discovery)
    """
    harvester = TheHarvesterIntegration(target_name=target_name)
    return harvester.harvest_name_based_emails(target_name, output_dir)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python theharvester_integration.py 'Full Name'")
        sys.exit(1)
        
    target = sys.argv[1]
    output = Path("./harvester_test_output")
    output.mkdir(exist_ok=True)
    
    results = enhance_email_discovery_with_theharvester(target, output)
    print(f"\ntheHarvester Results: {json.dumps(results, indent=2)}")
