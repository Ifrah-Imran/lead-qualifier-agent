# Lead Qualifier Agent

An AI pipeline that takes a raw lead (name + company + website), enriches it with facts
scraped from the company's own site, scores it against an Ideal Customer Profile (ICP),
drafts a first-touch outreach message for qualified leads, and logs everything to Postgres
for review in a dashboard. n8n orchestrates the pipeline end to end via a webhook, and
ChromaDB gives the scoring/drafting prompts memory of past leads so similar companies get
similar treatment.

## Architecture

```
                     POST /webhook/new-lead
                             │
                             ▼
                    ┌─────────────────┐
                    │       n8n        │  orchestrates: enrich → score → draft → log
                    └────────┬─────────┘
                             │ HTTP calls
                             ▼
                    ┌─────────────────┐        ┌──────────────┐
                    │   FastAPI (api)  │◀──────▶│   ChromaDB    │  past-lead examples
                    │  /enrich /score  │        │ (lead memory) │  for prompt calibration
                    │  /draft  /log    │        └──────────────┘
                    │  /leads          │
                    └────────┬─────────┘
                             │
                    ┌────────┴─────────┐
                    │    Postgres       │  leads + draft_attempts tables
                    └────────┬─────────┘
                             │
                    ┌────────┴─────────┐
                    │  Next.js frontend │  GET /leads, PATCH /leads/{id}/status
                    │  (approve/reject) │
                    └───────────────────┘
```

- **FastAPI (`app/`)** — the core pipeline logic. Each endpoint is independently callable
  (useful for testing/backfills) and also chained together by n8n for the automated flow.
- **n8n** — the orchestrator. A Webhook node receives a raw lead and chains four HTTP
  Request nodes (`enrich → score → draft → log`), passing each response into the next
  node's request body. Workflow definition: [`n8n/lead-qualifier-workflow.json`](n8n/lead-qualifier-workflow.json).
- **Postgres** — persists logged leads (`leads` table) and tracks per-company outreach
  rate limiting (`draft_attempts` table, 24h cooldown).
- **ChromaDB** — stores an embedding of every logged lead (profile fields only, not the
  score) so `/score` and `/draft` can retrieve similar past examples and calibrate against
  them.
- **Next.js frontend (`frontend/`)** — read/review dashboard: lists leads from Postgres,
  lets a human approve or reject each one.

## Pipeline flow

1. An external system (a form, CRM export, or `scripts/run_batch.py`) sends raw lead data
   to n8n's webhook.
2. **`/enrich`** — scrapes the company's homepage + up to 2 related pages (about/team/careers),
   and uses an LLM (structured output, `gpt-4o-mini`) to extract `company_size` and
   `industry` *only* when clearly evidenced in the page text. Returns `null` rather than
   guessing.
3. **`/score`** — scores the enriched lead 1–10 against the [ICP](app/icp.py), with a
   `confidence` level (low/medium/high) that drops when key fields are missing. Retrieves
   similar past leads from ChromaDB as calibration context.
4. **`/draft`** — if `score >= 6` and the company hasn't been drafted for in the last 24h,
   writes a specific, human-sounding first-touch outreach message referencing real facts
   from the lead (never invents details). Otherwise returns `drafted: false` with an
   explanation.
5. **`/log`** — persists the full lead + score + draft to Postgres and stores an embedding
   in ChromaDB for future calibration.
6. A human reviews new leads in the dashboard and marks each **Approved** or **Rejected**.

## Local setup

```bash
cp .env.example .env        # fill in OPENAI_API_KEY and Postgres creds
docker compose up --build
```

This starts Postgres, ChromaDB, the FastAPI app (`http://localhost:8000`, docs at
`/docs`), and n8n (`http://localhost:5678`). See
[`n8n/lead-qualifier-workflow.json`](n8n/lead-qualifier-workflow.json) for the workflow to
import (n8n UI → Import from File), then activate it and use the webhook URL below.

Frontend:

```bash
cd frontend
cp .env.local.example .env.local
npm install && npm run dev   # http://localhost:3000
```

Run tests: `pytest -v`

For deploying this stack to a real server, see [DEPLOYMENT.md](DEPLOYMENT.md).

## API reference

All endpoints are on the FastAPI app (default `http://localhost:8000`). Interactive docs:
`GET /docs`.

### `GET /health`
Liveness check.

