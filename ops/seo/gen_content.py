#!/usr/bin/env python3
# Builds the SEO content pages (English + French) from one layout, so the
# language versions and pages cannot drift apart. Homepage v5 look, same shell
# as ops/legal/gen_legal.py.
#
#   python ops/seo/gen_content.py
#
# Writes: vinted-bot.html, vinted-saved-search-alerts.html, vinted-bot-comparison.html,
#         the other SEO pages and fr/*.html. (The September price page moved to
#         gen_market_report.py on 10 Oct 2026 as an archived Market Report edition.)
#
# RULES FOR EDITING THE COPY
# - Every product fact must match what SNYPD really does (CLAUDE.md, plans.html's
#   audit comment). Never: sub-second speed, "instant", email/Telegram/Discord
#   alerts, re-list filtering, per-plan speed differences, "allowed by Vinted".
# - Competitor facts come from each vendor's own website and carry the date they
#   were checked (CHECKED). Re-check them before changing that date.
# - Prices come ONLY from ops/seo/data/*.json, the real Market Report output (run
#   inside the backend container). Never type a price by hand.
import csv, datetime, html, io, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plans  # noqa: E402  (plan facts: ops/seo/data/plans.json)
import compare_data as cd  # noqa: E402  (competitor facts in six languages, COMPARE_CHECKED)
from compare_data import COMPARE_CHECKED, COMPARE_CHECKED_SHORT, COMPETITORS, HELP435, HELP433, YES  # noqa: E402
import copy_alerts_compare as cac  # noqa: E402  (DE/NL/IT/ES copy for the alert hub and the comparison)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = 'https://www.snypd.store'
DISCORD = 'https://discord.gg/gjKD4auXhK'
EMAIL = 'help@snypd.store'
PUBLISHED = '2026-09-28'
MODIFIED = '2026-10-01'
CHECKED = {'en': '28 September 2026', 'fr': '28 septembre 2026'}
# French pages stay unpublished until SNYPD really polls vinted.fr (decided 2026-10-01).
# While False: no French files are written, English pages carry no hreflang or
# language switch, and prepublish.py leaves French URLs out of the sitemap.
FR_LIVE = True
# Every language a page can exist in, and whether it is published. A language that
# is not live is still generated, into ops/seo/preview/ (not deployed), for review.
# German: live on Claude's translation (Tanush's decision 9 Oct 2026). Dutch: live
# after Tanush approved outreach/12-nl-review.md (9 Oct 2026).
LIVE = {'en': True, 'fr': FR_LIVE, 'de': True, 'nl': True, 'it': True, 'es': True}
LANG_NAME = {'en': 'English', 'fr': 'Français', 'de': 'Deutsch', 'nl': 'Nederlands', 'it': 'Italiano', 'es': 'Español'}
# The Vinted sites the scraper accepts (scraper-worker/src/catalogue_contract.py
# MARKETS, verified live 2026-10-01). Update together with that list.
MARKETS_TEXT = {'en': 'every Vinted site in Europe and the US', 'fr': 'tous les sites Vinted d’Europe et des États-Unis',
                'de': 'jede Vinted-Seite in Europa und den USA', 'nl': 'elke Vinted-site in Europa en de VS'}
# How often SNYPD really checks a hunt, measured from the scraper's own log by
# ops/seo/check_interval.py. The copy says "about every 30 seconds" only while the
# measured median is 30 s: re-measure (and fix the copy) before changing either.
CHECK = json.load(open(os.path.join(ROOT, 'ops', 'seo', 'data', 'check-interval.json'), encoding='utf-8'))
if CHECK['median_seconds'] != 30:
    sys.exit('check-interval.json median is %ss: update the "about every 30 seconds" copy' % CHECK['median_seconds'])
_MONTHS = {'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
           'fr': ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
           'de': ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
           'nl': ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'],
           'it': ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'],
           'es': ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']}
_SPAN_SAME_MONTH = {'en': '%d-%d %s %d', 'fr': '%d au %d %s %d', 'de': '%d.-%d. %s %d', 'nl': '%d-%d %s %d',
                    'it': '%d-%d %s %d', 'es': '%d-%d de %s de %d'}
_SPAN_TWO_MONTHS = {'en': '%d %s to %d %s %d', 'fr': 'du %d %s au %d %s %d', 'de': '%d. %s bis %d. %s %d', 'nl': '%d %s tot %d %s %d',
                    'it': 'dal %d %s al %d %s %d', 'es': 'del %d de %s al %d de %s de %d'}
def _check_span(lang):
    a = datetime.date.fromisoformat(CHECK['measured_from'][:10])
    b = datetime.date.fromisoformat(CHECK['measured_to'][:10])
    m = _MONTHS[lang]
    if a == b:
        return '%d %s %d' % (b.day, m[b.month - 1], b.year)
    if (a.month, a.year) == (b.month, b.year):
        return _SPAN_SAME_MONTH[lang] % (a.day, b.day, m[b.month - 1], b.year)
    return _SPAN_TWO_MONTHS[lang] % (a.day, m[a.month - 1], b.day, m[b.month - 1], b.year)
SPEED_MEASURED = {
    'en': 'Measured in our own logs (%s, %s checks across %d searches): the median gap between two checks of the same search was %d seconds, and %d%% of checks came within 2 minutes.'
          % (_check_span('en'), format(CHECK['checks'], ','), CHECK['hunts'], CHECK['median_seconds'], CHECK['share_within_120s']),
    'fr': 'Mesuré dans nos propres journaux (%s, %s vérifications sur %d recherches)\xa0: l’écart médian entre deux vérifications d’une même recherche était de %d secondes, et %d\xa0%% des vérifications arrivaient en moins de 2 minutes.'
          % (_check_span('fr'), format(CHECK['checks'], ',').replace(',', '\xa0'), CHECK['hunts'], CHECK['median_seconds'], CHECK['share_within_120s']),
    'de': 'Gemessen in unseren eigenen Logs (%s, %s Prüfungen über %d Suchen): Der Median des Abstands zwischen zwei Prüfungen derselben Suche lag bei %d Sekunden, und %d\xa0%% der Prüfungen kamen innerhalb von 2 Minuten.'
          % (_check_span('de'), format(CHECK['checks'], ',').replace(',', '.'), CHECK['hunts'], CHECK['median_seconds'], CHECK['share_within_120s']),
    'nl': 'Gemeten in onze eigen logs (%s, %s controles over %d zoekopdrachten): de mediaan van de tijd tussen twee controles van dezelfde zoekopdracht was %d seconden, en %d%% van de controles kwam binnen 2 minuten.'
          % (_check_span('nl'), format(CHECK['checks'], ',').replace(',', '.'), CHECK['hunts'], CHECK['median_seconds'], CHECK['share_within_120s']),
    'it': 'Misurato nei nostri log (%s, %s controlli su %d ricerche): l’intervallo mediano tra due controlli della stessa ricerca è stato di %d secondi, e il %d%% dei controlli è arrivato entro 2 minuti.'
          % (_check_span('it'), format(CHECK['checks'], ',').replace(',', '.'), CHECK['hunts'], CHECK['median_seconds'], CHECK['share_within_120s']),
    'es': 'Medido en nuestros propios registros (%s, %s comprobaciones en %d búsquedas): el intervalo mediano entre dos comprobaciones de la misma búsqueda fue de %d segundos, y el %d\xa0%% de las comprobaciones llegó en menos de 2 minutos.'
          % (_check_span('es'), format(CHECK['checks'], ',').replace(',', '.'), CHECK['hunts'], CHECK['median_seconds'], CHECK['share_within_120s']),
}
# Applies to every tool that reads Vinted's search (CLAUDE.md section 3: 3-15 min, verified 9 Oct 2026).
VINTED_LAG = {
    'en': 'That is how often SNYPD looks, not how fast an item reaches you: Vinted itself shows a new listing in its search a few minutes after it is posted, for every tool.',
    'fr': 'C’est la fréquence à laquelle SNYPD regarde, pas le délai jusqu’à toi\xa0: Vinted affiche lui-même une nouvelle annonce dans sa recherche quelques minutes après sa publication, pour tous les outils.',
    'de': 'So oft schaut SNYPD nach, nicht so schnell erreicht dich ein Artikel: Vinted zeigt eine neue Anzeige selbst erst einige Minuten nach dem Einstellen in seiner Suche an, für jedes Tool.',
    'nl': 'Zo vaak kijkt SNYPD, niet zo snel bereikt een artikel je: Vinted toont een nieuwe advertentie zelf pas enkele minuten na plaatsing in de zoekresultaten, voor elke tool.',
    'it': 'Questa è la frequenza con cui SNYPD controlla, non il tempo che un annuncio impiega a raggiungerti: Vinted stesso mostra un nuovo annuncio nella sua ricerca qualche minuto dopo la pubblicazione, per qualsiasi strumento.',
    'es': 'Es la frecuencia con la que SNYPD mira, no lo que tarda un artículo en llegarte: el propio Vinted muestra un anuncio nuevo en su búsqueda unos minutos después de publicarse, para cualquier herramienta.',
}
# Free 24/7 trial (migration 042, since 7 Oct 2026; 3 days = 72 h + one 2-day extension when the hunt found
# nothing, for trials from 20 Oct 2026, owner-approved 19 Oct 2026; earlier trials keep 7 days, said only in /terms).
# Numbers are plans.py tokens. These sentences are the detailed explanation (bot page FAQ "Is there a free plan?").
TRIAL = {
    'en': 'For the first @@trial_days@@ days (@@trial_hours@@ h) after you save your first search, Free runs 24/7 with alerts, like a paid plan. If it finds nothing in that time, we add @@trial_ext_days@@ more days once.',
    'fr': 'Pendant les @@trial_days@@ premiers jours (@@trial_hours@@\xa0h) après ta première recherche enregistrée, Free tourne 24h/24 avec les alertes, comme un plan payant. Si ta recherche ne trouve rien pendant ce temps, on ajoute @@trial_ext_days@@ jours de plus, une seule fois.',
    'de': 'In den ersten @@trial_days@@ Tagen (@@trial_hours@@ Stunden) nach deiner ersten gespeicherten Suche läuft Free rund um die Uhr mit Benachrichtigungen, wie ein bezahlter Tarif. Findet deine Suche in dieser Zeit nichts, geben wir einmalig @@trial_ext_days@@ Tage dazu.',
    'nl': 'De eerste @@trial_days@@ dagen (@@trial_hours@@ uur) nadat je je eerste zoekopdracht opslaat, draait Free 24/7 met meldingen, net als een betaald abonnement. Vindt je zoekopdracht in die tijd niets, dan krijg je er eenmalig @@trial_ext_days@@ dagen bij.',
    'it': 'Per i primi @@trial_days@@ giorni (@@trial_hours@@ ore) dopo aver salvato la tua prima ricerca, Free funziona 24 ore su 24 con le notifiche, come un piano a pagamento. Se in quel periodo la ricerca non trova nulla, aggiungiamo @@trial_ext_days@@ giorni, una sola volta.',
    'es': 'Durante los @@trial_days@@ primeros días (@@trial_hours@@ horas) después de guardar tu primera búsqueda, Free funciona 24/7 con notificaciones, como un plan de pago. Si en ese tiempo tu búsqueda no encuentra nada, añadimos @@trial_ext_days@@ días más, una sola vez.',
}

# slug per language; the key is the page id
SLUGS = {
    'bot':     {'en': '/vinted-bot',                 'fr': '/fr/bot-vinted', 'de': '/de/vinted-bot', 'nl': '/nl/vinted-bot',
                'it': '/it/bot-vinted', 'es': '/es/bot-vinted'},
    'notify':  {'en': '/vinted-saved-search-alerts', 'fr': '/fr/alertes-recherche-vinted', 'de': '/de/vinted-benachrichtigung-neue-artikel',
                'nl': '/nl/vinted-melding-nieuwe-artikelen', 'it': '/it/notifiche-vinted-nuovi-annunci', 'es': '/es/alertas-vinted-nuevos-anuncios'},
    'compare': {'en': '/vinted-bot-comparison',      'fr': '/fr/comparatif-bot-vinted', 'de': '/de/vinted-bot-vergleich',
                'nl': '/nl/vinted-bot-vergelijken', 'it': '/it/confronto-bot-vinted', 'es': '/es/comparativa-bots-vinted'},
    'deals':   {'en': '/vinted-deals'},  # English only for now (decided 2026-10-02)
    'fees':    {'en': '/vinted-fees',                'fr': '/fr/frais-vinted'},
    'monitor': {'en': '/vinted-monitor',             'fr': '/fr/monitor-vinted'},
    'notwork': {'en': '/vinted-notifications-not-working', 'fr': '/fr/notification-vinted-ne-fonctionne-pas',
                'de': '/de/vinted-benachrichtigung-funktioniert-nicht', 'nl': '/nl/vinted-meldingen-werken-niet',
                'it': '/it/notifiche-vinted-non-funzionano', 'es': '/es/notificaciones-vinted-no-funcionan'},
    # work order 18 step 5; both rendered by gen_price_guide.py (they need the price data)
    'sold':    {'en': '/vinted-sold-items', 'fr': '/fr/vinted-voir-articles-vendus', 'de': '/de/vinted-verkaufte-artikel-sehen',
                'it': '/it/vinted-vedere-articoli-venduti', 'es': '/es/vinted-ver-articulos-vendidos'},
    'checker': {'en': '/vinted-price-checker', 'fr': '/fr/estimer-prix-vinted', 'it': '/it/stima-prezzo-vinted'},
}

CSS = r"""
@font-face { font-family: 'Cabinet Grotesk'; src: url('/assets/home/CabinetGrotesk-Black.woff2') format('woff2'); font-weight: 900; font-style: normal; font-display: swap; }
html, body { margin: 0; background: #0A0A0B; }
body { font-family: 'DM Mono', ui-monospace, monospace; color: #E8EAEB; -webkit-font-smoothing: antialiased; }
a { color: #00E5A0; text-decoration: none; }
a:hover { color: #57FFC8; }
a:focus-visible, button:focus-visible { outline: 2px solid #00E5A0; outline-offset: 2px; }
::selection { background: #A200FF; color: #FFFFFF; }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .lg-cursor { animation: none !important; } }
.lg-wrap { max-width: 1320px; margin: 0 auto; padding-left: 20px; padding-right: 20px; box-sizing: border-box; }
.lg-nav { position: sticky; top: 0; z-index: 30; background: rgba(10,10,11,.92); border-bottom: 1px solid #1D1D20; }
.lg-nav-in { display: flex; align-items: center; gap: 10px 18px; padding-top: 8px; padding-bottom: 8px; }
.lg-brand { display: flex; align-items: center; gap: 9px; color: #FFFFFF; min-height: 44px; }
.lg-brand:hover { color: #FFFFFF; }
.lg-brand img { width: 22px; height: 22px; object-fit: contain; display: block; }
.lg-brand span { font-size: 15.5px; font-weight: 700; letter-spacing: .02em; }
.lg-cursor { animation: blink 1.2s step-end infinite; }
.lg-links { display: flex; gap: 4px; flex: 1; }
.lg-navlink { font-size: 12px; letter-spacing: .1em; color: #8B9094; padding: 14px 10px; }
.lg-navlink:hover { color: #FFFFFF; }
.lg-navlink[aria-current="page"] { color: #FFFFFF; }
.lg-cta { font-size: 12px; letter-spacing: .1em; color: #FFFFFF; background: #A200FF; padding: 14px 16px; }
.lg-cta:hover { color: #FFFFFF; filter: brightness(1.18); }
@media (max-width: 699.98px) { .lg-links { display: none; } .lg-nav-in { justify-content: space-between; } .lg-login { margin-left: auto; } }
@media (max-width: 459.98px) { .lg-nav-in { gap: 4px; } .lg-navlink { padding: 14px 6px; letter-spacing: .05em; } .lg-cta { padding: 14px 10px; letter-spacing: .05em; } .lg-brand span { font-size: 14px; } }
.lg-head { border-bottom: 1px solid #1D1D20; }
.lg-head-in { padding-top: 56px; padding-bottom: 40px; display: flex; flex-direction: column; gap: 14px; }
.lg-eyebrow { font-size: 11px; letter-spacing: .16em; color: #8B9094; }
.lg-h1 { margin: 0; max-width: 20ch; font-family: 'Cabinet Grotesk', 'DM Mono', sans-serif; font-weight: 900; font-size: clamp(36px, 6vw, 60px); line-height: .98; letter-spacing: -.04em; color: #FFFFFF; }
.lg-meta { font-size: 12px; color: #8B9094; }
.lg-lead { margin: 6px 0 0; max-width: 68ch; font-size: 14px; line-height: 1.7; color: #B8BCBF; }
.lg-grid { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 48px; padding-top: 40px; padding-bottom: 72px; align-items: start; }
@media (max-width: 899.98px) { .lg-grid { grid-template-columns: minmax(0, 1fr); gap: 28px; padding-top: 28px; } }
.lg-toc { position: sticky; top: 84px; border: 1px solid #1D1D20; background: #0C0C0D; padding: 16px 18px; display: flex; flex-direction: column; gap: 2px; }
@media (max-width: 899.98px) { .lg-toc { position: static; } }
.lg-toc span { font-size: 11px; letter-spacing: .14em; color: #8B9094; margin-bottom: 8px; }
.lg-toc a { font-size: 12px; line-height: 1.5; color: #B8BCBF; padding: 5px 0; }
.lg-toc a:hover { color: #00E5A0; }
.lg-doc { max-width: 820px; min-width: 0; }
.lg-wide { grid-template-columns: minmax(0, 1fr); }
.lg-wide .lg-doc { max-width: 1120px; }
.lg-doc section { border-top: 1px solid #1D1D20; padding: 30px 0 6px; scroll-margin-top: 80px; }
.lg-doc section:first-child { border-top: 0; padding-top: 0; }
.lg-doc h2 { margin: 0 0 14px; font-family: 'Cabinet Grotesk', 'DM Mono', sans-serif; font-weight: 900; font-size: clamp(24px, 3.2vw, 30px); line-height: 1.05; letter-spacing: -.03em; color: #FFFFFF; }
.lg-doc h3 { margin: 22px 0 8px; font-size: 12.5px; font-weight: 400; letter-spacing: .1em; color: #FFFFFF; }
.lg-doc p, .lg-doc li { font-size: 13px; line-height: 1.75; color: #B8BCBF; }
.lg-doc p { margin: 0 0 14px; }
.lg-doc ul, .lg-doc ol { margin: 0 0 14px; padding-left: 20px; }
.lg-doc li { margin: 0 0 6px; }
.lg-doc strong { font-weight: 400; color: #FFFFFF; }
.lg-doc code { font-family: inherit; font-size: 12px; color: #FFFFFF; background: #141416; border: 1px solid #26262A; padding: 1px 5px; overflow-wrap: anywhere; }
.lg-doc blockquote { margin: 0 0 14px; padding: 12px 16px; border-left: 2px solid #00E5A0; background: #0C0C0D; font-size: 13px; line-height: 1.7; color: #E8EAEB; }
.lg-doc blockquote cite { display: block; margin-top: 6px; font-style: normal; font-size: 11.5px; color: #8B9094; }
.lg-box { border: 1px solid #1D1D20; background: #0C0C0D; padding: 18px; margin: 0 0 18px; display: flex; flex-direction: column; gap: 12px; }
.lg-box.lg-mint { border-color: rgba(0,229,160,.38); background: rgba(0,229,160,.06); }
.lg-box p { margin: 0; }
.ct-scroll { overflow-x: auto; margin: 0 0 18px; border: 1px solid #1D1D20; -webkit-overflow-scrolling: touch; }
.ct-table { width: 100%; border-collapse: collapse; min-width: 640px; }
.ct-table th, .ct-table td { text-align: left; vertical-align: top; padding: 12px 14px; border-top: 1px solid #1D1D20; font-size: 12px; line-height: 1.55; color: #B8BCBF; }
.ct-table thead th { border-top: 0; background: #121214; font-size: 11px; font-weight: 400; letter-spacing: .1em; color: #8B9094; }
.ct-table tbody th { font-weight: 400; color: #FFFFFF; min-width: 150px; }
.ct-table tbody tr { background: #0C0C0D; }
.ct-table tbody tr.ct-us { background: rgba(162,0,255,.07); }
.ct-table .ct-num { white-space: nowrap; color: #FFFFFF; }
.ct-table small { display: block; color: #8B9094; font-size: 11px; }
.ct-note { font-size: 11.5px !important; color: #8B9094 !important; }
.ct-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.ct-btn { display: inline-flex; align-items: center; min-height: 46px; padding: 0 18px; font-size: 12px; letter-spacing: .09em; color: #FFFFFF; background: #A200FF; }
.ct-btn:hover { color: #FFFFFF; filter: brightness(1.18); }
.ct-btn.ct-ghost { background: #141416; border: 1px solid #3A3A40; }
.ct-btn.ct-ghost:hover { filter: none; background: #1C1C1F; border-color: #55555C; }
.lg-foot { border-top: 1px solid #1D1D20; }
.lg-foot-in { padding-top: 24px; padding-bottom: 24px; display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.lg-foot-a { display: flex; flex-direction: column; gap: 6px; }
.lg-foot small { font-size: 11px; letter-spacing: .1em; color: #8B9094; }
.lg-foot-t { font-size: 12px; color: #8B9094; }
.lg-foot-l { display: flex; gap: 8px 16px; flex-wrap: wrap; margin-top: 4px; }
.lg-foot-l a, .lg-foot-l button { font-size: 12px; }
.lg-foot-l button { font-family: inherit; color: #00E5A0; background: none; border: 0; padding: 0; cursor: pointer; }
.lg-foot-l button:hover { color: #57FFC8; }
.lg-lang { position: relative; }
.lg-lang > summary { list-style: none; cursor: pointer; }
.lg-lang > summary::-webkit-details-marker { display: none; }
.lg-lang > div { position: absolute; left: 0; top: 100%; z-index: 40; display: flex; flex-direction: column; min-width: 150px; background: #0A0A0B; border: 1px solid #1D1D20; }
.pc { border: 1px solid rgba(0,229,160,.38); background: rgba(0,229,160,.06); padding: 18px; margin: 0 0 18px; }
.pc label { display: block; font-size: 11px; letter-spacing: .14em; color: #8B9094; margin-bottom: 8px; }
.pc input { width: 100%; box-sizing: border-box; min-height: 48px; padding: 0 14px; font: inherit; font-size: 16px; color: #FFFFFF; background: #0A0A0B; border: 1px solid #3A3A40; border-radius: 0; }
.pc input:focus { outline: 2px solid #00E5A0; outline-offset: 0; border-color: #00E5A0; }
.lg-doc .pc-list { list-style: none; margin: 10px 0 0; padding: 0; display: flex; flex-wrap: wrap; gap: 8px; }
.lg-doc .pc-list li { margin: 0; }
.pc-list button { font: inherit; font-size: 12px; color: #E8EAEB; background: #141416; border: 1px solid #3A3A40; padding: 9px 12px; min-height: 40px; cursor: pointer; text-align: left; }
.pc-list button:hover, .pc-list button[aria-pressed="true"] { border-color: #00E5A0; color: #FFFFFF; }
.pc-res { margin-top: 16px; border-top: 1px solid #1D1D20; padding-top: 16px; }
.pc-res[hidden] { display: none; }
.lg-doc .pc-res h3 { margin-top: 0; }
.pc-big { display: block; font-family: 'Cabinet Grotesk', 'DM Mono', sans-serif; font-weight: 900; font-size: 44px; line-height: 1; letter-spacing: -.03em; color: #FFFFFF; margin: 2px 0 12px; }
.pc-msg { font-size: 12.5px; color: #8B9094; margin: 10px 0 0; }
.pc-az { columns: 2 240px; column-gap: 32px; }
"""

UI = {
    'en': dict(locale='en_GB', toc='ON THIS PAGE', updated='Updated', by='By SNYPD, built by a Belgian sneaker reseller',
               nav=[('bot', 'VINTED BOT'), ('/vinted-price-guide', 'VINTED PRICES'), ('/plans', 'PRICING'), (DISCORD, 'DISCORD')],
               login='LOG IN', start='START FREE', switch=('FR', 'fr', 'Version française'),
               foot_tag='SNYPD &middot; NOT AFFILIATED WITH VINTED', foot_t='Reads public listings only.',
               foot=[('bot', 'Vinted bot'), ('monitor', 'Vinted monitor'), ('notify', 'Vinted notifications'), ('notwork', 'Vinted notifications not working'), ('saved', 'Vinted saved searches'), ('pricedrop', 'Vinted price drop alerts'), ('compare', 'Vinted bots compared'), ('/vinted-price-guide', 'Vinted price guide'), ('checker', 'Vinted price checker'), ('sold', 'Vinted sold items'),('/vinted-market-report', 'Vinted market report'), 
                     ('deals', 'Vinted deals'), ('fees', 'Vinted fees'), ('/faq', 'FAQ'), ('/support', 'Support'), (DISCORD, 'Discord')],
               legal='<a href="/privacy">Privacy</a><a href="/terms">Terms</a><a href="mailto:help@snypd.store">Contact</a><a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Cookie settings</a>',
               home='Home'),
    'fr': dict(locale='fr_FR', toc='SUR CETTE PAGE', updated='Mis à jour le', by='Par SNYPD, créé par un revendeur de sneakers belge',
               nav=[('bot', 'BOT VINTED'), ('/fr/guide-prix-vinted', 'PRIX VINTED'), ('/plans', 'TARIFS'), (DISCORD, 'DISCORD')],
               login='CONNEXION', start='COMMENCER', switch=('EN', 'en', 'English version'),
               foot_tag='SNYPD &middot; NON AFFILIÉ À VINTED', foot_t='Lit uniquement les annonces publiques.',
               foot=[('bot', 'Bot Vinted'), ('monitor', 'Monitor Vinted'), ('notify', 'Alertes Vinted'), ('notwork', 'Notifications Vinted en panne'), ('saved', 'Recherches enregistrées Vinted'), ('pricedrop', 'Baisse de prix Vinted'), ('compare', 'Comparatif des bots Vinted'), ('/fr/guide-prix-vinted', 'Guide des prix Vinted'), ('checker', 'Estimer un prix Vinted'), ('sold', 'Articles vendus sur Vinted'), ('/fr/rapport-marche-vinted', 'Rapport du marché Vinted'), ('fees', 'Frais Vinted'),
                     ('/faq', 'FAQ (anglais)'), ('/support', 'Support (anglais)'), (DISCORD, 'Discord')],
               legal='<a href="/privacy">Confidentialité</a><a href="/terms">Conditions</a><a href="mailto:help@snypd.store">Contact</a><a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Paramètres des cookies</a>',
               home='Accueil'),
    'de': dict(locale='de_DE', toc='AUF DIESER SEITE', updated='Aktualisiert am', by='Von SNYPD, gebaut von einem belgischen Sneaker-Reseller',
               nav=[('bot', 'VINTED BOT'), ('/de/vinted-preise', 'VINTED-PREISE'), ('/plans', 'TARIFE'), (DISCORD, 'DISCORD')],
               login='ANMELDEN', start='LOSLEGEN',
               foot_tag='SNYPD &middot; NICHT MIT VINTED VERBUNDEN', foot_t='Liest nur öffentliche Anzeigen.',
               foot=[('bot', 'Vinted Bot'), ('notify', 'Vinted-Benachrichtigung für neue Artikel'), ('notwork', 'Vinted-Benachrichtigungen kommen nicht'), ('saved', 'Gespeicherte Suchen auf Vinted'), ('pricedrop', 'Vinted-Preissenkung'), ('compare', 'Vinted Bots im Vergleich'), ('sold', 'Verkaufte Artikel auf Vinted sehen'), ('/de/vinted-preise', 'Vinted-Preisführer'),('monitor', 'Vinted-Monitor (EN)'), ('fees', 'Vinted-Gebühren (EN)'),
                     ('/faq', 'FAQ (EN)'), ('/support', 'Support (EN)'), (DISCORD, 'Discord')],
               legal='<a href="/privacy">Datenschutz</a><a href="/terms">Nutzungsbedingungen</a><a href="mailto:help@snypd.store">Kontakt</a><a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Cookie-Einstellungen</a>',
               home='Startseite'),
    'nl': dict(locale='nl_NL', toc='OP DEZE PAGINA', updated='Bijgewerkt op', by='Door SNYPD, gemaakt door een Belgische sneakerreseller',
               nav=[('bot', 'VINTED BOT'), ('/nl/vinted-prijzen', 'VINTED-PRIJZEN'), ('/plans', 'ABONNEMENTEN'), (DISCORD, 'DISCORD')],
               login='INLOGGEN', start='BEGINNEN',
               foot_tag='SNYPD &middot; NIET VERBONDEN AAN VINTED', foot_t='Leest alleen openbare advertenties.',
               foot=[('bot', 'Vinted bot'), ('notify', 'Vinted-melding bij nieuwe artikelen'), ('notwork', 'Vinted-meldingen werken niet'), ('saved', 'Opgeslagen zoekopdrachten op Vinted'), ('pricedrop', 'Vinted-prijsverlaging'), ('compare', 'Vinted bots vergeleken'), ('/nl/vinted-prijzen', 'Vinted-prijsgids'), ('monitor', 'Vinted monitor (EN)'), ('fees', 'Vinted-kosten (EN)'),
                     ('/faq', 'FAQ (EN)'), ('/support', 'Support (EN)'), (DISCORD, 'Discord')],
               legal='<a href="/privacy">Privacy</a><a href="/terms">Voorwaarden</a><a href="mailto:help@snypd.store">Contact</a><a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Cookie-instellingen</a>',
               home='Home'),
    'it': dict(locale='it_IT', toc='IN QUESTA PAGINA', updated='Aggiornato il', by='Di SNYPD, creato da un reseller di sneaker belga',
               nav=[('bot', 'VINTED BOT'), ('/plans', 'PREZZI'), (DISCORD, 'DISCORD')],
               login='ACCEDI', start='INIZIA',
               foot_tag='SNYPD &middot; NON AFFILIATO A VINTED', foot_t='Legge solo annunci pubblici.',
               foot=[('bot', 'Bot Vinted'), ('notify', 'Notifiche Vinted per nuovi annunci'), ('notwork', 'Notifiche Vinted non funzionano'), ('saved', 'Ricerche salvate su Vinted'), ('compare', 'Bot Vinted a confronto'), ('sold', 'Vedere gli articoli venduti su Vinted'), ('/it/prezzi-vinted', 'Guide prezzi Vinted'), ('/it/stima-prezzo-vinted', 'Stima prezzo Vinted'),('fees', 'Commissioni Vinted (EN)'),
                     ('/faq', 'FAQ (EN)'), ('/support', 'Supporto (EN)'), (DISCORD, 'Discord')],
               legal='<a href="/privacy">Privacy</a><a href="/terms">Termini</a><a href="mailto:help@snypd.store">Contatti</a><a href="/cookies">Cookie</a><a href="/cookies" data-cookie-settings>Impostazioni cookie</a>',
               home='Home'),
    'es': dict(locale='es_ES', toc='EN ESTA PÁGINA', updated='Actualizado el', by='Por SNYPD, creado por un revendedor de zapatillas belga',
               nav=[('bot', 'VINTED BOT'), ('/plans', 'PRECIOS'), (DISCORD, 'DISCORD')],
               login='ENTRAR', start='EMPEZAR',
               foot_tag='SNYPD &middot; SIN RELACIÓN CON VINTED', foot_t='Solo lee anuncios públicos.',
               foot=[('bot', 'Bot de Vinted'), ('notify', 'Alertas de Vinted para anuncios nuevos'), ('notwork', 'Notificaciones de Vinted no funcionan'), ('saved', 'Búsquedas guardadas en Vinted'), ('compare', 'Bots de Vinted comparados'), ('sold', 'Ver artículos vendidos en Vinted'), ('/vinted-price-guide', 'Precios de Vinted (EN)'),('fees', 'Comisiones de Vinted (EN)'),
                     ('/faq', 'FAQ (EN)'), ('/support', 'Soporte (EN)'), (DISCORD, 'Discord')],
               legal='<a href="/privacy">Privacidad</a><a href="/terms">Términos</a><a href="mailto:help@snypd.store">Contacto</a><a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Ajustes de cookies</a>',
               home='Inicio'),
}


# (page, language) pairs written to ops/seo/preview/ only, until Tanush approves the copy.
# 10 Oct 2026: the Dutch alert + comparison pages (review file: outreach/19-nl-review-step4.md).
# 18 Oct 2026: Dutch released (Tanush: "publish now"); the set stays for future held pages.
HOLD = set()


def live_langs(key):
    """Published languages of a page, English first."""
    return [l for l in ('en', 'fr', 'de', 'nl', 'it', 'es', 'pl', 'sv') if l in SLUGS[key] and LIVE[l] and (key, l) not in HOLD]
# Last real content change per page (shown as 'Updated' and used as dateModified).
# A floor only: write() moves the date to the day the page's <main> text really changes (stamp_modified).
# bot/notify/compare/monitor/deals: Solo plan copy, 18 Oct 2026 (site 0af4fbb).
PAGE_MODIFIED = {'bot': '2026-10-18', 'notify': '2026-10-18', 'compare': '2026-10-18', 'deals': '2026-10-18', 'fees': '2026-10-02',
                 'monitor': '2026-10-18', 'notwork': '2026-10-09', 'sold': '2026-10-10', 'checker': '2026-10-10'}
MONTHS_TXT = {'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
              'fr': ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
              'de': _MONTHS['de'], 'nl': _MONTHS['nl'], 'it': _MONTHS['it'], 'es': _MONTHS['es']}


def date_txt(iso, lang):
    y, m, d = (int(x) for x in iso.split('-'))
    day = {'fr': '1er' if d == 1 else str(d), 'de': '%d.' % d}.get(lang, str(d))
    if lang == 'es':
        return '%s de %s de %d' % (day, MONTHS_TXT[lang][m - 1], y)
    return '%s %s %d' % (day, MONTHS_TXT[lang][m - 1], y)


def esc(s):
    return html.escape(s, quote=True)


def href(key, lang):
    # a page that does not exist in this language links to its English version
    if key not in SLUGS:
        return key
    return SLUGS[key][lang] if lang in live_langs(key) else SLUGS[key]['en']


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + '</script>'


def page(key, lang, title, desc, eyebrow, h1, lead, toc, body, extra_ld=(), head_extra='', parent=None, bare=False):
    """parent: optional (name, path) shown between Home and this page in the breadcrumb.
    bare: a page with no URL of its own (404.html): noindex, no canonical, hreflang, JSON-LD or date line."""
    u = UI[lang]
    path = None if bare else SLUGS[key][lang]
    url = SITE + path if path else ''
    langs = [lang] if bare else live_langs(key)
    alts = ''
    if len(langs) > 1:
        alts = ''.join('<link rel="alternate" hreflang="%s" href="%s%s">\n' % (l, SITE, SLUGS[key][l]) for l in langs)
        alts += '<link rel="alternate" hreflang="x-default" href="%s%s">\n' % (SITE, SLUGS[key]['en'])
    others = [l for l in langs if l != lang]
    if len(others) == 1:
        o = others[0]
        switch = ('<a class="lg-navlink" href="%s" hreflang="%s" lang="%s" title="%s">%s</a>'
                  % (SLUGS[key][o], o, o, LANG_NAME[o], o.upper()))
    elif others:
        switch = ('<details class="lg-lang"><summary class="lg-navlink" title="%s">%s &#9662;</summary><div>%s</div></details>'
                  % (LANG_NAME[lang], lang.upper(), ''.join('<a class="lg-navlink" href="%s" hreflang="%s" lang="%s">%s</a>'
                                                          % (SLUGS[key][o], o, o, LANG_NAME[o]) for o in others)))
    else:
        switch = ''
    nav = ''.join('<a class="lg-navlink" href="%s"%s>%s</a>' % (href(k, lang), ' aria-current="page"' if k == key else '', t) for k, t in u['nav'])
    foot = ''.join('<a href="%s">%s</a>' % (href(k, lang), t + (' (EN)' if k in SLUGS and lang != 'en' and lang not in live_langs(k) and '(' not in t else ''))
                   for k, t in u['foot'])
    toc_html = ''.join('<a href="#%s">%s</a>' % (a, t) for a, t in (toc or []))
    toc_block = ('<nav class="lg-toc" aria-label="%s"><span>%s</span>%s</nav>' % (u['toc'].title(), u['toc'], toc_html)) if toc else ''
    grid_cls = 'lg-grid' if toc else 'lg-grid lg-wide'
    canon = '<meta name="robots" content="noindex">' if bare else '<link rel="canonical" href="%s">' % url
    og_url = '' if bare else '<meta property="og:url" content="%s">\n' % url
    meta_line = '' if bare else ('<span class="lg-meta">%s <time datetime="%s">%s</time> &middot; %s</span>'
                                 % (u['updated'], PAGE_MODIFIED[key], date_txt(PAGE_MODIFIED[key], lang), u['by']))
    ld = [] if bare else [
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': it} for i, (n, it) in enumerate(
                [(u['home'], SITE + '/')] + ([(parent[0], SITE + parent[1])] if parent else []) + [(h1_plain(h1), url)])]},
        {'@context': 'https://schema.org', '@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': title,
         'description': desc, 'inLanguage': lang, 'datePublished': PUBLISHED, 'dateModified': PAGE_MODIFIED[key],
         'isPartOf': {'@id': SITE + '/#website'}, 'publisher': {'@id': SITE + '/#org'}, 'about': {'@id': SITE + '/#app'}},
    ] + list(extra_ld)
    ld_html = '\n'.join(jsonld(o) for o in ld)
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{canon}
{alts}<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
{og_url}<meta property="og:site_name" content="SNYPD">
<meta property="og:locale" content="{u['locale']}">
<meta property="og:image" content="{SITE}/assets/og/og-v5.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="SNYPD - Vinted bot and monitor for new listing alerts">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0A0A0B">
<link rel="icon" type="image/png" sizes="192x192" href="/assets/icons/icon-192.png">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/dm-mono-400-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/dm-mono.css">
<link rel="preload" href="/assets/home/CabinetGrotesk-Black.woff2" as="font" type="font/woff2" crossorigin="anonymous">
<style>{CSS}{COMPARE_CSS}</style>
{ld_html}
<!-- Cookie consent: Google Analytics and the Whop pixel load only after the visitor agrees -->
<script src="/assets/consent.js" data-ga="G-VBC0SXPR6F" data-whop="biz_FO7MS9yTf8rm6n"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-VBC0SXPR6F');
</script>
</head>
<body>
<header class="lg-nav">
  <div class="lg-wrap lg-nav-in">
    <a class="lg-brand" href="/"><img src="/assets/home/logo.png" alt="SNYPD" width="22" height="22"><span>SNYPD<span class="lg-cursor">_</span></span></a>
    <nav class="lg-links" aria-label="Main">{nav}</nav>
    {switch}
    <a class="lg-navlink lg-login" href="/login">{u['login']}</a>
    <a class="lg-cta" href="/signup">{u['start']}</a>
  </div>
