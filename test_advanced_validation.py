#!/usr/bin/env python3
"""
Test script for the Advanced Data Quality Validation System
"""

import pandas as pd
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_validator import AdvancedDataValidator

def test_advanced_validation():
    """Test the advanced validation system with sample data"""
    
    print("🔍 Testing Advanced Data Quality Validation System")
    print("=" * 60)
    
    # Load the test dataset
    try:
        df = pd.read_csv('examples/employee_data_with_issues.csv')
        print(f"✅ Loaded test dataset: {df.shape[0]} records, {df.shape[1]} columns")
    except Exception as e:
        print(f"❌ Error loading test dataset: {e}")
        return False
    
    # Initialize the validator
    validator = AdvancedDataValidator(company_founding_year=1990)
    
    # Run validation
    print("\n🚀 Running advanced validation...")
    try:
        results = validator.validate_dataset(df)
        print("✅ Validation completed successfully!")
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Display results summary
    print("\n📊 Validation Results Summary:")
    print("-" * 40)
    
    summary = results['summary']
    print(f"Total Records: {summary['total_records']}")
    print(f"Issues Found: {summary['total_issues_found']}")
    print(f"High Severity: {summary['high_severity_issues']}")
    print(f"Medium Severity: {summary['medium_severity_issues']}")
    print(f"Low Severity: {summary['low_severity_issues']}")
    print(f"Affected Records: {summary['total_affected_records']}")
    print(f"Data Quality Score: {summary['data_quality_score']}%")
    
    # Display detailed issues
    if results['detailed_issues']:
        print("\n🔍 Detailed Issues Found:")
        print("-" * 40)
        
        for i, issue in enumerate(results['detailed_issues'], 1):
            print(f"\n{i}. {issue['category']} ({issue['severity']})")
            print(f"   Description: {issue['description']}")
            print(f"   Affected: {issue['count']} records ({issue['affected_percentage']}%)")
            print(f"   Recommendation: {issue['recommendation'][:100]}...")
    
    # Display recommendations
    if results['recommendations']:
        print("\n💡 Recommendations:")
        print("-" * 40)
        
        for rec_group in results['recommendations']:
            print(f"\n{rec_group['priority']} Priority - {rec_group['title']}:")
            for j, item in enumerate(rec_group['items'], 1):
                print(f"  {j}. {item[:80]}...")
    
    print(f"\n{'✅ VALIDATION PASSED' if results['validation_passed'] else '❌ VALIDATION FAILED'}")
    
    return True

if __name__ == "__main__":
    success = test_advanced_validation()
    sys.exit(0 if success else 1)
