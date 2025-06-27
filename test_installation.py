#!/usr/bin/env python3
"""
Installation test script for AI-Based Data Cleaner
Run this script to verify that all components are working correctly.
"""

import sys
import os
import traceback
from typing import Dict, List

def test_imports() -> Dict[str, bool]:
    """Test if all required packages can be imported"""
    
    results = {}
    required_packages = [
        'streamlit',
        'pandas', 
        'numpy',
        'openai',
        'openpyxl',
        'xlrd',
        'plotly',
        'python-dotenv'
    ]
    
    print("🔍 Testing package imports...")
    
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            else:
                __import__(package)
            results[package] = True
            print(f"  ✅ {package}")
        except ImportError as e:
            results[package] = False
            print(f"  ❌ {package}: {str(e)}")
    
    return results

def test_configuration() -> Dict[str, bool]:
    """Test configuration and environment setup"""
    
    results = {}
    
    print("\n🔧 Testing configuration...")
    
    # Test .env file exists
    env_exists = os.path.exists('.env')
    results['env_file'] = env_exists
    if env_exists:
        print("  ✅ .env file found")
    else:
        print("  ❌ .env file not found")
    
    # Test config import
    try:
        from config import Config
        results['config_import'] = True
        print("  ✅ Config module imported")
        
        # Test API key
        if Config.OPENAI_API_KEY:
            results['api_key'] = True
            print("  ✅ OpenAI API key configured")
        else:
            results['api_key'] = False
            print("  ❌ OpenAI API key not found")
            
    except Exception as e:
        results['config_import'] = False
        results['api_key'] = False
        print(f"  ❌ Config import failed: {str(e)}")
    
    return results

def test_modules() -> Dict[str, bool]:
    """Test if custom modules can be imported"""
    
    results = {}
    modules = [
        'data_processor',
        'ai_cleaner', 
        'cleaning_engine',
        'utils.logger',
        'utils.validators',
        'utils.error_handler'
    ]
    
    print("\n📦 Testing custom modules...")
    
    for module in modules:
        try:
            __import__(module)
            results[module] = True
            print(f"  ✅ {module}")
        except Exception as e:
            results[module] = False
            print(f"  ❌ {module}: {str(e)}")
    
    return results

def test_sample_data() -> Dict[str, bool]:
    """Test if sample data files exist and can be read"""
    
    results = {}
    
    print("\n📄 Testing sample data...")
    
    # Test sample CSV
    csv_path = 'examples/sample_data.csv'
    if os.path.exists(csv_path):
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            results['sample_csv'] = True
            print(f"  ✅ Sample CSV loaded ({df.shape[0]} rows, {df.shape[1]} columns)")
        except Exception as e:
            results['sample_csv'] = False
            print(f"  ❌ Sample CSV error: {str(e)}")
    else:
        results['sample_csv'] = False
        print("  ❌ Sample CSV file not found")
    
    return results

def test_basic_functionality() -> Dict[str, bool]:
    """Test basic functionality without API calls"""
    
    results = {}
    
    print("\n⚙️ Testing basic functionality...")
    
    try:
        # Test data processor
        from data_processor import DataProcessor
        processor = DataProcessor()
        results['data_processor'] = True
        print("  ✅ DataProcessor initialized")
    except Exception as e:
        results['data_processor'] = False
        print(f"  ❌ DataProcessor failed: {str(e)}")
    
    try:
        # Test cleaning engine (without AI)
        from cleaning_engine import CleaningEngine
        engine = CleaningEngine()
        results['cleaning_engine'] = True
        print("  ✅ CleaningEngine initialized")
    except Exception as e:
        results['cleaning_engine'] = False
        print(f"  ❌ CleaningEngine failed: {str(e)}")
    
    try:
        # Test with sample data
        if results.get('data_processor') and os.path.exists('examples/sample_data.csv'):
            import pandas as pd
            df = pd.read_csv('examples/sample_data.csv')
            analysis = processor.analyze_data_quality(df)
            results['data_analysis'] = True
            print(f"  ✅ Data analysis completed (quality metrics generated)")
        else:
            results['data_analysis'] = False
            print("  ❌ Data analysis skipped (dependencies not available)")
    except Exception as e:
        results['data_analysis'] = False
        print(f"  ❌ Data analysis failed: {str(e)}")
    
    return results

def generate_report(all_results: Dict[str, Dict[str, bool]]) -> None:
    """Generate a summary report"""
    
    print("\n" + "="*50)
    print("📊 INSTALLATION TEST REPORT")
    print("="*50)
    
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        print(f"\n{category.upper()}:")
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test}: {status}")
            total_tests += 1
            if passed:
                passed_tests += 1
    
    print(f"\n📈 SUMMARY:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")
    print(f"  Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Your installation is ready to use.")
        print("   Run 'streamlit run app.py' to start the application.")
    else:
        print("\n⚠️  SOME TESTS FAILED. Please check the issues above.")
        print("   Refer to SETUP.md for troubleshooting guidance.")

def main():
    """Run all installation tests"""
    
    print("🧹 AI-Based Data Cleaner - Installation Test")
    print("=" * 50)
    
    all_results = {}
    
    try:
        # Run all tests
        all_results['Package Imports'] = test_imports()
        all_results['Configuration'] = test_configuration()
        all_results['Custom Modules'] = test_modules()
        all_results['Sample Data'] = test_sample_data()
        all_results['Basic Functionality'] = test_basic_functionality()
        
        # Generate report
        generate_report(all_results)
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during testing:")
        print(f"   {str(e)}")
        print(f"\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
