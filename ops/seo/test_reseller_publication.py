"""Metadata, discovery and dataset boundaries for the reseller resource set."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

import gen_reseller
import reseller_content as content

ROOT = Path(gen_reseller.g.ROOT)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links, self.canonical, self.alts = [], [], [], {}
        self.h1, self.lang = 0, None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'html':
            self.lang = attrs.get('lang')
        if tag == 'h1':
            self.h1 += 1
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical.append(attrs['href'])
        if tag == 'link' and 'hreflang' in attrs:
            self.alts[attrs['hreflang']] = attrs['href']


class ResellerPublicationTests(unittest.TestCase):
    def test_output_matches_source(self):
        for rel, expected in gen_reseller.render().items():
            self.assertEqual((ROOT / rel).read_text(encoding='utf-8'), expected, rel)

    def test_six_pages_have_reciprocal_metadata_and_valid_fragment_links(self):
        sitemap = ET.parse(ROOT / 'sitemap.xml')
        urls = {e.text for e in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
        for key, langs in content.SLUGS.items():
            for lang, path in langs.items():
                text = (ROOT / (path.lstrip('/') + '.html')).read_text(encoding='utf-8')
                page = Page(text)
                url = 'https://www.snypd.store' + path
                self.assertIn(url, urls)
                self.assertEqual(page.canonical, [url])
                self.assertEqual(page.lang, lang)
                self.assertEqual(page.h1, 1)
                self.assertEqual(len(page.ids), len(set(page.ids)))
                self.assertEqual(page.alts, {**{l: 'https://www.snypd.store' + p for l, p in langs.items()},
                                            'x-default': 'https://www.snypd.store' + langs['en']})
                self.assertTrue(all(a[1:] in page.ids for a in page.links if a.startswith('#')))
                objects = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text)]
                web = next(o for o in objects if o['@type'] == 'WebPage')
                self.assertEqual(web['datePublished'], content.PUBLISHED.get(key, '2026-11-02'))
                self.assertIn('/signup', page.links)

    def test_established_hubs_link_to_the_new_resources(self):
        for lang, file in [('en', 'vinted-price-guide.html'), ('fr', 'fr/guide-prix-vinted.html')]:
            links = Page((ROOT / file).read_text(encoding='utf-8')).links
            for langs in content.SLUGS.values():
                self.assertIn(langs[lang], links)
        deals = Page((ROOT / 'vinted-deals.html').read_text(encoding='utf-8')).links
        self.assertIn(content.SLUGS['profit']['en'], deals)

    def test_brand_shortlist_uses_only_published_data_and_keeps_its_limits(self):
        index = json.loads((ROOT / 'assets/data/price-index.json').read_text())
        for lang in ['en', 'fr']:
            text = content.brands(lang, index, gen_reseller.g)[-1][1][2]
            self.assertIn(index['window']['from'], text)
            self.assertIn(index['window']['to'], text)
            self.assertIn('vinted.be', text)
            links = Page(text).links
            published = {i['url'][lang] for i in index['items']}
            self.assertEqual(len(links), 5)
            self.assertTrue(set(links) <= published)


class ToolsAndMoneyPageTests(unittest.TestCase):
    def test_new_pages_carry_dated_sources_faq_and_no_hand_typed_snypd_prices(self):
        index = json.loads((ROOT / 'assets/data/price-index.json').read_text(encoding='utf-8'))
        for lang in ['en', 'fr']:
            tools = content.tools(lang, index, gen_reseller.g)
            html_text = ''.join(s[2] for s in tools[4])
            self.assertIn(content.TOOLS_CHECKED[lang], html_text)
            self.assertIn('@@price:pass@@', html_text)          # SNYPD prices only via plans.py tokens
            self.assertNotRegex(html_text, r'SNYPD[^<]{0,80}(?:€|EUR) ?\d')
            self.assertEqual({o['@type'] for o in tools[5]}, {'FAQPage', 'ItemList'})
            for _, url in content.TOOL_SOURCES:
                self.assertIn(url, content.tools_sources(lang))
            money = content.money(lang, index, gen_reseller.g)
            text = ''.join(s[2] for s in money[4])
            self.assertIn(index['window']['from'], text)
            self.assertIn('vinted.be', text)
            published = {i['url'][lang] for i in index['items']}
            for item_id in content.MONEY_ITEMS:
                item = next(i for i in index['items'] if i['id'] == item_id)
                self.assertIn(item['url'][lang], published)
                self.assertIn(item['url'][lang], text)

    def test_buyer_fee_matches_the_fees_page_rule(self):
        self.assertEqual(content._buyer_fee(2000), 170)   # €20 -> €1.70 (/vinted-fees table)
        self.assertEqual(content._buyer_fee(500), 95)     # €5 -> €0.95
        self.assertEqual(content._buyer_fee(20000), 1070)  # €200 -> €10.70


if __name__ == '__main__':
    unittest.main()
