#!/usr/bin/env python3
"""
Phone Number Validation Module
Uses NumVerify and Twilio APIs to validate and gather carrier information
"""
import os
import requests
import logging
from twilio.rest import Client
from dotenv import load_dotenv
from .api_utils import NumVerifyClient

load_dotenv('config/.env')

class PhoneValidator:
    def __init__(self, phone_number):
        self.phone = phone_number
        self.logger = logging.getLogger(__name__)

        # API credentials
        self.numverify_key = os.getenv('NUMVERIFY_API_KEY')
        self.twilio_sid = os.getenv('TWILIO_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')

        # Rate-limited API clients
        self.numverify_client = NumVerifyClient(self.numverify_key)

    def validate_with_numverify(self):
        """Validate phone number using NumVerify API"""
        if not self.numverify_key:
            self.logger.warning("NumVerify API key not configured")
            return {}

        try:
            # Remove + from number for NumVerify
            clean_number = self.phone.replace('+', '')

            data = self.numverify_client.validate(clean_number)
            if data is None:
                self.logger.warning(f"NumVerify validation failed for {clean_number}")
                return {'valid': False, 'error': 'NumVerify API call failed'}

            if data.get('valid'):
                self.logger.info(f"NumVerify validation successful: {data.get('carrier', 'Unknown carrier')}")
                return {
                    'valid': data.get('valid', False),
                    'number': data.get('number', ''),
                    'local_format': data.get('local_format', ''),
                    'international_format': data.get('international_format', ''),
                    'country_prefix': data.get('country_prefix', ''),
                    'country_code': data.get('country_code', ''),
                    'country_name': data.get('country_name', ''),
                    'location': data.get('location', ''),
                    'carrier': data.get('carrier', ''),
                    'line_type': data.get('line_type', '')
                }
            else:
                self.logger.warning(f"NumVerify validation failed: {data}")
                return {'valid': False, 'error': 'Number not valid according to NumVerify'}

        except Exception as e:
            self.logger.error(f"NumVerify API error: {e}")
            return {'error': str(e)}

    def validate_with_twilio(self):
        """Validate phone number using Twilio Lookup API - AGGRESSIVE NAME HUNTING"""
        if not self.twilio_sid or not self.twilio_token:
            self.logger.warning("Twilio credentials not configured")
            return {}

        try:
            client = Client(self.twilio_sid, self.twilio_token)
            result = {}

            # Try basic validation first
            try:
                phone_number = client.lookups.v2.phone_numbers(self.phone).fetch()
                result.update({
                    'phone_number': phone_number.phone_number,
                    'national_format': phone_number.national_format,
                    'valid': phone_number.valid,
                    'country_code': phone_number.country_code
                })
                self.logger.info(f"Twilio basic validation successful")
            except Exception as e:
                self.logger.warning(f"Twilio basic validation failed: {e}")
                result['basic_validation_error'] = str(e)

            # AGGRESSIVE NAME HUNTING - Try all available fields
            name_hunting_fields = [
                'caller_name',
                'validation',
                'line_type_intelligence',
                'identity_match'
            ]

            for field in name_hunting_fields:
                try:
                    self.logger.info(f"🎯 HUNTING NAMES with field: {field}")
                    enhanced_lookup = client.lookups.v2.phone_numbers(self.phone).fetch(fields=field)

                    # Extract any name-related information
                    if hasattr(enhanced_lookup, field):
                        field_data = getattr(enhanced_lookup, field)
                        if field_data:
                            result[f'{field}_data'] = field_data
                            self.logger.info(f"💰 NAME HUNT SUCCESS with {field}: {field_data}")

                            # Special handling for different field types
                            if field == 'caller_name' and hasattr(field_data, 'caller_name'):
                                if field_data.caller_name:
                                    result['OWNER_NAME'] = field_data.caller_name
                                    self.logger.info(f"🔥 JACKPOT! OWNER NAME FOUND: {field_data.caller_name}")

                except Exception as e:
                    self.logger.warning(f"Name hunting with {field} failed: {e}")
                    result[f'{field}_error'] = str(e)

            owner_name = result.get('OWNER_NAME', 'Name hunting unsuccessful')
            self.logger.info(f"Twilio name hunt complete: {owner_name}")
            return result

        except Exception as e:
            self.logger.error(f"Twilio API error: {e}")
            return {'error': str(e)}

    def validate_comprehensive(self):
        """Run comprehensive validation using all available APIs"""
        self.logger.info(f"Starting comprehensive validation for: {self.phone}")

        results = {
            'phone_number': self.phone,
            'numverify': {},
            'twilio': {},
            'summary': {}
        }

        # Try NumVerify first
        numverify_result = self.validate_with_numverify()
        results['numverify'] = numverify_result

        # Try Twilio
        twilio_result = self.validate_with_twilio()
        results['twilio'] = twilio_result

        # Create summary from available data
        summary = self.create_summary(numverify_result, twilio_result)
        results['summary'] = summary

        self.logger.info(f"Validation complete. Carrier: {summary.get('carrier', 'Unknown')}")
        return results

    def create_summary(self, numverify_data, twilio_data):
        """Create a summary from all validation sources"""
        summary = {
            'valid': False,
            'carrier': 'Unknown',
            'location': 'Unknown',
            'line_type': 'Unknown',
            'country': 'Unknown',
            'owner_name': 'Unknown',
            'sources_used': []
        }

        # Use NumVerify data if available
        if numverify_data.get('valid'):
            summary.update({
                'valid': True,
                'carrier': numverify_data.get('carrier', 'Unknown'),
                'location': numverify_data.get('location', 'Unknown'),
                'line_type': numverify_data.get('line_type', 'Unknown'),
                'country': numverify_data.get('country_name', 'Unknown')
            })
            summary['sources_used'].append('NumVerify')

        # Supplement with Twilio data (Twilio data is more reliable, so it overrides NumVerify)
        if twilio_data.get('valid'):
            summary['valid'] = True
            if twilio_data.get('country_code'):
                summary['country'] = twilio_data['country_code']

            # Use Twilio line type intelligence data if available (more accurate than NumVerify)
            if 'line_type_intelligence_data' in twilio_data:
                lti_data = twilio_data['line_type_intelligence_data']
                if lti_data.get('carrier_name'):
                    summary['carrier'] = lti_data['carrier_name']
                if lti_data.get('type'):
                    summary['line_type'] = lti_data['type']

            summary['sources_used'].append('Twilio')

        # Extract owner name from Twilio if found
        if twilio_data.get('OWNER_NAME'):
            summary['owner_name'] = twilio_data['OWNER_NAME']
            if 'Twilio Name Hunt' not in summary['sources_used']:
                summary['sources_used'].append('Twilio Name Hunt')

        # Also check caller_name_data for names
        if 'caller_name_data' in twilio_data:
            caller_data = twilio_data['caller_name_data']
            if isinstance(caller_data, dict) and caller_data.get('caller_name'):
                summary['owner_name'] = caller_data['caller_name']
                if 'Twilio Name Hunt' not in summary['sources_used']:
                    summary['sources_used'].append('Twilio Name Hunt')

        # Use fallback if no APIs worked
        if not summary['sources_used']:
            summary.update({
                'carrier': 'Validation Failed',
                'location': 'Unknown',
                'line_type': 'Unknown',
                'country': 'Unknown',
                'error': 'No validation APIs available or working'
            })

        return summary

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python phone_validator.py <phone_number>")
        sys.exit(1)

    phone = sys.argv[1]
    validator = PhoneValidator(phone)
    results = validator.validate_comprehensive()

    print(f"\nValidation Results for {phone}:")
    print(f"Valid: {results['summary']['valid']}")
    print(f"Carrier: {results['summary']['carrier']}")
    print(f"Location: {results['summary']['location']}")
    print(f"Line Type: {results['summary']['line_type']}")
    print(f"Country: {results['summary']['country']}")
    print(f"Sources: {', '.join(results['summary']['sources_used'])}")