"""Small Italian pilot over the same verified vinted.be observations."""
from urllib.parse import urlencode

from price_quality import publishable_conditions

PILOT = ('nike-dunk-low', 'nike-air-force-1', 'adidas-samba', 'new-balance-550', 'the-north-face-nuptse')
NAME = {'ralph-lauren-jumper': 'Maglione Ralph Lauren', 'ralph-lauren-shirt': 'Camicia Ralph Lauren',
        'carhartt-detroit-jacket': 'Giacca Carhartt Detroit', 'pandora-bracelet': 'Bracciale Pandora',
        'ralph-lauren-polo': 'Polo Ralph Lauren', 'columbia-fleece': 'Pile Columbia', 'patagonia-fleece': 'Pile Patagonia'}
CONDITION = {'New, with tag': 'Nuovo con cartellino', 'New, no tag': 'Nuovo senza cartellino',
             'Very good': 'Ottime condizioni', 'Good': 'Buone condizioni', 'Satisfactory': 'Discrete condizioni'}


def install(p):
    p.NAME_IT = NAME
    p.HUB['it'] = '/it/prezzi-vinted'
    p.SLUGS['guide']['it'] = p.HUB['it']
    for slug in PILOT:
        if slug not in p.V:
            raise ValueError('Italian pilot needs a reviewed estimate before publication: ' + slug)
        p.SLUGS['pg:' + slug]['it'] = p.HUB['it'] + '/' + slug
    p.PC_TXT['it'] = dict(
        label='CERCA UN ARTICOLO', ph='es. Samba, Nuptse, Longchamp', typical='Prezzo richiesto tipico',
        middle='Metà centrale degli annunci:', listings='Annunci:', page='GUIDA PER CONDIZIONE',
        page_en='GUIDA COMPLETA IN INGLESE', alert='AVVISAMI SOTTO {p}',
        note='Prezzi richiesti, non prezzi di vendita. Campione vinted.be: i prezzi su vinted.it possono differire.',
        none='Nessun risultato per “{q}”. Prova una marca o un modello, per esempio Nike, Ralph Lauren o Carhartt.',
        many='{n} articoli trovati. Scegline uno:',
        unavailable='Non è disponibile una stima complessiva affidabile. La guida in inglese mostra gli eventuali prezzi per condizione verificati e i limiti dei dati.',
        unavailable_short='nessuna stima complessiva')


def item_link(p, it):
    local = it['slug'] in PILOT
    href = p.item_url(it, 'it' if local else 'en')
    return '<a href="%s">%s%s</a>' % (href, p.esc(p.iname(it, 'it')), '' if local else ' (guida in inglese)')


def dataset(p, lang_url):
    d = p.index_dataset_ld('en', lang_url)
    d.update(name='Prezzi richiesti Vinted: campione vinted.be',
             description='Mediana, quartili e numero di annunci per gli articoli con dati sufficienti. Prezzi richiesti su vinted.be, non prezzi di vendita o stime nazionali italiane.',
             inLanguage='it')
    return d


