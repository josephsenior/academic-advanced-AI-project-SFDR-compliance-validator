
from backend.extractors.agents.models import DataConsistencyResult
from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent
from backend.extractors.pipeline import ExtractionPipeline


def test_data_consistency_result_legacy_fields():
    res = DataConsistencyResult(document_id="test")
    assert hasattr(res, "numerical_inconsistencies")
    assert isinstance(res.numerical_inconsistencies, list)
    assert hasattr(res, "cross_reference_issues")
    assert isinstance(res.cross_reference_issues, list)
    # Aliases
    assert hasattr(res, "numerical_issues")
    assert hasattr(res, "cross_references")


def test_orchestrator_normalize_metadata_trims(tmp_path):
    pipeline = ExtractionPipeline(use_llm=False, output_dir=tmp_path)
    metadata = {
        "filename": " doc.pptx ",
        "fund_name": "  Example Fund  ",
        "is_professional_client": "True",
    }
    normalized = pipeline._normalize_metadata(metadata)
    assert normalized["filename"] == "doc.pptx"
    assert normalized["fund_name"] == "Example Fund"
    assert normalized["is_professional_client"] is True


def test_compare_percentages_and_detect_fund_type():
    agent = DataConsistencyAgent(enable_esg_validation=False)
    # Percentage comparisons
    assert agent._compare_percentages("1.5%", "1.50%", tolerance=0.01)
    assert agent._compare_percentages("1.5%", "0.015", tolerance=0.01)
    assert agent._compare_percentages("150%", "1.5", tolerance=0.01)
    assert not agent._compare_percentages("1.5%", "2.5%", tolerance=0.01)

    # Fund type insufficient information
    minimal = {"fund_name": "Test Fund"}
    result = agent._detect_fund_type(minimal)
    assert result["confidence"] == "low"
    assert "insufficient" in result["notes"].lower()
