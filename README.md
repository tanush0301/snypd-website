# SNYPD website and public market data

[SNYPD](https://www.snypd.store/) monitors public Vinted searches and alerts on new
matching listings. It does not buy items, sign into Vinted accounts, or monitor
price drops on existing listings.

## Reuse the aggregate market data

| Edition | Report and methodology | CSV | Metadata |
| --- | --- | --- | --- |
| October 2026 | [Report](https://www.snypd.store/vinted-market-report/october-2026) | [CSV](vinted-market-report-2026-10.csv) | [Metadata](vinted-market-report-2026-10.metadata.json) |
| November 2026 | [Report](https://www.snypd.store/vinted-market-report/november-2026) | [CSV](vinted-market-report-2026-11.csv) | [Metadata](vinted-market-report-2026-11.metadata.json) |

The published report datasets use [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Credit SNYPD and link to the dated report when reusing them. This data licence does
not separately license the website code, logos, photographs or other assets.

These are **asking prices observed on vinted.be**, not completed-sale prices or
country-specific estimates for every European marketplace. Searches are selected
by SNYPD users rather than a representative census. Item samples can overlap.
Each metadata file documents the observation window, marketplace, units, columns,
quality rule, row count, source URL and CSV checksum.

The CSVs contain one header and rectangular data rows. Source and licence details
live in their linked metadata rather than an irregular trailing comment row.
No seller identifiers, user accounts, listing descriptions or photographs are
included in these aggregate exports.

## Useful public tools

- [Price guide and methodology](https://www.snypd.store/vinted-price-guide)
- [Price checker](https://www.snypd.store/vinted-price-checker)
- [Italian price-checker pilot](https://www.snypd.store/it/stima-prezzo-vinted)
- [Italian model-guide pilot](https://www.snypd.store/it/prezzi-vinted)

Existing item URLs without a defensible overall estimate retain useful condition
data and limits. They are excluded from overall-price estimates rather than being
given an invented median. The November data correction is described on the report.

## Reproduce and verify publication

Canonical observations and content live under ops/seo/. Keep generated pages,
machine-readable summaries and downloads synchronized:

~~~sh
python3 ops/seo/gen_content.py
python3 ops/seo/gen_price_guide.py
python3 ops/seo/gen_reseller.py
python3 ops/seo/gen_expansion.py
python3 ops/seo/gen_market_report.py
python3 ops/seo/gen_regions.py
python3 ops/seo/gen_search_assets.py
python3 -c "import sys; sys.path.insert(0, 'ops/seo'); import prepublish; prepublish.write_sitemap()"
python3 ops/seo/test_search_publication.py
python3 ops/seo/check_site.py
python3 ops/seo/audit_search.py
~~~

The normal prepublish command additionally refreshes the public listings counter
from its existing API. The commands above regenerate local artifacts without that
network refresh. See ops/seo/MEASUREMENT.md for event definitions and account-side
measurement work.

The optional llms.txt files are navigation summaries generated from the same public
sources. They are not access controls, ranking guarantees, or a replacement for
crawlable, useful HTML.
