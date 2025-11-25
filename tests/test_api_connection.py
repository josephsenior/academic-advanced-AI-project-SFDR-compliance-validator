"""
Detailed API Connection Troubleshooting Script
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("API CONNECTION TROUBLESHOOTING")
print("=" * 80)
print()

# 1. Check environment variables
print("1. ENVIRONMENT VARIABLES CHECK")
print("-" * 80)
api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")

if api_key:
    print(f"[OK] API Key: {api_key[:10]}...{api_key[-4:]}")
else:
    print("[ERROR] API Key: NOT SET")
    
if base_url:
    print(f"[OK] Base URL: {base_url}")
else:
    print("[ERROR] Base URL: NOT SET")

if not api_key or not base_url:
    print("\n[ERROR] Missing required environment variables!")
    sys.exit(1)

print()

# 2. Test basic HTTP connectivity
print("2. BASIC HTTP CONNECTIVITY TEST")
print("-" * 80)
try:
    import requests
    print(f"Testing connection to: {base_url}")
    response = requests.get(base_url, timeout=10)
    print(f"[OK] HTTP Status: {response.status_code}")
    print(f"[OK] Response headers: {dict(list(response.headers.items())[:3])}")
except requests.exceptions.Timeout:
    print("[ERROR] Connection timeout - server not responding")
except requests.exceptions.ConnectionError as e:
    print(f"[ERROR] Connection error: {e}")
    print("  This could mean:")
    print("  - The server is down")
    print("  - Network connectivity issues")
    print("  - Firewall blocking the connection")
    print("  - Incorrect URL")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")

print()

# 3. Test LangChain ChatOpenAI connection
print("3. LANGCHAIN API CONNECTION TEST")
print("-" * 80)
try:
    from langchain_openai import ChatOpenAI
    
    print("Initializing ChatOpenAI...")
    llm = ChatOpenAI(
        model="hosted_vllm/Llama-3.1-70B-Instruct",
        temperature=0.0,
        api_key=api_key,
        base_url=base_url,
        timeout=30
    )
    
    print("Sending test message...")
    response = llm.invoke("Say 'API connection successful' if you can read this.")
    print(f"[OK] Response received: {response.content[:100]}")
    print("[OK] API connection is working!")
    
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("  Install with: pip install langchain-openai")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    
    # Try to get more details
    if hasattr(e, 'response'):
        print(f"\nResponse status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
        print(f"Response body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")

print()

# 4. Test with curl-like request
print("4. RAW HTTP REQUEST TEST")
print("-" * 80)
try:
    import requests
    import json
    
    # Try a simple chat completion request
    chat_url = f"{base_url}/v1/chat/completions" if not base_url.endswith("/chat/completions") else base_url
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "hosted_vllm/Llama-3.1-70B-Instruct",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "temperature": 0.0
    }
    
    print(f"Testing endpoint: {chat_url}")
    print(f"Headers: Authorization: Bearer {api_key[:10]}...")
    
    response = requests.post(chat_url, headers=headers, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("[OK] Raw HTTP request successful!")
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            print(f"[OK] Response: {result['choices'][0]['message']['content'][:100]}")
    else:
        print(f"[ERROR] Error response: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("TROUBLESHOOTING COMPLETE")
print("=" * 80)

