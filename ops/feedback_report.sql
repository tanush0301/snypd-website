-- feedback_report.sql (9 Nov 2026, website outreach/47, migration 081). Read-only; run in the Supabase SQL editor.
-- Table is small (~1 row per answer), so these are cheap.

-- 1. Counts by question / answer / plan (skips counted separately)
select question,
       coalesce(answer, case when skipped then '(skipped)' else '(text only)' end) as answer,
       coalesce(plan_at_answer, '?') as plan,
       count(*) as n,
       count(*) filter (where source = 'email') as via_email
from public.feedback_responses
group by 1, 2, 3
order by question, n desc;

-- 2. Answer rate per question (answered / shown; shown = answered + skipped)
select question,
       count(*) filter (where not skipped) as answered,
       count(*) filter (where skipped) as skipped,
       round(100.0 * count(*) filter (where not skipped) / nullif(count(*), 0), 1) as answer_pct
from public.feedback_responses
group by question
order by question;

-- 3. D score: share of "very disappointed", split by plan. Only meaningful at >= 40 answers.
select case when grouping(plan_at_answer) = 1 then 'all' else coalesce(plan_at_answer, '?') end as plan,
       count(*) as answers,
       round(100.0 * count(*) filter (where answer = 'very') / nullif(count(*), 0), 1) as very_pct,
       case when count(*) >= 40 then 'ok' else 'too few (<40)' end as reliability
from public.feedback_responses
where question = 'D' and not skipped
group by rollup (plan_at_answer)
order by plan;

-- 4. Text answers, newest first
select created_at, question, answer, plan_at_answer, source, detail
from public.feedback_responses
where detail is not null
order by created_at desc
limit 200;
