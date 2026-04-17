#!/usr/bin/env python3
"""
CLI Chatbot for testing Qwen API
"""
import os
import sys
import json
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any

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
QWEN_MAX_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
QWEN_VL_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

class QwenChatbot:
    def __init__(self):
        self.api_key = QWEN_API_KEY
        self.model = "qwen-max"
        self.conversation_history: List[Dict[str, str]] = []
        self.available_models = {
            "1": ("qwen-max", "Qwen Max (Text Generation)"),
            "2": ("qwen-vl-max", "Qwen VL Max (Vision-Language)"),
            "3": ("qwen-turbo", "Qwen Turbo (Fast)"),
        }
        
    def print_banner(self):
        """Print welcome banner"""
        print("\n" + "=" * 60)
        print("🤖 Qwen API CLI Chatbot")
        print("=" * 60)
        print(f"Model: {self.model}")
        print(f"API Key: {self.mask_api_key()}")
        print("=" * 60)
        print("Commands:")
        print("  /help     - Show this help message")
        print("  /model    - Change model")
        print("  /test     - Test API key")
        print("  /clear    - Clear conversation history")
        print("  /history  - Show conversation history")
        print("  /quit     - Exit chatbot")
        print("=" * 60 + "\n")
        
    def mask_api_key(self) -> str:
        """Mask API key for display"""
        if not self.api_key or len(self.api_key) < 10:
            return "Not configured"
        return f"{self.api_key[:10]}...{self.api_key[-4:]}"
        
    def check_api_key(self) -> bool:
        """Check if API key is configured"""
        if not self.api_key or self.api_key == "your-qwen-api-key":
            print("❌ Error: QWEN_API_KEY is not configured!")
            print(f"Please set your API key in {env_path}")
            return False
        return True
        
    def test_api_key(self) -> bool:
        """Test if API key is valid"""
        print("\n🔍 Testing API key...")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen-max",
            "input": {
                "messages": [{"role": "user", "content": "Hello"}]
            }
        }
        
        try:
            response = requests.post(QWEN_MAX_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                print("✅ API key is valid!")
                return True
            elif response.status_code == 401:
                print("❌ Invalid API key")
                print("Please check your QWEN_API_KEY in .env.local")
                return False
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Request timed out")
            return False
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
            
    def select_model(self):
        """Allow user to select model"""
        print("\n📋 Available Models:")
        for key, (model_id, description) in self.available_models.items():
            marker = "✓" if model_id == self.model else " "
            print(f"  [{marker}] {key}. {description}")
        
        choice = input("\nSelect model (1-3): ").strip()
        
        if choice in self.available_models:
            self.model = self.available_models[choice][0]
            print(f"✅ Model changed to: {self.model}")
        else:
            print("❌ Invalid choice")
            
    def send_message(self, message: str) -> Optional[str]:
        """Send message to Qwen API"""
        if not self.check_api_key():
            return None
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "input": {
                "messages": self.conversation_history
            }
        }
        
        try:
            print("🤖 Thinking...", end="\r")
            response = requests.post(QWEN_MAX_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract response based on API format
                if "output" in data and "choices" in data["output"]:
                    reply = data["output"]["choices"][0]["message"]["content"]
                elif "output" in data and "text" in data["output"]:
                    reply = data["output"]["text"]
                else:
                    reply = str(data)
                
                # Add assistant response to history
                self.conversation_history.append({"role": "assistant", "content": reply})
                
                return reply
                
            elif response.status_code == 401:
                return "❌ Error: Invalid API key. Please check your QWEN_API_KEY."
            else:
                return f"❌ Error: {response.status_code} - {response.text}"
                
        except requests.exceptions.Timeout:
            return "❌ Error: Request timed out. Please try again."
        except Exception as e:
            return f"❌ Error: {str(e)}"
            
    def show_history(self):
        """Display conversation history"""
        if not self.conversation_history:
            print("\n📭 No conversation history")
            return
            
        print("\n📜 Conversation History:")
        print("=" * 60)
        for msg in self.conversation_history:
            role = "🧑 You" if msg["role"] == "user" else "🤖 Assistant"
            print(f"\n{role}:")
            print(f"{msg['content']}")
        print("=" * 60)
        
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("✅ Conversation history cleared")
        
    def show_help(self):
        """Show help message"""
        print("\n📖 Help:")
        print("  Type any message to chat with the AI")
        print("  Use /commands to control the chatbot")
        print("\nCommands:")
        print("  /help     - Show this help message")
        print("  /model    - Change AI model")
        print("  /test     - Test API key validity")
        print("  /clear    - Clear conversation history")
        print("  /history  - Show conversation history")
        print("  /quit     - Exit chatbot")
        
    def run(self):
        """Main chatbot loop"""
        self.print_banner()
        
        if not self.check_api_key():
            print("\n⚠️  Please configure your API key before using the chatbot.")
            test = input("Would you like to test the current key? (y/n): ").strip().lower()
            if test == 'y':
                self.test_api_key()
            return
        
        # Optional API test on startup
        test = input("Test API key before starting? (y/n): ").strip().lower()
        if test == 'y':
            if not self.test_api_key():
                retry = input("Continue anyway? (y/n): ").strip().lower()
                if retry != 'y':
                    return
        
        print("\n💬 Chat started! Type /help for commands or /quit to exit.\n")
        
        while True:
            try:
                user_input = input("🧑 You: ").strip()
                
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.startswith('/'):
                    command = user_input.lower()
                    
                    if command == '/quit' or command == '/exit':
                        print("👋 Goodbye!")
                        break
                    elif command == '/help':
                        self.show_help()
                    elif command == '/model':
                        self.select_model()
                    elif command == '/test':
                        self.test_api_key()
                    elif command == '/clear':
                        self.clear_history()
                    elif command == '/history':
                        self.show_history()
                    else:
                        print(f"❌ Unknown command: {command}")
                        print("Type /help for available commands")
                    continue
                
                # Send message to API
                response = self.send_message(user_input)
                
                if response:
                    print(f"\n🤖 Assistant: {response}\n")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break

def main():
    """Entry point"""
    chatbot = QwenChatbot()
    chatbot.run()

if __name__ == "__main__":
    main()