**Response** `200`
```json
{ "status": "ok" }
```

---

### `POST /enrich`
Scrapes a company's website and extracts `company_size` / `industry` if evidenced.

**Request**
```json
{ "company_name": "Plausible Analytics", "website_url": "https://plausible.io" }
```

**Response** `200`
```json
{
  "company_name": "Plausible Analytics",
  "company_size": "10-20",
  "industry": "B2B SaaS",
  "pages_fetched": 2,
  "source_urls": ["https://plausible.io", "https://plausible.io/about"]
}
```
`company_size`/`industry` are `null` when the site doesn't clearly evidence them.
Errors: `500` if `OPENAI_API_KEY` unset, `502` on a malformed/missing OpenAI response.

---

### `POST /score`
Scores an enriched lead against the ICP.

**Request**
```json
{
  "name": "Uku Taht",
  "company": "Plausible Analytics",
  "title": "Founder",
  "company_size": "10-20",
  "industry": "B2B SaaS",
  "linkedin_active_recently": true,
  "estimated_monthly_leads": null,
  "has_dedicated_sales_role": false,
  "recent_signal": "Bootstrapped SaaS company actively growing customer base",
  "location": "Estonia"
}
```
Only `name` and `company` are required; every other field accepts `null` for unknown.
`company_size` accepts an int, a plain numeric string, or a range like `"10-20"`
(parsed to its midpoint).

**Response** `200`
```json
{ "score": 8, "confidence": "medium", "reason": "Strong ICP fit but inbound lead volume is unknown." }
```
Errors: `422` on an unparseable `company_size`, `500`/`502`/`503`/`504` on OpenAI/Chroma failures.

---

### `POST /draft`
Writes a first-touch outreach message for a scored, qualified lead. Same body as `/score`
plus the score fields.

**Request**: `LeadData` fields + `score` (1–10), `confidence`, `reason`.

**Response** `200` — qualified and not rate-limited:
```json
{ "drafted": true, "message": "Hey Uku — saw Plausible's been growing fast without a dedicated sales hire..." }
```

**Response** `200` — below threshold (`score < 6`) or already drafted for this company in
the last 24h:
```json
{ "drafted": false, "message": "This lead doesn't meet the threshold for outreach (score 4/10; need 6+)." }
```

---

### `POST /log`
Persists a lead (+ score + draft) to Postgres and stores it in ChromaDB for future
calibration.

**Request**: all `LeadData` fields + `score`, `confidence`, `reason`, `drafted_message`
(nullable), `status` (defaults to `"New"`).

**Response** `200`
```json
{ "logged": true, "id": 12, "status": "New", "message": "Lead saved with id=12" }
```

---

### `GET /leads`
Returns all logged leads, most recent first. Response: array of `Lead` (all fields above
plus `id`, `status`, `created_at`).

---

### `PATCH /leads/{lead_id}/status`
Updates a lead's review status.

**Request**
```json
{ "status": "Approved" }
```
`status` must be `"Approved"` or `"Rejected"`.

**Response** `200`: the updated `Lead`. `404` if `lead_id` doesn't exist.

## Webhook trigger (n8n)

Once the workflow is imported and activated, POST a raw lead to kick off the full
pipeline:

```
POST http://localhost:5678/webhook/new-lead
Content-Type: application/json

{
  "name": "Jane Doe",
  "company": "Acme Inc",
  "website_url": "https://acme.com",
  "title": "Head of Sales",
  "linkedin_active_recently": true,
  "estimated_monthly_leads": 500,
  "has_dedicated_sales_role": false,
  "recent_signal": "Raised Series A",
  "location": "Austin, TX"
}
```

Only `name`, `company`, and `website_url` are required; the rest may be omitted (treated
as unknown, which lowers scoring confidence). The webhook responds with the `/log` result
once the whole chain completes.

## Repo layout

```
app/            FastAPI application (endpoints, DB, ChromaDB memory, scraping, config)
frontend/       Next.js leads dashboard
n8n/            Exported n8n workflow (source of truth, re-import after UI edits)
scripts/        Batch tooling (dry-run the pipeline over a CSV of prospects)
tests/          pytest suite
docker-compose.yml         Local dev stack (hot reload, all ports open on localhost)
docker-compose.prod.yml    Production stack (no reload, no --dev bind mounts)
docker-compose.caddy.yml   Optional overlay: HTTPS via Caddy + a domain
```
