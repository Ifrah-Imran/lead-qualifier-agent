import json

from fastapi import FastAPI, HTTPException
from openai import OpenAI

from app.config import OPENAI_API_KEY
from app.icp import ICP
from app.schemas import LeadData, LeadScoreResult

app = FastAPI(title="Lead Qualifier Agent")

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


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/enrich")
def enrich():
    return {
        "status": "placeholder",
        "message": "Lead enrichment endpoint stub",
        "data": {},
    }


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


@app.post("/draft")
def draft():
    return {
        "status": "placeholder",
        "message": "Draft generation endpoint stub",
        "draft": "",
    }


@app.post("/log")
def log():
    return {
        "status": "placeholder",
        "message": "Activity logging endpoint stub",
        "logged": False,
    }
