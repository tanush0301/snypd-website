# SEO data refresh: monthly runbook

Written 18 Oct 2026 from the code in `ops/seo/` (nothing below was run while writing it). Repo root =
`C:\Users\Tanus\.gemini\antigravity\scratch\snypd-website`. Commands are Git Bash from the repo root unless marked
PowerShell. `ops/` never deploys (`.vercelignore`), so data files and scripts here are private.

## Hard rules (each one comes from a real incident)

- **Supabase is Free/Nano: 0.5 GB RAM, almost no disk headroom.** A query that reads `price_history` (~190 MB) or
  `listing_first_seen` from disk can starve the scraper's writes (17 Oct: writes fell to ~29% for 25 min; a later
  index build froze the DB for 27 min and needed a restart from the dashboard).
- **ONE heavy query at a time, off-peak, then stop and check health** (step 0 below) before the next one. At most the
  steps listed per day here. If anything looks slow: stop, do not start the next query, tell Tanush.
- **Never** run `CREATE INDEX` (also not `CONCURRENTLY`), `VACUUM FULL`, bulk `DELETE`, or `EXPLAIN ANALYZE` on these
  tables. Plain `EXPLAIN` (no ANALYZE) is fine: it does not execute the query.
- **Avoid busy minutes (UTC):** 03:00 (`price_history_retention` deletes rows with `last_seen_at` older than 14 days),
  every :20 (`listing_first_seen` retention), :03/:18/:33/:48 (trial email), Monday 06:00 (steals cron). Start at :07 or :37.
- **PostgREST roles time out at 8 s.** The batch scripts run inside the backend container with its own client; the
  `.sql` files run in the Supabase SQL Editor or the MCP `execute_sql` tool (as their headers say), never over REST.
- **`price_history` keeps 14 days.** The dated snapshot JSONs in `ops/seo/data/` are the ONLY price history SNYPD has:
  always commit them, never delete or overwrite an old one.
- **Never type a number into a page.** Every figure comes from a data JSON made by the script/SQL next to it. SQL
  output is pasted verbatim (no trailing newline) and its `md5sum` must equal the query's `md5` column.
- Push, VPS writes and anything Tanush has not seen: his OK first, per action.

## 1. What runs monthly and why

| Data | Made by (where) | Output | Feeds | Notes |
|---|---|---|---|---|
| Price guide | `price_guide_batch.py` (backend container, 47 Market Report runs, one after another) | `data/price-guide.json` + dated copy `data/price-guide-YYYY-MM-DD.json` | guide hub + item pages EN/FR/NL, `/vinted-price-checker`, sold-items pages, `assets/data/price-index.json`, homepage price cards (`gen_regions.HOME_ITEMS`) | Window = 14 days to `generated_at`. Monthly. |
| Market Report edition | `market_report_stats.sql` (SQL Editor / MCP) | `data/market-report-YYYY-MM.json` | new edition EN/FR, hub, `vinted-market-report-YYYY-MM.csv`, homepage link | **Window must equal the guide's** and run the same day as the guide (see step 2). |
| Deals | `deals_stats.sql` | `data/deals-YYYY-MM.json` | `/vinted-deals` (EN only) | Build stops if the condition example no longer holds. |
| Fees check | `fees_check.sql` | `data/fees-check-YYYY-MM.json` | `/vinted-fees`, `/fr/frais-vinted` | Build stops unless 100% of listings match the fee rule. |
| Comparison facts | by hand, vendors' own sites (Tanush's Chrome) | `COMPARE_CHECKED` in `compare_data.py` + `copy_pl_sv.py` | comparison pages (6 langs), alert hubs (8 langs) | Monthly per `compare_data.py` docstring. Date moves only after a real re-check. |
| Check interval | `check_interval.py` (scraper log, no DB) | `data/check-interval.json` | speed sentence on every SEO page, `plans.py`, `gen_regions.py` | Optional. All three generators exit if median != 30 s. |
| Weekly steals | `steals_batch.py`, VPS cron `snypd-steals-weekly` Mon 06:00 UTC | `~/snypd/logs/steals-<week>.json` (VPS) | preview only while `STEALS_HELD = True` (`gen_content.py`) | Monthly job: re-copy the item list to the VPS (step 4). |
| `price_report_batch.py` | — | `data/price-report-2026-09.json` | frozen September 2026 archive only | **Do not re-run.** Nothing else reads it. |

