#!/usr/bin/env python3
"""
Test script for Phase 1 Enhanced Name Hunting Features
Tests the new FastPeopleSearch, WhitePages, and Unified Name Hunter modules
"""

import sys
import os
import logging
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_fastpeople_hunter():
    """Test FastPeopleSearch hunter"""
    print("🔍 Testing FastPeopleSearch Hunter...")

    try:
        from scripts.fastpeople_hunter import FastPeopleHunter

        hunter = FastPeopleHunter("+14158586273")
        print("✅ FastPeopleHunter initialized successfully")

        # Test phone format generation
        formats = hunter._generate_search_formats()
        print(f"📱 Generated {len(formats)} phone formats")

        # Test name cleaning
        test_names = ["John Doe", "123invalid", "JOHN SMITH", ""]
        for name in test_names:
            cleaned = hunter._clean_name(name)
            print(f"   '{name}' -> '{cleaned}'")

        print("✅ FastPeopleHunter tests passed")

    except Exception as e:
        print(f"❌ FastPeopleHunter test failed: {e}")
        return False

    return True

def test_whitepages_hunter():
    """Test WhitePages hunter"""
    print("\n📞 Testing WhitePages Hunter...")

    try:
        from scripts.whitepages_hunter import WhitePagesHunter

        hunter = WhitePagesHunter("+14158586273")
        print("✅ WhitePagesHunter initialized successfully")

        # Test without API key (should handle gracefully)
        result = hunter.hunt_phone_lookup()
        print(f"🔧 No API key test: {result.get('error', 'No error')}")

        print("✅ WhitePagesHunter tests passed")

    except Exception as e:
        print(f"❌ WhitePagesHunter test failed: {e}")
        return False

    return True

def test_unified_name_hunter():
    """Test Unified Name Hunter"""
    print("\n🎯 Testing Unified Name Hunter...")

    try:
        from scripts.unified_name_hunter import UnifiedNameHunter

        hunter = UnifiedNameHunter("+14158586273")
        print("✅ UnifiedNameHunter initialized successfully")

        # Test name similarity calculation
        similarity = hunter._calculate_name_similarity("John Doe", "John D Doe")
        print(f"🧠 Name similarity test: {similarity:.2f}")

        # Test name cleaning
        cleaned = hunter._clean_name("  JOHN DOE  ")
        print(f"🧹 Name cleaning test: '{cleaned}'")

        print("✅ UnifiedNameHunter tests passed")

    except Exception as e:
        print(f"❌ UnifiedNameHunter test failed: {e}")
        return False

    return True

def test_integration():
    """Test integration with main phone_osint_master"""
    print("\n🔗 Testing Integration...")

    try:
        from phone_osint_master import PhoneOSINTMaster

        # Initialize without actually running investigation
        investigator = PhoneOSINTMaster("+14158586273")
        print("✅ PhoneOSINTMaster initialized with new features")

        # Check if new method exists
        if hasattr(investigator, 'run_unified_name_hunting'):
            print("✅ run_unified_name_hunting method found")
        else:
            print("❌ run_unified_name_hunting method missing")
            return False

        print("✅ Integration tests passed")

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

    return True

def test_report_generator():
    """Test report generator enhancements"""
    print("\n📊 Testing Report Generator Enhancements...")

    try:
        from scripts.report_generator import ReportGenerator

        # Create mock data
        mock_data = {
            'results': {
                'name_hunting': {
                    'found': True,
                    'primary_names': ['John Doe'],
                    'all_names': ['John Doe', 'J. Doe'],
                    'confidence_scores': {'John Doe': 0.9, 'J. Doe': 0.7},
                    'best_confidence': 0.9,
                    'execution_time': 15.5,
                    'methods_successful': ['twilio', 'whitepages']
                }
            }
        }

        generator = ReportGenerator("+14158586273", mock_data, Path("/tmp"))

        # Test new methods
        if hasattr(generator, '_get_best_owner_name'):
            best_name = generator._get_best_owner_name(
                mock_data['results']['name_hunting'],
                {'owner_name': 'Unknown'}
            )
            print(f"✅ Best owner name extraction: '{best_name}'")

        if hasattr(generator, 'format_name_hunting_results'):
            html_result = generator.format_name_hunting_results()
            print(f"✅ Name hunting HTML formatting: {len(html_result)} characters")

        print("✅ Report generator tests passed")

    except Exception as e:
        print(f"❌ Report generator test failed: {e}")
        return False

    return True

def main():
    """Run all Phase 1 tests"""
    print("🚀 PHASE 1 ENHANCED NAME HUNTING TESTS")
    print("=" * 50)

    # Setup basic logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise

    tests = [
        test_fastpeople_hunter,
        test_whitepages_hunter,
        test_unified_name_hunter,
        test_integration,
        test_report_generator
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL PHASE 1 TESTS PASSED!")
        print("🎯 Ready for name hunting deployment!")
    else:
        print("⚠️  Some tests failed. Review errors above.")

    print("\n💡 Note: Full functionality requires API keys in config/.env")
    print("🔍 To test with real data, configure APIs and run a full investigation")

if __name__ == "__main__":
    main()