"""Optional public navigation summaries. No network calls or ranking promises."""
import pathlib
import sys

import gen_content as content
import gen_price_guide as guide
import gen_market_report as report
import plans

ROOT = pathlib.Path(content.ROOT)


def render():
    prices = []
    for p in plans.DATA['plans'] + plans.DATA.get('passes', []):
        price = p['price']
        label = p['name']
        if label.lower() == 'free':
            period = 'free'
        elif p in plans.DATA.get('passes', []):
            period = 'one-time payment; 30 days; no renewal'
        else:
            period = 'per month'
        prices.append('- %s: EUR %s, %s.' % (label, price, period))
    links = [
        ('Product', '/'), ('Current plans and billing', '/plans'),
        ('Price-guide method', '/vinted-price-guide#method'),
        ('Price checker', '/vinted-price-checker'),
        ('Reselling workflow', '/how-to-resell-on-vinted'),
        ('Brand and model research', '/best-brands-to-resell-on-vinted'),
        ('Resale profit calculator', '/vinted-profit-calculator'),
        ('Search link builder', '/vinted-search-builder'),
        ('Phone alert setup and local device test', '/vinted-alerts-on-your-phone'),
        ('German price checker', '/de/vinted-preis-checker'),
        ('Spanish price checker', '/es/comprobar-precio-vinted'),
        ('Monthly reports and source data', '/vinted-market-report'),
        ('Italian checker', '/it/stima-prezzo-vinted'),
        ('Italian guide pilot', '/it/prezzi-vinted'),
        ('Support', '/support'),
    ]
    text = ('# SNYPD\n\n'
            '> Public Vinted search monitoring and alerts for new matching listings.\n\n'
            'SNYPD is independent of Vinted. It does not log into Vinted accounts, buy items,\n'
            'message sellers, or monitor price drops on existing listings.\n'
            'This optional navigation summary is not an access policy or a promise of search inclusion.\n\n'
            '## Public sources\n\n'
            + '\n'.join('- [%s](%s%s)' % (name, content.SITE, url) for name, url in links)
            + '\n\n## Pricing\n\n' + '\n'.join(prices)
            + '\n\nFree includes one search, with 24/7 monitoring for the first three days after saving\n'
            'the first search; afterwards it runs while the dashboard is open. Consult /plans\n'
            'for current limits and billing details.\n\n'
            '## Price data\n\n'
            + 'Observation window: %s to %s. Marketplace: vinted.be. Currency: EUR.\n'
            % (guide.WIN_FROM.isoformat(), guide.GEN.isoformat())
            + '%d overall estimates pass the publication checks; %d existing item guides explain\n'
            % (len(guide.PUB), len(guide.NOTE_ITEMS))
            + 'why an overall estimate is withheld and show validated condition data where available.\n'
            'These are asking prices, not completed-sale prices. The sample follows searches\n'
            'SNYPD users monitor and is not representative of every marketplace or seller location.\n'
            'Sample sizes for different item searches can overlap. Read the visible methodology.\n')
    extra = '\n## Reusable report downloads\n\n'
    for edition in report.EDITIONS:
        csv = report.csv_path(edition)
        extra += '- %s: %s/%s ; metadata: %s/%s\n' % (
            edition['name']['en'], content.SITE, csv, content.SITE, csv.replace('.csv', '.metadata.json'))
    extra += ('\nThe metadata supplies observation dates, source, licence, row count and checksum.\n'
              'The report datasets are CC BY 4.0 with attribution to the dated report.\n'
              'Country-language translations do not turn vinted.be samples into national price estimates.\n')
    return {'llms.txt': text, 'llms-full.txt': text + extra}


def main(check=False):
    changed = []
    for name, expected in render().items():
        path = ROOT / name
        if not path.exists() or path.read_text(encoding='utf-8') != expected:
            changed.append(name)
            if not check:
                path.write_text(expected, encoding='utf-8')
    print(('DRIFT: ' if check and changed else 'Search summaries: ') + (', '.join(changed) if changed else 'current'))
    return int(check and bool(changed))


if __name__ == '__main__':
    raise SystemExit(main('--check' in sys.argv))
