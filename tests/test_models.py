"""
Unit tests for data models/schemas.
"""

import pytest
from datetime import datetime
from src.models.schemas import Official, OfficialSocial, Election, ElectionResult, Funding


def test_official_model():
    """Test Official model validation."""
    official = Official(
        official_id="test123",
        name="田中太郎",
        age=45,
        faction="自民党",
        office_type="national",
        source_url="https://example.com",
    )
    
    assert official.official_id == "test123"
    assert official.name == "田中太郎"
    assert official.age == 45
    assert official.office_type == "national"


def test_official_id_validation():
    """Test Official ID validation."""
    with pytest.raises(ValueError):
        Official(
            official_id="",  # Empty ID should fail
            name="Test",
            source_url="https://example.com",
        )


def test_official_social_model():
    """Test OfficialSocial model."""
    social = OfficialSocial(
        official_id="test123",
        platform="x",
        profile_url="https://x.com/testuser",
        handle="testuser",
    )
    
    assert social.official_id == "test123"
    assert social.platform == "x"
    assert social.handle == "testuser"


def test_election_model():
    """Test Election model."""
    election = Election(
        election_id="election001",
        name="2024 General Election",
        jurisdiction="Tokyo",
        level="national",
        scheduled_date="2024-12-15",
        source_url="https://example.com",
    )
    
    assert election.election_id == "election001"
    assert election.level == "national"


def test_election_result_model():
    """Test ElectionResult model."""
    result = ElectionResult(
        election_id="election001",
        candidate_name="田中太郎",
        votes=10000,
        result="elected",
        source_url="https://example.com",
    )
    
    assert result.election_id == "election001"
    assert result.votes == 10000
    assert result.result == "elected"


def test_funding_model():
    """Test Funding model."""
    funding = Funding(
        official_id="test123",
        year=2024,
        report_url="https://example.com/report.pdf",
        income_total=1000000.0,
        expense_total=800000.0,
        source_url="https://example.com",
    )
    
    assert funding.official_id == "test123"
    assert funding.year == 2024
    assert funding.income_total == 1000000.0
    assert funding.currency == "JPY"
