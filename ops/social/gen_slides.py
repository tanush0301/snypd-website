"""Carousel slides for Instagram / TikTok photo mode / r/SNYPD, built ONLY from SNYPD's own
verified data files -- the same files the SEO pages use (ops/seo/data/*.json), through the same
helpers (gen_content.money/num/pct/fee_cents), so a slide can never say something the site
doesn't.

    python ops/social/gen_slides.py [OUT_DIR]      # default: C:/Users/Tanus/website/social
    node   ops/social/render.js OUT_DIR             # writes 1080x1350 PNGs next to each deck

Writes, per set, deck.html (one 1080x1350 div per slide) and captions.md (caption, hashtags,
alt text per slide). Nothing here is published by the script: posting is a separate step.
OUT_DIR is outside the repo on purpose -- the repo root is served publicly by Vercel.
Rules (from CLAUDE.md / outreach/00-fact-sheet.md): never "instant", "real-time", "safe",
"undetectable", "allowed by Vinted", no millisecond claims, no founder name.
"""
import datetime
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'ops', 'seo'))
import gen_content as G  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Tanus\website\social'
FONT = 'file:///' + ROOT.replace('\\', '/')
NB = '\u00a0'
# Instagram allows at most 5 hashtags per post/reel since 18 Dec 2025 (@creators on Threads).
TAGS = {'en': '#vinted #vintedfinds #vintedtips #reselling #sneakers',
        'fr': '#vinted #vintedfrance #astucevinted #achatrevente #sneakers'}
CTA = {'en': 'Link in bio.', 'fr': 'Lien en bio.'}

CSS = f"""
@font-face {{ font-family: 'Cabinet'; src: url('{FONT}/assets/home/CabinetGrotesk-Black.woff2') format('woff2'); font-weight: 900; }}
@font-face {{ font-family: 'DMMono'; src: url('{FONT}/assets/fonts/dm-mono-400-latin.woff2') format('woff2'); font-weight: 400; }}
@font-face {{ font-family: 'DMMono'; src: url('{FONT}/assets/fonts/dm-mono-400-latin-ext.woff2') format('woff2'); font-weight: 400; unicode-range: U+0100-024F; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #333; }}
.slide {{ width: 1080px; height: 1350px; background: #0A0A0B; color: #FFFFFF; font-family: 'DMMono', monospace;
  position: relative; overflow: hidden; padding: 96px 88px 150px; display: flex; flex-direction: column; margin: 0 0 40px; }}
.eyebrow {{ font-size: 26px; letter-spacing: .16em; color: #00E5A0; text-transform: uppercase; margin-bottom: 40px; }}
.h {{ font-family: 'Cabinet', sans-serif; font-weight: 900; font-size: 92px; line-height: .98; letter-spacing: -.02em; }}
.h.m {{ font-size: 76px; }} .h.s {{ font-size: 64px; }}
.big {{ font-family: 'Cabinet', sans-serif; font-weight: 900; font-size: 300px; line-height: .9; color: #00E5A0; letter-spacing: -.04em; }}
.p {{ font-size: 34px; line-height: 1.45; color: #B8BCBF; margin-top: 36px; }}
.p b {{ color: #FFFFFF; font-weight: 400; }}
.mint {{ color: #00E5A0; }}
.src {{ position: absolute; left: 88px; right: 88px; bottom: 96px; font-size: 22px; line-height: 1.5; color: #8B9094; }}
.foot {{ position: absolute; left: 88px; right: 88px; bottom: 44px; display: flex; justify-content: space-between;
  font-size: 22px; letter-spacing: .1em; color: #8B9094; border-top: 1px solid #1D1D20; padding-top: 18px; }}
.foot b {{ color: #FFFFFF; font-weight: 400; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 44px; font-size: 30px; }}
th {{ text-align: left; font-weight: 400; font-size: 21px; letter-spacing: .1em; color: #8B9094; padding: 0 0 18px; }}
td {{ padding: 20px 0; border-top: 1px solid #1D1D20; color: #FFFFFF; }}
td.n, th.n {{ text-align: right; padding-left: 34px; }} td.n {{ color: #00E5A0; }}
th {{ line-height: 1.35; vertical-align: bottom; }} th.n {{ width: 17%; }}
td small {{ display: block; font-size: 21px; color: #8B9094; margin-top: 4px; }}
ol {{ list-style: none; margin-top: 40px; display: flex; flex-direction: column; gap: 30px; }}
ol li {{ font-size: 34px; line-height: 1.4; color: #B8BCBF; padding-left: 78px; position: relative; }}
ol li span {{ position: absolute; left: 0; top: -2px; font-family: 'Cabinet'; font-weight: 900; font-size: 46px; color: #00E5A0; }}
ol li b {{ color: #FFFFFF; font-weight: 400; }}
.cta {{ margin-top: auto; border: 2px solid #00E5A0; padding: 34px 38px; font-size: 34px; line-height: 1.4; }}
.cta b {{ color: #00E5A0; font-weight: 400; }}
"""