</header>
<main>
  <div class="lg-head">
    <div class="lg-wrap lg-head-in">
      <span class="lg-eyebrow">{eyebrow}</span>
      <h1 class="lg-h1">{h1}</h1>
      {meta_line}
      <p class="lg-lead">{lead}</p>
      {head_extra}
    </div>
  </div>
  <div class="lg-wrap {grid_cls}">
    {toc_block}
    <article class="lg-doc">
{body}
    </article>
  </div>
</main>
<footer class="lg-foot">
  <div class="lg-wrap lg-foot-in">
    <div class="lg-foot-a">
      <small>{u['foot_tag']}</small>
      <span class="lg-foot-t">{u['foot_t']}</span>
      <span class="lg-foot-l">{foot}</span>
    </div>
    <nav class="lg-foot-l" aria-label="Legal" style="align-items:flex-start;">{u['legal']}</nav>
  </div>
</footer>
</body>
</html>
"""


def h1_plain(h):
    return html.unescape(h.replace('<br>', ' '))


def table(head, rows, us_row=None):
    th = ''.join('<th scope="col">%s</th>' % h for h in head)
    tr = []
    for i, r in enumerate(rows):
        cls = ' class="ct-us"' if us_row is not None and i == us_row else ''
        cells = '<th scope="row">%s</th>' % r[0] + ''.join('<td>%s</td>' % c for c in r[1:])
        tr.append('<tr%s>%s</tr>' % (cls, cells))
    return '<div class="ct-scroll"><table class="ct-table"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, ''.join(tr))


def faq_ld(pairs):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': html.unescape(a)}} for q, a in pairs]}


def faq_html(pairs):
    return ''.join('<h3>%s</h3><p>%s</p>' % (esc(q), a) for q, a in pairs)


def cta(lang):
    if lang in cps.CTA:
        return cps.CTA[lang]
    if lang == 'it':
        return ('<div class="lg-box lg-mint"><p><strong>Inizia gratis con una ricerca.</strong> Nessuna carta, nessun limite di tempo, nessun limite di notifiche. I primi @@trial_days@@ giorni funziona 24 ore su 24 con le notifiche. '
                'Passa a un piano a pagamento quando vuoi che la ricerca continui anche con la dashboard chiusa.</p>'
                '<p class="ct-note">Per ora registrazione e pagamento sono in inglese.</p>'
                '<div class="ct-actions"><a class="ct-btn" href="/signup">INIZIA GRATIS</a>'
                '<a class="ct-btn ct-ghost" href="/plans">VEDI I PIANI</a></div></div>')
    if lang == 'es':
        return ('<div class="lg-box lg-mint"><p><strong>Empieza gratis con una búsqueda.</strong> Sin tarjeta, sin límite de tiempo, sin límite de notificaciones. Los primeros @@trial_days@@ días funciona 24/7 con notificaciones. '
                'Pásate a un plan de pago cuando quieras que la búsqueda siga funcionando con el panel cerrado.</p>'
                '<p class="ct-note">De momento, el registro y el pago están en inglés.</p>'
                '<div class="ct-actions"><a class="ct-btn" href="/signup">EMPEZAR GRATIS</a>'
                '<a class="ct-btn ct-ghost" href="/plans">VER PLANES</a></div></div>')
    if lang == 'de':
        return ('<div class="lg-box lg-mint"><p><strong>Starte mit einer Suche, kostenlos.</strong> Keine Karte, kein Zeitlimit, keine Grenze bei Benachrichtigungen. Die ersten @@trial_days@@ Tage laufen rund um die Uhr mit Benachrichtigungen. '
                'Wechsle zu einem bezahlten Tarif, wenn deine Suche auch bei geschlossenem Dashboard weiterlaufen soll.</p>'
                '<p class="ct-note">Anmeldung und Bezahlung sind vorerst auf Englisch.</p>'
                '<div class="ct-actions"><a class="ct-btn" href="/signup">KOSTENLOS STARTEN</a>'
                '<a class="ct-btn ct-ghost" href="/plans">TARIFE ANSEHEN</a></div></div>')
    if lang == 'nl':
        return ('<div class="lg-box lg-mint"><p><strong>Begin gratis met één zoekopdracht.</strong> Geen kaart, geen tijdslimiet, geen limiet op meldingen. De eerste @@trial_days@@ dagen draaien 24/7 met meldingen. '
                'Stap over op een betaald abonnement als je zoekopdracht ook met gesloten dashboard moet blijven lopen.</p>'
                '<p class="ct-note">Registreren en betalen gaan voorlopig in het Engels.</p>'
                '<div class="ct-actions"><a class="ct-btn" href="/signup">GRATIS BEGINNEN</a>'
                '<a class="ct-btn ct-ghost" href="/plans">ABONNEMENTEN BEKIJKEN</a></div></div>')
    if lang == 'en':
        return ('<div class="lg-box lg-mint"><p><strong>Start with one search, free.</strong> No card, no time limit, no cap on notifications. The first @@trial_days@@ days run 24/7 with alerts. '
                'Upgrade when you want it to keep watching with your dashboard closed.</p>'
                '<div class="ct-actions"><a class="ct-btn" href="/signup">START FREE</a>'
                '<a class="ct-btn ct-ghost" href="/plans">SEE PLANS</a></div></div>')
    return ('<div class="lg-box lg-mint"><p><strong>Commence avec une recherche, gratuitement.</strong> Sans carte, sans limite de durée ni de notifications. Les @@trial_days@@ premiers jours tournent 24h/24 avec les alertes. '
            'Passe à un plan payant quand tu veux que la surveillance continue tableau de bord fermé.</p>'
            '<p class="ct-note">Inscription et paiement en français.</p>'
            '<div class="ct-actions"><a class="ct-btn" href="/signup">COMMENCER GRATUITEMENT</a>'
            '<a class="ct-btn ct-ghost" href="/plans">VOIR LES TARIFS</a></div></div>')


# ------------------------------------------------------------------ shared facts
PLANS_ROWS = {
    'en': [['Free', '<span class="ct-num">@@price:free@@</span>', '@@searches:free@@', 'First @@trial_days@@ days, then only while your dashboard is open', 'No'],
           ['Solo', '<span class="ct-num">@@price:solo@@</span>', '@@searches:solo@@', 'Yes, 24/7', 'No'],
           ['Kickstart', '<span class="ct-num">@@price:kickstart@@</span>', '@@searches:kickstart@@', 'Yes, 24/7', 'No'],
           ['Pro', '<span class="ct-num">@@price:pro@@</span>', '@@searches:pro@@', 'Yes, 24/7', 'Yes'],
           ['Elite', '<span class="ct-num">@@price:elite@@</span>', '@@searches:elite@@', 'Yes, 24/7', 'Yes']],
    'fr': [['Free', '<span class="ct-num">@@price:free@@</span>', '@@searches:free@@', '@@trial_days@@ premiers jours, puis tableau de bord ouvert seulement', 'Non'],
           ['Solo', '<span class="ct-num">@@price:solo@@</span>', '@@searches:solo@@', 'Oui, 24h/24', 'Non'],
           ['Kickstart', '<span class="ct-num">@@price:kickstart@@</span>', '@@searches:kickstart@@', 'Oui, 24h/24', 'Non'],
           ['Pro', '<span class="ct-num">@@price:pro@@</span>', '@@searches:pro@@', 'Oui, 24h/24', 'Oui'],
           ['Elite', '<span class="ct-num">@@price:elite@@</span>', '@@searches:elite@@', 'Oui, 24h/24', 'Oui']],
    'de': [['Free', '<span class="ct-num">@@price:free@@</span>', '@@searches:free@@', 'Erste @@trial_days@@ Tage, danach nur bei geöffnetem Dashboard', 'Nein'],
           ['Solo', '<span class="ct-num">@@price:solo@@</span>', '@@searches:solo@@', 'Ja, rund um die Uhr', 'Nein'],
           ['Kickstart', '<span class="ct-num">@@price:kickstart@@</span>', '@@searches:kickstart@@', 'Ja, rund um die Uhr', 'Nein'],
           ['Pro', '<span class="ct-num">@@price:pro@@</span>', '@@searches:pro@@', 'Ja, rund um die Uhr', 'Ja'],
           ['Elite', '<span class="ct-num">@@price:elite@@</span>', '@@searches:elite@@', 'Ja, rund um die Uhr', 'Ja']],
    'nl': [['Free', '<span class="ct-num">@@price:free@@</span>', '@@searches:free@@', 'Eerste @@trial_days@@ dagen, daarna alleen met dashboard open', 'Nee'],
           ['Solo', '<span class="ct-num">@@price:solo@@</span>', '@@searches:solo@@', 'Ja, 24/7', 'Nee'],
           ['Kickstart', '<span class="ct-num">@@price:kickstart@@</span>', '@@searches:kickstart@@', 'Ja, 24/7', 'Nee'],
           ['Pro', '<span class="ct-num">@@price:pro@@</span>', '@@searches:pro@@', 'Ja, 24/7', 'Ja'],
           ['Elite', '<span class="ct-num">@@price:elite@@</span>', '@@searches:elite@@', 'Ja, 24/7', 'Ja']],
    'it': [['Free', '<span class="ct-num">@@price:free@@</span>', '@@searches:free@@', 'Primi @@trial_days@@ giorni, poi solo con la dashboard aperta', 'No'],
           ['Solo', '<span class="ct-num">@@price:solo@@</span>', '@@searches:solo@@', 'Sì, 24 ore su 24', 'No'],
           ['Kickstart', '<span class="ct-num">@@price:kickstart@@</span>', '@@searches:kickstart@@', 'Sì, 24 ore su 24', 'No'],
           ['Pro', '<span class="ct-num">@@price:pro@@</span>', '@@searches:pro@@', 'Sì, 24 ore su 24', 'Sì'],
           ['Elite', '<span class="ct-num">@@price:elite@@</span>', '@@searches:elite@@', 'Sì, 24 ore su 24', 'Sì']],
    'es': [['Free', '<span class="ct-num">@@price:free@@</span>', '@@searches:free@@', 'Primeros @@trial_days@@ días, luego solo con el panel abierto', 'No'],
           ['Solo', '<span class="ct-num">@@price:solo@@</span>', '@@searches:solo@@', 'Sí, 24/7', 'No'],
           ['Kickstart', '<span class="ct-num">@@price:kickstart@@</span>', '@@searches:kickstart@@', 'Sí, 24/7', 'No'],
           ['Pro', '<span class="ct-num">@@price:pro@@</span>', '@@searches:pro@@', 'Sí, 24/7', 'Sí'],
           ['Elite', '<span class="ct-num">@@price:elite@@</span>', '@@searches:elite@@', 'Sí, 24/7', 'Sí']],
}
PLANS_HEAD = {'en': ['PLAN', 'PER MONTH, VAT INCL.', 'ACTIVE SEARCHES', 'WATCHES WITH DASHBOARD CLOSED', 'MARKET REPORT'],
              'fr': ['PLAN', 'PAR MOIS, TVA INCLUSE', 'RECHERCHES ACTIVES', 'SURVEILLE TABLEAU DE BORD FERMÉ', 'MARKET REPORT'],
              'de': ['TARIF', 'PRO MONAT, INKL. MWST.', 'AKTIVE SUCHEN', 'PRÜFT BEI GESCHLOSSENEM DASHBOARD', 'MARKET REPORT'],
              'nl': ['ABONNEMENT', 'PER MAAND, INCL. BTW', 'ACTIEVE ZOEKOPDRACHTEN', 'CONTROLEERT MET DASHBOARD DICHT', 'MARKET REPORT'],
              'it': ['PIANO', 'AL MESE, IVA INCLUSA', 'RICERCHE ATTIVE', 'CONTROLLA CON LA DASHBOARD CHIUSA', 'MARKET REPORT'],
              'es': ['PLAN', 'AL MES, IVA INCLUIDO', 'BÚSQUEDAS ACTIVAS', 'VIGILA CON EL PANEL CERRADO', 'MARKET REPORT']}



def page_bot_de():
    faq = [
        ('Kauft SNYPD Artikel für mich?', 'Nein. SNYPD findet neue Anzeigen und benachrichtigt dich. Du öffnest die Anzeige auf Vinted und kaufst oder machst selbst ein Angebot, über den normalen Vinted-Checkout.'),
        ('Muss ich SNYPD mein Vinted-Passwort geben?', 'Nein. SNYPD fragt nie nach deinen Vinted-Zugangsdaten und meldet sich nie in deinem Konto an. Für dein SNYPD-Konto brauchst du nur eine E-Mail-Adresse.'),
        ('Wie oft prüft SNYPD meine Suche?', 'Etwa alle 30 Sekunden. ' + SPEED_MEASURED['de'] + ' Ruhige Suchen werden langsamer geprüft, höchstens alle 5 Minuten. Das Tempo ist in jedem Tarif gleich.'),
        ('Funktioniert es auf dem iPhone?', 'Ja, sobald SNYPD auf deinem Home-Bildschirm ist: Öffne snypd.store in Safari, tippe auf Teilen und dann auf &bdquo;Zum Home-Bildschirm&ldquo;, und schalte die Benachrichtigungen in der installierten App ein. Apple erlaubt Web-Push nur für Apps auf dem Home-Bildschirm. Auf Android, Windows und Mac funktionieren die Benachrichtigungen direkt im Browser.'),
        ('Gibt es einen kostenlosen Tarif?', 'Ja. Free enthält eine Suche, ohne Zeitlimit und ohne Karte. ' + TRIAL['de'] + ' Danach prüft Free, solange dein SNYPD-Dashboard geöffnet ist; bezahlte Tarife ab @@price:solo@@ im Monat prüfen rund um die Uhr, auch wenn es geschlossen ist.'),
        ('Mit welchen Vinted-Ländern funktioniert es?', 'Mit jeder Vinted-Seite in Europa und den USA, 26 insgesamt: vinted.de, vinted.at, vinted.fr, vinted.nl, vinted.be, vinted.it, vinted.es, vinted.pl, vinted.co.uk, vinted.com und die übrigen. Füge einen Suchlink der Seite ein, auf der du einkaufst; die Preise erscheinen in deren Währung.'),
    ]
    body = f"""
<section id="kurz">
  <h2>SNYPD in einem Absatz</h2>
  <div class="lg-box lg-mint"><p>SNYPD ist ein Vinted Bot für Benachrichtigungen, auch Vinted-Monitor genannt, für Reseller. Du fügst einen Vinted-Suchlink mit deinen Filtern ein (Marke, Größe, Preis, Zustand), und SNYPD prüft diese Suche etwa alle 30 Sekunden. Sobald eine neue Anzeige passt, erscheint sie in deinem Dashboard und du bekommst eine Push-Benachrichtigung auf Handy oder Computer. SNYPD fragt nie nach deinem Vinted-Passwort, meldet sich nie in deinem Konto an, kauft nichts und schreibt keinen Verkäufern. Der kostenlose Tarif lässt eine Suche laufen: in den ersten @@trial_days@@ Tagen rund um die Uhr, danach solange dein Dashboard geöffnet ist. Bezahlte Tarife ab @@price:solo@@ im Monat überwachen rund um die Uhr.</p></div>
</section>
<section id="arten">
  <h2>Die drei Arten von Vinted Bots</h2>
  <p>&bdquo;Vinted Bot&ldquo; steht für Tools, die sehr Unterschiedliches tun. Der entscheidende Unterschied: Handeln sie über dein Vinted-Konto?</p>
  <h3>BENACHRICHTIGUNGS-BOTS ODER VINTED-MONITORE</h3>
  <p>Sie beobachten deine Suchen und sagen dir Bescheid, wenn etwas Neues passt; Reseller nennen sie auch Monitore. Du kaufst selbst, deshalb müssen sie nichts über dein Vinted-Konto tun. SNYPD, Telvin Bot und Crazed sind Benachrichtigungs-Tools.</p>
  <h3>AUTOBUY- UND AUTOCOP-BOTS</h3>
  <p>Sie kaufen oder bestellen für dich. Kaufen auf Vinted braucht ein angemeldetes Konto, also handeln diese Tools über deins; V-Tools zum Beispiel gibt an, dass du deine eigenen Vinted-Konten verbindest. Souk, V-Tools und Resell Reserve verkaufen Autobuy-Funktionen.</p>
  <h3>SKRIPTE ZUM SELBST-HOSTEN</h3>
  <p>Open-Source-Projekte auf GitHub, die du selbst betreibst und die meist an Discord oder Telegram posten. Kostenlos, aber du betreibst den Server und reparierst ihn, wenn Vinted etwas ändert.</p>
  <p>Preise, Benachrichtigungswege und kostenlose Tarife der einzelnen Tools stehen nebeneinander im <a href="{SLUGS['compare']['en']}">Vergleich der Vinted Bots</a> (auf Englisch). Wie ein Monitor Schritt für Schritt funktioniert: <a href="{SLUGS['monitor']['en']}">Was ist ein Vinted-Monitor?</a> (auf Englisch)</p>
</section>
<section id="automatisierung">
  <h2>Vinted-Automatisierung: Käuferseite, nicht Verkäuferseite</h2>
  <p>&bdquo;Vinted-Automatisierung&ldquo; meint meistens Tools für Verkäufer: Sie stellen deine Artikel neu ein oder schieben sie hoch, schicken Angebote an Leute, die sie favorisiert haben, oder schreiben deine Beschreibungen. Sie arbeiten an deinem eigenen Shop, also handeln sie über dein Vinted-Konto.</p>
  <p>SNYPD automatisiert nur die Käuferseite: Es beobachtet Suchen und sagt dir, was neu ist. Es fasst weder deinen Shop noch deine Anzeigen noch deine Nachrichten an und meldet sich nie an. Wenn du deine eigenen Anzeigen hochschieben oder neu einstellen willst, ist SNYPD nicht das richtige Tool.</p>
</section>
<section id="so-gehts">
  <h2>So funktioniert SNYPD</h2>
  <ol>
    <li>Suche im Browser auf deiner Vinted-Seite und setze deine Filter: Marke, Größe, Preis, Zustand.</li>
    <li>Kopiere die Adresse aus der Adresszeile. Eine Suchadresse enthält <code>/catalog?</code>.</li>
    <li>Füge sie in SNYPD ein, gib ihr einen kurzen Namen und schalte sie ein.</li>
    <li>SNYPD prüft sie etwa alle 30 Sekunden. Neue Treffer landen in deinem Dashboard und, wenn du Benachrichtigungen eingeschaltet hast, auf deinem Handy oder Computer. Mehrere Funde kurz hintereinander kommen als eine Benachrichtigung.</li>
    <li>Tippe auf die Benachrichtigung. Sie öffnet die Anzeige auf Vinted, wo du kaufst oder ein Angebot machst.</li>
  </ol>
  {figure('feed', 'de')}
</section>
<section id="tempo">
  <h2>Wie schnell ist es?</h2>
  <p>SNYPD prüft jede aktive Suche etwa alle 30 Sekunden. {SPEED_MEASURED['de']} {VINTED_LAG['de']} Suchen, die oft neue Artikel finden, bleiben bei diesem Tempo; Suchen, die ruhig werden, werden langsamer geprüft, bis zu etwa 5 Minuten zwischen zwei Prüfungen, und werden wieder schneller, sobald sie etwas finden. Das Tempo ist in jedem Tarif gleich: Bezahlen bringt mehr Suchen und Überwachung rund um die Uhr, keine schnelleren Prüfungen.</p>
  <p>Manche Tools werben mit Benachrichtigungen in Millisekunden. SNYPD macht diese Aussage nicht. Was SNYPD verspricht: Eine bezahlte Suche läuft weiter, wenn dein Laptop zu ist und dein Handy in der Tasche steckt, also genau dann, wenn man die meisten Funde verpasst.</p>
</section>
<section id="kosten">
  <h2>Was es kostet</h2>
  {table(PLANS_HEAD['de'], PLANS_ROWS['de'])}
  <p>Monatliche Abrechnung, jederzeit kündbar. Oder für einen einzelnen Artikel ohne Abo: der @@pass_days@@-Tage-Pass, @@price:pass@@ einmalig für 1 Suche über @@pass_days@@ Tage, danach endet er von selbst. Der Market Report zeigt den typischen Angebotspreis eines Artikels auf Vinted nach Zustand; ein Beispiel im <a href="/de/vinted-preise">Vinted-Preisführer</a>. Alle Details auf der <a href="/plans">Tarifseite</a> (auf Englisch).</p>
</section>
<section id="konto">
  <h2>Was SNYPD von dir braucht</h2>
  <p>Eine E-Mail-Adresse für dein SNYPD-Konto. Kein Vinted-Passwort, keine Vinted-Anmeldung, keine Browser-Erweiterung. SNYPD liest öffentliche Anzeigen mit eigenen Systemen: dieselben Suchergebnisse, die jeder auf Vinted ohne Konto öffnen kann.</p>
  <p>Weil SNYPD sich nie als du anmeldet, passiert nichts davon in deinem Vinted-Konto. Wenn du kaufst, kaufst du über Vinted wie jeder andere Käufer.</p>
</section>
<section id="fragen">
  <h2>Fragen</h2>
  {faq_html(faq)}
</section>
<section id="testen">
  <h2>Probier es mit einer Suche</h2>
  {cta('de')}
</section>"""
    return page('bot', 'de', 'Vinted Bot: Benachrichtigung bei neuen Anzeigen, ohne Autobuy | SNYPD',
                'SNYPD ist ein Vinted Bot, der deine Suchen überwacht und dir eine Push-Benachrichtigung schickt, sobald eine passende Anzeige erscheint. Ohne Login, ohne Autobuy.',
                'VINTED BOT', 'Ein Vinted Bot, der dich benachrichtigt und nie dein Konto anfasst.',
                'Die meisten Vinted Bots werden mit automatischem Kaufen beworben, also damit, in deinem Namen zu handeln. SNYPD übernimmt den anderen Teil: Es beobachtet deine Vinted-Suchen und sagt dir Bescheid, wenn etwas Neues passt. Du entscheidest und kaufst selbst auf Vinted.',
                [('kurz', 'In einem Absatz'), ('arten', 'Drei Arten von Bots'), ('automatisierung', 'Automatisierung'), ('so-gehts', 'So funktioniert es'), ('tempo', 'Wie schnell'), ('kosten', 'Kosten'), ('konto', 'Dein Vinted-Konto'), ('fragen', 'Fragen')],
                body, [faq_ld(faq)])


def page_bot_nl():
    faq = [
        ('Koopt SNYPD artikelen voor mij?', 'Nee. SNYPD vindt nieuwe advertenties en waarschuwt je. Je opent de advertentie op Vinted en koopt of doet zelf een bod, via de normale betaling van Vinted.'),
        ('Moet ik SNYPD mijn Vinted-wachtwoord geven?', 'Nee. SNYPD vraagt nooit om je Vinted-inloggegevens en logt nooit in op je account. Je hebt alleen een e-mailadres nodig voor je SNYPD-account.'),
        ('Hoe vaak controleert SNYPD mijn zoekopdracht?', 'Ongeveer elke 30 seconden. ' + SPEED_MEASURED['nl'] + ' Rustige zoekopdrachten vertragen tot hooguit 5 minuten. De snelheid is op elk abonnement hetzelfde.'),
        ('Werkt het op een iPhone?', 'Ja, zodra SNYPD op je beginscherm staat: open snypd.store in Safari, tik op Deel en daarna op &ldquo;Zet op beginscherm&rdquo;, en zet de meldingen aan in de geïnstalleerde app. Apple staat webmeldingen alleen toe voor apps op het beginscherm. Op Android, Windows en Mac werken meldingen direct vanuit de browser.'),
        ('Is er een gratis abonnement?', 'Ja. Free bevat één zoekopdracht, zonder tijdslimiet en zonder kaart. ' + TRIAL['nl'] + ' Daarna controleert Free zolang je SNYPD-dashboard open staat; betaalde abonnementen vanaf @@price:solo@@ per maand controleren 24/7, ook als het dicht is.'),
        ('Met welke Vinted-landen werkt het?', 'Met elke Vinted-site in Europa en de VS, 26 in totaal: vinted.nl, vinted.be, vinted.fr, vinted.de, vinted.it, vinted.es, vinted.pl, vinted.co.uk, vinted.com en de rest. Plak een zoeklink van de site waar je koopt; prijzen verschijnen in de munteenheid van die site.'),
    ]
    body = f"""
<section id="samenvatting">
  <h2>SNYPD in één alinea</h2>
  <div class="lg-box lg-mint"><p>SNYPD is een Vinted bot voor meldingen, ook wel Vinted monitor genoemd, voor resellers. Je plakt een Vinted-zoeklink met je filters (merk, maat, prijs, staat) en SNYPD controleert die zoekopdracht ongeveer elke 30 seconden. Zodra een nieuwe advertentie past, verschijnt die in je dashboard en krijg je een pushmelding op je telefoon of computer. SNYPD vraagt nooit om je Vinted-wachtwoord, logt nooit in op je account, koopt niets en stuurt geen berichten naar verkopers. Het gratis abonnement laat één zoekopdracht lopen: de eerste @@trial_days@@ dagen 24/7, daarna zolang je dashboard open staat. Betaalde abonnementen vanaf @@price:solo@@ per maand houden 24/7 de wacht.</p></div>
</section>
<section id="soorten">
  <h2>De drie soorten Vinted bots</h2>
  <p>&ldquo;Vinted bot&rdquo; staat voor tools die heel verschillende dingen doen. Het grote verschil: handelen ze via je Vinted-account?</p>
  <h3>MELDINGSBOTS OF VINTED MONITORS</h3>
  <p>Ze houden je zoekopdrachten in de gaten en laten je weten wanneer er iets nieuws bij zit; resellers noemen ze ook monitors. Je koopt zelf, dus ze hoeven niets via je Vinted-account te doen. SNYPD, Telvin Bot en Crazed zijn meldingstools.</p>
  <h3>AUTOBUY- EN AUTOCOP-BOTS</h3>
  <p>Ze kopen of rekenen af voor jou. Kopen op Vinted vraagt een ingelogd account, dus deze tools handelen via het jouwe; V-Tools zegt bijvoorbeeld dat je je eigen Vinted-accounts koppelt. Souk, V-Tools en Resell Reserve verkopen autobuy-functies.</p>
  <h3>SCRIPTS OM ZELF TE HOSTEN</h3>
  <p>Open-sourceprojecten op GitHub die je zelf draait en die meestal naar Discord of Telegram posten. Gratis, maar jij beheert de server en repareert hem als Vinted iets verandert.</p>
  <p>Prijzen, meldingskanalen en gratis abonnementen van elke tool staan naast elkaar in de <a href="{SLUGS['compare']['en']}">vergelijking van Vinted bots</a> (in het Engels). Hoe een monitor stap voor stap werkt: <a href="{SLUGS['monitor']['en']}">wat is een Vinted monitor?</a> (in het Engels)</p>
</section>
<section id="automatisering">
  <h2>Vinted-automatisering: de kant van de koper, niet van de verkoper</h2>
  <p>&ldquo;Vinted-automatisering&rdquo; betekent meestal tools voor verkopers: ze plaatsen je artikelen opnieuw of zetten ze bovenaan, sturen aanbiedingen naar mensen die ze als favoriet hebben, of schrijven je beschrijvingen. Ze werken in je eigen winkel, dus ze handelen via je Vinted-account.</p>
  <p>SNYPD automatiseert alleen de kant van de koper: het houdt zoekopdrachten in de gaten en vertelt je wat nieuw is. Het komt niet aan je winkel, je advertenties of je berichten en logt nooit in. Wil je je eigen advertenties bovenaan zetten of opnieuw plaatsen, dan is SNYPD niet de juiste tool.</p>
