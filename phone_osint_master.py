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
        
        # Check for local PhoneInfoga binary first
        possible_paths = [
            "phoneinfoga",  # System PATH
            "./phoneinfoga",  # Current directory
            "./phoneinfoga.exe",  # Windows executable
            "./tools/phoneinfoga",  # Tools directory
            "./tools/phoneinfoga.exe"  # Tools directory Windows
        ]
        
        phoneinfoga_cmd = None
        for path in possible_paths:
            try:
                result = subprocess.run([path, "--help"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    phoneinfoga_cmd = path
                    break
            except:
                continue
        
        if not phoneinfoga_cmd:
            self.logger.warning("PhoneInfoga executable not found. Skipping PhoneInfoga scan.")
            self.logger.info("To install PhoneInfoga: Download from https://github.com/sundowndev/phoneinfoga/releases")
            return {
                'error': 'PhoneInfoga not installed',
                'country': 'Unknown',
                'useful_findings': [],
                'scanners_succeeded': 0
            }
        
        cmd = [phoneinfoga_cmd, "scan", "-n", self.phone_number]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            with open(output_file, 'w', encoding='utf-8') as f:
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
            return {
                'error': str(e),
                'country': 'Unknown',
                'useful_findings': [],
                'scanners_succeeded': 0
            }
    
    def run_google_dorking(self, phone_data, enriched_identity=None):
        """Enhanced Google dorking based on enriched identity (names+emails) and phone data"""
        self.logger.info("Running enhanced Google dorking...")

        from scripts.google_dorker import GoogleDorker
        dorker = GoogleDorker(self.phone_number, phone_data, enriched_identity)
        results = dorker.search()

        output_file = self.output_dir / "google_dork_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        return results

    def run_social_media_scan(self, discovered_emails=None, enriched_identity=None):
        """Check social media platforms with comprehensive data extraction"""
        self.logger.info("Scanning social media platforms...")

        from scripts.social_scanner import SocialMediaScanner
        scanner = SocialMediaScanner(self.phone_number, discovered_emails, enriched_identity)
        results = scanner.scan_all_platforms()

        output_file = self.output_dir / "social_media_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        return results
    
    def run_truepeoplesearch_enrichment(self, enriched_identity=None):
        """
        Run TruePeopleSearch with all discovered data
        Best run AFTER breach discovery to use verified data
        Returns: Dict with names, addresses, associates, additional_phones
        """
        self.logger.info("="*70)
        self.logger.info("🔍 TRUEPEOPLESEARCH ENRICHMENT")
        self.logger.info("🎯 Using breach-verified data for comprehensive people search")
        self.logger.info("💡 Free source: names, addresses, associates, emails, phone numbers")
        self.logger.info("="*70)
        
        from scripts.truepeoplesearch_scraper import search_truepeoplesearch
        
        results = search_truepeoplesearch(self.phone_number)
        
        if results.get('found'):
            self.logger.info(f"✅ TruePeopleSearch SUCCESS")
            self.logger.info(f"   📛 Names: {len(results.get('names', []))}")
            self.logger.info(f"   📍 Addresses: {len(results.get('addresses', []))}")
            self.logger.info(f"   👥 Associates: {len(results.get('associates', []))}")
            if results.get('additional_phones'):
                self.logger.info(f"   📞 Additional Phones: {len(results.get('additional_phones', []))}")
        else:
            self.logger.warning(f"❌ TruePeopleSearch: {results.get('error', 'No results found')}")
        
        return results
    
    def run_data_breach_check(self, discovered_emails=None, email_results=None, enriched_identity=None):
        """
        Check data breaches using ALL discovered data (phone, emails, usernames, names, addresses)
        
        Args:
            discovered_emails: List of email strings discovered during investigation
            email_results: Full email discovery results dict (for fallback extraction)
            enriched_identity: Enriched identity data with usernames, names, addresses
            
        Returns:
            Dict with comprehensive breach information
        """
        self.logger.info("="*60)
        self.logger.info("🔍 COMPREHENSIVE BREACH DATABASE CHECK")
        self.logger.info("🎯 Searching with: phone, emails, usernames, names, addresses")
        self.logger.info("="*60)

        from scripts.breach_checker import BreachChecker
        from scripts.phone_breach_databases import ComprehensiveBreachSearcher
        
        # Build comprehensive email list from multiple sources
        emails_to_check = set()
        
        # Source 1: Provided list of discovered emails
        if discovered_emails and len(discovered_emails) > 0:
            self.logger.info(f"📧 Adding {len(discovered_emails)} emails from discovered_emails list")
            emails_to_check.update(discovered_emails)
        
        # Source 2: Extract from email_results if provided (fallback)
        if email_results:
            # Extract from verified_emails
            for email_data in email_results.get('verified_emails', []):
                if isinstance(email_data, dict) and 'email' in email_data:
                    emails_to_check.add(email_data['email'])
            
            # Extract from all emails
            for email_data in email_results.get('emails', []):
                if isinstance(email_data, dict) and 'email' in email_data:
                    emails_to_check.add(email_data['email'])
                elif isinstance(email_data, str):
                    emails_to_check.add(email_data)
        
        # Convert to list and filter invalid
        final_email_list = [e for e in emails_to_check if e and '@' in e and '.' in e]
        
        # Method 1: HIBP email checking (conditional - only if we have emails)
        if final_email_list and len(final_email_list) > 0:
            self.logger.info(f"📧 Checking {len(final_email_list)} unique emails via HIBP + searching DeHashed/LeakCheck...")
            self.logger.debug(f"Emails to check: {final_email_list}")
            checker = BreachChecker(self.phone_number)
            hibp_results = checker.check_all_sources(final_email_list)
        else:
            # No emails yet - skip HIBP, but continue with DeHashed/LeakCheck
            self.logger.info("🔍 No emails yet - searching DeHashed/LeakCheck by phone+name to discover emails")
            hibp_results = {
                'found': False,
                'sources_checked': [],
                'total_breaches': 0,
                'emails_checked': 0,
                'breached_emails': [],
                'clean_emails': [],
                'error_emails': [],
                'detailed_results': []
            }
        
        # Method 2: Comprehensive breach database search (phone, username, name, address)
        # ALWAYS RUN - can search by phone+name even without emails!
        self.logger.info("🔍 Searching comprehensive breach databases (DeHashed, LeakCheck, Intelligence X)...")
        
        # Build search parameters from ALL discovered data
        breach_search_params = {
            'emails': final_email_list,
            'usernames': enriched_identity.get('usernames', []) if enriched_identity else [],
            'names': enriched_identity.get('primary_names', []) if enriched_identity else [],
            'addresses': enriched_identity.get('addresses', []) if enriched_identity else []
        }
        
        comprehensive_searcher = ComprehensiveBreachSearcher(
            phone_number=self.phone_number,
            search_params=breach_search_params
        )
        
        comprehensive_results = comprehensive_searcher.search_all_databases()
        
        # Combine results
        results = hibp_results
        results['comprehensive_search'] = comprehensive_results
        
        # Merge discovered emails from comprehensive search
        if comprehensive_results.get('associated_emails'):
            self.logger.info(f"🔥 Comprehensive search found {len(comprehensive_results['associated_emails'])} additional emails!")
            results['additional_emails_discovered'] = comprehensive_results['associated_emails']
        
        # Merge discovered usernames
        if comprehensive_results.get('associated_usernames'):
            self.logger.info(f"👤 Comprehensive search found {len(comprehensive_results['associated_usernames'])} usernames!")
            results['additional_usernames_discovered'] = comprehensive_results['associated_usernames']

        # Save detailed results
        output_file = self.output_dir / "breach_check_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        # Enhanced logging
        total_breached = len(results.get('breached_emails', [])) + (1 if comprehensive_results.get('found') else 0)
        
        if total_breached > 0:
            self.logger.warning(f"🚨 BREACH ALERT: Data found in breach databases!")
            self.logger.info(f"📧 HIBP: {len(results.get('breached_emails', []))} emails compromised")
            self.logger.info(f"📊 Comprehensive: {len(comprehensive_results.get('breaches_found', []))} breach records")
        else:
            self.logger.info(f"✅ No breaches found across all databases")
        
        if results.get('additional_emails_discovered'):
            self.logger.info(f"🔥 BONUS: {len(results['additional_emails_discovered'])} NEW emails discovered from breach data!")
        
        if results.get('error_emails'):
            self.logger.warning(f"⚠️ Errors checking {len(results.get('error_emails', []))} emails")
        
        self.logger.info(f"💾 Breach results saved to: {output_file}")
        self.logger.info("="*60)

        return results
    
    def run_carrier_analysis(self, carrier_name):
        """Deep carrier analysis"""
        self.logger.info(f"Running carrier analysis for: {carrier_name}")
        
        from scripts.carrier_analyzer import CarrierAnalyzer
        analyzer = CarrierAnalyzer(self.phone_number, carrier_name)
        results = analyzer.analyze()
        
        output_file = self.output_dir / "carrier_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
            
        return results
    
    def generate_report(self, all_data):
        """Generate comprehensive HTML reports (classic + modern)"""
        self.logger.info("="*60)
        self.logger.info("📊 GENERATING REPORTS")
        self.logger.info("="*60)
        
        # Generate classic detailed report
        from scripts.report_generator import ReportGenerator
        generator = ReportGenerator(self.phone_number, all_data, self.output_dir)
        classic_report = generator.generate()
        self.logger.info(f"✅ Classic report generated: {classic_report}")
        
        # Generate modern dashboard report
        try:
            from scripts.modern_report_generator import ModernReportGenerator
            modern_generator = ModernReportGenerator(self.phone_number, all_data, self.output_dir)
            modern_report = modern_generator.generate()
            self.logger.info(f"✅ Modern dashboard generated: {modern_report}")
        except Exception as e:
            import traceback
            self.logger.warning(f"⚠️ Modern report generation failed: {e}")
            self.logger.warning(f"Full traceback:\n{traceback.format_exc()}")
            self.logger.info("📄 Classic report still available")
        
        self.logger.info("="*60)
        return classic_report
    
    def run_phone_validation(self):
        """Run comprehensive phone number validation"""
        self.logger.info("Running comprehensive phone validation...")

        from scripts.phone_validator import PhoneValidator
        validator = PhoneValidator(self.phone_number)
        results = validator.validate_comprehensive()

        output_file = self.output_dir / "phone_validation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        return results

    def run_unified_name_hunting(self, identity_data=None, skip_truepeoplesearch=False):
        """Run comprehensive unified name hunting (THE GRAIL!)"""
        self.logger.info("🎯 Starting UNIFIED NAME HUNTING - THE GRAIL!")

        if identity_data:
            self.logger.info(f"🎯 Enhanced hunting with identity data: {list(identity_data.keys())}")

        from scripts.unified_name_hunter import UnifiedNameHunter
        hunter = UnifiedNameHunter(self.phone_number, identity_data, skip_truepeoplesearch=skip_truepeoplesearch)
        results = hunter.hunt_ultimate()

        output_file = self.output_dir / "name_hunting_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        # Log the grail results
        if results['found']:
            self.logger.info(f"🔥 THE GRAIL ACHIEVED! Primary names: {results['primary_names']}")
            self.logger.info(f"💰 Total names discovered: {len(results['all_names'])}")
            self.logger.info(f"⭐ Best confidence: {results.get('best_confidence', 0):.2f}")
        else:
            self.logger.warning("❌ The Grail remains elusive - no names found")

        return results

    def run_email_discovery(self, identity_data=None, skip_pattern_generation=False, skip_public_records=False):
        """Run comprehensive email discovery with conditional phases"""
        self.logger.info("🎯 Starting email discovery...")

        from scripts.email_hunter import EmailHunter
        hunter = EmailHunter(self.phone_number, identity_data)
        results = hunter.hunt_comprehensive(skip_pattern_generation=skip_pattern_generation, skip_public_records=skip_public_records)

        output_file = self.output_dir / "email_discovery_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
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

    def run_employment_intelligence(self, identity_data=None):
        """Run employment intelligence hunting to discover work context"""
        self.logger.info("🎯 Starting employment intelligence hunting...")

        from scripts.employment_hunter import EmploymentHunter
        hunter = EmploymentHunter(self.phone_number, identity_data)
        results = hunter.hunt_comprehensive()

        output_file = self.output_dir / "employment_intelligence_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        # Log results
        if results.get('found'):
            employers = len(results.get('employers', []))
            domains = len(results.get('company_domains', []))
            self.logger.info(f"✅ Employment intelligence complete: {employers} employers, {domains} domains found")
        else:
            self.logger.warning("❌ Employment intelligence unsuccessful")

        return results

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

    def _build_enriched_identity(self, name_results=None, email_results=None, discovered_emails=None, 
                                 social_results=None, employment_results=None, original_identity=None):
        """
        Build comprehensive enriched identity context from all discovered data
        Creates a living context that gets richer throughout the investigation
        """
        enriched = {
            'phone': self.phone_number,
            'primary_names': [],
            'all_names': [],
            'emails': discovered_emails or [],
            'first_name': None,
            'last_name': None,
            'known_email': None,
            'locations': [],
            'companies': [],
            'usernames': [],
            'social_profiles': {},
            'addresses': [],
            'additional_phones': []
        }

        # Extract names from name hunting results
        if name_results and name_results.get('found'):
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

        # Extract social media discoveries
        if social_results:
            aggregated = social_results.get('aggregated_data', {})
            
            # Add discovered emails from social media
            social_emails = aggregated.get('all_emails', [])
            for email in social_emails:
                if email not in enriched['emails']:
                    enriched['emails'].append(email)
            
            # Add discovered usernames
            enriched['usernames'] = aggregated.get('all_usernames', [])
            
            # Add discovered locations
            enriched['locations'] = aggregated.get('all_locations', [])
            
            # Add discovered companies
            enriched['companies'] = aggregated.get('all_companies', [])
            
            # Extract social profiles URLs
            for platform, platform_data in social_results.items():
                if isinstance(platform_data, dict) and platform_data.get('profiles'):
                    enriched['social_profiles'][platform] = platform_data['profiles']

        # Extract employment data
        if employment_results and employment_results.get('found'):
            employers = employment_results.get('employers', [])
            for employer in employers:
                if employer not in enriched['companies']:
                    enriched['companies'].append(employer)

        # Extract additional data from email results
        if email_results and email_results.get('emails'):
            # Look for patterns that might reveal additional info
            for email_entry in email_results['emails']:
                email = email_entry.get('email', '')
                if email and '@' in email:
                    domain = email.split('@')[1]
                    # If it's a business domain, add to companies
                    if not self._is_personal_email_domain(domain):
                        company_name = domain.replace('.com', '').replace('.org', '').replace('.net', '')
                        if company_name not in enriched['companies']:
                            enriched['companies'].append(company_name.title())

        # Add original identity data if no discovered data
        if original_identity:
            for key, value in original_identity.items():
                if key in enriched and not enriched[key] and value:
                    enriched[key] = value
                elif key not in enriched and value:
                    enriched[key] = value

        # Use first discovered email as primary
        if enriched['emails'] and not enriched['known_email']:
            enriched['known_email'] = enriched['emails'][0]

        # Log enrichment summary
        discoveries = []
        if enriched['primary_names']: discoveries.append(f"{len(enriched['primary_names'])} names")
        if enriched['emails']: discoveries.append(f"{len(enriched['emails'])} emails")
        if enriched['usernames']: discoveries.append(f"{len(enriched['usernames'])} usernames")
        if enriched['locations']: discoveries.append(f"{len(enriched['locations'])} locations")
        if enriched['companies']: discoveries.append(f"{len(enriched['companies'])} companies")
        
        if discoveries:
            self.logger.info(f"🎯 Identity enriched with: {', '.join(discoveries)}")

        return enriched

    def _is_personal_email_domain(self, domain: str) -> bool:
        """Check if email domain is personal (not business)"""
        personal_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
            'icloud.com', 'aol.com', 'live.com', 'msn.com'
        }
        return domain.lower() in personal_domains

    def run_full_investigation(self, identity_data=None):
        """
        Run complete investigation pipeline
        REORGANIZED: Breach discovery FIRST to get VERIFIED data!
        """
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

        # 2. AGGRESSIVE NAME HUNTING (THE GRAIL!) - Skip TruePeopleSearch here (runs after breach)
        name_hunting_results = self.run_unified_name_hunting(identity_data, skip_truepeoplesearch=True)
        all_results['results']['name_hunting'] = name_hunting_results

        # 🎯 ENRICHMENT: Build initial identity from phone + name
        preliminary_identity = self._build_enriched_identity(
            name_results=name_hunting_results,
            original_identity=identity_data
        )
        self.logger.info(f"🎯 Initial identity - Names: {preliminary_identity.get('primary_names', [])}")

        # 3. ✨ BREACH DISCOVERY FIRST! (with phone + name = VERIFIED data!)
        self.logger.info("="*70)
        self.logger.info("🚨 PRIORITY: BREACH DATABASE SEARCH")
        self.logger.info("🎯 Searching with phone + name to discover VERIFIED emails/usernames")
        self.logger.info("="*70)
        
        breach_results = self.run_data_breach_check(
            discovered_emails=[],  # Start with nothing - let breaches discover emails!
            email_results=None,
            enriched_identity=preliminary_identity
        )
        all_results['results']['breaches'] = breach_results
        
        # Extract VERIFIED emails and usernames from breach data (HIGH CONFIDENCE!)
        verified_breach_emails = breach_results.get('additional_emails_discovered', [])
        verified_breach_usernames = breach_results.get('additional_usernames_discovered', [])
        
        if verified_breach_emails:
            self.logger.warning(f"🔥 VERIFIED: {len(verified_breach_emails)} emails discovered from breach data!")
            preliminary_identity['emails'] = verified_breach_emails
            preliminary_identity['email_source'] = 'breach_verified'
        
        if verified_breach_usernames:
            self.logger.warning(f"👤 VERIFIED: {len(verified_breach_usernames)} usernames discovered from breach data!")
            preliminary_identity['usernames'] = verified_breach_usernames
            preliminary_identity['username_source'] = 'breach_verified'

        # 4. TruePeopleSearch enrichment (NEW - moved here from name hunting)
        truepeoplesearch_results = self.run_truepeoplesearch_enrichment(preliminary_identity)
        all_results['results']['truepeoplesearch'] = truepeoplesearch_results
        
        # Update identity with TruePeopleSearch data
        if truepeoplesearch_results.get('found'):
            preliminary_identity['addresses'] = truepeoplesearch_results.get('addresses', [])
            preliminary_identity['associates'] = truepeoplesearch_results.get('associates', [])
            if truepeoplesearch_results.get('names'):
                preliminary_identity['primary_names'].extend(truepeoplesearch_results['names'])
        
        # 5. EMAIL DISCOVERY - CONDITIONAL based on verified email count
        verified_emails_count = len(verified_breach_emails)
        
        if verified_emails_count >= 2:
            # SMART MODE: Skip patterns/public records, keep LinkedIn/GitHub/Sherlock
            self.logger.info("="*70)
            self.logger.info(f"✅ {verified_emails_count} verified emails from breach data - SMART ENUMERATION MODE")
            self.logger.info("🎯 Using high-confidence breach-verified emails as foundation")
            self.logger.info("✓ RUNNING: LinkedIn scraping (bio/insights), GitHub, Sherlock (intelligence)")
            self.logger.info("⏭️ SKIPPING: Email pattern generation, public records scraping (redundant)")
            self.logger.info("="*70)
            
            email_results, discovered_emails = self.run_email_discovery(
                preliminary_identity,
                skip_pattern_generation=True,
                skip_public_records=True
            )
        else:
            # FULL MODE: Run everything
            self.logger.info("="*70)
            self.logger.info(f"🔍 FULL EMAIL ENUMERATION - Only {verified_emails_count} verified emails")
            self.logger.info("🎯 Running complete discovery: patterns, LinkedIn, GitHub, Sherlock, public records")
            self.logger.info("="*70)
            
            email_results, discovered_emails = self.run_email_discovery(preliminary_identity)
        all_results['results']['email_discovery'] = email_results
        
        # Merge breach-verified emails into discovered_emails (they're HIGH CONFIDENCE!)
        if verified_breach_emails:
            discovered_emails = list(set(discovered_emails + verified_breach_emails))
            self.logger.info(f"📧 Total emails (including {len(verified_breach_emails)} breach-verified): {len(discovered_emails)}")

        # 5. PhoneInfoga scan
        phone_data = self.run_phoneinfoga()
        all_results['results']['phoneinfoga'] = phone_data

        # 6. Employment intelligence - enhanced with breach-verified usernames
        employment_results = self.run_employment_intelligence(preliminary_identity)
        all_results['results']['employment_intelligence'] = employment_results

        # 7. Google dorking with verified data
        google_results = self.run_google_dorking(phone_data, preliminary_identity)
        all_results['results']['google_dorking'] = google_results

        # 🎯 ENRICHMENT CYCLE 2: Add ALL discoveries including breach-verified data
        mid_investigation_identity = self._build_enriched_identity(
            name_results=name_hunting_results,
            email_results=email_results,
            discovered_emails=discovered_emails,  # Includes breach-verified emails
            employment_results=employment_results,
            original_identity=identity_data
        )
        self.logger.info(f"🎯 Phase 2 enrichment - Breach-verified + discovered data combined")

        # 8. Enhanced social media scan - searches with VERIFIED breach usernames!
        social_results = self.run_social_media_scan(discovered_emails, mid_investigation_identity)
        all_results['results']['social_media'] = social_results

        # 🎯 ENRICHMENT CYCLE 3: Add social media discoveries
        post_social_identity = self._build_enriched_identity(
            name_results=name_hunting_results,
            email_results=email_results,
            discovered_emails=discovered_emails,
            social_results=social_results,
            original_identity=identity_data
        )
        
        # Extract new emails discovered during social media scan
        updated_emails = post_social_identity.get('emails', [])
        if len(updated_emails) > len(discovered_emails):
            self.logger.info(f"🔥 Social media discovered {len(updated_emails) - len(discovered_emails)} additional emails!")
            discovered_emails = updated_emails
        
        # 8. Secondary email discovery with social media enrichment (if new data found)
        if len(post_social_identity.get('usernames', [])) > 0 or len(post_social_identity.get('companies', [])) > 0:
            self.logger.info("🔄 Running secondary email discovery with social media enrichment...")
            secondary_email_results, secondary_emails = self.run_email_discovery(post_social_identity)
            
            # Merge with primary email results
            if secondary_email_results.get('found'):
                # Add new emails to the main email results
                all_results['results']['email_discovery']['emails'].extend(secondary_email_results.get('emails', []))
                all_results['results']['email_discovery']['verified_emails'].extend(secondary_email_results.get('verified_emails', []))
                
                # Update methods used
                new_methods = secondary_email_results.get('methods_used', [])
                existing_methods = all_results['results']['email_discovery'].get('methods_used', [])
                all_results['results']['email_discovery']['methods_used'] = list(set(existing_methods + new_methods))
                
                # Update found status
                all_results['results']['email_discovery']['found'] = True
                
                # Update discovered_emails for breach checking
                if secondary_emails:
                    new_unique_emails = [e for e in secondary_emails if e not in discovered_emails]
                    if new_unique_emails:
                        discovered_emails.extend(new_unique_emails)
                        self.logger.info(f"🔥 Secondary email hunt found {len(new_unique_emails)} additional emails!")

        # 🎯 FINAL ENRICHMENT: Build complete identity context with all discoveries
        final_enriched_identity = self._build_enriched_identity(
            name_results=name_hunting_results,
            email_results=email_results,
            discovered_emails=discovered_emails,
            social_results=social_results,
            employment_results=employment_results,
            original_identity=identity_data
        )

        # 9. REMOVED: Breach check moved to step 3 (BEFORE email discovery for better flow!)
        # Breach search now happens FIRST to discover verified emails/usernames
        # Those verified items inform ALL downstream searches

        # 10. Carrier analysis (using validation data)
        carrier_name = validation_results.get('summary', {}).get('carrier')
        if carrier_name and carrier_name != 'Unknown':
            carrier_results = self.run_carrier_analysis(carrier_name)
            all_results['results']['carrier_analysis'] = carrier_results

        # 11. Intelligent risk assessment with full enriched context
        risk_assessment = self.run_risk_assessment(all_results)
        all_results['results']['risk_assessment'] = risk_assessment

        # Store final enriched identity for potential future use
        all_results['enriched_identity'] = final_enriched_identity

        # 12. Generate comprehensive report
        report_path = self.generate_report(all_results)

        # Save complete results
        complete_file = self.output_dir / "complete_results.json"
        with open(complete_file, 'w', encoding='utf-8') as f:
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