import re
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


def parse_company_size(value: Any) -> Optional[int]:
    """
    Normalize company_size from /enrich (or callers) into a single int estimate.

    Accepts:
      - None / "" → None
      - int → as-is
      - "15" → 15
      - "10-20" / "10 – 20" → midpoint (15)
      - "50+" → 50
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("company_size must be an integer or range string, not a boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    if not isinstance(value, str):
        raise ValueError(f"Unsupported company_size type: {type(value).__name__}")

    text = value.strip().lower().replace(",", "")
    text = re.sub(r"\s*(employees?|people|staff)\s*$", "", text).strip()
    if not text:
        return None

    range_match = re.fullmatch(r"(\d+)\s*[-–—]\s*(\d+)", text)
    if range_match:
        low = int(range_match.group(1))
        high = int(range_match.group(2))
        if high < low:
            low, high = high, low
        return (low + high) // 2

    plus_match = re.fullmatch(r"(\d+)\s*\+", text)
    if plus_match:
        return int(plus_match.group(1))

    plain_match = re.fullmatch(r"(\d+)", text)
    if plain_match:
        return int(plain_match.group(1))

    raise ValueError(
        f"Unrecognized company_size {value!r}. "
        "Use an integer or a range like '10-20'."
    )


class LeadData(BaseModel):
    """Lead payload after /enrich. name and company are required; other fields may be null."""

    name: str
    company: str
    title: Optional[str] = None
    company_size: Optional[Union[int, str]] = Field(
        None,
        description="Employee count as an int, or a range string like '10-20'. "
        "/score parses ranges to a midpoint before the scoring prompt.",
    )
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
    company_size: Optional[Union[int, str]] = Field(
        None,
        description="Employee count as an int, or a range string like '10-20' (parsed to midpoint)",
    )
    industry: Optional[str] = None
    linkedin_active_recently: Optional[bool] = None
    estimated_monthly_leads: Optional[int] = None
    has_dedicated_sales_role: Optional[bool] = None
    recent_signal: Optional[str] = None
    location: Optional[str] = None
    score: int = Field(..., ge=1, le=10)
    confidence: Literal["low", "medium", "high"]
    reason: str

    @field_validator("company_size", mode="before")
    @classmethod
    def coerce_company_size(cls, value: Any) -> Optional[int]:
        return parse_company_size(value)


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


class LogRequest(BaseModel):
    """Full lead + score + draft payload to persist in Postgres."""

    name: str
    company: str
    title: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    linkedin_active_recently: Optional[bool] = None
    estimated_monthly_leads: Optional[int] = None
    has_dedicated_sales_role: Optional[bool] = None
    recent_signal: Optional[str] = None
    location: Optional[str] = None
    score: int = Field(..., ge=1, le=10)
    confidence: Literal["low", "medium", "high"]
    reason: str
    drafted_message: Optional[str] = None
    status: str = "New"


class LogResult(BaseModel):
    """Confirmation after a lead is written to the database."""

    logged: bool
    id: int
    status: str
    message: str
