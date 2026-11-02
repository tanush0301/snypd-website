"""Reproducible search builder, phone setup and DE/ES checker publication."""
from pathlib import Path
import sys

import gen_content as g
import gen_price_guide as prices
import expansion_content as copy
import plans

ROOT = Path(g.ROOT)
BUILDER_CSS = '''<style>.search-builder{padding:24px;border:1px solid #555560;border-radius:12px;background:#111116}
.builder-fields{display:grid;grid-template-columns:minmax(0,1fr) minmax(140px,1fr);gap:16px;align-items:center;margin:20px 0}
.search-builder input,.search-builder select,.search-builder textarea{box-sizing:border-box;width:100%;min-width:0;min-height:44px;border:1px solid #777;border-radius:6px;background:#19191f;color:#fff;padding:12px;font:inherit}
.search-builder textarea{font-size:14px;line-height:1.5;resize:vertical;overflow-wrap:anywhere}.search-builder label{font-size:15px;line-height:1.5}
.search-builder button{cursor:pointer}.search-builder [role=alert]{color:#ffbaba}.search-builder :focus-visible{outline:3px solid #00e5a0;outline-offset:3px}
[data-builder-result]{margin-top:20px}.search-builder .ct-actions{flex-wrap:wrap}
@media(max-width:600px){.search-builder{padding:16px}.builder-fields{grid-template-columns:1fr;gap:8px}.builder-fields input,.builder-fields select{margin-bottom:12px}}</style>'''
# Read prefill into memory, then remove only its sensitive parameters before any
# consent-managed analytics vendor can read the document URL. Campaign tags stay.
PREFILL = '''<script>(function(){window.SNYPD_BUILDER_PREFILL=location.search;try{var u=new URL(location.href);['q','max','currency','site'].forEach(function(k){u.searchParams.delete(k);});history.replaceState(null,'',u.pathname+u.search+u.hash);}catch(e){}})();</script>'''


def render():
    pages = {}
    for key, langs in copy.SLUGS.items():
        for lang, path in langs.items():
            title, desc, h1, lead, sections = (copy.builder if key == 'builder' else copy.phone)(lang)
            body = ''.join('<section id="%s"><h2>%s</h2>%s</section>' % s for s in sections)
            body += '<section id="start"><h2>%s</h2>%s</section>' % ('Commencer' if lang == 'fr' else 'Get started', g.cta(lang))
            text = g.page(key, lang, title, desc, 'VINTED · SNYPD', h1, lead,
                          [(i, h) for i, h, _ in sections], body, published=copy.UPDATED)
            if key == 'builder':
                text = text.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + PREFILL, 1).replace('</head>', BUILDER_CSS + '</head>', 1)
            pages[path.lstrip('/') + '.html'] = plans.fill(text, lang)
    for lang in ('de', 'es'):
        pages[g.SLUGS['checker'][lang].lstrip('/') + '.html'] = plans.fill(prices.page_checker(lang), lang)
    return {rel: g.stamp_modified(str(ROOT / rel), '\n'.join(line.rstrip() for line in text.splitlines()) + '\n')
            for rel, text in pages.items()}


def main(check=False):
    changed = []
    for rel, text in render().items():
        path = ROOT / rel
        if not path.exists() or path.read_text(encoding='utf-8') != text:
            changed.append(rel)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding='utf-8')
    print(('DRIFT: ' if check and changed else 'Expansion resources: ') + (', '.join(changed) if changed else 'current'))
    return int(check and bool(changed))


if __name__ == '__main__':
    raise SystemExit(main('--check' in sys.argv))
