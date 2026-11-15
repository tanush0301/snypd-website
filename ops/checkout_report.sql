-- checkout_report.sql (14 Nov 2026; website repo outreach/62, growth plan move 1). Read-only; run inside
--   begin transaction read only; ... rollback;
-- Reads auth.users (user_metadata.co, written by assets/checkout-record.js on /plans), public.users (test flag) and
-- public.whop_webhook_events (ground truth for payments). No big table is touched.
-- co fields: o opens | p last plan | pl plans opened | src / src1 last / first source | d device | ap Apple Pay
-- available | ld form loaded | fb hosted fallback shown | c closed without a result | cs seconds before the last
-- close | r last result (paid, failed, canceled) | t last open | t0 first record.

-- 1. Per last plan and device, accounts with a checkout opened in the last 28 days.
with c as (
  select a.id, a.raw_user_meta_data->'co' as co
  from auth.users a left join public.users u on u.id = a.id
  where a.raw_user_meta_data ? 'co' and coalesce(u.is_test_account, false) = false
    and (a.raw_user_meta_data->'co'->>'t')::timestamptz >= now() - interval '28 days'
)
select coalesce(co->>'p', '-') as last_plan, coalesce(co->>'d', '-') as device, count(*) as accounts,
       coalesce(sum((co->>'o')::int), 0) as opens,
       count(*) filter (where (co->>'ld')::int > 0) as form_loaded,
       count(*) filter (where (co->>'fb')::int > 0) as fallback_shown,
       count(*) filter (where (co->>'c')::int > 0) as closed_without_result,
       count(*) filter (where co->>'r' = 'paid') as paid_in_page,
       count(*) filter (where co->>'r' in ('failed', 'canceled')) as failed_or_canceled,
       count(*) filter (where co->>'ap' = '1') as apple_pay_available,
       percentile_disc(0.5) within group (order by (co->>'cs')::int) as median_secs_before_close
from c group by 1, 2 order by accounts desc;

-- 2. Where the first checkout open came from (email = trial-ended email, signup = plan button before sign-up,
--    dash = dashboard, site:<page> = one of our pages, other = another site, direct = no referrer).
with c as (
  select a.raw_user_meta_data->'co' as co
  from auth.users a left join public.users u on u.id = a.id
  where a.raw_user_meta_data ? 'co' and coalesce(u.is_test_account, false) = false
    and (a.raw_user_meta_data->'co'->>'t')::timestamptz >= now() - interval '28 days'
)
select coalesce(co->>'src1', '-') as first_source, count(*) as accounts,
       count(*) filter (where co->>'r' = 'paid') as paid_in_page
from c group by 1 order by accounts desc;

-- 3. Ground truth from Whop: of the accounts that opened a checkout, how many have a paid membership or payment
--    after their first record (the in-page result misses payments finished elsewhere).
with c as (
  select a.id, (a.raw_user_meta_data->'co'->>'t0')::timestamptz as first_open
  from auth.users a left join public.users u on u.id = a.id
  where a.raw_user_meta_data ? 'co' and coalesce(u.is_test_account, false) = false
    and (a.raw_user_meta_data->'co'->>'t')::timestamptz >= now() - interval '28 days'
),
paid as (
  select matched_user_id as uid, min(received_at) as first_paid
  from public.whop_webhook_events
  where matched_user_id is not null
    and (type = 'membership.activated' or (type like 'payment.%' and payload#>>'{data,status}' = 'paid'))
    and coalesce(payload#>>'{data,plan,id}', '') <> 'plan_jPBUwsY7FaO3w'  -- the free Whop plan
  group by 1
)
select count(*) as accounts_opened,
       count(*) filter (where paid.first_paid >= c.first_open - interval '1 minute') as paid_after_first_open
from c left join paid on paid.uid = c.id;
