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

## Day 2
Built real /score logic using OpenAI structured outputs. Tested 3 cases (good/borderline/bad fit) — scores came back 10/7/1 respectively, with confidence correctly dropping to medium when lead data had unknowns. Confirms scoring discriminates properly
## Real end-to-end pipeline test
- Ran a real company (Plausible Analytics) through the full manual chain:
  /enrich (scraped 3 real pages, estimated company_size 10-20, industry
  B2B SaaS) → /score (8/10, medium confidence, correctly flagged missing
  lead-volume data) → /draft (specific message referencing real facts:
  bootstrapped, growing, no dedicated sales role).
- This is the first real proof the core pipeline works end to end on
  genuine data, not just synthetic test leads.
- Noted: still manually copying output from one endpoint into the next -
  n8n needs to automate this chaining next.
  ## Week 2 complete — full core pipeline working
- All four endpoints real and tested: /enrich (web scraping + LLM
  extraction), /score (ICP-based scoring with confidence), /draft
  (gated, specific message generation), /log (saves to Postgres).
- Verified full manual chain end-to-end on a real company (Plausible
  Analytics): enriched real data -> scored 8/10 medium confidence ->
  drafted a specific message -> logged to leads table (id=1).
- Schema stores company_size as TEXT to handle ranges from /enrich.
- Still manual: copying output from one endpoint into the next by hand.
  n8n needs to automate this chaining - that's the next real milestone.

  ## n8n pipeline automation complete
- Wired all four endpoints (enrich, score, draft, log) together in n8n
  using HTTP Request nodes, chained automatically via node references
  ({{ $node['name'].json.field }} expressions).
- Learned: n8n containers reach FastAPI via the Docker service name
  (http://api:8000), not localhost, since they're separate containers
  on Docker's internal network.
- Learned Fixed vs Expression fields: Fixed for values that never
  change (URL, method, content type); Expression for values pulled
  from previous nodes' output.
- Hit and fixed a real type-mismatch bug: /enrich returns company_size
  as a text range ("10-20"), but /score needs a number (parsed with
  parseInt + split) while /log needs the original text - same field,
  different type needs, handled per-node in n8n expressions for now.
- Full pipeline tested end-to-end on real data (Plausible Analytics),
  confirmed working: enrich -> score -> draft -> log, logged as id=2.
- Still to fix properly: move the company_size type handling into the
  actual Python code (/score's schema) instead of n8n expressions, so
  it's robust regardless of what's calling it.