def esc(s):
    return html.escape(s, quote=False)


def foot(i, n):
    return f'<div class="foot"><span><b>SNYPD</b> &middot; snypd.store</span><span>{i}/{n}</span></div>'


def deck(slides):
    n = len(slides)
    body = ''.join(f'<section class="slide" id="s{i + 1}">{s}{foot(i + 1, n)}</section>' for i, s in enumerate(slides))
    return f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'


def write_set(name, slides, caption, alts):
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'deck.html'), 'w', encoding='utf-8').write(deck(slides))
    body, tags = caption.rsplit('\n\n', 1)  # URLs in Instagram captions aren't clickable
    caption = f'{body}\n\n{CTA[name[-2:]]}\n\n{tags}'
    md = [f'# {name}', '', '## Caption', '', caption, '', '## Alt text (one per slide, in order)', '']
    md += [f'{i + 1}. {a}' for i, a in enumerate(alts)]
    md += ['', f'Generated {datetime.date.today().isoformat()} by ops/social/gen_slides.py from ops/seo/data.', '']
    open(os.path.join(d, 'captions.md'), 'w', encoding='utf-8').write('\n'.join(md))
    print('wrote', name, len(slides), 'slides')


# ------------------------------------------------------------------ deals (EN)
def deals_en():
    d = json.load(open(G.DEALS, encoding='utf-8'))
    models = d['models']
    start = datetime.date.fromisoformat(d['window_start'][:10])
    last = datetime.date.fromisoformat(d['window_end'][:10]) - datetime.timedelta(days=1)
    span = f'{start.day} {G.MONTHS_TXT["en"][start.month - 1][:3]} to {last.day} {G.MONTHS_TXT["en"][last.month - 1][:3]} {last.year}'
    top = models[0]
    total = sum(m['n'] for m in models)
    lad = top['ladder']
    src = f'Asking prices on {d["marketplace"]}, {span}, {G.num(total, "en")} listings of {len(models)} models. Typical = median asking price for the same model and condition. Plain title match.'
    rows = ''.join(f'<tr><td>{esc(m["name"])}</td><td class="n">{G.num(m["n"], "en")}</td>'
                   f'<td class="n">{G.pct(m["under30"], m["n"])}</td><td class="n">{G.pct(m["under50"], m["n"])}</td></tr>' for m in models)
    lrows = ''.join(f'<tr><td>{G.COND_EN.get(c["condition"], esc(c["condition"]))}</td><td class="n">{G.money(c["median_cents"], "en")}</td>'
                    f'<td class="n">{G.num(c["n"], "en")}</td></tr>' for c in lad)
    vg = {c['condition']: c['median_cents'] for c in lad}['Très bon état']
    cap = int(round(vg * 0.7 / 100.0)) * 100
    slides = [
        f'<div class="eyebrow">Vinted data &middot; {span}</div><div class="big">{G.pct(top["under30"], top["n"])}</div>'
        f'<div class="h m">of {esc(top["name"])} listings went up 30%+ under the typical price for their condition.</div>'
        f'<div class="src">{src}</div>',
        f'<div class="eyebrow">How often listings go under the typical price</div><div class="h s">Seven models, two weeks.</div>'
        f'<table><tr><th>MODEL</th><th class="n">LISTINGS</th><th class="n">30%+ UNDER</th><th class="n">HALF PRICE</th></tr>{rows}</table>'
        f'<div class="src">{src}</div>',
        f'<div class="eyebrow">Why condition matters</div><div class="h s">The same shoe, five prices.</div>'
        f'<p class="p">Typical asking price of a <b>{esc(top["name"])}</b> on {d["marketplace"]}, by condition:</p>'
        f'<table><tr><th>CONDITION</th><th class="n">TYPICAL</th><th class="n">LISTINGS</th></tr>{lrows}</table>'
        f'<div class="src">A {G.money(cap, "en")} Very good pair is 30% under; a {G.money(cap, "en")} Good pair is above typical. {src}</div>',
        '<div class="eyebrow">How to catch them</div><div class="h s">Four steps.</div><ol>'
        '<li><span>1</span><b>Know the typical price</b> for the model and condition.</li>'
        '<li><span>2</span><b>Search narrow:</b> brand, size, condition, and a price cap around 70% of typical.</li>'
        '<li><span>3</span><b>Get alerted</b> when a new listing matches. Vinted&rsquo;s saved searches only show a &ldquo;+N&rdquo; counter.</li>'
        '<li><span>4</span><b>Check before paying:</b> photos, size, seller. Pay through Vinted&rsquo;s checkout to keep Buyer Protection.</li></ol>',
        '<div class="eyebrow">Full data and method</div><div class="h s">snypd.store/<br>vinted-deals</div>'
        '<p class="p">SNYPD watches your Vinted searches and sends a push alert when a new listing matches. It never logs into your Vinted account and never buys for you.</p>'
        '<div class="cta">Free plan: <b>1 search, no card.</b><br>Link in bio.</div>',
    ]
    caption = (f'How often do Vinted listings come up well under the typical price? We counted {G.num(total, "en")} listings of {len(models)} models on '
               f'{d["marketplace"]} ({span}). {esc(top["name"])}: {G.num(top["under30"], "en")} of {G.num(top["n"], "en")} listings ({G.pct(top["under30"], top["n"])}) '
               f'went up 30%+ under the typical asking price for their condition.\n\nAsking prices, not sold prices. Full table and method: snypd.store/vinted-deals\n\n{TAGS["en"]}')
    alts = [f'{G.pct(top["under30"], top["n"])} of {top["name"]} listings went up 30% or more under the typical price for their condition, {span}.',
            'Table: listings, share 30% or more under typical, and share at half price or less, for seven sneaker and streetwear models.',
            f'Typical asking price of a {top["name"]} by condition, from new with tags to satisfactory.',
            'Four steps: know the typical price, search narrow with a price cap, get alerted, check before paying.',
            'Full data at snypd.store/vinted-deals. SNYPD sends push alerts for new Vinted listings and never logs into your account.']
    write_set('deals-en', slides, caption, alts)


