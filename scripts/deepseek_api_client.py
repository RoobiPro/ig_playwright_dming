"""
Simple DeepSeek API Client

A straightforward client for the DeepSeek API that just works.
"""

import json
import requests
import os
from dotenv import load_dotenv


class DeepSeekClient:
    """Simple DeepSeek API client"""
    
    def __init__(self, api_key: str):
        """Initialize with API key"""
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> dict:
        """Generate a response from DeepSeek API"""
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request data
        data = {
            "model": "deepseek-reasoner",
            "messages": messages,
            "stream": False
        }
        
        # Make API request
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=60
            )
            
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return {
                    "content": content,
                    "usage": result.get("usage", {}),
                    "success": True
                }
            else:
                return {
                    "content": None,
                    "error": f"API Error {response.status_code}: {response.text}",
                    "success": False
                }
                
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return {
                "content": None,
                "error": f"Request failed: {str(e)}\nTraceback:\n{tb}",
                "success": False
            }


def create_client_from_env() -> DeepSeekClient:
    """Create client from environment variables"""
    
    # Load environment variables with override to ensure .env file takes precedence
    load_dotenv(override=True)
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is required")
    
    return DeepSeekClient(api_key)


if __name__ == "__main__":
    # Test the client
    client = create_client_from_env()
    result = client.generate_response("Hello, how are you?")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Response: {result['content']}")
    else:
        print(f"Error: {result['error']}")