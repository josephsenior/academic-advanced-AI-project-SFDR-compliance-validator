"""
ESG Compliance Agent Configuration

Configuration constants and environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get LLM configuration (same as data consistency agent)
OPENAI_API_KEY = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
OPENAI_BASE_URL = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL_NAME", "hosted_vllm/Llama-3.1-70B-Instruct")
LLM_MODEL_IMAGE = os.getenv("LLM_VISION_MODEL", "hosted_vllm/llava-1.5-7b-hf")

