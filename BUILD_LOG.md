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

  ## Fixed real enrichment bug - false employee count
- /enrich returned "10001-50000" employees for SmoothLedger (a tiny 2025
  startup) - LLM was likely confusing a user/customer count on the page
  with employee headcount.
- Fixed by making ENRICH_SYSTEM_PROMPT explicit: only extract company_size
  from language clearly about team/staff/employees, never from user/
  customer/revenue numbers. Ambiguous cases now return null instead of
  guessing.
- This was caught by manually reviewing real output critically, not by
  automated tests - a reminder that automated tests don't catch every
  real-world failure mode.

  ## Major UI redesign + real bug fixes
- Redesigned the dashboard through multiple iterations (Notion-inspired
  light theme -> bold, dark, color-blocked card system) - landed on a
  dark fintech-inspired aesthetic with a color-coded lead card system
  and an icon sidebar.
- Fixed real bug: the lead card's title was showing the contact name
  (defaulting to "Unknown" when blank) instead of the company name.
  Company name is now the primary bold title; contact name shows as
  secondary text only when it's actually set.
- Added DELETE /leads/{id} (app/main.py, app/db.py) and a delete/trash
  icon with a confirmation prompt on each card - verified end to end by
  creating and deleting a real test lead.
- Investigated and clarified: enrichment nulls on Pinterest/Booking.com
  are a real scraper limitation (JS-rendered content isn't readable by
  requests+BeautifulSoup, no headless browser in the stack) - not a
  bug. Documented as a known constraint; a real fix would mean adding
  Playwright, deferred for now.
- Built contact info extraction: phone number + social links
  (LinkedIn/Instagram/Facebook) parsed from the same pages /enrich
  already fetches, no new requests. Required a real schema migration
  (leads.phone, leads.social_links) - caught two live bugs while
  testing against a real site (a `::jsonb` cast syntax error in the
  raw SQL, and existing rows getting NULL instead of '{}' for the new
  column, which crashed GET /leads) and fixed both before calling it
  done.
- Fixed drafted-message text getting clipped on some cards: the
  blockquote had no word-wrap safeguard, so a long unbroken string
  (e.g. a URL) in a generated message could overflow past the card's
  overflow-hidden boundary while normally-wrapping messages looked
  fine - inconsistent-looking, but one root cause.
- Reverted contact name back to optional in the quick-test form (had
  briefly made it required; the card-title fix means an unset name is
  now hidden entirely instead of showing "Unknown", so the optional
  field is no longer confusing).
- Found and fixed a real repo-hygiene bug: frontend/lib/ (api.ts,
  pipeline.ts, csv.ts, cardColors.ts) was silently gitignored this
  entire session by a Python-packaging `lib/` pattern that matches at
  any depth, not just repo root. Anchored it to `/lib/` in .gitignore
  so it only catches the intended Python build directory.
- Learned: verify AI-reported "done" claims against actual rendered or
  served output, not just written summaries - a couple of things got
  reported complete but weren't actually live (one CSS fix that didn't
  fully resolve until a second root cause was found; a migration that
  looked right on paper but had a syntax error only a real API call
  caught).