</section>
<section id="werking">
  <h2>Zo werkt SNYPD</h2>
  <ol>
    <li>Zoek in een browser op je Vinted-site en stel je filters in: merk, maat, prijs, staat.</li>
    <li>Kopieer het adres uit de adresbalk. Een zoekadres bevat <code>/catalog?</code>.</li>
    <li>Plak het in SNYPD, geef het een korte naam en zet het aan.</li>
    <li>SNYPD controleert het ongeveer elke 30 seconden. Nieuwe treffers komen in je dashboard en, als je meldingen hebt aangezet, op je telefoon of computer. Meerdere vondsten kort na elkaar komen binnen als één melding.</li>
    <li>Tik op de melding. Die opent de advertentie op Vinted, waar je koopt of een bod doet.</li>
  </ol>
  {figure('feed', 'nl')}
</section>
<section id="snelheid">
  <h2>Hoe snel is het?</h2>
  <p>SNYPD controleert elke actieve zoekopdracht ongeveer elke 30 seconden. {SPEED_MEASURED['nl']} {VINTED_LAG['nl']} Zoekopdrachten die vaak nieuwe artikelen vinden, houden dat tempo; zoekopdrachten die rustig worden, worden trager gecontroleerd, tot ongeveer 5 minuten tussen twee controles, en versnellen weer zodra ze iets vinden. Het tempo is op elk abonnement hetzelfde: betalen geeft meer zoekopdrachten en 24/7 bewaking, geen snellere controles.</p>
  <p>Sommige tools adverteren met meldingen in milliseconden. SNYPD doet die belofte niet. Wat SNYPD wel belooft: een betaalde zoekopdracht blijft lopen als je laptop dicht is en je telefoon in je zak zit, precies wanneer je de meeste vondsten mist.</p>
</section>
<section id="kosten">
  <h2>Wat het kost</h2>
  {table(PLANS_HEAD['nl'], PLANS_ROWS['nl'])}
  <p>Maandelijks gefactureerd, altijd opzegbaar. Of, voor één artikel en zonder abonnement: de @@pass_days@@-dagenpas, @@price:pass@@ eenmalig voor 1 zoekopdracht gedurende @@pass_days@@ dagen, daarna stopt hij vanzelf. Het Market Report toont de typische vraagprijs van een artikel op Vinted per staat; een voorbeeld op <a href="/vinted-price-guide">Vinted-prijsgids</a> (in het Engels). Alle details op de <a href="/plans">abonnementenpagina</a> (in het Engels).</p>
</section>
<section id="account">
  <h2>Wat SNYPD van je nodig heeft</h2>
  <p>Een e-mailadres voor je SNYPD-account. Geen Vinted-wachtwoord, geen Vinted-login en geen browserextensie. SNYPD leest openbare advertenties met eigen systemen: dezelfde zoekresultaten die iedereen op Vinted zonder account kan openen.</p>
  <p>Omdat SNYPD nooit als jou inlogt, gebeurt niets ervan op je Vinted-account. Als je koopt, koop je via Vinted zoals elke andere koper.</p>
</section>
<section id="vragen">
  <h2>Vragen</h2>
  {faq_html(faq)}
</section>
<section id="proberen">
  <h2>Probeer het met één zoekopdracht</h2>
  {cta('nl')}
</section>"""
    return page('bot', 'nl', 'Vinted bot: melding bij nieuwe advertenties, zonder autobuy | SNYPD',
                'SNYPD is een Vinted bot die je zoekopdrachten in de gaten houdt en je een pushmelding stuurt zodra er een passende advertentie verschijnt. Zonder login, zonder autobuy.',
                'VINTED BOT', 'Een Vinted bot die je waarschuwt en nooit aan je account komt.',
                'De meeste Vinted bots worden verkocht op automatisch kopen, dus op handelen in jouw naam. SNYPD doet het andere deel van het werk: het houdt je Vinted-zoekopdrachten in de gaten en laat je weten wanneer er iets nieuws bij zit. Jij beslist en koopt zelf op Vinted.',
                [('samenvatting', 'In één alinea'), ('soorten', 'Drie soorten bots'), ('automatisering', 'Automatisering'), ('werking', 'Zo werkt het'), ('snelheid', 'Hoe snel'), ('kosten', 'Kosten'), ('account', 'Je Vinted-account'), ('vragen', 'Vragen')],
                body, [faq_ld(faq)])


def page_bot_it():
    faq = [
        ('SNYPD compra articoli al posto mio?', 'No. SNYPD trova i nuovi annunci e ti avvisa. Apri l’annuncio su Vinted e compri o fai un’offerta tu, con il normale pagamento di Vinted.'),
        ('Devo dare a SNYPD la mia password di Vinted?', 'No. SNYPD non chiede mai i tuoi dati di accesso a Vinted e non accede mai al tuo account. Per l’account SNYPD ti serve solo un indirizzo email.'),
        ('Ogni quanto SNYPD controlla la mia ricerca?', 'Circa ogni 30 secondi. ' + SPEED_MEASURED['it'] + ' Le ricerche tranquille rallentano, fino a un massimo di 5 minuti. La velocità è la stessa su ogni piano.'),
        ('Funziona su iPhone?', 'Sì, dopo aver aggiunto SNYPD alla schermata Home: apri snypd.store in Safari, tocca Condividi, poi &laquo;Aggiungi alla schermata Home&raquo;, e attiva le notifiche nell’app installata. Apple consente le notifiche web solo alle app sulla schermata Home. Su Android, Windows e Mac le notifiche funzionano direttamente dal browser.'),
        ('C’è un piano gratuito?', 'Sì. Free include una ricerca, senza limiti di tempo e senza carta. ' + TRIAL['it'] + ' Dopo, controlla finché la tua dashboard SNYPD è aperta; i piani a pagamento da @@price:solo@@ al mese controllano 24 ore su 24 anche quando è chiusa.'),
        ('Con quali paesi Vinted funziona?', 'Con ogni sito Vinted in Europa e negli Stati Uniti, 26 in tutto: vinted.it, vinted.fr, vinted.es, vinted.de, vinted.be, vinted.nl, vinted.pl, vinted.co.uk, vinted.com e gli altri. Incolla un link di ricerca del sito su cui compri; i prezzi appaiono nella valuta di quel sito.'),
    ]
    body = f"""
<section id="breve">
  <h2>SNYPD in un paragrafo</h2>
  <div class="lg-box lg-mint"><p>SNYPD è un bot Vinted per le notifiche, chiamato anche monitor Vinted, pensato per i reseller. Incolli un link di ricerca Vinted con i tuoi filtri (marca, taglia, prezzo, condizioni) e SNYPD controlla quella ricerca circa ogni 30 secondi. Appena un nuovo annuncio corrisponde, compare nella tua dashboard e ricevi una notifica push sul telefono o sul computer. SNYPD non chiede mai la tua password di Vinted, non accede mai al tuo account, non compra nulla e non scrive ai venditori. Il piano gratuito tiene attiva una ricerca: 24 ore su 24 nei primi @@trial_days@@ giorni, poi finché la dashboard è aperta. I piani a pagamento, da @@price:solo@@ al mese, controllano 24 ore su 24.</p></div>
</section>
<section id="tipi">
  <h2>I tre tipi di bot Vinted</h2>
  <p>&laquo;Bot Vinted&raquo; indica strumenti che fanno cose molto diverse. La differenza che conta: agiscono tramite il tuo account Vinted?</p>
  <h3>BOT DI NOTIFICA O MONITOR VINTED</h3>
  <p>Tengono d’occhio le tue ricerche e ti avvisano quando c’è qualcosa di nuovo; i reseller li chiamano anche monitor. Compri tu, quindi non devono fare nulla tramite il tuo account Vinted. SNYPD, Telvin Bot e Crazed sono strumenti di notifica.</p>
  <h3>BOT DI AUTOBUY E AUTOCOP</h3>
  <p>Comprano o pagano al posto tuo. Comprare su Vinted richiede un account con accesso effettuato, quindi questi strumenti agiscono tramite il tuo; V-Tools, per esempio, indica che colleghi i tuoi account Vinted. Souk, V-Tools e Resell Reserve vendono funzioni di autobuy.</p>
  <h3>SCRIPT DA FAR GIRARE IN PROPRIO</h3>
  <p>Progetti open source su GitHub che fai girare tu e che di solito pubblicano su Discord o Telegram. Gratis, ma il server lo gestisci tu e lo ripari quando Vinted cambia qualcosa.</p>
  <p>Prezzi, canali di notifica e piani gratuiti di ogni strumento sono affiancati nel <a href="{SLUGS['compare']['en']}">confronto dei bot Vinted</a> (in inglese). Come funziona un monitor passo per passo: <a href="{SLUGS['monitor']['en']}">cos’è un monitor Vinted?</a> (in inglese)</p>
</section>
<section id="automazione">
  <h2>Automazione Vinted: lato acquirente, non lato venditore</h2>
  <p>&laquo;Automazione Vinted&raquo; di solito indica strumenti per chi vende: ripubblicano o mettono in evidenza i tuoi articoli, inviano offerte a chi li ha messi nei Preferiti o scrivono le descrizioni. Lavorano sui tuoi articoli in vendita, quindi agiscono tramite il tuo account Vinted.</p>
  <p>SNYPD automatizza solo il lato di chi compra: tiene d’occhio le ricerche e ti dice cosa c’è di nuovo. Non tocca i tuoi annunci né i tuoi messaggi e non accede mai. Se vuoi mettere in evidenza o ripubblicare i tuoi annunci, SNYPD non è lo strumento giusto.</p>
</section>
<section id="come-funziona">
  <h2>Come funziona SNYPD</h2>
  <ol>
    <li>Cerca nel browser sul tuo sito Vinted e imposta i filtri: marca, taglia, prezzo, condizioni.</li>
    <li>Copia l’indirizzo dalla barra degli indirizzi. Un indirizzo di ricerca contiene <code>/catalog?</code>.</li>
    <li>Incollalo in SNYPD, dagli un nome breve e attivalo.</li>
    <li>SNYPD lo controlla circa ogni 30 secondi. I nuovi risultati arrivano nella dashboard e, se hai attivato le notifiche, sul telefono o sul computer. Più risultati ravvicinati arrivano in un’unica notifica.</li>
    <li>Tocca la notifica. Apre l’annuncio su Vinted, dove compri o fai un’offerta.</li>
  </ol>
  {figure('feed', 'it')}
</section>
<section id="velocita">
  <h2>Quanto è veloce?</h2>
  <p>SNYPD controlla ogni ricerca attiva circa ogni 30 secondi. {SPEED_MEASURED['it']} {VINTED_LAG['it']} Le ricerche che trovano spesso articoli nuovi mantengono questo ritmo; quelle che diventano tranquille vengono controllate più lentamente, fino a circa 5 minuti tra un controllo e l’altro, e riaccelerano appena trovano qualcosa. La velocità è la stessa su ogni piano: pagando ottieni più ricerche e il controllo 24 ore su 24, non controlli più rapidi.</p>
  <p>Alcuni strumenti promettono notifiche in millisecondi. SNYPD non fa questa promessa. Quello che SNYPD promette: una ricerca a pagamento continua a funzionare quando il portatile è chiuso e il telefono è in tasca, proprio quando si perdono più occasioni.</p>
</section>
<section id="costi">
  <h2>Quanto costa</h2>
  {table(PLANS_HEAD['it'], PLANS_ROWS['it'])}
  <p>Fatturazione mensile, disdici quando vuoi. Oppure, per un solo articolo e senza abbonamento: il pass di @@pass_days@@ giorni, @@price:pass@@ una tantum per 1 ricerca per @@pass_days@@ giorni, poi finisce da solo. Il Market Report mostra il prezzo richiesto tipico di un articolo su Vinted per condizione; un esempio su <a href="/vinted-price-guide">guida ai prezzi Vinted</a> (in inglese). Tutti i dettagli nella <a href="/plans">pagina dei piani</a> (in inglese).</p>
</section>
<section id="account">
  <h2>Cosa ti chiede SNYPD</h2>
  <p>Un indirizzo email per il tuo account SNYPD. Nessuna password di Vinted, nessun accesso a Vinted, nessuna estensione del browser. SNYPD legge gli annunci pubblici con i propri sistemi: gli stessi risultati di ricerca che chiunque può aprire su Vinted senza account.</p>
  <p>Poiché SNYPD non accede mai al posto tuo, niente di tutto questo avviene sul tuo account Vinted. Quando compri, compri tramite Vinted come qualsiasi altro acquirente.</p>
</section>
<section id="domande">
  <h2>Domande</h2>
  {faq_html(faq)}
</section>
<section id="prova">
  <h2>Provalo con una ricerca</h2>
  {cta('it')}
</section>"""
    return page('bot', 'it', 'Bot Vinted: notifica per i nuovi annunci, senza autobuy | SNYPD',
                'SNYPD è un bot Vinted che controlla le tue ricerche e ti invia una notifica push appena compare un annuncio che corrisponde. Senza login, senza autobuy.',
                'BOT VINTED', 'Un bot Vinted che ti avvisa e non tocca mai il tuo account.',
                'La maggior parte dei bot Vinted si vende sull’acquisto automatico, cioè sull’agire a nome tuo. SNYPD fa l’altra parte del lavoro: tiene d’occhio le tue ricerche Vinted e ti avvisa quando c’è qualcosa di nuovo. Decidi tu e compri tu su Vinted.',
                [('breve', 'In un paragrafo'), ('tipi', 'Tre tipi di bot'), ('automazione', 'Automazione'), ('come-funziona', 'Come funziona'), ('velocita', 'Quanto è veloce'), ('costi', 'Costi'), ('account', 'Il tuo account Vinted'), ('domande', 'Domande')],
                body, [faq_ld(faq)])


def page_bot_es():
    faq = [
        ('¿SNYPD compra artículos por mí?', 'No. SNYPD encuentra anuncios nuevos y te avisa. Abres el anuncio en Vinted y compras o haces una oferta tú, con el pago normal de Vinted.'),
        ('¿Tengo que darle a SNYPD mi contraseña de Vinted?', 'No. SNYPD nunca pide tus datos de acceso a Vinted y nunca inicia sesión en tu cuenta. Para tu cuenta de SNYPD solo necesitas un correo electrónico.'),
        ('¿Cada cuánto comprueba SNYPD mi búsqueda?', 'Más o menos cada 30 segundos. ' + SPEED_MEASURED['es'] + ' Las búsquedas tranquilas se ralentizan, hasta 5 minutos como máximo. La velocidad es la misma en todos los planes.'),
        ('¿Funciona en iPhone?', 'Sí, una vez que SNYPD está en tu pantalla de inicio: abre snypd.store en Safari, toca Compartir y luego &laquo;Añadir a pantalla de inicio&raquo;, y activa las notificaciones en la app instalada. Apple solo permite notificaciones web en apps de la pantalla de inicio. En Android, Windows y Mac las notificaciones funcionan directamente desde el navegador.'),
        ('¿Hay un plan gratuito?', 'Sí. Free incluye una búsqueda, sin límite de tiempo y sin tarjeta. ' + TRIAL['es'] + ' Después, comprueba mientras tu panel de SNYPD esté abierto; los planes de pago desde @@price:solo@@ al mes comprueban 24/7 aunque esté cerrado.'),
        ('¿Con qué países de Vinted funciona?', 'Con todos los sitios de Vinted en Europa y Estados Unidos, 26 en total: vinted.es, vinted.pt, vinted.fr, vinted.it, vinted.de, vinted.be, vinted.nl, vinted.co.uk, vinted.com y los demás. Pega un enlace de búsqueda del sitio en el que compras; los precios aparecen en la moneda de ese sitio.'),
    ]
    body = f"""
<section id="resumen">
  <h2>SNYPD en un párrafo</h2>
  <div class="lg-box lg-mint"><p>SNYPD es un bot de Vinted para notificaciones, también llamado monitor de Vinted, pensado para revendedores. Pegas un enlace de búsqueda de Vinted con tus filtros (marca, talla, precio, estado) y SNYPD comprueba esa búsqueda más o menos cada 30 segundos. En cuanto un anuncio nuevo coincide, aparece en tu panel y recibes una notificación push en el móvil o el ordenador. SNYPD nunca pide tu contraseña de Vinted, nunca inicia sesión en tu cuenta, no compra nada y no escribe a los vendedores. El plan gratuito mantiene una búsqueda activa: 24/7 durante los primeros @@trial_days@@ días y, después, mientras tu panel esté abierto. Los planes de pago, desde @@price:solo@@ al mes, vigilan 24/7.</p></div>
</section>
<section id="tipos">
  <h2>Los tres tipos de bots de Vinted</h2>
  <p>&laquo;Bot de Vinted&raquo; se usa para herramientas que hacen cosas muy distintas. La diferencia clave: ¿actúan a través de tu cuenta de Vinted?</p>
  <h3>BOTS DE NOTIFICACIÓN O MONITORES DE VINTED</h3>
  <p>Vigilan tus búsquedas y te avisan cuando aparece algo nuevo; los revendedores también los llaman monitores. Compras tú, así que no necesitan hacer nada a través de tu cuenta de Vinted. SNYPD, Telvin Bot y Crazed son herramientas de notificación.</p>
  <h3>BOTS DE AUTOBUY Y AUTOCOP</h3>
  <p>Compran o pagan por ti. Comprar en Vinted requiere una cuenta con la sesión iniciada, así que estas herramientas actúan a través de la tuya; V-Tools, por ejemplo, indica que conectas tus propias cuentas de Vinted. Souk, V-Tools y Resell Reserve venden funciones de autobuy.</p>
  <h3>SCRIPTS PARA EJECUTAR TÚ MISMO</h3>
  <p>Proyectos de código abierto en GitHub que ejecutas tú y que suelen publicar en Discord o Telegram. Gratis, pero el servidor lo gestionas tú y lo arreglas cuando Vinted cambia algo.</p>
  <p>Precios, canales de aviso y planes gratuitos de cada herramienta, uno al lado del otro, en la <a href="{SLUGS['compare']['en']}">comparativa de bots de Vinted</a> (en inglés). Cómo funciona un monitor paso a paso: <a href="{SLUGS['monitor']['en']}">¿qué es un monitor de Vinted?</a> (en inglés)</p>
</section>
<section id="automatizacion">
  <h2>Automatización de Vinted: lado del comprador, no del vendedor</h2>
  <p>&laquo;Automatización de Vinted&raquo; suele referirse a herramientas para vendedores: vuelven a subir o destacan tus artículos, envían ofertas a quien los tiene en favoritos o escriben tus descripciones. Trabajan sobre tus propios artículos en venta, así que actúan a través de tu cuenta de Vinted.</p>
  <p>SNYPD solo automatiza el lado del comprador: vigila búsquedas y te dice qué hay de nuevo. No toca tus anuncios ni tus mensajes y nunca inicia sesión. Si quieres destacar o volver a subir tus propios anuncios, SNYPD no es la herramienta adecuada.</p>
</section>
<section id="como-funciona">
  <h2>Cómo funciona SNYPD</h2>
  <ol>
    <li>Busca en el navegador en tu sitio de Vinted y pon tus filtros: marca, talla, precio, estado.</li>
    <li>Copia la dirección de la barra de direcciones. Una dirección de búsqueda contiene <code>/catalog?</code>.</li>
    <li>Pégala en SNYPD, ponle un nombre corto y actívala.</li>
    <li>SNYPD la comprueba más o menos cada 30 segundos. Los resultados nuevos llegan a tu panel y, si has activado las notificaciones, a tu móvil u ordenador. Varios hallazgos seguidos llegan en una sola notificación.</li>
    <li>Toca la notificación. Abre el anuncio en Vinted, donde compras o haces una oferta.</li>
  </ol>
  {figure('feed', 'es')}
</section>
<section id="velocidad">
  <h2>¿Cómo de rápido es?</h2>
  <p>SNYPD comprueba cada búsqueda activa más o menos cada 30 segundos. {SPEED_MEASURED['es']} {VINTED_LAG['es']} Las búsquedas que encuentran artículos nuevos a menudo mantienen ese ritmo; las que se quedan tranquilas se comprueban más despacio, hasta unos 5 minutos entre dos comprobaciones, y vuelven a acelerar en cuanto encuentran algo. La velocidad es la misma en todos los planes: pagar te da más búsquedas y vigilancia 24/7, no comprobaciones más rápidas.</p>
  <p>Algunas herramientas anuncian notificaciones en milisegundos. SNYPD no hace esa promesa. Lo que SNYPD sí promete: una búsqueda de pago sigue funcionando con el portátil cerrado y el móvil en el bolsillo, justo cuando más chollos se pierden.</p>
</section>
<section id="precio">
  <h2>Cuánto cuesta</h2>
  {table(PLANS_HEAD['es'], PLANS_ROWS['es'])}
  <p>Facturación mensual, cancela cuando quieras. O, para un solo artículo y sin suscripción: el pase de @@pass_days@@ días, @@price:pass@@ en un único pago por 1 búsqueda durante @@pass_days@@ días; después termina solo. El Market Report muestra el precio pedido típico de un artículo en Vinted según su estado; un ejemplo en <a href="/vinted-price-guide">guía de precios de Vinted</a> (en inglés). Todos los detalles en la <a href="/plans">página de planes</a> (en inglés).</p>
</section>
<section id="cuenta">
  <h2>Qué necesita SNYPD de ti</h2>
  <p>Un correo electrónico para tu cuenta de SNYPD. Sin contraseña de Vinted, sin iniciar sesión en Vinted y sin extensión del navegador. SNYPD lee anuncios públicos con sus propios sistemas: los mismos resultados de búsqueda que cualquiera puede abrir en Vinted sin cuenta.</p>
  <p>Como SNYPD nunca inicia sesión como tú, nada de esto pasa en tu cuenta de Vinted. Cuando compras, compras a través de Vinted como cualquier otro comprador.</p>
</section>
<section id="preguntas">
  <h2>Preguntas</h2>
  {faq_html(faq)}
</section>
<section id="probar">
  <h2>Pruébalo con una búsqueda</h2>
  {cta('es')}
</section>"""
    return page('bot', 'es', 'Bot de Vinted: aviso de anuncios nuevos, sin autobuy | SNYPD',
                'SNYPD es un bot de Vinted que vigila tus búsquedas y te envía una notificación push en cuanto aparece un anuncio que coincide. Sin login, sin autobuy.',
                'BOT DE VINTED', 'Un bot de Vinted que te avisa y nunca toca tu cuenta.',
                'La mayoría de los bots de Vinted se venden por la compra automática, es decir, por actuar en tu nombre. SNYPD hace la otra parte del trabajo: vigila tus búsquedas de Vinted y te avisa cuando aparece algo nuevo. Tú decides y compras en Vinted.',
                [('resumen', 'En un párrafo'), ('tipos', 'Tres tipos de bots'), ('automatizacion', 'Automatización'), ('como-funciona', 'Cómo funciona'), ('velocidad', 'Cómo de rápido'), ('precio', 'Precio'), ('cuenta', 'Tu cuenta de Vinted'), ('preguntas', 'Preguntas')],
                body, [faq_ld(faq)])


# ------------------------------------------------------------------ page: vinted bot
def page_bot(lang):
    if lang in cps.LANGS:
        return cps.page_bot_pl_sv(lang)
    if lang == 'de':
        return page_bot_de()
    if lang == 'nl':
        return page_bot_nl()
    if lang == 'it':
        return page_bot_it()
    if lang == 'es':
        return page_bot_es()
    if lang == 'en':
        faq = [
            ('Does SNYPD buy items for me?', 'No. SNYPD finds new listings and alerts you. You open the listing on Vinted and buy or make an offer yourself, through Vinted’s normal checkout.'),
            ('Do I need to give SNYPD my Vinted password?', 'No. SNYPD never asks for your Vinted login and never signs in to your account. You only need an email address for your SNYPD account.'),
            ('How often does SNYPD check my search?', 'About every 30 seconds. ' + SPEED_MEASURED['en'] + ' Searches that go quiet slow down to at most 5 minutes. Speed is the same on every plan.'),
            ('Does it work on iPhone?', 'Yes, once SNYPD is added to your Home Screen: open snypd.store in Safari, tap Share, then Add to Home Screen, and turn on alerts in the installed app. Apple only allows web push for Home Screen apps. On Android, Windows and Mac, alerts work straight from the browser.'),
            ('Is there a free plan?', 'Yes. Free includes one search with no time limit and no card. ' + TRIAL['en'] + ' After that it checks while your SNYPD dashboard is open; paid plans from @@price:solo@@ a month keep checking 24/7 with it closed.'),
            ('Which Vinted countries does it work with?', 'Every Vinted site in Europe and the US, 26 in all: vinted.fr, vinted.be, vinted.de, vinted.nl, vinted.it, vinted.es, vinted.pl, vinted.co.uk, vinted.com and the rest. Paste a search link from the site you shop on; prices show in that site’s currency.'),
        ]
        body = f"""
<section id="answer">
  <h2>SNYPD in one paragraph</h2>
  <div class="lg-box lg-mint"><p>SNYPD is a Vinted alert bot, also called a Vinted monitor, for resellers. You paste a Vinted search link with your filters (brand, size, price, condition) and SNYPD checks that search about every 30 seconds. When a new listing matches, it appears in your dashboard and you get a push notification on your phone or computer. SNYPD never asks for your Vinted password, never signs in to your account, never buys and never messages sellers. The free plan runs one search, 24/7 for the first @@trial_days@@ days and then while your dashboard is open; paid plans from @@price:solo@@ a month keep watching 24/7.</p></div>
</section>
<section id="kinds">
  <h2>The three kinds of Vinted bot</h2>
  <p>&ldquo;Vinted bot&rdquo; covers tools that do very different things. What separates them is whether they act on your Vinted account.</p>
  <h3>ALERT BOTS, OR VINTED MONITORS</h3>
  <p>They watch your searches and tell you when something new matches; resellers also call them monitors. You buy yourself, so they have no reason to act on your Vinted account. SNYPD, Telvin Bot and Crazed are alert tools.</p>
  <h3>AUTOBUY AND AUTOCOP BOTS</h3>
  <p>They buy or check out for you. Buying on Vinted needs a logged-in account, so these tools act through yours; V-Tools, for example, states that you connect your own Vinted accounts. Souk, V-Tools and Resell Reserve sell autobuy features.</p>
  <h3>DO-IT-YOURSELF SCRIPTS</h3>
  <p>Open-source projects on GitHub that you host yourself, usually posting to Discord or Telegram. Free, but you run the server and fix it when Vinted changes something.</p>
  <p>Prices, channels and free plans of each tool are side by side in <a href="{SLUGS['compare']['en']}">Vinted bots compared</a>. How a monitor works, step by step: <a href="{SLUGS['monitor']['en']}">what is a Vinted monitor?</a></p>
</section>
<section id="automation">
  <h2>Vinted automation: the buyer side, not the seller side</h2>
  <p>&ldquo;Vinted automation&rdquo; usually means seller tools: they relist or bump your items, send offers to people who favourited them, or write your descriptions. They work on your own shop, so they act on your Vinted account.</p>
  <p>SNYPD automates the buyer side only: it watches searches and tells you what is new. It does not touch your shop, your listings or your messages, and it never signs in. If you want your own listings bumped or relisted, SNYPD is not that tool.</p>
</section>
<section id="how">
  <h2>How SNYPD works</h2>
  <ol>
    <li>In a browser, search on your Vinted site and set your filters: brand, size, price, condition.</li>
    <li>Copy the address from the browser bar. A search address contains <code>/catalog?</code>.</li>
    <li>Paste it into SNYPD, give it a short name and switch it on.</li>
    <li>SNYPD checks it about every 30 seconds. New matches go to your dashboard and, if you turned alerts on, to your phone or computer. Several finds close together arrive as one notification.</li>
    <li>Tap the alert. It opens the listing on Vinted, where you buy or make an offer.</li>
  </ol>
  {figure('feed', 'en')}
</section>
<section id="speed">
  <h2>How fast is it?</h2>
  <p>SNYPD checks each active search about every 30 seconds. {SPEED_MEASURED['en']} {VINTED_LAG['en']} Searches that keep producing new items stay at that pace; searches that go quiet slow down, up to about 5 minutes between checks, and speed back up as soon as they find something. The speed is the same on every plan: paying buys more searches and 24/7 watching, not faster checks.</p>
  <p>Some tools advertise alerts in milliseconds. SNYPD does not make that claim. What it does promise is that a paid search keeps running when your laptop is closed and your phone is in your pocket, which is when most finds are missed.</p>
</section>
<section id="pricing">
  <h2>What it costs</h2>
  {table(PLANS_HEAD['en'], PLANS_ROWS['en'])}
  <p>Billed monthly, cancel any time. Or, for one item and no subscription: the Hunt Pass, @@price:pass@@ once for 1 search over @@pass_days@@ days, then it simply ends. The Market Report shows the typical Vinted asking price of an item by condition; see a sample in <a href="/vinted-price-guide">Vinted price guide</a>. Full details on <a href="/plans">the plans page</a>.</p>
</section>
<section id="account">
  <h2>What SNYPD needs from you</h2>
  <p>An email address for your SNYPD account. No Vinted password, no Vinted login and no browser extension. SNYPD reads public listings with its own systems: the same search results anyone can open on Vinted without an account.</p>
  <p>Because SNYPD never signs in as you, nothing it does happens on your Vinted account. When you buy, you buy through Vinted like any other buyer.</p>
</section>
<section id="faq">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="start">
  <h2>Try it on one search</h2>
  {cta('en')}
</section>"""
        return page('bot', 'en', 'Vinted Bot & Monitor: New Listing Alerts, No Autobuy | SNYPD',
                    'SNYPD is a Vinted bot and monitor that watches your searches and sends a push alert when a matching listing appears. It never logs in, buys or messages for you.',
                    'VINTED BOT &amp; MONITOR', 'A Vinted bot and monitor that alerts you and never touches your account.',
                    'Most Vinted bots are sold on buying for you, which means acting as you. SNYPD does the other part of the job: it keeps watching your Vinted searches and tells you when something new matches, so you decide and buy on Vinted yourself.',
                    [('answer', 'In one paragraph'), ('kinds', 'Three kinds of bot'), ('automation', 'Automation'), ('how', 'How it works'), ('speed', 'How fast'), ('pricing', 'What it costs'), ('account', 'Your Vinted account'), ('faq', 'Questions')],
                    body, [faq_ld(faq)])
    faq = [
        ('Est-ce que SNYPD achète à ma place ?', 'Non. SNYPD trouve les nouvelles annonces et t’alerte. Tu ouvres l’annonce sur Vinted et tu achètes ou fais une offre toi-même, avec le paiement normal de Vinted.'),
        ('Dois-je donner mon mot de passe Vinted ?', 'Non. SNYPD ne demande jamais tes identifiants Vinted et ne se connecte jamais à ton compte. Il te faut seulement une adresse e-mail pour ton compte SNYPD.'),
        ('À quelle fréquence SNYPD vérifie ma recherche ?', 'Environ toutes les 30 secondes. ' + SPEED_MEASURED['fr'] + ' Les recherches calmes ralentissent, jusqu’à 5 minutes au plus. La vitesse est la même pour tous les plans.'),
        ('Est-ce que ça marche sur iPhone ?', 'Oui, une fois SNYPD ajouté à l’écran d’accueil : ouvre snypd.store dans Safari, appuie sur Partager puis Sur l’écran d’accueil, et active les alertes dans l’app installée. Apple n’autorise les notifications web que pour les apps de l’écran d’accueil. Sur Android, Windows et Mac, les alertes marchent directement depuis le navigateur.'),
        ('Y a-t-il un plan gratuit ?', 'Oui. Le plan Free comprend une recherche, sans limite de durée et sans carte. ' + TRIAL['fr'] + ' Ensuite, il vérifie tant que ton tableau de bord SNYPD est ouvert ; les plans payants, à partir de @@price:solo@@ par mois, vérifient 24h/24 même fermé.'),
        ('Avec quels pays Vinted ça fonctionne ?', 'Tous les sites Vinted d’Europe et des États-Unis, 26 au total : vinted.fr, vinted.be, vinted.de, vinted.nl, vinted.it, vinted.es, vinted.pl, vinted.co.uk et vinted.com, entre autres. Colle un lien de recherche du site où tu achètes ; les prix s’affichent dans la devise de ce site.'),
    ]
    body = f"""
<section id="resume">
  <h2>SNYPD en un paragraphe</h2>
  <div class="lg-box lg-mint"><p>SNYPD est un bot d’alertes Vinted pour les revendeurs. Tu colles le lien d’une recherche Vinted avec tes filtres (marque, taille, prix, état) et SNYPD vérifie cette recherche environ toutes les 30 secondes. Quand une nouvelle annonce correspond, elle apparaît dans ton tableau de bord et tu reçois une notification push sur ton téléphone ou ton ordinateur. SNYPD ne demande jamais ton mot de passe Vinted, ne se connecte jamais à ton compte, n’achète rien et n’envoie aucun message aux vendeurs. Le plan gratuit fait tourner une recherche 24h/24 pendant les @@trial_days@@ premiers jours, puis tant que ton tableau de bord est ouvert ; les plans payants, à partir de @@price:solo@@ par mois, surveillent 24h/24.</p></div>
