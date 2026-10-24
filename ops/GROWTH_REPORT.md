# Reproducible growth reporting

Run `python ops/growth_report.py /private/reconciled.json --output /private/report.json`.
Run tests with `python -m unittest discover -s ops -p test_growth_report.py`.
Python standard library only. The script does not fetch data, send analytics, or change production.

**Keep all real exports and outputs outside this repository and its Vercel deployment.**
Do not commit account IDs, email addresses, payment exports or private commercial reports.

## Export contract (version 1)

This is a normalized input format, not a claim that the production database has these columns.
An owner must reconcile a complete account export with successful Whop payments, refunds,
disputes and billing cycles. The previously supplied aggregate snapshot cannot reconstruct these rows.
Use opaque account/payment identifiers; no emails, search text, listing URLs or notification tokens.

Top-level keys:

- `schema_version`: 1.
- `as_of`: ISO timestamp with timezone. All data and refund/dispute state must reflect this cutoff.
- `coverage`: explicitly true for `accounts_complete`, `payments_reconciled`,
  `refunds_reconciled`, `renewal_dues_complete`. False or missing stops the report.
  Set `first_hunt_at`, `first_match_view_at`, `push_registered_at` true only when historical
  coverage is complete for the exported population. Missing/false means unavailable, never zero.
- `accounts`: all accounts created through cutoff, with explicit test flags.
- `payments`: all confirmed, nonzero successful payments through cutoff, including payments later refunded.
  Exclude failed attempts, checkout visits, free trials and duplicate webhook deliveries.
- `renewal_dues`: all recurring billing cycles due through cutoff (future rows may be included).
  Include unpaid due cycles. Exclude first purchases and Pass purchases. Use actual provider
  billing periods; do not assume every month has 30 days. Cancellation before a cycle becomes
  due is excluded: this is collection of due renewals, not overall subscriber retention.

Account fields: `id`, `created_at`, `is_test` (boolean), `source` (string or null),
`first_hunt_at`, `first_match_view_at`, `push_registered_at`, `trial_started_at`,
`trial_ends_at`, `trial_cohort`. Milestone and trial fields are timezone timestamps or null.
Under complete coverage null means confirmed absent. Use the effective trial end after extensions.
Use separate cohort labels, e.g. `legacy_7d`, `72h`, `72h_extended_48h`.
Do not infer a match view from a matching-listing database row, push send, or last_requested_at.
Do not infer push registration from browser permission alone. Existing deleted hunts require
historical evidence before claiming first-hunt coverage.

Payment fields: `id`, `user_id`, `paid_at`, `amount_minor`, `refunded_minor`, `currency`,
`disputed` (boolean), `product` (`pass`, `solo`, `kickstart`, `pro`, `elite`),
`kind` (`initial` or `renewal`), `subscription_id` (null for Pass).
Amounts are integers in each currency's minor units. Map Pass from the provider plan ID;
the internal entitlement name `solo` alone does not identify a subscription.
Refunds are cumulative through cutoff; disputed means an unresolved or lost dispute at cutoff.
Resolve unmatched payments before running. This script fails rather than silently dropping them.

Renewal fields: `id`, `user_id`, `subscription_id`, `due_at`, `payment_id` (null if unpaid).
Each payment can satisfy one billing cycle only. Include the complete prior payment history
so the first observed payment is the actual first payment, not a renewal from a truncated export.

## Metric definitions

| Metric | Numerator | Denominator |
|---|---|---|
| Seven-day activation | Accounts reaching each milestone within seven days of creation | Non-test accounts at least seven days old |
| Trial conversion | First confirmed payment between trial start and effective end + 7 days | Non-test trials whose entire window elapsed; exclude pretrial payers |
| First-payment refund observation | First payments retaining some value without dispute after 15 days | First payments at least 15 days old |
| Due renewal collection | Due cycles with matched successful payment by due + 7 days | Cycles whose due + 7-day window elapsed |

First-payment partial refunds are reported separately and count as retaining some value;
they must not be described as full-price retained customers. Refunds after day 15 still change
the current report: the observation window is not a promise of final retention. Trial conversion
counts a successful payment even if later refunded; consult the refund metric separately.
Renewal collection is gross successful payment and can include subsequently refunded renewals.
No metric here measures future willingness to pay, cancellation retention, profit or lifetime value.

Currencies remain separate. Gross, refunds and disputed gross are separate totals;
do not subtract disputed gross again without reconciling overlap with refunds. Fees and VAT
are not netted out. Pass revenue is never MRR. Source counts are descriptive and unadjusted
for cohort age; small counts are not evidence that one source performs better.

## Weekly review

1. Fix the cutoff and reconcile exports; preserve the source extracts privately.
2. Run validation; resolve unmatched IDs, duplicate payments and missing coverage.
3. Review activation for mature signup cohorts and conversion by trial version.
4. Inspect refunds, disputes and actual due renewals separately.
5. Segment by source, device, country and intended use only when joined evidence exists.
6. Compare releases using consistent eligibility windows; before/after comparisons remain
   confounded by traffic mix, trial changes, incident recovery and calendar effects.
7. Do not divide page visitors by unrelated account totals or treat page totals as nested steps.

See `ops/test_growth_report.py` for synthetic fixtures covering boundary conditions.
