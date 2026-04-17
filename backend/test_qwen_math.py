#!/usr/bin/env python3
"""
Test Qwen API with a simple math question: 1+1=?
Passes if the answer contains "2"
"""
import os
import sys
import requests
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

QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
# Use international endpoint (Singapore) - API key only works with this endpoint
QWEN_MAX_URL = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation"


def test_qwen_math():
    """Test Qwen API with 1+1=? question"""
    print("=" * 60)
    print("🧮 Qwen Flash (Turbo) Math Test: 1+1=?")
    print("=" * 60)
    
    # Check API key
    if not QWEN_API_KEY or QWEN_API_KEY == "your-qwen-api-key":
        print("❌ QWEN_API_KEY is not configured!")
        print(f"Please set your API key in {env_path}")
        return False
    
    print(f"API Key: {QWEN_API_KEY[:10]}...{QWEN_API_KEY[-4:]}")
    print("-" * 60)
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": "What is 1+1? Answer with just the number."
                }
            ]
        }
    }
    
    try:
        print("📝 Sending question to Qwen API...")
        response = requests.post(QWEN_MAX_URL, headers=headers, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract answer based on API response format
            answer = ""
            if "output" in data:
                if "choices" in data["output"]:
                    answer = data["output"]["choices"][0]["message"]["content"]
                elif "text" in data["output"]:
                    answer = data["output"]["text"]
            
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
                
        elif response.status_code == 401:
            print("\n❌ TEST FAILED: Invalid API key")
            print("Please check your QWEN_API_KEY in .env.local")
            print("=" * 60)
            return False
        else:
            print(f"\n❌ TEST FAILED: API Error {response.status_code}")
            print(f"Response: {response.text}")
            print("=" * 60)
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ TEST FAILED: Request timed out")
        print("=" * 60)
        return False
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        print("=" * 60)
        return False


def main():
    """Run the math test"""
    success = test_qwen_math()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
