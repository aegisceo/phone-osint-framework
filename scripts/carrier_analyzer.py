#!/usr/bin/env python3
import phonenumbers
from phonenumbers import carrier, geocoder, timezone

class CarrierAnalyzer:
    def __init__(self, phone_number, carrier_name):
        self.phone = phone_number
        self.carrier_name = carrier_name
        
    def analyze(self):
        """Analyze carrier information"""
        try:
            parsed = phonenumbers.parse(self.phone, None)
            
            return {
                'carrier': self.carrier_name,
                'valid_number': phonenumbers.is_valid_number(parsed),
                'possible_number': phonenumbers.is_possible_number(parsed),
                'region': geocoder.description_for_number(parsed, 'en'),
                'timezones': timezone.time_zones_for_number(parsed),
                'number_type': self.get_number_type(parsed)
            }
        except Exception as e:
            return {'error': str(e)}
            
    def get_number_type(self, parsed_number):
        """Get the type of phone number"""
        number_type = phonenumbers.number_type(parsed_number)
        types = {
            0: "FIXED_LINE",
            1: "MOBILE",
            2: "FIXED_LINE_OR_MOBILE",
            3: "TOLL_FREE",
            4: "PREMIUM_RATE",
            5: "SHARED_COST",
            6: "VOIP",
            7: "PERSONAL_NUMBER",
            8: "PAGER",
            9: "UAN",
            10: "VOICEMAIL",
            99: "UNKNOWN"
        }
        return types.get(number_type, "UNKNOWN")