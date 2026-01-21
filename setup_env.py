"""
Helper script to create .env file with API credentials
"""
from pathlib import Path

env_content = """# Token Factory API Configuration
# IMPORTANT: Replace with your own API credentials
TOKEN_FACTORY_API_KEY=your_api_key_here
TOKEN_FACTORY_BASE_URL=https://tokenfactory.esprit.tn/api

# Optional: Vision Model (defaults to hosted_vllm/llava-1.5-7b-hf)
LLM_VISION_MODEL=hosted_vllm/llava-1.5-7b-hf

# Optional: Text Model (defaults to hosted_vllm/Llama-3.1-70B-Instruct)
LLM_MODEL_NAME=hosted_vllm/Llama-3.1-70B-Instruct
"""

env_file = Path(".env")

if env_file.exists():
    print(f"[INFO] .env file already exists at {env_file.absolute()}")
    response = input("Do you want to overwrite it? (y/n): ")
    if response.lower() != 'y':
        print("[CANCELLED] .env file not modified")
        exit(0)

try:
    env_file.write_text(env_content, encoding='utf-8')
    print(f"[SUCCESS] .env file created at {env_file.absolute()}")
    print("[INFO] The .env file is in .gitignore and will not be committed to version control")
except Exception as e:
    print(f"[ERROR] Failed to create .env file: {e}")
    exit(1)

