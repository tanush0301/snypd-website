-- Homepage "What's moving" sample (ops/seo/home_market_sample.sql). Read-only, one small table
-- (market_daily_stats: one row per tracked search per day), six searches, 40 days. Output: one JSON line.
begin transaction read only;
set local statement_timeout = '5s';
\t on
\a
select json_build_object('read_at', to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'), 'series',
  (select json_object_agg(q, rows) from (
     select query_text as q, json_agg(json_build_array(day, median_cents, p25_cents, p75_cents, sample_size, distinct_sellers, verdict, reduced_pct) order by day) as rows
     from public.market_daily_stats
     where query_text in ('stone island hoodie', 'palace hoodie', 'yeezy foam runner', 'adidas handball', 'adidas spezial', 'levis 501', 'levi''s 501')
       and day >= current_date - 40
     group by query_text) s));
rollback;