def page_hub(p):
    items = [it for it in p.PUB if it['slug'] in PILOT]
    rows = [[item_link(p, it), p.money(p.V[it['slug']]['typical_cents'], 'it'),
             p.num(p.V[it['slug']]['sample_size'], 'it')] for it in items]
    body = ('<section id="guide"><h2>Cinque guide iniziali</h2><p>Questo è un primo gruppo di guide in italiano, non un elenco completo del mercato.</p>%s</section>'
            '<section id="cerca"><h2>Cerchi un altro modello?</h2><p><a href="%s">Apri lo strumento di stima</a>: cerca tra %d stime complessive verificate e %d schede con limiti dei dati. Le guide non ancora tradotte sono indicate come inglesi.</p></section>'
            '<section id="metodo"><h2>Da dove arrivano i prezzi</h2><p>Gli annunci sono stati osservati su vinted.be, %s, per le ricerche monitorate dagli utenti SNYPD. Non sono prezzi di vendita né un campione rappresentativo di Vinted Italia. I prezzi su vinted.it possono differire.</p>'
            '<p>Le stime mostrano la mediana dei prezzi richiesti. Ogni articolo incluso ha almeno %d annunci e passa i controlli di qualità originali. Taglie, varianti, lotti e possibili contraffazioni possono influenzare il confronto. I campioni di articoli diversi possono sovrapporsi.</p>'
            '<p><a href="/vinted-price-guide#method">Metodo completo (inglese)</a> · <a href="/vinted-market-report">Rapporti e CSV (inglese)</a></p></section>') % (
                p.table(['ARTICOLO', 'PREZZO RICHIESTO MEDIANO', 'ANNUNCI'], rows),
                p.SLUGS['checker']['it'], len(p.PUB), len(p.NOTE_ITEMS), p.window('it'), p.MIN_LISTINGS)
    return p.gc.page('guide', 'it', 'Prezzi Vinted: 5 guide in italiano e stima per modello | SNYPD',
                     'Guide in italiano per cinque modelli e uno strumento gratuito basato su prezzi richiesti osservati su vinted.be. Campione e limiti dichiarati.',
                     'PREZZI VINTED', 'Prezzi Vinted: guide e stime per modello',
                     'Dati osservati su vinted.be, spiegati in italiano. Non sono prezzi di vendita e non rappresentano automaticamente il mercato italiano.',
                     [('guide', 'Guide'), ('cerca', 'Cerca un modello'), ('metodo', 'Metodo')], body)


def page_checker(p):
    rows = [[item_link(p, it), p.money(p.V[it['slug']]['typical_cents'], 'it')] for it in sorted(p.PUB, key=lambda x: p.iname(x, 'it').lower())]
    notes = ''.join('<li>%s</li>' % item_link(p, it) for it in p.NOTE_ITEMS)
    body = ('<section id="cerca"><h2>Cerca una marca o un modello</h2><p>Per esempio Samba, Nuptse o Longchamp. Il risultato indica il prezzo richiesto mediano, la metà centrale degli annunci e il numero di annunci. I modelli senza una stima affidabile rimandano a una scheda con i limiti dei dati.</p>%s</section>'
            '<section id="stime"><h2>Le %d stime complessive disponibili</h2><p>Questi dati restano leggibili anche senza JavaScript. Cinque guide sono in italiano; le altre sono indicate come inglesi.</p>%s</section>'
            '<section id="limiti"><h2>Articoli senza una stima complessiva</h2><p>Non sostituiamo i dati mancanti con prezzi inventati. Le schede seguenti spiegano i limiti e gli eventuali dati verificati per condizione (in inglese).</p><ul>%s</ul></section>'
            '<section id="metodo"><h2>Come leggere il risultato</h2><p>La mediana divide gli annunci in due metà; l’intervallo centrale va dal 25º al 75º percentile. Il quarto più economico è un filtro di ricerca, non la prova di un affare o di autenticità.</p>'
            '<p>Campione vinted.be, %s: ricerche monitorate dagli utenti SNYPD, non tutto Vinted. Prezzi richiesti, non prezzi di vendita. I prezzi su vinted.it possono differire.</p>'
            '<p><a href="%s">Guide in italiano</a> · <a href="/assets/data/price-index.json">Dati JSON</a> · <a href="%s" rel="license">CC BY 4.0</a></p></section>') % (
                p.checker_box('it'), len(p.PUB), p.table(['ARTICOLO', 'PREZZO RICHIESTO MEDIANO'], rows), notes,
                p.window('it'), p.HUB['it'], p.DATASET_LICENSE)
    return p.gc.page('checker', 'it', 'Stima prezzo Vinted: cerca modello e condizione | SNYPD',
                     'Cerca un modello e consulta prezzi richiesti mediani, intervallo e campione. Strumento gratuito con dati vinted.be e limiti dichiarati.',
                     'STIMA PREZZO VINTED', 'Stima un prezzo Vinted',
                     'Uno strumento gratuito in italiano basato su osservazioni di vinted.be. Non mostra prezzi di vendita e non presume che i prezzi italiani siano identici.',
                     [('cerca', 'Cerca'), ('stime', 'Stime'), ('limiti', 'Limiti'), ('metodo', 'Metodo')], body,
                     [dataset(p, p.SLUGS['checker']['it'])], parent=('Guide prezzi', p.HUB['it']))


