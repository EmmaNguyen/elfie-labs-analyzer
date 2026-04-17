#!/usr/bin/env python3
"""
Test Qwen API using DashScope SDK with international endpoint
Tests with question "Who are you?" and verifies response is not empty
"""
import os
import sys
from pathlib import Path

# Load environment variables from .env.local
env_path = Path(__file__).parent.parent / ".env.local"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Try to import dashscope
try:
    from dashscope import Generation
    import dashscope
except ImportError:
    print("❌ Error: dashscope package not installed")
    print("Please run: pip install dashscope")
    sys.exit(1)

# Use QWEN_API_KEY from .env.local (mapped to DASHSCOPE_API_KEY)
DASHSCOPE_API_KEY = os.getenv("QWEN_API_KEY", "")

# Set international endpoint (Singapore region)
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'


def test_qwen_dashscope_sdk():
    """Test Qwen API using DashScope SDK"""
    print("=" * 60)
    print("🧪 Qwen DashScope SDK Test (International Endpoint)")
    print("=" * 60)
    
    # Check API key
    if not DASHSCOPE_API_KEY or DASHSCOPE_API_KEY == "your-qwen-api-key":
        print("❌ DASHSCOPE_API_KEY (QWEN_API_KEY) is not configured!")
        print(f"Please set your API key in {env_path}")
        return False
    
    print(f"API Key: {DASHSCOPE_API_KEY[:10]}...{DASHSCOPE_API_KEY[-4:]}")
    print(f"Base URL: {dashscope.base_http_api_url}")
    print("-" * 60)
    
    # Prepare messages
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Who are you?'}
    ]
    
    try:
        print("📝 Sending request: 'Who are you?'")
        
        # Call Generation API
        response = Generation.call(
            api_key=DASHSCOPE_API_KEY,
            model="qwen-turbo",  # Using qwen-turbo (Flash) for fast response
            messages=messages,
            result_format="message"
        )
        
        # Check response status
        if response.status_code == 200:
            # Extract response content
            response_content = response.output.choices[0].message.content
            
            print(f"\n🤖 Qwen's Response:")
            print(f"{response_content}")
            
            # Verify response is not empty
            if response_content and len(response_content.strip()) > 0:
                print("\n✅ TEST PASSED: Received valid response")
                print(f"Response length: {len(response_content)} characters")
                print("=" * 60)
                return True
            else:
                print("\n❌ TEST FAILED: Empty response")
                print("=" * 60)
                return False
        else:
            print(f"\n❌ TEST FAILED: HTTP {response.status_code}")
            print(f"Error code: {response.code}")
            print(f"Error message: {response.message}")
            print("See: https://www.alibabacloud.com/help/model-studio/developer-reference/error-code")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        print("=" * 60)
        return False


def test_qwen_math_dashscope_sdk():
    """Test Qwen API with math question using DashScope SDK"""
    print("\n" + "=" * 60)
    print("🧮 Qwen DashScope SDK Math Test: 1+1=?")
    print("=" * 60)
    
    # Check API key
    if not DASHSCOPE_API_KEY or DASHSCOPE_API_KEY == "your-qwen-api-key":
        print("❌ DASHSCOPE_API_KEY (QWEN_API_KEY) is not configured!")
        return False
    
    print(f"API Key: {DASHSCOPE_API_KEY[:10]}...{DASHSCOPE_API_KEY[-4:]}")
    print("-" * 60)
    
    # Prepare messages
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'What is 1+1? Answer with just the number.'}
    ]
    
    try:
        print("📝 Sending request: 'What is 1+1? Answer with just the number.'")
        
        # Call Generation API
        response = Generation.call(
            api_key=DASHSCOPE_API_KEY,
            model="qwen-turbo",
            messages=messages,
            result_format="message"
        )
        
        # Check response status
        if response.status_code == 200:
            # Extract response content
            answer = response.output.choices[0].message.content
            
            print(f"\n🤖 Qwen's Answer: {answer}")
            
            # Check if answer contains "2"
            if "2" in answer:
                print("\n✅ TEST PASSED: Answer contains '2'")
                print("=" * 60)
                return True
            else:
                print(f"\n❌ TEST FAILED: Answer does not contain '2'")
                print(f"Expected: Answer containing '2'")
                print(f"Got: {answer}")
                print("=" * 60)
                return False
        else:
            print(f"\n❌ TEST FAILED: HTTP {response.status_code}")
            print(f"Error code: {response.code}")
            print(f"Error message: {response.message}")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        print("=" * 60)
        return False


def main():
    """Run all DashScope SDK tests"""
    print("\n🚀 Starting Qwen API Tests (DashScope SDK with International Endpoint)\n")
    
    # Run basic test
    test1_passed = test_qwen_dashscope_sdk()
    
    # Run math test
    test2_passed = test_qwen_math_dashscope_sdk()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Basic Response Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Math Test (1+1=2):   {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
