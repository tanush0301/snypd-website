"""Useful existing item URLs without an invented overall estimate."""
from urllib.parse import urlencode

from price_quality import publishable_conditions

TEXT = {
    'en': dict(
        title='{name} on Vinted: condition prices and data limits | SNYPD',
        h1='{name}: prices by condition',
        lead='We cannot publish a reliable overall asking price for this item. Any figures below apply only to the named condition, not to the whole search.',
        why='Why there is no overall estimate',
        sample='SNYPD observed {n} matching listings on vinted.be, {window}. The overall search is too mixed or too spread out for one defensible median. This is a sample of the searches our users monitor, not all of Vinted or a record of completed sales.',
        correction='Correction, 2 November 2026: a previous version presented a condition-specific figure as an overall estimate. The source quality checks and measured quartiles have been restored.',
        conditions='Condition-specific figures that pass the checks',
        empty='No condition in this sample has enough clear data for a price estimate. A missing figure is not a zero price.',
        scope='Each row describes only that condition and its own sample count. Other sizes, models, bundles and possible counterfeits can change the comparison.',
        headers=['CONDITION', 'LISTINGS', 'MEDIAN ASKING PRICE', 'MIDDLE HALF'],
        compare='How to compare an item',
        steps='Match the exact model, size and condition on Vinted. Compare several similar live listings and include fees and shipping in your budget. A low asking price is not proof of authenticity, a bargain or the final sale price.',
        watch='Watch new listings for this item',
        watch_copy='Choose your own maximum price when you create the search. SNYPD alerts on new matching listings; it does not track price reductions on listings already online.',
        button='CREATE A SEARCH', method='Price guide and full method', notes='Items without a reliable overall estimate',
        summary='These guides remain available with validated condition figures where possible and an explanation of the limits. They are excluded from the overall-price checker and report estimates.',
        overlap='Item sample counts may overlap across searches. Their sum is not a count of unique listings across the entire catalogue.'),
    'fr': dict(
        title='{name} sur Vinted : prix par état et limites des données | SNYPD',
        h1='{name} : prix selon l’état',
        lead='Nous ne pouvons pas publier de prix demandé global fiable pour cet article. Les chiffres éventuels ci-dessous concernent uniquement l’état indiqué, pas toute la recherche.',
        why='Pourquoi aucun prix global n’est publié',
        sample='SNYPD a observé {n} annonces correspondantes sur vinted.be, {window}. La recherche globale est trop mélangée ou les prix trop dispersés pour une médiane fiable. Cet échantillon couvre les recherches suivies par nos utilisateurs, pas tout Vinted ni les ventes réalisées.',
        correction='Correction du 2 novembre 2026 : une version précédente présentait un prix propre à un état comme une estimation globale. Les contrôles de qualité et les quartiles mesurés ont été rétablis.',
        conditions='Prix par état qui passent les contrôles',
        empty='Aucun état de cet échantillon ne dispose de données assez claires pour une estimation. Une valeur absente ne signifie pas un prix nul.',
        scope='Chaque ligne concerne uniquement cet état et son propre nombre d’annonces. Les tailles, modèles, lots et contrefaçons éventuelles peuvent modifier la comparaison.',
        headers=['ÉTAT', 'ANNONCES', 'PRIX DEMANDÉ MÉDIAN', 'MOITIÉ CENTRALE'],
        compare='Comment comparer un article',
        steps='Sur Vinted, compare le modèle exact, la taille et l’état. Regarde plusieurs annonces similaires et ajoute les frais et la livraison à ton budget. Un prix bas ne prouve ni l’authenticité, ni une bonne affaire, ni le prix de vente final.',
        watch='Surveille les nouvelles annonces de cet article',
        watch_copy='Choisis ton propre prix maximum en créant la recherche. SNYPD signale les nouvelles annonces correspondantes, pas les baisses de prix des annonces déjà en ligne.',
        button='CRÉER UNE RECHERCHE', method='Guide des prix et méthode complète', notes='Articles sans estimation globale fiable',
        summary='Ces guides restent accessibles avec les prix par état validés lorsqu’ils existent et une explication des limites. Ils sont exclus des estimations globales de l’outil et du rapport.',
        overlap='Les échantillons peuvent se recouper entre recherches. Leur somme ne représente pas le nombre d’annonces uniques de tout le catalogue.'),
    'nl': dict(
        title='{name} op Vinted: prijzen per staat en databeperkingen | SNYPD',
        h1='{name}: prijzen per staat',
        lead='Voor dit artikel kunnen we geen betrouwbare algemene vraagprijs publiceren. Eventuele cijfers hieronder gelden alleen voor de genoemde staat, niet voor de volledige zoekopdracht.',
        why='Waarom er geen algemene schatting is',
        sample='SNYPD zag {n} passende advertenties op vinted.be, {window}. De volledige zoekopdracht bevat te veel verschillende artikelen of te uiteenlopende prijzen voor één betrouwbare mediaan. Dit is een steekproef van de zoekopdrachten van onze gebruikers, niet heel Vinted of een overzicht van verkoopprijzen.',
        correction='Correctie, 2 november 2026: een eerdere versie gaf een prijs voor één staat weer als algemene schatting. De oorspronkelijke kwaliteitscontroles en gemeten kwartielen zijn hersteld.',
        conditions='Prijzen per staat die de controles doorstaan',
        empty='Geen staat in deze steekproef heeft genoeg duidelijke gegevens voor een schatting. Een ontbrekend cijfer betekent geen prijs van nul.',
        scope='Elke rij geldt alleen voor die staat en het eigen aantal advertenties. Andere maten, modellen, bundels en mogelijke namaak kunnen de vergelijking veranderen.',
        headers=['STAAT', 'ADVERTENTIES', 'MEDIANE VRAAGPRIJS', 'MIDDELSTE HELFT'],
        compare='Zo vergelijk je een artikel',
        steps='Vergelijk op Vinted hetzelfde model, dezelfde maat en dezelfde staat. Bekijk meerdere vergelijkbare advertenties en tel kosten en verzending bij je budget. Een lage vraagprijs bewijst geen echtheid, koopje of uiteindelijke verkoopprijs.',
        watch='Volg nieuwe advertenties voor dit artikel',
        watch_copy='Kies je eigen maximumprijs bij het aanmaken van de zoekopdracht. SNYPD meldt nieuwe passende advertenties, geen prijsverlagingen van bestaande advertenties. Registratie en betaling zijn in het Engels of Frans.',
        button='MAAK EEN ZOEKOPDRACHT', method='Prijsgids en volledige methode', notes='Artikelen zonder betrouwbare algemene schatting',
        summary='Deze gidsen blijven beschikbaar met gevalideerde prijzen per staat waar mogelijk en een uitleg van de beperkingen. Ze tellen niet mee als algemene prijsschattingen in de zoekfunctie of het rapport.',
        overlap='Steekproeven kunnen tussen zoekopdrachten overlappen. Hun som is geen aantal unieke advertenties voor de volledige catalogus.'),
    'de': dict(
        title='{name} auf Vinted: Zustandspreise und Datengrenzen | SNYPD',
        h1='{name}: Preise nach Zustand',
        lead='Für diesen Artikel können wir keinen verlässlichen allgemeinen Angebotspreis veröffentlichen. Etwaige Zahlen unten gelten nur für den genannten Zustand, nicht für die gesamte Suche.',
        why='Warum es keine allgemeine Schätzung gibt',
        sample='SNYPD erfasste {n} passende Angebote auf vinted.be, {window}. Die gesamte Suche enthält zu unterschiedliche Artikel oder zu stark gestreute Preise für einen verlässlichen Median. Diese Stichprobe stammt aus den Suchen unserer Nutzer, nicht aus ganz Vinted oder abgeschlossenen Verkäufen.',
        correction='Korrektur, 2. November 2026: Eine frühere Version zeigte einen zustandsspezifischen Preis als allgemeine Schätzung. Die ursprünglichen Qualitätsprüfungen und gemessenen Quartile wurden wiederhergestellt.',
        conditions='Zustandspreise, die die Prüfungen bestehen',
        empty='Kein Zustand in dieser Stichprobe hat genügend klare Daten für eine Preisschätzung. Eine fehlende Zahl bedeutet keinen Preis von null.',
        scope='Jede Zeile gilt nur für diesen Zustand und die eigene Angebotszahl. Andere Größen, Modelle, Bündel und mögliche Fälschungen können den Vergleich verändern.',
        headers=['ZUSTAND', 'ANGEBOTE', 'MEDIAN DES ANGEBOTSPREISES', 'MITTLERE HÄLFTE'],
        compare='So vergleichst du einen Artikel',
        steps='Vergleiche auf Vinted dasselbe Modell, dieselbe Größe und denselben Zustand. Sieh dir mehrere ähnliche Angebote an und rechne Gebühren und Versand hinzu. Ein niedriger Angebotspreis beweist weder Echtheit noch ein Schnäppchen oder den endgültigen Verkaufspreis.',
        watch='Neue Angebote für diesen Artikel beobachten',
        watch_copy='Wähle beim Erstellen der Suche deinen eigenen Höchstpreis. SNYPD meldet neue passende Angebote, keine Preissenkungen bestehender Angebote. Registrierung und Zahlung sind auf Englisch oder Französisch.',
        button='SUCHE ERSTELLEN', method='Preisführer und vollständige Methode', notes='Artikel ohne verlässliche allgemeine Schätzung',
        summary='Diese Leitfäden bleiben mit geprüften Zustandspreisen, soweit vorhanden, und einer Erklärung der Grenzen verfügbar. Sie zählen nicht als allgemeine Preisschätzungen im Preisprüfer oder Bericht.',
        overlap='Stichproben können sich zwischen Suchen überschneiden. Ihre Summe ist keine Zahl einzigartiger Angebote im gesamten Katalog.'),
}


