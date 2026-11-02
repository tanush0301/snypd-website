-- Owner/admin console only. Read-only aggregate diagnostics; no historical writes.
-- The first result inventories the two attribution contracts over 28 calendar days.
-- Counts include test accounts unless an authoritative test-account exclusion is added.
begin read only;

select
  (created_at at time zone 'Europe/Brussels')::date as signup_day_brussels,
  count(*) as accounts,
  count(*) filter (where nullif(raw_user_meta_data->>'entry_page', '') is not null) as with_legacy_or_current_entry_hint,
  count(*) filter (where nullif(raw_user_meta_data->>'landing_path', '') is not null) as with_any_landing_path,
  count(*) filter (where raw_user_meta_data->>'landing_path_basis' = 'navigation_chain_v1') as with_versioned_navigation_path
from auth.users
where created_at >= ((date_trunc('day', now() at time zone 'Europe/Brussels') - interval '27 days') at time zone 'Europe/Brussels')
group by 1 order by 1;

-- Keep legacy entry_page separate. Do not call it a historical first landing page.
with classified as (
  select case
    when raw_user_meta_data->>'landing_path_basis' = 'navigation_chain_v1'
      and raw_user_meta_data->>'landing_path' ~ '^/[a-z0-9/-]{0,160}$'
      then 'navigation_chain_v1'
    when nullif(raw_user_meta_data->>'entry_page', '') is not null then 'legacy_entry_hint'
    else 'unknown' end as attribution_basis,
    case when raw_user_meta_data->>'landing_path_basis' = 'navigation_chain_v1'
      and raw_user_meta_data->>'landing_path' ~ '^/[a-z0-9/-]{0,160}$'
      then raw_user_meta_data->>'landing_path' else null end as navigation_path
  from auth.users
  where created_at >= ((date_trunc('day', now() at time zone 'Europe/Brussels') - interval '27 days') at time zone 'Europe/Brussels')
)
select attribution_basis, navigation_path, count(*) as accounts
from classified group by 1,2 order by 3 desc,1,2;

-- Discover candidate reporting functions; inspect the actual definition privately
-- before changing a growth RPC. No SQL definition or account record is exported.
select n.nspname as schema_name, p.proname as function_name
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.proname ilike '%growth%'
order by 1,2;
rollback;
