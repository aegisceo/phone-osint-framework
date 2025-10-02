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

        # Try to reconfigure stdout for UTF-8 (safer than reopening file descriptor)
        # This handles emojis without breaking subprocess.Popen(stdout=PIPE)
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, OSError):
            # stdout is not reconfigurable (e.g., when it's a PIPE from subprocess)
            pass

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
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
    
    def run_google_dorking(self, phone_data, enriched_identity=None):
        """Enhanced Google dorking based on enriched identity (names+emails) and phone data"""
        self.logger.info("Running enhanced Google dorking...")

        from scripts.google_dorker import GoogleDorker
        dorker = GoogleDorker(self.phone_number, phone_data, enriched_identity)
        results = dorker.search()

        output_file = self.output_dir / "google_dork_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        return results

    def run_yandex_scraping(self, enriched_identity=None, proxy_list=None):
        """
        Yandex search scraping with anti-bot measures
        Particularly useful for Russian/Eastern European data
        """
        self.logger.info("Running Yandex search scraping...")

        from scripts.yandex_scraper import YandexScraper, load_free_proxy_list

        # Load proxies if not provided
        if proxy_list is None:
            proxy_list = load_free_proxy_list()
            if proxy_list:
                self.logger.info(f"Loaded {len(proxy_list)} proxies for rotation")
            else:
                self.logger.warning("No proxies available - scraping without proxy rotation (higher risk of blocking)")

        scraper = YandexScraper(self.phone_number, enriched_identity, proxy_list)
        results = scraper.search()

        output_file = self.output_dir / "yandex_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Log summary
        total = sum(len(v) for v in results.values())
        self.logger.info(f"Yandex scraping complete: {total} results found")

        return results
    
    def run_social_media_scan(self, discovered_emails=None):
        """Check social media platforms with email correlation"""
        self.logger.info("Scanning social media platforms...")

        from scripts.social_scanner import SocialMediaScanner
        scanner = SocialMediaScanner(self.phone_number, discovered_emails)
        results = scanner.scan_all_platforms()

        output_file = self.output_dir / "social_media_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        return results
    
    def run_data_breach_check(self, discovered_emails=None):
        """Check data breaches using discovered emails"""
        self.logger.info("Checking data breach databases...")

        from scripts.breach_checker import BreachChecker
        checker = BreachChecker(self.phone_number)
        results = checker.check_all_sources(discovered_emails)

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

    def run_email_discovery(self, identity_data=None):
        """Run comprehensive email discovery"""
        self.logger.info("🎯 Starting email discovery...")

        from scripts.email_hunter import EmailHunter
        hunter = EmailHunter(self.phone_number, identity_data)
        results = hunter.hunt_comprehensive()

        output_file = self.output_dir / "email_discovery_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Extract emails for use by other modules (only real discovered emails)
        discovered_emails = []

        # Add verified emails (highest confidence)
        for email_data in results.get('verified_emails', []):
            discovered_emails.append(email_data['email'])

        # Add ALL emails found (including user-provided)
        for email_data in results.get('emails', []):
            discovered_emails.append(email_data['email'])

        # Remove duplicates
        discovered_emails = list(set(discovered_emails))

        # Log results
        total_emails = len(results.get('emails', [])) + len(results.get('verified_emails', []))
        verified_count = len(results.get('verified_emails', []))

        if results.get('found'):
            self.logger.info(f"✅ Email discovery complete: {total_emails} emails found, {verified_count} verified")
        else:
            self.logger.warning("❌ No emails discovered")

        # Return both full results and extracted emails for downstream use
        return results, discovered_emails

    def run_risk_assessment(self, all_results):
        """Run comprehensive risk assessment on investigation results"""
        self.logger.info("🎯 Running intelligent risk assessment...")

        from scripts.risk_assessor import RiskAssessor
        assessor = RiskAssessor(self.phone_number)
        risk_assessment = assessor.calculate_overall_risk(all_results)

        output_file = self.output_dir / "risk_assessment.json"
        with open(output_file, 'w') as f:
            json.dump(risk_assessment, f, indent=2)

        # Log key findings
        score = risk_assessment['overall_score']
        level = risk_assessment['risk_level']
        factor_count = len(risk_assessment['risk_factors'])

        self.logger.info(f"🎯 Risk Assessment Complete: {level} ({score}/10)")
        self.logger.info(f"📊 {factor_count} risk factors analyzed")

        return risk_assessment

    def _build_enriched_identity(self, name_results, email_results, discovered_emails, original_identity=None):
        """
        Build enriched identity context from discovered data for smarter downstream searches
        This prevents wasteful phone-only searches when we have names and emails
        """
        enriched = {
            'phone': self.phone_number,
            'primary_names': [],
            'all_names': [],
            'emails': discovered_emails or [],
            'first_name': None,
            'last_name': None,
            'known_email': None
        }

        # Extract names from name hunting results
        if name_results.get('found'):
            enriched['primary_names'] = name_results.get('primary_names', [])
            enriched['all_names'] = name_results.get('all_names', [])

            # Parse first primary name into first/last
            if enriched['primary_names']:
                primary = enriched['primary_names'][0]
                parts = primary.split()
                if len(parts) >= 2:
                    enriched['first_name'] = parts[0]
                    enriched['last_name'] = ' '.join(parts[1:])
                elif len(parts) == 1:
                    enriched['first_name'] = parts[0]

        # Add original identity data if no discovered data
        if original_identity:
            if not enriched['first_name'] and original_identity.get('first_name'):
                enriched['first_name'] = original_identity['first_name']
            if not enriched['last_name'] and original_identity.get('last_name'):
                enriched['last_name'] = original_identity['last_name']
            if original_identity.get('known_email'):
                enriched['known_email'] = original_identity['known_email']

        # Use first discovered email as primary
        if enriched['emails'] and not enriched['known_email']:
            enriched['known_email'] = enriched['emails'][0]

        return enriched

    def run_full_investigation(self, identity_data=None):
        """Run complete investigation pipeline"""
        self.logger.info(f"Starting full investigation for: {self.phone_number}")

        if identity_data:
            self.logger.info(f"Enhanced investigation with identity data: {list(identity_data.keys())}")

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

        # 🎯 BUILD PRELIMINARY ENRICHED IDENTITY - Use discovered names for email hunting!
        preliminary_identity = self._build_enriched_identity(
            name_hunting_results,
            {},  # No email results yet
            [],  # No discovered emails yet
            identity_data
        )
        self.logger.info(f"🎯 Preliminary identity built with names: {preliminary_identity.get('primary_names', [])}")

        # 3. EMAIL DISCOVERY - Now with discovered names from name hunting!
        email_results, discovered_emails = self.run_email_discovery(preliminary_identity)
        all_results['results']['email_discovery'] = email_results

        # 🎯 FINALIZE ENRICHED IDENTITY CONTEXT - Add discovered emails!
        enriched_identity = self._build_enriched_identity(
            name_hunting_results,
            email_results,
            discovered_emails,
            identity_data
        )
        self.logger.info(f"🎯 Enriched identity finalized: {list(enriched_identity.keys())}")

        # 4. PhoneInfoga scan
        phone_data = self.run_phoneinfoga()
        all_results['results']['phoneinfoga'] = phone_data

        # 5. Google dorking with enriched identity
        google_results = self.run_google_dorking(phone_data, enriched_identity)
        all_results['results']['google_dorking'] = google_results

        # 6. Yandex scraping (Russian/Eastern European data)
        yandex_results = self.run_yandex_scraping(enriched_identity)
        all_results['results']['yandex'] = yandex_results

        # 7. Enhanced social media with email correlation
        social_results = self.run_social_media_scan(discovered_emails)
        all_results['results']['social_media'] = social_results

        # 7. Enhanced breach check with discovered emails
        breach_results = self.run_data_breach_check(discovered_emails)
        all_results['results']['breaches'] = breach_results

        # 8. Carrier analysis (using validation data)
        carrier_name = validation_results.get('summary', {}).get('carrier')
        if carrier_name and carrier_name != 'Unknown':
            carrier_results = self.run_carrier_analysis(carrier_name)
            all_results['results']['carrier_analysis'] = carrier_results

        # 9. INTELLIGENT RISK ASSESSMENT - Comprehensive multi-factor analysis
        risk_assessment = self.run_risk_assessment(all_results)
        all_results['results']['risk_assessment'] = risk_assessment

        # 10. Generate report
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