# Signup confirmation recovery

The 14 October 2026 incident showed `email_not_confirmed` login failures, a confirmation resend, and then `/verify` returning `One-time token not found`. The HTTP 303 was an error redirect, not a successful verification. The evidence does not establish whether an older/superseded link, a mail scanner, or another token problem caused the rejection. Site URL and `/login` redirect allowlisting were correct when inspected.

`assets/auth.js` now takes unconfirmed logins and expired confirmation links straight to an email/code form at `/login?verify=1`. Resend is explicit, validated and throttled in the UI (Supabase remains the authority for rate limits). Invalid codes remain recoverable. Verification errors cannot fall through to a cached account. A code submission opens the dashboard only when Supabase returns a confirmed session for the submitted email. Passwords and codes are never stored by this UI; the pending email is retained only in sessionStorage for a refresh in the same tab.

## Coordinated rollout

1. Deploy `assets/auth.js` plus generated `assets/i18n.js`. Translation source is `ops/i18n/fr.py`; regenerate with `python ops/i18n/gen_i18n.py`.
2. Verify `/login?verify=1` renders the code form in production.
3. In Supabase Auth > Emails > Confirm sign up, replace the body with `confirm-signup-email.html`. Keep the bilingual subject. It uses `{{ .Token }}` and a neutral entry link. Do not restore `{{ .ConfirmationURL }}` alongside the code: scanners could consume the shared one-time credential by following that link.
4. Keep Confirm email enabled. Use a bounded email OTP expiry (recommended 1800 seconds). The expiry also applies to other email OTP/link flows. The UI accepts 6–10 digits to support provider length changes.
5. Complete a fresh signup with a controlled real inbox: confirm on another browser, verify dashboard access and matching Supabase `email_confirmed_at`; test latest-code resend and reused-code recovery. The regression suite mocks the provider and does not establish email delivery or live end-to-end signup success.

## Regression checks

Run `cd ops/auth && npm ci && npm test` (Node 20+). Tests cover code verification, leading zeros, wrong/missing session, stale session, signup and unconfirmed login, returned/thrown legacy callback errors, expired hosted links, resends, duplicate submission, timeout, basic login/OAuth/recovery compatibility, French copy, and scanner-safe email markup.

## Recovery / rollback

If the code UI has a production problem, restore the previous confirmation template first (a bilingual `{{ .ConfirmationURL }}` link), then revert this frontend change. Never leave a code-only email paired with the old frontend. Existing valid hosted confirmation links remain compatible with this frontend. Already confirmed accounts use normal login. Do not manually confirm arbitrary users or disable email confirmation as a workaround.

Inspect Supabase auth logs for `/verify` errors and successful confirmation events; do not export token-bearing URLs, codes, access tokens, or refresh tokens. A passed mocked test suite cannot guarantee every mailbox provider or future signup will succeed.
