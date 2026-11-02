"""Read-only source audit. This does not claim live HTTP or Google index status."""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.robotparser
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SITE = 'https://www.snypd.store'


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = None
        self.languages = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical = a.get('href')
        if tag == 'link' and a.get('rel') == 'alternate' and a.get('hreflang'):
            self.languages[a['hreflang']] = a.get('href')


def audit():
    xml = ET.parse(ROOT / 'sitemap.xml')
    urls = [e.text for e in xml.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    pages = [p for p in ROOT.rglob('*.html') if not {'.git', 'ops', 'assets', 'tools', 'node_modules'} & set(p.relative_to(ROOT).parts)]
    languages = Counter()
    issues = []
    datasets = 0
    for url in urls:
        relative = url.removeprefix(SITE).strip('/')
        languages[relative.split('/')[0] if re.match(r'^[a-z]{2}/', relative) else 'en'] += 1
        path = ROOT / (relative + '.html' if relative else 'index.html')
        if not path.exists():
            issues.append('Missing source for ' + url)
            continue
        text = path.read_text(encoding='utf-8')
        parsed = Metadata()
        parsed.feed(text)
        if parsed.canonical != url:
            issues.append('Canonical differs: ' + url)
        datasets += len(re.findall(r'"@type"\s*:\s*"Dataset"', text))
    if len(set(urls)) != len(urls):
        issues.append('Duplicate sitemap URLs')
    robots = urllib.robotparser.RobotFileParser()
    robots.parse((ROOT / 'robots.txt').read_text().splitlines())
    crawlers = {bot: robots.can_fetch(bot, SITE + '/vinted-price-guide') for bot in
                ['Googlebot', 'OAI-SearchBot', 'PerplexityBot', 'Claude-SearchBot']}
    return {
        'scope': 'Read-only source audit; not a live HTTP crawl, WAF test or Search Console index report.',
        'public_html_files': len(pages), 'sitemap_urls': len(urls),
        'sitemap_by_language': dict(sorted(languages.items())),
        'dataset_definitions_on_sitemap_pages': datasets,
        'robots_allows_public_guide': crawlers,
        'optional_ai_summaries': {name: (ROOT / name).exists() for name in ['llms.txt', 'llms-full.txt']},
        'issues': issues,
    }


if __name__ == '__main__':
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result['issues']))
