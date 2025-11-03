#!/usr/bin/env python3
"""
Maigret Integration for Username Enumeration
Searches for usernames across 2500+ websites
Complements Sherlock with broader coverage and enhanced features
"""

import os
import json
import subprocess
import logging
from typing import Dict, List, Optional
from pathlib import Path
import tempfile

class MaigretIntegration:
    """
    Wrapper for Maigret - comprehensive username search across 2500+ sites
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.maigret_path = self._find_maigret()
        
    def _find_maigret(self) -> Optional[str]:
        """Find Maigret installation"""
        possible_paths = [
            # Installed via pip
            'maigret',
            # Local installation
            './tools/maigret/maigret.py',
            '../maigret/maigret.py',
            # Framework directory
            Path(__file__).parent.parent / 'tools' / 'maigret' / 'maigret.py',
        ]
        
        for path in possible_paths:
            try:
                # Test if maigret is available
                result = subprocess.run(
                    [str(path) if not str(path).endswith('.py') else 'python', str(path), '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 or 'maigret' in result.stdout.lower() or 'maigret' in result.stderr.lower():
                    self.logger.info(f"✅ Maigret found: {path}")
                    return str(path)
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
        
        self.logger.warning("⚠️ Maigret not found - install with: pip install maigret")
        return None
    
    def check_maigret_available(self) -> bool:
        """Check if Maigret is available"""
        return self.maigret_path is not None
    
    def search_username(self, username: str, timeout: int = 300) -> Dict:
        """
        Search for username across 2500+ sites using Maigret
        
        Args:
            username: Username to search for
            timeout: Maximum execution time in seconds (default 5 minutes)
            
        Returns:
            Dict with discovered profiles and metadata
        """
        
        results = {
            'username': username,
            'found': False,
            'profiles': [],
            'total_sites_checked': 0,
            'sites_found': 0,
            'tool': 'maigret',
            'error': None
        }
        
        if not self.maigret_path:
            results['error'] = 'Maigret not installed'
            self.logger.error("❌ Maigret not available")
            return results
        
        self.logger.info(f"🔍 Maigret searching for username: {username}")
        self.logger.info(f"⏱️ Timeout: {timeout} seconds (searching 2500+ sites)")
        
        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / f"maigret_{username}.json"
            
            try:
                # Build Maigret command
                cmd = [
                    'python' if self.maigret_path.endswith('.py') else self.maigret_path,
                ]
                
                if self.maigret_path.endswith('.py'):
                    cmd.append(self.maigret_path)
                
                cmd.extend([
                    username,
                    '--json', str(output_file),
                    '--timeout', '10',  # Per-site timeout
                    # Progress bar enabled for cool visual output!
                ])
                
                # Run Maigret with live colorful output
                self.logger.info(f"🎨 Maigret scan starting (2500+ sites - live output below)...")
                self.logger.info("=" * 70)
                
                result = subprocess.run(
                    cmd,
                    capture_output=False,  # Show colorful progress bars and output!
                    timeout=timeout,
                    cwd=os.getcwd()
                )
                
                self.logger.info("=" * 70)
                
                # Parse results
                if output_file.exists():
                    with open(output_file, 'r', encoding='utf-8') as f:
                        maigret_data = json.load(f)
                    
                    # Extract profile information
                    if username in maigret_data:
                        user_results = maigret_data[username]
                        
                        for site_name, site_data in user_results.items():
                            if isinstance(site_data, dict) and site_data.get('status') == 'found':
                                profile = {
                                    'site': site_name,
                                    'url': site_data.get('url', ''),
                                    'url_user': site_data.get('url_user', ''),
                                    'username': username,
                                    'status': 'found',
                                    'http_status': site_data.get('http_status'),
                                    'response_time': site_data.get('check_time_ms'),
                                    'extracted_data': site_data.get('ids', {})
                                }
                                results['profiles'].append(profile)
                        
                        results['sites_found'] = len(results['profiles'])
                        results['total_sites_checked'] = len(user_results)
                        results['found'] = results['sites_found'] > 0
                        
                        self.logger.info(f"✅ Maigret found username '{username}' on {results['sites_found']} sites!")
                        self.logger.info(f"📊 Checked {results['total_sites_checked']} sites total")
                        
                        # Log top sites found
                        if results['profiles']:
                            top_sites = [p['site'] for p in results['profiles'][:10]]
                            self.logger.info(f"🎯 Top sites: {', '.join(top_sites)}")
                    
                    else:
                        self.logger.warning(f"⚠️ No data for username '{username}' in Maigret results")
                        results['error'] = 'No data in results'
                
                else:
                    self.logger.error(f"❌ Maigret output file not created: {output_file}")
                    results['error'] = 'Output file not created'
                    
                    # Check stderr for errors
                    if result.stderr:
                        self.logger.debug(f"Maigret stderr: {result.stderr[:500]}")
                
            except subprocess.TimeoutExpired:
                self.logger.warning(f"⏱️ Maigret search timed out after {timeout} seconds")
                results['error'] = f'Timeout after {timeout} seconds'
            
            except Exception as e:
                self.logger.error(f"❌ Maigret search error: {e}")
                results['error'] = str(e)
        
        return results
    
    def search_multiple_usernames(self, usernames: List[str], timeout: int = 300) -> Dict:
        """
        Search for multiple usernames
        
        Args:
            usernames: List of usernames to search
            timeout: Timeout per username search
            
        Returns:
            Dict with results for all usernames
        """
        
        all_results = {
            'total_usernames': len(usernames),
            'successful_searches': 0,
            'failed_searches': 0,
            'total_profiles_found': 0,
            'results': []
        }
        
        for username in usernames:
            result = self.search_username(username, timeout=timeout)
            all_results['results'].append(result)
            
            if result['found']:
                all_results['successful_searches'] += 1
                all_results['total_profiles_found'] += result['sites_found']
            else:
                all_results['failed_searches'] += 1
        
        return all_results


# Integration functions for easy use

def search_maigret_username(username: str) -> Dict:
    """
    Search for a username using Maigret
    
    Args:
        username: Username to search for
        
    Returns:
        Dict with discovered profiles
    """
    maigret = MaigretIntegration()
    
    if not maigret.check_maigret_available():
        return {
            'found': False,
            'error': 'Maigret not installed - pip install maigret',
            'profiles': []
        }
    
    return maigret.search_username(username)


def enhance_username_discovery_with_maigret(discovered_usernames: List[str]) -> Dict:
    """
    Enhance username discovery by searching all discovered usernames with Maigret
    
    Args:
        discovered_usernames: List of usernames discovered during investigation
        
    Returns:
        Comprehensive results across all usernames
    """
    
    if not discovered_usernames:
        return {
            'found': False,
            'note': 'No usernames provided',
            'profiles': []
        }
    
    maigret = MaigretIntegration()
    
    if not maigret.check_maigret_available():
        return {
            'found': False,
            'error': 'Maigret not installed',
            'profiles': [],
            'install_command': 'pip install maigret'
        }
    
    # Search all usernames
    logger = logging.getLogger(__name__)
    logger.info(f"🔍 Maigret searching {len(discovered_usernames)} discovered usernames...")
    
    results = maigret.search_multiple_usernames(discovered_usernames, timeout=180)
    
    logger.info(f"✅ Maigret complete: {results['total_profiles_found']} total profiles found across {results['successful_searches']} usernames")
    
    return results


def get_maigret_status() -> Dict:
    """Get Maigret installation status and info"""
    maigret = MaigretIntegration()
    
    return {
        'available': maigret.check_maigret_available(),
        'path': maigret.maigret_path,
        'install_command': 'pip install maigret',
        'capabilities': {
            'sites_supported': '2500+',
            'features': [
                'Username enumeration across 2500+ sites',
                'Broader coverage than Sherlock',
                'Enhanced data extraction',
                'Multiple username search',
                'JSON output for automation'
            ]
        },
        'vs_sherlock': {
            'sherlock': '400+ sites',
            'maigret': '2500+ sites (6x more coverage)',
            'recommendation': 'Use both for comprehensive coverage'
        }
    }


if __name__ == "__main__":
    # Test Maigret integration
    import sys
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input("Enter username to search: ")
    
    print("\n" + "="*60)
    print(f"Maigret Username Search: {username}")
    print("="*60 + "\n")
    
    # Check status
    status = get_maigret_status()
    if not status['available']:
        print("❌ Maigret not installed!")
        print(f"Install with: {status['install_command']}\n")
        exit(1)
    
    # Search
    results = search_maigret_username(username)
    
    if results['found']:
        print(f"✅ Username '{username}' found on {results['sites_found']} sites!")
        print(f"📊 Total sites checked: {results['total_sites_checked']}\n")
        
        print("🎯 Discovered Profiles:")
        print("-" * 60)
        
        for profile in results['profiles'][:20]:  # Show first 20
            print(f"  • {profile['site']}: {profile['url']}")
        
        if len(results['profiles']) > 20:
            print(f"\n  ...and {len(results['profiles']) - 20} more profiles\n")
    
    else:
        print(f"❌ Username '{username}' not found")
        if results.get('error'):
            print(f"Error: {results['error']}")

