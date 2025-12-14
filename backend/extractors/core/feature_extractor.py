"""
Content Feature Extractor using LangChain
Extracts structured features from document text for compliance validation

"""

import os
import sys
# Apply Pydantic v1 patch for Python 3.12 compatibility
try:
    from backend.utils import pydantic_v1_patch
except ImportError:
    # Fallback if running as script
    pass

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Import PydanticOutputParser once, not in TYPE_CHECKING block
try:
    from langchain.output_parsers import PydanticOutputParser
except ImportError:
    from langchain_core.output_parsers import PydanticOutputParser  # type: ignore[no-redef]

from dotenv import load_dotenv

from ..models import ContentFeatures, ESGFeature, PerformanceFeature, CountryFeature, CompanyFeature, FinancialTermFeature

load_dotenv()


class ContentFeatureExtractor:
    """
    Extract structured content features from document text using LangChain
    """
    
    #dima nhottou liste ta3 countries w financial terms houni
    # List of countries to detect (from registration Excel)
    COUNTRIES = [
        "Germany", "Austria", "Belgium", "Chile", "Spain", "France", "Italy",
        "Luxembourg", "Netherlands", "Peru", "Portugal", "United Kingdom",
        "Singapore", "Sweden", "Switzerland", "Finland", "Denmark", "Norway",
        "Ireland", "United Arab Emirates", "Iceland"
    ]
    

    # Financial terms to detect
    FINANCIAL_TERMS = [
        "YtM", "Yield to Maturity", "YtW", "Yield to Worst",
        "YTM", "YTW", "yield to maturity", "yield to worst"
    ]
    
    def __init__(
        self, 
        model_name: str = "hosted_vllm/Llama-3.1-70B-Instruct", 
        temperature: float = 0.0, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize feature extractor with Token Factory (OpenAI-compatible API)

        Args:
            model_name: Token Factory model identifier (default: hosted_vllm/Llama-3.1-70B-Instruct)
            temperature: sampling temperature for LLM (0.0 for deterministic)
            api_key: optional Token Factory API key (overrides env)
            base_url: optional Token Factory base URL (overrides env)
        """
        # Try to get API key and base URL from .env or parameters
        api_key = api_key or os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
        base_url = base_url or os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
        
        if not api_key:
            raise ValueError(
                "Token Factory API key is required. Set TOKEN_FACTORY_API_KEY or LLM_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        if not base_url:
            raise ValueError(
                "Token Factory base URL is required. Set TOKEN_FACTORY_BASE_URL or LLM_BASE_URL environment variable "
                "or pass base_url parameter."
            )
        
        # Initialize Token Factory LLM using OpenAI-compatible API
        # Disable SSL verification for self-signed certificates
        import httpx
        sync_client = httpx.Client(verify=False)
        async_client = httpx.AsyncClient(verify=False)
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=(lambda: api_key),
            base_url=base_url
        )
        # Manually set clients to bypass validation issues in langchain-openai 0.0.2
        # self.llm.http_client = sync_client
        # self.llm.http_async_client = async_client
        

        # Ninitializiw Pydantic parser - to convert LLM response to structured format
        self.parser = PydanticOutputParser(pydantic_object=ContentFeatures)  # type: ignore[type-var]
        

        # Create prompt template - template we send to LLM
        self.prompt_template = self._create_prompt_template()
        

        # Create chain: prompt | llm | parser
        self.chain = self.prompt_template | self.llm | self.parser
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        # template li naba3thou lel LLM m3a instructions 3al format li 7achti bih
        """Create prompt template for feature extraction"""
        

        # Get format instructions from parser
        format_instructions = self.parser.get_format_instructions()
        

        # This is the prompt we send to LLM - asks it to extract specific features
        template = """You are an expert in analyzing financial marketing documents for compliance purposes.

Your task is to extract specific features from the document text that are relevant for compliance validation.

**Extract the following features:**

1. **ESG Mentions**: 
   - Keywords: "ESG", "sustainable", "sustainability", "environmental", "social", "governance"
   - SFDR articles: "Article 6", "Article 8", "Article 9"
   - ESG scores, ratings, or criteria mentions
   - Context: What is being said about ESG?

2. **Performance Data**:
   - Past performance data (dates, percentages, returns)
   - Date ranges (e.g., "2020-2024", "Since inception")
   - Forecasts or simulations of future performance
   - Back-tested performance
   - Any numerical data with dates

3. **Country Mentions**:
   - Explicit country names: {countries}
   - Phrases like "available in", "registered in", "distributed in"
   - Context: Why is the country mentioned?

4. **Company/Issuer Mentions**:
   - Company names, logos mentioned
   - Issuers, holdings mentioned
   - Context: How are companies mentioned?

5. **Financial Terms**:
   - YtM (Yield to Maturity), YtW (Yield to Worst)
   - Other financial terms that require specific disclaimers
   - Full context where term appears

**Important:**
- Extract ONLY what is explicitly or implicitly mentioned in the text
- Provide location information (page/slide number if available, or "document" if not)
- Assign confidence scores (0.0-1.0) based on how clear the mention is
- If a feature type is not found, return an empty list
- Be thorough but accurate - false positives are problematic

**Document Text:**
{document_text}

**Format Instructions:**
{format_instructions}
"""
        
        return ChatPromptTemplate.from_template(template)
    
    def extract_features(self, document_text: str, page_info: Optional[Dict[str, Any]] = None) -> ContentFeatures:
        # prompt -> LLM -> parser, w yraja3 ContentFeatures
        # Ken fama page_info yzid location bi _enhance_locations bch nzidou fil token efficiency w vitesse w accuracy
        """
        Extract features from document text

        Args:
            document_text: full text to analyze
            page_info: optional dict with page/slide mapping

        Returns:
            ContentFeatures pydantic object with extracted features
        """
        try:

            # Format countries list as string for prompt
            countries_str = ", ".join(self.COUNTRIES)
            

            # Invoke chain (prompt -> LLM -> parser)
            result = self.chain.invoke({
                "document_text": document_text,
                "countries": countries_str,
                "format_instructions": self.parser.get_format_instructions()
            })
            

            # Enhance location information if page_info provided
            if page_info:
                result = self._enhance_locations(result, page_info)
            
            return result
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            # Return empty features on error
            return ContentFeatures()
    
    def _enhance_locations(self, features: ContentFeatures, page_info: Dict[str, Any]) -> ContentFeatures:
        # Yzid info ta3 location (page/slide) itha 3tina page_info  bch nsahlou l processing
        # (tawan mta3na nasta3mil location li raja3tha l'LLM)
        """Enhance location information with page/slide details"""
        return features
    
    def extract_features_chunked(self, document_text: str, chunk_size: int = 10000, overlap: int = 500) -> ContentFeatures:
        # Ken document kbir, nfragmentih lchunks w nruni extract_features 3la kol chunk
        # Baad ncombini w na7i duplicates yatlaa resultat final
        # Split text into chunks
        """
        Extract features from large documents by chunking

        Args:
            document_text: Full text content
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks to avoid missing features

        Returns:
            Combined ContentFeatures from all chunks
        """
        chunks = self._chunk_text(document_text, chunk_size, overlap)
        
        all_features = ContentFeatures()
        
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}...")
            chunk_features = self.extract_features(chunk)
            
            # Merge features
            all_features.esg_mentions.extend(chunk_features.esg_mentions)
            all_features.performance_data.extend(chunk_features.performance_data)
            all_features.country_mentions.extend(chunk_features.country_mentions)
            all_features.company_mentions.extend(chunk_features.company_mentions)
            all_features.financial_terms.extend(chunk_features.financial_terms)
        
        # Deduplicate features
        all_features = self._deduplicate_features(all_features)
        
        return all_features
    
    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        # yaksem text lchunks m3a overlap bch ma yensach features
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    def _deduplicate_features(self, features: ContentFeatures) -> ContentFeatures:
        # Ynadhef lfeatures: yna7i duplicates (ESG, performance, etc.)
        # Houni nabdaw bel ESG, najmou netstaamlou nafs el logique lil types okhrin
        seen_esg = set()
        unique_esg = []
        for item in features.esg_mentions:
            key = (item.text.lower(), item.location)
            if key not in seen_esg:
                seen_esg.add(key)
                unique_esg.append(item)
        features.esg_mentions = unique_esg
        
        # Similar for other feature types...
        # For now, return as-is (can be enhanced)
        return features


def extract_content_features(
    text: str, 
    chunk_size: Optional[int] = None,
    model_name: str = "hosted_vllm/Llama-3.1-70B-Instruct",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> ContentFeatures:
    """
    Convenience function to extract features from text using Token Factory

    Args:
        text: Document text
        chunk_size: Optional chunk size for large documents (None = no chunking)
        model_name: Token Factory model to use
        api_key: Optional Token Factory API key
        base_url: Optional Token Factory base URL

    Returns:
        ContentFeatures object
    """
    extractor = ContentFeatureExtractor(
        model_name=model_name,
        api_key=api_key,
        base_url=base_url
    )
    
    if chunk_size and len(text) > chunk_size:
        return extractor.extract_features_chunked(text, chunk_size=chunk_size)
    else:
        return extractor.extract_features(text)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # Test with sample text
    sample_text = """
    This fund is registered under Article 8 of SFDR, promoting environmental characteristics.
    Past performance from 2020 to 2024 shows a return of 15.3%.
    The fund is available in France, Germany, and Switzerland.
    Key holdings include Apple Inc. and Microsoft Corporation.
    The yield to maturity (YtM) is 3.5%.
    """
    
    try:
        # Try to use configured Token Factory LLM
        from ..config.llm_config import get_token_factory_config
        config = get_token_factory_config()
        extractor = ContentFeatureExtractor(**config)
    except Exception as e:
        print(f"Error loading LLM config: {e}")
        print("Using default Token Factory configuration...")
        extractor = ContentFeatureExtractor()
    
    features = extractor.extract_features(sample_text)
    
    print("Extracted Features:")
    print(f"ESG Mentions: {len(features.esg_mentions)}")
    print(f"Performance Data: {len(features.performance_data)}")
    print(f"Country Mentions: {len(features.country_mentions)}")
    print(f"Company Mentions: {len(features.company_mentions)}")
    print(f"Financial Terms: {len(features.financial_terms)}")
    
    print("\nDetails:")
    for feature_type, items in [
        ("ESG", features.esg_mentions),
        ("Performance", features.performance_data),
        ("Countries", features.country_mentions),
        ("Companies", features.company_mentions),
        ("Financial Terms", features.financial_terms)
    ]:
        if items:
            print(f"\n{feature_type}:")
            for item in items:
                print(f"  - {item}")

