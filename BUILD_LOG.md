# Build Log

## Day 1 — [today's date]
- Set up the FastAPI + Postgres + Docker skeleton using Cursor.
- Learned: Docker packages an app so it runs identically on any computer;
  Docker Compose runs multiple containers (my app + database) together
  so they can talk to each other.
- Learned: Postgres is the database that stores my leads, scores, and logs
  persistently — separate from my app code.
- Learned: .env holds secret values (API key, DB password) separately
  from code, and .gitignore makes sure it never gets uploaded to GitHub.
- Next: run `docker compose up --build` and confirm the four placeholder
  endpoints (/enrich /score /draft /log) actually respond at
  http://localhost:8000/docs