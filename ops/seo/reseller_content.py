"""EN/FR reseller resources. Platform facts checked against Vinted help on 2 Nov 2026.

Search targets were observed in Google suggestions and search results, not ranked
by verified monthly volume. No sales-speed, profit or authenticity guarantees.
"""
import html

UPDATED = '2026-11-02'
SLUGS = {
    'resell': {'en': '/how-to-resell-on-vinted', 'fr': '/fr/achat-revente-vinted'},
    'resell-brands': {'en': '/best-brands-to-resell-on-vinted', 'fr': '/fr/meilleures-marques-revente-vinted'},
    'profit': {'en': '/vinted-profit-calculator', 'fr': '/fr/calculateur-marge-vinted'},
    # 7 Nov 2026 (GEO priority: "best Vinted reselling tool", "how to make money on Vinted")
    'tools': {'en': '/best-vinted-reselling-tools', 'fr': '/fr/meilleurs-outils-revente-vinted'},
    'money': {'en': '/how-to-make-money-on-vinted', 'fr': '/fr/gagner-argent-vinted'},
}
# First publication per page; pages not listed were published on UPDATED.
PUBLISHED = {'tools': '2026-11-07', 'money': '2026-11-07'}
LABELS = {
    'en': ['How to resell on Vinted', 'Brands and models to research', 'Resale profit calculator',
           'Best Vinted reselling tools', 'How to make money on Vinted'],
    'fr': ['Achat-revente sur Vinted', 'Marques et modèles à étudier', 'Calculateur de marge',
           'Meilleurs outils de revente Vinted', 'Gagner de l’argent sur Vinted'],
}
# Competitor facts on /best-vinted-reselling-tools: each from the tool's own site, read on TOOLS_CHECKED.
# Re-read every site before changing the date. Never type a SNYPD price: use plans.py tokens.
TOOLS_CHECKED = {'en': '7 November 2026', 'fr': '7 novembre 2026'}
TOOL_SOURCES = [
    ('ResellTrack', 'https://reselltrack.io/'),
    ('Zipsale', 'https://zipsale.co.uk/pricing'),
    ('VintedCRM', 'https://vintedcrm.com/tarifs/'),
    ('Vendoo', 'https://www.vendoo.co/'),
    ('Crosslist', 'https://crosslist.com/pricing'),
    ('Relistly', 'https://www.relistly.com/'),
]
# Models for the "cheapest quarter vs typical ask" table on /how-to-make-money-on-vinted (all in price-index.json).
MONEY_ITEMS = ['nike-dunk-low', 'adidas-gazelle', 'new-balance-550', 'ralph-lauren-quarter-zip',
               'carhartt-detroit-jacket', 'the-north-face-nuptse']


def related(lang):
    links = ''.join('<li><a href="%s">%s</a></li>' % (SLUGS[k][lang], label)
                    for k, label in zip(SLUGS, LABELS[lang]))
    import expansion_content
    labels = ['Build a search link', 'Set up phone alerts'] if lang == 'en' else ['Créer un lien de recherche', 'Configurer les alertes sur téléphone']
    links += ''.join('<li><a href="%s">%s</a></li>' % (expansion_content.SLUGS[k][lang], label)
                     for k, label in zip(('builder', 'phone'), labels))
    heading = 'Resources for Vinted resellers' if lang == 'en' else 'Ressources pour la revente sur Vinted'
    return '<section id="reseller-resources"><h2>%s</h2><ul>%s</ul></section>' % (heading, links)


def sources(lang, fees=False):
    host = 'https://www.vinted.co.uk' if lang == 'en' else 'https://www.vinted.fr'
    ids = [('1120', 'Commercial selling' if lang == 'en' else 'Ventes commerciales')]
    if fees:
        ids.append(('373', 'Selling and buying fees' if lang == 'en' else 'Frais de vente et d’achat'))
    links = ''.join('<li><a href="%s/help/%s" rel="nofollow noopener">Vinted — %s</a></li>' % (host, i, name) for i, name in ids)
    text = ('Platform sources checked on 2 November 2026. Rules, account eligibility and fees can vary by market; use the terms of the site where you buy or sell.' if lang == 'en' else
            'Sources Vinted consultées le 2 novembre 2026. Règles, éligibilité des comptes et frais peuvent varier selon le pays : consulte les conditions du site où tu achètes ou vends.')
    return '<section id="sources"><h2>Sources</h2><p>%s</p><ul>%s</ul></section>' % (text, links)


def guide(lang):
    if lang == 'en':
        title = 'How to Resell on Vinted: Sourcing, Costs & First Search | SNYPD'
        desc = 'A practical Vinted reselling workflow: check commercial-selling rules, choose a model, calculate your buying budget and monitor a focused search.'
        h1 = 'How to resell on Vinted: start with a buying budget'
        lead = 'Reselling starts before the purchase. Work out which second-hand item you understand, what it can cost you in total and how much uncertainty you can afford.'
        sections = [
            ('rules', 'Is reselling allowed on Vinted?', '<p>Vinted distinguishes clearing out your own belongings from sourcing stock for profit. Its UK commercial-selling guidance says professional selling belongs on an eligible Pro account. It also rules out new commercial stock bought specifically for resale, including wholesale or retail stock, even for Pro sellers. Check the account and catalogue terms for your own market before sourcing.</p><p>A monitor does not change those rules. SNYPD watches public searches; it does not grant permission to sell, verify authenticity or operate your Vinted account.</p>'),
            ('model', '1. Choose one model you can evaluate', '<p>Start with a small category you understand rather than a list of fashionable labels. Record the exact model, size range, acceptable condition and the photographs or measurements you need. A used jacket with a damaged zip is a different purchase from the same model in sound condition.</p><p>Use the <a href="/best-brands-to-resell-on-vinted">brand and model research guide</a> to build a shortlist. If you cannot explain why a buyer would choose the item, leave it out of your first search.</p>'),
            ('budget', '2. Calculate the maximum you can pay', '<p>Use expected sale proceeds, then subtract purchase-related charges, packaging or postage you pay, other costs and the profit you want to retain. A hypothetical sale at €40 with €7 of non-item costs and a €10 target leaves a maximum item price of €23. This is a worked example, not a resale valuation.</p><p>Use the <a href="/vinted-profit-calculator">Vinted profit calculator</a> and test a lower sale price too. Include allocated subscription costs, promotion, cleaning or repair where relevant. Taxes and your time are additional considerations; an unsold item has not generated sale proceeds.</p>'),
            ('search', '3. Build a focused Vinted search', '<ol><li>Search the exact model on the Vinted marketplace where you can buy.</li><li>Set useful size, condition and category filters, then your maximum item price.</li><li>Sort by newest first when you want to review new stock; compare older listings separately.</li><li>Save the search. If you want to monitor it with SNYPD, copy the filtered catalogue address and paste it into the app.</li></ol><p>Keep a broad discovery search separate from a model search. A cheap match is a prompt to inspect an item, not an automatic buying instruction. More detail: <a href="/vinted-deals">finding Vinted deals</a> and <a href="/vinted-saved-searches">saved searches</a>.</p>'),
            ('check', '4. Check the listing before buying', '<ul><li>Compare the same model and condition, including wear, missing parts and measurements.</li><li>Read the description and ask the seller for factual clarification when photographs are insufficient.</li><li>Check authenticity evidence appropriate to the item. A low price, review count or automated price estimate cannot authenticate it.</li><li>Use the checkout total, including the actual Buyer Protection and shipping amounts shown to you.</li><li>Use Vinted’s normal purchase flow; SNYPD does not buy or message for you.</li></ul>'),
            ('measure', '5. Track what actually sells', '<p>Record purchase cost, date, realised sale proceeds, direct costs and time in stock. Keep unsold stock in your cash-flow records. Active asking prices, favourites and a listing disappearing from search do not establish a completed sale or its final price.</p><p>Compare your own results for the same model, size and condition. Increase your budget or number of searches only when the realised results justify it. For asking-price context, see the <a href="/vinted-price-checker">price checker</a>; it shows the sample market and dates.</p>'),
            ('questions', 'Questions before your first purchase', '<h3>How much money do I need to start reselling?</h3><p>There is no universal starting budget. Allow for the item, checkout charges and stock that may not sell. Start with an amount you can leave tied up without relying on a quick sale.</p><h3>Can I use a Vinted bot to resell?</h3><p>Different tools do different things. SNYPD alerts you to new matching listings and leaves the purchase decision to you. It does not list, relist, authenticate or sell your stock.</p><h3>Does a saved search notify me about every new listing?</h3><p>Vinted’s saved-search help describes a new-item counter. See the <a href="/vinted-saved-search-alerts">new-listing alert guide</a> for the difference between a saved search, native notifications and a separate monitor.</p>'),
        ]
    else:
        title = 'Achat-revente Vinted : budget, recherche et coûts | SNYPD'
        desc = 'Une méthode concrète pour l’achat-revente sur Vinted : règles de vente professionnelle, choix du modèle, budget d’achat et recherche ciblée.'
        h1 = 'Achat-revente sur Vinted : commence par ton budget'
        lead = 'Le travail commence avant l’achat : choisir un article de seconde main que tu sais évaluer, calculer son coût complet et prévoir ce qui se passe s’il ne se vend pas.'
        sections = [
            ('regles', 'L’achat-revente est-il autorisé sur Vinted ?', '<p>Vinted distingue le vide-dressing personnel de l’approvisionnement destiné à générer des revenus. Son aide française sur les ventes commerciales renvoie la vente professionnelle vers un compte Pro éligible. Elle exclut aussi les nouveaux stocks commerciaux achetés spécifiquement pour être revendus, y compris auprès de grossistes ou en magasin, même pour les vendeurs Pro. Vérifie les conditions de ton marché avant de constituer un stock.</p><p>Un outil de surveillance ne change pas ces règles. SNYPD observe des recherches publiques : il ne t’accorde pas un droit de vendre et n’authentifie pas les articles.</p>'),
            ('modele', '1. Choisis un modèle que tu sais examiner', '<p>Commence par une petite catégorie que tu connais, plutôt que par une liste de marques à la mode. Note le modèle exact, les tailles, les états acceptables et les photos ou mesures nécessaires. Une veste dont la fermeture est abîmée n’est pas le même achat que le même modèle en bon état de fonctionnement.</p><p>Le <a href="/fr/meilleures-marques-revente-vinted">guide des marques et modèles à étudier</a> aide à construire cette sélection. Si tu ne sais pas pourquoi quelqu’un choisirait cet article, écarte-le de ta première recherche.</p>'),
            ('budget', '2. Calcule ton prix d’achat maximum', '<p>Pars du montant de vente espéré, puis retire les frais d’acquisition, l’emballage ou le port à ta charge, les autres coûts et le bénéfice visé. Exemple fictif : une vente à 40 €, 7 € de coûts hors article et un objectif de 10 € laissent au maximum 23 € pour l’article. Ce n’est pas une estimation du prix de revente d’un modèle réel.</p><p>Utilise le <a href="/fr/calculateur-marge-vinted">calculateur de marge Vinted</a> et teste aussi un prix de vente inférieur. Ajoute au besoin une part d’abonnement, la promotion, le nettoyage ou la réparation. La fiscalité et ton temps restent à considérer ; un article invendu ne produit pas de recette.</p>'),
            ('recherche', '3. Prépare une recherche Vinted précise', '<ol><li>Cherche le modèle exact sur le site Vinted où tu peux acheter.</li><li>Choisis les filtres utiles de taille, d’état et de catégorie, puis le prix maximum de l’article.</li><li>Trie par nouveautés pour examiner les nouveaux articles ; compare les anciennes annonces séparément.</li><li>Sauvegarde la recherche. Pour la suivre dans SNYPD, copie son adresse de catalogue filtré et colle-la dans l’application.</li></ol><p>Sépare une recherche de découverte d’une recherche portant sur un modèle précis. Un petit prix mérite un examen, pas un achat automatique. Les <a href="/fr/recherches-enregistrees-vinted">recherches enregistrées</a> et les <a href="/fr/alertes-recherche-vinted">alertes de nouvelles annonces</a> répondent à des besoins différents.</p>'),
            ('controle', '4. Vérifie l’article avant d’acheter', '<ul><li>Compare le même modèle dans un état comparable : usure, pièces manquantes et mesures comptent.</li><li>Lis la description et demande des précisions factuelles si les photos ne suffisent pas.</li><li>Examine les éléments d’authenticité adaptés à l’article. Ni le prix, ni les évaluations, ni une estimation automatique ne l’authentifient.</li><li>Compte le total du paiement, avec la Protection acheteurs et le port réellement affichés.</li><li>Achète par le parcours normal de Vinted : SNYPD n’achète pas et n’envoie pas de messages à ta place.</li></ul>'),
            ('suivi', '5. Mesure tes ventes réelles', '<p>Note le prix d’achat, la date, la recette réellement obtenue, les coûts directs et le temps en stock. Garde les invendus dans ton suivi de trésorerie. Un prix demandé, des favoris ou une annonce qui disparaît ne prouvent ni une vente ni son prix final.</p><p>Compare tes propres résultats pour le même modèle, la même taille et le même état. Augmente ton budget ou le nombre de recherches lorsque tes résultats réalisés le justifient. L’<a href="/fr/estimer-prix-vinted">outil de prix</a> fournit un contexte de prix demandés avec son marché et sa période d’observation.</p>'),
            ('questions', 'Questions avant de commencer', '<h3>Quel budget pour commencer l’achat-revente ?</h3><p>Il n’existe pas de montant universel. Prévois le prix de l’article, les frais de paiement et les invendus. Commence avec une somme que tu peux immobiliser sans compter sur une vente rapide.</p><h3>SNYPD revend-il les articles pour moi ?</h3><p>Non. Il signale les nouvelles annonces qui correspondent à tes recherches. Tu décides de l’achat. Il ne publie pas, ne republie pas, n’authentifie pas et ne vend pas ton stock.</p><h3>Une recherche sauvegardée envoie-t-elle une alerte pour chaque annonce ?</h3><p>L’aide Vinted décrit un compteur de nouveaux articles. Le <a href="/fr/alertes-recherche-vinted">guide des alertes</a> explique la différence avec les notifications natives et un outil de surveillance.</p>'),
        ]
    return title, desc, h1, lead, sections


