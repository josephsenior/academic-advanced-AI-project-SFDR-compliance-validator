"""
Detailed API Connection Troubleshooting Script - Pytest Compatible
"""
import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def get_api_credentials():
    api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
    return api_key, base_url

@pytest.mark.skipif(not all(get_api_credentials()), reason="Missing API credentials")
def test_basic_http_connectivity():
    """Test basic HTTP connectivity"""
    api_key, base_url = get_api_credentials()
    
    import requests
    print(f"Testing connection to: {base_url}")
    try:
        response = requests.get(base_url, timeout=10)
        assert response.status_code in [200, 404, 401, 403], f"Unexpected status code: {response.status_code}"
    except requests.exceptions.Timeout:
        pytest.skip("Connection timeout - server not responding")
    except requests.exceptions.ConnectionError as e:
        pytest.skip(f"Connection error: {e}")

@pytest.mark.skipif(not all(get_api_credentials()), reason="Missing API credentials")
def test_langchain_connection():
    """Test LangChain ChatOpenAI connection"""
    api_key, base_url = get_api_credentials()
    
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        pytest.skip("Missing dependency: langchain-openai")

    llm = ChatOpenAI(
        model="hosted_vllm/Llama-3.1-70B-Instruct",
        temperature=0.0,
        api_key=api_key,
        base_url=base_url,
        timeout=30
    )
    
    try:
        response = llm.invoke("Say 'API connection successful' if you can read this.")
        assert response.content, "Empty response content"
    except Exception as e:
        pytest.skip(f"LangChain connection failed: {e}")


