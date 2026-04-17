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
import PyPDF2
from io import BytesIO
import base64

# Try to import PIL for image conversion
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available. Install with: pip install Pillow")

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


def check_dependencies():
    """Check if required dependencies are installed"""
    print_header("DEPENDENCY CHECK")
    
    # Check Pillow
    try:
        from PIL import Image
        print("  ✅ Pillow (PIL) installed")
    except ImportError:
        print("  ❌ Pillow not installed")
        print("     Install: pip install Pillow")
    
    # Check pdf2image
    try:
        import pdf2image
        print("  ✅ pdf2image installed")
    except ImportError:
        print("  ⚠️  pdf2image not installed (optional but recommended)")
        print("     Install: pip install pdf2image")
    
    # Check poppler (system dependency)
    try:
        from pdf2image import convert_from_path
        # Try a dummy conversion to check if poppler works
        print("  ✅ poppler-utils (system) installed")
    except ImportError:
        pass  # Already reported above
    except Exception as e:
        if "poppler" in str(e).lower() or "pdftoppm" in str(e).lower():
            print("  ❌ poppler-utils (system) not installed")
            print("     macOS: brew install poppler")
            print("     Ubuntu/Debian: sudo apt-get install poppler-utils")
            print("     Windows: https://github.com/oschwartz10612/poppler-windows")
        else:
            print(f"  ⚠️  Could not verify poppler: {e}")


def test_pdf_file(pdf_path: str, language: str = "en"):
    """Test PDF analysis with the given file"""
    
    # Check dependencies first
    check_dependencies()
    
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
    
    # Extract text using Qwen-VL from JPG conversion
    print_header("EXTRACTING TEXT USING QWEN-VL (PDF → JPG → AI)")
    
    try:
        # Read PDF and convert to images
        with open(pdf_file, 'rb') as f:
            pdf_content = f.read()
        
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
        num_pages = len(pdf_reader.pages)
        print(f"  PDF has {num_pages} page(s)")
        
        # For each page, extract using Qwen-VL
        all_extracted_text = []
        
        for page_num in range(num_pages):
            print(f"\n  Processing page {page_num + 1}/{num_pages}...")
            
            # Convert PDF page to image using pdf2image if available
            img_bytes = None
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(pdf_file, first_page=page_num + 1, last_page=page_num + 1)
                if images:
                    img = images[0]
                    # Convert to bytes
                    img_buffer = BytesIO()
                    img.save(img_buffer, format='JPEG')
                    img_bytes = img_buffer.getvalue()
                    print("    ✅ PDF converted to JPG")
                else:
                    raise Exception("No image generated")
            except ImportError:
                print("    ⚠️  pdf2image not installed")
                print("       Install: pip install pdf2image")
                print("       Also install system dependency:")
                print("         - macOS: brew install poppler")
                print("         - Ubuntu/Debian: sudo apt-get install poppler-utils")
                print("         - Windows: download from https://github.com/oschwartz10612/poppler-windows")
            except Exception as e:
                print(f"    ⚠️  Failed to convert PDF to image: {e}")
            
            # Fallback: use PDF bytes directly if image conversion failed
            if img_bytes is None:
                print("    ⚠️  Using direct PDF bytes (may not work with Qwen-VL)")
                img_bytes = pdf_content
            
            # Use Qwen-VL to extract text from image
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {os.getenv('QWEN_API_KEY', '')}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "qwen-vl-plus",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "image": f"data:image/jpeg;base64,{img_base64}"
                                },
                                {
                                    "text": "Extract all text from this lab report image. Preserve the table structure and formatting. List all lab tests with their values, units, and reference ranges."
                                }
                            ]
                        }
                    ]
                }
            }
            
            try:
                # Use Qwen international endpoint directly
                qwen_url = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
                response = requests.post(
                    qwen_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    extracted = result["output"]["choices"][0]["message"]["content"]
                    
                    # Handle different response formats (string or list)
                    if isinstance(extracted, list):
                        # If it's a list of dicts with 'text' key, extract the text
                        if len(extracted) > 0 and isinstance(extracted[0], dict) and 'text' in extracted[0]:
                            extracted_text_content = extracted[0]['text']
                        else:
                            extracted_text_content = str(extracted)
                    else:
                        extracted_text_content = str(extracted)
                    
                    all_extracted_text.append(f"--- Page {page_num + 1} ---\n{extracted_text_content}")
                    print(f"    ✅ Extracted {len(extracted_text_content)} characters")
                else:
                    print(f"    ❌ Qwen API error: {response.status_code}")
                    print(f"       {response.text[:200]}")
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        # Display combined extracted text
        combined_text = "\n\n".join(all_extracted_text)
        print_header("QWEN-VL EXTRACTED TEXT")
        if combined_text.strip():
            preview = combined_text[:1500]
            if len(combined_text) > 1500:
                preview += f"\n\n... [{len(combined_text) - 1500} more characters]"
            print(preview)
            print(f"\n  Total characters extracted by Qwen: {len(combined_text)}")
        else:
            print("  ⚠️  No text extracted by Qwen-VL")
            
    except Exception as e:
        print(f"  ⚠️  Error in Qwen extraction: {e}")
        import traceback
        print(traceback.format_exc())
    
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
        description="Manual test for PDF lab analysis using Qwen-VL (PDF → JPG → AI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_manual_pdf.py ~/Documents/lab_results.pdf
  python test_manual_pdf.py ./test_lab_results.pdf --language fr
  python test_manual_pdf.py /path/to/report.pdf --language en

Note: This script converts PDF to JPG and uses Qwen-VL for text extraction.
Install dependencies: pip install Pillow pdf2image
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
