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
}
LABELS = {
    'en': ['How to resell on Vinted', 'Brands and models to research', 'Resale profit calculator'],
    'fr': ['Achat-revente sur Vinted', 'Marques et modèles à étudier', 'Calculateur de marge'],
}


def related(lang):
    links = ''.join('<li><a href="%s">%s</a></li>' % (SLUGS[k][lang], label)
                    for k, label in zip(SLUGS, LABELS[lang]))
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
            '<div class="profit-results" data-profit-result aria-live="polite" aria-atomic="true" hidden><dl>%s</dl></div>'
            '<noscript><p>%s</p></noscript></form><script src="/assets/profit-calculator.js" defer></script>'
            % (help_text, 'Devise' if fr else 'Currency', inputs, 'Calculer' if fr else 'Calculate',
               'Réinitialiser l’exemple' if fr else 'Reset example', results,
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