def brands(lang, index, g):
    fr = lang == 'fr'
    wanted = ['nike-dunk-low', 'adidas-samba', 'levis-501', 'carhartt-detroit-jacket', 'the-north-face-nuptse']
    items = {x['id']: x for x in index['items']}
    rows = []
    checks = {
        'en': ['Size, colourway, outsole wear and authenticity evidence', 'Exact version, sole wear and size', 'Waist and inseam measurements, alterations and fabric wear', 'Exact jacket model, lining, zip and measurements', 'Exact model, fill condition, repairs and measurements'],
        'fr': ['Taille, coloris, usure de la semelle et éléments d’authenticité', 'Version exacte, semelle et pointure', 'Mesures de taille et longueur, retouches et usure', 'Modèle exact, doublure, fermeture et mesures', 'Modèle exact, garnissage, réparations et mesures'],
    }
    for item_id, check in zip(wanted, checks[lang]):
        item = items[item_id]
        name = html.escape(item['name'].get(lang, item['name']['en']))
        price = ('%.2f' % (item['typical'] / 100)).rstrip('0').rstrip('.')
        price = price.replace('.', ',') + ' €' if fr else '€' + price
        rows.append(['<a href="%s">%s</a>' % (item['url'][lang], name), price, str(item['n']), check])
    table = g.table(['MODÈLE' if fr else 'MODEL', 'MÉDIANE DEMANDÉE' if fr else 'MEDIAN ASK', 'ANNONCES' if fr else 'LISTINGS', 'À VÉRIFIER' if fr else 'CHECK BEFORE BUYING'], rows)
    if not fr:
        title = 'Best Brands to Resell on Vinted: Models, Prices & Checks | SNYPD'
        desc = 'Research Nike, Adidas, Levi’s, Carhartt and The North Face by exact model, condition and total cost. Asking-price context, not guaranteed resale profits.'
        h1 = 'Best brands to resell on Vinted: build a model shortlist'
        lead = 'A recognisable label is a starting point. Your buying price, the exact item and its condition decide whether that purchase fits your resale plan.'
        sections = [
            ('answer', 'Which brands should you research?', '<p>Nike, Adidas, Levi’s, Carhartt and The North Face give you specific models to compare in SNYPD’s published sample. The table below is an illustrative research shortlist, not a ranking of sales, search popularity or profit. A brand can contain both desirable models and stock that does not fit your budget.</p><p>Choose a category you can inspect accurately. Compare the same model, size and condition rather than assuming every item with the logo has the same value.</p>'),
            ('models', 'Five model references with published price context', table + '<p>These medians are from newly observed <strong>vinted.be asking prices</strong>, from %s to %s. They are not completed-sale prices, current live offers or country-wide resale valuations. Item-search samples can overlap. Open each guide for condition data and the full method.</p>' % (index['window']['from'], index['window']['to'])),
            ('demand', 'What sells best on Vinted?', '<p>This sample cannot answer that with a sales ranking. Many active listings can mean plenty of supply, not fast sales. Favourites are not purchases, and a listing can disappear because it was removed. Do not convert any of those signals into a claimed sell-through rate.</p><p>Use your own completed sales and time-in-stock records, or independent sales evidence with a stated market, period and method. Check small and unusual sizes separately; do not transfer a price from one condition or model version to another.</p>'),
            ('costs', 'A model only works at the right buying cost', '<p>Start from plausible sale proceeds and deduct all your costs and target profit. A hypothetical €40 sale with €7 of non-item costs and €10 target profit gives a €23 item-price ceiling. Paying €30 would miss that target even if the brand is familiar. Use the <a href="/vinted-profit-calculator">profit calculator</a> with your own numbers.</p><p>The published median is not a guaranteed sale price. Stress-test a lower sale value and allow for stock that remains unsold.</p>'),
            ('avoid', 'What should you avoid buying?', '<ul><li>Items whose exact model or condition you cannot establish.</li><li>Listings that require an unsupported authenticity assumption.</li><li>Stock whose checkout total leaves no room for costs or uncertainty.</li><li>New commercial stock bought for resale where Vinted’s catalogue rules prohibit it.</li></ul><p>“Cheap” and “suitable for your resale plan” are different decisions. No brand removes the need for a listing check.</p>'),
            ('search', 'Turn the shortlist into a search', '<p>Pick one model, use relevant size and condition filters, set a personal maximum price and save the search. SNYPD can monitor that filtered search for new matching listings; you still inspect and buy on Vinted yourself.</p><p>Follow the <a href="/how-to-resell-on-vinted">reselling workflow</a>, compare <a href="/vinted-price-checker">asking-price references</a> or read how <a href="/vinted-saved-search-alerts">new-listing alerts</a> work. SNYPD does not track price reductions on existing listings.</p>'),
        ]
    else:
        title = 'Meilleures marques à revendre sur Vinted : modèles et prix | SNYPD'
        desc = 'Étudie Nike, Adidas, Levi’s, Carhartt et The North Face par modèle, état et coût total. Repères de prix demandés, sans promesse de bénéfice.'
        h1 = 'Quelles marques revendre sur Vinted ? Choisis des modèles précis'
        lead = 'Une marque connue donne une piste. Le prix d’achat, le modèle exact et son état déterminent si cet article entre dans ton projet de revente.'
        sections = [
            ('reponse', 'Quelles marques regarder ?', '<p>Nike, Adidas, Levi’s, Carhartt et The North Face offrent des modèles précis à comparer dans l’échantillon publié par SNYPD. Le tableau est une sélection illustrative de recherches, pas un classement des ventes, de la popularité des recherches ou des bénéfices. Une même marque comprend des modèles très différents.</p><p>Choisis une catégorie que tu sais examiner. Compare le même modèle, la même taille et le même état : le logo seul ne détermine pas la valeur de l’article.</p>'),
            ('modeles', 'Cinq modèles avec des repères de prix publiés', table + '<p>Ces médianes proviennent des <strong>prix demandés sur vinted.be</strong>, observés du %s au %s. Ce ne sont ni des prix de ventes conclues, ni des offres en direct, ni une estimation de tout le marché français. Les échantillons de recherches peuvent se recouper. Chaque guide précise les états et la méthode.</p>' % (index['window']['from'], index['window']['to'])),
            ('demande', 'Qu’est-ce qui se vend le mieux ou le plus vite sur Vinted ?', '<p>Cet échantillon ne fournit pas de classement des ventes. Beaucoup d’annonces actives peuvent signaler une offre abondante, pas des ventes rapides. Un favori n’est pas un achat et une annonce peut disparaître parce qu’elle a été retirée. N’en déduis pas un taux de vente.</p><p>Appuie-toi sur tes ventes réalisées et ton temps en stock, ou sur une source indépendante qui explique son marché, sa période et sa méthode. Étudie les tailles inhabituelles à part et ne transpose pas le prix d’un état à un autre.</p>'),
            ('couts', 'Une marque n’est intéressante qu’au bon coût d’achat', '<p>Pars d’une recette plausible puis retire tes coûts et ton bénéfice visé. Exemple fictif : vente à 40 €, coûts hors article de 7 € et objectif de 10 € donnent un plafond d’achat de 23 €. Acheter à 30 € ne respecte pas cet objectif, même pour une marque connue. Fais le calcul avec tes chiffres dans le <a href="/fr/calculateur-marge-vinted">calculateur de marge</a>.</p><p>La médiane publiée ne garantit pas ton prix de vente. Essaie un scénario de vente plus bas et prévois les invendus.</p>'),
            ('eviter', 'Quels achats écarter ?', '<ul><li>Les articles dont tu n’arrives pas à établir le modèle ou l’état.</li><li>Les annonces qui demandent de supposer l’authenticité sans éléments suffisants.</li><li>Les achats dont le total ne laisse aucune place aux frais ou à l’incertitude.</li><li>Les nouveaux stocks commerciaux achetés pour la revente lorsque les règles Vinted les excluent.</li></ul><p>Un petit prix et un achat adapté à ton projet sont deux décisions différentes. Aucune marque ne remplace l’examen de l’annonce.</p>'),
            ('recherche', 'Transforme ta sélection en recherche', '<p>Choisis un modèle, les filtres utiles de taille et d’état, puis un prix maximum personnel. Enregistre la recherche. SNYPD peut surveiller les nouvelles annonces correspondantes ; tu examines et achètes toi-même sur Vinted.</p><p>Suis la <a href="/fr/achat-revente-vinted">méthode d’achat-revente</a>, compare les <a href="/fr/estimer-prix-vinted">prix demandés</a> ou consulte le fonctionnement des <a href="/fr/alertes-recherche-vinted">alertes</a>. SNYPD ne suit pas les baisses de prix d’annonces déjà en ligne.</p>'),
        ]
    return title, desc, h1, lead, sections


