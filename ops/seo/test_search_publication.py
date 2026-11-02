"""Publication regressions: source integrity, unavailable estimates and reuse."""
import copy
import csv
import hashlib
import io
import json
import pathlib
import re
import unittest

import gen_market_report as report
import gen_price_guide as guide
from price_quality import publishable_conditions, publishable_overall

ROOT = pathlib.Path(guide.ROOT)


class PublicationTests(unittest.TestCase):
    def test_quality_checks_do_not_promote_provisional_or_inverted_prices(self):
        good = {'display_verdict': 'ok', 'confidence': 'high', 'sample_size': 100,
                'typical_cents': 2000, 'range_cents': {'low': 1000, 'high': 3000}}
        self.assertTrue(publishable_overall(good))
        for change in [{'provisional': True}, {'sample_size': 99}, {'display_verdict': 'too_broad'},
                       {'confidence': 'low'}, {'range_cents': {'low': 3000, 'high': 1000}}]:
            with self.subTest(change=change):
                self.assertFalse(publishable_overall(dict(good, **change)))

    def test_original_air_max_quartile_and_refusal_are_preserved(self):
        snapshot = json.loads((ROOT / 'ops/seo/data/price-guide-2026-11-01.json').read_text())
        v = next(r['view'] for r in snapshot['results'] if r['q'] == 'air max 90')
        vg = next(c for c in v['by_condition'] if c['condition_label'] == 'Very good')
        self.assertEqual(vg['range_cents']['high'], 8125)
        self.assertEqual(vg['verdict'], 'too_broad')
        self.assertFalse(publishable_overall(v))
        self.assertNotIn(vg, publishable_conditions(v))

    def test_condition_publication_does_not_mutate_the_source(self):
        view = copy.deepcopy(guide.RAW_V['jordan 4'])
        before = copy.deepcopy(view)
        valid = publishable_conditions(view)
        self.assertTrue(valid)
        self.assertEqual(view, before)
        self.assertFalse(publishable_overall(view))

    def test_unavailable_items_have_no_machine_readable_overall_price(self):
        index = guide.price_index()
        self.assertEqual(len(index['unavailable']), len(guide.NOTE_ITEMS))
        self.assertFalse({x['id'] for x in index['items']} & {x['id'] for x in index['unavailable']})
        for item in index['unavailable']:
            self.assertTrue(item['unavailable'])
            for field in ['typical', 'p25', 'p75']:
                self.assertNotIn(field, item)

    def test_note_pages_keep_their_language_urls_without_claiming_a_dataset(self):
        for item in guide.NOTE_ITEMS:
            for lang in guide.LANGS:
                with self.subTest(item=item['slug'], lang=lang):
                    page = guide.page_item(item, lang)
                    self.assertIn(guide.SITE + guide.item_url(item, lang), page)
                    self.assertIn('2026', page)
                    self.assertNotIn('"@type":"Dataset"', page)
                    self.assertNotIn('class="pc-big"', page)

    def test_italian_pilot_has_reciprocal_alternates(self):
        for slug in guide.price_italian.PILOT:
            item = next(i for i in guide.PUB if i['slug'] == slug)
            self.assertIn('it', guide.SLUGS['pg:' + slug])
            for lang in ['en', 'fr', 'de', 'nl', 'it']:
                page = guide.page_item(item, lang)
                self.assertIn('hreflang="it"', page)
                self.assertIn('hreflang="en"', page)
        for item in guide.price_index()['items']:
            if item['id'] not in guide.price_italian.PILOT:
                self.assertNotIn('it', item['url'])

    def test_italian_checker_explains_the_marketplace_and_language_limits(self):
        page = guide.page_checker('it')
        self.assertIn('vinted.be', page)
        self.assertIn('vinted.it', page)
        self.assertIn('guida in inglese', page)
        self.assertIn('data-lang="it"', page)

    def test_csvs_are_rectangular_and_match_their_metadata(self):
        for edition in report.EDITIONS:
            with self.subTest(edition=edition['id']):
                path = ROOT / report.csv_path(edition)
                data = path.read_bytes()
                rows = list(csv.reader(io.StringIO(data.decode('utf-8'))))
                self.assertGreater(len(rows), 1)
                self.assertTrue(all(len(r) == len(rows[0]) for r in rows))
                meta = json.loads(path.with_suffix('.metadata.json').read_text())
                self.assertEqual(meta['columns'], rows[0])
                self.assertEqual(meta['item_count'], len(rows) - 1)
                self.assertEqual(meta['csv_sha256'], hashlib.sha256(data).hexdigest())
                self.assertEqual(meta['price_basis'], 'asking prices, not completed-sale prices')

    def test_shared_index_points_only_to_real_public_files(self):
        for item in guide.price_index()['items'] + guide.price_index()['unavailable']:
            for url in item['url'].values():
                self.assertTrue((ROOT / (url.lstrip('/') + '.html')).is_file(), url)


if __name__ == '__main__':
    unittest.main()
