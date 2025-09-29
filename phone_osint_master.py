#!/usr/bin/env python3
"""
Master Phone OSINT Orchestrator
Coordinates all tools and generates comprehensive reports
"""
import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

class PhoneOSINTMaster:
    def __init__(self, phone_number):
        self.phone_number = phone_number
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"results/{self.timestamp}_{phone_number}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        log_file = self.output_dir / "investigation.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def parse_phoneinfoga_output(self, output):
        """Parse PhoneInfoga text output to extract useful intelligence (filtering out useless search URLs)"""
        data = {
            'country': None,
            'local': None,
            'e164': None,
            'international': None,
            'raw_local': None,
            'useful_findings': [],  # Only real findings, not search URLs
            'scanners_succeeded': 0,
            'scanners_failed': []
        }

        current_section = None

        for line in output.split('\n'):
            line = line.strip()

            # Extract basic phone formats
            if 'Country:' in line:
                data['country'] = line.split('Country:')[1].strip()
            elif 'Local:' in line:
                data['local'] = line.split('Local:')[1].strip()
            elif 'E164:' in line:
                data['e164'] = line.split('E164:')[1].strip()
            elif 'International:' in line:
                data['international'] = line.split('International:')[1].strip()
            elif 'Raw local:' in line:
                data['raw_local'] = line.split('Raw local:')[1].strip()

            # Track scanners status
            elif 'scanner(s) succeeded' in line:
                try:
                    data['scanners_succeeded'] = int(line.split()[0])
                except:
                    pass
            elif ':' in line and 'Invalid authentication' in line:
                scanner_name = line.split(':')[0].strip()
                data['scanners_failed'].append(scanner_name)

            # Skip useless sections that only contain search URLs
            elif line in ['Social media:', 'Disposable providers:', 'Reputation:', 'Individuals:', 'General:']:
                current_section = 'skip'  # Mark to skip all URLs in these sections

            # Skip all URLs - they're just useless Google search queries
            elif line.startswith('URL:') and current_section == 'skip':
                continue  # Ignore all the garbage URLs

            # Look for actual useful findings (non-URL data)
            elif current_section != 'skip' and line.strip() and not line.startswith('URL:'):
                # Only capture non-URL findings that might be useful
                if 'scanner' not in line.lower() and 'result' not in line.lower() and len(line.strip()) > 10:
                    data['useful_findings'].append(line.strip())

        return data

    def run_phoneinfoga(self):
        """Run PhoneInfoga scan"""
        self.logger.info("Starting PhoneInfoga scan...")
        
        output_file = self.output_dir / "phoneinfoga_results.json"
        
        cmd = [
            "phoneinfoga",
            "scan",
            "-n", self.phone_number
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            with open(output_file, 'w') as f:
                f.write(result.stdout)

            # Parse text output to extract comprehensive intelligence
            output = result.stdout
            data = self.parse_phoneinfoga_output(output)

            # Enhanced logging (cleaned up)
            country = data.get('country', 'Unknown')
            useful_findings = len(data.get('useful_findings', []))
            scanners_succeeded = data.get('scanners_succeeded', 0)

            self.logger.info(f"PhoneInfoga scan complete. Country: {country}, Useful findings: {useful_findings}, Scanners: {scanners_succeeded}")
            return data
            
        except Exception as e:
            self.logger.error(f"PhoneInfoga error: {e}")
            return {}
    
    def run_google_dorking(self, phone_data):
        """Enhanced Google dorking based on phone data"""
        self.logger.info("Running enhanced Google dorking...")
        
        from scripts.google_dorker import GoogleDorker
        dorker = GoogleDorker(self.phone_number, phone_data)
        results = dorker.search()
        
        output_file = self.output_dir / "google_dork_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        return results
    
    def run_social_media_scan(self):
        """Check social media platforms"""
        self.logger.info("Scanning social media platforms...")
        
        from scripts.social_scanner import SocialMediaScanner
        scanner = SocialMediaScanner(self.phone_number)
        results = scanner.scan_all_platforms()
        
        output_file = self.output_dir / "social_media_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        return results
    
    def run_data_breach_check(self):
        """Check data breaches"""
        self.logger.info("Checking data breach databases...")
        
        from scripts.breach_checker import BreachChecker
        checker = BreachChecker(self.phone_number)
        results = checker.check_all_sources()
        
        output_file = self.output_dir / "breach_check_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        return results
    
    def run_carrier_analysis(self, carrier_name):
        """Deep carrier analysis"""
        self.logger.info(f"Running carrier analysis for: {carrier_name}")
        
        from scripts.carrier_analyzer import CarrierAnalyzer
        analyzer = CarrierAnalyzer(self.phone_number, carrier_name)
        results = analyzer.analyze()
        
        output_file = self.output_dir / "carrier_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        return results
    
    def generate_report(self, all_data):
        """Generate comprehensive HTML report"""
        self.logger.info("Generating final report...")
        
        from scripts.report_generator import ReportGenerator
        generator = ReportGenerator(self.phone_number, all_data, self.output_dir)
        report_path = generator.generate()
        
        self.logger.info(f"Report generated: {report_path}")
        return report_path
    
    def run_phone_validation(self):
        """Run comprehensive phone number validation"""
        self.logger.info("Running comprehensive phone validation...")

        from scripts.phone_validator import PhoneValidator
        validator = PhoneValidator(self.phone_number)
        results = validator.validate_comprehensive()

        output_file = self.output_dir / "phone_validation.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        return results

    def run_unified_name_hunting(self, identity_data=None):
        """Run comprehensive unified name hunting (THE GRAIL!)"""
        self.logger.info("🎯 Starting UNIFIED NAME HUNTING - THE GRAIL!")

        if identity_data:
            self.logger.info(f"🎯 Enhanced hunting with identity data: {list(identity_data.keys())}")

        from scripts.unified_name_hunter import UnifiedNameHunter
        hunter = UnifiedNameHunter(self.phone_number, identity_data)
        results = hunter.hunt_ultimate()

        output_file = self.output_dir / "name_hunting_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Log the grail results
        if results['found']:
            self.logger.info(f"🔥 THE GRAIL ACHIEVED! Primary names: {results['primary_names']}")
            self.logger.info(f"💰 Total names discovered: {len(results['all_names'])}")
            self.logger.info(f"⭐ Best confidence: {results.get('best_confidence', 0):.2f}")
        else:
            self.logger.warning("❌ The Grail remains elusive - no names found")

        return results

    def run_full_investigation(self, identity_data=None):
        """Run complete investigation pipeline"""
        self.logger.info(f"Starting full investigation for: {self.phone_number}")

        if identity_data:
            self.logger.info(f"🎯 Enhanced investigation with identity data: {list(identity_data.keys())}")

        all_results = {
            'phone_number': self.phone_number,
            'timestamp': self.timestamp,
            'results': {}
        }

        # 1. Phone validation (NumVerify + Twilio)
        validation_results = self.run_phone_validation()
        all_results['results']['validation'] = validation_results

        # 2. AGGRESSIVE NAME HUNTING (THE GRAIL!) - Now with identity data!
        name_hunting_results = self.run_unified_name_hunting(identity_data)
        all_results['results']['name_hunting'] = name_hunting_results

        # 3. PhoneInfoga scan
        phone_data = self.run_phoneinfoga()
        all_results['results']['phoneinfoga'] = phone_data

        # 4. Google dorking
        google_results = self.run_google_dorking(phone_data)
        all_results['results']['google_dorking'] = google_results

        # 5. Social media
        social_results = self.run_social_media_scan()
        all_results['results']['social_media'] = social_results

        # 6. Breach check
        breach_results = self.run_data_breach_check()
        all_results['results']['breaches'] = breach_results

        # 7. Carrier analysis (using validation data)
        carrier_name = validation_results.get('summary', {}).get('carrier')
        if carrier_name and carrier_name != 'Unknown':
            carrier_results = self.run_carrier_analysis(carrier_name)
            all_results['results']['carrier_analysis'] = carrier_results

        # 8. Generate report
        report_path = self.generate_report(all_results)

        # Save complete results
        complete_file = self.output_dir / "complete_results.json"
        with open(complete_file, 'w') as f:
            json.dump(all_results, f, indent=2)

        self.logger.info(f"Investigation complete! Results in: {self.output_dir}")

        return report_path

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python phone_osint_master.py <phone_number> [identity_data_json]")
        sys.exit(1)

    phone = sys.argv[1]
    identity_data = None

    # Parse identity data if provided
    if len(sys.argv) == 3:
        try:
            identity_data = json.loads(sys.argv[2])
            print(f"Identity data loaded: {list(identity_data.keys())}")
        except json.JSONDecodeError as e:
            print(f"Error parsing identity data JSON: {e}")
            sys.exit(1)

    investigator = PhoneOSINTMaster(phone)
    report = investigator.run_full_investigation(identity_data)
    print(f"\nInvestigation complete! Open report: {report}")