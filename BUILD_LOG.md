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

  ## Day 1 (continued)
- Got Docker running after a restart fixed a WSL2 hang.
- Successfully ran docker compose up --build — saw FastAPI + Postgres
  containers start.
- Tested /score endpoint via the auto-generated docs page — confirmed
  it returns the placeholder JSON hardcoded in main.py, traced it back
  to the actual function to understand where the response comes from.
- Learned Git needs a configured name/email before committing
  (git config --global).
- Made first commit and pushed to GitHub successfully.