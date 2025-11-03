#!/usr/bin/env python3
"""
Holehe Integration for Email Validation
Checks if emails exist on 120+ platforms (Instagram, Twitter, Facebook, etc.)
Perfect for validating pattern-generated emails to see which are real
"""

import os
import json
import subprocess
import logging
from typing import Dict, List
from pathlib import Path

class HoleheIntegration:
    """
    Integration wrapper for Holehe email platform verification
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def check_holehe_available(self) -> bool:
        """Check if Holehe is installed and available"""
        try:
            # Check if holehe command exists
            result = subprocess.run(['holehe', '--help'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            try:
                # Check if python holehe exists
                result = subprocess.run(['python3', '-m', 'holehe', '--help'], capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            except:
                return False

    def check_email_platforms(self, email: str, output_dir: Path) -> Dict:
        """Check if email exists on various platforms using Holehe"""
        
        if not self.check_holehe_available():
            return {
                'found': False,
                'error': 'Holehe not installed',
                'install_instructions': 'pip install holehe'
            }
        
        self.logger.info(f"🔍 Running Holehe validation for: {email}")
        
        # Create holehe output directory
        holehe_dir = output_dir / "holehe_results"
        holehe_dir.mkdir(exist_ok=True)
        
        output_file = holehe_dir / f"{email.replace('@', '_at_').replace('.', '_')}_holehe.json"
        
        # Holehe command
        cmd = [
            'holehe',
            email,
            '--output', str(output_file),
            '--only-used'  # Only show platforms where email is used
        ]
        
        try:
            self.logger.info(f"🎨 Holehe validation starting (live output below)...")
            self.logger.info("=" * 70)
            
            result = subprocess.run(
                cmd,
                capture_output=False,  # Show colorful output in terminal!
                timeout=60  # 1 minute timeout
            )
            
            self.logger.info("=" * 70)
            
            platforms_found = []
            
            if result.returncode == 0:
                # Parse Holehe output
                if output_file.exists():
                    try:
                        with open(output_file, 'r') as f:
                            holehe_data = json.load(f)
                        
                        # Extract platforms where email was found
                        for platform, platform_data in holehe_data.items():
                            if isinstance(platform_data, dict) and platform_data.get('exists'):
                                platforms_found.append({
                                    'platform': platform,
                                    'exists': True,
                                    'rateLimit': platform_data.get('rateLimit', False),
                                    'emailrecovery': platform_data.get('emailrecovery', ''),
                                    'phoneNumber': platform_data.get('phoneNumber', ''),
                                })
                                
                    except Exception as e:
                        self.logger.warning(f"Error parsing Holehe output: {e}")
                
                # Also parse from stdout if available
                if result.stdout and 'Used' in result.stdout:
                    # Holehe outputs "Used" for platforms where email exists
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if '[+]' in line and 'Used' in line:
                            # Extract platform name from output line
                            platform = line.split('[+]')[1].split(':')[0].strip()
                            if platform not in [p['platform'] for p in platforms_found]:
                                platforms_found.append({
                                    'platform': platform,
                                    'exists': True,
                                    'source': 'stdout_parse'
                                })
                
                self.logger.info(f"✅ Holehe found {email} on {len(platforms_found)} platforms")
                return {
                    'found': len(platforms_found) > 0,
                    'email': email,
                    'platforms': platforms_found,
                    'total_platforms_found': len(platforms_found),
                    'method': 'holehe'
                }
            else:
                self.logger.debug(f"Holehe found no platforms for {email}")
                return {
                    'found': False,
                    'email': email,
                    'platforms': [],
                    'method': 'holehe'
                }
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Holehe scan timed out for {email}")
            return {'found': False, 'error': 'Scan timed out'}
        except Exception as e:
            self.logger.error(f"Holehe error for {email}: {e}")
            return {'found': False, 'error': str(e)}

    def validate_email_batch(self, emails: List[str], output_dir: Path, max_emails: int = 10) -> Dict:
        """Validate multiple emails using Holehe (batch processing)"""
        
        all_results = {
            'emails_validated': [],
            'emails_found_on_platforms': [],
            'total_platform_matches': 0,
            'validation_summary': {}
        }
        
        self.logger.info(f"🎯 Batch validating {len(emails)} emails with Holehe")
        
        # Limit emails to avoid long scan times
        emails_to_check = emails[:max_emails]
        if len(emails) > max_emails:
            self.logger.warning(f"Limiting to first {max_emails} emails (Holehe can be slow)")
        
        for email in emails_to_check:
            try:
                email_result = self.check_email_platforms(email, output_dir)
                all_results['validation_summary'][email] = email_result
                
                if email_result.get('found'):
                    platforms_count = len(email_result.get('platforms', []))
                    all_results['emails_found_on_platforms'].append({
                        'email': email,
                        'platforms': email_result.get('platforms', []),
                        'platform_count': platforms_count
                    })
                    all_results['total_platform_matches'] += platforms_count
                    self.logger.info(f"✅ {email} verified on {platforms_count} platforms")
                else:
                    self.logger.info(f"❌ {email} not found on any platforms")
                
                all_results['emails_validated'].append(email)
                
                # Rate limiting between emails
                time.sleep(3)
                
            except Exception as e:
                self.logger.warning(f"Holehe validation failed for {email}: {e}")
                continue
        
        validated_count = len(all_results['emails_found_on_platforms'])
        total_count = len(all_results['emails_validated'])
        
        if validated_count > 0:
            self.logger.info(f"🎉 Holehe validation complete!")
            self.logger.info(f"📊 {validated_count}/{total_count} emails found on platforms")
            self.logger.info(f"🌐 {all_results['total_platform_matches']} total platform matches")
        
        return all_results

# Integration function for main framework
def validate_emails_with_holehe(email_candidates: List[str], output_dir: Path) -> Dict:
    """
    Validate email candidates using Holehe platform checking
    Much more reliable than DNS validation for determining if emails are real
    """
    
    holehe = HoleheIntegration()
    return holehe.validate_email_batch(email_candidates, output_dir)

def get_holehe_installation_status() -> Dict:
    """Check Holehe installation status and provide setup instructions"""
    
    holehe = HoleheIntegration()
    is_available = holehe.check_holehe_available()
    
    return {
        'available': is_available,
        'install_command': 'pip install holehe',
        'github': 'https://github.com/megadose/holehe',
        'purpose': 'Validate emails by checking if they exist on 120+ platforms',
        'value': 'Turns email patterns into confirmed real emails'
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python holehe_integration.py email@example.com")
        sys.exit(1)
        
    email = sys.argv[1]
    output = Path("./holehe_test_output")
    output.mkdir(exist_ok=True)
    
    holehe = HoleheIntegration()
    results = holehe.check_email_platforms(email, output)
    print(f"\nHolehe Results: {json.dumps(results, indent=2)}")
