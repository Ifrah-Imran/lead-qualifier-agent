"""Postgres helpers for the leads table."""

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
    score INTEGER,
    confidence TEXT,
    reason TEXT,
    drafted_message TEXT,
    status TEXT NOT NULL DEFAULT 'New',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
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
    :score,
    :confidence,
    :reason,
    :drafted_message,
    :status
)
RETURNING id, status, created_at;
"""


def ensure_leads_table() -> None:
    """Create the leads table if it does not already exist."""
    with engine.begin() as conn:
        conn.execute(text(CREATE_LEADS_TABLE_SQL))


def insert_lead(values: dict) -> dict:
    """Insert one lead row and return id/status/created_at."""
    with engine.begin() as conn:
        row = conn.execute(text(INSERT_LEAD_SQL), values).mappings().one()
        return dict(row)
