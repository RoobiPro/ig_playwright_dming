"""
Test script to verify API key loading from .env file
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deepseek_api_client import create_client_from_env

def test_env_loading():
    """Test that .env file is properly loaded with override"""
    print("Testing environment variable loading...")
    
    # Load .env with override
    load_dotenv(override=True)
    
    # Check if API keys are loaded
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    deepinfra_key = os.getenv("DEEPINFRA_API_KEY")
    ai_provider = os.getenv("AI_PROVIDER")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    print(f"DEEPSEEK_API_KEY: {'[OK] Found' if deepseek_key else '[X] Not found'}")
    print(f"DEEPINFRA_API_KEY: {'[OK] Found' if deepinfra_key else '[X] Not found'}")
    print(f"AI_PROVIDER: {ai_provider if ai_provider else '[X] Not set'}")
    print(f"GEMINI_API_KEY: {'[OK] Found' if gemini_key else '[X] Not found'}")
    
    print("\n" + "="*50)
    
    return {
        'deepseek_key': bool(deepseek_key),
        'deepinfra_key': bool(deepinfra_key),
        'ai_provider': ai_provider,
        'gemini_key': bool(gemini_key)
    }

def test_deepseek_client():
    """Test DeepSeek client creation"""
    print("Testing DeepSeek client creation...")
    
    try:
        client = create_client_from_env()
        print("[OK] DeepSeek client created successfully")
        print(f"[OK] API key loaded: {client.api_key[:10]}...")
        return True
    except Exception as e:
        print(f"[X] DeepSeek client creation failed: {e}")
        return False

def test_api_provider_selection():
    """Test AI provider selection logic"""
    print("Testing AI provider selection...")
    
    try:
        # Load environment
        load_dotenv(override=True)
        provider = os.getenv("AI_PROVIDER")
        print(f"Selected AI Provider: {provider}")
        
        if provider == "DEEPINFRA":
            print("[OK] Will use DeepInfra API")
        elif provider == "DEEPSEEK":
            print("[OK] Will use DeepSeek API")
        elif provider == "GEMINI":
            print("[OK] Will use Gemini API")
        else:
            print(f"[!] Unknown provider: {provider}")
            
        return True
    except Exception as e:
        print(f"[X] Provider selection test failed: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("API Key Configuration Test")
    print("="*60)
    
    # Run tests
    env_results = test_env_loading()
    print()
    
    deepseek_ok = test_deepseek_client()
    print()
    
    provider_ok = test_api_provider_selection()
    print()
    
    print("="*60)
    print("Test Summary:")
    print(f"Environment loading: {'[OK]' if any(env_results.values()) else '[X]'}")
    print(f"DeepSeek client: {'[OK]' if deepseek_ok else '[X]'}")
    print(f"Provider selection: {'[OK]' if provider_ok else '[X]'}")
    print("="*60)