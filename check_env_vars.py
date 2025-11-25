"""
Helper script to check environment variable configuration
"""
import os
from dotenv import load_dotenv

print("=" * 60)
print("Environment Variables Check")
print("=" * 60)
print()

# Load from .env file if it exists
load_dotenv()

# Check all possible variable names
env_vars = {
    "TOKEN_FACTORY_API_KEY": os.getenv("TOKEN_FACTORY_API_KEY"),
    "LLM_API_KEY": os.getenv("LLM_API_KEY"),
    "TOKEN_FACTORY_BASE_URL": os.getenv("TOKEN_FACTORY_BASE_URL"),
    "LLM_BASE_URL": os.getenv("LLM_BASE_URL"),
    "LLM_VISION_MODEL": os.getenv("LLM_VISION_MODEL"),
}

print("Environment Variables Status:")
print("-" * 60)
for var_name, var_value in env_vars.items():
    if var_value:
        # Mask the API key for security
        if "API_KEY" in var_name:
            masked = var_value[:10] + "..." + var_value[-4:] if len(var_value) > 14 else "***"
            print(f"  {var_name}: SET ({masked})")
        else:
            print(f"  {var_name}: SET ({var_value})")
    else:
        print(f"  {var_name}: NOT SET")

print()
print("Resolved Configuration:")
print("-" * 60)
api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
vision_model = os.getenv("LLM_VISION_MODEL", "hosted_vllm/llava-1.5-7b-hf")

if api_key:
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
    print(f"  API Key: {masked_key}")
else:
    print(f"  API Key: NOT FOUND")

if base_url:
    print(f"  Base URL: {base_url}")
else:
    print(f"  Base URL: NOT FOUND")

print(f"  Vision Model: {vision_model}")

print()
if api_key and base_url:
    print("[SUCCESS] Configuration is complete!")
else:
    print("[WARNING] Missing required environment variables.")
    print()
    print("To set environment variables, you can:")
    print("  1. Create a .env file in the project root with:")
    print("     TOKEN_FACTORY_API_KEY=your_key_here")
    print("     TOKEN_FACTORY_BASE_URL=your_url_here")
    print()
    print("  2. Set them in your system environment variables")
    print("  3. Export them in your shell before running tests")