# ------------------------------------------------------------------ fees (EN + FR)
FEE_PRICES = [500, 1000, 2000, 3000, 5000, 10000, 20000]


def fees(lang):
    chk = json.load(open(G.FEES_CHECK, encoding='utf-8'))
    if chk['fee_matches'] != chk['listings']:
        sys.exit('fees: formula no longer matches every listing in fees-check; do not publish')
    n = G.num(chk['listings'], lang)
    m = lambda c: G.m2(c, lang).replace('&#8239;', NB)
    rows = ''.join(f'<tr><td>{m(c)}</td><td class="n">{m(G.fee_cents(c))}</td><td class="n">{m(c + G.fee_cents(c))}</td></tr>' for c in FEE_PRICES)
    if lang == 'en':
        slides = [
            '<div class="eyebrow">Vinted Buyer Protection, in euros</div><div class="h">5% + &euro;0.70</div>'
            f'<p class="p">On top of the item price, on vinted.fr, .de, .nl, .it and .es (their own price lists). Checked on <b>{n}</b> vinted.be listings: every one matched.</p>'
            '<div class="src">Rounded to the cent. Selling on Vinted is free; shipping is extra. UK and US use different rules.</div>',
            f'<div class="eyebrow">What a buyer really pays</div><div class="h s">Before shipping.</div>'
            f'<table><tr><th>ITEM PRICE</th><th class="n">FEE</th><th class="n">YOU PAY</th></tr>{rows}</table>'
            '<div class="src">5% + &euro;0.70, rounded to the cent. Shipping not included.</div>',
            f'<div class="eyebrow">Bundle tip</div><div class="h s">The &euro;0.70 is per order, not per item.</div>'
            f'<p class="p">Vinted charges the fee on the item <b>or the bundle</b>. Three &euro;10 items bought one by one: {m(3 * G.fee_cents(1000))} in fees. As one bundle: {m(G.fee_cents(3000))}.</p>',
            '<div class="eyebrow">Fee calculator</div><div class="h s">snypd.store/<br>vinted-fees</div>'
            '<p class="p">Any price, the fee and the total in one line. SNYPD also shows each new listing&rsquo;s price including Buyer Protection.</p>'
            '<div class="cta">SNYPD: push alerts for new Vinted listings. <b>Free plan, 1 search.</b></div>',
        ]
        caption = (f'Vinted Buyer Protection on vinted.fr/.de/.nl/.it/.es is 5% + EUR0.70 on top of the price. We checked {n} real vinted.be listings and every '
                   f'single one matched. Bundles pay the EUR0.70 once.\n\nCalculator: snypd.store/vinted-fees\n\n{TAGS["en"]}')
        alts = ['Vinted Buyer Protection is 5% plus 0.70 euro on top of the item price, checked on real listings.',
                'Table of item prices from 5 to 200 euros with the Buyer Protection fee and the total paid.',
                'Bundle tip: the 0.70 euro part of the fee is charged once per order, not per item.',
                'Fee calculator at snypd.store/vinted-fees.']
        write_set('fees-en', slides, caption, alts)
        return
    slides = [
        f'<div class="eyebrow">Protection acheteurs Vinted</div><div class="h">5{NB}% + 0,70{NB}&euro;</div>'
        f'<p class="p">En plus du prix, sur vinted.fr, .de, .nl, .it et .es (leurs propres grilles tarifaires). Vérifié sur <b>{n}</b> annonces vinted.be{NB}: toutes correspondent.</p>'
        f'<div class="src">Arrondi au centime. Vendre sur Vinted est gratuit{NB}; la livraison est en plus.</div>',
        f'<div class="eyebrow">Ce que paie vraiment l’acheteur</div><div class="h s">Hors livraison.</div>'
        f'<table><tr><th>PRIX</th><th class="n">FRAIS</th><th class="n">TOTAL</th></tr>{rows}</table>'
        f'<div class="src">5{NB}% + 0,70{NB}&euro;, arrondi au centime. Livraison non comprise.</div>',
        f'<div class="eyebrow">Astuce lots</div><div class="h s">Les 0,70{NB}&euro; sont par commande, pas par article.</div>'
        f'<p class="p">Vinted applique les frais sur l’article <b>ou le lot</b>. Trois articles à 10{NB}&euro; achetés séparément{NB}: {m(3 * G.fee_cents(1000))} de frais. En un lot{NB}: {m(G.fee_cents(3000))}.</p>',
        f'<div class="eyebrow">Calculateur</div><div class="h s">snypd.store/<br>fr/frais-vinted</div>'
        f'<p class="p">N’importe quel prix, les frais et le total en une ligne. SNYPD affiche aussi le prix de chaque nouvelle annonce protection acheteurs incluse.</p>'
        f'<div class="cta">SNYPD{NB}: alertes push pour les nouvelles annonces Vinted. <b>Plan gratuit, 1 recherche.</b></div>',
    ]
    caption = (f'La protection acheteurs Vinted sur vinted.fr/.de/.nl/.it/.es{NB}: 5{NB}% + 0,70{NB}EUR en plus du prix. Vérifié sur {n} vraies annonces vinted.be, '
               f'toutes correspondent. En lot, les 0,70{NB}EUR ne sont payés qu’une fois.\n\nCalculateur{NB}: snypd.store/fr/frais-vinted\n\n{TAGS["fr"]}')
    alts = ['La protection acheteurs Vinted vaut 5 % plus 0,70 euro en plus du prix, vérifié sur de vraies annonces.',
            'Tableau des prix de 5 à 200 euros avec les frais de protection acheteurs et le total payé.',
            'Astuce : la partie fixe de 0,70 euro est payée une fois par commande, pas par article.',
            'Calculateur des frais sur snypd.store/fr/frais-vinted.']
    write_set('fees-fr', slides, caption, alts)


