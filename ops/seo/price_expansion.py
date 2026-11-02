"""German and Spanish checkers over the existing validated vinted.be sample."""
UPDATED = '2026-11-02'
NAME_ES = {
    'ralph-lauren-jumper': 'Jersey Ralph Lauren', 'ralph-lauren-shirt': 'Camisa Ralph Lauren',
    'ralph-lauren-quarter-zip': 'Jersey Ralph Lauren con media cremallera',
    'carhartt-detroit-jacket': 'Chaqueta Carhartt Detroit', 'carhartt-double-knee': 'Pantalón Carhartt Double Knee',
    'pandora-bracelet': 'Pulsera Pandora', 'columbia-fleece': 'Forro polar Columbia',
    'patagonia-fleece': 'Forro polar Patagonia', 'stussy-hoodie': 'Sudadera Stüssy',
    'stone-island-jumper': 'Jersey Stone Island', 'supreme-box-logo': 'Supreme Box Logo',
}


def install(p):
    p.PC_TXT['es'] = dict(
        label='BUSCA UN ARTÍCULO', ph='p. ej., Samba, Nuptse o Longchamp', typical='Precio anunciado mediano',
        middle='Mitad central de los anuncios:', listings='Anuncios:', page='PRECIOS POR ESTADO',
        page_en='GUÍA COMPLETA EN INGLÉS', alert='AVÍSAME POR DEBAJO DE {p}',
        note='Precios anunciados en vinted.be, no precios de ventas. Los precios en vinted.es pueden ser distintos.',
        none='No hay resultados para «{q}». Prueba una marca o un modelo: Nike, Ralph Lauren o Carhartt.',
        many='{n} artículos coinciden. Elige uno:',
        unavailable='No hay una estimación global fiable. La guía en inglés explica los límites y los datos por estado que sí pasan los controles.',
        unavailable_short='sin estimación global')


def item_link(p, it, lang):
    local = lang == 'de'
    return '<a href="%s">%s%s</a>' % (p.item_url(it, lang if local else 'en'),
        p.esc(p.iname(it, lang)), '' if local else ' (guía en inglés)')