def note_links(p, lang):
    if not p.NOTE_ITEMS:
        return ''
    t = TEXT[lang]
    links = ''.join('<li><a href="%s">%s</a></li>' % (p.item_url(it, lang), p.esc(p.iname(it, lang))) for it in p.NOTE_ITEMS)
    return '<section id="data-limits"><h2>%s</h2><p>%s</p><ul>%s</ul><p>%s</p></section>' % (t['notes'], t['summary'], links, t['overlap'])


def page_note(p, it, lang):
    t = TEXT[lang]
    v = p.RAW_V[it['query']]
    name = p.iname(it, lang)
    rows = [[p.COND.get(c['condition_label'], {}).get(lang, c['condition_label']),
             p.num(c['sample_size'], lang), p.money(c['typical_cents'], lang),
             '%s &ndash; %s' % (p.money(c['range_cents']['low'], lang), p.money(c['range_cents']['high'], lang))]
            for c in publishable_conditions(v, p.MIN_COND)]
    figures = p.table(t['headers'], rows) if rows else '<p>%s</p>' % t['empty']
    signup = '/signup?' + urlencode({'hunt': it['query'], 'lang': 'fr' if lang == 'fr' else 'en'})
    sample = t['sample'].format(n=p.num(v.get('sample_size') or 0, lang), window=p.window(lang))
    body = ('<section id="overview"><h2>%s</h2><p>%s</p><div class="lg-box"><p>%s</p></div></section>'
            '<section id="conditions"><h2>%s</h2>%s<p>%s</p></section>'
            '<section id="compare"><h2>%s</h2><p>%s</p><p><a href="%s">%s</a></p></section>'
            '<section id="watch"><h2>%s</h2><p>%s</p><a class="ct-btn" href="%s">%s</a></section>') % (
                t['why'], sample, t['correction'], t['conditions'], figures, t['scope'],
                t['compare'], t['steps'], p.HUB[lang], t['method'], t['watch'], t['watch_copy'], signup, t['button'])
    return p.gc.page('pg:' + it['slug'], lang, t['title'].format(name=name), t['lead'], 'VINTED', t['h1'].format(name=name),
                     t['lead'], [('overview', t['why']), ('conditions', t['conditions']), ('compare', t['compare'])],
                     body, [], parent=(t['method'], p.HUB[lang]))