## 2. Preconditions and safety

- [ ] `git status --short` clean apart from known untracked files (`_local_preview_server.py`, `marketing/` never commit;
      anything else you did not make: leave it out of your commits).
- [ ] `git pull` / `git log origin/main..main` empty. Other AI tools edit this repo: re-read anything you rely on.
- [ ] Step 0 health check below passes. Supabase not restricted (watchdog prints `supabase=200`, DOCUMENTED format).
- [ ] Tanush knows the dates. No other heavy DB work planned those days.

**Step 0, health check (run before and after every heavy step):**
```
ssh snypd-vps "cd ~/snypd && python3 ops/watchdog.py --status"
ssh snypd-vps "docker logs --since 10m snypd-scraper-worker-2 2>&1 | grep -cE 'FAILED|PG_DIRECT_ERROR|ReadTimeout'"
ssh snypd-vps "docker logs --since 10m snypd-scraper-worker-2 2>&1 | grep -c PRICE_HISTORY_OK"
```
Pass = every shard >= 80% completion, queue < 2000, first count 0, second count > 0. The log tokens are DOCUMENTED in
CLAUDE.md, not re-checked here; if `docker ps` shows a different scraper container name, use that.
If it fails during a run: stop. The documented relief dial is `runtime_config.poll_interval_seconds` 30 -> 60 (a DB
write: Tanush's OK). A frozen DB is fixed only by Tanush restarting it in the Supabase dashboard.

## 3. Step by step: 1 November 2026

Plan: **Day 1 (Sun 1 Nov)** guide + Market Report = Release A. **Day 2 (Mon 2 Nov)** deals. **Day 3 (Tue 3 Nov)**
fees, then Release B with deals, fees and any comparison re-check. Dates below assume the guide runs on 1 Nov; if
`generated_at` says another date, use that date everywhere `2026-11-01` appears.

### Day 1, step 1: price guide batch (after 04:00 UTC)
```
python -c "import json;print(json.dumps([i['query'] for i in json.load(open('ops/seo/price_items.json',encoding='utf-8'))['items']]))" | ssh snypd-vps "cat > /tmp/q.json" && tr -d '\r' < ops/seo/price_guide_batch.py | ssh snypd-vps "cat > /tmp/pgb.py && docker cp /tmp/q.json backend:/tmp/q.json && docker cp /tmp/pgb.py backend:/tmp/pgb.py && docker exec backend python /tmp/pgb.py /tmp/q.json" > ops/seo/data/price-guide.json.new
```
(Same command as the script header, but written to `.new` so a failed ssh cannot truncate the live data file.)
Check it, then promote it and make the dated snapshot:
```
python -c "import json;d=json.load(open('ops/seo/data/price-guide.json.new',encoding='utf-8'));r=d['results'];print(d['generated_at'],len(r),'results',sum(not x['ok'] for x in r),'errors')"
mv ops/seo/data/price-guide.json.new ops/seo/data/price-guide.json && D=$(python -c "import json;print(json.load(open('ops/seo/data/price-guide.json'))['generated_at'][:10])") && cp ops/seo/data/price-guide.json ops/seo/data/price-guide-$D.json && echo $D
```
Expected: today's `generated_at`, 47 results, 0 errors (October: 47/0). Any error: do not continue; rerun later.
Snapshot name uses the UTC date of `generated_at` (the script header's `date +%F` is local time; same date off-midnight).
Run step 0.

**Publication rule** (`gen_price_guide.views()`, reused by the Market Report): not `skip` in `price_items.json`
(9 items skipped today), `display_verdict == 'ok'`, confidence medium/high, `sample_size >= MIN_LISTINGS` (100),
typical + range present. Per condition: shown only with verdict ok and `>= MIN_COND` (10) listings. October: 38 of 47.

### Day 1, step 2: Market Report SQL (same day as step 1, before the next 03:00 UTC)
Why same day: the query reads rows first seen in the guide's window; the 03:00 retention would delete the oldest of them.
Print the window (guide `generated_at`, seconds dropped, minus 14 days):
```
python -c "import json,datetime as t;g=t.datetime.fromisoformat(json.load(open('ops/seo/data/price-guide.json'))['generated_at'].replace('Z','+00:00')).replace(second=0);print((g-t.timedelta(days=14)).isoformat(),g.isoformat())"
```
In `ops/seo/market_report_stats.sql` replace all four window literals (two `timestamptz` in `where`, two strings in
`json_build_object`) with these two values, and add `set statement_timeout = '60s';` as the first statement (the deals
and fees files have it; this one does not). Run plain `EXPLAIN` on the query first: a `Seq Scan on price_history` means
a full read, so it must be the only heavy thing running. UNCLEAR: whether `price_history` has an index on
`first_seen_at`; the EXPLAIN tells you. Then run it once (SQL Editor or MCP `execute_sql`).
Paste the `json` column verbatim, **no trailing newline**, into `ops/seo/data/market-report-2026-11.json`, then:
```
md5sum ops/seo/data/market-report-2026-11.json; tail -c1 ops/seo/data/market-report-2026-11.json | od -c
```
Expected: md5 equals the `md5` column, last byte `}`, `window_start`/`window_end` = the printed window, `listings` > 0
(October: 317,962). Run step 0. **Day 1 has no more DB work.**

### Day 1, step 3: add the November edition in `gen_market_report.py`
Append to `EDITIONS` (the last entry is "latest"; nothing else needs a constant):
```python
    {'id': '2026-11', 'published': '2026-11-01', 'guide': 'price-guide-2026-11-01.json', 'stats': 'market-report-2026-11.json',
     'slug': {'en': 'november-2026', 'fr': 'novembre-2026'}, 'name': {'en': 'November 2026', 'fr': 'novembre 2026'}},
```
What then happens on its own: `SLUGS['mr:2026-11']` = `/vinted-market-report/november-2026` + `/fr/rapport-marche-vinted/novembre-2026`;
the hub "Latest" box and citation switch to November; the hub "All editions" table lists every `EDITIONS` entry newest
first, then the September archive row; `sitemap_pages()` adds both URLs with hreflang; `PAGE_MODIFIED['mreport']` =
latest `published`; the homepage link (`gen_regions.home_data`) points to November. October is not "archived": it keeps
its URL and stays in the table. Only September is a special archive (own renderer, `SEPT`, frozen).

**Month on month (built 18 Oct 2026, Tanush's choice):** every edition after the first compares itself with the one
before: a key-finding line first (rose/fell counts, median change, biggest rise/fall), a 'Change since last month'
section (typical asking price then/now per item published in both), `previous_typical_asking_eur` + `change_pct` CSV
columns, and the hub's latest findings lead with it. The 'first monthly report' sentence shows only on the first
edition. Tested with a synthetic November edition (scratch script, nothing written). Check November's numbers by eye:
a large median change usually means the mix of listings changed, which the page already says.
Also UNCLEAR: whether October should get a "newer edition available" line (no code for that today).

Note: every run re-renders ALL editions from their own snapshot, but with the CURRENT `price_items.json` (`skip`, names)
and `MIN_LISTINGS`/`MIN_COND`. Changing those changes October. Check its diff (step 5).

### Day 1, step 4: generate Release A
```
python ops/seo/gen_price_guide.py && python ops/seo/gen_market_report.py && python ops/seo/prepublish.py
```
Expected: `items published: N of 47 (min 100 listings)`; `wrote vinted-market-report/november-2026.html` and the FR
twin and `vinted-market-report-2026-11.csv`; prepublish prints counters, `sitemap.xml: 173 URLs` (171 today + 2) if the
item set did not change (each item gained/lost = +/-3 with NL), check_site exit 0.
Verify:
```
git diff --stat; git diff sitemap.xml | grep '^[-+].*<loc>'; git diff vinted-market-report/october-2026.html fr/rapport-marche-vinted/octobre-2026.html
```
- A `-<loc>` for a guide item = it failed the rule this month. Its old HTML is NOT deleted and stays live with old
  numbers, out of the sitemap and hub. **UNCLEAR, ask Tanush:** keep, redirect, or remove (no code handles this).
- October diff: only the wording you chose in step 3. Any number change = stop and find out why.
- `gen_regions` exits if fewer than 3 of `HOME_ITEMS` are published: edit that list (a choice, not a number).

Re-copy the steals item list to the VPS (the cron counts only what this file lists; back up first, VPS write = OK):
```
python ops/seo/steals_items.py > ops/seo/data/steals_items.json.new && ssh snypd-vps "cp ~/snypd/ops/steals/steals_items.json ~/snypd/ops/steals/steals_items.json.bak.$(date +%Y%m%d)" && scp ops/seo/data/steals_items.json.new snypd-vps:snypd/ops/steals/steals_items.json && rm ops/seo/data/steals_items.json.new
tr -d '\r' < ops/seo/steals_batch.py | md5sum; ssh snypd-vps "md5sum ~/snypd/ops/steals/steals_batch.py"
```
If the two md5s differ, the VPS batch is stale: copy it too (`tr -d '\r' < ops/seo/steals_batch.py | ssh snypd-vps "cat > ~/snypd/ops/steals/steals_batch.py"`).
Release A now (section 4).

### Day 2 (Mon 2 Nov, after 07:00 UTC, steals cron done): deals
In `ops/seo/deals_stats.sql`, `win` CTE: `'2026-10-19 00:00:00+00'` to `'2026-11-02 00:00:00+00'` (14 days; `'days', 14`
stays). UNCLEAR: retention keys on `last_seen_at`, so listings first seen 19 Oct before ~03:00 UTC and never seen again
are already gone by 2 Nov; October's run had the same gap (window started 18 Sep, ran 2 Oct 22:12). Accept it, or use a
13-day window AND change `'days'`. Step 0, plain `EXPLAIN`, run once, paste `j` verbatim to `ops/seo/data/deals-2026-11.json`,
`md5sum` = `md5` column. In `gen_content.py` set `DEALS = ... 'deals-2026-11.json'`. Step 0.

### Day 3 (Tue 3 Nov): fees
In `ops/seo/fees_check.sql`, `win`: `'2026-10-26 00:00:00+00'` to `'2026-11-02 00:00:00+00'` (7 days by `last_seen_at`,
like October). Same routine -> `ops/seo/data/fees-check-2026-11.json`; set `FEES_CHECK` in `gen_content.py`. `FEES_CHECKED`
("price lists read on 2 October 2026") changes only if someone re-reads Vinted's price lists (Tanush's Chrome, never the
proxies). UNCLEAR: whether that re-read is monthly; nothing in the code says so.

### Any day, no DB: check interval (optional) and comparison facts
```
ssh snypd-vps "docker logs --since 24h snypd-scraper-worker-2 2>&1 | grep '\"QUEUE_CONSUME\"'" | python ops/seo/check_interval.py > ops/seo/data/check-interval.json.new
```
Keep it only if it exits 0 and `median_seconds` is 60 (30 before the 19 Oct 2026 poll change; the copy says "about once a minute"): `mv ops/seo/data/check-interval.json.new ops/seo/data/check-interval.json`.
Otherwise delete the `.new` and tell Tanush (the "about once a minute" copy would be wrong).
Comparison: re-check every vendor fact on its own site, write the evidence file
(`C:\Users\Tanus\website\outreach\research-2026-11-XX-competitors.md`), fix `COMPETITORS` / `ALERT_WAYS` in
`compare_data.py` (and `WAY_CELLS` prices in `copy_pl_sv.py`), then set `COMPARE_CHECKED` + `COMPARE_CHECKED_SHORT`
(6 langs, `compare_data.py`) and `COMPARE_CHECKED` (pl, sv, `copy_pl_sv.py`). They drive the "checked on" date,
eyebrow and FAQ dates on the comparison pages and the alert-hub intro/FAQ. Never move the date without the re-check.

### Day 3: generate Release B
```
python ops/seo/gen_content.py && python ops/seo/prepublish.py
```
Expected: `wrote vinted-deals.html`, `wrote vinted-fees.html`, `wrote fr/frais-vinted.html`, no `sys.exit` from the deals
or fees guards, check_site exit 0. Pages whose `<main>` changed get today's `Updated` date automatically; others keep theirs.

## 4. Release and verification

1. `git status --short`, then add each path by name (never `-A`). Release A typically:
```
git add ops/seo/data/price-guide.json ops/seo/data/price-guide-2026-11-01.json ops/seo/data/market-report-2026-11.json ops/seo/market_report_stats.sql ops/seo/gen_market_report.py vinted-price-guide.html vinted-price-guide fr/guide-prix-vinted.html fr/guide-prix-vinted nl/vinted-prijzen.html nl/vinted-prijzen vinted-price-checker.html fr/estimer-prix-vinted.html assets/data/price-index.json vinted-market-report.html vinted-market-report fr/rapport-marche-vinted.html fr/rapport-marche-vinted vinted-market-report-2026-11.csv index.html signup.html login.html reset-password.html sitemap.xml
```
   plus any sold-items page `git status` lists (EN/FR/DE/IT/ES). Release B: the two data JSONs, the two `.sql` files,
   `gen_content.py` (+ `compare_data.py`, `copy_pl_sv.py`, `check-interval.json` if changed) and the HTML `git status` shows.
2. `git commit`; `git log -1 --format=%ae` must be `khtanush@gmail.com` (else Vercel blocks the deploy).
3. `git log origin/main..main` : read every commit. **Tanush's OK**, then `git push origin main`.
4. Vercel project `prj_ZgI9YGSaoupHwDpNScYoLCLcR0Jz` (team `team_ldKDX1XcCVYjnwALBks07B8t`): the deployment for that SHA is READY.
5. Live bytes = commit: `curl -s https://www.snypd.store/vinted-market-report/november-2026 | md5sum` vs
   `md5sum vinted-market-report/november-2026.html` (same for the hub and one guide item).
6. Screenshots + checks at 390 and 1440 px: copy `ops/qa/shots_1018.js` to `ops/qa/shots_1101.js`, set its `pages` list
   (new edition EN/FR, both hubs, guide hub, one item, /vinted-deals, /vinted-fees), then
   `MSYS_NO_PATHCONV=1 node ops/qa/shots_1101.js https://www.snypd.store <scratch dir>`. Pass: status 200, `overflow`
   false, `errs` 0, `ld` true on every row; look at the PNGs.
7. IndexNow, **PowerShell only**, changed pages only (replace `<BASE>` with the SHA before the release):
```
$p = git diff --name-only <BASE> HEAD -- '*.html' | ForEach-Object { ('/' + ($_ -replace '\.html$','')) -replace '^/index$','/' } | Where-Object { $_ -ne '/404' }; python ops/seo/indexnow.py @p
```
   Expected `IndexNow HTTP 200` or `202`. Google: request indexing of the new edition in Search Console (by hand).
8. Log it: `outreach/seo-geo-log.md` and CLAUDE.md per its update rule.

## 5. Rollback

- **Before push:** `git checkout -- <file>` or `git restore`; a bad data file: rerun its step (old snapshot files stay).
- **After push:** `git revert --no-commit <sha> && git checkout <sha> -- ops/seo/data/ && git commit` : pages go back,
  the new snapshot JSONs stay (they are the only history and never deploy). Same push checks, Tanush's OK.
  Vercel "Instant Rollback" is faster for the live site, but the next push redeploys `main`: still revert in git.
- **A published edition URL should not vanish** (it is meant to be cited): prefer a fix-forward wording change.
  Withdrawing one needs Tanush's decision and a redirect.
- **VPS:** `ssh snypd-vps "cp ~/snypd/ops/steals/steals_items.json.bak.<YYYYMMDD> ~/snypd/ops/steals/steals_items.json"`.
- **DB:** every query here is read-only, so there is nothing to undo; a slowed DB recovers by stopping (section 2).
- IndexNow pings cannot be undone; ping the same paths again after the fix.

## 6. Adding a new language (checklist from how `copy_pl_sv.py` was wired, 18 Oct 2026)

Put the copy in its own module (like `copy_pl_sv.py`) and wire it with one `install(globals())` call near the end of
`gen_content.py`. Everything below is a dict entry keyed by the language code.
- [ ] `LIVE[lang] = True` (or False to build into `ops/seo/preview/` for review), `LANG_NAME[lang]`.
- [ ] Dates: `_MONTHS`, `MONTHS_TXT`, `_SPAN_SAME_MONTH`, `_SPAN_TWO_MONTHS` (grammar: Polish uses the genitive).
- [ ] `SPEED_MEASURED[lang]` from `CHECK` via `_check_span(lang)` (never a typed number), `VINTED_LAG`, `TRIAL`
      (`@@trial_days@@` token, filled from `plans.json`).
- [ ] `SLUGS[key][lang]` for every page built (pl/sv: `bot`, `notify`).
- [ ] `UI[lang]`: locale, toc, updated, by, nav, login, start, footer tag/text/links, legal links, home.
- [ ] CTA: `cta()` returns `cps.CTA[lang]` for the module's languages; add the same hook for a new module.
- [ ] `PLANS_ROWS[lang]` / `PLANS_HEAD[lang]` with `@@price:...@@` / `@@searches:...@@` tokens only.
- [ ] `SHOT_TEXT[lang]` (screenshot captions; pl/sv: `feed`).
- [ ] `compare_data`: `COMPARE_CHECKED` (and `COMPARE_CHECKED_SHORT` if the comparison page is built), `HELP435`,
      `HELP433`, `HELP435_QUOTE` (verbatim from the local Vinted help page, with date), `HELP435_TITLE`, `ALERT_WAYS_HEAD`,
      `SOURCE_WORD`, `VINTED_HELP_WORD`.
- [ ] `ALERT_WAYS` cells (`name`, `get`, `how`, `cost`) for every row; `install()` raises KeyError on a row it lacks.
- [ ] `copy_alerts_compare`: `PUSH`, `WAYS`, `NOTIFY`.
- [ ] Page renderer: `page_bot()` hands pl/sv to `cps.page_bot_pl_sv`; a new language needs its hook or its own branch.
- [ ] `live_langs()` tuple in `gen_content.py` must contain the code, or the page gets no hreflang/sitemap entry.
- [ ] Main write loops in `gen_content.py` `__main__`: the bot loop tuple (`'de','nl','it','es','pl','sv'`) and the
      `for lang in cps.LANGS` notify loop; add the new code where its pages are written.
- [ ] `check_site.py BANNED`: add the new language's words for "instant", "real-time", "fastest", "safe",
      "undetectable", "allowed by Vinted", "sold prices", and its negation words to `NEGATION` (pl/sv added 18 Oct 2026).
- [ ] Then: `python ops/seo/gen_content.py && python ops/seo/prepublish.py` (hreflang reciprocity is checked),
      native-speaker or Tanush review, screenshots at 390/1440, IndexNow for the new paths only.