</section>
<section id="types">
  <h2>Les trois types de bot Vinted</h2>
  <p>« Bot Vinted » désigne des outils qui font des choses très différentes. Ce qui les distingue : est-ce qu’ils agissent sur ton compte Vinted ?</p>
  <h3>BOTS D’ALERTES, OU MONITORS VINTED</h3>
  <p>Ils surveillent tes recherches et te préviennent quand un nouvel article correspond ; on parle aussi de « monitor Vinted ». Tu achètes toi-même, donc ils n’ont aucune raison d’agir sur ton compte Vinted. SNYPD, Telvin Bot et Crazed sont des outils d’alertes.</p>
  <h3>BOTS D’ACHAT AUTOMATIQUE (AUTOBUY, AUTOCOP)</h3>
  <p>Ils achètent ou passent commande à ta place. Acheter sur Vinted demande un compte connecté, donc ces outils agissent via le tien ; V-Tools, par exemple, indique que tu connectes tes propres comptes Vinted. Souk, V-Tools et Resell Reserve vendent de l’achat automatique.</p>
  <h3>SCRIPTS À HÉBERGER SOI-MÊME</h3>
  <p>Des projets open source sur GitHub que tu héberges toi-même, qui postent en général sur Discord ou Telegram. Gratuits, mais c’est toi qui gères le serveur et qui répares quand Vinted change quelque chose.</p>
  <p>Les prix, canaux d’alerte et plans gratuits de chaque outil sont côte à côte dans le <a href="{SLUGS['compare']['fr']}">comparatif des bots Vinted</a>. Le fonctionnement d’un monitor, étape par étape : <a href="{SLUGS['monitor']['fr']}">qu’est-ce qu’un monitor Vinted ?</a></p>
</section>
<section id="automatisation">
  <h2>Automatisation Vinted : côté acheteur, pas côté vendeur</h2>
  <p>« Automatisation Vinted » désigne le plus souvent des outils pour vendeurs : ils republient ou remontent tes articles, envoient des offres aux personnes qui les ont mis en favoris, ou rédigent tes descriptions. Ils travaillent sur ta propre boutique, donc ils agissent sur ton compte Vinted.</p>
  <p>SNYPD automatise uniquement le côté acheteur : il surveille des recherches et te dit ce qui est nouveau. Il ne touche ni à ta boutique, ni à tes annonces, ni à tes messages, et ne se connecte jamais. Si tu veux remonter ou republier tes propres annonces, SNYPD n’est pas cet outil.</p>
</section>
<section id="fonctionnement">
  <h2>Comment marche SNYPD</h2>
  <ol>
    <li>Dans un navigateur, fais ta recherche sur ton site Vinted et règle tes filtres : marque, taille, prix, état.</li>
    <li>Copie l’adresse dans la barre du navigateur. Une adresse de recherche contient <code>/catalog?</code>.</li>
    <li>Colle-la dans SNYPD, donne-lui un nom court et active-la.</li>
    <li>SNYPD la vérifie environ toutes les 30 secondes. Les nouvelles annonces arrivent dans ton tableau de bord et, si tu as activé les alertes, sur ton téléphone ou ton ordinateur. Plusieurs trouvailles rapprochées arrivent en une seule notification.</li>
    <li>Appuie sur l’alerte. Elle ouvre l’annonce sur Vinted, où tu achètes ou fais une offre.</li>
  </ol>
  {figure('feed', 'fr')}
</section>
<section id="vitesse">
  <h2>C’est rapide ?</h2>
  <p>SNYPD vérifie chaque recherche active environ toutes les 30 secondes. {SPEED_MEASURED['fr']} {VINTED_LAG['fr']} Les recherches qui trouvent souvent de nouveaux articles gardent ce rythme ; celles qui deviennent calmes ralentissent, jusqu’à environ 5 minutes entre deux vérifications, et réaccélèrent dès qu’elles trouvent quelque chose. La vitesse est la même pour tous les plans : payer donne plus de recherches et une surveillance 24h/24, pas des vérifications plus rapides.</p>
  <p>Certains outils annoncent des alertes en millisecondes. SNYPD ne fait pas cette promesse. Ce qu’il promet, c’est qu’une recherche payante continue de tourner quand ton ordinateur est fermé et ton téléphone dans ta poche, c’est-à-dire au moment où l’on rate le plus d’affaires.</p>
</section>
<section id="prix">
  <h2>Combien ça coûte</h2>
  {table(PLANS_HEAD['fr'], PLANS_ROWS['fr'])}
  <p>Facturé chaque mois, résiliable à tout moment. Ou, pour un seul article et sans abonnement, le Pass 30 jours&nbsp;: @@price:pass@@ en une fois pour 1 recherche pendant @@pass_days@@ jours, puis il s’arrête tout seul. Le Market Report montre le prix demandé typique d’un article sur Vinted selon son état ; un exemple dans <a href="/fr/guide-prix-vinted">Guide des prix Vinted</a>. Tous les détails sur <a href="/plans">la page des tarifs</a>.</p>
</section>
<section id="compte">
  <h2>Ce dont SNYPD a besoin</h2>
  <p>Une adresse e-mail pour ton compte SNYPD. Pas de mot de passe Vinted, pas de connexion Vinted, pas d’extension de navigateur. SNYPD lit les annonces publiques avec ses propres systèmes : les mêmes résultats de recherche que n’importe qui peut ouvrir sur Vinted sans compte.</p>
  <p>Comme SNYPD ne se connecte jamais à ta place, rien de ce qu’il fait ne se passe sur ton compte Vinted. Quand tu achètes, tu achètes sur Vinted comme n’importe quel acheteur.</p>
</section>
<section id="questions">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="essayer">
  <h2>Essaie sur une recherche</h2>
  {cta('fr')}
</section>"""
    return page('bot', 'fr', 'Bot Vinted d’alertes, sans achat automatique | SNYPD',
                'SNYPD est un bot Vinted qui surveille tes recherches et t’envoie une alerte push quand une annonce correspond. Sans accès à ton compte, sans achat auto.',
                'BOT VINTED', 'Un bot Vinted qui t’alerte, sans jamais toucher à ton compte.',
                'La plupart des bots Vinted se vendent sur l’achat automatique, donc sur le fait d’agir à ta place. SNYPD fait l’autre partie du travail : il surveille tes recherches Vinted et te prévient quand un nouvel article correspond. Tu décides et tu achètes toi-même sur Vinted.',
                [('resume', 'En un paragraphe'), ('types', 'Trois types de bot'), ('automatisation', 'Automatisation'), ('fonctionnement', 'Fonctionnement'), ('vitesse', 'Vitesse'), ('prix', 'Prix'), ('compte', 'Ton compte Vinted'), ('questions', 'Questions')],
                body, [faq_ld(faq)])


# ------------------------------------------------------------------ page: notifications
def page_notify(lang):
    if lang == 'en':
        body = f"""
<section id="answer">
  <h2>Short answer</h2>
  <div class="lg-box lg-mint"><p>Vinted&rsquo;s saved searches show a counter, not an alert. According to Vinted&rsquo;s help centre, a saved search shows a number with a plus sign (&ldquo;+N&rdquo;) for new items the next time you open the search bar, and the count resets when you look. Vinted&rsquo;s list of what triggers a notification does not include new matches for a saved search. To get a push notification for each new match, you need a tool that watches the search for you.</p></div>
</section>
<section id="vinted">
  <h2>What Vinted&rsquo;s saved searches do</h2>
  <p>Vinted&rsquo;s own help page says that, the next time you open the search bar, a saved search shows</p>
  <blockquote>&ldquo;a number with a plus indicating how many new items were listed&rdquo;<cite>Vinted Help Centre, <a href="{HELP435['en']}" rel="nofollow noopener">Save your searches</a></cite></blockquote>
  <ul>
    <li>You can save an unlimited number of searches.</li>
    <li>The counter resets each time you view the search.</li>
    <li>Saved searches you never open are removed after 6 months.</li>
  </ul>
  <p>Vinted&rsquo;s notifications page lists what does trigger a notification: members you follow listing new items, price drops and sales on items you favourited, favourites on your own items, new followers, feedback, messages and news from Vinted (<a href="{HELP433['en']}" rel="nofollow noopener">Managing your notifications</a>). New matches for a saved search are not on that list.</p>
  <p>Some third-party sites say Vinted sends occasional notifications for saved searches. Vinted does not document one, so this page does not assume one.</p>
</section>
{alert_ways_table('en')}
<section id="enough">
  <h2>When Vinted&rsquo;s own tools are enough</h2>
  <ul>
    <li>You browse Vinted several times a day anyway: the counter tells you where to look.</li>
    <li>You want new items from one particular seller: follow them, and Vinted notifies you when they list.</li>
    <li>You are waiting for a price drop on one item: favourite it, and Vinted notifies you when the price is reduced.</li>
  </ul>
</section>
<section id="alerts">
  <h2>When you need real alerts</h2>
  <p>If you resell, the listings worth having can be gone before your next look at the counter. An alert tool checks the search for you and notifies you when something new matches, so you see it while it is still for sale.</p>
  <p>With SNYPD, that search is the same one you saved on Vinted:</p>
  <ol>
    <li>Open the search on Vinted in a browser, with your filters (brand, size, price, condition).</li>
    <li>Copy the address from the browser bar. It contains <code>/catalog?</code>.</li>
    <li>Paste it into SNYPD and switch it on.</li>
    <li>SNYPD checks it about every 30 seconds and sends a push notification to your phone or computer when a new listing matches. The alert opens the listing on Vinted.</li>
  </ol>
  <p>SNYPD never asks for your Vinted login. The free plan runs one search: 24/7 for the first @@trial_days@@ days, then while your dashboard is open; paid plans from @@price:solo@@ a month keep checking 24/7. More on how it works: <a href="{SLUGS['bot']['en']}">SNYPD, the Vinted alert bot</a>.</p>
  {figure('feed', 'en')}
</section>
{push_setup('en')}
<section id="start">
  <h2>Try it on one search</h2>
  {cta('en')}
</section>"""
        return page('notify', 'en', 'Vinted Alerts & Notifications for New Listings (2026) | SNYPD',
                    'Vinted’s saved searches show a +N counter, not a push alert. What Vinted’s own help centre says, and how to get a notification for each new match.',
                    'VINTED NOTIFICATIONS', 'How to get notified when something new is listed on Vinted',
                    'Vinted lets you save searches, but it does not document a notification for new matches. Here is exactly what Vinted&rsquo;s help centre says, and how to get an alert on your phone for every new listing that matches.',
                    [('answer', 'Short answer'), ('vinted', 'What Vinted does'), ('ways', 'Every way'), ('enough', 'When that is enough'), ('alerts', 'Real alerts'), ('push', 'Push setup')],
                    body)
    body = f"""
<section id="reponse">
  <h2>Réponse courte</h2>
  <div class="lg-box lg-mint"><p>Les recherches sauvegardées de Vinted affichent un compteur, pas une alerte. Selon le centre d’aide de Vinted, une recherche sauvegardée affiche un nombre suivi d’un signe plus (« +N ») pour les nouveaux articles la prochaine fois que tu ouvres la barre de recherche, et le compteur revient à zéro quand tu consultes la recherche. La liste de Vinted de ce qui déclenche une notification ne contient pas les nouvelles annonces d’une recherche sauvegardée. Pour recevoir une notification push à chaque nouvelle annonce, il faut un outil qui surveille la recherche pour toi.</p></div>
</section>
<section id="vinted">
  <h2>Ce que font les recherches sauvegardées de Vinted</h2>
  <p>D’après la page d’aide de Vinted, la prochaine fois que tu ouvres la barre de recherche, une recherche sauvegardée affiche</p>
  <blockquote>« un nombre suivi d’un signe plus indiquant le nombre de nouveaux articles »<cite>Centre d’aide Vinted, <a href="{HELP435['fr']}" rel="nofollow noopener">Comment sauvegarder une recherche ?</a></cite></blockquote>
  <ul>
    <li>Tu peux sauvegarder un nombre illimité de recherches.</li>
    <li>Le compteur est remis à zéro à chaque fois que tu consultes la recherche.</li>
    <li>Les recherches sauvegardées que tu n’ouvres jamais sont retirées au bout de 6 mois.</li>
  </ul>
  <p>La page de Vinted sur les notifications liste ce qui en déclenche une : les membres que tu suis qui publient de nouveaux articles, les baisses de prix et les ventes des articles en favoris, les favoris sur tes articles, les nouveaux abonnés, les évaluations, les messages et les actualités de Vinted (<a href="{HELP433['fr']}" rel="nofollow noopener">Comment gérer tes notifications ?</a>). Les nouvelles annonces d’une recherche sauvegardée n’y figurent pas.</p>
  <p>Certains sites affirment que Vinted envoie parfois des notifications pour les recherches sauvegardées. Vinted n’en documente aucune, donc cette page n’en suppose aucune.</p>
</section>
{alert_ways_table('fr')}
<section id="suffisant">
  <h2>Quand les outils de Vinted suffisent</h2>
  <ul>
    <li>Tu vas sur Vinted plusieurs fois par jour de toute façon : le compteur te dit où regarder.</li>
    <li>Tu veux les nouveautés d’un vendeur précis : abonne-toi à lui, Vinted te prévient quand il publie.</li>
    <li>Tu attends une baisse de prix sur un article : mets-le en favori, Vinted te prévient quand le prix baisse.</li>
  </ul>
</section>
<section id="alertes">
  <h2>Quand il te faut de vraies alertes</h2>
  <p>Si tu revends, les annonces intéressantes peuvent être parties avant ton prochain coup d’œil au compteur. Un outil d’alertes vérifie la recherche pour toi et te prévient quand un nouvel article correspond, pour que tu le voies tant qu’il est encore en vente.</p>
  <p>Avec SNYPD, c’est la même recherche que celle que tu as sauvegardée sur Vinted :</p>
  <ol>
    <li>Ouvre la recherche sur Vinted dans un navigateur, avec tes filtres (marque, taille, prix, état).</li>
    <li>Copie l’adresse dans la barre du navigateur. Elle contient <code>/catalog?</code>.</li>
    <li>Colle-la dans SNYPD et active-la.</li>
    <li>SNYPD la vérifie environ toutes les 30 secondes et envoie une notification push sur ton téléphone ou ton ordinateur quand une nouvelle annonce correspond. L’alerte ouvre l’annonce sur Vinted.</li>
  </ol>
  <p>SNYPD ne demande jamais tes identifiants Vinted. Le plan gratuit fait tourner une recherche 24h/24 pendant les @@trial_days@@ premiers jours, puis tant que ton tableau de bord est ouvert ; les plans payants, à partir de @@price:solo@@ par mois, vérifient 24h/24. Plus de détails : <a href="{SLUGS['bot']['fr']}">SNYPD, le bot d’alertes Vinted</a>.</p>
  {figure('feed', 'fr')}
</section>
{push_setup('fr')}
<section id="essayer">
  <h2>Essaie sur une recherche</h2>
  {cta('fr')}
