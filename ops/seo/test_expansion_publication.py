"""Publication, language, discovery and import-order regressions."""
import json
import re
from pathlib import Path
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

import gen_expansion
import expansion_content as copy
from test_reseller_publication import Page

ROOT = Path(gen_expansion.g.ROOT)


class ExpansionTests(unittest.TestCase):
    def test_generated_outputs_match_source(self):
        for rel, text in gen_expansion.render().items():
            self.assertEqual((ROOT / rel).read_text(encoding='utf-8'), text, rel)

    def test_new_pages_have_real_metadata_and_are_discoverable(self):
        urls = [e.text for e in ET.parse(ROOT / 'sitemap.xml').findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertEqual(len(urls), len(set(urls)))
        for rel in gen_expansion.render():
            text = (ROOT / rel).read_text(encoding='utf-8')
            page = Page(text)
            url = 'https://www.snypd.store/' + rel.removesuffix('.html')
            self.assertEqual(page.canonical, [url])
            self.assertEqual(page.h1, 1)
            self.assertIn(url, urls)
            self.assertEqual(len(page.ids), len(set(page.ids)))
            self.assertTrue(all(link[1:] in page.ids for link in page.links if link.startswith('#')))
            objects = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text)]
            web = next(o for o in objects if o['@type'] == 'WebPage')
            self.assertEqual(web['datePublished'], '2026-11-02')
            self.assertGreaterEqual(web['dateModified'], web['datePublished'])

    def test_checker_alternates_are_reciprocal_and_spanish_guides_are_labelled(self):
        for lang in ['en', 'fr', 'it', 'de', 'es']:
            rel = gen_expansion.g.SLUGS['checker'][lang].lstrip('/') + '.html'
            page = Page((ROOT / rel).read_text(encoding='utf-8'))
            self.assertEqual(set(page.alts), {'en', 'fr', 'it', 'de', 'es', 'x-default'})
        text = (ROOT / 'es/comprobar-precio-vinted.html').read_text(encoding='utf-8')
        self.assertIn('guía en inglés', text)
        self.assertIn('vinted.be', text)
        self.assertIn('no precios de ventas', text)

    def test_sitemap_registration_is_independent_of_price_generator_import_order(self):
        result = subprocess.run([sys.executable, '-c',
            "import sys;sys.path.insert(0,'ops/seo');import gen_price_guide,prepublish;urls=[r[0] for r in prepublish.PAGES];assert len(urls)==len(set(urls))"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_contextual_links_reach_the_new_tools(self):
        for lang, rel in [('en', 'vinted-saved-searches.html'), ('fr', 'fr/recherches-enregistrees-vinted.html')]:
            links = Page((ROOT / rel).read_text(encoding='utf-8')).links
            self.assertIn(copy.SLUGS['builder'][lang], links)
            self.assertIn(copy.SLUGS['phone'][lang], links)
        self.assertIn('/de/vinted-preis-checker', Page((ROOT / 'de/vinted-preise.html').read_text()).links)


if __name__ == '__main__':
    unittest.main()
