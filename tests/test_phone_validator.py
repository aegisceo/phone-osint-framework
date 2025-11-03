#!/usr/bin/env python3
"""
Unit tests for PhoneValidator module
Tests phone number validation and API integration
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.phone_validator import PhoneValidator


class TestPhoneValidatorInitialization:
    """Test PhoneValidator initialization"""

    def test_init_with_phone_number(self):
        """Test that PhoneValidator initializes with phone number"""
        validator = PhoneValidator("+14158586273")
        assert validator.phone == "+14158586273"
        assert hasattr(validator, 'numverify_key')
        assert hasattr(validator, 'logger')

    def test_init_loads_api_key(self):
        """Test that API key is loaded from environment"""
        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'test_key_123'}):
            validator = PhoneValidator("+14158586273")
            assert validator.numverify_key == 'test_key_123'


class TestValidate:
    """Test phone validation functionality"""

    def test_validate_no_api_key(self):
        """Test validation when API key is not configured"""
        with patch.dict(os.environ, {}, clear=True):
            validator = PhoneValidator("+14158586273")
            result = validator.validate()

            assert result['valid'] == False
            assert 'error' in result
            assert result['error'] == 'No API key'

    @patch('scripts.phone_validator.requests.get')
    def test_validate_valid_number(self, mock_get):
        """Test validation of a valid phone number"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'valid': True,
            'number': '14158586273',
            'local_format': '4158586273',
            'international_format': '+14158586273',
            'country_prefix': '+1',
            'country_code': 'US',
            'country_name': 'United States',
            'location': 'California',
            'carrier': 'AT&T Mobility',
            'line_type': 'mobile'
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'test_key'}):
            validator = PhoneValidator("+14158586273")
            result = validator.validate()

            assert result['valid'] == True
            assert result['country_code'] == 'US'
            assert result['carrier'] == 'AT&T Mobility'
            assert result['line_type'] == 'mobile'

    @patch('scripts.phone_validator.requests.get')
    def test_validate_invalid_number(self, mock_get):
        """Test validation of an invalid phone number"""
        # Mock API response for invalid number
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'valid': False,
            'error': {
                'code': 310,
                'info': 'Invalid phone number'
            }
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'test_key'}):
            validator = PhoneValidator("+999999999")
            result = validator.validate()

            assert result['valid'] == False

    @patch('scripts.phone_validator.requests.get')
    def test_validate_api_error(self, mock_get):
        """Test handling of API errors"""
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'test_key'}):
            validator = PhoneValidator("+14158586273")
            result = validator.validate()

            assert result['valid'] == False
            assert 'error' in result

    @patch('scripts.phone_validator.requests.get')
    def test_validate_network_exception(self, mock_get):
        """Test handling of network exceptions"""
        # Mock network error
        mock_get.side_effect = Exception("Connection timeout")

        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'test_key'}):
            validator = PhoneValidator("+14158586273")
            result = validator.validate()

            assert result['valid'] == False
            assert 'error' in result
            assert 'Connection timeout' in result['error']


class TestNumverifyIntegration:
    """Test Numverify API integration"""

    @patch('scripts.phone_validator.requests.get')
    def test_numverify_request_format(self, mock_get):
        """Test that API request is formatted correctly"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'valid': True}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'test_key_123'}):
            validator = PhoneValidator("+14158586273")
            validator.validate()

            # Verify request was made
            assert mock_get.called
            call_args = mock_get.call_args

            # Check URL contains API endpoint
            assert 'numverify' in str(call_args) or 'validate' in str(call_args)

    @patch('scripts.phone_validator.requests.get')
    def test_multiple_validations(self, mock_get):
        """Test multiple validation calls"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'valid': True, 'carrier': 'Test Carrier'}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'test_key'}):
            validator1 = PhoneValidator("+14158586273")
            result1 = validator1.validate()

            validator2 = PhoneValidator("+14155552671")
            result2 = validator2.validate()

            assert mock_get.call_count == 2
            assert result1['valid'] == True
            assert result2['valid'] == True


class TestInternationalNumbers:
    """Test validation of international phone numbers"""

    @patch('scripts.phone_validator.requests.get')
    def test_validate_uk_number(self, mock_get):
        """Test UK phone number validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'valid': True,
            'country_code': 'GB',
            'country_name': 'United Kingdom',
            'carrier': 'British Telecom',
            'line_type': 'mobile'
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'test_key'}):
            validator = PhoneValidator("+442071838750")
            result = validator.validate()

            assert result['valid'] == True
            assert result['country_code'] == 'GB'

    @patch('scripts.phone_validator.requests.get')
    def test_validate_german_number(self, mock_get):
        """Test German phone number validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'valid': True,
            'country_code': 'DE',
            'country_name': 'Germany',
            'carrier': 'Deutsche Telekom',
            'line_type': 'landline'
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'test_key'}):
            validator = PhoneValidator("+4930123456")
            result = validator.validate()

            assert result['valid'] == True
            assert result['country_code'] == 'DE'


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_phone_number(self):
        """Test validation with empty phone number"""
        validator = PhoneValidator("")
        assert validator.phone == ""

    def test_malformed_phone_number(self):
        """Test validation with malformed input"""
        validator = PhoneValidator("not-a-phone")
        assert validator.phone == "not-a-phone"

    @patch('scripts.phone_validator.requests.get')
    def test_phone_with_spaces(self, mock_get):
        """Test phone number with spaces"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'valid': True}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'test_key'}):
            validator = PhoneValidator("+1 415 858 6273")
            result = validator.validate()

            # Validator should handle spaces
            assert 'valid' in result

    @patch('scripts.phone_validator.requests.get')
    def test_phone_with_dashes(self, mock_get):
        """Test phone number with dashes"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'valid': True}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'test_key'}):
            validator = PhoneValidator("+1-415-858-6273")
            result = validator.validate()

            assert 'valid' in result


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios"""

    @patch('scripts.phone_validator.requests.get')
    def test_full_validation_workflow(self, mock_get):
        """Test complete validation workflow"""
        # Mock successful validation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'valid': True,
            'number': '14158586273',
            'local_format': '4158586273',
            'international_format': '+14158586273',
            'country_prefix': '+1',
            'country_code': 'US',
            'country_name': 'United States',
            'location': 'California',
            'carrier': 'Verizon Wireless',
            'line_type': 'mobile'
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'NUMVERIFY_API_KEY': 'production_key'}):
            # Initialize validator
            phone = "+14158586273"
            validator = PhoneValidator(phone)

            # Perform validation
            result = validator.validate()

            # Verify comprehensive result
            assert result['valid'] == True
            assert result['country_code'] == 'US'
            assert result['carrier'] == 'Verizon Wireless'
            assert result['line_type'] == 'mobile'
            assert result['location'] == 'California'
            assert result['international_format'] == '+14158586273'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
