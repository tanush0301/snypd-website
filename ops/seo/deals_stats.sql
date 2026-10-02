-- Read-only statistics behind /vinted-deals (ops/seo/gen_content.py reads
-- ops/seo/data/deals-<edition>.json, which is this query's output, verbatim).
--
-- Run it in the Supabase SQL editor or via the MCP execute_sql tool, paste the
-- single JSON value it returns into the data file, then check the file's md5
-- against the "md5" column (computed over the same text). Never type a number.
--
-- Method, stated on the page:
--   * price_history rows first seen in a fixed 14-day window, vinted.be (EUR).
--   * A listing belongs to a model when its title contains every word listed.
--     This is a plain word match, not the Market Report's matching, so counts
--     differ from /vinted-prices.
--   * "Typical price" = median first asking price of that model in that
--     condition; conditions with fewer than 30 listings are left out.
--   * "Under" = first asking price at or below 70% (or 50%) of that median.
set statement_timeout = '60s';
with q(name, pat) as (values
  ('Nike Dunk Low',          array['dunk', 'low']),
  ('Stone Island jumper',    array['stone island']),
  ('New Balance 9060',       array['9060']),
  ('Adidas Campus',          array['campus']),
  ('Air Jordan 1 Mid',       array['jordan', '1', 'mid']),
  ('Salomon XT-6',           array['xt-6']),
  ('Carhartt Detroit jacket', array['carhartt', 'detroit'])),
win as (select timestamptz '2026-09-18 00:00:00+00' a, timestamptz '2026-10-02 00:00:00+00' b),
base as (
  select q.name, p.condition_raw c, p.first_price_cents fp
  from q cross join win
  join price_history p
    on p.currency = 'EUR' and p.marketplace = 'eu' and p.condition_raw is not null
   and p.first_seen_at >= win.a and p.first_seen_at < win.b
   and (select bool_and(lower(p.title) like '%' || t || '%') from unnest(q.pat) t)),
med as (
  select name, c, (percentile_cont(0.5) within group (order by fp))::numeric m, count(*) n
  from base group by 1, 2 having count(*) >= 30),
per_model as (
  select b.name,
         count(*) n,
         count(*) filter (where b.fp <= 0.7 * m.m) under30,
         count(*) filter (where b.fp <= 0.5 * m.m) under50,
         (select json_agg(json_build_object('condition', m2.c, 'median_cents', round(m2.m)::int, 'n', m2.n) order by m2.m desc)
            from med m2 where m2.name = b.name) ladder
  from base b join med m using (name, c)
  group by b.name),
doc as (
  select json_build_object(
    'window_start', (select a from win), 'window_end', (select b from win), 'days', 14,
    'marketplace', 'vinted.be', 'currency', 'EUR',
    'models', (select json_agg(row_to_json(per_model) order by n desc) from per_model))::text j)
select j, md5(j) from doc;
