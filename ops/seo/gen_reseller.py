"""Render the EN/FR reseller resources (guide, brands, calculator, tools, money) from source and validated price data.

Run after gen_price_guide.py; --check is read-only and fails on stale output.
"""
import json
from pathlib import Path
import sys

import gen_content as g
import plans
import reseller_content as content

ROOT = Path(g.ROOT)


def render():
    index = json.loads((ROOT / 'assets/data/price-index.json').read_text(encoding='utf-8'))
    pages = {}
    for key, langs in content.SLUGS.items():
        for lang, path in langs.items():
            extra_ld = ()
            if key == 'resell':
                title, desc, h1, lead, sections = content.guide(lang)
            elif key == 'resell-brands':
                title, desc, h1, lead, sections = content.brands(lang, index, g)
            elif key == 'tools':
                title, desc, h1, lead, sections, extra_ld = content.tools(lang, index, g)
            elif key == 'money':
                title, desc, h1, lead, sections, extra_ld = content.money(lang, index, g)
            else:
                title, desc, h1, lead, sections = content.calculator(lang)
            body = ''.join('<section id="%s"><h2>%s</h2>%s</section>' % section for section in sections)
            body += content.related(lang)
            body += content.tools_sources(lang) if key == 'tools' else content.sources(lang, fees=key in ('profit', 'money'))
            body += '<section id="start"><h2>%s</h2>%s</section>' % (
                'Surveille ta recherche' if lang == 'fr' else 'Monitor your search', g.cta(lang))
            text = g.page(key, lang, title, desc, 'VINTED · REVENTE' if lang == 'fr' else 'VINTED · RESELLING',
                          h1, lead, [(i, h) for i, h, _ in sections], body, extra_ld=extra_ld,
                          published=content.PUBLISHED.get(key, content.UPDATED))
            rel = path.lstrip('/') + '.html'
            text = plans.fill(text, lang)
            pages[rel] = g.stamp_modified(str(ROOT / rel), text)
    return pages


def main(check=False):
    changed = []
    for rel, expected in render().items():
        path = ROOT / rel
        if not path.exists() or path.read_text(encoding='utf-8') != expected:
            changed.append(rel)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(expected, encoding='utf-8')
    print(('DRIFT: ' if check and changed else 'Reseller resources: ') + (', '.join(changed) if changed else 'current'))
    return int(check and bool(changed))


if __name__ == '__main__':
    raise SystemExit(main('--check' in sys.argv))
