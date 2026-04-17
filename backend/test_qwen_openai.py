#!/usr/bin/env python3
"""
Test Qwen API using OpenAI-compatible mode
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

# Try to import openai
try:
    from openai import OpenAI
except ImportError:
    print("❌ Error: openai package not installed")
    print("Please run: pip install openai")
    sys.exit(1)

# Use QWEN_API_KEY from .env.local (mapped to DASHSCOPE_API_KEY)
DASHSCOPE_API_KEY = os.getenv("QWEN_API_KEY", "")

# Base URL for Singapore region (intl)
BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


def test_qwen_openai():
    """Test Qwen API using OpenAI-compatible SDK"""
    print("=" * 60)
    print("🧪 Qwen OpenAI-Compatible API Test")
    print("=" * 60)
    
    # Check API key
    if not DASHSCOPE_API_KEY or DASHSCOPE_API_KEY == "your-qwen-api-key":
        print("❌ DASHSCOPE_API_KEY (QWEN_API_KEY) is not configured!")
        print(f"Please set your API key in {env_path}")
        return False
    
    print(f"API Key: {DASHSCOPE_API_KEY[:10]}...{DASHSCOPE_API_KEY[-4:]}")
    print(f"Base URL: {BASE_URL}")
    print("-" * 60)
    
    try:
        # Initialize OpenAI client with DashScope base URL
        print("🔌 Initializing OpenAI client...")
        client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=BASE_URL
        )
        
        # Send request
        print("📝 Sending request: 'Who are you?'")
        completion = client.chat.completions.create(
            model="qwen-turbo",  # Using qwen-turbo (Flash) for fast response
            messages=[{"role": "user", "content": "Who are you?"}],
            timeout=30
        )
        
        # Extract response
        response_content = completion.choices[0].message.content
        
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
            
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ TEST FAILED: {error_msg}")
        
        # Check for specific error types
        if "401" in error_msg or "authentication" in error_msg.lower():
            print("\n💡 Tip: Invalid API key. Please check your QWEN_API_KEY in .env.local")
        elif "404" in error_msg or "model" in error_msg.lower():
            print("\n💡 Tip: Model not found. The model name may be incorrect.")
        elif "timeout" in error_msg.lower():
            print("\n💡 Tip: Request timed out. Please try again.")
        
        print("=" * 60)
        return False


def test_qwen_math_openai():
    """Test Qwen API with math question using OpenAI-compatible SDK"""
    print("\n" + "=" * 60)
    print("🧮 Qwen OpenAI-Compatible Math Test: 1+1=?")
    print("=" * 60)
    
    # Check API key
    if not DASHSCOPE_API_KEY or DASHSCOPE_API_KEY == "your-qwen-api-key":
        print("❌ DASHSCOPE_API_KEY (QWEN_API_KEY) is not configured!")
        return False
    
    print(f"API Key: {DASHSCOPE_API_KEY[:10]}...{DASHSCOPE_API_KEY[-4:]}")
    print("-" * 60)
    
    try:
        # Initialize OpenAI client
        print("🔌 Initializing OpenAI client...")
        client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=BASE_URL
        )
        
        # Send math question
        print("📝 Sending request: 'What is 1+1? Answer with just the number.'")
        completion = client.chat.completions.create(
            model="qwen-turbo",
            messages=[{"role": "user", "content": "What is 1+1? Answer with just the number."}],
            timeout=30
        )
        
        # Extract response
        answer = completion.choices[0].message.content
        
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
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        print("=" * 60)
        return False


def main():
    """Run all OpenAI-compatible tests"""
    print("\n🚀 Starting Qwen API Tests (OpenAI-compatible mode)\n")
    
    # Run basic test
    test1_passed = test_qwen_openai()
    
    # Run math test
    test2_passed = test_qwen_math_openai()
    
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
