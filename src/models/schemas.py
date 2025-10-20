"""
Data models for Japanese Public Officials scraper.
Using Pydantic for validation and serialization.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator


class Official(BaseModel):
    """Public official profile data."""
    
    official_id: str = Field(..., description="Unique identifier (generated)")
    name: str = Field(..., description="Full name in Japanese")
    name_kana: Optional[str] = Field(None, description="Phonetic reading")
    name_romaji: Optional[str] = Field(None, description="Romanized name")
    age: Optional[int] = Field(None, ge=0, le=150)
    faction: Optional[str] = Field(None, description="Political party/caucus")
    office_type: Optional[Literal["national", "prefectural", "municipal"]] = None
    jurisdiction: Optional[str] = Field(None, description="Geographic area")
    term_start: Optional[str] = Field(None, description="Term start date")
    term_end: Optional[str] = Field(None, description="Term end date")
    promises_text: Optional[str] = Field(None, max_length=5000)
    promises_url: Optional[str] = None
    website_url: Optional[str] = None
    blog_url: Optional[str] = None
    source_url: str = Field(..., description="Where data was collected")
    last_updated: datetime = Field(default_factory=datetime.now)
    
    @field_validator('official_id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Ensure ID is not empty."""
        if not v or not v.strip():
            raise ValueError("official_id cannot be empty")
        return v.strip()


class OfficialSocial(BaseModel):
    """Social media profile for an official."""
    
    official_id: str = Field(..., description="Links to Official")
    platform: Literal["x", "instagram", "facebook", "youtube", "blog"]
    handle: Optional[str] = Field(None, description="Username or channel ID")
    profile_url: str = Field(..., description="Full profile URL")
    verified: Optional[bool] = Field(None, description="Verification status")
    follower_count: Optional[int] = Field(None, ge=0)
    last_updated: datetime = Field(default_factory=datetime.now)


class Election(BaseModel):
    """Scheduled or past election."""
    
    election_id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Election name")
    jurisdiction: str = Field(..., description="Geographic scope")
    level: Literal["national", "prefectural", "municipal"]
    scheduled_date: Optional[str] = Field(None, description="Election date")
    election_type: Optional[str] = Field(None, description="General/By-election/etc")
    source_url: str
    last_updated: datetime = Field(default_factory=datetime.now)


class ElectionResult(BaseModel):
    """Result for a candidate in an election."""
    
    election_id: str = Field(..., description="Links to Election")
    candidate_name: str
    official_id: Optional[str] = Field(None, description="Links to Official if matched")
    party: Optional[str] = Field(None, description="Political affiliation")
    votes: Optional[int] = Field(None, ge=0)
    vote_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    result: Literal["elected", "defeated", "pending"]
    rank: Optional[int] = Field(None, ge=1)
    source_url: str
    last_updated: datetime = Field(default_factory=datetime.now)


class Funding(BaseModel):
    """Political funding/activity fund report."""
    
    official_id: str = Field(..., description="Links to Official")
    year: int = Field(..., ge=1945, le=2100)
    report_url: str = Field(..., description="Official disclosure link")
    income_total: Optional[float] = Field(None, ge=0.0)
    expense_total: Optional[float] = Field(None, ge=0.0)
    balance: Optional[float] = None
    currency: str = Field(default="JPY")
    source_url: str
    last_updated: datetime = Field(default_factory=datetime.now)


# Type aliases for convenience
OfficialDict = dict
SocialDict = dict
ElectionDict = dict
ResultDict = dict
FundingDict = dict