</section>"""
    return page('notify', 'fr', 'Alerte Vinted : être prévenu des nouvelles annonces | SNYPD',
                'Les recherches sauvegardées Vinted affichent un compteur +N, pas une alerte. Ce que dit Vinted, et comment être notifié de chaque nouvelle annonce.',
                'ALERTES VINTED', 'Être prévenu dès qu’une nouvelle annonce Vinted correspond à ta recherche',
                'Vinted permet de sauvegarder des recherches, mais ne documente aucune notification pour les nouvelles annonces. Voici exactement ce que dit le centre d’aide de Vinted, et comment recevoir une alerte sur ton téléphone pour chaque nouvelle annonce qui correspond.',
                [('reponse', 'Réponse courte'), ('vinted', 'Ce que fait Vinted'), ('ways', 'Toutes les façons'), ('suffisant', 'Quand ça suffit'), ('alertes', 'De vraies alertes'), ('push', 'Activer le push')],
                body)


# ------------------------------------------------------------------ page: comparison
# Why SNYPD, then the side-by-side table. Every competitor fact is from that
# vendor's own homepage on COMPARE_CHECKED and is linked from its row.
# EU comparative-advertising rules (Directive 2006/114/EC; Belgian Code of
# Economic Law VI.17) allow naming competitors only when each comparison is
# objective, verifiable and not misleading: keep every claim checkable, write
# "not stated" (never "no") when a site is silent, and re-check before changing
# the date. Tanush chose the eight reasons on 2026-10-01; none use testimonials
# because none exist yet.
# COMPARE_CHECKED, COMPETITORS, YES, HELP435/HELP433: ops/seo/compare_data.py (six languages).
COMPARE_CSS = r"""
.rs-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 0 0 18px; }
@media (max-width: 759.98px) { .rs-grid { grid-template-columns: minmax(0, 1fr); } }
.rs-card { border: 1px solid #1D1D20; background: #0C0C0D; padding: 18px 18px 16px; display: flex; flex-direction: column; gap: 9px; min-width: 0; }
.rs-card:first-child, .rs-card:nth-child(2) { border-color: rgba(0,229,160,.38); background: rgba(0,229,160,.05); }
.rs-num { font-size: 11px; letter-spacing: .14em; color: #00E5A0; }
.lg-doc .rs-title { margin: 0; font-family: 'Cabinet Grotesk', 'DM Mono', sans-serif; font-weight: 900; font-size: 21px; line-height: 1.08; letter-spacing: -.02em; color: #FFFFFF; }
.lg-doc .rs-card p { margin: 0; font-size: 12.5px; line-height: 1.7; }
.lg-doc .rs-card p.rs-proof { padding-top: 9px; border-top: 1px dashed #26262A; font-size: 11.5px; color: #8B9094; }
.rs-proof a { color: #00E5A0; }
.ct-yes { color: #00E5A0; }
.ct-table tbody tr.ct-us th, .ct-table tbody tr.ct-us td { color: #FFFFFF; border-top-color: rgba(0,229,160,.45); }
.ct-table tbody tr.ct-us th { box-shadow: inset 3px 0 0 #00E5A0; }
.ct-badge { display: inline-block; margin-left: 6px; padding: 2px 6px; font-size: 10px; letter-spacing: .1em; color: #0A0A0B; background: #00E5A0; vertical-align: 1px; }
.ct-table tbody th[scope="row"] { position: sticky; left: 0; z-index: 1; background: #0C0C0D; }
.ct-table thead th:first-child { position: sticky; left: 0; z-index: 2; background: #121214; }
.ct-table tbody tr.ct-us th[scope="row"] { background: #160C20; }
@media (max-width: 699.98px) { .ct-table tbody th { min-width: 118px; } }
.glance { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 0; padding: 0; list-style: none; }
.glance li { font-size: 12px; letter-spacing: .04em; color: #FFFFFF; border: 1px solid rgba(0,229,160,.38); background: rgba(0,229,160,.06); padding: 8px 11px; }
.glance li span { color: #00E5A0; margin-right: 6px; }
.fit-list { list-style: none; padding: 0 !important; margin: 0 0 18px !important; display: flex; flex-direction: column; gap: 10px; }
.fit-list li { margin: 0 !important; padding: 12px 14px; border: 1px solid #1D1D20; background: #0C0C0D; }
.fit-list li strong { display: block; margin-bottom: 3px; }
.fit-list li.fit-yes { border-color: rgba(0,229,160,.38); }
.lg-fig { margin: 4px 0 20px; border: 1px solid #1D1D20; background: #0C0C0D; }
.lg-fig picture { display: block; }
.lg-fig img { display: block; width: 100%; height: auto; }
.lg-fig figcaption { padding: 10px 14px; border-top: 1px solid #1D1D20; font-size: 11.5px; line-height: 1.6; color: #8B9094; }
.lg-fig.fig-narrow { max-width: 520px; }
.fig-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; align-items: start; margin: 0 0 18px; }
.fig-row .lg-fig { margin: 0; max-width: none; }
@media (max-width: 759.98px) { .fig-row { grid-template-columns: minmax(0, 1fr); } }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }
.ct-duel { margin: 0 0 18px; }
.ct-duel label { display: flex; flex-direction: column; gap: 8px; margin: 0 0 10px; font-size: 11px; letter-spacing: .12em; color: #8B9094; }
.ct-duel select { font-family: inherit; font-size: 14px; color: #FFFFFF; background: #141416; border: 1px solid #3A3A40; border-radius: 0; padding: 0 12px; min-height: 46px; }
.ct-duel table { width: 100%; border-collapse: collapse; table-layout: fixed; border: 1px solid #1D1D20; }
.ct-duel th, .ct-duel td { text-align: left; vertical-align: top; padding: 11px 10px; border-top: 1px solid #1D1D20; font-size: 12px; line-height: 1.5; color: #B8BCBF; overflow-wrap: anywhere; }
.ct-duel thead th { border-top: 0; background: #121214; font-size: 11px; font-weight: 400; letter-spacing: .08em; color: #8B9094; }
.ct-duel thead th.d-us { color: #FFFFFF; }
.ct-duel tbody th { width: 28%; font-weight: 400; font-size: 11px; letter-spacing: .06em; color: #8B9094; }
.ct-duel td.d-us { color: #FFFFFF; background: rgba(162,0,255,.07); }
.ct-duel [data-t] { display: none; }
.ct-duel [data-t].on { display: table-cell; }
@media (min-width: 700px) { .ct-duel { display: none; } }
@media (max-width: 699.98px) { .ct-full { display: none; } }
.fc { border: 1px solid rgba(0,229,160,.38); background: rgba(0,229,160,.05); padding: 18px; margin: 0 0 18px; display: flex; flex-direction: column; gap: 14px; }
.fc-in { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12px; }
@media (max-width: 559.98px) { .fc-in { grid-template-columns: minmax(0, 1fr); } }
.fc label { display: flex; flex-direction: column; gap: 8px; font-size: 11px; letter-spacing: .12em; color: #8B9094; }
.fc input, .fc select { font-family: inherit; font-size: 16px; color: #FFFFFF; background: #141416; border: 1px solid #3A3A40; border-radius: 0; padding: 0 12px; min-height: 48px; width: 100%; box-sizing: border-box; }
.fc input:focus-visible, .fc select:focus-visible { outline: 2px solid #00E5A0; outline-offset: 1px; }
.fc-out { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; background: #1D1D20; border: 1px solid #1D1D20; margin: 0; }
.fc-out div { background: #0C0C0D; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px; }
.fc-out dt { font-size: 11px; letter-spacing: .1em; color: #8B9094; }
.fc-out dd { margin: 0; font-size: 18px; color: #FFFFFF; }
.fc-out div.fc-total dd { color: #00E5A0; }
"""

# Real screenshots of the live SNYPD dashboard, taken 2 October 2026 in a signed-in session.
# Listing photos belong to Vinted sellers and are blurred; nothing else is edited. Files: assets/seo/.
# Phones get their own capture (one card / the panel at phone width), because the desktop
# capture scaled to ~350px makes its text about 7px tall.
SHOTS = {
    'feed':   ('/assets/seo/snypd-feed.webp', 1400, 662, ('/assets/seo/snypd-feed-phone.webp', 396, 650), ''),
    'market': ('/assets/seo/snypd-market-report.webp', 781, 665, ('/assets/seo/snypd-market-report-phone.webp', 358, 653), ' fig-narrow'),
    'hunts':  ('/assets/seo/snypd-hunts.webp', 635, 674, ('/assets/seo/snypd-hunts-phone.webp', 350, 537), ' fig-narrow'),
}
SHOT_TEXT = {
    'en': {
        'feed': ('SNYPD dashboard feed showing new Vinted listings with price, price including Buyer Protection, condition and the time found',
                 'SNYPD&rsquo;s feed during a real session on 2 October 2026: new listings from one search, each with its price, the price including Vinted&rsquo;s Buyer Protection, its condition and when it was found. Photos are blurred because they belong to the sellers.'),
        'market': ('SNYPD Market Report for jordan 1 mid: typical asking price 45 euros from 975 listings, broken down by condition',
                   'A real Market Report for &ldquo;jordan 1 mid&rdquo; on 2 October 2026: a typical asking price of &euro;45 from 975 listings by 880 sellers, then the price for each condition.'),
        'hunts': ('List of SNYPD hunts, each a Vinted search on vinted.be, some live and some paused',
                  'Hunts in SNYPD: each one is a Vinted search link with its own filters, either live or paused. Screenshot from 2 October 2026.'),
    },
    'fr': {
        'feed': ('Flux du tableau de bord SNYPD avec de nouvelles annonces Vinted : prix, prix avec protection acheteurs, état et moment de la détection',
                 'Le flux SNYPD pendant une vraie session, le 2 octobre 2026 : de nouvelles annonces d’une même recherche, avec leur prix, le prix protection acheteurs de Vinted incluse, leur état et le moment où elles ont été trouvées. Photos floutées, car elles appartiennent aux vendeurs. Interface en anglais.'),
        'market': ('Market Report SNYPD pour jordan 1 mid : prix demandé typique de 45 euros sur 975 annonces, détaillé par état',
                   'Un vrai Market Report pour « jordan 1 mid », le 2 octobre 2026 : un prix demandé typique de 45 &euro; sur 975 annonces de 880 vendeurs, puis le prix pour chaque état. Interface en anglais.'),
        'hunts': ('Liste des recherches SNYPD, chacune une recherche Vinted sur vinted.be, certaines actives et d’autres en pause',
                  'Les recherches dans SNYPD : chacune est un lien de recherche Vinted avec ses propres filtres, active ou en pause. Capture du 2 octobre 2026, interface en anglais.'),
    },
    'de': {
        'feed': ('SNYPD-Dashboard mit neuen Vinted-Anzeigen: Preis, Preis mit Käuferschutz, Zustand und Fundzeit',
                 'Der SNYPD-Feed in einer echten Sitzung am 2. Oktober 2026: neue Anzeigen aus einer Suche, jeweils mit Preis, Preis inklusive Vinted-Käuferschutz, Zustand und Fundzeit. Die Fotos sind unscharf, weil sie den Verkäufern gehören. Oberfläche auf Englisch.'),
    },
    'nl': {
        'feed': ('SNYPD-dashboard met nieuwe Vinted-advertenties: prijs, prijs met kopersbescherming, staat en tijdstip van vinden',
                 'De SNYPD-feed tijdens een echte sessie op 2 oktober 2026: nieuwe advertenties uit één zoekopdracht, elk met prijs, prijs inclusief de kopersbescherming van Vinted, staat en tijdstip van vinden. De foto&rsquo;s zijn vervaagd omdat ze van de verkopers zijn. Interface in het Engels.'),
    },
    'it': {
        'feed': ('Dashboard SNYPD con nuovi annunci Vinted: prezzo, prezzo con Protezione acquisti, condizioni e ora del ritrovamento',
                 'Il feed di SNYPD in una sessione reale del 2 ottobre 2026: nuovi annunci di una ricerca, ognuno con prezzo, prezzo comprensivo della Protezione acquisti di Vinted, condizioni e ora in cui è stato trovato. Le foto sono sfocate perché appartengono ai venditori. Interfaccia in inglese.'),
    },
    'es': {
        'feed': ('Panel de SNYPD con anuncios nuevos de Vinted: precio, precio con Protección al comprador, estado y hora en que se encontró',
                 'El feed de SNYPD en una sesión real el 2 de octubre de 2026: anuncios nuevos de una búsqueda, cada uno con su precio, el precio con la Protección al comprador de Vinted incluida, su estado y cuándo se encontró. Las fotos están difuminadas porque pertenecen a los vendedores. Interfaz en inglés.'),
    },
}


def figure(key, lang):
    src, w, h, (psrc, pw, ph), extra = SHOTS[key]
    alt, cap = SHOT_TEXT[lang][key]
    return ('<figure class="lg-fig%s"><picture><source media="(max-width: 699.98px)" srcset="%s" width="%d" height="%d">'
            '<img src="%s" alt="%s" width="%d" height="%d" loading="lazy" decoding="async"></picture><figcaption>%s</figcaption></figure>'
            % (extra, psrc, pw, ph, src, esc(alt), w, h, cap))


# One row per tool, cells per language: (en, fr). Order: tool, type, price data,
# account, alerts arrive, refund, per month, free option.
def compare_table(lang):
    head = cd.HEAD[lang]
    rows, us = [], None
    for i, c in enumerate(COMPETITORS):
        url = c['url'] or HELP435[lang]
        label = '<a href="%s"%s>%s</a>' % (url, '' if c.get('us') else ' rel="nofollow noopener"', cd.name(c, lang))
        if c.get('us'):
            label += '<span class="ct-badge">%s</span>' % cd.US_BADGE[lang]
            us = i
        rows.append([label] + [cell[lang] for cell in c['cells']])
    return '<div class="ct-full">%s</div>' % table(head, rows, us_row=us)


DUEL_LABEL = {'en': ('COMPARE SNYPD WITH', 'SNYPD compared with the tool you pick', 'Point'),
              'fr': ('COMPARER SNYPD AVEC', 'SNYPD comparé à l’outil choisi', 'Critère'),
              'de': ('SNYPD VERGLEICHEN MIT', 'SNYPD im Vergleich mit dem gewählten Tool', 'Punkt'),
              'nl': ('SNYPD VERGELIJKEN MET', 'SNYPD vergeleken met de gekozen tool', 'Punt'),
              'it': ('CONFRONTA SNYPD CON', 'SNYPD confrontato con lo strumento scelto', 'Voce'),
              'es': ('COMPARAR SNYPD CON', 'SNYPD comparado con la herramienta elegida', 'Punto')}


def compare_duel(lang):
    # Phones get SNYPD next to ONE other tool at a time (NN/g: at most 2 options side by side
    # on small screens). Same cells as the full table; the full table is hidden below 700px.
    us, others = COMPETITORS[0], COMPETITORS[1:]
    label, cap, point = DUEL_LABEL[lang]
    opts = ''.join('<option value="%d"%s>%s</option>' % (i, ' selected' if i == 0 else '', cd.name(c, lang)) for i, c in enumerate(others))
    heads = ''.join('<th scope="col" data-t="%d"%s><a href="%s" rel="nofollow noopener">%s</a></th>'
                    % (i, ' class="on"' if i == 0 else '', c['url'] or HELP435[lang], cd.name(c, lang)) for i, c in enumerate(others))
    body = ''
    for j, h in enumerate(cd.HEAD[lang][1:]):
        cells = ''.join('<td data-t="%d"%s>%s</td>' % (i, ' class="on"' if i == 0 else '', c['cells'][j][lang]) for i, c in enumerate(others))
        body += '<tr><th scope="row">%s</th><td class="d-us">%s</td>%s</tr>' % (h, us['cells'][j][lang], cells)
    js = ("<script>(function(){var s=document.getElementById('duel-pick');if(!s)return;"
          "function on(){var v=s.value;var c=document.querySelectorAll('.ct-duel [data-t]');"
          "for(var i=0;i<c.length;i++){c[i].className=c[i].getAttribute('data-t')===v?'on':'';}}"
          "s.addEventListener('change',on);on();})();</script>")
    return ('<div class="ct-duel"><label for="duel-pick">%s<select id="duel-pick">%s</select></label>'
            '<table><caption class="sr-only">%s</caption><thead><tr><th scope="col"><span class="sr-only">%s</span></th>'
            '<th scope="col" class="d-us">SNYPD</th>%s</tr></thead><tbody>%s</tbody></table></div>%s'
            % (label, opts, cap, point, heads, body, js))


def compare_itemlist(lang):
    """ItemList of the tools in the table, in table order (names + their own pages). No ratings."""
    return {'@context': 'https://schema.org', '@type': 'ItemList', 'name': cd.HEAD[lang][0],
            'numberOfItems': len(COMPETITORS) - 1,
            'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': cd.name(c, lang), 'url': c['url']}
                                for i, c in enumerate(x for x in COMPETITORS if x['url'])]}


def reasons(lang):
    if lang == 'en':
        R = [
            ('Price data is built in',
             'Pro (@@price:pro@@ a month) includes the Market Report: type an item and see its typical Vinted asking price, split by condition. It shows no price at all when the data is too thin or too mixed to trust.',
             'Some tools here show a price figure too: CopMarket a &ldquo;cote&rdquo; (the median of recent comparable listings), VintageLab a free price check, DealFindr market trends, Resell Reserve AI estimates on its &pound;44.99 plan. See SNYPD&rsquo;s numbers in the <a href="/vinted-price-guide">Vinted price guide</a>.'),
            ('Your Vinted account stays yours',
             'SNYPD needs an email address and nothing else: no Vinted password, no login, no browser extension. It never buys and never messages sellers. You buy through Vinted&rsquo;s normal checkout.',
             'Autobuy needs your account: Souk&rsquo;s docs say &ldquo;To use Autobuy, first link your Vinted account&rdquo;, VINTI asks you to sign in to your Vinted account, and V-Tools&rsquo; plans come with connected Vinted accounts. V-Tools&rsquo; own FAQ on bans: &ldquo;No tool can guarantee zero risk.&rdquo;'),
            ('Alerts land on your phone',
             'Push notifications go straight to your phone or computer. No Telegram, no Discord server, no extra account. Several finds close together arrive as one notification, not a buzz each.',
             'Telvin alerts only inside Telegram; Resell Reserve, Resell Vault, Monitorius and VintageLab in Discord. On iPhone, add SNYPD to your Home Screen once: Apple only allows web push for Home Screen apps.'),
            ('Every Vinted filter you set',
             'Paste a Vinted search link and SNYPD keeps every filter in it: brand, size, price, condition, colour, material, category. If you can filter it on Vinted, SNYPD keeps that filter.',
             'Souk builds alerts from its own form (brand, category, size, keywords, price). SNYPD works on %s: 26 sites, each in its own currency.' % MARKETS_TEXT['en']),
            ('14 days to change your mind',
             'Not happy with a paid plan? Email within 14 days of your first payment and you get it back in full. Prices include VAT, plans run month to month, cancel any time.',
             'Souk&rsquo;s site states one week. Resell Reserve&rsquo;s refund policy says payments are &ldquo;generally non-refundable&rdquo;, with a conditional first-month guarantee on its Core plan; VINTI refunds nothing once the account is activated.'),
            ('Your finds, tracked to the profit',
             'Claim an item you bought and SNYPD keeps it in History: Holding, then Sold, with your realised profit added up for you. No spreadsheet next to your bot.',
             'Part of the SNYPD dashboard. Matches also carry a NEW badge and a DROP badge when the price fell since SNYPD first saw it.'),
            ('Made by a reseller',
             'SNYPD is built by a Belgian sneaker reseller with 150+ sales and 3.8k Instagram followers, and run in the open with resellers in its Discord.',
             'Questions go to a person: <a href="mailto:%s">%s</a> or the <a href="%s">Discord</a>.' % (EMAIL, EMAIL, DISCORD)),
            ('A founding price, for life',
             'The first 100 accounts, free accounts included, keep Pro at @@founding_price@@ a month for life.',
             'The number of places left is counted live on the <a href="/">homepage</a>.'),
        ]
    else:
        R = [
            ('Les données de prix sont incluses',
             'Pro (@@price:pro@@ par mois) inclut le Market Report : tape un article et vois son prix demandé typique sur Vinted, détaillé par état. Il n’affiche aucun prix quand les données sont trop maigres ou trop mélangées pour être fiables.',
             'D’autres outils ici affichent aussi un prix : CopMarket une « cote » (la médiane d’annonces récentes comparables), VintageLab une vérification de prix gratuite, DealFindr des tendances du marché, Resell Reserve des estimations IA sur son plan à 44,99&nbsp;&pound;. Les chiffres de SNYPD : <a href="/fr/guide-prix-vinted">Guide des prix Vinted</a>.'),
            ('Ton compte Vinted reste à toi',
             'SNYPD a besoin d’une adresse e-mail, rien d’autre : pas de mot de passe Vinted, pas de connexion, pas d’extension. Il n’achète jamais et n’écrit jamais aux vendeurs. Tu achètes avec le paiement normal de Vinted.',
             'L’achat automatique passe par ton compte : la doc de Souk dit « To use Autobuy, first link your Vinted account », VINTI te demande de te connecter à ton compte Vinted, et les plans de V-Tools incluent des comptes Vinted connectés. La FAQ de V-Tools sur les bannissements : « No tool can guarantee zero risk ».'),
            ('Les alertes arrivent sur ton téléphone',
             'Les notifications push arrivent directement sur ton téléphone ou ton ordinateur. Pas de Telegram, pas de serveur Discord, pas de compte en plus. Plusieurs trouvailles rapprochées arrivent en une seule notification.',
             'Telvin alerte uniquement dans Telegram ; Resell Reserve, Resell Vault, Monitorius et VintageLab dans Discord. Sur iPhone, ajoute SNYPD à ton écran d’accueil une fois : Apple n’autorise les notifications web que pour les apps de l’écran d’accueil.'),
            ('Chaque filtre Vinted que tu règles',
             'Colle un lien de recherche Vinted et SNYPD garde tous ses filtres : marque, taille, prix, état, couleur, matière, catégorie. Si tu peux le filtrer sur Vinted, SNYPD garde ce filtre.',
             'Souk crée les alertes depuis son propre formulaire (marque, catégorie, taille, mots-clés, prix). SNYPD fonctionne sur %s : 26 sites, chacun dans sa devise.' % MARKETS_TEXT['fr']),
            ('14 jours pour changer d’avis',
             'Pas convaincu par un plan payant ? Écris dans les 14 jours suivant ton premier paiement et tu es remboursé en totalité. Prix TVA incluse, plans au mois, résiliables à tout moment.',
             'Le site de Souk indique une semaine. La politique de Resell Reserve indique que les paiements sont « generally non-refundable », avec une garantie conditionnelle le premier mois sur son plan Core ; VINTI ne rembourse rien une fois le compte activé.'),
            ('Tes trouvailles, suivies jusqu’au bénéfice',
             'Marque un article acheté et SNYPD le garde dans History : Holding, puis Sold, avec ton bénéfice réalisé calculé pour toi. Plus besoin d’un tableur à côté de ton bot.',
             'Inclus dans le tableau de bord SNYPD. Les annonces portent aussi un badge NEW et un badge DROP quand le prix a baissé depuis que SNYPD l’a vue.'),
            ('Créé par un revendeur',
             'SNYPD est créé par un revendeur de sneakers belge, avec plus de 150 ventes et 3,8k abonnés Instagram, et développé au grand jour avec des revendeurs sur son Discord.',
             'Tes questions arrivent à une vraie personne : <a href="mailto:%s">%s</a> ou le <a href="%s">Discord</a>.' % (EMAIL, EMAIL, DISCORD)),
            ('Un prix fondateur, à vie',
             'Les 100 premiers comptes, gratuits compris, gardent Pro à @@founding_price@@ par mois à vie.',
             'Le nombre de places restantes est affiché en direct sur la <a href="/">page d’accueil</a>.'),
        ]
    cards = ''.join('<div class="rs-card"><span class="rs-num">%02d</span><h3 class="rs-title">%s</h3><p>%s</p><p class="rs-proof">%s</p></div>' % (i + 1, t, b, p)
                    for i, (t, b, p) in enumerate(R))
    return '<div class="rs-grid">%s</div>' % cards


COMPARE_FAQ = {
    'en': [
        ('What is a Vinted monitor?',
         'A tool that keeps checking a Vinted search for you and alerts you when a new listing matches it. A monitor does not buy: you open the listing and decide. All the tools on this page monitor searches; Souk, V-Tools, Resell Reserve, Resell Vault, VINTI, VintageLab and CopMarket (Pro) also sell autobuy. More in <a href="%s">what is a Vinted monitor?</a>' % SLUGS['monitor']['en']),
        ('Are Vinted bots worth it?',
         'For resellers who buy in a narrow niche, often. Vinted&rsquo;s own saved searches show a &ldquo;+N&rdquo; counter the next time you open the app, but they do not notify you about each new match, so a well-priced listing can be gone before you look. If you only buy now and then for yourself, saved searches may be enough. Try a free plan before paying: SNYPD, Telvin, Crazed and MarktAlert all list one.'),
        ('Can a Vinted bot get my account banned?',
         'Vinted&rsquo;s terms prohibit bots and scraping programs, so no tool can promise there is no risk. V-Tools&rsquo; own FAQ says: &ldquo;No tool can guarantee zero risk.&rdquo; What differs is what happens on your account: autobuy tools act through your logged-in Vinted account, while SNYPD never signs in as you, so nothing it does happens on your account.'),
        ('Is there a free Vinted bot?',
         'Yes, with limits. According to each tool&rsquo;s own site, checked on %s: SNYPD Free runs 1 search with no time limit, 24/7 for the first @@trial_days@@ days and then while your dashboard is open; Vinotify&rsquo;s free plan checks 1 search once a day; Telvin&rsquo;s free plan covers 1 keyword alert and 100 notifications; Crazed is free with 3 alerts and 30 items a day; MarktAlert&rsquo;s free plan has 2 alerts checked every 15 minutes; DealFindr&rsquo;s has 3 searches checked hourly, with alerts 30 minutes late. InstantAlert, Monitorius and CopMarket offer short trials. Open-source scripts such as Vinted Scanner are free if you run them yourself.' % COMPARE_CHECKED['en']),
        ('Which Vinted bot is the fastest?',
         'There is no fair way to say. Each vendor measures its own speed in its own way (see <a href="#speed">what about speed?</a>). SNYPD checks each search about every 30 seconds on every plan, and keeps paid searches running 24/7. ' + SPEED_MEASURED['en'] + ''),
    ],
    'fr': [
        ('Qu’est-ce qu’un monitor Vinted\xa0?',
         'Un outil qui vérifie une recherche Vinted à ta place et t’alerte quand une nouvelle annonce correspond. Un monitor n’achète pas\xa0: tu ouvres l’annonce et tu décides. Tous les outils de cette page surveillent des recherches\xa0; Souk, V-Tools, Resell Reserve, Resell Vault, VINTI, VintageLab et CopMarket (Pro) vendent aussi de l’achat automatique. Plus de détails\xa0: <a href="%s">qu’est-ce qu’un monitor Vinted\xa0?</a>' % SLUGS['monitor']['fr']),
        ('Un bot Vinted, ça vaut le coup\xa0?',
         'Pour un revendeur qui achète dans une niche précise, souvent oui. Les recherches sauvegardées de Vinted affichent un compteur «\xa0+N\xa0» à ta prochaine visite dans l’app, mais ne te notifient pas pour chaque nouvelle annonce\xa0: une annonce bien placée peut partir avant que tu regardes. Si tu achètes de temps en temps pour toi, les recherches sauvegardées peuvent suffire. Essaie un plan gratuit avant de payer\xa0: SNYPD, Telvin, Crazed et MarktAlert en proposent un.'),
        ('Un bot Vinted peut-il faire bannir mon compte\xa0?',
         'Les conditions de Vinted interdisent les bots et les programmes de scraping, donc aucun outil ne peut promettre zéro risque. La FAQ de V-Tools le dit elle-même\xa0: «\xa0No tool can guarantee zero risk\xa0». Ce qui change, c’est ce qui se passe sur ton compte\xa0: les outils d’achat automatique agissent via ton compte Vinted connecté, alors que SNYPD ne se connecte jamais à ta place, donc rien de ce qu’il fait ne se passe sur ton compte.'),
        ('Existe-t-il un bot Vinted gratuit\xa0?',
         'Oui, avec des limites. D’après le site de chaque outil, vérifié le %s\xa0: SNYPD Free fait tourner 1 recherche sans limite de durée, 24h/24 pendant les @@trial_days@@ premiers jours puis tant que ton tableau de bord est ouvert\xa0; le plan gratuit de Vinotify vérifie 1 recherche une fois par jour\xa0; celui de Telvin couvre 1 alerte mot-clé et 100 notifications\xa0; Crazed est gratuit avec 3 alertes et 30 articles par jour\xa0; le plan gratuit de MarktAlert a 2 alertes vérifiées toutes les 15 minutes\xa0; celui de DealFindr 3 recherches vérifiées toutes les heures, avec 30 minutes de retard. InstantAlert, Monitorius et CopMarket proposent des essais courts. Les scripts open source comme Vinted Scanner sont gratuits si tu les fais tourner toi-même.' % COMPARE_CHECKED['fr']),
        ('Quel est le bot Vinted le plus rapide\xa0?',
         'Impossible de le dire honnêtement. Chaque éditeur mesure sa vitesse à sa façon (voir <a href="#vitesse">et la vitesse\xa0?</a>). SNYPD vérifie chaque recherche environ toutes les 30 secondes sur tous les plans, et les recherches payantes tournent 24h/24. ' + SPEED_MEASURED['fr'] + ''),
    ],
}


def page_compare(lang):
    tbl = compare_table(lang)
    faq = COMPARE_FAQ[lang]
    if lang == 'en':
        body = f"""
<section id="disclosure">
  <div class="lg-box lg-mint"><p><strong>We make SNYPD, so we&rsquo;re not neutral.</strong> Every fact about another tool on this page comes from that tool&rsquo;s own website, checked on {COMPARE_CHECKED['en']}, and is linked in the table. Prices change: check before you pay. Spotted something out of date? Email <a href="mailto:{EMAIL}">{EMAIL}</a> and it gets fixed.</p></div>
</section>
<section id="reasons">
  <h2>8 reasons resellers choose SNYPD</h2>
  {reasons('en')}
  <div class="fig-row">{figure('market', 'en')}{figure('hunts', 'en')}</div>
</section>
<section id="table">
  <h2>SNYPD and {cd.others_count()} other Vinted tools, side by side</h2>
  {tbl}
  {compare_duel('en')}
  <p class="ct-note">Buying on Vinted needs a logged-in account, so any autobuy feature acts through yours. &ldquo;Not stated&rdquo;, &ldquo;not on its site&rdquo; and &ldquo;not on its homepage&rdquo; mean we couldn&rsquo;t find it on that tool&rsquo;s public pages, not proof it doesn&rsquo;t exist. Vinted Scanner is a free open-source script you run yourself, not a service.</p>
</section>
<section id="others">
  <h2>What other tools do better</h2>
  <p>No tool is best at everything. Three things other Vinted bots offer that SNYPD does not, from each tool&rsquo;s own site:</p>
  <ul class="fit-list">
    <li><strong>They can buy for you.</strong>Souk, V-Tools, Resell Reserve, Resell Vault, VINTI, VintageLab and CopMarket (Pro) sell autobuy. Buying on Vinted needs a logged-in account, so those features act through yours. SNYPD never signs in as you, so every purchase stays your decision, made on Vinted.</li>
    <li><strong>They alert you in Telegram, Discord or their own app.</strong>Telvin sends alerts in Telegram; Resell Reserve, Resell Vault, Monitorius and VintageLab in Discord; InstantAlert, Vinotify and DealFindr in their own apps; MarktAlert by Telegram, email or webhooks. SNYPD sends push notifications to your phone or computer only: nothing to install, but no Telegram or Discord option.</li>
    <li><strong>Their first paid plan costs less.</strong>Vinotify starts at &euro;2.99 a month, Telvin at &euro;4.90, InstantAlert and DealFindr at &euro;4.99. SNYPD&rsquo;s first paid plan, Solo, is @@price:solo@@ and watches 1 search 24/7; the Market Report starts with Pro at @@price:pro@@. Without a subscription, the Hunt Pass is @@price:pass@@ once for 1 search over @@pass_days@@ days.</li>
  </ul>
</section>
<section id="speed">
  <h2>What about speed?</h2>
  <p>Telvin advertises alerts in 750 ms on its paid plans, Resell Reserve detection in under 0.15 s, Resell Vault &ldquo;0.14ms&rdquo;, V-Tools detection &ldquo;in a few milliseconds&rdquo;, Bot Vinted &ldquo;2,2 secondes&rdquo;, InstantAlert &ldquo;within 60 seconds&rdquo;, DealFindr a check every 5 to 60 minutes depending on the plan, and Crazed &ldquo;temps r&eacute;el&rdquo; (real time). Those are each vendor&rsquo;s own figures, measured in their own way, so they can&rsquo;t be compared with each other, or with SNYPD.</p>
  <p>SNYPD checks each search about every 30 seconds, slowing to at most 5 minutes on searches that go quiet, and the same on every plan. {SPEED_MEASURED['en']} {VINTED_LAG['en']} What it adds is reach: paid searches keep running 24/7 with your laptop closed, and the alert finds you on your phone wherever you are.</p>
</section>
<section id="fit">
  <h2>Is SNYPD right for you?</h2>
  <ul class="fit-list">
    <li class="fit-yes"><strong>Yes, if you want to judge every deal yourself.</strong>You see the listing first, check it against real Vinted price data, and buy it on Vinted without handing over your account.</li>
    <li><strong>Not if you want a bot to buy for you.</strong>Automatic buying needs a tool that operates your Vinted account, such as Souk, V-Tools, Resell Reserve, Resell Vault or VINTI.</li>
    <li><strong>Also buying on Marktplaats or 2dehands?</strong>MarktAlert covers both, DealFindr covers Marktplaats. SNYPD is Vinted only.</li>
  </ul>
</section>
<section id="faq">
  <h2>Questions about Vinted bots</h2>
  {faq_html(faq)}
</section>
<section id="start">
  <h2>Try it on one search</h2>
  {cta('en')}
</section>"""
        return page('compare', 'en', 'Best Vinted Bot & Monitor 2026: %d Tools Compared | SNYPD' % (cd.others_count() + 1),
                    'SNYPD vs %d Vinted bots and alert apps (Souk, Telvin, V-Tools, InstantAlert, Vinotify, VINTI, Resell Vault and more): price data, account, alerts, refunds, from each tool’s own site.' % cd.others_count(),
                    'VINTED BOTS &amp; MONITORS COMPARED &middot; CHECKED ' + COMPARE_CHECKED_SHORT['en'], 'Best Vinted bots and monitors in 2026: SNYPD and %d others compared' % cd.others_count(),
                    'SNYPD alerts you to new Vinted listings, shows the typical Vinted asking price of what you&rsquo;re looking at, and never touches your Vinted account. Here is how that compares with %d other Vinted tools, point by point, with the source for every fact.' % cd.others_count(),
                    None, body, [faq_ld(faq), compare_itemlist('en')], head_extra='<ul class="glance" aria-label="SNYPD at a glance"><li><span>&#10003;</span>Price data included</li><li><span>&#10003;</span>No Vinted login, ever</li><li><span>&#10003;</span>Alerts on your phone</li><li><span>&#10003;</span>14-day refund</li></ul>')
    body = f"""
<section id="transparence">
  <div class="lg-box lg-mint"><p><strong>SNYPD est notre outil, donc cette page n’est pas neutre.</strong> Chaque information sur un autre outil vient du site de cet outil, vérifié le {COMPARE_CHECKED['fr']}, avec un lien dans le tableau. Les prix changent : vérifie avant de payer. Une info n’est plus à jour ? Écris à <a href="mailto:{EMAIL}">{EMAIL}</a> et elle sera corrigée.</p></div>
</section>
<section id="raisons">
  <h2>8 raisons de choisir SNYPD</h2>
  {reasons('fr')}
  <div class="fig-row">{figure('market', 'fr')}{figure('hunts', 'fr')}</div>
</section>
<section id="tableau">
  <h2>SNYPD et {cd.others_count()} autres outils Vinted, côte à côte</h2>
  {tbl}
  {compare_duel('fr')}
  <p class="ct-note">Acheter sur Vinted demande un compte connecté, donc toute fonction d’achat automatique passe par le tien. « Non précisé », « absent de son site » et « absent de sa page d’accueil » veulent dire que nous ne l’avons pas trouvé sur les pages publiques de l’outil, pas que cela n’existe pas. Vinted Scanner est un script open source gratuit à faire tourner toi-même, pas un service.</p>
</section>
<section id="autres">
  <h2>Ce que d’autres outils font mieux</h2>
  <p>Aucun outil n’est le meilleur en tout. Trois choses que d’autres bots Vinted proposent et pas SNYPD, d’après le site de chaque outil :</p>
  <ul class="fit-list">
    <li><strong>Ils peuvent acheter à ta place.</strong>Souk, V-Tools, Resell Reserve, Resell Vault, VINTI, VintageLab et CopMarket (Pro) vendent de l’achat automatique. Acheter sur Vinted demande un compte connecté, donc ces fonctions passent par le tien. SNYPD ne se connecte jamais à ta place : chaque achat reste ta décision, sur Vinted.</li>
    <li><strong>Ils alertent dans Telegram, Discord ou leur propre app.</strong>Telvin alerte dans Telegram ; Resell Reserve, Resell Vault, Monitorius et VintageLab dans Discord ; InstantAlert, Vinotify et DealFindr dans leur app ; MarktAlert par Telegram, e-mail ou webhooks. SNYPD envoie uniquement des notifications push sur ton téléphone ou ton ordinateur : rien à installer, mais pas d’option Telegram ou Discord.</li>
    <li><strong>Leur premier plan payant coûte moins cher.</strong>Vinotify commence à 2,99&nbsp;&euro; par mois, Telvin à 4,90&nbsp;&euro;, InstantAlert et DealFindr à 4,99&nbsp;&euro;. Le premier plan payant de SNYPD, Solo, coûte @@price:solo@@ et surveille 1 recherche 24h/24 ; le Market Report commence avec Pro à @@price:pro@@. Sans abonnement, le Pass 30 jours coûte @@price:pass@@ en une fois pour 1 recherche pendant @@pass_days@@ jours.</li>
  </ul>
</section>
<section id="vitesse">
  <h2>Et la vitesse ?</h2>
  <p>Telvin annonce des alertes en 750 ms sur ses plans payants, Resell Reserve une détection en moins de 0,15 s, Resell Vault « 0.14ms », V-Tools une détection « in a few milliseconds », Bot Vinted « 2,2 secondes », InstantAlert « within 60 seconds », DealFindr une vérification toutes les 5 à 60 minutes selon le plan, et Crazed du « temps réel ». Ce sont les chiffres de chaque éditeur, mesurés à sa façon, donc impossibles à comparer entre eux ou avec SNYPD.</p>
  <p>SNYPD vérifie chaque recherche environ toutes les 30 secondes, jusqu’à 5 minutes au plus sur les recherches calmes, et pareil pour tous les plans. {SPEED_MEASURED['fr']} {VINTED_LAG['fr']} Ce qu’il apporte, c’est la portée : les recherches payantes tournent 24h/24 ordinateur fermé, et l’alerte te trouve sur ton téléphone où que tu sois.</p>
</section>
<section id="pour-qui">
  <h2>SNYPD est-il fait pour toi ?</h2>
  <ul class="fit-list">
    <li class="fit-yes"><strong>Oui, si tu veux juger chaque affaire toi-même.</strong>Tu vois l’annonce en premier, tu la compares aux vrais prix Vinted, et tu achètes sur Vinted sans confier ton compte.</li>
    <li><strong>Non, si tu veux qu’un bot achète à ta place.</strong>L’achat automatique demande un outil qui utilise ton compte Vinted, comme Souk, V-Tools, Resell Reserve, Resell Vault ou VINTI.</li>
    <li><strong>Tu achètes aussi sur Marktplaats ou 2dehands ?</strong>MarktAlert couvre les deux, DealFindr couvre Marktplaats. SNYPD ne couvre que Vinted.</li>
  </ul>
</section>
<section id="questions">
  <h2>Questions sur les bots Vinted</h2>
  {faq_html(faq)}
</section>
<section id="essayer">
  <h2>Essaie sur une recherche</h2>
  {cta('fr')}
</section>"""
    return page('compare', 'fr', 'Meilleur bot Vinted 2026 ? %d bots comparés | SNYPD' % (cd.others_count() + 1),
                'SNYPD face à %d bots et apps d’alerte Vinted (Souk, Telvin, V-Tools, InstantAlert, Vinotify, VINTI, Resell Vault…) : prix, compte, alertes, remboursement, d’après le site de chaque outil.' % cd.others_count(),
                'COMPARATIF DES BOTS VINTED &middot; VÉRIFIÉ LE ' + COMPARE_CHECKED_SHORT['fr'], 'Meilleur bot Vinted en 2026 : SNYPD et %d autres outils comparés' % cd.others_count(),
                'SNYPD t’alerte des nouvelles annonces Vinted, te montre le prix demandé typique d’un article sur Vinted, et ne touche jamais à ton compte Vinted. Voici la comparaison avec %d autres outils Vinted, point par point, avec la source de chaque information.' % cd.others_count(),
                None, body, [faq_ld(faq), compare_itemlist('fr')], head_extra='<ul class="glance" aria-label="SNYPD en bref"><li><span>&#10003;</span>Données de prix incluses</li><li><span>&#10003;</span>Jamais de connexion Vinted</li><li><span>&#10003;</span>Alertes sur ton téléphone</li><li><span>&#10003;</span>Remboursement sous 14 jours</li></ul>')


# ------------------------------------------------------------------ page: what is a vinted monitor
# Added 2026-10-03: "vinted monitor" ranks the same sites as "vinted bot" on Google UK, and
# Google's People-also-ask shows "What is a Vinted monitor?" and "Are Vinted bots worth it?".
# Competitor facts below come from COMPETITORS (each vendor's own site, COMPARE_CHECKED).
MONITOR_TYPES_HEAD = {'en': ['TYPE', 'WHAT IT DOES', 'ACTS ON YOUR VINTED ACCOUNT', 'WHO DECIDES EACH PURCHASE'],
                      'fr': ['TYPE', 'CE QU’IL FAIT', 'AGIT SUR TON COMPTE VINTED', 'QUI DÉCIDE DE CHAQUE ACHAT']}
MONITOR_TYPES = {
    'en': [['Monitor (alert bot)', 'Finds new listings in your searches and alerts you', 'No need to: it only reads search results', 'You'],
           ['Autobuy or autocop bot', 'Buys or checks out for you', 'Yes: buying needs a logged-in account', 'The bot, following your rules'],
           ['Seller automation', 'Relists, bumps or sends offers from your shop', 'Yes: it works on your own shop', 'Not a buying tool'],
           ['Script you host (GitHub)', 'A monitor you run on your own server', 'Depends on the script', 'You']],
    'fr': [['Monitor (bot d’alertes)', 'Trouve les nouvelles annonces de tes recherches et t’alerte', 'Pas besoin : il lit seulement les résultats de recherche', 'Toi'],
           ['Bot d’achat automatique (autobuy)', 'Achète ou passe commande à ta place', 'Oui : acheter demande un compte connecté', 'Le bot, selon tes règles'],
           ['Automatisation vendeur', 'Republie, remonte ou envoie des offres depuis ta boutique', 'Oui : il travaille sur ta propre boutique', 'Pas un outil d’achat'],
           ['Script à héberger (GitHub)', 'Un monitor que tu fais tourner sur ton propre serveur', 'Dépend du script', 'Toi']],
}


def page_monitor(lang):
    if lang == 'en':
        faq = [
            ('What is the difference between a Vinted monitor and a Vinted bot?',
             '&ldquo;Vinted bot&rdquo; is the wider word: it covers monitors, autobuy bots and seller tools. A monitor is the kind that only watches searches and alerts you. Resellers often use the two words for the same thing, which is why most monitors also call themselves bots.'),
            ('Is there a free Vinted monitor?',
             'Yes, with limits. SNYPD Free runs one search with no time limit: 24/7 for the first @@trial_days@@ days, then while your dashboard is open. Other tools list free plans too; their limits are side by side in <a href="%s">Vinted bots compared</a>.' % SLUGS['compare']['en']),
            ('How fast is a Vinted monitor?',
             'It depends on how often the tool checks. SNYPD checks each search about every 30 seconds on every plan. ' + SPEED_MEASURED['en'] + ' Some vendors advertise milliseconds; those are their own figures, measured their own way.'),
            ('Do I need Discord or Telegram?',
             'Only if the monitor you pick sends alerts there. SNYPD sends push notifications to your phone or computer, so there is nothing else to install. On iPhone, add SNYPD to your Home Screen first: Apple only allows web push for Home Screen apps.'),
            ('Which Vinted countries can a monitor watch?',
             'That depends on the tool. SNYPD works on %s, 26 sites in all, each in its own currency: paste a search link from the site you shop on.' % MARKETS_TEXT['en']),
        ]
        body = f"""
<section id="answer">
  <h2>The short answer</h2>
  <div class="lg-box lg-mint"><p>A Vinted monitor is a tool that checks your Vinted searches over and over and alerts you when a listing appears that was not there before. Resellers also call it a Vinted alert bot. A monitor only finds and tells: you open the listing on Vinted and decide whether to buy. Tools that also buy for you are autobuy bots, and they need your logged-in Vinted account.</p></div>
</section>
<section id="why">
  <h2>Why resellers use one</h2>
  <p>Vinted&rsquo;s own saved searches show a &ldquo;+N&rdquo; counter the next time you open the app (<a href="{HELP435['en']}" rel="nofollow noopener">Vinted help</a>). They do not send a notification for each new match, so you only find out when you look.</p>
  <p>Everyone watching the same search can see a new listing the moment it appears, and the first person to notice it gets the first chance to buy. Well-priced listings are exactly the ones that go first. How often listings come up well under the typical price is measured in <a href="{SLUGS['deals']['en']}">Vinted deals</a>.</p>
</section>
<section id="how">
  <h2>How a Vinted monitor works</h2>
  <ol>
    <li>You give it a search: usually a Vinted search link with your filters, or keywords in the tool&rsquo;s own form.</li>
    <li>It loads the newest results of that search: the same public results anyone can open on Vinted.</li>
    <li>It compares them with what it saw last time. A listing it has not seen before is new.</li>
    <li>It sends you the new listing: a push notification, a Telegram or Discord message, or a line in an app, depending on the tool.</li>
    <li>It repeats. How often depends on the tool; SNYPD checks about every 30 seconds, less often (up to 5 minutes) on searches that go quiet.</li>
  </ol>
  {figure('feed', 'en')}
</section>
<section id="types">
  <h2>Monitor, autobuy bot or seller automation?</h2>
  <p>All three get called &ldquo;Vinted bots&rdquo;. What separates them is what they do with your Vinted account.</p>
  {table(MONITOR_TYPES_HEAD['en'], MONITOR_TYPES['en'])}
  <p>Searches for &ldquo;Vinted automation&rdquo; mostly lead to seller tools. A monitor automates the buyer side only. More on the differences in <a href="{SLUGS['bot']['en']}">Vinted bot</a>.</p>
</section>
<section id="alerts">
  <h2>Where the alerts arrive</h2>
  <p>Monitors differ most in how they reach you. From each tool&rsquo;s own site, checked on {COMPARE_CHECKED['en']}:</p>
  <ul>
    <li><strong>Push notifications</strong> to your phone or computer: SNYPD, with nothing to install. App-based tools such as InstantAlert, Vinotify and DealFindr push through their own apps.</li>
    <li><strong>Telegram</strong>: Telvin Bot sends alerts only there; MarktAlert offers Telegram among other channels.</li>
    <li><strong>Discord</strong>: Resell Reserve, Resell Vault, Monitorius and VintageLab post alerts in Discord.</li>
    <li><strong>An app feed</strong>: V-Tools shows finds in its own app.</li>
  </ul>
  <p>Whichever you pick, check that the alert reaches you with your laptop closed. A monitor that only runs while a browser tab is open misses most of the night.</p>
</section>
<section id="checklist">
  <h2>What to check before you pick one</h2>
  <ul class="fit-list">
    <li><strong>Does it ask for your Vinted login?</strong>A monitor only reads search results, so it has no reason to. Tools that buy for you do need it.</li>
    <li><strong>Does it keep every filter?</strong>Pasting a Vinted search link keeps all of them: brand, size, price, condition, colour, material. A tool&rsquo;s own form may offer fewer.</li>
    <li><strong>Does it keep watching when you are not there?</strong>On SNYPD&rsquo;s free plan, a search runs 24/7 for the first @@trial_days@@ days, then while your dashboard is open; paid plans keep it running 24/7.</li>
    <li><strong>Does it cover your Vinted country?</strong>Each Vinted site has its own listings and currency.</li>
    <li><strong>Can you test it before paying?</strong>Look for a free plan or a refund you can actually use after trying it.</li>
  </ul>
  <p>How seven tools answer these questions: <a href="{SLUGS['compare']['en']}">Vinted bots and monitors compared</a>.</p>
</section>
<section id="rules">
  <h2>Is a Vinted monitor allowed?</h2>
  <p>Vinted&rsquo;s terms prohibit bots and scraping programs, and no monitor can promise how Vinted applies them. What you can control is what happens on your own account. A monitor that never signs in, like SNYPD, does nothing on your Vinted account: you find the listing through the alert and buy it through Vinted&rsquo;s normal checkout. Tools that buy for you act through your logged-in account.</p>
</section>
<section id="snypd">
  <h2>SNYPD as a Vinted monitor</h2>
  <p>Paste a Vinted search link, switch it on, and SNYPD checks it about every 30 seconds. New matches land in your dashboard with their price, the price including Buyer Protection and their condition, and as a push notification on your phone. It never asks for your Vinted password, never buys and never messages sellers. Pro and Elite add the Market Report: the typical Vinted asking price of an item by condition.</p>
  {table(PLANS_HEAD['en'], PLANS_ROWS['en'])}
</section>
<section id="faq">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="start">
  <h2>Try a monitor on one search</h2>
  {cta('en')}
</section>"""
        return page('monitor', 'en', 'What Is a Vinted Monitor? How It Works (2026 Guide) | SNYPD',
                    'A Vinted monitor checks your Vinted searches and alerts you when a new listing matches. How monitors work, how they differ from autobuy bots, and what to check.',
                    'VINTED MONITOR &middot; GUIDE', 'What is a Vinted monitor?',
                    'A Vinted monitor watches your Vinted searches and tells you when something new matches. Here is how monitors work, how they differ from autobuy bots and seller tools, what to check before you pick one, and where SNYPD fits.',
                    [('answer', 'Short answer'), ('why', 'Why use one'), ('how', 'How it works'), ('types', 'Monitor or autobuy'), ('alerts', 'Where alerts arrive'),
                     ('checklist', 'What to check'), ('rules', 'Is it allowed?'), ('snypd', 'SNYPD'), ('faq', 'Questions')],
                    body, [faq_ld(faq)])
    faq = [
        ('Quelle différence entre un monitor Vinted et un bot Vinted ?',
         '« Bot Vinted » est le mot le plus large : il couvre les monitors, les bots d’achat automatique et les outils pour vendeurs. Un monitor est le type qui surveille seulement des recherches et t’alerte. Les revendeurs emploient souvent les deux mots pour la même chose, c’est pourquoi la plupart des monitors se présentent aussi comme des bots.'),
        ('Existe-t-il un monitor Vinted gratuit ?',
         'Oui, avec des limites. SNYPD Free fait tourner une recherche sans limite de durée, 24h/24 pendant les @@trial_days@@ premiers jours puis tant que ton tableau de bord est ouvert. D’autres outils proposent aussi un plan gratuit ; leurs limites sont côte à côte dans le <a href="%s">comparatif des bots Vinted</a>.' % SLUGS['compare']['fr']),
        ('Un monitor Vinted, c’est rapide ?',
         'Ça dépend de la fréquence de vérification de l’outil. SNYPD vérifie chaque recherche environ toutes les 30 secondes, sur tous les plans. ' + SPEED_MEASURED['fr'] + ' Certains éditeurs annoncent des millisecondes ; ce sont leurs propres chiffres, mesurés à leur façon.'),
        ('Faut-il Discord ou Telegram ?',
         'Seulement si le monitor choisi envoie ses alertes là-bas. SNYPD envoie des notifications push sur ton téléphone ou ton ordinateur, sans rien d’autre à installer. Sur iPhone, ajoute d’abord SNYPD à ton écran d’accueil : Apple n’autorise les notifications web que pour les apps de l’écran d’accueil.'),
        ('Quels pays Vinted un monitor peut-il surveiller ?',
         'Ça dépend de l’outil. SNYPD fonctionne sur %s, 26 sites au total, chacun dans sa devise : colle un lien de recherche du site où tu achètes.' % MARKETS_TEXT['fr']),
    ]
    body = f"""
<section id="reponse">
  <h2>La réponse courte</h2>
  <div class="lg-box lg-mint"><p>Un monitor Vinted est un outil qui vérifie tes recherches Vinted encore et encore et t’alerte quand une annonce apparaît qui n’était pas là avant. On parle aussi de bot d’alertes Vinted. Un monitor se contente de trouver et de prévenir : tu ouvres l’annonce sur Vinted et tu décides d’acheter ou non. Les outils qui achètent aussi à ta place sont des bots d’achat automatique, et ils ont besoin de ton compte Vinted connecté.</p></div>
</section>
<section id="pourquoi">
  <h2>Pourquoi les revendeurs en utilisent un</h2>
  <p>Les recherches sauvegardées de Vinted affichent un compteur « +N » à ta prochaine visite dans l’app (<a href="{HELP435['fr']}" rel="nofollow noopener">aide Vinted</a>). Elles n’envoient pas de notification pour chaque nouvelle annonce : tu ne le découvres qu’en allant voir.</p>
  <p>Tous ceux qui surveillent la même recherche voient une nouvelle annonce au même moment, et le premier qui la remarque a la première chance de l’acheter. Les annonces bien placées sont justement celles qui partent en premier.</p>
</section>
<section id="fonctionnement">
  <h2>Comment marche un monitor Vinted</h2>
  <ol>
    <li>Tu lui donnes une recherche : en général un lien de recherche Vinted avec tes filtres, ou des mots-clés dans le formulaire de l’outil.</li>
    <li>Il charge les résultats les plus récents de cette recherche : les mêmes résultats publics que n’importe qui peut ouvrir sur Vinted.</li>
    <li>Il les compare à ce qu’il a vu la dernière fois. Une annonce qu’il n’a jamais vue est nouvelle.</li>
    <li>Il t’envoie la nouvelle annonce : une notification push, un message Telegram ou Discord, ou une ligne dans une app, selon l’outil.</li>
    <li>Il recommence. La fréquence dépend de l’outil ; SNYPD vérifie environ toutes les 30 secondes, moins souvent (jusqu’à 5 minutes) sur les recherches calmes.</li>
  </ol>
  {figure('feed', 'fr')}
</section>
<section id="types">
  <h2>Monitor, bot d’achat automatique ou automatisation vendeur ?</h2>
  <p>Les trois sont appelés « bots Vinted ». Ce qui les distingue, c’est ce qu’ils font de ton compte Vinted.</p>
  {table(MONITOR_TYPES_HEAD['fr'], MONITOR_TYPES['fr'])}
  <p>Les recherches « automatisation Vinted » mènent surtout à des outils pour vendeurs. Un monitor automatise uniquement le côté acheteur. Plus de détails sur la page <a href="{SLUGS['bot']['fr']}">bot Vinted</a>.</p>
</section>
<section id="alertes">
  <h2>Où arrivent les alertes</h2>
  <p>Les monitors diffèrent surtout par la façon de te prévenir. D’après le site de chaque outil, vérifié le {COMPARE_CHECKED['fr']} :</p>
  <ul>
    <li><strong>Notifications push</strong> sur ton téléphone ou ton ordinateur : SNYPD, sans rien installer. Des outils à application comme InstantAlert, Vinotify et DealFindr envoient leurs push via leur app.</li>
    <li><strong>Telegram</strong> : Telvin Bot alerte uniquement là ; MarktAlert propose Telegram parmi d’autres canaux.</li>
    <li><strong>Discord</strong> : Resell Reserve, Resell Vault, Monitorius et VintageLab publient les alertes dans Discord.</li>
    <li><strong>Le flux d’une app</strong> : V-Tools affiche les trouvailles dans sa propre app.</li>
  </ul>
  <p>Quel que soit ton choix, vérifie que l’alerte t’arrive ordinateur fermé. Un monitor qui ne tourne que dans un onglet ouvert rate la plus grande partie de la nuit.</p>
</section>
<section id="verifier">
  <h2>Ce qu’il faut vérifier avant de choisir</h2>
  <ul class="fit-list">
    <li><strong>Il demande tes identifiants Vinted ?</strong>Un monitor lit seulement des résultats de recherche, il n’en a donc pas besoin. Les outils qui achètent à ta place, si.</li>
    <li><strong>Il garde tous tes filtres ?</strong>Coller un lien de recherche Vinted les garde tous : marque, taille, prix, état, couleur, matière. Le formulaire d’un outil peut en proposer moins.</li>
    <li><strong>Il continue quand tu n’es pas là ?</strong>Avec le plan gratuit de SNYPD, une recherche tourne 24h/24 pendant les @@trial_days@@ premiers jours, puis tant que ton tableau de bord est ouvert ; les plans payants la font tourner 24h/24.</li>
    <li><strong>Il couvre ton pays Vinted ?</strong>Chaque site Vinted a ses propres annonces et sa devise.</li>
    <li><strong>Tu peux l’essayer avant de payer ?</strong>Cherche un plan gratuit ou un remboursement utilisable après l’avoir essayé.</li>
  </ul>
  <p>Les réponses de sept outils à ces questions : <a href="{SLUGS['compare']['fr']}">comparatif des bots Vinted</a>.</p>
</section>
<section id="regles">
  <h2>Un monitor Vinted, c’est autorisé ?</h2>
  <p>Les conditions de Vinted interdisent les bots et les programmes de scraping, et aucun monitor ne peut promettre comment Vinted les applique. Ce que tu maîtrises, c’est ce qui se passe sur ton propre compte. Un monitor qui ne se connecte jamais, comme SNYPD, ne fait rien sur ton compte Vinted : tu trouves l’annonce grâce à l’alerte et tu l’achètes avec le paiement normal de Vinted. Les outils qui achètent à ta place agissent via ton compte connecté.</p>
</section>
<section id="snypd">
  <h2>SNYPD, un monitor Vinted</h2>
  <p>Colle un lien de recherche Vinted, active-le, et SNYPD le vérifie environ toutes les 30 secondes. Les nouvelles annonces arrivent dans ton tableau de bord avec leur prix, le prix protection acheteurs incluse et leur état, et en notification push sur ton téléphone. Il ne demande jamais ton mot de passe Vinted, n’achète rien et n’écrit jamais aux vendeurs. Pro et Elite ajoutent le Market Report : le prix demandé typique d’un article sur Vinted selon son état.</p>
  {table(PLANS_HEAD['fr'], PLANS_ROWS['fr'])}
</section>
<section id="questions">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="essayer">
  <h2>Essaie un monitor sur une recherche</h2>
  {cta('fr')}
</section>"""
    return page('monitor', 'fr', 'Monitor Vinted : c’est quoi et comment ça marche (2026) | SNYPD',
                'Un monitor Vinted surveille tes recherches Vinted et t’alerte quand une nouvelle annonce correspond. Fonctionnement, différences avec l’achat auto, quoi vérifier.',
                'MONITOR VINTED &middot; GUIDE', 'Qu’est-ce qu’un monitor Vinted ?',
                'Un monitor Vinted surveille tes recherches Vinted et te prévient quand un nouvel article correspond. Voici comment marchent les monitors, en quoi ils diffèrent des bots d’achat automatique et des outils pour vendeurs, quoi vérifier avant d’en choisir un, et où se place SNYPD.',
                [('reponse', 'Réponse courte'), ('pourquoi', 'Pourquoi'), ('fonctionnement', 'Fonctionnement'), ('types', 'Monitor ou achat auto'), ('alertes', 'Où arrivent les alertes'),
                 ('verifier', 'Quoi vérifier'), ('regles', 'Autorisé ?'), ('snypd', 'SNYPD'), ('questions', 'Questions')],
                body, [faq_ld(faq)])


# ------------------------------------------------------------------ money / numbers
def money(cents, lang):
    whole = cents % 100 == 0
    if lang == 'en':
        s = '{:,}'.format(cents // 100) if whole else '{:,.2f}'.format(cents / 100)
        return '&euro;' + s
    s = '{:,}'.format(cents // 100) if whole else '{:,.2f}'.format(cents / 100)
    if lang == 'nl':  # Dutch: euro sign first, dot for thousands (same as plans.price)
        return '&euro;&nbsp;' + s.replace(',', '#').replace('.', ',').replace('#', '.')
    s = s.replace(',', ' ').replace('.', ',')
    return s + '&nbsp;&euro;'


def num(n, lang):
    if lang == 'nl':
        return '{:,}'.format(n).replace(',', '.')
    return '{:,}'.format(n) if lang == 'en' else '{:,}'.format(n).replace(',', ' ')


# ------------------------------------------------------------------ page: deals guide
# Figures come ONLY from DEALS, the verbatim output of ops/seo/deals_stats.sql (its
# header explains the method and the md5 check). Never type a number into the copy.
DEALS = os.path.join(ROOT, 'ops', 'seo', 'data', 'deals-2026-10.json')
# Vinted's own English names for its condition grades (stored in French on vinted.be).
COND_EN = {'Neuf avec étiquette': 'New with tags', 'Neuf sans étiquette': 'New without tags',
           'Très bon état': 'Very good', 'Bon état': 'Good', 'Satisfaisant': 'Satisfactory'}
BUY_SAFE = 'https://www.vinted.co.uk/help/82'


def pct(a, b):
    return '%d%%' % round(100.0 * a / b)


# Weekly "far below typical" counts (work order 18, Step 6). HELD behind a legal gate: written only to
# ops/seo/preview/ until Tanush confirms in writing in outreach/seo-geo-log.md. Data: ops/seo/steals_batch.py
# (read-only, backend container; same item matching and typical prices as the price guide); the VPS cron
# snypd-steals-weekly saves every week to ~/snypd/logs/steals-<week>.json before the 14-day retention.
STEALS_HELD = True
STEALS_WEEK = os.path.join(ROOT, 'ops', 'seo', 'data', 'steals-2026-W40.json')
STEALS_MIN_ROWS = 20  # per item shown, and for the week as a whole
STEALS_HELP_READ = '10 October 2026'


def steals_section(path):
    d = json.load(open(path, encoding='utf-8'))
    names = {it['slug']: it['name'] for it in json.load(open(os.path.join(ROOT, 'ops', 'seo', 'price_items.json'), encoding='utf-8'))['items']}
    ok = [i for i in d['items'] if 'error' not in i and i['eligible'] > 0]
    below, elig = sum(i['below_rule'] for i in ok), sum(i['eligible'] for i in ok)
    if below < STEALS_MIN_ROWS:
        sys.exit('steals: %s has fewer than %d listings under the rule' % (d['week'], STEALS_MIN_ROWS))
    shown = sorted([i for i in ok if i['below_rule'] >= STEALS_MIN_ROWS], key=lambda i: -i['share_below_pct'])
    a = datetime.date.fromisoformat(d['from'][:10])
    b = datetime.date.fromisoformat(d['to'][:10]) - datetime.timedelta(days=1)
    span = '%d %s to %d %s %d' % (a.day, MONTHS_TXT['en'][a.month - 1], b.day, MONTHS_TXT['en'][b.month - 1], b.year)
    rows = [['<a href="/vinted-price-guide/%s">%s</a>' % (i['slug'], esc(names.get(i['slug'], i['slug']))),
             '<span class="ct-num">%s</span>' % num(i['eligible'], 'en'),
             '<span class="ct-num">%s</span><small>%s%%</small>' % (num(i['below_rule'], 'en'), ('%.1f' % i['share_below_pct']).rstrip('0').rstrip('.')),
             '<span class="ct-num">%d%%</span>' % round(i['median_pct_under'])] for i in shown]
    tbl = table(['ITEM', 'NEW LISTINGS', 'AT 60% OF TYPICAL OR LESS', 'MEDIAN DISCOUNT'], rows)
    return f"""<section id="weekly">
  <h2>Week of {span}: listings far below the typical price</h2>
  <p>Every item in the <a href="/vinted-price-guide">Vinted price guide</a>, counted on vinted.be for one week ({span}, Brussels time). A listing counts when its asking price was 60% or less of the typical asking price for the same item in the same condition, the figure the price guide is built on. Kids&rsquo; sizes, lots and bundles, business sellers and conditions without a typical price are left out.</p>
  <div class="lg-box lg-mint"><p>Across {len(ok)} items, {num(below, 'en')} of {num(elig, 'en')} new listings ({pct(below, elig)}) went up at 60% or less of the typical price for their condition.</p></div>
  {tbl}
  <p class="ct-note">Shown: the {len(shown)} items with at least {STEALS_MIN_ROWS} such listings that week. Median discount: half of those listings were further under the typical price, half less. Asking prices, not sold prices: SNYPD can&rsquo;t tell whether these listings sold, or for how much.</p>
  <h3>BEFORE YOU JUMP ON ONE</h3>
  <p>A price far below the usual one is a reason to look closer, not proof of a bargain: a different colourway, wear the condition label doesn&rsquo;t show, or a fake can all explain it. Pay only through Vinted. Vinted&rsquo;s help centre: &ldquo;If you make a payment outside of Vinted&rsquo;s system (without using the Buy now button), your purchase won&rsquo;t be protected&rdquo; (<a href="{BUY_SAFE}" rel="noopener">Vinted help: Buying safely</a>, read {STEALS_HELP_READ}). For some eligible items Vinted also sells Item Verification; the listing shows a banner when it is available.</p>
</section>
"""


def page_deals(lang, steals=None):
    d = json.load(open(DEALS, encoding='utf-8'))
    models = d['models']
    start = datetime.date.fromisoformat(d['window_start'][:10])
    last = datetime.date.fromisoformat(d['window_end'][:10]) - datetime.timedelta(days=1)
    span = f'{start.day} {MONTHS_TXT["en"][start.month - 1]} to {last.day} {MONTHS_TXT["en"][last.month - 1]} {last.year}'
    days = d['days']
    by = {m['name']: m for m in models}
    top = models[0]  # most listings
    rare = min(models, key=lambda m: m['under50'] / m['n'])
    vg = {c['condition']: c['median_cents'] for c in top['ladder']}.get('Très bon état')
    if vg is None:
        sys.exit('deals: the top model has no "Très bon état" median; pick another example')
    cap = int(round(vg * 0.7 / 100.0)) * 100
    lad = {c['condition']: c['median_cents'] for c in top['ladder']}
    good, nwt = lad.get('Bon état'), lad.get('Neuf avec étiquette')
    if not good or not nwt or not (good < cap < vg):
        sys.exit('deals: the condition example no longer holds for ' + top['name'])
    rows = []
    for m in models:
        rows.append([m['name'],
                     f'<span class="ct-num">{num(m["n"], "en")}</span>',
                     f'<span class="ct-num">{num(m["under30"], "en")}</span><small>{pct(m["under30"], m["n"])} &middot; about {num(round(m["under30"] / days), "en")} a day</small>',
                     f'<span class="ct-num">{num(m["under50"], "en")}</span><small>{pct(m["under50"], m["n"])}</small>'])
    ladder_rows = [[COND_EN.get(c['condition'], esc(c['condition'])), f'<span class="ct-num">{money(c["median_cents"], "en")}</span>',
                    f'<span class="ct-num">{num(c["n"], "en")}</span>'] for c in top['ladder']]
    shares = [m['under30'] / m['n'] for m in models]
    lo_pct, hi_pct = '%d%%' % round(100 * min(shares)), '%d%%' % round(100 * max(shares))
    faq = [
        ('What counts as a steal on Vinted?',
         'A listing priced well below what the same item is usually listed for in the same condition, that is still the item it claims to be. A price alone does not make a steal: for the models in this guide, between %s and %s of new listings went up 30%% or more under the typical price for their condition.' % (lo_pct, hi_pct)),
        ('Where can I see the typical Vinted price of an item?',
         f'Vinted does not show one on its listings. SNYPD&rsquo;s free <a href="/vinted-price-guide">Vinted prices</a> page lists typical asking prices for popular sneakers and streetwear, and the Market Report in Pro and Elite prices any search by condition.'),
        ('Are very cheap Vinted listings fake?',
         'Some are, and a low price is one of the reasons to look closer, but it is not proof. Kids&rsquo; sizes, other colourways, wear the condition label does not show and sellers who want a quick sale also explain low prices. Check the photos, the size and the seller before you buy.'),
        ('Does SNYPD buy deals for me?',
         'No. SNYPD watches your Vinted searches and sends you an alert when a new listing matches. You open it on Vinted and decide yourself. It never signs in to your Vinted account.'),
    ]
    tbl = table(['MODEL', 'NEW LISTINGS', '30% OR MORE UNDER TYPICAL', 'HALF PRICE OR LESS'], rows)
    body = f"""
<section id="answer">
  <h2>Short answer</h2>
  <div class="lg-box lg-mint"><p>A cheap Vinted listing is not rare. From {span}, {num(top['under30'], 'en')} of the {num(top['n'], 'en')} new {top['name']} listings SNYPD saw on vinted.be ({pct(top['under30'], top['n'])}) were posted at 30% or more below the typical asking price for their condition, and {num(top['under50'], 'en')} ({pct(top['under50'], top['n'])}) at half price or less. What is rare is seeing the right one first. Finding Vinted deals comes down to four things: know the typical price for the exact condition, search narrow with a price cap, get alerted to new listings instead of refreshing, and check the listing before you pay.</p></div>
</section>
<section id="data">
  <h2>How often deep discounts appear</h2>
  <p>New listings on vinted.be over {days} days, {span}, compared with the typical asking price for the same model in the same condition:</p>
  {tbl}
  <p>The pattern differs by model. On {top['name']}, half-price listings are common, so a cheap one proves little on its own: check the size, colourway and wear first. On {rare['name']}, only {num(rare['under50'], 'en')} of {num(rare['n'], 'en')} new listings went up at half price or less, so a big discount there is unusual and worth both speed and a closer look.</p>
  <p class="ct-note">How these numbers are made is under <a href="#method">method and limits</a>. Asking prices, not sold prices.</p>
</section>
{steals_section(steals) if steals else ''}<section id="price">
  <h2>1. Know the typical price for the exact condition</h2>
  <p>A price only looks low against the right comparison. Condition moves Vinted prices a lot: on {top['name']}, the typical New with tags price is {nwt / good:.1f} times the Good one. Typical asking prices for new {top['name']} listings, {span}:</p>
  {table(['CONDITION', 'TYPICAL ASKING PRICE', 'LISTINGS'], ladder_rows)}
  <p>So the same {money(cap, 'en')} is 30% under the typical price for a Very good pair, but above the typical price for a Good pair ({money(good, 'en')}). For more models, see the <a href="/vinted-price-guide">Vinted price guide</a>. In SNYPD Pro and Elite, the Market Report gives this breakdown for any search you type.</p>
</section>
<section id="search">
  <h2>2. Search narrow, with a price cap</h2>
  <ul>
    <li><strong>Name the exact model</strong> and, for clothing, the garment. &ldquo;Nike&rdquo; alone returns too much to watch.</li>
    <li><strong>Set your size and condition filters</strong>, so every match is one you would actually buy.</li>
    <li><strong>Set the maximum price</strong> around 70% of the typical price for that condition. For a Very good {top['name']}, that is about {money(cap, 'en')}.</li>
    <li><strong>Sort by newest first</strong>, so new listings come to the top. In the search link this shows as <code>order=newest_first</code>.</li>
  </ul>
</section>
<section id="first">
  <h2>3. Be first: get alerted, don&rsquo;t refresh</h2>
  <p>Everyone watching the same search can see a new listing the moment it appears, so the first to notice it gets the first chance. Vinted&rsquo;s saved searches show a &ldquo;+N&rdquo; counter the next time you open the app; they do not send a notification for each new match (<a href="{SLUGS['notify']['en']}">how Vinted notifications work</a>). To hear about a new match while you are doing something else, you need a tool that watches the search for you.</p>
  <p>SNYPD checks each search about every 30 seconds and sends a push notification to your phone or computer when a new listing matches. The free plan runs one search, 24/7 for the first @@trial_days@@ days and then while your dashboard is open; paid plans from @@price:solo@@ a month keep watching 24/7.</p>
  {figure('feed', 'en')}
</section>
<section id="check">
  <h2>4. Check before you pay</h2>
  <ul>
    <li><strong>Photos against the label.</strong> Look for wear the condition grade does not mention: soles, creases, stains, missing tags.</li>
    <li><strong>The size.</strong> Kids&rsquo; and adult sizes share model names and differ a lot in price.</li>
    <li><strong>The price against the typical one.</strong> Compare the discount with how often that model gets one: on {rare['name']}, a half-price listing came up {num(rare['under50'], 'en')} times in {days} days.</li>
    <li><strong>The seller.</strong> Reviews and other listings tell you more than one photo.</li>
    <li><strong>Pay with Vinted&rsquo;s Buy now button.</strong> Vinted says that payments made outside its system are not covered by Buyer Protection (<a href="{BUY_SAFE}" rel="noopener">Vinted help: buying safely</a>).</li>
  </ul>
</section>
<section id="method">
  <h2>Method and limits</h2>
  <ul>
    <li><strong>Source.</strong> Listings SNYPD&rsquo;s systems first saw on vinted.be, in euros, from {span}.</li>
    <li><strong>Matching.</strong> A listing counts for a model when its title contains the model&rsquo;s words (for example &ldquo;dunk&rdquo; and &ldquo;low&rdquo;). This is a simpler match than the Market Report&rsquo;s, so counts differ from the <a href="/vinted-price-guide">Vinted price guide</a>.</li>
    <li><strong>Typical price</strong> is the median first asking price for that model in that condition. Conditions with fewer than 30 listings are left out.</li>
    <li><strong>Under</strong> means a first asking price at or below 70% (or 50%) of that median.</li>
  </ul>
  <h3>LIMITS</h3>
  <ul>
    <li>Asking prices, not sold prices. We cannot see which listings sold or for how much.</li>
    <li>Sizes and colourways are mixed, and fakes are not removed, so some low prices are a different item rather than a bargain.</li>
    <li>One site (vinted.be) and one two-week window. Other Vinted sites and months will differ.</li>
  </ul>
</section>
<section id="faq">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="start">
  <h2>Watch one search for free</h2>
  {cta('en')}
</section>"""
    return page('deals', 'en', 'Vinted Deals: How to Find Steals Before Anyone Else | SNYPD',
                'How to find Vinted deals and steals: real data on how often listings go up far below the typical price, and four steps to see the right one first.',
                'VINTED DEALS &middot; GUIDE', 'How to find Vinted deals before anyone else',
                f'Low prices on Vinted are common; good deals that are still the item you want, seen before anyone else, are not. This guide uses {num(sum(m["n"] for m in models), "en")} real vinted.be listings from {span} to show how often deep discounts appear, then the four steps that get you to them first.',
                [('answer', 'Short answer'), ('data', 'How often')] + ([('weekly', 'This week')] if steals else []) + [('price', 'Know the price'), ('search', 'Search narrow'), ('first', 'Be first'), ('check', 'Check first'), ('method', 'Method'), ('faq', 'Questions')],
                body, [faq_ld(faq)])


# ------------------------------------------------------------------ page: fees + calculator
# The fee rule is Vinted's own (price lists of vinted.fr/.de/.nl/.it/.es and vinted.com, read
# 2 Oct 2026). FEES_CHECK is the verbatim output of ops/seo/fees_check.sql: the same integer
# formula tested against every real vinted.be listing of a week. If it ever stops matching
# 100%, the build stops instead of publishing a wrong claim.
FEES_CHECK = os.path.join(ROOT, 'ops', 'seo', 'data', 'fees-check-2026-10.json')
FEES_CHECKED = {'en': '2 October 2026', 'fr': '2 octobre 2026'}
FEE_SRC = {
    'fr_list': 'https://www.vinted.fr/pricelist', 'fr_help': 'https://www.vinted.fr/help/1654',
    'us_list': 'https://www.vinted.com/pricelist', 'uk_list': 'https://www.vinted.co.uk/pricelist',
    'free_en': 'https://www.vinted.co.uk/help/373-is-selling-on-vinted-free', 'free_fr': 'https://www.vinted.fr/help/373',
    'ship_en': 'https://www.vinted.co.uk/help/458-who-pays-for-shipping', 'ship_fr': 'https://www.vinted.fr/help/458',
    'safe_en': 'https://www.vinted.co.uk/help/82', 'safe_fr': 'https://www.vinted.fr/help/82',
}
# Dataset rich results (Google): creator must be a typed Organization on the page itself (an @id
# pointing at the homepage's Organization is reported as 'Invalid object type'), and a license
# is expected. CC BY 4.0: anyone may reuse the figures if they credit SNYPD (decided 2026-10-03).
DATASET_CREATOR = {'@type': 'Organization', '@id': SITE + '/#org', 'name': 'SNYPD', 'url': SITE + '/'}
DATASET_LICENSE = 'https://creativecommons.org/licenses/by/4.0/'
FEE_TABLE_CENTS = [500, 1000, 2000, 3000, 5000, 10000, 20000, 50000]

# Plain ASCII on purpose. Whole cents only: fee = 70 + floor((cents * 5 + 50) / 100).
FEE_JS = r"""<script>
(function () {
  var f = document.getElementById('fc'); if (!f) return;
  var inp = document.getElementById('fc-price'), cur = document.getElementById('fc-cur'), L = f.getAttribute('data-lang');
  function fmt(c, k) {
    var s = (c / 100).toFixed(2);
    if (k === 'usd') return L === 'fr' ? s.replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '\u202f') + '\u00a0$' : '$' + s.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    if (L === 'fr') return s.replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '\u202f') + '\u00a0\u20ac';
    return '\u20ac' + s.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }
  function put(id, t) { document.getElementById(id).textContent = t; }
  function run() {
    var r = String(inp.value).replace(/[\s\u00a0\u202f\u20ac$]/g, '');
    r = /,\d{1,2}$/.test(r) ? r.replace(/\./g, '').replace(',', '.') : r.replace(/,/g, '');
    var v = /^\d+(\.\d{0,2})?$/.test(r) ? parseFloat(r) : NaN;
    if (!(v > 0) || v > 1000000) { put('fc-fee', '-'); put('fc-total', '-'); put('fc-pct', '-'); put('fc-seller', '-'); return; }
    var c = Math.round(v * 100), fee = 70 + Math.floor((c * 5 + 50) / 100), k = cur.value;
    put('fc-fee', fmt(fee, k)); put('fc-total', fmt(c + fee, k)); put('fc-seller', fmt(c, k));
    var p = (100 * fee / c).toFixed(1); put('fc-pct', (L === 'fr' ? p.replace('.', ',') + '\u00a0%' : p + '%'));
  }
  inp.addEventListener('input', run); cur.addEventListener('change', run); run();
})();
</script>"""


def fee_cents(c):
    return 70 + (c * 5 + 50) // 100


def m2(c, lang):
    s = '{:,.2f}'.format(c / 100)
    if lang == 'en':
        return '&euro;' + s
    return s.replace(',', '&#8239;').replace('.', ',') + '&nbsp;&euro;'


def pct1(a, b, lang):
    s = '%.1f' % (100.0 * a / b)
    return s + '%' if lang == 'en' else s.replace('.', ',') + '&nbsp;%'


def page_fees(lang):
    chk = json.load(open(FEES_CHECK, encoding='utf-8'))
    if not (chk['listings'] > 0 and chk['fee_matches'] == chk['listings'] == chk['total_matches']):
        sys.exit('fees: the real-listing check no longer matches 100%; do not publish the rule as verified')
    n = num(chk['listings'], lang)
    lo, hi = m2(chk['min_price_cents'], lang), m2(chk['max_price_cents'], lang)
    ws = datetime.date.fromisoformat(chk['window_start'][:10])
    we = datetime.date.fromisoformat(chk['window_end'][:10]) - datetime.timedelta(days=1)
    rows = [[f'<span class="ct-num">{m2(c, lang)}</span>', f'<span class="ct-num">{m2(fee_cents(c), lang)}</span>',
             f'<span class="ct-num">{m2(c + fee_cents(c), lang)}</span>', f'<span class="ct-num">{pct1(fee_cents(c), c, lang)}</span>']
            for c in FEE_TABLE_CENTS]
    ex = 2000
    small, big = FEE_TABLE_CENTS[0], FEE_TABLE_CENTS[-2]
    b1, nb = 1000, 3
    sep, bun = nb * fee_cents(b1), fee_cents(nb * b1)
    ui = {'en': ('ITEM PRICE', 'CURRENCY', 'BUYER PROTECTION FEE', 'BUYER PAYS (BEFORE SHIPPING)', 'FEE AS % OF PRICE', 'SELLER RECEIVES',
                 'Euro sites: vinted.fr, .be, .de, .nl, .it, .es', 'US dollars: vinted.com', '20.00'),
          'fr': ('PRIX DE L’ARTICLE', 'DEVISE', 'FRAIS DE PROTECTION ACHETEURS', 'L’ACHETEUR PAIE (HORS LIVRAISON)', 'FRAIS EN % DU PRIX', 'LE VENDEUR REÇOIT',
                 'Sites en euros : vinted.fr, .be, .de, .nl, .it, .es', 'Dollars US : vinted.com', '20,00')}[lang]
    calc = (f'<div class="fc" id="fc" data-lang="{lang}"><div class="fc-in">'
            f'<label>{ui[0]}<input id="fc-price" type="text" inputmode="decimal" autocomplete="off" value="{ui[8]}"></label>'
            f'<label>{ui[1]}<select id="fc-cur"><option value="eur">{ui[6]}</option><option value="usd">{ui[7]}</option></select></label></div>'
            f'<dl class="fc-out" aria-live="polite"><div><dt>{ui[2]}</dt><dd id="fc-fee">{m2(fee_cents(ex), lang)}</dd></div>'
            f'<div class="fc-total"><dt>{ui[3]}</dt><dd id="fc-total">{m2(ex + fee_cents(ex), lang)}</dd></div>'
            f'<div><dt>{ui[4]}</dt><dd id="fc-pct">{pct1(fee_cents(ex), ex, lang)}</dd></div>'
            f'<div><dt>{ui[5]}</dt><dd id="fc-seller">{m2(ex, lang)}</dd></div></dl></div>' + FEE_JS)
    S = FEE_SRC
    if lang == 'en':
        faq = [
            ('Who pays Vinted fees?', f'The buyer. The Buyer Protection fee is added to the price at checkout, and the buyer also pays shipping. Selling is free: the seller receives the full item price (<a href="{S["free_en"]}" rel="noopener">Vinted help</a>).'),
            ('How much is the Vinted fee on a &euro;20 item?', f'{m2(fee_cents(ex), "en")}: &euro;0.70 plus 5% of &euro;20. The buyer pays {m2(ex + fee_cents(ex), "en")} before shipping.'),
            ('Why is the fee so high on cheap items?', f'Because &euro;0.70 of it is fixed. On a {m2(small, "en")} item the fee is {pct1(fee_cents(small), small, "en")} of the price; on a {m2(big, "en")} item it is {pct1(fee_cents(big), big, "en")}.'),
            ('Is VAT included in the Vinted fee?', f'Yes. Vinted says the total of its fees, VAT included, is added to the final price at checkout (<a href="{S["fr_help"]}" rel="noopener">Vinted help, in French</a>).'),
            ('Can I avoid the Buyer Protection fee?', f'Only by paying outside Vinted, and then you are not covered. Vinted says payments made outside its system are not covered by Buyer Protection (<a href="{S["safe_en"]}" rel="noopener">Vinted help</a>). Buying several items from one seller as a bundle is the legitimate way to pay the &euro;0.70 once.'),
        ]
        body = f"""
<section id="answer">
  <h2>Short answer</h2>
  <div class="lg-box lg-mint"><p>On Vinted&rsquo;s euro sites the buyer pays a <strong>Buyer Protection fee of &euro;0.70 plus 5% of the item price</strong>, VAT included, on top of the price and shipping. Selling is free: the seller gets the full item price. On a &euro;20 item the fee is {m2(fee_cents(ex), 'en')}, so the buyer pays {m2(ex + fee_cents(ex), 'en')} before shipping. We checked the rule against all {n} vinted.be listings SNYPD saw from {ws.day} {MONTHS_TXT['en'][ws.month - 1]} to {we.day} {MONTHS_TXT['en'][we.month - 1]} {we.year}: every fee matched to the cent.</p></div>
</section>
<section id="calculator">
  <h2>Vinted fee calculator</h2>
  <p>Type the item price as shown on the listing.</p>
  {calc}
  <p class="ct-note">Uses the rule in Vinted&rsquo;s price lists: &euro;0.70 (or $0.70 on vinted.com) plus 5% of the item price, rounded to the nearest cent. Shipping is extra and depends on the parcel and carrier. Vinted&rsquo;s checkout always shows the exact total; it describes the rule as what is &ldquo;usually&rdquo; charged.</p>
</section>
<section id="table">
  <h2>The fee at common prices</h2>
  {table(['ITEM PRICE', 'BUYER PROTECTION FEE', 'BUYER PAYS (BEFORE SHIPPING)', 'FEE AS % OF PRICE'], rows)}
  <p>The fixed &euro;0.70 is why the fee weighs most on cheap items: {pct1(fee_cents(small), small, 'en')} of a {m2(small, 'en')} item, but {pct1(fee_cents(big), big, 'en')} of a {m2(big, 'en')} one.</p>
</section>
<section id="bundles">
  <h2>Bundles pay the fixed part once</h2>
  <p>Vinted&rsquo;s price list charges the fee on the price of the item <em>or the bundle</em>. Buy {nb} items of {m2(b1, 'en')} from one seller separately and the fees add up to {m2(sep, 'en')}; buy them as one bundle and the fee is {m2(bun, 'en')}, saving {m2(sep - bun, 'en')}.</p>
</section>
<section id="sites">
  <h2>Fees by Vinted site</h2>
  <ul>
    <li><strong>vinted.fr, vinted.de, vinted.nl, vinted.it, vinted.es:</strong> 5% + &euro;0.70, per each site&rsquo;s price list (<a href="{S['fr_list']}" rel="noopener">vinted.fr</a>). <strong>vinted.be:</strong> the same, checked on {n} real listings.</li>
    <li><strong>vinted.com (US):</strong> $0.70 plus 5% of the agreed item price, not including shipping (<a href="{S['us_list']}" rel="noopener">price list</a>). Not checked against our own data.</li>
    <li><strong>vinted.co.uk:</strong> a range, &ldquo;3% to 8% + &pound;0.3 to &pound;0.8&rdquo;, VAT included, depending on the item, the order value and the order type (<a href="{S['uk_list']}" rel="noopener">price list</a>). No exact calculator is possible; the UK checkout shows the fee.</li>
  </ul>
  <p>Other Vinted sites publish their own price lists; check yours before relying on these numbers.</p>
</section>
<section id="sellers">
  <h2>What sellers pay</h2>
  <p>Nothing to list or sell: Vinted says selling is free and the seller keeps the full item price (<a href="{S['free_en']}" rel="noopener">Vinted help</a>). Sellers only pay if they choose paid visibility, such as bumping an item or a wardrobe showcase; Vinted&rsquo;s price list says those prices depend on duration, item price and reach.</p>
</section>
<section id="shipping">
  <h2>Who pays shipping</h2>
  <p>The buyer, at checkout, when buying with the Buy now button. The price depends on the parcel size and the buyer&rsquo;s and seller&rsquo;s locations. The exception is custom shipping, where the seller pays upfront (<a href="{S['ship_en']}" rel="noopener">Vinted help</a>).</p>
</section>
<section id="resellers">
  <h2>For resellers: count the real buying cost</h2>
  <p>What you pay for stock is the price, plus the Buyer Protection fee, plus shipping. A &ldquo;cheap&rdquo; &euro;5 item really costs {m2(small + fee_cents(small), 'en')} before shipping. SNYPD&rsquo;s dashboard shows each new listing&rsquo;s price including Buyer Protection, and its Market Report shows the typical asking price for an item&rsquo;s condition, so you can see the margin before you buy. See <a href="{SLUGS['deals']['en']}">how to find Vinted deals</a> and <a href="/vinted-price-guide">typical Vinted prices</a>.</p>
  {figure('feed', 'en')}
</section>
<section id="method">
  <h2>How we checked</h2>
  <ul>
    <li>SNYPD stores the price, fee and total Vinted reports for every listing it sees. For {n} vinted.be listings seen from {ws.day} {MONTHS_TXT['en'][ws.month - 1]} to {we.day} {MONTHS_TXT['en'][we.month - 1]} {we.year}, priced {lo} to {hi}, the fee always equalled &euro;0.70 plus 5% of the price rounded to the nearest cent, and the total always equalled price plus fee.</li>
    <li>Price lists and help pages were read on {FEES_CHECKED['en']}. Vinted can change its fees; its checkout is the final word.</li>
  </ul>
</section>
<section id="faq">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="start">
  <h2>See new listings first</h2>
  {cta('en')}
</section>"""
        return page('fees', 'en', 'Vinted Fees 2026: Buyer Protection Fee Calculator | SNYPD',
                    'Vinted’s Buyer Protection fee is €0.70 + 5% of the price, paid by the buyer; selling is free. Calculator, fee table, and a check on real listings.',
                    'VINTED FEES &middot; CALCULATOR', 'Vinted fees: what buyers pay and sellers keep',
                    f'Buying on Vinted costs more than the price on the listing. Here is the Buyer Protection fee for any price, how it differs by Vinted site, and what it means for your margin, checked against {n} real listings.',
                    [('answer', 'Short answer'), ('calculator', 'Calculator'), ('table', 'Fee table'), ('bundles', 'Bundles'), ('sites', 'By Vinted site'), ('sellers', 'Sellers'), ('shipping', 'Shipping'), ('resellers', 'For resellers'), ('method', 'How we checked'), ('faq', 'Questions')],
                    body, [faq_ld(faq)])
    faq = [
        ('Qui paie les frais Vinted ?', f'L’acheteur. Les frais de protection acheteurs s’ajoutent au prix au paiement, et l’acheteur paie aussi la livraison. Vendre est gratuit : le vendeur reçoit le prix complet de l’article (<a href="{S["free_fr"]}" rel="noopener">aide Vinted</a>).'),
        ('Combien coûtent les frais Vinted sur un article à 20&nbsp;&euro; ?', f'{m2(fee_cents(ex), "fr")} : 0,70&nbsp;&euro; plus 5&nbsp;% de 20&nbsp;&euro;. L’acheteur paie {m2(ex + fee_cents(ex), "fr")} hors livraison.'),
        ('Pourquoi les frais sont-ils si élevés sur les petits prix ?', f'Parce que 0,70&nbsp;&euro; sont fixes. Sur un article à {m2(small, "fr")}, les frais font {pct1(fee_cents(small), small, "fr")} du prix ; sur un article à {m2(big, "fr")}, {pct1(fee_cents(big), big, "fr")}.'),
        ('La TVA est-elle comprise dans les frais Vinted ?', f'Oui. Vinted indique que le total des frais Vinted, TVA incluse, est ajouté au prix final au paiement (<a href="{S["fr_help"]}" rel="noopener">aide Vinted</a>).'),
        ('Peut-on éviter les frais de protection acheteurs ?', f'Seulement en payant hors de Vinted, et tu n’es alors plus protégé : Vinted indique que les paiements effectués en dehors de son système ne sont pas couverts (<a href="{S["safe_fr"]}" rel="noopener">aide Vinted</a>). Acheter plusieurs articles au même vendeur en lot est la façon normale de ne payer les 0,70&nbsp;&euro; qu’une fois.'),
    ]
    body = f"""
<section id="reponse">
  <h2>Réponse courte</h2>
  <div class="lg-box lg-mint"><p>Sur les sites Vinted en euros, l’acheteur paie des <strong>frais de protection acheteurs de 0,70&nbsp;&euro; plus 5&nbsp;% du prix de l’article</strong>, TVA incluse, en plus du prix et de la livraison. Vendre est gratuit : le vendeur reçoit le prix complet. Sur un article à 20&nbsp;&euro;, les frais sont de {m2(fee_cents(ex), 'fr')}, donc l’acheteur paie {m2(ex + fee_cents(ex), 'fr')} hors livraison. Nous avons vérifié la règle sur les {n} annonces vinted.be vues par SNYPD du {date_txt(ws.isoformat(), 'fr')} au {date_txt(we.isoformat(), 'fr')} : tous les frais correspondaient au centime près.</p></div>
</section>
<section id="calculateur">
  <h2>Calculateur des frais Vinted</h2>
  <p>Saisis le prix de l’article tel qu’il apparaît sur l’annonce.</p>
  {calc}
  <p class="ct-note">Applique la règle des grilles tarifaires de Vinted : 0,70&nbsp;&euro; (ou 0,70&nbsp;$ sur vinted.com) plus 5&nbsp;% du prix, arrondi au centime le plus proche. La livraison s’ajoute et dépend du colis et du transporteur. Le paiement Vinted affiche toujours le total exact ; Vinted décrit cette règle comme ce qui est facturé « généralement ».</p>
</section>
<section id="tableau">
  <h2>Les frais aux prix courants</h2>
  {table(['PRIX DE L’ARTICLE', 'FRAIS DE PROTECTION', 'L’ACHETEUR PAIE (HORS LIVRAISON)', 'FRAIS EN % DU PRIX'], rows)}
  <p>Les 0,70&nbsp;&euro; fixes expliquent pourquoi les frais pèsent surtout sur les petits prix : {pct1(fee_cents(small), small, 'fr')} d’un article à {m2(small, 'fr')}, mais {pct1(fee_cents(big), big, 'fr')} d’un article à {m2(big, 'fr')}.</p>
</section>
<section id="lots">
  <h2>En lot, la partie fixe n’est payée qu’une fois</h2>
  <p>La grille tarifaire de Vinted applique les frais au prix de l’article <em>ou du lot</em>. Achète {nb} articles à {m2(b1, 'fr')} chez le même vendeur séparément et les frais font {m2(sep, 'fr')} ; achète-les en un seul lot et les frais sont de {m2(bun, 'fr')}, soit {m2(sep - bun, 'fr')} d’économie.</p>
</section>
<section id="sites">
  <h2>Les frais selon le site Vinted</h2>
  <ul>
    <li><strong>vinted.fr, vinted.de, vinted.nl, vinted.it, vinted.es :</strong> 5&nbsp;% + 0,70&nbsp;&euro;, selon la grille tarifaire de chaque site (<a href="{S['fr_list']}" rel="noopener">vinted.fr</a>). <strong>vinted.be :</strong> pareil, vérifié sur {n} annonces réelles.</li>
    <li><strong>vinted.com (États-Unis) :</strong> 0,70&nbsp;$ plus 5&nbsp;% du prix convenu, hors livraison (<a href="{S['us_list']}" rel="noopener">grille tarifaire</a>). Non vérifié sur nos données.</li>
    <li><strong>vinted.co.uk :</strong> une fourchette, de 3 à 8&nbsp;% + 0,30 à 0,80&nbsp;&pound;, TVA incluse, selon l’article, le montant et le type de commande (<a href="{S['uk_list']}" rel="noopener">grille tarifaire</a>). Pas de calcul exact possible ; le paiement affiche les frais.</li>
  </ul>
  <p>Les autres sites Vinted publient leur propre grille tarifaire ; vérifie la tienne avant de te fier à ces chiffres.</p>
</section>
<section id="vendeurs">
  <h2>Ce que paient les vendeurs</h2>
  <p>Rien pour mettre en ligne ni pour vendre : Vinted indique que vendre est gratuit et que le vendeur garde le prix complet (<a href="{S['free_fr']}" rel="noopener">aide Vinted</a>). Le vendeur ne paie que s’il choisit une option de visibilité, comme le Boost ou la Vitrine ; la grille tarifaire précise que leur prix dépend de la durée, du prix de l’article et de la zone de diffusion.</p>
</section>
<section id="livraison">
  <h2>Qui paie la livraison</h2>
  <p>L’acheteur, au paiement, quand il achète avec le bouton Acheter. Le prix dépend de la taille du colis et de la localisation de l’acheteur et du vendeur. Les frais de port s’affichent au paiement et s’ajoutent au total (<a href="{S['ship_fr']}" rel="noopener">aide Vinted</a>).</p>
</section>
<section id="revendeurs">
  <h2>Pour les revendeurs : compte le vrai prix d’achat</h2>
  <p>Ton stock te coûte le prix, plus les frais de protection acheteurs, plus la livraison. Un article « pas cher » à 5&nbsp;&euro; coûte en réalité {m2(small + fee_cents(small), 'fr')} hors livraison. Le tableau de bord SNYPD affiche le prix de chaque nouvelle annonce protection acheteurs incluse, et son Market Report montre le prix demandé typique selon l’état, pour voir ta marge avant d’acheter. Voir aussi <a href="/fr/guide-prix-vinted">les prix Vinted typiques</a>.</p>
  {figure('feed', 'fr')}
</section>
<section id="methode">
  <h2>Comment nous avons vérifié</h2>
  <ul>
    <li>SNYPD enregistre le prix, les frais et le total indiqués par Vinted pour chaque annonce qu’il voit. Sur {n} annonces vinted.be vues du {date_txt(ws.isoformat(), 'fr')} au {date_txt(we.isoformat(), 'fr')}, de {lo} à {hi}, les frais étaient toujours égaux à 0,70&nbsp;&euro; plus 5&nbsp;% du prix arrondi au centime, et le total toujours égal au prix plus les frais.</li>
    <li>Grilles tarifaires et pages d’aide lues le {FEES_CHECKED['fr']}. Vinted peut changer ses frais ; le total affiché au paiement fait foi.</li>
  </ul>
</section>
<section id="questions">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="essayer">
  <h2>Vois les nouvelles annonces en premier</h2>
  {cta('fr')}
</section>"""
    return page('fees', 'fr', 'Frais Vinted 2026 : calcul de la protection acheteurs | SNYPD',
                'Les frais Vinted : 0,70 € + 5 % du prix, payés par l’acheteur ; vendre est gratuit. Calculateur, tableau des frais et vérification sur de vraies annonces.',
                'FRAIS VINTED &middot; CALCULATEUR', 'Frais Vinted : ce que paie l’acheteur, ce que garde le vendeur',
                f'Acheter sur Vinted coûte plus que le prix affiché. Voici les frais de protection acheteurs pour n’importe quel prix, les différences entre sites Vinted et ce que ça change pour ta marge, vérifiés sur {n} annonces réelles.',
                [('reponse', 'Réponse courte'), ('calculateur', 'Calculateur'), ('tableau', 'Tableau des frais'), ('lots', 'Lots'), ('sites', 'Par site Vinted'), ('vendeurs', 'Vendeurs'), ('livraison', 'Livraison'), ('revendeurs', 'Revendeurs'), ('methode', 'Vérification'), ('questions', 'Questions')],
                body, [faq_ld(faq)])


# ------------------------------------------------------------------ page: notifications not working
# Every fact from Vinted's own help centre, read in each language on 9 Oct 2026: help 435 (saved
# searches: only a "+N" counter in the search bar, unlimited, removed after 6 months unopened) and
# help 433 (the list of notification triggers, which has no saved-search item; app menu names;
# the daily limit for non-priority notifications). Re-check both before changing NOTWORK_CHECKED.
NOTWORK_CHECKED = '2026-10-09'
_VH = {'en': 'https://www.vinted.co.uk/help/', 'fr': 'https://www.vinted.fr/help/', 'de': 'https://www.vinted.de/help/',
       'nl': 'https://www.vinted.nl/help/', 'it': 'https://www.vinted.it/help/', 'es': 'https://www.vinted.es/help/'}
NOTWORK = {
    'en': dict(
        title='Vinted saved search notifications not working? Why, and the fix | SNYPD',
        desc='Vinted saved searches do not send a push for each new listing: Vinted only shows a "+" counter in the search bar. What Vinted does notify you about, the settings to check, and how to get a push for every new match.',
        eyebrow='VINTED NOTIFICATIONS', h1='Vinted not notifying you about new listings? Here is why.',
        lead='Vinted&rsquo;s saved searches do not send a push notification for every new listing. Vinted&rsquo;s own help centre describes only a counter in the search bar. Below: what Vinted does notify you about, the settings to check if other notifications stopped too, and how to get a push for every new match.',
        toc=[('short', 'Short answer'), ('notifies', 'What Vinted notifies'), ('settings', 'Check your settings'), ('every', 'A push for every listing'), ('faq', 'Questions')],
        h_short='The short answer', h_notifies='What Vinted does send notifications for', h_settings='If other Vinted notifications stopped too', h_every='How to get a push for every new listing', h_faq='Questions', h_start='Try it on one search',
        short=('When you save a search, Vinted shows a number with a plus next to it the next time you open the search bar: the new listings since you last looked. Opening the search resets it (<a href="{h435}" rel="nofollow">Vinted help: saved searches</a>). '
               'New listings in a saved search are not on Vinted&rsquo;s list of push notification triggers (<a href="{h433}" rel="nofollow">Vinted help: managing notifications</a>). So if you expected a push for each new listing, nothing on your phone is broken. Both pages checked {checked}.'),
        notifies_intro='According to Vinted&rsquo;s help centre, you get a notification when:',
        triggers=['a member you follow lists a new item', 'the price of an item in your favourites drops', 'an item in your favourites sells', 'someone favourites an item you listed',
                  'someone starts following you', 'you get feedback from another member', 'you get a new message', 'Vinted sends you news'],
        notifies_tip='Two of these help buyers: follow sellers whose style you like, and favourite items you want, to hear when their price drops. Neither covers brand-new listings from people you don&rsquo;t follow.',
        settings_steps=['In the Vinted app, go to your profile, then <strong>Settings</strong>, then <strong>Push notifications</strong>. The first option turns all of them on or off.',
                        'In the same list, <strong>Other notifications</strong> has a daily limit for notifications that are not high priority. A low limit means some stop arriving for the rest of the day.',
                        'On the phone: iPhone <strong>Settings &gt; Notifications &gt; Vinted</strong>; Android <strong>Settings &gt; Apps &gt; Vinted &gt; Notifications</strong> (names differ by phone maker). Focus or Do Not Disturb also hides them.',
                        'On the Vinted website, notifications cannot be turned off; you can only choose which ones also arrive by email.'],
        settings_more='Saved searches you never open are removed after 6 months, and you can save as many as you like (<a href="{h435}" rel="nofollow">Vinted help</a>).',
        every=('SNYPD watches a Vinted search for you and sends a push notification when a new listing matches. Paste the same search link you would save on Vinted, filters included, or type a few words. '
               'SNYPD checks it about every 30 seconds and the alert opens the listing on Vinted. It never asks for your Vinted password and never buys for you. On iPhone, alerts work once SNYPD is on your Home Screen. '
               'More: <a href="{notify}">Vinted saved search alerts</a> and <a href="{bot}">how SNYPD works</a>.'),
        faq=[('Why doesn&rsquo;t Vinted notify me about my saved search?', 'Because Vinted&rsquo;s saved searches only show a counter (a number with a plus) in the search bar the next time you open it. New listings in a saved search are not among the push notifications Vinted lists in its help centre.'),
             ('Does Vinted send push notifications for new items?', 'Only for members you follow: when someone you follow lists a new item. Not for new listings that match a saved search.'),
             ('How do I turn Vinted notifications back on?', 'In the app: profile, Settings, Push notifications. Then check your phone&rsquo;s settings for Vinted and the daily limit under Other notifications.'),
             ('How do I get notified when a new item is listed on Vinted?', 'Use a tool that watches the search for you. SNYPD checks a Vinted search about every 30 seconds and sends a push for each new match; the first search is free, 24/7 for the first @@trial_days@@ days.')]),
    'fr': dict(
        title='Notifications Vinted qui ne marchent pas : pourquoi, et la solution | SNYPD',
        desc='Les recherches sauvegardées Vinted n’envoient pas de notification pour chaque nouvelle annonce : Vinted affiche seulement un compteur « + ». Ce que Vinted notifie, les réglages à vérifier, et comment être alerté à chaque annonce.',
        eyebrow='NOTIFICATIONS VINTED', h1='Vinted ne te prévient pas des nouvelles annonces ? Voici pourquoi.',
        lead='Les recherches sauvegardées de Vinted n’envoient pas de notification push pour chaque nouvelle annonce. Le centre d’aide de Vinted ne décrit qu’un compteur dans la barre de recherche. Ci-dessous : ce que Vinted notifie vraiment, les réglages à vérifier si d’autres notifications ont aussi disparu, et comment recevoir une notification à chaque nouvelle annonce.',
        toc=[('reponse', 'En bref'), ('notifie', 'Ce que Vinted notifie'), ('reglages', 'Tes réglages'), ('chaque', 'Une alerte par annonce'), ('questions', 'Questions')],
        h_short='La réponse courte', h_notifies='Ce que Vinted notifie', h_settings='Si d’autres notifications Vinted ont aussi disparu', h_every='Recevoir une notification à chaque nouvelle annonce', h_faq='Questions', h_start='Essaie sur une recherche',
        short=('Quand tu sauvegardes une recherche, Vinted affiche un nombre suivi d’un signe plus à côté la prochaine fois que tu ouvres la barre de recherche : les nouvelles annonces depuis ta dernière visite. Ouvrir la recherche le remet à zéro (<a href="{h435}" rel="nofollow">aide Vinted : recherches sauvegardées</a>). '
               'Les nouvelles annonces d’une recherche sauvegardée ne font pas partie des notifications push listées par Vinted (<a href="{h433}" rel="nofollow">aide Vinted : notifications</a>). Si tu attendais une notification par annonce, ton téléphone n’est donc pas en panne. Pages vérifiées le {checked}.'),
        notifies_intro='Selon le centre d’aide de Vinted, tu reçois une notification quand :',
        triggers=['un membre que tu suis met en ligne un nouvel article', 'le prix d’un article de tes favoris baisse', 'un article de tes favoris est vendu', 'un membre ajoute un de tes articles à ses favoris',
                  'un membre commence à te suivre', 'un membre te laisse une évaluation', 'tu reçois un nouveau message', 'Vinted t’envoie un message'],
        notifies_tip='Deux d’entre elles aident les acheteurs : suis les vendeurs dont tu aimes le style, et mets en favoris les articles que tu veux pour savoir quand leur prix baisse. Aucune ne couvre les nouvelles annonces de membres que tu ne suis pas.',
        settings_steps=['Dans l’app Vinted, va sur ton profil, puis <strong>Paramètres</strong>, puis <strong>Notifications (Mobile)</strong>. La première option les active ou les coupe toutes.',
                        'Dans la même liste, <strong>Notifications secondaires</strong> fixe un nombre maximal par jour de notifications non prioritaires. Avec une limite basse, certaines n’arrivent plus jusqu’au lendemain.',
                        'Sur le téléphone : iPhone <strong>Réglages &gt; Notifications &gt; Vinted</strong> ; Android <strong>Paramètres &gt; Applications &gt; Vinted &gt; Notifications</strong> (les noms varient selon la marque). Les modes Concentration ou Ne pas déranger les masquent aussi.',
                        'Sur le site Vinted, les notifications ne peuvent pas être désactivées ; tu peux seulement choisir celles qui arrivent aussi par e-mail.'],
        settings_more='Les recherches sauvegardées que tu n’ouvres jamais sont retirées au bout de 6 mois, et tu peux en sauvegarder autant que tu veux (<a href="{h435}" rel="nofollow">aide Vinted</a>).',
        every=('SNYPD surveille une recherche Vinted pour toi et t’envoie une notification push quand une nouvelle annonce correspond. Colle le même lien de recherche que tu sauvegarderais sur Vinted, filtres compris, ou tape quelques mots. '
               'SNYPD la vérifie environ toutes les 30 secondes et l’alerte ouvre l’annonce sur Vinted. Il ne demande jamais ton mot de passe Vinted et n’achète jamais à ta place. Sur iPhone, les alertes marchent une fois SNYPD ajouté à l’écran d’accueil. '
               'Plus de détails : <a href="{notify}">alertes de recherche Vinted</a> et <a href="{bot}">comment marche SNYPD</a>.'),
        faq=[('Pourquoi Vinted ne me prévient pas pour ma recherche sauvegardée ?', 'Parce que les recherches sauvegardées de Vinted affichent seulement un compteur (un nombre suivi d’un plus) dans la barre de recherche la prochaine fois que tu l’ouvres. Les nouvelles annonces d’une recherche sauvegardée ne figurent pas parmi les notifications push listées dans le centre d’aide de Vinted.'),
             ('Vinted envoie-t-il des notifications pour les nouveaux articles ?', 'Seulement pour les membres que tu suis : quand un membre que tu suis met en ligne un article. Pas pour les nouvelles annonces qui correspondent à une recherche sauvegardée.'),
             ('Comment réactiver les notifications Vinted ?', 'Dans l’app : profil, Paramètres, Notifications (Mobile). Vérifie ensuite les réglages de ton téléphone pour Vinted et la limite quotidienne dans Notifications secondaires.'),
             ('Comment être prévenu dès qu’un article est mis en ligne sur Vinted ?', 'Avec un outil qui surveille la recherche pour toi. SNYPD vérifie une recherche Vinted environ toutes les 30 secondes et envoie une notification push pour chaque nouvelle annonce ; la première recherche est gratuite, 24h/24 pendant les @@trial_days@@ premiers jours.')]),
    'de': dict(
        title='Vinted-Benachrichtigung funktioniert nicht? Der Grund und die Lösung | SNYPD',
        desc='Gespeicherte Suchen bei Vinted schicken keine Push-Benachrichtigung für jede neue Anzeige: Vinted zeigt nur einen „+“-Zähler in der Suche. Wofür Vinted benachrichtigt, welche Einstellungen du prüfen solltest und wie du bei jeder neuen Anzeige Bescheid bekommst.',
        eyebrow='VINTED-BENACHRICHTIGUNGEN', h1='Vinted sagt dir nicht Bescheid, wenn neue Artikel kommen? Darum.',
        lead='Gespeicherte Suchen bei Vinted schicken keine Push-Benachrichtigung für jede neue Anzeige. Vinteds eigenes Hilfe-Center beschreibt nur einen Zähler im Suchfeld. Hier steht, wofür Vinted wirklich benachrichtigt, welche Einstellungen du prüfen solltest, wenn auch andere Benachrichtigungen fehlen, und wie du bei jeder neuen passenden Anzeige eine Push-Benachrichtigung bekommst.',
        toc=[('kurz', 'Kurze Antwort'), ('wofuer', 'Wofür Vinted benachrichtigt'), ('einstellungen', 'Einstellungen prüfen'), ('jede', 'Push für jede Anzeige'), ('fragen', 'Fragen')],
        h_short='Die kurze Antwort', h_notifies='Wofür Vinted Benachrichtigungen schickt', h_settings='Wenn auch andere Vinted-Benachrichtigungen fehlen', h_every='So bekommst du für jede neue Anzeige eine Push-Benachrichtigung', h_faq='Fragen', h_start='Probier es mit einer Suche',
        short=('Wenn du eine Suche speicherst, zeigt Vinted beim nächsten Öffnen des Suchfelds eine Zahl mit einem Pluszeichen daneben: die neuen Artikel seit deinem letzten Blick. Öffnest du die Suche, steht der Zähler wieder auf null (<a href="{h435}" rel="nofollow">Vinted-Hilfe: gespeicherte Suchen</a>). '
               'Neue Anzeigen in einer gespeicherten Suche stehen nicht auf Vinteds Liste der Push-Benachrichtigungen (<a href="{h433}" rel="nofollow">Vinted-Hilfe: Benachrichtigungen</a>). Wenn du für jede neue Anzeige eine Benachrichtigung erwartet hast, ist an deinem Handy also nichts kaputt. Beide Seiten geprüft am {checked}.'),
        notifies_intro='Laut Vinteds Hilfe-Center bekommst du eine Benachrichtigung, wenn:',
        triggers=['ein Mitglied, dem du folgst, einen neuen Artikel hochlädt', 'der Preis eines deiner Favoriten gesenkt wird', 'einer deiner Favoriten verkauft wird', 'jemand einen deiner Artikel favorisiert',
                  'dir jemand neu folgt', 'du eine Bewertung bekommst', 'du eine neue Nachricht bekommst', 'Vinted dir Neuigkeiten schickt'],
        notifies_tip='Zwei davon helfen Käufern: Folge Verkäufern, deren Stil dir gefällt, und favorisiere Artikel, die du willst, um von Preissenkungen zu erfahren. Keine davon deckt neue Anzeigen von Leuten ab, denen du nicht folgst.',
        settings_steps=['In der Vinted-App: <strong>Mein Profil</strong>, dann <strong>Meine Einstellungen</strong>, dann <strong>Push-Benachrichtigungen</strong>. Die erste Option schaltet alle ein oder aus.',
                        'In derselben Liste legt <strong>Andere Benachrichtigungen</strong> ein Tageslimit für nicht vorrangige Benachrichtigungen fest. Bei einem niedrigen Limit kommen manche bis zum nächsten Tag nicht mehr an.',
                        'Am Handy: iPhone <strong>Einstellungen &gt; Mitteilungen &gt; Vinted</strong>; Android <strong>Einstellungen &gt; Apps &gt; Vinted &gt; Benachrichtigungen</strong> (die Namen unterscheiden sich je nach Hersteller). Fokus oder „Nicht stören“ blenden sie ebenfalls aus.',
                        'Auf der Vinted-Website lassen sich Benachrichtigungen nicht abschalten; du kannst nur wählen, welche zusätzlich per E-Mail kommen.'],
        settings_more='Gespeicherte Suchen, die du 6 Monate lang nicht öffnest, werden entfernt, und du kannst so viele speichern, wie du möchtest (<a href="{h435}" rel="nofollow">Vinted-Hilfe</a>).',
        every=('SNYPD beobachtet eine Vinted-Suche für dich und schickt dir eine Push-Benachrichtigung, sobald eine neue Anzeige passt. Füge denselben Suchlink ein, den du bei Vinted speichern würdest, mit allen Filtern, oder tippe ein paar Wörter. '
               'SNYPD prüft ihn etwa alle 30 Sekunden, und die Benachrichtigung öffnet die Anzeige auf Vinted. SNYPD fragt nie nach deinem Vinted-Passwort und kauft nie für dich. Auf dem iPhone funktionieren die Benachrichtigungen, sobald SNYPD auf dem Home-Bildschirm ist. '
               'Mehr: <a href="{bot}">so funktioniert SNYPD</a>.'),
        faq=[('Warum benachrichtigt mich Vinted nicht über meine gespeicherte Suche?', 'Weil gespeicherte Suchen bei Vinted nur einen Zähler (eine Zahl mit Pluszeichen) im Suchfeld zeigen, wenn du es das nächste Mal öffnest. Neue Anzeigen in einer gespeicherten Suche gehören nicht zu den Push-Benachrichtigungen, die Vinted in seinem Hilfe-Center aufzählt.'),
             ('Schickt Vinted Benachrichtigungen für neue Artikel?', 'Nur für Mitglieder, denen du folgst: wenn jemand, dem du folgst, einen neuen Artikel hochlädt. Nicht für neue Anzeigen, die zu einer gespeicherten Suche passen.'),
             ('Wie schalte ich Vinted-Benachrichtigungen wieder ein?', 'In der App: Mein Profil, Meine Einstellungen, Push-Benachrichtigungen. Prüfe danach die Handy-Einstellungen für Vinted und das Tageslimit unter Andere Benachrichtigungen.'),
             ('Wie werde ich benachrichtigt, wenn ein neuer Artikel bei Vinted eingestellt wird?', 'Mit einem Tool, das die Suche für dich beobachtet. SNYPD prüft eine Vinted-Suche etwa alle 30 Sekunden und schickt für jeden neuen Treffer eine Push-Benachrichtigung; die erste Suche ist kostenlos, in den ersten @@trial_days@@ Tagen rund um die Uhr.')]),
    'nl': dict(
        title='Vinted-meldingen werken niet? Waarom, en de oplossing | SNYPD',
        desc='Bewaarde zoekopdrachten op Vinted sturen geen pushmelding voor elke nieuwe advertentie: Vinted toont alleen een "+"-teller in de zoekbalk. Waarvoor Vinted wel meldingen stuurt, welke instellingen je checkt en hoe je bij elke nieuwe advertentie een melding krijgt.',
        eyebrow='VINTED-MELDINGEN', h1='Krijg je geen melding van Vinted bij nieuwe artikelen? Daarom.',
        lead='Bewaarde zoekopdrachten op Vinted sturen geen pushmelding voor elke nieuwe advertentie. Het eigen helpcentrum van Vinted beschrijft alleen een teller in de zoekbalk. Hieronder: waarvoor Vinted wel meldingen stuurt, welke instellingen je checkt als ook andere meldingen wegblijven, en hoe je voor elke nieuwe passende advertentie een pushmelding krijgt.',
        toc=[('kort', 'Kort antwoord'), ('waarvoor', 'Waarvoor Vinted meldt'), ('instellingen', 'Instellingen checken'), ('elke', 'Melding per advertentie'), ('vragen', 'Vragen')],
        h_short='Het korte antwoord', h_notifies='Waarvoor Vinted wel meldingen stuurt', h_settings='Als ook andere Vinted-meldingen wegblijven', h_every='Zo krijg je een pushmelding voor elke nieuwe advertentie', h_faq='Vragen', h_start='Probeer het met één zoekopdracht',
        short=('Als je een zoekopdracht bewaart, toont Vinted er de volgende keer dat je de zoekbalk opent een getal met een plusteken naast: de nieuwe artikelen sinds je laatste bezoek. Open je de zoekopdracht, dan staat de teller weer op nul (<a href="{h435}" rel="nofollow">Vinted-hulp: zoekopdrachten bewaren</a>). '
               'Nieuwe advertenties in een bewaarde zoekopdracht staan niet in de lijst van pushmeldingen van Vinted (<a href="{h433}" rel="nofollow">Vinted-hulp: meldingen</a>). Verwachtte je een melding per advertentie, dan is er aan je telefoon dus niets kapot. Beide pagina&rsquo;s gecontroleerd op {checked}.'),
        notifies_intro='Volgens het helpcentrum van Vinted krijg je een melding wanneer:',
        triggers=['een lid dat je volgt een nieuw artikel uploadt', 'de prijs van een van je favorieten daalt', 'een van je favorieten verkocht is', 'iemand een artikel van jou als favoriet bewaart',
                  'iemand je begint te volgen', 'je een beoordeling krijgt', 'je een nieuw bericht krijgt', 'Vinted je nieuws stuurt'],
        notifies_tip='Twee daarvan helpen kopers: volg verkopers van wie je de stijl leuk vindt, en bewaar artikelen die je wilt als favoriet om te horen wanneer de prijs daalt. Geen enkele dekt nieuwe advertenties van mensen die je niet volgt.',
        settings_steps=['In de Vinted-app: ga naar je <strong>profiel</strong>, dan <strong>Mijn instellingen</strong>, dan <strong>Pushmeldingen</strong>. De eerste optie zet ze allemaal aan of uit.',
                        'In dezelfde lijst stelt <strong>Minder belangrijke notificaties</strong> een daglimiet in voor meldingen zonder hoge prioriteit. Met een lage limiet komen sommige pas de volgende dag weer binnen.',
                        'Op je telefoon: iPhone <strong>Instellingen &gt; Berichtgeving &gt; Vinted</strong>; Android <strong>Instellingen &gt; Apps &gt; Vinted &gt; Meldingen</strong> (namen verschillen per merk). Focus of Niet storen verbergt ze ook.',
                        'Op de Vinted-website kun je meldingen niet uitzetten; je kiest alleen welke ook per e-mail komen.'],
        settings_more='Bewaarde zoekopdrachten die je 6 maanden lang niet bekijkt, worden verwijderd, en je kunt er zoveel bewaren als je wilt (<a href="{h435}" rel="nofollow">Vinted-hulp</a>).',
        every=('SNYPD houdt een Vinted-zoekopdracht voor je in de gaten en stuurt een pushmelding zodra er een nieuwe passende advertentie is. Plak dezelfde zoeklink die je op Vinted zou bewaren, met filters, of typ een paar woorden. '
               'SNYPD controleert hem ongeveer elke 30 seconden en de melding opent de advertentie op Vinted. SNYPD vraagt nooit om je Vinted-wachtwoord en koopt nooit voor je. Op een iPhone werken meldingen zodra SNYPD op je beginscherm staat. '
               'Meer: <a href="{bot}">zo werkt SNYPD</a>.'),
        faq=[('Waarom krijg ik geen melding van Vinted voor mijn bewaarde zoekopdracht?', 'Omdat bewaarde zoekopdrachten op Vinted alleen een teller (een getal met een plusteken) in de zoekbalk tonen als je die de volgende keer opent. Nieuwe advertenties in een bewaarde zoekopdracht horen niet bij de pushmeldingen die Vinted in zijn helpcentrum noemt.'),
             ('Stuurt Vinted meldingen voor nieuwe artikelen?', 'Alleen voor leden die je volgt: als iemand die je volgt een nieuw artikel uploadt. Niet voor nieuwe advertenties die bij een bewaarde zoekopdracht passen.'),
             ('Hoe zet ik Vinted-meldingen weer aan?', 'In de app: profiel, Mijn instellingen, Pushmeldingen. Check daarna de instellingen van je telefoon voor Vinted en de daglimiet onder Minder belangrijke notificaties.'),
             ('Hoe krijg ik een melding als er een nieuw artikel op Vinted komt?', 'Met een tool die de zoekopdracht voor je in de gaten houdt. SNYPD controleert een Vinted-zoekopdracht ongeveer elke 30 seconden en stuurt voor elke nieuwe treffer een pushmelding; de eerste zoekopdracht is gratis, de eerste @@trial_days@@ dagen 24/7.')]),
    'it': dict(
        title='Notifiche Vinted non funzionano? Impostazioni e ricerche salvate | SNYPD',
        desc='Non ricevi notifiche Vinted? Controlla le impostazioni push e scopri la differenza tra avvisi per i preferiti e nuovi risultati delle ricerche salvate.',
        eyebrow='NOTIFICHE VINTED', h1='Vinted non ti avvisa dei nuovi annunci? Ecco perché.',
        lead='Le ricerche salvate su Vinted non inviano una notifica push per ogni nuovo annuncio. Il centro assistenza di Vinted descrive solo un contatore nella barra di ricerca. Qui sotto: per cosa Vinted invia davvero notifiche, le impostazioni da controllare se sono sparite anche altre notifiche e come ricevere una notifica push per ogni nuovo annuncio che corrisponde.',
        toc=[('breve', 'In breve'), ('cosa', 'Cosa notifica Vinted'), ('impostazioni', 'Le impostazioni'), ('ogni', 'Una notifica per annuncio'), ('domande', 'Domande')],
        h_short='La risposta breve', h_notifies='Per cosa Vinted invia notifiche', h_settings='Se sono sparite anche altre notifiche di Vinted', h_every='Come ricevere una notifica per ogni nuovo annuncio', h_faq='Domande', h_start='Provalo con una ricerca',
        short=('Quando salvi una ricerca, la prossima volta che apri la barra di ricerca Vinted mostra accanto un numero con il segno più: i nuovi annunci dall&rsquo;ultima volta. Aprendo la ricerca il contatore si azzera (<a href="{h435}" rel="nofollow">assistenza Vinted: ricerche salvate</a>). '
               'I nuovi annunci di una ricerca salvata non sono nell&rsquo;elenco delle notifiche push di Vinted (<a href="{h433}" rel="nofollow">assistenza Vinted: notifiche</a>). Se ti aspettavi una notifica per ogni annuncio, il tuo telefono non ha nessun problema. Pagine controllate il {checked}.'),
        notifies_intro='Secondo il centro assistenza di Vinted, ricevi una notifica quando:',
        triggers=['un utente che segui carica un nuovo articolo', 'il prezzo di un articolo nei tuoi Preferiti scende', 'un articolo nei tuoi Preferiti viene venduto', 'qualcuno aggiunge ai Preferiti un tuo articolo',
                  'qualcuno inizia a seguirti', 'ricevi una recensione', 'ricevi un nuovo messaggio', 'Vinted ti invia novità'],
        notifies_tip='Due di queste aiutano chi compra: segui i venditori di cui ti piace lo stile e aggiungi ai Preferiti gli articoli che vuoi, per sapere quando il prezzo scende. Nessuna copre i nuovi annunci di persone che non segui.',
        settings_steps=['Nell&rsquo;app Vinted vai sul tuo <strong>profilo</strong>, poi <strong>Impostazioni</strong>, poi <strong>Notifiche push</strong>. La prima opzione le attiva o le disattiva tutte.',
                        'Nella stessa lista, <strong>Altre notifiche</strong> imposta un limite giornaliero per le notifiche senza priorità alta. Con un limite basso alcune non arrivano più fino al giorno dopo.',
                        'Sul telefono: iPhone <strong>Impostazioni &gt; Notifiche &gt; Vinted</strong>; Android <strong>Impostazioni &gt; App &gt; Vinted &gt; Notifiche</strong> (i nomi cambiano secondo il produttore). Anche Full immersion o Non disturbare le nascondono.',
                        'Sul sito Vinted le notifiche non si possono disattivare; puoi solo scegliere quali ricevere anche via email.'],
        settings_more='Le ricerche salvate che non apri per 6 mesi non sono più visibili, e puoi salvarne quante vuoi (<a href="{h435}" rel="nofollow">assistenza Vinted</a>).',
        every=('SNYPD controlla una ricerca Vinted per te e ti invia una notifica push quando c&rsquo;è un nuovo annuncio che corrisponde. Incolla lo stesso link di ricerca che salveresti su Vinted, filtri compresi, oppure scrivi qualche parola. '
               'SNYPD lo controlla circa ogni 30 secondi e la notifica apre l&rsquo;annuncio su Vinted. Non chiede mai la tua password di Vinted e non compra mai al posto tuo. Su iPhone le notifiche funzionano una volta aggiunto SNYPD alla schermata Home. '
               'Di più: <a href="{bot}">come funziona SNYPD</a>.'),
        faq=[('Perché Vinted non mi avvisa per la mia ricerca salvata?', 'Perché le ricerche salvate di Vinted mostrano solo un contatore (un numero con il segno più) nella barra di ricerca la volta successiva che la apri. I nuovi annunci di una ricerca salvata non sono tra le notifiche push elencate nel centro assistenza di Vinted.'),
             ('Vinted invia notifiche per i nuovi articoli?', 'Solo per gli utenti che segui: quando qualcuno che segui carica un nuovo articolo. Non per i nuovi annunci che corrispondono a una ricerca salvata.'),
             ('Come riattivo le notifiche di Vinted?', 'Nell&rsquo;app: profilo, Impostazioni, Notifiche push. Poi controlla le impostazioni del telefono per Vinted e il limite giornaliero in Altre notifiche.'),
             ('Come ricevo un avviso quando viene pubblicato un nuovo articolo su Vinted?', 'Con uno strumento che controlla la ricerca per te. SNYPD controlla una ricerca Vinted circa ogni 30 secondi e invia una notifica push per ogni nuovo annuncio; la prima ricerca è gratis, 24 ore su 24 per i primi @@trial_days@@ giorni.')]),
    'es': dict(
        title='¿Las notificaciones de Vinted no funcionan? Por qué, y la solución | SNYPD',
        desc='Las búsquedas guardadas de Vinted no envían una notificación por cada anuncio nuevo: Vinted solo muestra un contador "+" en la barra de búsqueda. Para qué envía notificaciones Vinted, qué ajustes revisar y cómo recibir un aviso con cada anuncio nuevo.',
        eyebrow='NOTIFICACIONES DE VINTED', h1='¿Vinted no te avisa de los anuncios nuevos? Este es el motivo.',
        lead='Las búsquedas guardadas de Vinted no envían una notificación push por cada anuncio nuevo. El propio centro de ayuda de Vinted solo describe un contador en la barra de búsqueda. Aquí: para qué envía Vinted notificaciones de verdad, qué ajustes revisar si también han desaparecido otras notificaciones y cómo recibir una notificación push con cada anuncio nuevo que encaje.',
        toc=[('corta', 'Respuesta corta'), ('que', 'Qué notifica Vinted'), ('ajustes', 'Revisa tus ajustes'), ('cada', 'Un aviso por anuncio'), ('preguntas', 'Preguntas')],
        h_short='La respuesta corta', h_notifies='Para qué envía Vinted notificaciones', h_settings='Si también han desaparecido otras notificaciones de Vinted', h_every='Cómo recibir una notificación con cada anuncio nuevo', h_faq='Preguntas', h_start='Pruébalo con una búsqueda',
        short=('Cuando guardas una búsqueda, la próxima vez que abres la barra de búsqueda Vinted muestra a su lado un número con el signo "+": los anuncios nuevos desde tu última visita. Al abrir la búsqueda, el contador vuelve a cero (<a href="{h435}" rel="nofollow">ayuda de Vinted: búsquedas guardadas</a>). '
               'Los anuncios nuevos de una búsqueda guardada no están en la lista de notificaciones push de Vinted (<a href="{h433}" rel="nofollow">ayuda de Vinted: notificaciones</a>). Si esperabas una notificación por cada anuncio, a tu móvil no le pasa nada. Páginas comprobadas el {checked}.'),
        notifies_intro='Según el centro de ayuda de Vinted, recibes una notificación cuando:',
        triggers=['un miembro al que sigues sube un artículo nuevo', 'baja el precio de un artículo de tus favoritos', 'se vende un artículo de tus favoritos', 'alguien marca como favorito un artículo tuyo',
                  'alguien empieza a seguirte', 'recibes una valoración', 'recibes un mensaje nuevo', 'Vinted te envía novedades'],
        notifies_tip='Dos de ellas ayudan a quien compra: sigue a los vendedores cuyo estilo te gusta y marca como favoritos los artículos que quieres para saber cuándo baja su precio. Ninguna cubre los anuncios nuevos de personas a las que no sigues.',
        settings_steps=['En la app de Vinted, ve a tu <strong>perfil</strong>, luego <strong>Ajustes</strong> y luego <strong>Notificaciones de la app</strong>. La primera opción las activa o desactiva todas.',
                        'En la misma lista, <strong>Otras notificaciones</strong> fija un límite diario para las notificaciones sin prioridad. Con un límite bajo, algunas dejan de llegar hasta el día siguiente.',
                        'En el móvil: iPhone <strong>Ajustes &gt; Notificaciones &gt; Vinted</strong>; Android <strong>Ajustes &gt; Aplicaciones &gt; Vinted &gt; Notificaciones</strong> (los nombres cambian según el fabricante). Los modos Concentración o No molestar también las ocultan.',
                        'En la web de Vinted las notificaciones no se pueden desactivar; solo puedes elegir cuáles te llegan también por email.'],
        settings_more='Las búsquedas guardadas que no abres en 6 meses desaparecen, y puedes guardar tantas como quieras (<a href="{h435}" rel="nofollow">ayuda de Vinted</a>).',
        every=('SNYPD vigila una búsqueda de Vinted por ti y te envía una notificación push cuando aparece un anuncio nuevo que encaja. Pega el mismo enlace de búsqueda que guardarías en Vinted, con filtros incluidos, o escribe unas palabras. '
               'SNYPD lo comprueba más o menos cada 30 segundos y la notificación abre el anuncio en Vinted. Nunca te pide la contraseña de Vinted y nunca compra por ti. En iPhone, las notificaciones funcionan cuando SNYPD está en la pantalla de inicio. '
               'Más: <a href="{bot}">cómo funciona SNYPD</a>.'),
        faq=[('¿Por qué Vinted no me avisa de mi búsqueda guardada?', 'Porque las búsquedas guardadas de Vinted solo muestran un contador (un número con el signo +) en la barra de búsqueda la próxima vez que la abres. Los anuncios nuevos de una búsqueda guardada no están entre las notificaciones push que Vinted enumera en su centro de ayuda.'),
             ('¿Vinted envía notificaciones de artículos nuevos?', 'Solo de los miembros a los que sigues: cuando alguien al que sigues sube un artículo. No de los anuncios nuevos que encajan con una búsqueda guardada.'),
             ('¿Cómo vuelvo a activar las notificaciones de Vinted?', 'En la app: perfil, Ajustes, Notificaciones de la app. Después revisa los ajustes del móvil para Vinted y el límite diario en Otras notificaciones.'),
             ('¿Cómo recibo un aviso cuando se publica un artículo nuevo en Vinted?', 'Con una herramienta que vigile la búsqueda por ti. SNYPD comprueba una búsqueda de Vinted más o menos cada 30 segundos y envía una notificación push por cada anuncio nuevo; la primera búsqueda es gratis, 24/7 durante los 7 primeros días.')]),
}


def page_notwork(lang):
    t = NOTWORK[lang]
    links = {'h435': _VH[lang] + '435', 'h433': _VH[lang] + '433', 'checked': date_txt(NOTWORK_CHECKED, lang),
             'notify': href('notify', lang), 'bot': href('bot', lang)}
    ids = [a for a, _ in t['toc']]
    faq = t['faq']
    body = f"""
<section id="{ids[0]}">
  <h2>{t['h_short']}</h2>
  <div class="lg-box lg-mint"><p>{t['short'].format(**links)}</p></div>
</section>
<section id="{ids[1]}">
  <h2>{t['h_notifies']}</h2>
  <p>{t['notifies_intro']}</p>
  <ul>{''.join('<li>%s</li>' % x for x in t['triggers'])}</ul>
  <p>{t['notifies_tip']}</p>
</section>
<section id="{ids[2]}">
  <h2>{t['h_settings']}</h2>
  <ol>{''.join('<li>%s</li>' % x for x in t['settings_steps'])}</ol>
  <p>{t['settings_more'].format(**links)}</p>
</section>
<section id="{ids[3]}">
  <h2>{t['h_every']}</h2>
  <p>{t['every'].format(**links)}</p>
  {figure('feed', lang) if lang in SHOT_TEXT else ''}
</section>
<section id="{ids[4]}">
  <h2>{t['h_faq']}</h2>
  {faq_html([(html.unescape(q), a) for q, a in faq])}
</section>
<section id="start">
  <h2>{t['h_start']}</h2>
  {cta(lang)}
</section>"""
    return page('notwork', lang, html.unescape(t['title']), html.unescape(t['desc']), t['eyebrow'], t['h1'], t['lead'], t['toc'],
                body, [faq_ld([(html.unescape(q), a) for q, a in faq])])


# ------------------------------------------------------------------ alert hub + comparison, shared parts
def alert_ways_table(lang):
    w = cac.WAYS[lang]
    rows, us = [], None
    for i, r in enumerate(cd.ALERT_WAYS):
        src = r['src'][lang] if isinstance(r['src'], dict) else r['src']
        word = cd.VINTED_HELP_WORD[lang] if isinstance(r['src'], dict) else cd.SOURCE_WORD[lang]
        nm = r['name'][lang] if isinstance(r['name'], dict) else r['name']
        if r.get('us'):
            us = i
        rows.append([nm, r['get'][lang], r['how'][lang], r['cost'][lang],
                     '<a href="%s"%s>%s</a>' % (src, '' if r.get('us') else ' rel="nofollow noopener"', word)])
    return ('<section id="ways"><h2>%s</h2><p>%s</p>%s<p class="ct-note">%s</p></section>'
            % (w['h'], w['intro'].format(date=COMPARE_CHECKED[lang]), table(cd.ALERT_WAYS_HEAD[lang], rows, us_row=us),
               w['note'].format(compare=href('compare', lang))))


def push_setup(lang, sid='push'):
    t = cac.PUSH[lang]
    return ('<section id="%s"><h2>%s</h2><h3>%s</h3><ol>%s</ol><h3>%s</h3><ol>%s</ol><h3>%s</h3><p>%s</p><p class="ct-note">%s</p></section>'
            % (sid, t['h'], t['ios'].upper(), ''.join('<li>%s</li>' % x for x in t['ios_steps']), t['android'].upper(),
               ''.join('<li>%s</li>' % x for x in t['android_steps']), t['desk'].upper(), t['desk_p'], t['why']))


def page_notify_x(lang):
    """The alert hub in German, Dutch, Italian and Spanish (copy: copy_alerts_compare.NOTIFY)."""
    t = cac.NOTIFY[lang]
    ids = [a for a, _ in t['toc']]
    faq = [(q, a.format(date=COMPARE_CHECKED[lang])) for q, a in t['faq']]
    body = (
        '<section id="%s"><h2>%s</h2><div class="lg-box lg-mint"><p>%s</p></div></section>' % (ids[0], t['h_answer'], t['answer'])
        + '<section id="%s"><h2>%s</h2><p>%s</p><blockquote>&ldquo;%s&rdquo;<cite>%s, <a href="%s" rel="nofollow noopener">%s</a></cite></blockquote><ul>%s</ul><p>%s</p></section>'
        % (ids[1], t['h_vinted'], t['vinted_intro'], cd.HELP435_QUOTE[lang], t['cite'], HELP435[lang], cd.HELP435_TITLE[lang],
           ''.join('<li>%s</li>' % b for b in t['bullets']), t['follow'].format(h433=HELP433['en'] if lang in ('nl', 'it') else HELP433[lang]))
        + alert_ways_table(lang).replace('<section id="ways">', '<section id="%s">' % ids[2], 1)
        + '<section id="%s"><h2>%s</h2><ul>%s</ul></section>' % (ids[3], t['h_enough'], ''.join('<li>%s</li>' % b for b in t['enough']))
        + '<section id="%s"><h2>%s</h2><p>%s</p><ol>%s</ol><p>%s</p>%s</section>'
        % (ids[4], t['h_alerts'], t['alerts_intro'], ''.join('<li>%s</li>' % x for x in t['steps']), t['after'].format(bot=href('bot', lang)),
           ' '.join([SPEED_MEASURED[lang], VINTED_LAG[lang]]).join(['<p class="ct-note">', '</p>']))
        + push_setup(lang, ids[5])
        + '<section id="%s"><h2>%s</h2>%s</section>' % (ids[6], t['h_faq'], faq_html(faq))
        + '<section id="start"><h2>%s</h2>%s</section>' % (t['h_start'], cta(lang)))
    return page('notify', lang, t['title'], t['desc'], t['eyebrow'], t['h1'], t['lead'], t['toc'], body, [faq_ld(faq)])


def page_compare_x(lang):
    """The comparison in German, Dutch, Italian and Spanish (copy: copy_alerts_compare.COMPARE)."""
    t = cac.COMPARE[lang]
    n = cd.others_count()
    f = dict(n=n, total=n + 1, date=COMPARE_CHECKED[lang], short=COMPARE_CHECKED_SHORT[lang], email=EMAIL)
    faq = [(q, a.format(**f)) for q, a in t['faq']]
    body = (
        '<section id="disclosure"><div class="lg-box lg-mint"><p>%s</p></div></section>' % t['disclosure'].format(**f)
        + '<section id="table"><h2>%s</h2>%s%s<p class="ct-note">%s</p></section>' % (t['h_table'].format(**f), compare_table(lang), compare_duel(lang), t['table_note'])
        + '<section id="look"><h2>%s</h2><ul class="fit-list">%s</ul></section>' % (t['h_look'], ''.join('<li>%s</li>' % x for x in t['look']))
        + '<section id="others"><h2>%s</h2><ul class="fit-list">%s</ul></section>' % (t['h_others'], ''.join('<li>%s</li>' % x for x in t['others']))
        + '<section id="speed"><h2>%s</h2><p>%s</p><p>%s %s</p></section>' % (t['h_speed'], t['speed'], SPEED_MEASURED[lang], VINTED_LAG[lang])
        + '<section id="fit"><h2>%s</h2><ul class="fit-list">%s</ul></section>'
        % (t['h_fit'], ''.join('<li%s>%s</li>' % (' class="fit-yes"' if i == 0 else '', x) for i, x in enumerate(t['fit'])))
        + '<section id="faq"><h2>%s</h2>%s</section>' % (t['h_faq'], faq_html(faq))
        + '<section id="start"><h2>%s</h2>%s</section>' % (t['h_start'], cta(lang)))
    glance = '<ul class="glance">%s</ul>' % ''.join('<li><span>&#10003;</span>%s</li>' % g for g in t['glance'])
    return page('compare', lang, t['title'].format(**f), t['desc'].format(**f), t['eyebrow'].format(**f), t['h1'].format(**f),
                t['lead'].format(**f), None, body, [faq_ld(faq), compare_itemlist(lang)], head_extra=glance)


def nl_review_file(pages):
    """Write the Dutch copy held in HOLD as plain text for Tanush's review (website repo, not deployed)."""
    import re as _re
    out = ['# Dutch review: alert page + comparison (work order 18, step 4)', '',
           'Written ' + datetime.date.today().isoformat() + '. These two pages are built but NOT published (gen_content.HOLD).',
           'Read them as a Dutch-speaking reseller would. Reply "NL ok" or list the lines to change.',
           'Step 5 adds the Dutch price guide to the SAME review: outreach/19b-nl-review-step5.md. One "NL ok" covers both files.',
           'Preview files (open in a browser): ops/seo/preview/' + ', ops/seo/preview/'.join(r.replace('/', '-') for r, _ in pages), '']
    for rel, text in pages:
        main = text.split('<main>', 1)[1].split('</main>', 1)[0]
        main = _re.sub(r'<script\b.*?</script>', ' ', main, flags=_re.S)
        main = _re.sub(r'<(h1|h2|h3)[^>]*>', '\n\n## ', main)
        main = _re.sub(r'<(p|li|tr|blockquote)[^>]*>', '\n', main)
        main = _re.sub(r'<t[dh][^>]*>', ' | ', main)
        main = _re.sub(r'<[^>]+>', '', main)
        main = _re.sub(r'[ \t]+', ' ', html.unescape(main))
        main = _re.sub(r'\n\s*\n\s*\n+', '\n\n', main)
        out += ['', '---', '', '# /' + rel[:-5], '', main.strip()]
    path = r'C:\Users\Tanus\website\outreach\19-nl-review-step4.md'
    if os.path.isdir(os.path.dirname(path)):
        open(path, 'w', encoding='utf-8').write(plans.fill('\n'.join(out) + '\n', 'nl'))
        print('wrote', path)



def page_404():
    """404.html: Vercel serves it (status 404) for any path that matches no file. Not in the sitemap,
    noindex, no canonical or hreflang. Every link is root-relative: the page is served at any depth."""
    links = [
        ('/', 'SNYPD homepage', 'what SNYPD does and how to start.'),
        (SLUGS['bot']['en'], 'Vinted bot', 'how SNYPD watches your Vinted searches and alerts you to new listings.'),
        ('/vinted-price-guide', 'Vinted price guide', 'typical Vinted asking prices by condition, item by item.'),
        (SLUGS['checker']['en'], 'Vinted price checker', 'type an item, see its typical asking price on Vinted.'),
        ('/plans', 'Plans and prices', 'the Free plan and the paid plans side by side.'),
    ]
    items = ''.join('<li><a href="%s">%s</a>: %s</li>' % (h, t, d) for h, t, d in links)
    body = """
<section id="where">
  <h2>Where to go from here</h2>
  <ul>%s</ul>
  <p lang="fr">En fran\u00e7ais\u00a0: <a href="%s" hreflang="fr">le bot Vinted SNYPD</a> et <a href="/fr/guide-prix-vinted" hreflang="fr">le guide des prix Vinted</a>.</p>
</section>""" % (items, SLUGS['bot']['fr'])
    return page('notfound', 'en', 'Page not found | SNYPD',
                'This page does not exist on snypd.store. Go to the homepage, the Vinted bot guide, the price guide or the price checker.',
                'ERROR 404', 'This page doesn&rsquo;t exist',
                'The link may be old or mistyped. These are the pages most people are looking for.', None, body, bare=True)


_TIME_RE = re.compile(r'(<span class="lg-meta">[^<]*<time datetime=")(\d{4}-\d{2}-\d{2})(">)([^<]*)(</time>)')
_PAGE_DM_RE = re.compile(r'("@type":"WebPage"[^<]*?"dateModified":")(\d{4}-\d{2}-\d{2})(")')


def _main_text(t):
    m = re.search(r'<main>.*</main>', t, re.S)
    return _TIME_RE.sub('', m.group(0)) if m else t


def stamp_modified(path, text):
    """The 'Updated' line and the WebPage dateModified follow the page's real content: when
    <main> is byte-identical to the file on disk the later of the two dates is kept, otherwise it
    becomes today. Nav, footer and <head> changes never move it (no fake freshness)."""
    m = _TIME_RE.search(text)
    if not m:
        return text
    old = open(path, encoding='utf-8').read() if os.path.isfile(path) else None
    om = _TIME_RE.search(old) if old else None
    if om and _main_text(old) == _main_text(text):
        iso = max(om.group(2), m.group(2))
    else:
        iso = max(datetime.date.today().isoformat(), m.group(2))
    if iso == m.group(2):
        return text
    lang = re.search(r'<html lang="([a-z]+)"', text).group(1)
    text = _TIME_RE.sub(lambda x: x.group(1) + iso + x.group(3) + date_txt(iso, lang) + x.group(5), text, count=1)
    return _PAGE_DM_RE.sub(lambda x: x.group(1) + iso + x.group(3), text, count=1)


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rel.endswith('.csv'):
        text = plans.fill(text, plans.page_lang(text))
        text = stamp_modified(path, text)
    data = text.encode('utf-8')
    if not os.path.isfile(path) or open(path, 'rb').read() != data:
        open(path, 'wb').write(data)
    print('wrote', rel, len(data), 'bytes')


# Polish + Swedish (bot page and alert hub): copy and wiring in copy_pl_sv.py.
import copy_pl_sv as cps  # noqa: E402
cps.install(globals())

# Help guides (18 Oct 2026): Vinted saved searches (8 languages) and price-drop notifications (4).
# Copy + sources: copy_guides.py; facts quoted from Vinted's help centre (articles 433, 435, 258).
import copy_guides as cg  # noqa: E402
GUIDE_FAQ_H = {'en': 'Questions', 'fr': 'Questions', 'de': 'Fragen', 'nl': 'Vragen', 'it': 'Domande', 'es': 'Preguntas',
               'pl': 'Pytania', 'sv': 'Frågor'}
for _k, _g in cg.GUIDES.items():
    SLUGS[_k] = dict(_g['slugs'])
    PAGE_MODIFIED[_k] = cg.HELP_READ


def page_guide(key, lang):
    c = cg.GUIDES[key][lang]
    fmt = {k: href(k, lang) for k in ('bot', 'notify', 'notwork', 'sold', 'saved', 'pricedrop')}
    for art in ('433', '435', '258'):
        fmt['h' + art] = cg.HELP.get((art, lang)) or cg.HELP.get((art, 'en'), '')
    fmt['read'] = date_txt(cg.HELP_READ, lang)
    F = lambda t: t.format(**fmt)  # noqa: E731
    faq = [(F(q), F(a)) for q, a in c['faq']]
    toc = list(c['toc'])
    if 'faq' not in [i for i, _ in toc]:
        toc.append(('faq', GUIDE_FAQ_H[lang]))
    body = ('<section id="answer"><div class="lg-box lg-mint"><p>%s</p></div></section>' % F(c['answer'])
            + ''.join('<section id="%s"><h2>%s</h2>%s</section>' % (i, F(h), F(t)) for i, h, t in c['sections'])
            + '<section id="faq"><h2>%s</h2>%s</section>' % (GUIDE_FAQ_H[lang], faq_html(faq))
            + '<section id="start"><h2>%s</h2>%s</section>' % (F(c['cta_h']), cta(lang)))
    return page(key, lang, F(c['title']), F(c['desc']), F(c['eyebrow']), F(c['h1']), F(c['lead']), toc, body, [faq_ld(faq)])


if __name__ == '__main__':
    for lang in (('en', 'fr') if FR_LIVE else ('en',)):
        prefix = '' if lang == 'en' else 'fr/'
        write(prefix + SLUGS['bot'][lang].rsplit('/', 1)[1] + '.html', page_bot(lang))
        write(prefix + SLUGS['notify'][lang].rsplit('/', 1)[1] + '.html', page_notify(lang))
        write(prefix + SLUGS['compare'][lang].rsplit('/', 1)[1] + '.html', page_compare(lang))
    for lang in SLUGS['notwork']:
        rel = SLUGS['notwork'][lang].lstrip('/') + '.html'
        write(rel if LIVE[lang] else 'ops/seo/preview/' + rel.replace('/', '-'), page_notwork(lang))
    for lang in ('de', 'nl', 'it', 'es', 'pl', 'sv'):
        rel = SLUGS['bot'][lang].lstrip('/') + '.html'
        write(rel if LIVE[lang] else 'ops/seo/preview/' + rel.replace('/', '-'), page_bot(lang))
    held = []
    for key, fn in (('notify', page_notify_x), ('compare', page_compare_x)):
        for lang in ('de', 'nl', 'it', 'es'):
            rel = SLUGS[key][lang].lstrip('/') + '.html'
            text = fn(lang)
            if (key, lang) in HOLD or not LIVE[lang]:
                write('ops/seo/preview/' + rel.replace('/', '-'), text)
                held.append((rel, text))
            else:
                write(rel, text)
    for lang in cps.LANGS:
        write(SLUGS['notify'][lang].lstrip('/') + '.html', page_notify_x(lang))
    for key in cg.GUIDES:
        for lang in live_langs(key):
            write(SLUGS[key][lang].lstrip('/') + '.html', page_guide(key, lang))
    if held:
        nl_review_file(held)
    write('vinted-deals.html', page_deals('en'))
    if STEALS_HELD:
        write('ops/seo/preview/vinted-deals-weekly.html', page_deals('en', STEALS_WEEK))
    write('404.html', page_404())
    for lang in (('en', 'fr') if FR_LIVE else ('en',)):
        write(SLUGS['monitor'][lang].lstrip('/') + '.html', page_monitor(lang))
    for lang in (('en', 'fr') if FR_LIVE else ('en',)):
        write(SLUGS['fees'][lang].lstrip('/') + '.html', page_fees(lang))