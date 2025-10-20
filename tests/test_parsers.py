"""
Unit tests for parsers utilities.
"""

import pytest
from src.utils.parsers import (
    parse_html,
    extract_text,
    clean_text,
    extract_age_from_text,
    extract_date_from_text,
    is_valid_url,
    normalize_url,
)


def test_parse_html():
    """Test HTML parsing."""
    html = "<html><body><h1>Test</h1></body></html>"
    soup = parse_html(html)
    assert soup.find('h1') is not None
    assert soup.find('h1').text == "Test"


def test_extract_text():
    """Test text extraction."""
    html = "<div>  Hello   World  </div>"
    soup = parse_html(html)
    div = soup.find('div')
    text = extract_text(div)
    assert text == "Hello World"


def test_clean_text():
    """Test text cleaning."""
    assert clean_text("  Hello   World  ") == "Hello World"
    assert clean_text("\n\nTest\n\n") == "Test"
    assert clean_text("") == ""


def test_extract_age_from_text():
    """Test age extraction."""
    assert extract_age_from_text("田中太郎（45歳）") == 45
    assert extract_age_from_text("年齢：50") == 50
    assert extract_age_from_text("Age: 35") == 35
    assert extract_age_from_text("No age here") is None


def test_extract_date_from_text():
    """Test date extraction."""
    assert extract_date_from_text("2024年12月15日に実施") == "2024-12-15"
    assert extract_date_from_text("2024年1月5日") == "2024-01-05"
    assert extract_date_from_text("2024-03-20") == "2024-03-20"
    assert extract_date_from_text("2024/05/10") == "2024-05-10"
    assert extract_date_from_text("No date") is None


def test_is_valid_url():
    """Test URL validation."""
    assert is_valid_url("https://example.com")
    assert is_valid_url("http://example.com/path")
    assert not is_valid_url("not a url")
    assert not is_valid_url("")


def test_normalize_url():
    """Test URL normalization."""
    base = "https://example.com/page/"
    assert normalize_url("about.html", base) == "https://example.com/page/about.html"
    assert normalize_url("https://other.com") == "https://other.com"
    assert normalize_url("test.html#fragment", base) == "https://example.com/page/test.html"
