import json

from fastapi import FastAPI, HTTPException
from openai import OpenAI

from app.config import OPENAI_API_KEY
from app.db import ensure_leads_table, insert_lead
from app.icp import ICP
from app.schemas import (
    DraftRequest,
    DraftResult,
    EnrichRequest,
    EnrichResult,
    LeadData,
    LeadScoreResult,
    LogRequest,
    LogResult,
)
from app.scrape import gather_company_text

app = FastAPI(title="Lead Qualifier Agent")


@app.on_event("startup")
def on_startup() -> None:
    ensure_leads_table()


OUTREACH_SCORE_THRESHOLD = 6
MIN_ENRICH_TEXT_CHARS = 200

SCORE_SYSTEM_PROMPT = f"""
You are a lead qualification scorer for a B2B SaaS product.

Score how well a lead matches this Ideal Customer Profile (ICP):
{ICP}

Rules:
- Lead data has already been through enrichment. Treat null/missing fields as unknown — do NOT invent or guess values.
- Missing key fields (title, company_size, industry, estimated_monthly_leads, linkedin_active_recently, location, etc.) should lower confidence, and the reason should mention the uncertainty.
- Still return a score 1-10 based only on what is known.
- confidence must be exactly one of: low, medium, high.
- reason must be exactly one sentence.
""".strip()

DRAFT_SYSTEM_PROMPT = """
You write short, specific first-touch outreach messages for qualifying B2B SaaS leads.

Rules:
- Write as a human founder reaching out — warm, direct, no fluff.
- Reference something REAL from the lead data (recent_signal, title + company context, location, inbound volume pain, etc.).
- Do NOT invent facts. If a field is null, do not pretend you know it.
- Keep it to 2–4 short sentences. No subject line. No signature block.
- End with one low-friction question or soft CTA.
- Do not be generic ("Congrats on all the success", "I help companies like yours grow").
""".strip()

ENRICH_SYSTEM_PROMPT = """
You extract company facts from website page text for lead enrichment.

Rules:
- Use ONLY evidence present in the provided text. Do not use outside knowledge about the brand.
- company_size should be an employee-count range string when evidenced (e.g. "1-10", "10-20", "50-100").
- industry should be a short category when evidenced (e.g. "B2B SaaS", "fintech", "HR software").
- If the text does not clearly support a field, return null for that field.
- Never guess from the company name alone.
""".strip()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/enrich", response_model=EnrichResult)
def enrich(payload: EnrichRequest) -> EnrichResult:
    combined_text, source_urls = gather_company_text(payload.website_url)

    # No usable pages / almost no text → return nulls, do not call OpenAI.
    if not source_urls or len(combined_text.strip()) < MIN_ENRICH_TEXT_CHARS:
        return EnrichResult(
            company_name=payload.company_name,
            company_size=None,
            industry=None,
            pages_fetched=len(source_urls),
            source_urls=source_urls,
        )

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    client = OpenAI(api_key=OPENAI_API_KEY)

    # nullable fields need type: ["string", "null"] under strict structured outputs
    tools = [
        {
            "type": "function",
            "function": {
                "name": "return_company_enrichment",
                "description": "Return company_size and industry inferred only from page text.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company_size": {
                            "type": ["string", "null"],
                            "description": "Employee range like '10-20', or null if not evidenced",
                        },
                        "industry": {
                            "type": ["string", "null"],
                            "description": "Short industry label, or null if not evidenced",
                        },
                    },
                    "required": ["company_size", "industry"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": ENRICH_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Company name (for context only — do not invent facts from it): "
                    f"{payload.company_name}\n\n"
                    "Website text gathered from the pages below. "
                    "Estimate company_size and industry only if clearly supported; "
                    "otherwise return null for that field.\n\n"
                    f"Pages fetched:\n{json.dumps(source_urls, indent=2)}\n\n"
                    f"Combined text:\n{combined_text}"
                ),
            },
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "return_company_enrichment"}},
    )

    message = response.choices[0].message
    if not message.tool_calls:
        raise HTTPException(status_code=502, detail="OpenAI did not return structured enrichment output")

    raw_args = message.tool_calls[0].function.arguments
    try:
        parsed = json.loads(raw_args)
        return EnrichResult(
            company_name=payload.company_name,
            company_size=parsed.get("company_size"),
            industry=parsed.get("industry"),
            pages_fetched=len(source_urls),
            source_urls=source_urls,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Invalid enrichment payload from OpenAI: {exc}",
        ) from exc


