# Leads Dashboard

Minimal Next.js frontend for the lead qualifier agent. Lists all leads from Postgres (via the FastAPI backend) with Approve/Reject buttons that update each lead's status.

## Setup

```bash
cp .env.local.example .env.local  # defaults to http://localhost:8000
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Requires the FastAPI backend running (`docker-compose up` from the repo root, or `uvicorn app.main:app --reload`) — this app calls `GET /leads` and `PATCH /leads/{id}/status` directly.