def _eur(cents, lang):
    s = ('%.2f' % (cents / 100)).rstrip('0').rstrip('.')
    return s.replace('.', ',') + ' €' if lang == 'fr' else '€' + s


def _buyer_fee(cents):
    """Buyer Protection on Vinted's euro sites: €0.70 + 5% (rounded), as on /vinted-fees."""
    return 70 + (cents * 5 + 50) // 100


def _ext(url, text):
    return '<a href="%s" rel="nofollow noopener">%s</a>' % (url, text)


def _help(lang):
    import compare_data
    host = 'https://www.vinted.co.uk' if lang == 'en' else 'https://www.vinted.fr'
    return host + '/help/1120', compare_data.HELP435[lang], compare_data.COMPARE_CHECKED[lang]


def tools(lang, index, g):
    """/best-vinted-reselling-tools: one tool per reselling job. Returns (title, desc, h1, lead, sections, extra_ld)."""
    fr = lang == 'fr'
    d = TOOLS_CHECKED[lang]
    n = len(index['items'])
    a, b = index['window']['from'], index['window']['to']
    h1120, h435, _ = _help(lang)
    src = dict(TOOL_SOURCES)
    if not fr:
        rows = [
            ['<a href="/vinted-bot">SNYPD</a>', 'Sourcing: alerts for new matching listings, with a weekly price comparison on finds',
             'Yes: %s' % g.MARKETS_TEXT['en'], 'No login: watches public search results; never buys or messages sellers',
             'Free plan, 24/7 for the first @@trial_days@@ days; Hunt Pass @@price:pass@@ once (@@pass_days@@ days); Solo @@price:solo@@ a month'],
            [_ext(src['ResellTrack'], 'ResellTrack'), 'Market and niche research from Vinted sales data',
             'Yes, every country where Vinted operates', 'Says it never asks for your Vinted credentials; its extension reads the page you have open',
             '€24 a month; no free trial'],
            [_ext(src['Zipsale'], 'Zipsale'), 'Crosslisting and auto-delisting across 8 marketplaces',
             'Yes, for UK sellers; says it uses the Vinted API', 'Connects your marketplace accounts',
             'From £15 a month + VAT; free plan without auto-delisting'],
            [_ext(src['VintedCRM'], 'VintedCRM'), 'CRM, invoicing and accounting for a Vinted shop',
             'Yes: built for Vinted', 'Says its CRM needs neither your Vinted password nor a session token',
             'Free plan; paid from €12.99 a month excl. VAT'],
            [_ext(src['Vendoo'], 'Vendoo'), 'Crosslisting', 'Vinted is not among the marketplaces named on its site', 'Not stated',
             '$14.99 a month billed monthly; 14-day free trial'],
            [_ext(src['Crosslist'], 'Crosslist'), 'Crosslisting', 'No: says it does not support users residing in the European Union',
             'Browser extension in your own browser for some marketplaces', '$29.99 a month; 20 free listings'],
            [_ext(src['Relistly'], 'Relistly'), 'Cross-posting browser extension', 'Not yet: Vinted is marked “Soon”',
             'Works through the marketplace sessions you are signed in to', 'No price shown; 7-day free trial'],
        ]
        table = g.table(['TOOL', 'JOB', 'WORKS WITH VINTED? (ITS SITE)', 'YOUR VINTED ACCOUNT', 'CHEAPEST OPTION (ITS SITE)'], rows, us_row=0)
        faq = [
            ('What is the best Vinted reselling tool?',
             'It depends on the job. For finding underpriced items, SNYPD alerts you to new matching listings and compares each find’s price with that week’s finds when there is enough data. '
             'For crosslisting to Vinted, Zipsale supports Vinted for UK sellers. For invoices and bookkeeping, VintedCRM has a free plan. '
             'We make SNYPD; the other facts come from each tool’s own site, checked on %s.' % d),
            ('Is there a free Vinted reselling tool?',
             'Yes. SNYPD has a free plan: your first search runs 24/7 with alerts for the first @@trial_days@@ days, then while the dashboard is open. '
             'Its price guide and profit calculator are free without an account. VintedCRM has a free plan, and Zipsale a free plan without auto-delisting.'),
            ('Do I need a bot to resell on Vinted?',
             'No. You can resell with Vinted’s own search and a spreadsheet. Tools save time on one job each: an alert tool watches your searches, '
             'a crosslister copies listings to other marketplaces. SNYPD only alerts; you open the listing and buy on Vinted yourself.'),
            ('Which crosslisting tools work with Vinted?',
             'On %s, Zipsale named Vinted among its marketplaces, for UK sellers. Vendoo did not name Vinted, Crosslist said it does not support users '
             'residing in the European Union, and Relistly showed Vinted as coming soon. Check the tool’s own site before you pay.' % d),
        ]
        title = 'Best Vinted Reselling Tools 2026: Sourcing, Listing, Admin | SNYPD'
        desc = ('The best Vinted reselling tools for each job: finding underpriced items, price research, crosslisting and bookkeeping. '
                'Facts from each tool’s own site, checked %s.' % d)
        h1 = 'Best Vinted reselling tools in 2026, by job'
        lead = ('No single tool does every reselling job on Vinted. Here is the tool to use for each one: finding stock, pricing it, '
                'listing it and keeping the books. We make SNYPD, the sourcing tool on this page, so every other fact links to the tool’s own site and its date.')
        sections = [
            ('answer', 'The short answer',
             '<ul><li><strong>Finding underpriced items (sourcing): SNYPD.</strong> It checks your Vinted searches about once a minute and sends a push '
             'alert when a new listing matches. Once a search has enough finds, it also shows how each new find’s price compares with that week’s finds. It never logs in to your Vinted account and never buys for you.</li>'
             '<li><strong>Price research:</strong> SNYPD’s free <a href="/vinted-price-guide">Vinted price guide</a> (asking prices for %d models) '
             'or ResellTrack (paid market research).</li>'
             '<li><strong>Crosslisting to Vinted:</strong> Zipsale, for UK sellers. Check before paying for any crosslister: on %s, Vendoo, '
             'Crosslist and Relistly did not offer Vinted as a live marketplace on their own sites.</li>'
             '<li><strong>Invoices and bookkeeping:</strong> VintedCRM (free plan) or a spreadsheet.</li></ul>' % (n, d)),
            ('compare', 'Vinted reselling tools compared', table +
             '<p class="ct-note">Each row except SNYPD’s is what the tool’s own website said on %s. Prices and features change: '
             'check the tool’s site before you pay.</p>' % d),
            ('sourcing', 'Sourcing: the job most tool lists skip',
             '<p>Your margin is mostly set when you buy. A well-priced listing is open to every buyer on Vinted, so seeing it early matters. '
             'Vinted’s own saved searches show a “+N” counter of new items when you open them; they do not send a notification for each new match '
             '(%s).</p>'
             '<p>SNYPD watches the searches you paste in, with all your Vinted filters, and alerts you on your phone or computer when a new listing matches. '
             '%s %s</p>'
             '<p>On paid plans, the Hunt Pass and the free trial, each find shows how its asking price compares with what the same search found that week, '
             'when there are enough finds in that condition to compare. You still open the listing and decide: SNYPD does not buy, message sellers or relist.</p>'
             '<p>Other alert tools work differently: some buy through your account, some alert only in Telegram or Discord. '
             'The <a href="/vinted-bot-comparison">Vinted bot comparison</a> puts them side by side, with sources.</p>'
             % (_ext(h435, 'Vinted Help'), g.SPEED_MEASURED['en'], g.VINTED_LAG['en'])),
            ('pricing', 'Price research: asking prices or sales data',
             '<p>Vinted does not publish what items sell for, so price tools use one of two sources. SNYPD’s <a href="/vinted-price-guide">price guide</a> '
             'and <a href="/vinted-price-checker">price checker</a> are free and use asking prices: the typical price for %d models by condition, '
             'from vinted.be listings observed %s to %s, with the method on the page. ResellTrack says it analyses Vinted sales in every country '
             'where Vinted operates, from €24 a month.</p>'
             '<p>Whichever you use, compare the same model, size and condition, then turn the figure into a buying limit with the '
             '<a href="/vinted-profit-calculator">profit calculator</a>.</p>' % (n, a, b)),
            ('listing', 'Listing and crosslisting: check Vinted support first',
             '<p>Crosslisting tools post one listing to several marketplaces, and many are built for US marketplaces. On %s: Vendoo’s site did not '
             'name Vinted among its marketplaces; Crosslist said it does not support users residing in the European Union; Relistly showed Vinted as '
             '“Soon”. Zipsale named Vinted among its marketplaces, said it uses the Vinted API and said it is made for the UK.</p>'
             '<p>Relisting and auto-posting extensions work inside your logged-in Vinted session, so they act as you. Read Vinted’s terms for your '
             'country before you let any tool act on your account.</p>' % d),
            ('admin', 'Invoices, bookkeeping and the Pro account',
             '<p>Once you resell regularly, you need records: what you paid, what you received and what is still in stock. VintedCRM offers CRM, '
             'invoicing and accounting for Vinted shops, with a free plan and paid plans from €12.99 a month excluding VAT. A spreadsheet with '
             'purchase price, date, costs and sale proceeds also works when you start.</p>'
             '<p>Vinted’s commercial-selling guidance says professional selling belongs on an eligible Pro account, and it excludes new commercial '
             'stock bought for resale (%s). No tool changes those rules.</p>' % _ext(h1120, 'Vinted Help')),
            ('account', 'Which tools act on your Vinted account?',
             '<ul><li><strong>Read-only:</strong> SNYPD watches public search results and never logs in. ResellTrack says it never asks for your '
             'Vinted credentials and that its extension reads the page you have open.</li>'
             '<li><strong>Through your session:</strong> relisting and auto-posting extensions, and autobuy bots, act inside your logged-in Vinted account.</li>'
             '<li><strong>Through an API:</strong> Zipsale says it uses the Vinted API.</li></ul>'
             '<p>A tool that never touches your account cannot list, relist or buy for you; a tool that does can. Decide which jobs you want '
             'automated, then read Vinted’s terms for your country.</p>'),
            ('questions', 'Questions', g.faq_html(faq)),
        ]
    else:
        rows = [
            ['<a href="/fr/bot-vinted">SNYPD</a>', 'Sourcing : alertes de nouvelles annonces, avec une comparaison de prix sur la semaine',
             'Oui : %s' % g.MARKETS_TEXT['fr'], 'Aucune connexion : surveille les résultats de recherche publics ; n’achète pas, n’écrit pas aux vendeurs',
             'Plan gratuit, 24h/24 les @@trial_days@@ premiers jours ; Pass 30 jours @@price:pass@@ une fois ; Solo @@price:solo@@ par mois'],
            [_ext(src['ResellTrack'], 'ResellTrack'), 'Étude de marché et de niches à partir des ventes Vinted',
             'Oui, dans tous les pays où Vinted est présent', 'Dit ne jamais demander tes identifiants Vinted ; son extension lit la page que tu as ouverte',
             '24 € par mois ; pas d’essai gratuit'],
            [_ext(src['Zipsale'], 'Zipsale'), 'Multi-publication et retrait automatique sur 8 plateformes',
             'Oui, pour les vendeurs au Royaume-Uni ; dit utiliser l’API Vinted', 'Connecte tes comptes de plateformes',
             'Dès 15 £ par mois + TVA ; plan gratuit sans retrait automatique'],
            [_ext(src['VintedCRM'], 'VintedCRM'), 'CRM, facturation et comptabilité d’une boutique Vinted',
             'Oui : conçu pour Vinted', 'Dit que son CRM ne demande ni ton mot de passe Vinted ni un jeton de session',
             'Plan gratuit ; payant dès 12,99 € HT par mois'],
            [_ext(src['Vendoo'], 'Vendoo'), 'Multi-publication', 'Vinted ne figure pas parmi les plateformes citées sur son site', 'Non précisé',
             '14,99 $ par mois en mensuel ; essai gratuit de 14 jours'],
            [_ext(src['Crosslist'], 'Crosslist'), 'Multi-publication', 'Non : dit ne pas accepter les utilisateurs résidant dans l’Union européenne',
             'Extension dans ton propre navigateur pour certaines plateformes', '29,99 $ par mois ; 20 annonces gratuites'],
            [_ext(src['Relistly'], 'Relistly'), 'Extension de publication croisée', 'Pas encore : Vinted est indiqué « Soon » (bientôt)',
             'Passe par les sessions de plateformes où tu es connecté', 'Pas de prix affiché ; essai gratuit de 7 jours'],
        ]
        table = g.table(['OUTIL', 'RÔLE', 'MARCHE AVEC VINTED ? (SON SITE)', 'TON COMPTE VINTED', 'OFFRE LA MOINS CHÈRE (SON SITE)'], rows, us_row=0)
        faq = [
            ('Quel est le meilleur outil pour la revente sur Vinted ?',
             'Cela dépend de la tâche. Pour trouver des articles sous-évalués, SNYPD t’alerte des nouvelles annonces qui correspondent à tes recherches '
             'et compare le prix de chaque trouvaille avec celles de la semaine quand il y a assez de données. Pour publier sur Vinted et ailleurs, Zipsale gère Vinted pour les vendeurs au Royaume-Uni. '
             'Pour la facturation, VintedCRM a un plan gratuit. Nous éditons SNYPD ; les autres informations viennent du site de chaque outil, consulté le %s.' % d),
            ('Existe-t-il un outil de revente Vinted gratuit ?',
             'Oui. SNYPD a un plan gratuit : ta première recherche tourne 24h/24 avec les alertes pendant les @@trial_days@@ premiers jours, puis tant que '
             'le tableau de bord est ouvert. Son guide des prix et son calculateur de marge sont gratuits sans compte. VintedCRM a un plan gratuit, '
             'et Zipsale un plan gratuit sans retrait automatique.'),
            ('Faut-il un bot pour faire de l’achat-revente sur Vinted ?',
             'Non. Tu peux revendre avec la recherche de Vinted et un tableur. Les outils font gagner du temps sur une tâche chacun : un outil d’alerte '
             'surveille tes recherches, un outil de multi-publication copie tes annonces sur d’autres plateformes. SNYPD alerte seulement ; tu ouvres '
             'l’annonce et tu achètes toi-même sur Vinted.'),
            ('Quels outils de multi-publication fonctionnent avec Vinted ?',
             'Le %s, Zipsale citait Vinted parmi ses plateformes, pour les vendeurs au Royaume-Uni. Vendoo ne citait pas Vinted, Crosslist indiquait ne pas '
             'accepter les utilisateurs résidant dans l’Union européenne et Relistly affichait Vinted comme bientôt disponible. Vérifie le site de l’outil '
             'avant de payer.' % d),
        ]
        title = 'Meilleurs outils de revente Vinted 2026 : sourcing, annonces | SNYPD'
        desc = ('Les meilleurs outils de revente Vinted pour chaque tâche : trouver des articles sous-évalués, étudier les prix, publier et facturer. '
                'Infos tirées du site de chaque outil, le %s.' % d)
        h1 = 'Meilleurs outils de revente Vinted en 2026, tâche par tâche'
        lead = ('Aucun outil ne fait tout le travail de revente sur Vinted. Voici l’outil à utiliser pour chaque tâche : trouver le stock, '
                'le prix, publier et tenir les comptes. Nous éditons SNYPD, l’outil de sourcing de cette page : chaque autre information renvoie au site '
                'de l’outil, avec sa date.')
        sections = [
            ('reponse', 'La réponse courte',
             '<ul><li><strong>Trouver des articles sous-évalués (sourcing) : SNYPD.</strong> Il vérifie tes recherches Vinted environ une fois par minute '
             'et envoie une notification quand une nouvelle annonce correspond. Quand une recherche a assez de trouvailles, il compare aussi le prix de chaque nouvelle '
             'avec celles de la semaine. Il ne se connecte jamais '
             'à ton compte Vinted et n’achète jamais à ta place.</li>'
             '<li><strong>Étude des prix :</strong> le <a href="/fr/guide-prix-vinted">guide des prix Vinted</a> gratuit de SNYPD (prix demandés '
             'pour %d modèles) ou ResellTrack (étude de marché payante).</li>'
             '<li><strong>Publier sur Vinted et ailleurs :</strong> Zipsale, pour les vendeurs au Royaume-Uni. Vérifie avant de payer un outil de '
             'multi-publication : le %s, Vendoo, Crosslist et Relistly ne proposaient pas Vinted comme plateforme active sur leur propre site.</li>'
             '<li><strong>Factures et comptabilité :</strong> VintedCRM (plan gratuit) ou un tableur.</li></ul>' % (n, d)),
            ('comparatif', 'Outils de revente Vinted comparés', table +
             '<p class="ct-note">Chaque ligne, sauf celle de SNYPD, reprend ce que le site de l’outil indiquait le %s. Prix et fonctions évoluent : '
             'vérifie le site de l’outil avant de payer.</p>' % d),
            ('sourcing', 'Le sourcing : la tâche que la plupart des listes oublient',
             '<p>Ta marge se joue surtout à l’achat. Une annonce bien placée est visible par tous les acheteurs de Vinted : la voir tôt compte. '
             'Les recherches enregistrées de Vinted affichent un compteur « +N » de nouveaux articles quand tu les ouvres ; elles n’envoient pas de '
             'notification pour chaque nouvelle annonce (%s).</p>'
             '<p>SNYPD surveille les recherches que tu colles, avec tous tes filtres Vinted, et t’alerte sur ton téléphone ou ton ordinateur quand une '
             'nouvelle annonce correspond. %s %s</p>'
             '<p>Avec un plan payant, le Pass 30 jours et l’essai gratuit, chaque trouvaille indique où se situe son prix demandé par rapport à ce que '
             'la même recherche a trouvé dans la semaine, quand il y a assez d’annonces dans cet état pour comparer. Tu ouvres l’annonce et tu décides : '
             'SNYPD n’achète pas, n’écrit pas aux vendeurs et ne republie pas.</p>'
             '<p>D’autres outils d’alerte fonctionnent autrement : certains achètent via ton compte, d’autres alertent seulement dans Telegram ou Discord. '
             'Le <a href="/fr/comparatif-bot-vinted">comparatif des bots Vinted</a> les met côte à côte, avec les sources.</p>'
             % (_ext(h435, 'aide Vinted'), g.SPEED_MEASURED['fr'], g.VINTED_LAG['fr'])),
            ('prix', 'Étudier les prix : prix demandés ou données de ventes',
             '<p>Vinted ne publie pas le prix final des ventes : les outils de prix s’appuient donc sur l’une de deux sources. Le '
             '<a href="/fr/guide-prix-vinted">guide des prix</a> et l’<a href="/fr/estimer-prix-vinted">outil de prix</a> de SNYPD sont gratuits et '
             'utilisent les prix demandés : le prix typique de %d modèles par état, à partir d’annonces vinted.be observées du %s au %s, avec la méthode '
             'sur la page. ResellTrack dit analyser les ventes Vinted dans tous les pays où Vinted est présent, à partir de 24 € par mois.</p>'
             '<p>Dans tous les cas, compare le même modèle, la même taille et le même état, puis transforme le chiffre en prix d’achat maximum avec le '
             '<a href="/fr/calculateur-marge-vinted">calculateur de marge</a>.</p>' % (n, a, b)),
            ('publication', 'Publier et multi-publier : vérifie d’abord la prise en charge de Vinted',
             '<p>Les outils de multi-publication diffusent une annonce sur plusieurs plateformes, et beaucoup sont conçus pour les plateformes américaines. '
             'Le %s : le site de Vendoo ne citait pas Vinted parmi ses plateformes ; Crosslist indiquait ne pas accepter les utilisateurs résidant dans '
             'l’Union européenne ; Relistly affichait Vinted avec la mention « Soon ». Zipsale citait Vinted parmi ses plateformes, disait utiliser '
             'l’API Vinted et être conçu pour le Royaume-Uni.</p>'
             '<p>Les extensions de republication et de publication automatique travaillent dans ta session Vinted connectée : elles agissent en ton nom. '
             'Lis les conditions de Vinted dans ton pays avant de laisser un outil agir sur ton compte.</p>' % d),
            ('gestion', 'Factures, comptabilité et compte Pro',
             '<p>Dès que tu revends régulièrement, il te faut un suivi : ce que tu as payé, ce que tu as encaissé et ce qui reste en stock. VintedCRM '
             'propose CRM, facturation et comptabilité pour les boutiques Vinted, avec un plan gratuit et des plans payants dès 12,99 € HT par mois. '
             'Un tableur avec prix d’achat, date, coûts et recette de vente suffit aussi pour commencer.</p>'
             '<p>L’aide Vinted sur les ventes commerciales renvoie la vente professionnelle vers un compte Pro éligible et exclut les nouveaux stocks '
             'commerciaux achetés pour être revendus (%s). Aucun outil ne change ces règles.</p>' % _ext(h1120, 'aide Vinted')),
            ('compte', 'Quels outils agissent sur ton compte Vinted ?',
             '<ul><li><strong>Lecture seule :</strong> SNYPD surveille des résultats de recherche publics et ne se connecte jamais. ResellTrack dit ne '
             'jamais demander tes identifiants Vinted et que son extension lit la page que tu as ouverte.</li>'
             '<li><strong>Via ta session :</strong> les extensions de republication et de publication automatique, ainsi que les bots d’achat '
             'automatique, agissent dans ton compte Vinted connecté.</li>'
             '<li><strong>Via une API :</strong> Zipsale dit utiliser l’API Vinted.</li></ul>'
             '<p>Un outil qui ne touche jamais ton compte ne peut ni publier, ni republier, ni acheter pour toi ; un outil qui le touche le peut. '
             'Décide quelles tâches tu veux automatiser, puis lis les conditions de Vinted dans ton pays.</p>'),
            ('questions', 'Questions', g.faq_html(faq)),
        ]
    site = 'https://www.snypd.store'
    items = [('SNYPD', site + '/')] + list(TOOL_SOURCES[:3])
    itemlist = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': h1,
                'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': nm, 'url': u} for i, (nm, u) in enumerate(items)]}
    return title, desc, h1, lead, sections, [g.faq_ld(faq), itemlist]


