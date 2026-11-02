# Search and registration measurement

Use separate, dated sources rather than presenting clicks as completed registrations.

| Metric | Definition | Authoritative source |
| --- | --- | --- |
| Search impressions and clicks | Search Console reporting window, property, country, query, device and landing URL | Search Console |
| Signup intent | A signup CTA was clicked; this is not an account creation | Consent-respecting browser event |
| Registered account | A distinct account created in the reporting window, excluding agreed test accounts | Auth/database account creation records |
| Verified email | A successful verification, separate from account creation | Auth confirmation records |
| Activated account | A registered account with a first successfully saved hunt | Database hunt/first-hunt records |
| Push enabled | A successful subscription, not merely a permission-button click | Subscription records |
| First useful match | First delivered qualifying match, using an agreed definition | Application delivery records |
| Paid conversion | A successful, matched payment; a plan/status row alone is insufficient | Whop payment records and fulfillment |

The browser sign_up event now requires an identified successful SDK response.
Google returns must have first-sign-in and creation timestamps within five seconds;
returning accounts are not counted solely because they were created in the previous
15 minutes. Duplicate calls are suppressed within the page. Account IDs and email
addresses are not included in event payloads. Existing consent controls are preserved.

Browser events remain consent-dependent estimates, not a cross-device unique-account
ledger. Server records are the basis for unique registrations and paid conversion.
Do not infer revenue from entitlements or interpret zero configured GA key events
as zero business sales.

For comparisons, retain the date range and source timezone. The supplied historical
snapshot contains a short GA summary window and a longer detail-event window.
Do not divide those numbers into a single conversion rate.

## Next account-side checks

1. Obtain a current 28-day Search Console export, retaining queries, pages, countries
   and devices, and compare with an equivalent preceding period.
2. Verify GA event definitions and key-event settings against actual account creation.
3. Join consented acquisition information to activation and payments only through the
   existing authorized data flow. Do not send email addresses or customer IDs to GA.
4. Review query intent before changing low-CTR pages. A page average can mix branded
   searches, countries, devices and different positions.
5. Evaluate the Italian pilot through qualified visits and activated accounts.
   More pages or a robots.txt allowance is not evidence of incremental traffic.

These account-side settings require access to the owner's Google properties.
No Search Console or GA configuration is silently assumed to have been changed.
