# Signup entry attribution

The website now preserves a public-page navigation chain through ordinary internal
links without adding cookies, session identifiers or a tracking vendor. Example:
`/fr/achat-revente-vinted` → calculator → builder → signup.

On an interaction with an internal public link, consent.js carries the existing
`from` page key and a new `entry_basis=nav-v1` marker. It excludes private pages,
downloads and external destinations. Query strings from the source page are not
copied wholesale. Existing validated campaign fields retain their own rules.

Email signup saves `entry_page` for compatibility. If a versioned navigation
chain is present it also saves `landing_path` (a path without query/hash) and
`landing_path_basis=navigation_chain_v1`. Google carries that context through its
return URL and fills missing fields only for an identified first sign-in. URL
cleanup within the auth page does not discard the initially captured context.

These are descriptive, unsigned browser observations, never authorization data.
They describe the initial public page in the carried navigation chain, not a
persisted visit, the user's first-ever touch, a verified acquisition source or
cross-device identity. Direct signup, bookmarks, stripped parameters, devices or
browser changes can leave attribution unknown. Legacy `entry_page` records do not
become historical landing paths. No past accounts are rewritten.

## Private reporting work

`ops/attribution_audit.sql` is a read-only aggregate diagnostic for an owner/admin
database console. It counts the old and new fields separately and lists candidate
growth reporting functions. It does not modify an RPC or infer payment conversion.
Keep its results outside the public repository.

The supplied dashboard grouped `landing_path` while the website saved
`entry_page`. The actual deployed RPC and historical metadata distributions were
not accessible through the connected frontend repository. The new frontend
contract is implemented; verifying or changing that private reporting RPC remains
pending an authorized database connection. Do not report an audit as executed or
the historical mismatch as repaired without that evidence.

If the report offers a legacy fallback, expose it as `legacy_entry_hint`, with its
own missing count. Preserve `navigation_chain_v1` as a separate category. Exclude
known test accounts only using an authoritative flag. Do not label unknown as
direct traffic. Use the reconciled export contract in `ops/GROWTH_REPORT.md` before
comparing paid outcomes; current paid-plan state is not a payment ledger.

## Tool events and evaluation

The builder emits `search_builder_generate`, `search_builder_copy` and
`search_builder_monitor` with `page_lang` only. Existing consent controls when GA
loads. No typed words, URL, budget or account ID is included in these custom
events. They count actions, not unique visitors, accounts or conversions.

The profit calculator passes a user-selected budget to the builder only when its
link is followed. The builder removes its prefill parameters from the visible
document URL before consent-managed vendor scripts load. Opening Vinted or the
signup link transmits the chosen search to that destination at the user's request.
The existing functional hunt-intent store lasts at most one day on that browser.

The current conversion hypothesis is that a useful budget/search handoff produces
more completed first hunts than generic signup copy. This release implements the
handoff; it does not claim a controlled A/B result. Before starting an experiment,
choose one eligible population and an account/hunt metric with a verified join,
record assignment and exposure under appropriate consent, and fix a sample size
and stop rule. Do not run many low-traffic variants or declare a paid winner from
the snapshot's small, unreconciled paid-plan count. Compare completed post-release
windows by country/device with matching scopes; before/after is observational.