def tools_sources(lang):
    h1120, h435, checked435 = _help(lang)
    fr = lang == 'fr'
    links = ''.join('<li>%s</li>' % _ext(u, nm) for nm, u in TOOL_SOURCES)
    links += '<li>%s</li><li>%s</li>' % (_ext(h1120, 'Vinted — ' + ('Ventes commerciales' if fr else 'Commercial selling')),
                                         _ext(h435, 'Vinted — ' + ('Recherches enregistrées' if fr else 'Save your searches')))
    text = (('Informations sur les outils tirées du site de chaque outil, consulté le %s. Aide Vinted : ventes commerciales consultée le 2 novembre 2026, '
             'recherches enregistrées le %s. SNYPD est notre produit ; ses informations viennent du produit en service.') if fr else
            ('Tool facts from each tool’s own website, read on %s. Vinted Help: commercial selling checked on 2 November 2026, saved searches on %s. '
             'SNYPD is our product; its facts come from the running product.')) % (TOOLS_CHECKED[lang], checked435)
    return '<section id="sources"><h2>Sources</h2><p>%s</p><ul>%s</ul></section>' % (text, links)


def money(lang, index, g):
    """/how-to-make-money-on-vinted: selling vs reselling, with published asking-price gaps. Returns 6 values like tools()."""
    fr = lang == 'fr'
    items = {x['id']: x for x in index['items']}
    picked = [items[i] for i in MONEY_ITEMS]
    a, b = index['window']['from'], index['window']['to']
    h1120, h435, _ = _help(lang)
    n = len(index['items'])
    rows = []
    for it in picked:
        name = html.escape(it['name'].get(lang, it['name']['en']))
        rows.append(['<a href="%s">%s</a>' % (it['url'][lang], name), _eur(it['p25'], lang), _eur(it['typical'], lang),
                     _eur(it['typical'] - it['p25'], lang), ('{:,}'.format(it['n'])).replace(',', ' ' if fr else ',')])

    def example(it):
        fee = _buyer_fee(it['p25'])
        return (html.escape(it['name'].get(lang, it['name']['en'])), _eur(it['p25'], lang), _eur(fee, lang),
                _eur(it['typical'], lang), _eur(it['typical'] - it['p25'] - fee, lang))
    ex1, ex2 = example(picked[0]), example(picked[-1])
    if not fr:
        table = g.table(['MODEL', 'CHEAPEST QUARTER ASKED', 'TYPICAL ASK', 'GAP', 'LISTINGS'], rows)
        faq = [
            ('How much money can you make on Vinted?',
             'There is no reliable average: it depends on what you sell, what you paid for it and how many items you list. In our data the gap between '
             'the cheapest quarter of listings and the typical ask was %s for %s and %s for %s, but a gap is not profit until the item sells. '
             'We make no income promises.' % (_eur(picked[0]['typical'] - picked[0]['p25'], 'en'), ex1[0],
                                             _eur(picked[-1]['typical'] - picked[-1]['p25'], 'en'), ex2[0])),
            ('Is reselling on Vinted worth it?',
             'It can be when you know the category and buy below a limit you calculated in advance. Count every cost: the Buyer Protection fee and shipping '
             'when you buy, packaging, unsold stock and your time.'),
            ('What sells best on Vinted?',
             'Vinted does not publish sales rankings. Our <a href="/best-brands-to-resell-on-vinted">brand and model guide</a> lists models with enough '
             'listings to compare prices: a starting point for research, not a sales ranking.'),
            ('Do you pay tax on Vinted sales?',
             'It depends on your country and on whether you sell as a business. Selling your own used belongings is often treated differently from '
             'regular reselling for profit; check your tax authority’s guidance. This page is not tax advice.'),
        ]
        title = 'How to Make Money on Vinted: Selling vs Reselling (2026) | SNYPD'
        desc = ('Two ways to make money on Vinted: sell what you own, or resell. Seller fees, real asking-price gaps on %d models, buying limits '
                'and tools. No income promises.' % len(picked))
        h1 = 'How to make money on Vinted'
        lead = ('There are two ways: sell what you already own, or buy second-hand items below their usual asking price and resell them. '
                'Both start from the same rule: on Vinted’s euro sites, the seller keeps the full item price.')
        sections = [
            ('answer', 'The short answer',
             '<ol><li>Start by selling what you own. On Vinted’s euro sites selling is free: the seller receives the full item price and the buyer pays '
             'the Buyer Protection fee (<a href="/vinted-fees">Vinted fees</a>).</li>'
             '<li>Price each item against the same model and condition with the <a href="/vinted-price-checker">price checker</a>.</li>'
             '<li>To resell, pick one category you can judge and set a maximum buying price before you search '
             '(<a href="/vinted-profit-calculator">profit calculator</a>).</li>'
             '<li>Watch that search for new listings under your limit: the cheapest ones are the ones other buyers want too.</li>'
             '<li>Record every purchase and sale, and follow Vinted’s rules: regular professional selling belongs on a Pro account.</li></ol>'
             '<p>We publish no income figures: what you make depends on what you buy, at what price, and what sells.</p>'),
            ('selling', 'Way 1: sell what you already own',
             '<p>This is the low-risk start, because you buy no stock. On Vinted’s euro sites the buyer pays a Buyer Protection fee of €0.70 plus 5% of '
             'the item price on top of the price, and the seller receives the full item price. The <a href="/vinted-fees">Vinted fee calculator</a> '
             'shows the fee for any price and how we checked it.</p>'
             '<ul><li>Price against the same model, size and condition, not against the brand in general.</li>'
             '<li>Photograph labels, measurements and any flaws: every question your listing answers is one a buyer does not have to ask.</li>'
             '<li>Name the exact model and size as written on the label.</li></ul>'),
            ('reselling', 'Way 2: resell. Your margin is set when you buy',
             '<p>Reselling means buying below what similar items usually ask and selling near the typical price. Our own data shows how wide that gap '
             'can be. For each model below, “cheapest quarter asked” is the price a quarter of listings were at or below; “typical ask” is the median.</p>'
             + table +
             '<p>Asking prices on vinted.be, observed %s to %s, all conditions together, so part of each gap is condition. Asking prices are not completed '
             'sales, and a listing in the cheapest quarter is not always a bargain: check its condition. Prices by condition for %d models are in the '
             '<a href="/vinted-price-guide">Vinted price guide</a>.</p>' % (a, b, n)),
            ('maths', 'Do the maths before you buy',
             '<p>Two examples from the table, before the shipping you pay to receive the item, packaging and your time:</p>'
             '<ul><li><strong>%s:</strong> buy at %s and pay %s Buyer Protection. If it then sells at the typical %s, you receive the full %s: '
             '%s left.</li>'
             '<li><strong>%s:</strong> buy at %s and pay %s Buyer Protection. If it then sells at the typical %s, %s left.</li></ul>'
             '<p>Small tickets leave little room once shipping is counted; a lower sale price, or no sale, changes everything. Enter your own costs in the '
             '<a href="/vinted-profit-calculator">profit calculator</a> to get a maximum buying price, then use it as the price filter of your Vinted search.</p>'
             % (ex1[0], ex1[1], ex1[2], ex1[3], ex1[3], ex1[4], ex2[0], ex2[1], ex2[2], ex2[3], ex2[4])),
            ('speed', 'Finding the cheap listings first',
             '<p>Listings in the cheapest quarter are visible to every buyer on Vinted. Vinted’s saved searches show a counter of new items when you open '
             'them, not a notification for each match (%s). That is the gap an alert tool fills.</p>'
             '<p>SNYPD watches your search, with your price limit and filters, and sends a push alert when a new listing matches. %s It never logs in '
             'to your Vinted account and never buys: you open the listing and decide. For the other jobs (pricing, crosslisting, bookkeeping), see the '
             '<a href="/best-vinted-reselling-tools">best Vinted reselling tools</a>.</p>' % (_ext(h435, 'Vinted Help'), g.SPEED_MEASURED['en'])),
            ('rules', 'Rules, records and tax',
             '<p>Vinted’s commercial-selling guidance says professional selling belongs on an eligible Pro account and excludes new commercial stock '
             'bought for resale, even for Pro sellers (%s). Whether your reselling counts as a business, and what tax you owe, depends on your country: '
             'check your tax authority’s own guidance.</p>'
             '<p>Keep a record of each item: purchase price and date, costs, sale proceeds and what is still unsold. That record is what tells you '
             'whether reselling actually makes you money. The step-by-step method is in <a href="/how-to-resell-on-vinted">how to resell on Vinted</a>.</p>'
             % _ext(h1120, 'Vinted Help')),
            ('questions', 'Questions', g.faq_html(faq)),
        ]
    else:
        table = g.table(['MODÈLE', 'QUART LE MOINS CHER', 'PRIX TYPIQUE DEMANDÉ', 'ÉCART', 'ANNONCES'], rows)
        faq = [
            ('Combien peut-on gagner sur Vinted ?',
             'Il n’existe pas de moyenne fiable : cela dépend de ce que tu vends, du prix payé et du nombre d’articles mis en vente. Dans nos données, '
             'l’écart entre le quart des annonces les moins chères et le prix typique demandé était de %s pour le modèle %s et de %s pour le modèle %s, mais un écart '
             'n’est un bénéfice qu’une fois l’article vendu. Nous ne promettons aucun revenu.'
             % (_eur(picked[0]['typical'] - picked[0]['p25'], 'fr'), ex1[0], _eur(picked[-1]['typical'] - picked[-1]['p25'], 'fr'), ex2[0])),
            ('L’achat-revente sur Vinted est-il rentable ?',
             'Il peut l’être si tu connais la catégorie et que tu achètes sous un plafond calculé à l’avance. Compte chaque coût : Protection acheteurs '
             'et port à l’achat, emballage, invendus et ton temps.'),
            ('Qu’est-ce qui se vend le mieux sur Vinted ?',
             'Vinted ne publie pas de classement des ventes. Notre <a href="/fr/meilleures-marques-revente-vinted">guide des marques et modèles</a> '
             'liste des modèles avec assez d’annonces pour comparer les prix : un point de départ pour étudier, pas un classement des ventes.'),
            ('Faut-il déclarer ses ventes Vinted aux impôts ?',
             'Cela dépend de ton pays et du fait que tu vendes ou non à titre professionnel. Vendre tes propres affaires d’occasion est souvent traité '
             'différemment de l’achat-revente régulier ; consulte les informations de ton administration fiscale. Cette page n’est pas un conseil fiscal.'),
        ]
        title = 'Gagner de l’argent sur Vinted : vendre ou revendre (2026) | SNYPD'
        desc = ('Deux façons de gagner de l’argent sur Vinted : vendre tes affaires ou faire de l’achat-revente. Frais, écarts de prix réels sur %d '
                'modèles, budget d’achat et outils. Sans promesse de revenu.' % len(picked))
        h1 = 'Gagner de l’argent sur Vinted'
        lead = ('Il y a deux façons : vendre ce que tu possèdes déjà, ou acheter des articles d’occasion sous leur prix habituel et les revendre. '
                'Les deux partent de la même règle : sur les sites Vinted en euros, le vendeur reçoit le prix entier de l’article.')
        sections = [
            ('reponse', 'La réponse courte',
             '<ol><li>Commence par vendre tes affaires. Sur les sites Vinted en euros, vendre est gratuit : le vendeur reçoit le prix entier et '
             'l’acheteur paie la Protection acheteurs (<a href="/fr/frais-vinted">frais Vinted</a>).</li>'
             '<li>Fixe chaque prix en comparant le même modèle dans le même état avec l’<a href="/fr/estimer-prix-vinted">outil de prix</a>.</li>'
             '<li>Pour revendre, choisis une catégorie que tu sais évaluer et fixe un prix d’achat maximum avant de chercher '
             '(<a href="/fr/calculateur-marge-vinted">calculateur de marge</a>).</li>'
             '<li>Surveille cette recherche pour repérer les nouvelles annonces sous ton plafond : les moins chères intéressent aussi les autres acheteurs.</li>'
             '<li>Note chaque achat et chaque vente, et respecte les règles de Vinted : la vente professionnelle régulière relève d’un compte Pro.</li></ol>'
             '<p>Nous ne publions aucun chiffre de revenu : ce que tu gagnes dépend de ce que tu achètes, à quel prix, et de ce qui se vend.</p>'),
            ('vendre', 'Façon 1 : vendre ce que tu possèdes déjà',
             '<p>C’est le départ le moins risqué, car tu n’achètes aucun stock. Sur les sites Vinted en euros, l’acheteur paie une Protection acheteurs '
             'de 0,70 € plus 5 % du prix de l’article en plus du prix, et le vendeur reçoit le prix entier. Le <a href="/fr/frais-vinted">calculateur '
             'de frais Vinted</a> donne les frais pour tout prix et explique notre vérification.</p>'
             '<ul><li>Compare avec le même modèle, la même taille et le même état, pas avec la marque en général.</li>'
             '<li>Photographie étiquettes, mesures et défauts : chaque question à laquelle ton annonce répond, l’acheteur n’a pas à la poser.</li>'
             '<li>Indique le modèle exact et la taille écrits sur l’étiquette.</li></ul>'),
            ('revendre', 'Façon 2 : revendre. Ta marge se joue à l’achat',
             '<p>L’achat-revente consiste à acheter sous le prix habituellement demandé pour des articles similaires, puis à vendre près du prix typique. '
             'Nos données montrent l’ampleur de cet écart. Pour chaque modèle, « quart le moins cher » est le prix sous lequel se trouvait un quart des '
             'annonces ; « prix typique » est la médiane.</p>'
             + table +
             '<p>Prix demandés sur vinted.be, observés du %s au %s, tous états confondus : une partie de chaque écart vient de l’état. Les prix demandés '
             'ne sont pas des ventes conclues, et une annonce du quart le moins cher n’est pas toujours une bonne affaire : vérifie son état. Les prix par '
             'état de %d modèles sont dans le <a href="/fr/guide-prix-vinted">guide des prix Vinted</a>.</p>' % (a, b, n)),
            ('calcul', 'Fais le calcul avant d’acheter',
             '<p>Deux exemples tirés du tableau, avant le port payé pour recevoir l’article, l’emballage et ton temps :</p>'
             '<ul><li><strong>%s :</strong> achat à %s et %s de Protection acheteurs. Revendu au prix typique de %s, tu reçois les %s : '
             'il reste %s.</li>'
             '<li><strong>%s :</strong> achat à %s et %s de Protection acheteurs. Revendu au prix typique de %s, il reste %s.</li></ul>'
             '<p>Les petits prix laissent peu de marge une fois le port compté ; un prix de vente plus bas, ou pas de vente, change tout. Entre tes propres '
             'coûts dans le <a href="/fr/calculateur-marge-vinted">calculateur de marge</a> pour obtenir un prix d’achat maximum, puis utilise-le comme '
             'filtre de prix de ta recherche Vinted.</p>'
             % (ex1[0], ex1[1], ex1[2], ex1[3], ex1[3], ex1[4], ex2[0], ex2[1], ex2[2], ex2[3], ex2[4])),
            ('vitesse', 'Repérer les annonces les moins chères en premier',
             '<p>Les annonces du quart le moins cher sont visibles par tous les acheteurs de Vinted. Les recherches enregistrées de Vinted affichent un '
             'compteur de nouveaux articles quand tu les ouvres, pas une notification pour chaque annonce (%s). C’est ce manque que comble un outil d’alerte.</p>'
             '<p>SNYPD surveille ta recherche, avec ton plafond de prix et tes filtres, et envoie une notification quand une nouvelle annonce correspond. '
             '%s Il ne se connecte jamais à ton compte Vinted et n’achète jamais : tu ouvres l’annonce et tu décides. Pour les autres tâches (prix, '
             'multi-publication, comptabilité), vois les <a href="/fr/meilleurs-outils-revente-vinted">meilleurs outils de revente Vinted</a>.</p>'
             % (_ext(h435, 'aide Vinted'), g.SPEED_MEASURED['fr'])),
            ('regles', 'Règles, suivi et impôts',
             '<p>L’aide Vinted sur les ventes commerciales renvoie la vente professionnelle vers un compte Pro éligible et exclut les nouveaux stocks '
             'commerciaux achetés pour être revendus, même pour les vendeurs Pro (%s). Savoir si ton achat-revente est une activité professionnelle, et '
             'quels impôts tu dois, dépend de ton pays : consulte ton administration fiscale.</p>'
             '<p>Note chaque article : prix et date d’achat, coûts, recette de vente et invendus. C’est ce suivi qui te dit si l’achat-revente te '
             'rapporte vraiment. La méthode pas à pas est dans <a href="/fr/achat-revente-vinted">achat-revente sur Vinted</a>.</p>'
             % _ext(h1120, 'aide Vinted')),
            ('questions', 'Questions', g.faq_html(faq)),
        ]
    return title, desc, h1, lead, sections, [g.faq_ld(faq)]


