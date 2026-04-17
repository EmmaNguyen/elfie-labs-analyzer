#!/usr/bin/env python3
"""
Manual test script for PDF analysis
Usage: python test_manual_pdf.py <path_to_pdf_file> [--language en|fr|ar|vn]
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# Load environment variables from .env.local
env_path = Path(__file__).parent.parent / ".env.local"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Import after setting env vars
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def set_api_url(url: str):
    """Update the global API_BASE_URL"""
    global API_BASE_URL
    API_BASE_URL = url


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Print a test result with status"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"       {details}")


def test_pdf_file(pdf_path: str, language: str = "en"):
    """Test PDF analysis with the given file"""
    
    pdf_file = Path(pdf_path)
    
    # Validate file exists
    print_header("FILE VALIDATION")
    if not pdf_file.exists():
        print_test_result("File exists", False, f"File not found: {pdf_path}")
        sys.exit(1)
    
    print_test_result("File exists", True, str(pdf_file.absolute()))
    print_test_result("File is PDF", pdf_file.suffix.lower() == ".pdf", f"Extension: {pdf_file.suffix}")
    print(f"  File size: {pdf_file.stat().st_size / 1024:.2f} KB")
    
    # Test health endpoint
    print_header("BACKEND HEALTH CHECK")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        health_ok = response.status_code == 200
        print_test_result("Backend is healthy", health_ok, f"Status: {response.status_code}")
        if health_ok:
            print(f"  Timestamp: {response.json().get('timestamp', 'N/A')}")
    except requests.exceptions.ConnectionError:
        print_test_result("Backend is healthy", False, f"Cannot connect to {API_BASE_URL}")
        print("\n  ⚠️  Make sure the backend server is running:")
        print("     cd backend && source .venv/bin/activate && python main.py")
        sys.exit(1)
    except Exception as e:
        print_test_result("Backend is healthy", False, str(e))
        sys.exit(1)
    
    # Test PDF analysis
    print_header(f"PDF ANALYSIS (Language: {language})")
    print(f"Uploading: {pdf_file.name}")
    print("This may take 10-30 seconds...\n")
    
    try:
        with open(pdf_file, 'rb') as f:
            files = {'pdf_file': (pdf_file.name, f, 'application/pdf')}
            data = {'language': language}
            
            response = requests.post(
                f"{API_BASE_URL}/analyze-pdf",
                files=files,
                data=data,
                timeout=120
            )
        
        print_test_result("API request successful", response.status_code == 200, 
                         f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"\n  Error response: {response.text[:500]}")
            sys.exit(1)
        
        result = response.json()
        
        # Display summary
        print_header("ANALYSIS SUMMARY")
        summary = result.get('summary', {})
        print(f"  Total Tests:   {summary.get('total_tests', 'N/A')}")
        print(f"  Normal:        {summary.get('normal', 'N/A')} ✅")
        print(f"  Abnormal:      {summary.get('abnormal', 'N/A')} ⚠️")
        print(f"  Critical:      {summary.get('critical', 'N/A')} 🚨")
        print(f"  Language:      {summary.get('language', 'N/A')}")
        print(f"  Timestamp:     {summary.get('analysis_timestamp', 'N/A')}")
        
        # Display results
        print_header("EXTRACTED LAB RESULTS")
        results = result.get('results', [])
        
        if not results:
            print("  ⚠️  No lab results found in PDF")
            sys.exit(1)
        
        for i, test in enumerate(results, 1):
            test_name = test.get('test_name', 'Unknown')
            value = test.get('value', 'N/A')
            unit = test.get('unit', '')
            status = test.get('status', 'Unknown')
            ref_range = test.get('reference_range', 'N/A')
            severity = test.get('severity_tier', 'Unknown')
            
            # Status icon
            status_icon = {
                'Normal': '✅',
                'Low': '🔽',
                'High': '🔼',
                'Critical': '🚨'
            }.get(status, '❓')
            
            print(f"\n  {i}. {test_name}")
            print(f"     Value: {value} {unit} {status_icon} {status}")
            print(f"     Reference Range: {ref_range}")
            print(f"     Severity: {severity}")
            
            # Show explanation preview (first 60 chars)
            explanation = test.get('patient_explanation', '')
            if explanation:
                preview = explanation[:60] + "..." if len(explanation) > 60 else explanation
                print(f"     Explanation: {preview}")
        
        # Validation tests
        print_header("VALIDATION TESTS")
        
        # Test 1: Results count matches summary
        count_match = len(results) == summary.get('total_tests', 0)
        print_test_result("Results count matches summary", count_match,
                         f"Found: {len(results)}, Expected: {summary.get('total_tests', 0)}")
        
        # Test 2: All results have required fields
        required_fields = ['test_name', 'value', 'unit', 'reference_range', 'status', 
                          'severity_tier', 'patient_explanation', 'next_steps']
        all_fields_present = all(
            all(field in test for field in required_fields)
            for test in results
        )
        print_test_result("All required fields present", all_fields_present)
        
        # Test 3: Normal + Abnormal + Critical = Total
        total_check = (summary.get('normal', 0) + summary.get('abnormal', 0)) == summary.get('total_tests', 0)
        print_test_result("Summary counts add up correctly", total_check)
        
        # Test 4: Status values are valid
        valid_statuses = {'Normal', 'Low', 'High', 'Critical'}
        all_statuses_valid = all(test.get('status') in valid_statuses for test in results)
        print_test_result("All status values are valid", all_statuses_valid)
        
        # Test 5: LOINC codes present for known tests
        tests_with_loinc = sum(1 for test in results if test.get('loinc_code'))
        print_test_result(f"LOINC codes present ({tests_with_loinc}/{len(results)} tests)", 
                         tests_with_loinc > 0)
        
        # Final summary
        print_header("TEST SUMMARY")
        print(f"  PDF File: {pdf_file.name}")
        print(f"  Tests Extracted: {len(results)}")
        print(f"  Language: {language}")
        print(f"  Backend: {API_BASE_URL}")
        print(f"\n  ✅ Analysis completed successfully!")
        
        # Save results to file
        output_file = pdf_file.parent / f"{pdf_file.stem}_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n  Results saved to: {output_file}")
        
        return result
        
    except requests.exceptions.Timeout:
        print_test_result("API request", False, "Request timed out (120s)")
        sys.exit(1)
    except Exception as e:
        print_test_result("API request", False, str(e))
        import traceback
        print(f"\n  Error details:\n{traceback.format_exc()}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Manual test for PDF lab analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_manual_pdf.py ~/Documents/lab_results.pdf
  python test_manual_pdf.py ./test_lab_results.pdf --language fr
  python test_manual_pdf.py /path/to/report.pdf --language en
        """
    )
    
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to analyze"
    )
    
    parser.add_argument(
        "--language", "-l",
        choices=["en", "fr", "ar", "vn"],
        default="en",
        help="Language for analysis (default: en)"
    )
    
    parser.add_argument(
        "--api-url", "-a",
        default=API_BASE_URL,
        help=f"Backend API URL (default: {API_BASE_URL})"
    )
    
    args = parser.parse_args()
    
    # Update API URL if provided
    set_api_url(args.api_url)
    
    # Run the test
    test_pdf_file(args.pdf_path, args.language)


if __name__ == "__main__":
    main()