def page_item(p, it):
    v = p.V[it['slug']]
    name = p.iname(it, 'it')
    rows = [[CONDITION.get(c['condition_label'], c['condition_label']), p.num(c['sample_size'], 'it'),
             p.money(c['typical_cents'], 'it'), '%s &ndash; %s' % (p.money(c['range_cents']['low'], 'it'), p.money(c['range_cents']['high'], 'it'))]
            for c in publishable_conditions(v, p.MIN_COND)]
    target = '/signup?' + urlencode({'hunt': it['query'], 'max': v['range_cents']['low'] // 100, 'lang': 'en'})
    body = ('<section id="prezzo"><h2>Prezzo richiesto nel campione</h2><p>Mediana: <strong>%s</strong>. La metà centrale degli annunci va da %s a %s. Campione: %s annunci su vinted.be, %s.</p></section>'
            '<section id="condizione"><h2>Prezzi per condizione</h2>%s<p>Ogni riga riguarda solo la condizione e il numero di annunci indicati. Una condizione assente non dispone di dati abbastanza chiari.</p></section>'
            '<section id="limiti"><h2>Cosa questi numeri non dicono</h2><p>Sono prezzi richiesti, non prezzi di vendita. Gli annunci provengono dalle ricerche monitorate dagli utenti SNYPD su vinted.be; non sono un censimento del mercato italiano. Taglie per bambini e adulti, varianti, lotti e possibili contraffazioni possono influenzare i prezzi. Il prezzo più basso non prova un affare o autenticità.</p></section>'
            '<section id="avvisi"><h2>Usa il prezzo come filtro</h2><p>Puoi iniziare una ricerca con il limite del quarto più economico e adattarlo alla tua taglia e condizione. SNYPD segnala nuovi annunci corrispondenti, non cali di prezzo di annunci già online. Registrazione e pagamento sono disponibili in inglese o francese.</p>'
            '<a class="ct-btn" href="%s">CERCA NUOVI ANNUNCI SOTTO %s</a><p><a href="%s">Stima un altro modello</a> · <a href="/vinted-price-guide#method">Metodo completo (inglese)</a></p></section>') % (
                p.money(v['typical_cents'], 'it'), p.money(v['range_cents']['low'], 'it'), p.money(v['range_cents']['high'], 'it'),
                p.num(v['sample_size'], 'it'), p.window('it'),
                p.table(['CONDIZIONE', 'ANNUNCI', 'PREZZO MEDIANO', 'METÀ CENTRALE'], rows), target,
                p.money(v['range_cents']['low'], 'it'), p.SLUGS['checker']['it'])
    url = p.item_url(it, 'it')
    d = p.dataset_ld(it, v, 'en', url)
    d.update(name='Prezzi richiesti per %s su vinted.be' % name, inLanguage='it',
             description='Mediana e quartili dei prezzi richiesti per %s nel campione vinted.be, complessivi e per condizione. Non sono prezzi di vendita o una stima del mercato italiano.' % name)
    return p.gc.page('pg:' + it['slug'], 'it', '%s su Vinted: prezzi richiesti e condizioni (%s) | SNYPD' % (name, p.month_year('it')),
                     'Prezzo richiesto mediano di %s: %s nel campione vinted.be. Intervallo, numero di annunci, condizioni e limiti; non prezzi di vendita.' % (name, p.plain_eur(v['typical_cents'], 'it')),
                     'GUIDA PREZZI VINTED', name + ': prezzi richiesti su Vinted',
                     'Dati vinted.be spiegati in italiano: confronta sempre lo stesso modello, la taglia e la condizione. I prezzi su vinted.it possono differire.',
                     [('prezzo', 'Prezzo'), ('condizione', 'Condizione'), ('limiti', 'Limiti'), ('avvisi', 'Avvisi')],
                     body, [d], parent=('Guide prezzi', p.HUB['it']))
