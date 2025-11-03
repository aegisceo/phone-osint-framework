#!/usr/bin/env python3
"""
Sherlock Integration for Username Enumeration
Finds usernames across 400+ social media platforms for enhanced email discovery
"""

import os
import json
import subprocess
import logging
import time
from typing import Dict, List
from pathlib import Path

class SherlockIntegration:
    """
    Integration wrapper for Sherlock username enumeration tool
    """

    def __init__(self, target_name: str):
        self.target_name = target_name
        self.logger = logging.getLogger(__name__)
        
        # Generate potential usernames from full name
        self.usernames_to_check = self._generate_username_patterns(target_name)
        
    def _generate_username_patterns(self, full_name: str) -> List[str]:
        """Generate potential usernames from full name"""
        if not full_name:
            return []
            
        # Parse name
        parts = full_name.lower().strip().split()
        if len(parts) < 2:
            return [parts[0]] if parts else []
            
        first = parts[0]
        last = parts[-1]  # Handle middle names
        
        # Common username patterns
        patterns = [
            f"{first}{last}",           # johndoe
            f"{first}.{last}",          # john.doe  
            f"{first}_{last}",          # john_doe
            f"{first}{last[0]}",        # johnd
            f"{first[0]}{last}",        # jdoe
            f"{first}-{last}",          # john-doe
            f"{last}{first}",           # doejohn (less common)
        ]
        
        return patterns[:5]  # Top 5 most likely patterns

    def check_sherlock_available(self) -> bool:
        """Check if Sherlock is installed and available"""
        try:
            # Check if sherlock command exists in the framework directory
            sherlock_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sherlock', 'sherlock_project', 'sherlock.py')
            if os.path.exists(sherlock_path):
                result = subprocess.run(['python', sherlock_path, '--help'], capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            
            # Check system sherlock
            result = subprocess.run(['sherlock', '--help'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def run_sherlock_scan(self, username: str, output_dir: Path) -> Dict:
        """Run Sherlock scan for a specific username"""
        
        if not self.check_sherlock_available():
            return {
                'found': False,
                'error': 'Sherlock not installed',
                'install_instructions': 'pip install sherlock-project or clone from https://github.com/sherlock-project/sherlock'
            }
        
        self.logger.info(f"🔍 Running Sherlock scan for username: {username}")
        
        # Create sherlock output directory  
        sherlock_dir = output_dir / "sherlock_results"
        sherlock_dir.mkdir(exist_ok=True)
        
        output_file = sherlock_dir / f"{username}_sherlock.json"
        
        # Build Sherlock command - use the installed version in our directory
        sherlock_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sherlock', 'sherlock_project', 'sherlock.py')
        
        cmd = [
            'python', sherlock_path,
            username,
            '--output', str(output_file),
            '--timeout', '10',  # 10 second timeout per site
            '--print-found'  # Only show found results (color enabled for cool output!)
        ]
        
        try:
            # Run Sherlock with live terminal output
            self.logger.info(f"🎨 Sherlock scan starting (live output below)...")
            self.logger.info("=" * 70)
            
            result = subprocess.run(
                cmd, 
                capture_output=False,  # Show colorful output in terminal!
                timeout=120  # 2 minute timeout
            )
            
            self.logger.info("=" * 70)
            
            if result.returncode == 0:
                # Parse Sherlock JSON output
                if output_file.exists():
                    with open(output_file, 'r') as f:
                        sherlock_data = json.load(f)
                    
                    # Extract successful matches
                    found_profiles = []
                    for site, site_data in sherlock_data.items():
                        if isinstance(site_data, dict) and site_data.get('exists') == 'yes':
                            found_profiles.append({
                                'platform': site,
                                'url': site_data.get('url_user', ''),
                                'username': username,
                                'response_time': site_data.get('http_status', '')
                            })
                    
                    self.logger.info(f"✅ Sherlock found {len(found_profiles)} profiles for {username}")
                    return {
                        'found': len(found_profiles) > 0,
                        'username': username,
                        'profiles_found': found_profiles,
                        'total_sites_checked': len(sherlock_data),
                        'raw_data': sherlock_data
                    }
                else:
                    return {'found': False, 'error': 'No Sherlock output file generated'}
            else:
                self.logger.warning(f"Sherlock failed for {username}: {result.stderr}")
                return {'found': False, 'error': result.stderr}
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Sherlock scan timed out for {username}")
            return {'found': False, 'error': 'Scan timed out after 2 minutes'}
        except Exception as e:
            self.logger.error(f"Sherlock error for {username}: {e}")
            return {'found': False, 'error': str(e)}

    def hunt_comprehensive(self, output_dir: Path) -> Dict:
        """Run comprehensive Sherlock-based username enumeration"""
        
        all_results = {
            'found': False,
            'total_usernames_checked': len(self.usernames_to_check),
            'successful_usernames': [],
            'all_profiles_found': [],
            'platforms_with_matches': [],
            'scan_summary': {}
        }
        
        self.logger.info(f"🎯 Starting Sherlock username enumeration for: {self.target_name}")
        self.logger.info(f"📊 Checking {len(self.usernames_to_check)} username patterns")
        
        # Check each potential username
        for username in self.usernames_to_check:
            self.logger.info(f"Scanning username: {username}")
            
            username_results = self.run_sherlock_scan(username, output_dir)
            all_results['scan_summary'][username] = username_results
            
            if username_results.get('found'):
                all_results['successful_usernames'].append(username)
                profiles = username_results.get('profiles_found', [])
                all_results['all_profiles_found'].extend(profiles)
                
                # Track which platforms have matches
                for profile in profiles:
                    platform = profile.get('platform')
                    if platform not in all_results['platforms_with_matches']:
                        all_results['platforms_with_matches'].append(platform)
                
                self.logger.info(f"✅ Username '{username}' found on {len(profiles)} platforms")
            else:
                self.logger.info(f"❌ Username '{username}' not found")
            
            # Small delay between username checks
            time.sleep(2)
        
        all_results['found'] = len(all_results['successful_usernames']) > 0
        
        if all_results['found']:
            total_profiles = len(all_results['all_profiles_found'])
            total_platforms = len(all_results['platforms_with_matches'])
            successful = len(all_results['successful_usernames'])
            
            self.logger.info(f"🎉 Sherlock scan complete!")
            self.logger.info(f"📊 {successful}/{self.total_usernames_checked} usernames found")
            self.logger.info(f"🌐 {total_profiles} profiles across {total_platforms} platforms")
            
        return all_results

# Standalone function for easy integration
def run_sherlock_username_hunt(target_name: str, output_dir: Path) -> Dict:
    """
    Standalone function to run Sherlock username enumeration
    Returns discovered usernames for use in email discovery enrichment
    """
    sherlock = SherlockIntegration(target_name)
    return sherlock.hunt_comprehensive(output_dir)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python sherlock_integration.py 'Full Name'")
        sys.exit(1)
        
    target = sys.argv[1]
    output = Path("./sherlock_test_output")
    output.mkdir(exist_ok=True)
    
    results = run_sherlock_username_hunt(target, output)
    print(f"\nSherlock Results: {json.dumps(results, indent=2)}")
