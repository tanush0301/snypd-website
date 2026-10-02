-- Read-only check behind /vinted-fees and /fr/frais-vinted: does Vinted's Buyer
-- Protection fee on real vinted.be listings equal EUR 0.70 + 5% of the item price,
-- rounded to the nearest cent (half up), and is the buyer's total price + fee?
-- price_history stores Vinted's own service_fee_cents and total_price_cents per listing.
--
-- Paste the single JSON value into ops/seo/data/fees-check-<edition>.json and check
-- its md5 against the "md5" column. Never type a number. The rule tested here is the
-- same integer formula the page calculator uses: 70 + floor((cents * 5 + 50) / 100).
set statement_timeout = '60s';
with win as (select timestamptz '2026-09-25 00:00:00+00' a, timestamptz '2026-10-02 00:00:00+00' b),
s as (
  select p.price_cents pc, p.service_fee_cents f, p.total_price_cents t
  from price_history p cross join win
  where p.currency = 'EUR' and p.marketplace = 'eu' and p.service_fee_cents is not null
    and p.price_cents > 0 and p.last_seen_at >= win.a and p.last_seen_at < win.b),
doc as (
  select json_build_object(
    'window_start', (select a from win), 'window_end', (select b from win),
    'marketplace', 'vinted.be', 'currency', 'EUR',
    'listings', count(*),
    'fee_matches', count(*) filter (where f = 70 + floor((pc * 5 + 50) / 100)),
    'total_matches', count(*) filter (where t = pc + f),
    'min_price_cents', min(pc), 'max_price_cents', max(pc))::text j
  from s)
select j, md5(j) from doc;
