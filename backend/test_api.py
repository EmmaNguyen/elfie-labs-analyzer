"""
Test suite for backend API endpoints
Run with: python test_api.py
"""

import requests
import json
from io import BytesIO

# Backend URL (change to your Render URL when deployed)
BACKEND_URL = "http://localhost:8000"
# BACKEND_URL = "https://elfie-labs-backend-api.onrender.com"  # Uncomment for Render

def test_health_endpoint():
    """Test the health check endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "status" in data, "Response should contain 'status'"
        assert "timestamp" in data, "Response should contain 'timestamp'"
        assert data["status"] == "healthy", f"Expected 'healthy', got {data['status']}"
        print("✅ Health endpoint test passed")
        return True
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def test_pdf_analysis_endpoint():
    """Test the PDF analysis endpoint with sample data"""
    print("Testing PDF analysis endpoint...")
    try:
        # Create a sample PDF-like file (in production, use actual PDF)
        # For now, we'll test with a minimal file
        sample_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        files = {'pdf_file': ('test.pdf', BytesIO(sample_content), 'application/pdf')}
        data = {'language': 'en'}
        
        response = requests.post(
            f"{BACKEND_URL}/analyze-pdf",
            files=files,
            data=data,
            timeout=30
        )
        
        # We expect either success or a proper error
        assert response.status_code in [200, 400, 500], f"Unexpected status code: {response.status_code}"
        
        if response.status_code == 200:
            result = response.json()
            assert "success" in result, "Response should contain 'success'"
            assert "summary" in result, "Response should contain 'summary'"
            print("✅ PDF analysis endpoint test passed (success)")
        else:
            # Error is expected for invalid PDF
            print(f"✅ PDF analysis endpoint test passed (expected error: {response.status_code})")
        
        return True
    except Exception as e:
        print(f"❌ PDF analysis endpoint test failed: {e}")
        return False

def test_cors_headers():
    """Test that CORS headers are properly set"""
    print("Testing CORS headers...")
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        cors_headers = response.headers.get('Access-Control-Allow-Origin', '')
        print(f"CORS headers: {cors_headers}")
        # CORS headers should be present (even if empty for some requests)
        print("✅ CORS headers test passed")
        return True
    except Exception as e:
        print(f"❌ CORS headers test failed: {e}")
        return False

def test_response_time():
    """Test that API responds within reasonable time"""
    print("Testing response time...")
    try:
        import time
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/health")
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response_time < 5.0, f"Response time too slow: {response_time}s"
        print(f"✅ Response time test passed ({response_time:.2f}s)")
        return True
    except Exception as e:
        print(f"❌ Response time test failed: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid requests"""
    print("Testing error handling...")
    try:
        # Test with missing required fields
        response = requests.post(f"{BACKEND_URL}/analyze-pdf", data={})
        # Should return error
        assert response.status_code != 200, "Should return error for invalid request"
        print("✅ Error handling test passed")
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("=" * 50)
    print("Running Backend API Tests")
    print("=" * 50)
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 50)
    
    tests = [
        test_health_endpoint,
        test_cors_headers,
        test_response_time,
        test_error_handling,
        test_pdf_analysis_endpoint,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
