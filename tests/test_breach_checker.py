#!/usr/bin/env python3
"""
Unit tests for BreachChecker module
Tests the Have I Been Pwned integration and breach checking functionality
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.breach_checker import BreachChecker


class TestBreachCheckerInitialization:
    """Test BreachChecker class initialization"""

    def test_init_with_phone_number(self):
        """Test that BreachChecker initializes with phone number"""
        checker = BreachChecker("+14158586273")
        assert checker.phone == "+14158586273"
        assert hasattr(checker, 'hibp_key')
        assert hasattr(checker, 'logger')

    def test_init_loads_env_key(self):
        """Test that API key is loaded from environment"""
        with patch.dict(os.environ, {'HAVEIBEENPWNED_API_KEY': 'test_key_123'}):
            checker = BreachChecker("+14158586273")
            assert checker.hibp_key == 'test_key_123'


class TestCheckHIBP:
    """Test Have I Been Pwned API integration"""

    def test_check_hibp_no_api_key(self):
        """Test behavior when API key is not configured"""
        with patch.dict(os.environ, {}, clear=True):
            checker = BreachChecker("+14158586273")
            result = checker.check_hibp("test@example.com")

            assert result['found'] == False
            assert result['error'] == 'No API key'
            assert 'breaches' in result

    def test_check_hibp_no_email_provided(self):
        """Test behavior when no email is provided"""
        checker = BreachChecker("+14158586273")
        result = checker.check_hibp(None)

        assert result['found'] == False
        assert 'note' in result
        assert result['note'] == 'No email provided for HIBP check'

    @patch('scripts.breach_checker.requests.get')
    def test_check_hibp_breach_found(self, mock_get):
        """Test successful breach detection"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'Name': 'Adobe', 'BreachDate': '2013-10-04'},
            {'Name': 'LinkedIn', 'BreachDate': '2012-05-05'},
            {'Name': 'Dropbox', 'BreachDate': '2012-07-01'}
        ]
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'HAVEIBEENPWNED_API_KEY': 'test_key'}):
            checker = BreachChecker("+14158586273")
            result = checker.check_hibp("pwned@example.com")

            assert result['found'] == True
            assert result['email'] == "pwned@example.com"
            assert result['breach_count'] == 3
            assert 'Adobe' in result['breaches']
            assert 'LinkedIn' in result['breaches']

    @patch('scripts.breach_checker.requests.get')
    def test_check_hibp_no_breach_found(self, mock_get):
        """Test when email is not in breaches"""
        # Mock 404 response (not found)
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'HAVEIBEENPWNED_API_KEY': 'test_key'}):
            checker = BreachChecker("+14158586273")
            result = checker.check_hibp("clean@example.com")

            assert result['found'] == False
            assert result['email'] == "clean@example.com"
            assert 'message' in result

    @patch('scripts.breach_checker.requests.get')
    def test_check_hibp_api_error(self, mock_get):
        """Test handling of API errors"""
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'HAVEIBEENPWNED_API_KEY': 'test_key'}):
            checker = BreachChecker("+14158586273")
            result = checker.check_hibp("error@example.com")

            assert result['found'] == False
            assert 'error' in result
            assert 'HTTP 500' in result['error']

    @patch('scripts.breach_checker.requests.get')
    def test_check_hibp_network_exception(self, mock_get):
        """Test handling of network exceptions"""
        # Mock network error
        mock_get.side_effect = Exception("Network timeout")

        with patch.dict(os.environ, {'HAVEIBEENPWNED_API_KEY': 'test_key'}):
            checker = BreachChecker("+14158586273")
            result = checker.check_hibp("test@example.com")

            assert result['found'] == False
            assert 'error' in result
            assert 'Network timeout' in result['error']


class TestCheckAllSources:
    """Test comprehensive breach checking across all sources"""

    def test_check_all_sources_no_emails(self):
        """Test when no emails are provided"""
        checker = BreachChecker("+14158586273")
        result = checker.check_all_sources(None)

        assert result['found'] == False
        assert 'sources_checked' in result
        assert 'haveibeenpwned' in result['sources_checked']
        assert 'note' in result

    @patch('scripts.breach_checker.requests.get')
    def test_check_all_sources_multiple_emails(self, mock_get):
        """Test checking multiple email addresses"""
        # Mock responses for different emails
        def side_effect(*args, **kwargs):
            url = args[0]
            mock_response = Mock()
            if 'pwned@' in url:
                mock_response.status_code = 200
                mock_response.json.return_value = [
                    {'Name': 'Adobe', 'BreachDate': '2013-10-04'}
                ]
            else:
                mock_response.status_code = 404
            return mock_response

        mock_get.side_effect = side_effect

        with patch.dict(os.environ, {'HAVEIBEENPWNED_API_KEY': 'test_key'}):
            checker = BreachChecker("+14158586273")
            emails = ['clean@example.com', 'pwned@example.com']
            result = checker.check_all_sources(emails)

            assert result['found'] == True  # At least one breach found
            assert len(result['emails_checked']) == 2
            assert 'Adobe' in result['breaches']

    def test_check_all_sources_empty_list(self):
        """Test with empty email list"""
        checker = BreachChecker("+14158586273")
        result = checker.check_all_sources([])

        # Empty list should iterate over nothing, resulting in no breaches
        assert result['found'] == False
        assert len(result['emails_checked']) == 0


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios"""

    @patch('scripts.breach_checker.requests.get')
    def test_full_investigation_workflow(self, mock_get):
        """Test complete investigation workflow"""
        # Mock breach found
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'Name': 'Collection1', 'BreachDate': '2019-01-07'}
        ]
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {'HAVEIBEENPWNED_API_KEY': 'test_key'}):
            # Initialize checker
            phone = "+14158586273"
            checker = BreachChecker(phone)

            # Perform check
            emails = ["potential@email.com"]
            result = checker.check_all_sources(emails)

            # Verify results
            assert result['found'] == True
            assert len(result['emails_checked']) == 1
            assert 'Collection1' in result['breaches']
            assert result['sources_checked'] == ['haveibeenpwned']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