def page_checker(p, lang):
    de = lang == 'de'
    rows = [[item_link(p, it, lang), p.money(p.V[it['slug']]['typical_cents'], lang)]
            for it in sorted(p.PUB, key=lambda x: p.iname(x, lang).lower())]
    notes = ''.join('<li>%s</li>' % item_link(p, it, lang) for it in p.NOTE_ITEMS)
    if de:
        title = 'Vinted Preischeck: Modelle und Angebotspreise vergleichen | SNYPD'
        desc = 'Kostenloser Vinted Preischeck mit Median, Preisspanne und Stichprobe je Modell. Beobachtete Angebotspreise auf vinted.be, keine Verkaufspreise.'
        h1 = 'Vinted Preischeck: Was wird für dein Modell verlangt?'
        lead = 'Vergleiche ein genaues Modell anhand beobachteter Angebotspreise. Die Daten stammen von vinted.be; sie sind keine Bewertung des deutschen Marktes.'
        sections = [
            ('search', 'Suche eine Marke oder ein Modell', '<p>Zum Beispiel Samba, Nuptse oder Longchamp. Das Ergebnis zeigt den Median, das mittlere Preisintervall und die Zahl der beobachteten Angebote. Ein niedriger Preis beweist weder Echtheit noch einen späteren Gewinn.</p>' + p.checker_box(lang, review_budget=True)),
            ('prices', 'Die %d verfügbaren Gesamtschätzungen' % len(p.PUB), '<p>Die Tabelle bleibt ohne JavaScript lesbar. Jeder Link führt zum deutschen Modellleitfaden mit Zustandsdaten und Methodik.</p>' + p.table(['MODELL', 'MEDIAN DER ANGEBOTSPREISE'], rows)),
            ('limits', 'Modelle ohne verlässliche Gesamtschätzung', '<p>Für diese Modelle nennen wir keinen erfundenen Gesamtpreis. Die Leitfäden erklären die Datengrenzen und zeigen geprüfte Zustandspreise, soweit verfügbar.</p><ul>' + notes + '</ul>'),
            ('method', 'So liest du die Daten', '<p>Beobachtungszeitraum: %s, Marktplatz vinted.be, Währung EUR. Erfasst wurden Angebote, die zu überwachten SNYPD-Suchen passten. Die Auswahl bildet weder ganz Vinted noch den deutschen Markt repräsentativ ab.</p><p>Der Median teilt die Stichprobe in zwei Hälften. Das zentrale Intervall reicht vom 25. bis zum 75. Perzentil. Preise sind Forderungen der Anbieter, keine bestätigten Verkaufspreise. Artikelstichproben können sich überschneiden. Größe, Zustand, Modellversion, Sets und mögliche Fälschungen beeinflussen den Vergleich.</p>' % p.window(lang)),
            ('use', 'Lege dein eigenes Suchbudget fest', '<p>Vergleiche denselben Artikelzustand und die passende Größe. Rechne Gebühren und Versand in dein Budget ein. SNYPD kann neue passende Angebote überwachen; bestehende Preissenkungen werden nicht verfolgt. Die Anmeldung und das Dashboard sind auf Englisch oder Französisch verfügbar.</p><p><a href="/de/vinted-preise">Deutsche Preisleitfäden</a> · <a href="/de/vinted-verkaufte-artikel-sehen">Verkaufte Artikel und Datengrenzen</a> · <a href="/de/vinted-gespeicherte-suchen">Gespeicherte Suchen</a> · <a href="/vinted-search-builder">Suchlink erstellen (Englisch)</a></p>'),
        ]
    else:
        title = 'Comprobar precio en Vinted: mediana y rango por modelo | SNYPD'
        desc = 'Consulta precios anunciados en Vinted por modelo: mediana, intervalo y muestra. Herramienta gratuita con datos de vinted.be, no precios de ventas.'
        h1 = 'Comprobar un precio en Vinted'
        lead = 'Busca un modelo y compara sus precios anunciados. Los datos proceden de vinted.be: no son precios de ventas ni una valoración del mercado español.'
        sections = [
            ('search', 'Busca una marca o un modelo', '<p>Por ejemplo, Samba, Nuptse o Longchamp. El resultado muestra la mediana, el intervalo central y el número de anuncios. Las fichas completas todavía están en inglés y sus enlaces lo indican.</p>' + p.checker_box(lang, review_budget=True)),
            ('prices', 'Las %d estimaciones globales disponibles' % len(p.PUB), '<p>La tabla sigue disponible sin JavaScript. Ninguna mediana garantiza el precio al que venderás tu artículo.</p>' + p.table(['MODELO', 'MEDIANA DEL PRECIO ANUNCIADO'], rows)),
            ('limits', 'Artículos sin una estimación global fiable', '<p>No sustituimos un dato ausente por un precio inventado. Estas guías en inglés explican los límites y los datos por estado que superan los controles, si los hay.</p><ul>' + notes + '</ul>'),
            ('method', 'Cómo interpretar la muestra', '<p>Periodo observado: %s. Mercado: vinted.be. Moneda: EUR. Son anuncios que coincidieron con búsquedas vigiladas por usuarios de SNYPD, no una muestra representativa de todo Vinted ni de vinted.es.</p><p>La mediana divide los anuncios en dos mitades. El intervalo central va del percentil 25 al 75. Los precios son importes anunciados, no ventas confirmadas. Las muestras de distintos artículos pueden solaparse. Tallas, estado, variantes, lotes y posibles falsificaciones pueden afectar a la comparación.</p>' % p.window(lang)),
            ('use', 'Elige tu propio límite de compra', '<p>Compara el mismo modelo, talla y estado. Incluye los gastos de compra y envío en tu presupuesto. SNYPD avisa de nuevos anuncios coincidentes; no vigila rebajas en anuncios que ya estaban publicados. El registro y el panel están disponibles en inglés o francés.</p><p><a href="/es/vinted-ver-articulos-vendidos">Artículos vendidos y límites de los datos</a> · <a href="/es/vinted-busquedas-guardadas">Búsquedas guardadas</a> · <a href="/vinted-search-builder">Crear un enlace de búsqueda (inglés)</a> · <a href="/vinted-profit-calculator">Calculadora de beneficio (inglés)</a></p>'),
        ]
    body = ''.join('<section id="%s"><h2>%s</h2>%s</section>' % s for s in sections)
    body += '<section id="data"><h2>%s</h2><p><a href="/assets/data/price-index.json">JSON</a> · <a href="%s" rel="license">CC BY 4.0</a> · <a href="/vinted-price-guide#method">%s</a></p></section>' % (
        'Daten und Quellen' if de else 'Datos y fuentes', p.DATASET_LICENSE, 'Vollständige Methodik (Englisch)' if de else 'Método completo (inglés)')
    dataset = p.index_dataset_ld('en', p.SLUGS['checker'][lang])
    dataset.update(inLanguage=lang, name=h1, description=desc)
    return p.gc.page('checker', lang, title, desc, 'VINTED', h1, lead,
                     [(i, h) for i, h, _ in sections], body, [dataset], published=UPDATED)
