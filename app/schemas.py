from typing import Literal, Optional

from pydantic import BaseModel, Field


class LeadData(BaseModel):
    """Lead payload after /enrich. name and company are required; other fields may be null."""

    name: str
    company: str
    title: Optional[str] = None
    company_size: Optional[int] = None
    industry: Optional[str] = None
    linkedin_active_recently: Optional[bool] = None
    estimated_monthly_leads: Optional[int] = None
    has_dedicated_sales_role: Optional[bool] = None
    recent_signal: Optional[str] = None
    location: Optional[str] = None


class LeadScoreResult(BaseModel):
    """Structured shape OpenAI must return — enforced via JSON schema."""

    score: int = Field(..., ge=1, le=10, description="Fit score from 1 (poor) to 10 (excellent)")
    confidence: Literal["low", "medium", "high"] = Field(
        ...,
        description="How confident the score is given available (non-null) fields",
    )
    reason: str = Field(..., description="One sentence explaining the score")


class DraftRequest(BaseModel):
    """Lead plus the score result from /score — input for outreach drafting."""

    name: str
    company: str
    title: Optional[str] = None
    company_size: Optional[int] = None
    industry: Optional[str] = None
    linkedin_active_recently: Optional[bool] = None
    estimated_monthly_leads: Optional[int] = None
    has_dedicated_sales_role: Optional[bool] = None
    recent_signal: Optional[str] = None
    location: Optional[str] = None
    score: int = Field(..., ge=1, le=10)
    confidence: Literal["low", "medium", "high"]
    reason: str


class DraftResult(BaseModel):
    """Outreach draft response — either a real message or a threshold skip."""

    drafted: bool = Field(..., description="True if an outreach message was written")
    message: str = Field(..., description="Outreach text, or skip explanation if not drafted")


class EnrichRequest(BaseModel):
    """Minimal input for website-based company enrichment."""

    company_name: str
    website_url: str


class EnrichResult(BaseModel):
    """Estimated company facts from page text — null when signal is too weak."""

    company_name: str
    company_size: Optional[str] = Field(
        None,
        description="Employee-count range if evidenced in page text, e.g. '10-20'",
    )
    industry: Optional[str] = Field(
        None,
        description="Industry/category if evidenced in page text",
    )
    pages_fetched: int = Field(
        ...,
        description="How many pages successfully loaded (homepage + related)",
    )
    source_urls: list[str] = Field(
        default_factory=list,
        description="URLs that were successfully fetched",
    )
