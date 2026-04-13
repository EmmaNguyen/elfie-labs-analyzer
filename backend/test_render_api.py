"""
Test script specifically for Render API deployment
Run with: python test_render_api.py
"""

import requests
import sys
import time

# Render backend URL - update this with your actual Render URL
RENDER_URL = "https://elfie-labs-backend-api.onrender.com"

def test_render_health():
    """Test the Render health endpoint"""
    print(f"Testing Render health endpoint: {RENDER_URL}/health")
    try:
        response = requests.get(f"{RENDER_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ Render health endpoint is working!")
                return True
            else:
                print(f"❌ Render health endpoint returned unhealthy status: {data.get('status')}")
                return False
        else:
            print(f"❌ Render health endpoint returned status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out - Render service might be starting up")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Render service might not be deployed yet")
        return False
    except Exception as e:
        print(f"❌ Error testing Render health endpoint: {e}")
        return False

def test_render_pdf_analysis():
    """Test the Render PDF analysis endpoint"""
    print(f"\nTesting Render PDF analysis endpoint: {RENDER_URL}/analyze-pdf")
    try:
        # Create a minimal test PDF
        from io import BytesIO
        sample_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        files = {'pdf_file': ('test.pdf', BytesIO(sample_content), 'application/pdf')}
        data = {'language': 'en'}
        
        response = requests.post(
            f"{RENDER_URL}/analyze-pdf",
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Render PDF analysis endpoint is working!")
            return True
        else:
            print(f"❌ Render PDF analysis endpoint returned status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out - PDF analysis might take longer")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Render service might not be deployed yet")
        return False
    except Exception as e:
        print(f"❌ Error testing Render PDF analysis endpoint: {e}")
        return False

def wait_for_render_ready(max_attempts=10, delay=5):
    """Wait for Render service to be ready"""
    print(f"Waiting for Render service to be ready...")
    print(f"Will check {max_attempts} times with {delay}s delay between attempts")
    
    for attempt in range(max_attempts):
        print(f"\nAttempt {attempt + 1}/{max_attempts}")
        if test_render_health():
            print("✅ Render service is ready!")
            return True
        if attempt < max_attempts - 1:
            print(f"Waiting {delay}s before next attempt...")
            time.sleep(delay)
    
    print("❌ Render service did not become ready within expected time")
    return False

def main():
    print("=" * 60)
    print("Render API Deployment Test")
    print("=" * 60)
    print(f"Testing Render URL: {RENDER_URL}")
    print("=" * 60)
    
    # Test health endpoint
    health_ok = test_render_health()
    
    if health_ok:
        # Test PDF analysis endpoint
        pdf_ok = test_render_pdf_analysis()
        
        if pdf_ok:
            print("\n" + "=" * 60)
            print("🎉 All Render API tests passed!")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("⚠️  Health check passed but PDF analysis failed")
            print("=" * 60)
            return 1
    else:
        print("\n" + "=" * 60)
        print("❌ Render health check failed - service might not be ready")
        print("=" * 60)
        print("\nSuggestions:")
        print("1. Check if Render deployment is complete")
        print("2. Verify the RENDER_URL is correct")
        print("3. Check Render dashboard for deployment logs")
        print("4. Wait a bit longer and try again")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    # Allow passing Render URL as argument
    if len(sys.argv) > 1:
        RENDER_URL = sys.argv[1]
        print(f"Using custom Render URL: {RENDER_URL}")
    
    sys.exit(main())
