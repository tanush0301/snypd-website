-- Weekly SEO/GEO + activation scoreboard (sign-up side). Read-only. Run in Supabase (MCP execute_sql or the
-- SQL editor) and paste the result into C:\Users\Tanus\website\outreach\seo-geo-log.md.
-- Window: the last 7 days vs the 7 days before. Search/referrer numbers come from GSC, Bing and Vercel
-- Analytics (see the log's checklist); this file covers what only the database knows.
with params as (select now() - interval '7 days' as cur_start, now() - interval '14 days' as prev_start),
u as (
  select au.id, au.created_at,
         coalesce(au.raw_user_meta_data->>'utm_source', '(none)') as src,
         au.raw_app_meta_data->>'provider' as provider,
         au.raw_user_meta_data->>'entry_hunt' as entry_hunt,
         au.raw_user_meta_data->>'ui_lang' as ui_lang,
         case when au.created_at >= p.cur_start then 'this_week' else 'last_week' end as wk
  from auth.users au, params p
  where au.created_at >= p.prev_start
),
first_search as (
  select distinct on (s.user_id) s.user_id, substring(s.vinted_url from 'vinted\.([a-z.]+)/') as host
  from public.user_searches s join u on u.id = s.user_id
  order by s.user_id, s.created_at
)
select
  (select json_agg(t) from (select wk, count(*) signups,
          count(*) filter (where exists (select 1 from public.user_searches s where s.user_id = u.id)) with_search,
          count(*) filter (where exists (select 1 from public.push_subscriptions ps where ps.user_id = u.id)) with_push,
          count(*) filter (where entry_hunt is not null) via_price_guide
     from u group by wk order by wk desc) t) as by_week,
  (select json_agg(t) from (select wk, src, provider, count(*) n from u group by 1, 2, 3 order by 1 desc, 4 desc) t) as by_source,
  (select json_agg(t) from (select coalesce(fs.host, '(no search)') host, count(*) n
     from u left join first_search fs on fs.user_id = u.id where u.wk = 'this_week' group by 1 order by 2 desc) t) as first_search_site_this_week,
  (select json_agg(t) from (select coalesce(ui_lang, '(not set)') ui_lang, count(*) n from u where wk = 'this_week' group by 1) t) as ui_lang_this_week,
  (select json_agg(t) from (select coalesce(subscription_plan, '?') plan, count(*) n from public.users group by 1 order by 2 desc) t) as plans_now,
  (select count(*) from public.push_subscriptions) as push_subscriptions_total;
