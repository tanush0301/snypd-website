#!/usr/bin/env python3
"""Regression coverage for mixed newline conventions in generated page regions."""
import unittest

import gen_regions as regions


class RegionNewlines(unittest.TestCase):
    def test_generated_regions_keep_their_existing_newlines(self):
        cases = [
            (regions.HTML_RE, '<!--plans:plans-faq-->{}<!--/plans:plans-faq-->', False),
            (regions.JS_RE, '/*plans:plans-js*/{}/*/plans:plans-js*/', True),
        ]
        for pattern, template, plain in cases:
            for newline in ('\n', '\r\n'):
                with self.subTest(plain=plain, newline=repr(newline)):
                    match = pattern.fullmatch(template.format('old' + newline + 'content'))
                    output = regions.render_region(match, plain)
                    self.assertEqual(output.count('\n'), output.count(newline))
                    if newline == '\n':
                        self.assertNotIn('\r', output)
                    regenerated = regions.render_region(pattern.fullmatch(output), plain)
                    self.assertEqual(output, regenerated)


if __name__ == '__main__':
    unittest.main()
