#!/usr/bin/env python3
"""
WhitePages Integration for Professional Name Hunting
Official API integration for reliable phone number owner identification
"""

import requests
import logging
import os
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv('config/.env')

class WhitePagesHunter:
    """
    WhitePages API integration for phone number owner identification
    Professional-grade name hunting with official API
    """

    def __init__(self, phone_number: str):
        self.phone = phone_number
        self.logger = logging.getLogger(__name__)

        # API credentials
        self.api_key = os.getenv('WHITEPAGES_API_KEY')
        self.base_url = "https://proapi.whitepages.com/3.0"

        if not self.api_key:
            self.logger.warning("WhitePages API key not configured")

    def hunt_phone_lookup(self) -> Dict:
        """
        Perform phone lookup via WhitePages Phone API
        """
        if not self.api_key:
            return {'error': 'WhitePages API key not configured', 'found': False}

        self.logger.info("🎯 Starting WhitePages phone lookup...")

        try:
            url = f"{self.base_url}/phone"
            params = {
                'phone': self.phone,
                'api_key': self.api_key
            }

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            results = {
                'found': False,
                'names': [],
                'carriers': [],
                'locations': [],
                'line_type': None,
                'confidence': 0.0,
                'raw_data': data
            }

            # Parse phone data
            if 'results' in data and data['results']:
                phone_result = data['results'][0]

                # Extract line type and carrier
                if 'line_type' in phone_result:
                    results['line_type'] = phone_result['line_type']

                if 'carrier' in phone_result:
                    results['carriers'].append(phone_result['carrier'])

                # Extract associated person data
                if 'belongs_to' in phone_result:
                    for person in phone_result['belongs_to']:
                        person_data = self._extract_person_data(person)
                        if person_data['names']:
                            results['names'].extend(person_data['names'])
                            results['found'] = True
                        if person_data['locations']:
                            results['locations'].extend(person_data['locations'])

                # Calculate confidence based on data quality
                results['confidence'] = self._calculate_confidence(results)

                if results['found']:
                    self.logger.info(f"💰 WhitePages SUCCESS: {len(results['names'])} names found")
                else:
                    self.logger.warning("WhitePages lookup returned no names")

            return results

        except requests.exceptions.RequestException as e:
            self.logger.error(f"WhitePages API request error: {e}")
            return {'error': str(e), 'found': False}
        except Exception as e:
            self.logger.error(f"WhitePages processing error: {e}")
            return {'error': str(e), 'found': False}

    def hunt_reverse_phone(self) -> Dict:
        """
        Perform reverse phone lookup for enhanced results
        """
        if not self.api_key:
            return {'error': 'WhitePages API key not configured', 'found': False}

        self.logger.info("🎯 Starting WhitePages reverse phone lookup...")

        try:
            url = f"{self.base_url}/phone_intelligence"
            params = {
                'phone': self.phone,
                'api_key': self.api_key
            }

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            results = {
                'found': False,
                'caller_id_name': None,
                'spam_score': 0,
                'is_valid': False,
                'country_code': None,
                'carrier': None,
                'line_type': None,
                'confidence': 0.0,
                'raw_data': data
            }

            if 'results' in data and data['results']:
                intel_result = data['results'][0]

                # Extract caller ID name (THE GRAIL!)
                if 'caller_id_name' in intel_result:
                    results['caller_id_name'] = intel_result['caller_id_name']
                    if results['caller_id_name']:
                        results['found'] = True

                # Extract phone intelligence
                if 'is_valid' in intel_result:
                    results['is_valid'] = intel_result['is_valid']

                if 'country_calling_code' in intel_result:
                    results['country_code'] = intel_result['country_calling_code']

                if 'carrier' in intel_result:
                    results['carrier'] = intel_result['carrier']

                if 'line_type' in intel_result:
                    results['line_type'] = intel_result['line_type']

                if 'reputation' in intel_result:
                    rep_data = intel_result['reputation']
                    if 'spam_score' in rep_data:
                        results['spam_score'] = rep_data['spam_score']

                # Calculate confidence
                results['confidence'] = self._calculate_intel_confidence(results)

                if results['found']:
                    self.logger.info(f"🔥 WhitePages Intelligence SUCCESS: Caller ID = {results['caller_id_name']}")

            return results

        except requests.exceptions.RequestException as e:
            self.logger.error(f"WhitePages Intelligence API error: {e}")
            return {'error': str(e), 'found': False}
        except Exception as e:
            self.logger.error(f"WhitePages Intelligence processing error: {e}")
            return {'error': str(e), 'found': False}

    def _extract_person_data(self, person_data: Dict) -> Dict:
        """
        Extract names and locations from person data
        """
        extracted = {
            'names': [],
            'locations': []
        }

        try:
            # Extract names
            if 'name' in person_data:
                name_data = person_data['name']
                full_name_parts = []

                if 'first_name' in name_data and name_data['first_name']:
                    full_name_parts.append(name_data['first_name'])
                if 'middle_name' in name_data and name_data['middle_name']:
                    full_name_parts.append(name_data['middle_name'])
                if 'last_name' in name_data and name_data['last_name']:
                    full_name_parts.append(name_data['last_name'])

                if full_name_parts:
                    full_name = ' '.join(full_name_parts)
                    extracted['names'].append(full_name)

            # Extract current addresses
            if 'current_addresses' in person_data:
                for address in person_data['current_addresses']:
                    if 'location_details' in address:
                        loc_details = address['location_details']
                        location_parts = []

                        if 'city' in loc_details and loc_details['city']:
                            location_parts.append(loc_details['city'])
                        if 'state_code' in loc_details and loc_details['state_code']:
                            location_parts.append(loc_details['state_code'])

                        if location_parts:
                            location = ', '.join(location_parts)
                            extracted['locations'].append(location)

        except Exception as e:
            self.logger.warning(f"Error extracting person data: {e}")

        return extracted

    def _calculate_confidence(self, results: Dict) -> float:
        """
        Calculate confidence score based on data quality
        """
        confidence = 0.0

        if results['names']:
            confidence += 0.6  # Base confidence for having names

        if results['carriers']:
            confidence += 0.1

        if results['locations']:
            confidence += 0.1

        if results['line_type']:
            confidence += 0.1

        # Multiple names increase confidence
        if len(results['names']) > 1:
            confidence += 0.1

        return min(confidence, 1.0)

    def _calculate_intel_confidence(self, results: Dict) -> float:
        """
        Calculate confidence for intelligence data
        """
        confidence = 0.0

        if results['caller_id_name']:
            confidence += 0.8  # High confidence for caller ID

        if results['is_valid']:
            confidence += 0.1

        if results['carrier']:
            confidence += 0.05

        if results['line_type']:
            confidence += 0.05

        return min(confidence, 1.0)

    def hunt_comprehensive(self) -> Dict:
        """
        Run comprehensive WhitePages hunting using all available endpoints
        """
        self.logger.info(f"🚀 Starting comprehensive WhitePages hunting for: {self.phone}")

        comprehensive_results = {
            'found': False,
            'names': [],
            'caller_id_name': None,
            'carriers': [],
            'locations': [],
            'line_type': None,
            'spam_score': 0,
            'is_valid': False,
            'best_confidence': 0.0,
            'methods_used': [],
            'detailed_results': {}
        }

        # Method 1: Standard phone lookup
        lookup_results = self.hunt_phone_lookup()
        if not lookup_results.get('error'):
            comprehensive_results['methods_used'].append('phone_lookup')
            comprehensive_results['detailed_results']['phone_lookup'] = lookup_results

            if lookup_results['found']:
                comprehensive_results['found'] = True
                comprehensive_results['names'].extend(lookup_results['names'])
                comprehensive_results['carriers'].extend(lookup_results['carriers'])
                comprehensive_results['locations'].extend(lookup_results['locations'])
                if lookup_results['line_type']:
                    comprehensive_results['line_type'] = lookup_results['line_type']
                comprehensive_results['best_confidence'] = max(
                    comprehensive_results['best_confidence'],
                    lookup_results['confidence']
                )

        # Method 2: Phone intelligence lookup
        intel_results = self.hunt_reverse_phone()
        if not intel_results.get('error'):
            comprehensive_results['methods_used'].append('phone_intelligence')
            comprehensive_results['detailed_results']['phone_intelligence'] = intel_results

            if intel_results['found']:
                comprehensive_results['found'] = True
                comprehensive_results['caller_id_name'] = intel_results['caller_id_name']

                # Add caller ID name to names list if not already present
                if intel_results['caller_id_name']:
                    caller_name = intel_results['caller_id_name'].strip()
                    if caller_name not in comprehensive_results['names']:
                        comprehensive_results['names'].append(caller_name)

            # Update additional intel data
            if intel_results['carrier'] and intel_results['carrier'] not in comprehensive_results['carriers']:
                comprehensive_results['carriers'].append(intel_results['carrier'])

            if intel_results['line_type'] and not comprehensive_results['line_type']:
                comprehensive_results['line_type'] = intel_results['line_type']

            comprehensive_results['spam_score'] = intel_results['spam_score']
            comprehensive_results['is_valid'] = intel_results['is_valid']

            comprehensive_results['best_confidence'] = max(
                comprehensive_results['best_confidence'],
                intel_results['confidence']
            )

        # Remove duplicates
        comprehensive_results['names'] = list(set(comprehensive_results['names']))
        comprehensive_results['carriers'] = list(set(comprehensive_results['carriers']))
        comprehensive_results['locations'] = list(set(comprehensive_results['locations']))

        # Final summary
        if comprehensive_results['found']:
            self.logger.info(f"🎯 WHITEPAGES HUNT COMPLETE: {len(comprehensive_results['names'])} names, confidence: {comprehensive_results['best_confidence']:.2f}")
            if comprehensive_results['caller_id_name']:
                self.logger.info(f"🔥 CALLER ID JACKPOT: {comprehensive_results['caller_id_name']}")
        else:
            self.logger.warning("❌ WhitePages hunting unsuccessful")

        return comprehensive_results


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python whitepages_hunter.py <phone_number>")
        sys.exit(1)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    phone = sys.argv[1]
    hunter = WhitePagesHunter(phone)
    results = hunter.hunt_comprehensive()

    print(f"\n🎯 WhitePages Results for {phone}:")
    print(f"Found: {results['found']}")
    print(f"Names: {results['names']}")
    print(f"Caller ID: {results['caller_id_name']}")
    print(f"Confidence: {results['best_confidence']:.2f}")
    print(f"Methods: {', '.join(results['methods_used'])}")