# Lead Qualifier — AI-Powered Lead Qualification & Outreach Agent

Stop spending 15-20 minutes manually researching every lead. This tool researches, scores, and drafts personalized outreach for you — automatically, with a clear explanation for every decision, and full control before anything goes out.

> 🎥 [Watch the demo on LinkedIn](https://lnkd.in/p/dZxD3_qA) — 90 seconds, shows a real lead going from raw company name to a scored, drafted, ready-to-send message

---

## The Problem

If you're running outreach — as a founder, an agency, or a sales team — every new lead means the same repetitive work: look up the company, figure out if they're actually worth pursuing, and write something that doesn't sound like a template. Multiply that by dozens of leads a week, and most of it either doesn't get done properly, or eats hours that should go toward actually closing deals.

## The Solution — and why it's worth using

Give it a company name and website. In seconds, it gives you back:

- **A fit score (1-10) with a plain-English reason** — not a black-box number, an actual explanation you can trust or push back on
- **The company's real size, industry, and contact details** — pulled live from their own website, so you're not guessing
- **A specific, ready-to-send outreach message** — written using real facts about that company, not a generic template
- **Full control** — nothing sends automatically. You review every draft and decide yourself.

The result: what used to take 15-20 minutes of manual research and writing per lead now takes seconds, without losing the personal touch that makes outreach actually work.

### For engineers reviewing this repo

- Full-stack, containerized system: FastAPI + PostgreSQL + ChromaDB (RAG) + n8n + Next.js, orchestrated via Docker Compose
- Structured LLM outputs (function calling) for reliable, parseable scoring and drafting — not prompt-and-hope
- Real debugging, not just implementation: found and fixed a self-reinforcing RAG retrieval bug (a lead's own past score was being retrieved as its own calibration example), a scraper-blocking bot-detection issue (missing browser headers), and an enrichment bug misreading customer counts as employee headcount — see [Known Limitations](#known-limitations) for what's still open
- Tested against real, uncurated companies (not synthetic data) throughout development, including deliberately adversarial cases (unreachable domains, JS-rendered sites, enterprise-scale companies that should be disqualified)
- CI/CD via GitHub Actions, automated tests with mocked external calls, structured error handling with correct HTTP status codes

---


## Architecture

```
                     ┌─────────────────────┐
   CSV Upload   ───▶ │                     │
   Webhook trigger──▶│        n8n          │  orchestration, triggers, routing
   (n8n-native,      │                     │
    ready for an     └──────────┬──────────┘
    external form)              │ calls
                                ▼
                     ┌─────────────────────┐
                     │   FastAPI Service    │
                     │  /enrich  /score      │
                     │  /draft   /log        │
                     │  /leads (GET/DELETE)  │
                     └──────────┬──────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
      ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
      │  PostgreSQL    │ │  ChromaDB      │ │  OpenAI API    │
      │  leads, audit  │ │  (vector DB,   │ │  scoring,      │
      │  log, rate     │ │   RAG          │ │  drafting,     │
      │  limiting      │ │   calibration) │ │  enrichment    │
      └───────────────┘ └───────────────┘ └───────────────┘
              ▲
              │
      ┌───────────────┐
      │  Next.js        │
      │  Dashboard      │
      │  (upload, review,│
      │   approve/reject)│
      └───────────────┘
```

---

## Key Features

- **Explainable scoring** — every score ships with a plain-language reason, not a black-box number
- **RAG-calibrated scoring & drafting** — references similar past leads via ChromaDB, with safeguards against self-reference and low-confidence contamination
- **Real web scraping with graceful degradation** — distinguishes "unreachable" from "no data found," rescues thin/JS-rendered pages, avoids bot-blocking
- **Contact extraction** — pulls email, phone, and social links automatically from the same pages already scraped
- **Human-in-the-loop guardrails** — score-threshold gating, 24-hour duplicate-outreach prevention, explicit Approve/Reject — nothing sends without you
- **CSV batch upload + tested + CI/CD** — process leads in bulk, backed by a pytest suite and GitHub Actions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend / API | FastAPI (Python), Pydantic |
| Database | PostgreSQL |
| Vector store / RAG | ChromaDB |
| LLM | OpenAI (`gpt-4o-mini`), structured outputs via function calling |
| Orchestration | n8n |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Containerization | Docker, Docker Compose |
| Testing / CI | pytest, GitHub Actions |
| Web scraping | requests, BeautifulSoup |

---

## Setup — run it yourself in under 5 minutes

**Prerequisites:** Docker Desktop installed, an OpenAI API key ([get one here](https://platform.openai.com/api-keys))

```bash
# 1. Clone the repo
git clone https://github.com/Ifrah-Imran/lead-qualifier-agent.git
cd lead-qualifier-agent

# 2. Set up your environment
cp .env.example .env
# open .env and add your OPENAI_API_KEY

# 3. Build and run everything (backend, database, vector store, orchestration)
docker compose up --build
```

That's it. Once the containers are running:

| What | Where |
|---|---|
| Dashboard (upload leads, review results) | [http://localhost:3000](http://localhost:3000) |
| API docs (interactive, auto-generated) | [http://localhost:8000/docs](http://localhost:8000/docs) |
| n8n (workflow orchestration) | [http://localhost:5678](http://localhost:5678) |

Upload a CSV of `company_name, website_url` pairs from the dashboard, or use the quick-test form to try a single company.

### Running the test suite
```bash
python -m venv venv
venv\Scripts\activate        # Windows — use source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
pytest -v
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/enrich` | POST | Scrape and extract company data from a website |
| `/score` | POST | Score a lead against the ICP with explainable confidence |
| `/draft` | POST | Draft outreach for a qualifying lead (gated by score threshold + rate limit) |
| `/log` | POST | Persist a lead and its results, store a calibration example |
| `/leads` | GET | List all leads |
| `/leads/{id}/status` | PATCH | Update a lead's status (Approved/Rejected) |
| `/leads/{id}` | DELETE | Delete a single lead |
| `/leads` | DELETE | Delete all leads (requires confirmation in UI) |

Full interactive documentation, including request/response schemas, is auto-generated at `/docs`.

---

## Known Limitations

Documented honestly, not hidden:

- **JS-rendered sites** — the scraper reads static HTML, so heavily JavaScript-rendered pages may return incomplete data. Partially mitigated with a meta-description fallback; a full fix needs headless-browser rendering (Playwright).
- **Scoring ceiling from missing data** — three ICP-relevant fields (LinkedIn activity, lead volume, dedicated sales role) currently have no data source and default to null. Since the ICP hard-gates on these, most leads cap around 5-6/10 even with strong fit otherwise. Fix: add manual input fields or a real enrichment source for these — next on the roadmap.
- **RAG sensitivity to sparse data** — leads with many missing fields can cluster together in retrieval. Self-reference and low-confidence filtering reduce this; full resolution depends on closing the gap above.

---

## Future Improvements

Not yet built — planned next steps, in rough priority order:

- [ ] **Connect a real external form** (Google Forms, Tally, or a custom landing page) to the existing n8n webhook trigger, so leads can flow in automatically from a live source instead of manual CSV upload
- [ ] **Real, persistent deployment** (Oracle Cloud or similar) with a public URL, so the tool is usable by someone other than the person running it locally
- [ ] **Input fields for the three ICP attributes with no current data source** (LinkedIn activity, monthly lead volume, dedicated sales role) — either as optional manual fields in the dashboard, or via a real enrichment source
- [ ] **Headless-browser scraping (Playwright)** for JavaScript-heavy sites the current scraper can't fully read
- [ ] **Bulk actions** on the leads dashboard (select multiple, approve/reject in one action) once lead volume grows enough to need it
- [ ] **LangChain/LangGraph refactor** as a deliberate framework-fluency exercise, on top of the current hand-built pipeline

---

## Author

Ifrah Imran — BS Data Science, COMSATS University Islamabad
[LinkedIn](https://www.linkedin.com/in/ifrah-imran-820a80325/) · [GitHub](https://github.com/Ifrah-Imran)
