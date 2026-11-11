-- first_session_report.sql (10 Nov 2026, website outreach/53, release R1). Read-only; run inside
--   begin transaction read only; ... rollback;
-- Reads only auth.users (a few hundred rows) and public.users. No big table is touched.
-- fs = user_metadata.fs, written by assets/first-session.js for accounts in their first 7 days.

-- 1. The funnel per first device (accounts whose record started in the window)
with f as (
  select a.id, a.raw_user_meta_data->'fs' as fs
  from auth.users a
  left join public.users u on u.id = a.id
  where a.raw_user_meta_data ? 'fs'
    and coalesce(u.is_test_account, false) = false
    and (a.raw_user_meta_data->'fs'->>'t0')::timestamptz >= now() - interval '14 days'
)
select fs->>'dev' as first_device,
       count(*) as accounts,
       count(*) filter (where (fs->>'wz')::int >= 1) as saw_wizard,
       count(*) filter (where fs ? 'max') as saved_first_hunt,
       count(*) filter (where (fs->>'wz')::int >= 3) as reached_alerts_step,
       count(*) filter (where (fs->>'al_try')::int >= 1) as tapped_turn_on,
       count(*) filter (where fs->>'al1' = 'ios') as shown_home_screen_text,
       count(*) filter (where fs->>'al1' = 'denied') as refused_permission,
       count(*) filter (where fs ? 'app') as opened_installed_app,
       count(*) filter (where fs->>'al' = 'on') as alerts_on,
       count(*) filter (where fs->>'later' = '1' and coalesce(fs->>'al', '') <> 'on') as later_and_still_off
from f
group by 1
order by accounts desc;

-- 2. The first hunt: price limit and minimum, and how often step 1 refused the form
with f as (
  select a.raw_user_meta_data->'fs' as fs from auth.users a
  where a.raw_user_meta_data ? 'fs' and (a.raw_user_meta_data->'fs'->>'t0')::timestamptz >= now() - interval '14 days'
)
select coalesce(fs->>'src', '(no hunt)') as saved_from,
       case when fs->>'max' = '1' then 'price limit' when fs->>'max' = '0' then 'no limit' else '-' end as price_limit,
       coalesce(fs->>'min', '-') as minimum,
       count(*) as accounts,
       count(*) filter (where (fs->>'werr')::int >= 1) as form_refused_at_least_once,
       count(*) filter (where (fs->>'hw')::int >= 1) as words_warning_shown
from f
group by 1, 2, 3
order by accounts desc;

-- 3. Set-up card and the "too broad" / coach card
with f as (
  select a.raw_user_meta_data->'fs' as fs from auth.users a
  where a.raw_user_meta_data ? 'fs' and (a.raw_user_meta_data->'fs'->>'t0')::timestamptz >= now() - interval '14 days'
)
select 'setup card' as card, coalesce(fs->>'card', '(never shown)') as last_state, count(*) from f group by 2
union all
select 'volume card (' || coalesce(fs->>'vol_k', '-') || ')', coalesce(fs->>'vol', '(never shown)'), count(*) from f group by 1, 2
order by 1, 3 desc;

-- 4. Where alerts finally came on, and how long after the first record
select fs->>'dev' as first_device, fs->>'al_dev' as alerts_on_device, count(*),
       percentile_disc(0.5) within group (order by extract(epoch from ((fs->>'al_on')::timestamptz - (fs->>'t0')::timestamptz)) / 60)::int as median_minutes
from (select a.raw_user_meta_data->'fs' as fs from auth.users a
      where a.raw_user_meta_data ? 'fs' and a.raw_user_meta_data->'fs' ? 'al_on'
        and (a.raw_user_meta_data->'fs'->>'t0')::timestamptz >= now() - interval '14 days') x
group by 1, 2
order by 3 desc;
