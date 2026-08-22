# SNYPD Project Instructions & Operating Rules
> Auto-loaded project instructions for Claude Code, Qwen, Cursor, and AI Agents.
> Location: `C:\Users\Tanus\snypd_codebase\CLAUDE.md`

## 1. Project Overview & Value Proposition
* **Project:** SNYPD (`snypd.store`) - Near-real-time Vinted listing monitor.
* **Core Promise:** "You see relevant Vinted listings faster and more reliably than anyone else."
* **Stack:** FastAPI, RabbitMQ, Redis, Scraper Workers (asyncio/Playwright), Supabase Postgres, Caddy, Webflow/Vercel frontend.
* **Hosting:** IONOS VPS Germany (`82.165.195.178`).
* **Database:** Supabase (`igbuqanjocfmahlzzupc.supabase.co`).

---

## 2. The 11 Sacred Rules (Strictly Binding)
1. **Heartbeat gating is sacred:** Never scrape without an active user heartbeat in the last 60s.
2. **Server-side scraping only:** Frontend never scrapes; it pulses heartbeats and renders Supabase results over RLS.
3. **Drop listings >30 min old** on seed evaluation to eliminate spam alerts.
4. **Supabase ordering is authoritative:** Always `.order('uploaded_at_ts', {ascending: false})`.
5. **Strict JWT + Proxy pairing:** A Vinted token is permanently bound to its exact proxy IP (mismatch = instant 401/403 ban).
6. **Speed & reliability > elegance:** Zero missed listings outranks UI refactoring.
7. **No zombie background jobs:** Purge tasks immediately when a user disconnects or closes the tab.
8. **No silent failures:** All API errors, token expirations, and proxy exceptions must be logged and surfaced.
9. **Always verify running containers:** Never assume local files match running containers. Confirm state via `docker exec` and logs.
10. **Repeated polling model:** 60s repeat jobs, `page=1`, `per_page=3`, `order=newest_first`.
11. **Strict Webflow parity:** Wrap custom Vercel HTML between exported `template_start.txt` and `template_end.txt`.

---

## 3. Code Standards & Container Verification
* **Container Rebuilds:**
  ```bash
  docker compose down -v && docker compose build --no-cache && docker compose up -d
  ```
* **No Placeholders:** `# add logic here` is strictly forbidden. Provide concrete, copy-pasteable code blocks.
* **Surgical Edits:** Make surgical edits over rewrites, except for scraper worker `handle_task` which requires full clean block replacement to avoid indentation bugs.
* **Tone:** Direct, technical, data-driven. Zero corporate fluff, no cheerleading.
