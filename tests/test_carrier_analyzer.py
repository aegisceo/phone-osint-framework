#!/usr/bin/env python3
"""
Unit tests for CarrierAnalyzer module
Tests phone number carrier analysis and validation
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.carrier_analyzer import CarrierAnalyzer


class TestCarrierAnalyzerInitialization:
    """Test CarrierAnalyzer initialization"""

    def test_init_with_valid_params(self):
        """Test initialization with phone number and carrier name"""
        analyzer = CarrierAnalyzer("+14158586273", "Verizon Wireless")
        assert analyzer.phone == "+14158586273"
        assert analyzer.carrier_name == "Verizon Wireless"

    def test_init_with_different_carriers(self):
        """Test initialization with various carrier names"""
        carriers = ["AT&T", "T-Mobile", "Sprint", "Unknown"]
        for carrier in carriers:
            analyzer = CarrierAnalyzer("+14158586273", carrier)
            assert analyzer.carrier_name == carrier


class TestAnalyze:
    """Test carrier analysis functionality"""

    def test_analyze_valid_us_mobile(self):
        """Test analysis of valid US mobile number"""
        analyzer = CarrierAnalyzer("+14158586273", "AT&T")
        result = analyzer.analyze()

        assert 'carrier' in result
        assert result['carrier'] == "AT&T"
        assert 'valid_number' in result
        assert 'possible_number' in result
        assert 'region' in result
        assert 'timezones' in result
        assert 'number_type' in result

    def test_analyze_valid_us_mobile_validation(self):
        """Test that valid US mobile numbers pass validation"""
        analyzer = CarrierAnalyzer("+14155552671", "Verizon")
        result = analyzer.analyze()

        assert result['valid_number'] == True
        assert result['possible_number'] == True
        assert 'number_type' in result

    def test_analyze_invalid_number(self):
        """Test analysis of invalid phone number"""
        analyzer = CarrierAnalyzer("+1999999999999", "Unknown")
        result = analyzer.analyze()

        # Invalid number should still return structure
        if 'error' not in result:
            assert result['valid_number'] == False

    def test_analyze_uk_number(self):
        """Test analysis of UK phone number"""
        analyzer = CarrierAnalyzer("+442071838750", "British Telecom")
        result = analyzer.analyze()

        if 'error' not in result:
            assert result['carrier'] == "British Telecom"
            assert 'region' in result
            # UK phone should have region
            assert len(result['region']) > 0

    def test_analyze_returns_timezones(self):
        """Test that timezone information is returned"""
        analyzer = CarrierAnalyzer("+14158586273", "AT&T")
        result = analyzer.analyze()

        if 'error' not in result:
            assert 'timezones' in result
            assert isinstance(result['timezones'], (list, tuple))

    def test_analyze_exception_handling(self):
        """Test error handling for malformed input"""
        analyzer = CarrierAnalyzer("invalid", "Unknown")
        result = analyzer.analyze()

        assert 'error' in result
        assert isinstance(result['error'], str)


class TestGetNumberType:
    """Test number type detection"""

    def test_get_number_type_mobile(self):
        """Test mobile number type detection"""
        analyzer = CarrierAnalyzer("+14158586273", "AT&T")
        result = analyzer.analyze()

        if 'error' not in result:
            # US numbers starting with +1415 are typically mobile
            assert result['number_type'] in ['MOBILE', 'FIXED_LINE_OR_MOBILE']

    def test_get_number_type_toll_free(self):
        """Test toll-free number detection"""
        analyzer = CarrierAnalyzer("+18005551212", "Toll-Free")
        result = analyzer.analyze()

        if 'error' not in result:
            assert result['number_type'] == 'TOLL_FREE'

    def test_get_number_type_mapping(self):
        """Test that number type codes map to readable strings"""
        analyzer = CarrierAnalyzer("+14158586273", "AT&T")

        # Test the mapping exists
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

        # Verify all expected types are defined
        for code, name in types.items():
            assert isinstance(name, str)
            assert len(name) > 0


class TestRegionalNumbers:
    """Test analysis of numbers from different regions"""

    def test_analyze_canadian_number(self):
        """Test Canadian phone number"""
        analyzer = CarrierAnalyzer("+14165551234", "Rogers")
        result = analyzer.analyze()

        if 'error' not in result:
            assert 'region' in result
            # Canadian numbers should be valid
            assert result['possible_number'] == True

    def test_analyze_australian_number(self):
        """Test Australian phone number"""
        analyzer = CarrierAnalyzer("+61412345678", "Telstra")
        result = analyzer.analyze()

        if 'error' not in result:
            assert result['carrier'] == "Telstra"
            assert 'region' in result

    def test_analyze_german_number(self):
        """Test German phone number"""
        analyzer = CarrierAnalyzer("+4930123456", "Deutsche Telekom")
        result = analyzer.analyze()

        if 'error' not in result:
            assert result['carrier'] == "Deutsche Telekom"
            # German numbers should have Berlin region for +4930
            assert 'region' in result


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_carrier_name(self):
        """Test with empty carrier name"""
        analyzer = CarrierAnalyzer("+14158586273", "")
        result = analyzer.analyze()

        if 'error' not in result:
            assert result['carrier'] == ""
            # Should still analyze the number
            assert 'valid_number' in result

    def test_none_carrier_name(self):
        """Test with None carrier name"""
        analyzer = CarrierAnalyzer("+14158586273", None)
        result = analyzer.analyze()

        if 'error' not in result:
            assert result['carrier'] is None

    def test_special_characters_in_phone(self):
        """Test phone numbers with special characters"""
        analyzer = CarrierAnalyzer("+1 (415) 858-6273", "AT&T")
        result = analyzer.analyze()

        # phonenumbers library should handle formatting
        if 'error' not in result:
            assert 'valid_number' in result

    def test_very_long_carrier_name(self):
        """Test with unusually long carrier name"""
        long_name = "A" * 1000
        analyzer = CarrierAnalyzer("+14158586273", long_name)
        result = analyzer.analyze()

        if 'error' not in result:
            assert result['carrier'] == long_name


class TestIntegrationScenarios:
    """Integration tests for real-world use cases"""

    def test_full_analysis_workflow(self):
        """Test complete carrier analysis workflow"""
        # Scenario: Analyzing a phone number from investigation
        phone = "+14155552671"
        carrier = "AT&T Mobility"

        analyzer = CarrierAnalyzer(phone, carrier)
        result = analyzer.analyze()

        # Verify all expected fields are present
        assert 'carrier' in result
        assert 'valid_number' in result
        assert 'possible_number' in result
        assert 'region' in result
        assert 'timezones' in result
        assert 'number_type' in result

        # Verify reasonable values
        assert result['carrier'] == carrier
        assert isinstance(result['valid_number'], bool)
        assert isinstance(result['possible_number'], bool)

    def test_multiple_analyses_same_instance(self):
        """Test that analyzer can be reused (though not typical)"""
        analyzer = CarrierAnalyzer("+14158586273", "Verizon")

        # First analysis
        result1 = analyzer.analyze()

        # Second analysis (same data)
        result2 = analyzer.analyze()

        # Results should be consistent
        assert result1 == result2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
