-- Read-only statistics behind the monthly Vinted Market Report (ops/seo/gen_market_report.py
-- reads ops/seo/data/market-report-<edition>.json, which is this query's output, verbatim).
--
-- Run it via the Supabase MCP execute_sql tool or the SQL editor, paste the single JSON value
-- it returns into the data file, then check the file's md5 against the "md5" column (computed
-- over the same text). Never type a number. Set the window to the price guide's window
-- (ops/seo/data/price-guide.json: generated_at minus 14 days .. generated_at).
--
-- Method, stated on the page:
--   * price_history rows first seen in the window, vinted.be (EUR), i.e. listings that matched
--     SNYPD users' searches. Asking prices only.
--   * A price change is only visible for listings SNYPD saw at least twice (times_seen >= 2):
--     first_price_cents (first sighting) vs price_cents (latest sighting).
set statement_timeout = '60s';

with w as (
  select * from public.price_history
  where marketplace = 'eu' and currency = 'EUR'
    and first_seen_at >= timestamptz '2026-10-18 12:31:00+00' and first_seen_at < timestamptz '2026-11-01 12:31:00+00'
), seen as (
  select * from w where times_seen >= 2 and first_price_cents is not null and first_price_cents > 0
), cut as (
  select 100.0 * (first_price_cents - price_cents) / first_price_cents as pct from seen where price_cents < first_price_cents
), j as (
  select json_build_object(
    'window_start', '2026-10-18T12:31:00+00:00', 'window_end', '2026-11-01T12:31:00+00:00',
    'marketplace', 'vinted.be', 'currency', 'EUR',
    'listings', (select count(*) from w),
    'sellers', (select count(distinct seller_id) from w),
    'seen_twice', (select count(*) from seen),
    'price_cut', (select count(*) from cut),
    'price_raised', (select count(*) from seen where price_cents > first_price_cents),
    'cut_pct_p25', (select round(percentile_cont(0.25) within group (order by pct)::numeric, 1) from cut),
    'cut_pct_median', (select round(percentile_cont(0.5) within group (order by pct)::numeric, 1) from cut),
    'cut_pct_p75', (select round(percentile_cont(0.75) within group (order by pct)::numeric, 1) from cut),
    'condition_mix', (select json_object_agg(c, n) from (select coalesce(condition_raw, 'unknown') c, count(*) n from w group by 1) x)
  )::text as v
)
select v as json, md5(v) as md5 from j;