@app.post("/score", response_model=LeadScoreResult)
def score(lead: LeadData) -> LeadScoreResult:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Structured outputs via forced function calling + JSON schema.
    # OpenAI must call this tool, and the arguments must match the schema exactly.
    tools = [
        {
            "type": "function",
            "function": {
                "name": "return_lead_score",
                "description": "Return the lead qualification score as structured data.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "score": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Fit score from 1 (poor) to 10 (excellent)",
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Confidence given available (non-null) fields",
                        },
                        "reason": {
                            "type": "string",
                            "description": "One sentence explaining the score",
                        },
                    },
                    "required": ["score", "confidence", "reason"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SCORE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Score this enriched lead against the ICP. "
                    "Null fields are unknown — do not guess them.\n\n"
                    f"{lead.model_dump_json(indent=2)}"
                ),
            },
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "return_lead_score"}},
    )

    message = response.choices[0].message
    if not message.tool_calls:
        raise HTTPException(status_code=502, detail="OpenAI did not return structured score output")

    raw_args = message.tool_calls[0].function.arguments
    try:
        return LeadScoreResult.model_validate(json.loads(raw_args))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Invalid score payload from OpenAI: {exc}") from exc


@app.post("/draft", response_model=DraftResult)
def draft(payload: DraftRequest) -> DraftResult:
    # Gate before calling OpenAI — low scores never get a draft written.
    if payload.score < OUTREACH_SCORE_THRESHOLD:
        return DraftResult(
            drafted=False,
            message=(
                f"This lead doesn't meet the threshold for outreach "
                f"(score {payload.score}/10; need {OUTREACH_SCORE_THRESHOLD}+)."
            ),
        )

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    client = OpenAI(api_key=OPENAI_API_KEY)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "return_outreach_draft",
                "description": "Return a short, specific first-touch outreach message.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The outreach message body (2–4 short sentences)",
                        },
                    },
                    "required": ["message"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    lead_context = payload.model_dump(
        include={
            "name",
            "company",
            "title",
            "company_size",
            "industry",
            "linkedin_active_recently",
            "estimated_monthly_leads",
            "has_dedicated_sales_role",
            "recent_signal",
            "location",
            "score",
            "confidence",
            "reason",
        }
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Draft a first-touch outreach message for this qualified lead. "
                    "Use only facts present below; null means unknown.\n\n"
                    f"{json.dumps(lead_context, indent=2)}"
                ),
            },
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "return_outreach_draft"}},
    )

    message = response.choices[0].message
    if not message.tool_calls:
        raise HTTPException(status_code=502, detail="OpenAI did not return structured draft output")

    raw_args = message.tool_calls[0].function.arguments
    try:
        drafted_message = json.loads(raw_args)["message"]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Invalid draft payload from OpenAI: {exc}") from exc

    return DraftResult(drafted=True, message=drafted_message)


@app.post("/log", response_model=LogResult)
def log(payload: LogRequest) -> LogResult:
    # Idempotent — safe if startup already created the table.
    ensure_leads_table()

    try:
        row = insert_lead(
            {
                "name": payload.name,
                "company": payload.company,
                "title": payload.title,
                "company_size": payload.company_size,
                "industry": payload.industry,
                "linkedin_active_recently": payload.linkedin_active_recently,
                "estimated_monthly_leads": payload.estimated_monthly_leads,
                "has_dedicated_sales_role": payload.has_dedicated_sales_role,
                "recent_signal": payload.recent_signal,
                "location": payload.location,
                "score": payload.score,
                "confidence": payload.confidence,
                "reason": payload.reason,
                "drafted_message": payload.drafted_message,
                "status": payload.status or "New",
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to log lead: {exc}") from exc

    return LogResult(
        logged=True,
        id=row["id"],
        status=row["status"],
        message=f"Lead saved with id={row['id']}",
    )

