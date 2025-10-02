#!/usr/bin/env python3
"""
Email Validation Module
Validates email addresses using DNS MX records and optional SMTP checks
"""

import re
import dns.resolver
import smtplib
import socket
import logging
from typing import Dict, List, Optional
from email.utils import parseaddr

class EmailValidator:
    """
    Email validation using DNS and SMTP checks
    - DNS MX record validation (fast, reliable)
    - SMTP deliverability check (optional, can be slow)
    - Syntax validation
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.dns_cache = {}  # Cache DNS lookups

    def validate_syntax(self, email: str) -> bool:
        """Basic email syntax validation"""
        if not email or '@' not in email:
            return False

        # RFC 5322 compliant regex (simplified)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def check_dns_mx(self, domain: str) -> Dict:
        """
        Check if domain has valid MX records
        Returns dict with validation status and MX servers
        """
        # Check cache first
        if domain in self.dns_cache:
            return self.dns_cache[domain]

        result = {
            'valid': False,
            'mx_records': [],
            'error': None
        }

        try:
            # Query MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            result['mx_records'] = [str(r.exchange).rstrip('.') for r in mx_records]
            result['valid'] = len(result['mx_records']) > 0

            if result['valid']:
                self.logger.debug(f"✓ Domain {domain} has {len(result['mx_records'])} MX records")

        except dns.resolver.NXDOMAIN:
            result['error'] = 'Domain does not exist'
            self.logger.debug(f"✗ Domain {domain} does not exist")
        except dns.resolver.NoAnswer:
            result['error'] = 'No MX records found'
            self.logger.debug(f"✗ Domain {domain} has no MX records")
        except dns.resolver.Timeout:
            result['error'] = 'DNS query timeout'
            self.logger.debug(f"⚠ DNS timeout for domain {domain}")
        except Exception as e:
            result['error'] = str(e)
            self.logger.debug(f"✗ DNS error for {domain}: {e}")

        # Cache result (5 min TTL in production, infinite for this session)
        self.dns_cache[domain] = result
        return result

    def check_smtp_deliverability(self, email: str, timeout: int = 10) -> Dict:
        """
        Check if email address accepts mail via SMTP (VRFY/RCPT TO)
        WARNING: This can be slow and may trigger rate limits
        Use sparingly!
        """
        result = {
            'deliverable': False,
            'smtp_code': None,
            'smtp_message': None,
            'method': None,
            'error': None
        }

        domain = email.split('@')[1]
        mx_check = self.check_dns_mx(domain)

        if not mx_check['valid']:
            result['error'] = f"No valid MX records: {mx_check.get('error')}"
            return result

        # Try primary MX server
        mx_server = mx_check['mx_records'][0]

        try:
            # Connect to mail server
            server = smtplib.SMTP(timeout=timeout)
            server.set_debuglevel(0)

            self.logger.debug(f"Connecting to {mx_server}:25...")
            code, message = server.connect(mx_server, 25)

            if code != 220:
                result['error'] = f"SMTP connection failed: {code}"
                server.quit()
                return result

            # HELO/EHLO
            server.ehlo_or_helo_if_needed()

            # MAIL FROM (use a generic sender)
            server.mail('validator@example.com')

            # RCPT TO (check if recipient exists)
            code, message = server.rcpt(email)
            result['smtp_code'] = code
            result['smtp_message'] = message.decode() if isinstance(message, bytes) else str(message)

            # 250 = OK, 251 = forwarding, 252 = cannot verify (but accepting)
            if code in [250, 251, 252]:
                result['deliverable'] = True
                result['method'] = 'RCPT TO'
                self.logger.debug(f"✓ {email} appears deliverable (code {code})")
            else:
                result['error'] = f"SMTP rejected: {code} {message}"
                self.logger.debug(f"✗ {email} rejected (code {code})")

            server.quit()

        except smtplib.SMTPServerDisconnected:
            result['error'] = "Server disconnected"
        except smtplib.SMTPResponseException as e:
            result['smtp_code'] = e.smtp_code
            result['smtp_message'] = e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
            result['error'] = f"SMTP error: {e.smtp_code}"
        except socket.timeout:
            result['error'] = "Connection timeout"
        except Exception as e:
            result['error'] = f"SMTP check failed: {type(e).__name__}: {e}"
            self.logger.debug(f"SMTP check error for {email}: {e}")

        return result

    def validate_email(self, email: str, check_smtp: bool = False) -> Dict:
        """
        Complete email validation

        Args:
            email: Email address to validate
            check_smtp: Whether to perform SMTP deliverability check (slow!)

        Returns:
            Dict with validation results and confidence score
        """
        result = {
            'email': email,
            'valid': False,
            'confidence': 0.0,
            'checks': {
                'syntax': False,
                'dns_mx': False,
                'smtp_deliverable': None  # None = not checked
            },
            'status': 'unknown',
            'mx_records': [],
            'errors': []
        }

        # 1. Syntax validation
        if not self.validate_syntax(email):
            result['status'] = 'invalid_syntax'
            result['errors'].append('Invalid email syntax')
            return result

        result['checks']['syntax'] = True

        # 2. Extract domain
        try:
            domain = email.split('@')[1].lower()
        except IndexError:
            result['status'] = 'invalid_format'
            result['errors'].append('Cannot extract domain')
            return result

        # 3. DNS MX record check
        mx_check = self.check_dns_mx(domain)
        result['checks']['dns_mx'] = mx_check['valid']
        result['mx_records'] = mx_check.get('mx_records', [])

        if not mx_check['valid']:
            result['status'] = 'no_mx_records'
            result['errors'].append(mx_check.get('error', 'No MX records'))
            return result

        # At this point: valid syntax + valid MX records = likely valid
        result['valid'] = True
        result['confidence'] = 0.7  # 70% confidence with DNS only
        result['status'] = 'likely_valid'

        # 4. Optional SMTP deliverability check
        if check_smtp:
            smtp_check = self.check_smtp_deliverability(email)
            result['checks']['smtp_deliverable'] = smtp_check['deliverable']

            if smtp_check['deliverable']:
                result['confidence'] = 0.95  # 95% confidence with SMTP verification
                result['status'] = 'verified'
            elif smtp_check['error']:
                result['errors'].append(f"SMTP: {smtp_check['error']}")
                # Keep likely_valid status (DNS passed, SMTP inconclusive)

        return result

    def validate_batch(self, emails: List[str], check_smtp: bool = False, max_smtp_checks: int = 5) -> List[Dict]:
        """
        Validate multiple emails efficiently

        Args:
            emails: List of email addresses
            check_smtp: Whether to perform SMTP checks
            max_smtp_checks: Maximum number of SMTP checks (rate limiting)

        Returns:
            List of validation results
        """
        results = []
        smtp_checks_done = 0

        for email in emails:
            # Skip SMTP check if we've hit the limit
            do_smtp = check_smtp and smtp_checks_done < max_smtp_checks

            result = self.validate_email(email, check_smtp=do_smtp)

            if do_smtp and result['checks']['smtp_deliverable'] is not None:
                smtp_checks_done += 1

            results.append(result)

        self.logger.info(f"Validated {len(emails)} emails (DNS: {len(emails)}, SMTP: {smtp_checks_done})")
        return results


if __name__ == "__main__":
    # Test validation
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    validator = EmailValidator()

    print("=" * 60)
    print("Email Validator Test")
    print("=" * 60)

    test_emails = [
        'test@gmail.com',           # Valid domain
        'invalid@nonexistentdomain123456.com',  # Invalid domain
        'bad-email',                 # Bad syntax
        'user@yahoo.com',            # Valid domain
    ]

    for email in test_emails:
        print(f"\nTesting: {email}")
        result = validator.validate_email(email, check_smtp=False)
        print(f"  Valid: {result['valid']}")
        print(f"  Status: {result['status']}")
        print(f"  Confidence: {result['confidence']:.0%}")
        if result['mx_records']:
            print(f"  MX Records: {len(result['mx_records'])}")
        if result['errors']:
            print(f"  Errors: {', '.join(result['errors'])}")
