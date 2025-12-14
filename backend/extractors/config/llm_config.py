"""
LLM Configuration Helper - Token Factory
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_token_factory_config() -> dict:
    """
    Get Token Factory configuration from environment variables
    
    Returns:
        Dict with:
        - model_name: Model to use (default: Llama for text)
        - api_key: Token Factory API key
        - base_url: Token Factory API base URL
    """
    api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
    model_name = os.getenv("LLM_MODEL_NAME", "hosted_vllm/Llama-3.1-70B-Instruct")
    
    if not api_key:
        raise ValueError(
            "TOKEN_FACTORY_API_KEY or LLM_API_KEY is required. "
            "Set it in .env file or pass as environment variable."
        )
    
    if not base_url:
        raise ValueError(
            "TOKEN_FACTORY_BASE_URL or LLM_BASE_URL is required. "
            "Set it in .env file or pass as environment variable."
        )
    
    return {
        "model_name": model_name,
        "api_key": api_key,
        "base_url": base_url
    }


def get_vision_model_config() -> dict:
    """
    Get Token Factory configuration for vision model (charts/images)
    
    Returns:
        Dict with:
        - model_name: Vision model (default: LLaVA)
        - api_key: Token Factory API key (same as text model)
        - base_url: Token Factory API base URL (same as text model)
    """
    api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
    # Use LLaVA for vision tasks (charts, graphs, images)
    vision_model = os.getenv("LLM_VISION_MODEL", "hosted_vllm/llava-1.5-7b-hf")
    
    if not api_key:
        raise ValueError(
            "TOKEN_FACTORY_API_KEY or LLM_API_KEY is required. "
            "Set it in .env file or pass as environment variable."
        )
    
    if not base_url:
        raise ValueError(
            "TOKEN_FACTORY_BASE_URL or LLM_BASE_URL is required. "
            "Set it in .env file or pass as environment variable."
        )
    
    return {
        "model_name": vision_model,
        "api_key": api_key,
        "base_url": base_url
    }


def create_feature_extractor():
    """Create ContentFeatureExtractor with Token Factory LLM"""
    from ..core.feature_extractor import ContentFeatureExtractor
    
    config = get_token_factory_config()
    return ContentFeatureExtractor(**config)