def calculator(lang):
    fr = lang == 'fr'
    fields = [
        ('sale', 'Expected sale proceeds', 'Recette de vente prévue', '40'),
        ('buy', 'Item purchase price', 'Prix d’achat de l’article', '20'),
        ('inbound', 'Buying fees and inbound delivery', 'Frais d’achat et livraison reçue', '5'),
        ('outbound', 'Packaging and delivery you pay', 'Emballage et envoi à ta charge', '2'),
        ('other', 'Other costs for this item', 'Autres coûts pour cet article', '0'),
        ('target', 'Target profit', 'Bénéfice visé', '10'),
    ]
    inputs = ''.join('<label for="profit-%s">%s (<span data-currency-label>EUR</span>)</label>'
                     '<input id="profit-%s" name="%s" type="text" inputmode="decimal" value="%s" '
                     'maxlength="10" required aria-describedby="profit-help profit-error">'
                     % (key, french if fr else english, key, key, value)
                     for key, english, french, value in fields)
    outputs = [('profit', 'Estimated profit', 'Bénéfice estimé'),
               ('cost', 'Total costs', 'Coûts totaux'), ('margin', 'Profit margin', 'Marge sur recette'),
               ('roi', 'Return on all entered costs', 'Rendement sur tous les coûts saisis'),
               ('break-even', 'Break-even sale proceeds', 'Recette au seuil de rentabilité'),
               ('budget', 'Maximum item purchase price for your target', 'Prix d’achat maximal pour ton objectif')]
    results = ''.join('<div><dt>%s</dt><dd data-value="%s">—</dd></div>' % (f if fr else e, key)
                      for key, e, f in outputs)
    help_text = ('Les montants préremplis sont fictifs. Utilise la même devise partout. Le choix EUR/GBP ne convertit aucun montant. '
                 'Accepte le point ou la virgule décimale, sans séparateur de milliers.' if fr else
                 'The prefilled amounts are hypothetical. Use one currency throughout. Choosing EUR/GBP does not convert amounts. '
                 'Use a decimal point or comma, with no thousands separators.')
    form = ('<style>.profit-form{border:1px solid #555560;padding:24px;border-radius:12px;background:#111116}'
            '.profit-fields{display:grid;grid-template-columns:minmax(0,1fr) minmax(110px,160px);gap:14px;align-items:center}'
            '.profit-fields label{font-size:15px;line-height:1.5}.profit-form input,.profit-form select{box-sizing:border-box;'
            'width:100%%;min-width:0;min-height:44px;border:1px solid #696975;border-radius:6px;padding:10px;'
            'background:#18181f;color:#fff;font:inherit}.profit-form input[aria-invalid=true]{border-color:#ff9b9b}'
            '.profit-actions{display:flex;flex-wrap:wrap;gap:12px;margin:20px 0}.profit-actions button{min-height:44px;'
            'border:1px solid #888;border-radius:6px;padding:10px 18px;background:#c4f46f;color:#101010;font:inherit;cursor:pointer}'
            '.profit-actions button[type=reset]{background:#24242b;color:#fff}.profit-form :focus-visible{outline:3px solid #c4f46f;outline-offset:3px}'
            '.profit-error{color:#ffbaba}.profit-results dl{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:0}'
            '.profit-results dl>div{padding:12px;border:1px solid #555560;border-radius:6px}.profit-results dt{font-size:13px;line-height:1.5}'
            '.profit-results dd{font-size:22px;margin:8px 0 0;overflow-wrap:anywhere}.profit-results dl>div:last-child{grid-column:1/-1}'
            '@media(max-width:520px){.profit-form{padding:16px}.profit-fields{grid-template-columns:1fr;gap:8px}'
            '.profit-fields input,.profit-fields select{margin-bottom:12px}.profit-results dl{grid-template-columns:1fr}}</style>'
            '<form class="profit-form" data-profit novalidate><p id="profit-help">%s</p><div class="profit-fields">'
            '<label for="profit-currency">%s</label><select id="profit-currency" name="currency">'
            '<option value="EUR">EUR — euro</option><option value="GBP">GBP — pound sterling</option></select>%s</div>'
            '<div class="profit-actions"><button type="submit">%s</button><button type="reset">%s</button></div>'
            '<p class="profit-error" id="profit-error" data-profit-error role="alert"></p>'
            '<div class="profit-results" data-profit-result aria-live="polite" aria-atomic="true" hidden><dl>%s</dl><p><a data-profit-builder>%s</a></p></div>'
            '<noscript><p>%s</p></noscript></form><script src="/assets/profit-calculator.js" defer></script>'
            % (help_text, 'Devise' if fr else 'Currency', inputs, 'Calculer' if fr else 'Calculate',
               'Réinitialiser l’exemple' if fr else 'Reset example', results,
               'Utiliser ce plafond dans le créateur de recherche' if fr else 'Use this buying limit in the search builder',
               'Active JavaScript pour le calcul interactif. Les formules et l’exemple restent disponibles ci-dessous.' if fr else
               'Enable JavaScript for the interactive calculation. The formulas and worked example remain available below.'))
    if not fr:
        title = 'Vinted Profit Calculator: Margin, ROI & Buying Budget | SNYPD'
        desc = 'Calculate Vinted resale profit, margin, break-even price and maximum buying budget. Free EUR/GBP calculator using your own purchase and delivery costs.'
        h1 = 'Vinted profit calculator'
        lead = 'Check whether a possible resale leaves enough room for your costs and target profit. Change the example amounts to your own figures; no account is needed.'
        sections = [
            ('calculator', 'Calculate profit and a buying limit', form),
            ('inputs', 'Which amounts should you enter?', '<p><strong>Sale proceeds:</strong> the amount you expect to receive for the item. If a selling charge has already been deducted from that figure, do not enter it again. Do not include postage paid directly by the buyer unless you also receive and account for that money.</p><p><strong>Purchase price:</strong> the item price you pay. Put buyer charges and delivery to you in the buying-cost field. Put packaging and any delivery you personally fund in the next field. Use “other costs” for item-specific expenses such as cleaning, repairs or applicable charges that you have not already counted.</p><p><strong>Target profit:</strong> your desired amount after those entered costs. All fields must use the same currency. There are no automatic tax, VAT, buyer-protection or shipping-rate assumptions. Include costs relevant to your circumstances yourself; the result is before costs and taxes you leave out.</p>'),
            ('formulas', 'How are profit, margin and ROI calculated?', '<ul><li>Total costs = purchase price + buying costs + packaging/delivery + other costs.</li><li>Estimated profit = sale proceeds − total costs.</li><li>Profit margin = profit ÷ sale proceeds × 100.</li><li>ROI here = profit ÷ <strong>all entered costs</strong> × 100.</li><li>Break-even proceeds = total entered costs.</li><li>Maximum item price = sale proceeds − non-item costs − target profit.</li></ul><p>A margin needs positive sale proceeds; ROI needs positive costs. The tool displays “Not defined” when the denominator is zero. Negative profit remains visible as a loss. A negative buying limit means even a free item would not meet the target at those costs.</p>'),
            ('example', 'Worked example: €40 proceeds and €27 costs', '<p>The initial values are an example, not a SNYPD earnings claim: €40 proceeds, €20 purchase, €5 buying costs and €2 packaging/delivery give €27 total costs. Profit is €13, margin is 32.5%, and return on those costs is about 48.1%. Break-even proceeds are €27.</p><p>For a €10 profit target, the maximum item purchase price is €23. Try reducing expected proceeds to €30: profit falls to €3 and the buying limit becomes €13. Lower prices, unsold inventory and extra costs can change the outcome; this is a single-item scenario rather than a forecast of business income.</p>'),
            ('fees', 'Does Vinted charge a selling fee?', '<p>The linked UK Vinted help page describes standard listing and selling as free, with buyer protection applied at checkout. That does not make acquiring stock, packaging, optional services or running a resale activity cost-free. Check your own marketplace and account terms, then enter actual costs without counting them twice.</p><p>This calculator is independent of Vinted. It does not access your account, verify a listing or establish whether professional selling is permitted for you. Vinted’s commercial-selling rules apply; consult them before sourcing items for regular resale.</p>'),
            ('use', 'Use your buying limit in a search', '<p>Compare an exact model and condition in the <a href="/vinted-price-checker">price checker</a>. Those references are asking prices, so choose a cautious proceeds estimate rather than treating a median as a guaranteed sale.</p><p>Set your chosen item-price ceiling and other filters on Vinted, check the checkout total, then save that filtered search in SNYPD for new-listing monitoring. The tool does not automatically copy currency or amounts to a search, change a listing or buy anything. Entered amounts are calculated in your browser and are not sent by the calculator to SNYPD analytics or a server.</p>'),
        ]
    else:
        title = 'Calculateur de marge Vinted : bénéfice, rendement et budget | SNYPD'
        desc = 'Calcule ton bénéfice de revente Vinted, ta marge, ton seuil de rentabilité et ton prix d’achat maximal. Outil gratuit en euros ou livres, avec tes frais.'
        h1 = 'Calculateur de marge Vinted'
        lead = 'Vérifie si une revente laisse assez de place à tes coûts et à ton bénéfice visé. Remplace les montants fictifs par tes chiffres, sans créer de compte.'
        sections = [
            ('calculator', 'Calcule ton bénéfice et ton plafond d’achat', form),
            ('montants', 'Quels montants saisir ?', '<p><strong>Recette prévue :</strong> la somme que tu penses recevoir pour l’article. Si une commission a déjà été retirée de ce montant, ne la saisis pas une seconde fois. N’ajoute pas les frais de port payés directement par l’acheteur si tu ne reçois pas cette somme.</p><p><strong>Prix d’achat :</strong> le prix de l’article que tu paies. Les frais acheteur et la livraison jusqu’à toi vont dans les frais d’achat. Ajoute ensuite l’emballage et l’envoi que tu finances toi-même. Réserve les autres coûts aux dépenses de cet article : nettoyage, réparation ou frais applicables non encore comptés.</p><p><strong>Bénéfice visé :</strong> la somme souhaitée après les coûts saisis. Utilise la même devise dans tous les champs. L’outil ne présume aucun taux de taxe, TVA, protection acheteur ou livraison. Ajoute toi-même les dépenses qui te concernent : le résultat reste avant les coûts et impôts que tu ne saisis pas.</p>'),
            ('formules', 'Comment calculer bénéfice, marge et rendement ?', '<ul><li>Coûts totaux = achat + frais d’achat + emballage/envoi + autres coûts.</li><li>Bénéfice estimé = recette − coûts totaux.</li><li>Marge sur recette = bénéfice ÷ recette × 100.</li><li>Rendement ici = bénéfice ÷ <strong>tous les coûts saisis</strong> × 100.</li><li>Recette au seuil de rentabilité = coûts totaux.</li><li>Prix d’achat maximal = recette − coûts hors article − bénéfice visé.</li></ul><p>La marge exige une recette positive ; le rendement exige des coûts positifs. Le résultat affiche « Non défini » si le dénominateur vaut zéro. Une perte reste affichée. Un plafond d’achat négatif signifie que même un article gratuit ne permet pas d’atteindre cet objectif avec ces frais.</p>'),
            ('exemple', 'Exemple : 40 € de recette et 27 € de coûts', '<p>Les valeurs initiales illustrent le calcul, pas une promesse de revenus SNYPD : 40 € de recette, 20 € d’achat, 5 € de frais d’achat et 2 € d’emballage/envoi donnent 27 € de coûts. Le bénéfice est de 13 €, la marge de 32,5 % et le rendement sur ces coûts d’environ 48,1 %. Le seuil de rentabilité est de 27 € de recette.</p><p>Pour un objectif de 10 €, le plafond d’achat de l’article est de 23 €. Si la recette prévue tombe à 30 €, le bénéfice devient 3 € et le plafond d’achat 13 €. Une baisse de prix, des invendus ou de nouveaux frais modifient le résultat : c’est un scénario pour un article, pas une prévision de revenu professionnel.</p>'),
            ('frais', 'Y a-t-il des frais vendeur sur Vinted ?', '<p>La page d’aide française citée décrit la mise en vente et la vente standard comme gratuites. Cela ne supprime pas les frais pour acquérir l’article, l’emballer, utiliser des services optionnels ou exercer une activité de revente. Vérifie les conditions de ton marché et de ton compte, puis saisis tes coûts réels une seule fois.</p><p>Ce calculateur est indépendant de Vinted. Il ne consulte pas ton compte, ne vérifie pas l’annonce et ne détermine pas si tu peux exercer une activité professionnelle. Consulte les règles Vinted sur la vente commerciale avant d’acheter pour une revente régulière.</p>'),
            ('utiliser', 'Applique ton plafond dans une recherche', '<p>Compare un modèle et un état précis dans l’<a href="/fr/estimer-prix-vinted">outil de prix</a>. Ses repères sont des prix demandés : choisis une recette prudente au lieu de prendre la médiane pour un prix de vente garanti.</p><p>Règle ton prix maximum et tes autres filtres sur Vinted, contrôle le total à payer, puis enregistre cette recherche dans SNYPD pour surveiller les nouvelles annonces. Aucun montant ni devise n’est copié automatiquement ; l’outil ne modifie aucune annonce et n’achète rien. Les calculs restent dans ton navigateur : le calculateur n’envoie pas les montants à un serveur ou aux outils de mesure SNYPD.</p>'),
        ]
    return title, desc, h1, lead, sections