# ------------------------------------------------------------------ saved searches vs monitor (EN + FR)
def monitor(lang):
    if lang == 'en':
        slides = [
            '<div class="eyebrow">Vinted tip</div><div class="h">Vinted&rsquo;s saved searches don&rsquo;t ping you.</div>'
            '<p class="p">They show a <b>&ldquo;+N&rdquo; counter</b> the next time you open the app. No notification for each new match.</p>'
            '<div class="src">Source: Vinted help centre, article 435 (saved searches).</div>',
            '<div class="eyebrow">Why it matters</div><div class="h s">Everyone watching a search sees a new listing at the same moment.</div>'
            '<p class="p">The first person to notice it gets the first chance to buy. Well-priced listings are the ones that go first.</p>',
            '<div class="eyebrow">What a Vinted monitor does</div><div class="h s">Checks the search for you, and tells you.</div><ol>'
            '<li><span>1</span>Paste a Vinted search link with your filters.</li>'
            '<li><span>2</span>SNYPD checks it every <b>30 seconds to 5 minutes</b>.</li>'
            '<li><span>3</span>A new match arrives as a <b>push notification</b> on your phone.</li>'
            '<li><span>4</span>You open it on Vinted and decide. It never buys for you.</li></ol>',
            '<div class="eyebrow">Try it</div><div class="h s">snypd.store</div>'
            '<p class="p">Never asks for your Vinted password. Never logs in. Works on 26 Vinted sites in Europe and the US.</p>'
            '<div class="cta">Free plan: <b>1 search, no card.</b> Paid plans watch 24/7 from &euro;14.99/month.</div>',
        ]
        caption = ('Vinted\'s saved searches only show a "+N" counter when you open the app (Vinted help, article 435), so you find out when you look. '
                   'A monitor checks the search for you and sends a push alert when something new matches. SNYPD does that every 30 s to 5 min, '
                   f'never logs into your account and never buys for you.\n\nWhat a Vinted monitor is: snypd.store/vinted-monitor\n\n{TAGS["en"]}')
        alts = ['Vinted saved searches show a plus-N counter, not a notification for each new match.',
                'Everyone watching the same search sees a new listing at the same moment.',
                'How a Vinted monitor works: paste a search link, it checks every 30 seconds to 5 minutes, sends a push, you decide.',
                'SNYPD at snypd.store: free plan with one search; paid plans watch 24/7 from 14.99 euros a month.']
        write_set('monitor-en', slides, caption, alts)
        return
    slides = [
        f'<div class="eyebrow">Astuce Vinted</div><div class="h">Les recherches sauvegardées ne te préviennent pas.</div>'
        f'<p class="p">Elles affichent un <b>compteur «{NB}+N{NB}»</b> à ta prochaine visite dans l’app. Pas de notification pour chaque nouvelle annonce.</p>'
        '<div class="src">Source : centre d’aide Vinted, article 435 (recherches sauvegardées).</div>'.replace(' :', NB + ':'),
        f'<div class="eyebrow">Pourquoi c’est important</div><div class="h s">Tout le monde voit une nouvelle annonce au même moment.</div>'
        f'<p class="p">Le premier qui la remarque a la première chance de l’acheter. Les annonces bien placées partent en premier.</p>',
        f'<div class="eyebrow">Ce que fait un monitor Vinted</div><div class="h s">Il vérifie la recherche pour toi, et te prévient.</div><ol>'
        f'<li><span>1</span>Colle un lien de recherche Vinted avec tes filtres.</li>'
        f'<li><span>2</span>SNYPD la vérifie toutes les <b>30 secondes à 5 minutes</b>.</li>'
        f'<li><span>3</span>Une nouvelle annonce arrive en <b>notification push</b> sur ton téléphone.</li>'
        f'<li><span>4</span>Tu l’ouvres sur Vinted et tu décides. Il n’achète jamais à ta place.</li></ol>',
        f'<div class="eyebrow">Essaie</div><div class="h s">snypd.store</div>'
        f'<p class="p">Ne demande jamais ton mot de passe Vinted. Ne se connecte jamais. Fonctionne sur 26 sites Vinted en Europe et aux États-Unis.</p>'
        f'<div class="cta">Plan gratuit{NB}: <b>1 recherche, sans carte.</b> Les plans payants surveillent 24h/24 dès 14,99{NB}&euro;/mois.</div>',
    ]
    caption = (f'Les recherches sauvegardées Vinted n’affichent qu’un compteur «{NB}+N{NB}» quand tu ouvres l’app (aide Vinted, article 435). Un monitor vérifie la recherche pour toi '
               f'et t’envoie une alerte push dès qu’une annonce correspond. SNYPD le fait toutes les 30{NB}s à 5{NB}min, sans jamais se connecter à ton compte ni acheter à ta place.'
               f'\n\nC’est quoi un monitor Vinted{NB}: snypd.store/fr/monitor-vinted\n\n{TAGS["fr"]}')
    alts = ['Les recherches sauvegardées Vinted affichent un compteur plus N, pas une notification par annonce.',
            'Tout le monde voit une nouvelle annonce au même moment.',
            'Fonctionnement d’un monitor Vinted : lien de recherche, vérification toutes les 30 secondes à 5 minutes, notification push, tu décides.',
            'SNYPD sur snypd.store : plan gratuit avec une recherche, plans payants 24h/24 dès 14,99 euros par mois.']
    write_set('monitor-fr', slides, caption, alts)


if __name__ == '__main__':
    deals_en()
    fees('en')
    fees('fr')
    monitor('en')
    monitor('fr')
