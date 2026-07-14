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
