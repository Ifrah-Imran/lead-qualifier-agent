"""Postgres helpers for the leads table."""

import json

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import DATABASE_URL

engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True)

CREATE_LEADS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    company TEXT NOT NULL,
    title TEXT,
    company_size TEXT,
    industry TEXT,
    linkedin_active_recently BOOLEAN,
    estimated_monthly_leads INTEGER,
    has_dedicated_sales_role BOOLEAN,
    recent_signal TEXT,
    location TEXT,
    phone TEXT,
    social_links JSONB NOT NULL DEFAULT '{}'::jsonb,
    website_url TEXT,
    score INTEGER,
    confidence TEXT,
    reason TEXT,
    drafted_message TEXT,
    status TEXT NOT NULL DEFAULT 'New',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

ALTER_LEADS_ADD_CONTACT_COLUMNS_SQL = """
ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS social_links JSONB;
UPDATE leads SET social_links = '{}'::jsonb WHERE social_links IS NULL;
ALTER TABLE leads ALTER COLUMN social_links SET DEFAULT '{}'::jsonb;
ALTER TABLE leads ALTER COLUMN social_links SET NOT NULL;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS website_url TEXT;
"""

INSERT_LEAD_SQL = """
INSERT INTO leads (
    name,
    company,
    title,
    company_size,
    industry,
    linkedin_active_recently,
    estimated_monthly_leads,
    has_dedicated_sales_role,
    recent_signal,
    location,
    phone,
    social_links,
    website_url,
    score,
    confidence,
    reason,
    drafted_message,
    status
) VALUES (
    :name,
    :company,
    :title,
    :company_size,
    :industry,
    :linkedin_active_recently,
    :estimated_monthly_leads,
    :has_dedicated_sales_role,
    :recent_signal,
    :location,
    :phone,
    CAST(:social_links AS jsonb),
    :website_url,
    :score,
    :confidence,
    :reason,
    :drafted_message,
    :status
)
RETURNING id, status, created_at;
"""


LIST_LEADS_SQL = """
SELECT *
FROM leads
ORDER BY created_at DESC;
"""

UPDATE_LEAD_STATUS_SQL = """
UPDATE leads
SET status = :status
WHERE id = :id
RETURNING *;
"""

DELETE_LEAD_SQL = """
DELETE FROM leads
WHERE id = :id
RETURNING id;
"""


CREATE_DRAFT_ATTEMPTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS draft_attempts (
    id SERIAL PRIMARY KEY,
    company TEXT NOT NULL,
    drafted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_draft_attempts_company_time
    ON draft_attempts (lower(trim(company)), drafted_at DESC);
"""

CHECK_RECENT_DRAFT_SQL = """
SELECT 1
FROM draft_attempts
WHERE lower(trim(company)) = lower(trim(:company))
  AND drafted_at > NOW() - INTERVAL '24 hours'
LIMIT 1;
"""

INSERT_DRAFT_ATTEMPT_SQL = """
INSERT INTO draft_attempts (company) VALUES (:company);
"""


def ensure_leads_table() -> None:
    """Create application tables if they do not already exist, and self-migrate
    any columns added since a table was first created (idempotent, safe to
    run on every startup)."""
    with engine.begin() as conn:
        conn.execute(text(CREATE_LEADS_TABLE_SQL))
        conn.execute(text(ALTER_LEADS_ADD_CONTACT_COLUMNS_SQL))
        conn.execute(text(CREATE_DRAFT_ATTEMPTS_TABLE_SQL))


def company_drafted_recently(company: str) -> bool:
    """True if this company received a draft within the last 24 hours."""
    with engine.connect() as conn:
        row = conn.execute(text(CHECK_RECENT_DRAFT_SQL), {"company": company}).first()
        return row is not None


def record_draft_attempt(company: str) -> None:
    """Record a successful outreach draft for rate limiting."""
    with engine.begin() as conn:
        conn.execute(text(INSERT_DRAFT_ATTEMPT_SQL), {"company": company.strip()})


def insert_lead(values: dict) -> dict:
    """Insert one lead row and return id/status/created_at."""
    values = {**values, "social_links": json.dumps(values.get("social_links") or {})}
    with engine.begin() as conn:
        row = conn.execute(text(INSERT_LEAD_SQL), values).mappings().one()
        return dict(row)


def list_leads() -> list[dict]:
    """Return all leads, most recently created first."""
    with engine.connect() as conn:
        rows = conn.execute(text(LIST_LEADS_SQL)).mappings().all()
        return [dict(row) for row in rows]


def update_lead_status(lead_id: int, status: str) -> dict | None:
    """Update a lead's status and return the updated row, or None if it doesn't exist."""
    with engine.begin() as conn:
        row = conn.execute(text(UPDATE_LEAD_STATUS_SQL), {"id": lead_id, "status": status}).mappings().first()
        return dict(row) if row else None


def delete_lead(lead_id: int) -> bool:
    """Delete a lead by id. Returns True if a row was deleted, False if it didn't exist."""
    with engine.begin() as conn:
        row = conn.execute(text(DELETE_LEAD_SQL), {"id": lead_id}).first()
        return row is not None
