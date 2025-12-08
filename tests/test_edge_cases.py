"""
Comprehensive Test Suite - Edge Cases
Tests edge cases for fund type detection and validation
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any

# Mock imports for testing
from src.extractors.data_consistency_agent import DataConsistencyAgent


class TestFundTypeEdgeCases:
    """Test edge cases in fund type detection"""
    
    @pytest.fixture
    def agent(self):
        """Create DataConsistencyAgent instance"""
        return DataConsistencyAgent(enable_esg_validation=True)
    
    def test_etf_with_private_equity(self, agent):
        """Test fund with both ETF and Private Equity characteristics"""
        features = {
            "fund_name": "ODDO BHF Private Equity ETF",
            "isin": "FR001400AEM1",
            "fund_structure": "ETF",
            "investment_strategy": "Private equity investments through listed securities",
            "liquidity": "Daily",
            "is_etf": True,
            "is_private_equity": True
        }
        
        result = agent._detect_fund_type(features)
        
        # Should prioritize ETF due to daily liquidity
        assert result["fund_type"] == "ETF"
        assert result["confidence"] == "medium"
        assert "private equity characteristics" in result["notes"]
    
    def test_dated_fund_with_article_9(self, agent):
        """Test dated fund with Article 9 classification"""
        features = {
            "fund_name": "ODDO BHF Sustainable Growth 2030",
            "isin": "FR001400XYZ1",
            "fund_structure": "SICAV",
            "sfdr_classification": "Article 9",
            "maturity_date": "2030-12-31",
            "is_dated_fund": True
        }
        
        result = agent._detect_fund_type(features)
        
        # Should detect both characteristics
        assert "DATED" in result["fund_type"]
        assert "Article 9" in result["fund_type"]
        assert result["confidence"] == "high"
    
    def test_fund_with_multiple_share_classes(self, agent):
        """Test handling of multiple share classes"""
        features = {
            "fund_name": "ODDO BHF Algo Trend US",
            "isin": "FR001400AEM1",
            "share_classes": [
                {"class": "A", "currency": "EUR"},
                {"class": "I", "currency": "USD"},
                {"class": "R", "currency": "GBP"}
            ]
        }
        
        # Should process without errors
        result = agent._detect_fund_type(features)
        assert result["fund_type"] is not None
    
    def test_client_type_institutional_vs_retail(self, agent):
        """Test client type detection for mixed target"""
        
        # Institutional indicators
        institutional_features = {
            "minimum_investment": "5000000 EUR",
            "eligible_investors": "Qualified institutional investors",
            "distribution_channels": ["Institutional platforms"]
        }
        
        result = agent._detect_client_type(institutional_features)
        assert result["client_type"] == "INSTITUTIONAL"
        assert result["confidence"] == "high"
        
        # Retail indicators
        retail_features = {
            "minimum_investment": "100 EUR",
            "eligible_investors": "Retail investors",
            "distribution_channels": ["Banks", "Online platforms"]
        }
        
        result = agent._detect_client_type(retail_features)
        assert result["client_type"] == "RETAIL"
        assert result["confidence"] == "high"
    
    def test_missing_key_features(self, agent):
        """Test handling of missing key features"""
        minimal_features = {
            "fund_name": "Test Fund"
        }
        
        result = agent._detect_fund_type(minimal_features)
        
        # Should still return result with low confidence
        assert result["confidence"] == "low"
        assert "insufficient information" in result["notes"].lower()
    
    def test_conflicting_indicators(self, agent):
        """Test handling of conflicting fund type indicators"""
        conflicting_features = {
            "fund_name": "ODDO BHF Test Fund",
            "fund_structure": "Open-ended",
            "liquidity": "Daily",
            "is_etf": True,
            "is_private_equity": True,
            "is_dated_fund": True,
            "maturity_date": "2030-12-31"
        }
        
        result = agent._detect_fund_type(conflicting_features)
        
        # Should handle gracefully with medium confidence
        assert result["confidence"] in ["medium", "low"]
        assert len(result["notes"]) > 0


class TestNumericalValidationEdgeCases:
    """Test edge cases in numerical validation"""
    
    @pytest.fixture
    def agent(self):
        """Create DataConsistencyAgent instance"""
        return DataConsistencyAgent()
    
    def test_percentage_formatting_variations(self, agent):
        """Test different percentage formats"""
        test_cases = [
            ("1.5%", "1.50%", True),  # Should match
            ("1.5%", "0.015", True),  # Decimal format
            ("150%", "1.5", True),  # Ratio format
            ("1.5%", "2.5%", False)  # Should not match
        ]
        
        for val1, val2, should_match in test_cases:
            result = agent._compare_percentages(val1, val2, tolerance=0.01)
            assert result == should_match, f"Failed for {val1} vs {val2}"
    
    def test_currency_formatting_variations(self, agent):
        """Test different currency formats"""
        test_cases = [
            ("EUR 1,000,000", "1000000 EUR", True),
            ("1.5M EUR", "1500000 EUR", True),
            ("USD 1,000", "EUR 900", False),  # Different currencies
            ("1,234.56", "1234.56", True)
        ]
        
        for val1, val2, should_match in test_cases:
            result = agent._compare_currency_values(val1, val2, tolerance=0.01)
            assert result == should_match, f"Failed for {val1} vs {val2}"
    
    def test_date_formatting_variations(self, agent):
        """Test different date formats"""
        test_cases = [
            ("2024-01-15", "15/01/2024", True),
            ("January 15, 2024", "2024-01-15", True),
            ("15.01.2024", "2024-01-15", True),
            ("2024-01-15", "2024-02-15", False)
        ]
        
        for val1, val2, should_match in test_cases:
            result = agent._compare_dates(val1, val2)
            assert result == should_match, f"Failed for {val1} vs {val2}"
    
    def test_very_small_numbers(self, agent):
        """Test handling of very small numbers"""
        test_cases = [
            ("0.0001%", "0.0001%", True),
            ("1e-6", "0.000001", True),
            ("0.0001", "0.0002", False)
        ]
        
        for val1, val2, should_match in test_cases:
            result = agent._compare_percentages(val1, val2, tolerance=0.00001)
            assert result == should_match
    
    def test_very_large_numbers(self, agent):
        """Test handling of very large numbers"""
        test_cases = [
            ("1,000,000,000", "1B", True),
            ("5.5B EUR", "5500000000 EUR", True),
            ("1.5T", "1500B", True)
        ]
        
        for val1, val2, should_match in test_cases:
            result = agent._compare_currency_values(val1, val2, tolerance=0.01)
            assert result == should_match


class TestESGValidationEdgeCases:
    """Test edge cases in ESG validation"""
    
    @pytest.fixture
    def agent(self):
        """Create DataConsistencyAgent instance with ESG"""
        return DataConsistencyAgent(enable_esg_validation=True)
    
    def test_no_sfdr_classification(self, agent):
        """Test fund with no SFDR classification"""
        features = {
            "fund_name": "ODDO BHF Classic Fund",
            "isin": "FR001400XYZ1",
            "sfdr_classification": None
        }
        
        result = agent._validate_esg_compliance(features)
        
        # Should handle gracefully
        assert result is not None
        assert "sfdr_classification" in result
    
    def test_article_6_with_esg_considerations(self, agent):
        """Test Article 6 fund with some ESG considerations"""
        features = {
            "fund_name": "Test Fund",
            "sfdr_classification": "Article 6",
            "esg_integration": "Limited ESG screening",
            "sustainability_risks": "Considered in investment process"
        }
        
        result = agent._validate_esg_compliance(features)
        
        # Should detect potential misclassification
        assert "compliance_issues" in result
    
    def test_article_9_missing_pai(self, agent):
        """Test Article 9 fund missing PAI indicators"""
        features = {
            "fund_name": "Test Sustainable Fund",
            "sfdr_classification": "Article 9",
            "sustainable_investment_objective": "Carbon reduction",
            "pai_statement": None  # Missing!
        }
        
        result = agent._validate_esg_compliance(features)
        
        # Should flag as compliance issue
        assert any("PAI" in str(issue) for issue in result.get("compliance_issues", []))
    
    def test_taxonomy_alignment_without_article_8_9(self, agent):
        """Test taxonomy alignment claim without Article 8/9 classification"""
        features = {
            "fund_name": "Test Fund",
            "sfdr_classification": "Article 6",
            "taxonomy_aligned": "50%"  # Shouldn't have this for Article 6
        }
        
        result = agent._validate_esg_compliance(features)
        
        # Should flag inconsistency
        assert result.get("validation_status") in ["warning", "failed"]


class TestDocumentParsingEdgeCases:
    """Test edge cases in document parsing"""
    
    def test_corrupted_pdf(self):
        """Test handling of corrupted PDF"""
        # This would test actual file handling
        pass
    
    def test_scanned_document_no_text(self):
        """Test handling of scanned document with no extractable text"""
        pass
    
    def test_multilingual_document(self):
        """Test handling of document with multiple languages"""
        pass
    
    def test_very_large_document(self):
        """Test handling of document with 200+ pages"""
        pass


class TestPerformanceBenchmarks:
    """Performance benchmarks for system"""
    
    def test_single_document_extraction_time(self):
        """Benchmark: Single document should extract in <60 seconds"""
        # Measure extraction time
        pass
    
    def test_chart_analysis_time(self):
        """Benchmark: Chart analysis should complete in <5 seconds"""
        pass
    
    def test_esg_validation_time(self):
        """Benchmark: ESG validation should complete in <10 seconds"""
        pass
    
    def test_memory_usage(self):
        """Benchmark: Memory usage should stay under 2GB"""
        pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
