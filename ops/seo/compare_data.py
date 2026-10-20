"""Comparison data for the Vinted bot comparison pages and the alert-hub table, in six languages.

Every competitor fact comes from that vendor's OWN website or its own app-store listing, read on
COMPARE_CHECKED (evidence, URLs and quotes: C:/Users/Tanus/website/outreach/research-2026-10-10-competitors.md).
EU comparative-advertising rules (Directive 2006/114/EC; Belgian Code of Economic Law VI.17): each
claim objective, verifiable, not misleading. Write "not stated" (never "no") when a site is silent.
Vendor speed claims are never repeated as facts; the pages attribute them. Re-check monthly.
Cells are HTML. Plan prices for SNYPD are plans.py tokens (filled at write time).
ops/ is in .vercelignore: never deploys.
"""
SITE = 'https://www.snypd.store'
LANGS = ('en', 'fr', 'de', 'nl', 'it', 'es')
COMPARE_CHECKED = {'en': '10 October 2026', 'fr': '10 octobre 2026', 'de': '10. Oktober 2026', 'nl': '10 oktober 2026',
                   'it': '10 ottobre 2026', 'es': '10 de octubre de 2026'}
COMPARE_CHECKED_SHORT = {'en': '10 OCT 2026', 'fr': '10 OCT. 2026', 'de': '10. OKT. 2026', 'nl': '10 OKT. 2026',
                         'it': '10 OTT. 2026', 'es': '10 OCT. 2026'}
YES = '<span class="ct-yes">&#10003;</span> '


def L(en, fr, de, nl, it, es):
    return {'en': en, 'fr': fr, 'de': de, 'nl': nl, 'it': it, 'es': es}


def money_range(lo, hi, cur='eur', note=None):
    """'4.90','14.90' -> per-language range; cur eur or gbp; note = {lang: suffix} or None."""
    sym = {'eur': '&euro;', 'gbp': '&pound;'}[cur]
    out = {}
    for l in LANGS:
        a, b = (lo, hi) if l == 'en' else (lo.replace('.', ','), hi.replace('.', ',') if hi else hi)
        if l == 'en':
            s = sym + a + ('&ndash;' + sym + b if hi else '')
        elif l == 'nl':
            s = sym + '&nbsp;' + a + ('&ndash;' + b if hi else '')
        else:
            s = a + ('&ndash;' + b if hi else '') + '&nbsp;' + sym
        out[l] = s + (note[l] if note else '')
    return out


NS = L('Not stated', 'Non précisé', 'Nicht angegeben', 'Niet vermeld', 'Non indicato', 'No indicado')
NOT_SITE = L('Not on its site', 'Absent de son site', 'Nicht auf der Website', 'Niet op de site', 'Non sul sito', 'No figura en su web')
NOT_HOME = L('Not on its homepage', 'Absent de sa page d’accueil', 'Nicht auf der Startseite', 'Niet op de homepage', 'Non in homepage', 'No figura en su portada')
ALERTS = L('Alerts', 'Alertes', 'Benachrichtigungen', 'Meldingen', 'Notifiche', 'Alertas')
ALERTS_AUTOBUY = L('Alerts + autobuy', 'Alertes + achat automatique', 'Benachrichtigungen + Autobuy', 'Meldingen + autobuy',
                   'Notifiche + acquisto automatico', 'Alertas + compra automática')
DISCORD = L('Discord', 'Discord', 'Discord', 'Discord', 'Discord', 'Discord')
WITHDRAW14 = L('14-day withdrawal, minus what you used', 'Rétractation 14 jours, moins l’usage', '14 Tage Widerruf, abzüglich Nutzung',
               '14 dagen herroeping, min gebruik', 'Recesso 14 giorni, meno l’uso', 'Desistimiento 14 días, menos el uso')
NO = L('No', 'Non', 'Nein', 'Nee', 'No', 'No')
DASH = L('&mdash;', '&mdash;', '&mdash;', '&mdash;', '&mdash;', '&mdash;')
FREE = L('Free', 'Gratuit', 'Kostenlos', 'Gratis', 'Gratis', 'Gratis')

HEAD = {
    'en': ['TOOL', 'WHAT IT DOES', 'PRICE DATA', 'NEEDS YOUR VINTED ACCOUNT', 'ALERTS ARRIVE', 'REFUND', 'PER MONTH', 'FREE OPTION'],
    'fr': ['OUTIL', 'CE QU’IL FAIT', 'DONNÉES DE PRIX', 'BESOIN DE TON COMPTE VINTED', 'ALERTES VIA', 'REMBOURSEMENT', 'PAR MOIS', 'OPTION GRATUITE'],
    'de': ['TOOL', 'WAS ES MACHT', 'PREISDATEN', 'BRAUCHT DEIN VINTED-KONTO', 'BENACHRICHTIGUNG ÜBER', 'ERSTATTUNG', 'PRO MONAT', 'GRATIS-OPTION'],
    'nl': ['TOOL', 'WAT HET DOET', 'PRIJSDATA', 'HEEFT JE VINTED-ACCOUNT NODIG', 'MELDINGEN VIA', 'TERUGBETALING', 'PER MAAND', 'GRATIS OPTIE'],
    'it': ['STRUMENTO', 'COSA FA', 'DATI SUI PREZZI', 'SERVE IL TUO ACCOUNT VINTED', 'NOTIFICHE VIA', 'RIMBORSO', 'AL MESE', 'OPZIONE GRATUITA'],
    'es': ['HERRAMIENTA', 'QUÉ HACE', 'DATOS DE PRECIOS', 'NECESITA TU CUENTA DE VINTED', 'ALERTAS POR', 'REEMBOLSO', 'AL MES', 'OPCIÓN GRATUITA'],
}
US_BADGE = L('US', 'NOUS', 'WIR', 'WIJ', 'NOI', 'NOSOTROS')

# kind: monitor = alerts only; autobuy = also buys; app; script; builtin. 'langs' limits a row to some pages (default: all).
COMPETITORS = [
    {'name': 'SNYPD', 'url': SITE + '/plans', 'us': True, 'cells': [
        L('Alerts + price data', 'Alertes + données de prix', 'Benachrichtigungen + Preisdaten', 'Meldingen + prijsdata', 'Notifiche + dati sui prezzi', 'Alertas + datos de precios'),
        {k: YES + v for k, v in L('Market Report on Pro and Elite', 'Market Report sur Pro et Elite', 'Market Report bei Pro und Elite', 'Market Report bij Pro en Elite',
                                  'Market Report con Pro ed Elite', 'Market Report en Pro y Elite').items()},
        {k: YES + v for k, v in L('Never: email only', 'Jamais : e-mail seulement', 'Nie: nur E-Mail', 'Nooit: alleen e-mail', 'Mai: solo e-mail', 'Nunca: solo e-mail').items()},
        {k: YES + v for k, v in L('Push to phone and computer', 'Push sur téléphone et ordinateur', 'Push auf Handy und Computer', 'Push op telefoon en computer',
                                  'Push su telefono e computer', 'Push en móvil y ordenador').items()},
        {k: YES + v for k, v in L('14 days, full, after use', '14 jours, intégral, même après usage', '14 Tage, voll, auch nach Nutzung', '14 dagen, volledig, ook na gebruik',
                                  '14 giorni, totale, anche dopo l’uso', '14 días, íntegro, aunque lo hayas usado').items()},
        L('@@price:pass@@ once / @@price:solo@@&ndash;@@price:elite@@ a month <small>VAT incl.</small>',
          '@@price:pass@@ en une fois / @@num:solo@@&ndash;@@price:elite@@ par mois <small>TVA incluse</small>',
          '@@price:pass@@ einmalig / @@num:solo@@&ndash;@@price:elite@@ im Monat <small>inkl. MwSt.</small>',
          '@@price:pass@@ eenmalig / @@price:solo@@&ndash;@@num:elite@@ per maand <small>incl. btw</small>',
          '@@price:pass@@ una tantum / @@num:solo@@&ndash;@@price:elite@@ al mese <small>IVA incl.</small>',
          '@@price:pass@@ pago único / @@num:solo@@&ndash;@@price:elite@@ al mes <small>IVA incl.</small>'),
        {k: YES + v for k, v in L('1 search, no time limit, 24/7 for the first @@trial_days@@ days', '1 recherche, sans limite de durée, 24h/24 les @@trial_days@@ premiers jours',
                                  '1 Suche, ohne Zeitlimit, die ersten @@trial_days@@ Tage rund um die Uhr', '1 zoekopdracht, zonder tijdslimiet, de eerste @@trial_days@@ dagen 24/7',
                                  '1 ricerca, senza limiti di tempo, 24 ore su 24 i primi @@trial_days@@ giorni', '1 búsqueda, sin límite de tiempo, 24/7 los primeros @@trial_days@@ días').items()}]},
    # souk.to/en + /en/docs/autobuy ("To use Autobuy, first link your Vinted account from the Souk settings.")
    {'name': 'Souk', 'url': 'https://souk.to/en', 'kind': 'autobuy', 'cells': [
        ALERTS_AUTOBUY, NOT_SITE,
        L('Yes, to autobuy: you link your Vinted account', 'Oui, pour l’achat auto : tu lies ton compte Vinted', 'Ja, für Autobuy: du verknüpfst dein Vinted-Konto',
          'Ja, voor autobuy: je koppelt je Vinted-account', 'Sì, per l’acquisto automatico: colleghi il tuo account Vinted', 'Sí, para la compra automática: vinculas tu cuenta de Vinted'),
        L('Push', 'Push', 'Push', 'Push', 'Push', 'Push'),
        L('One week', 'Une semaine', 'Eine Woche', 'Eén week', 'Una settimana', 'Una semana'),
        money_range('29', '99'),
        L('&ldquo;Start for free&rdquo;, no details', '« Start for free », sans détail', '&bdquo;Start for free&ldquo;, ohne Details', '&lsquo;Start for free&rsquo;, zonder details',
          '&laquo;Start for free&raquo;, senza dettagli', '&laquo;Start for free&raquo;, sin detalles')]},
    # telvin-bot.com/en/ + /en/vinted-alerts/ + terms (14-day withdrawal lost once the service starts)
    {'name': 'Telvin Bot', 'url': 'https://www.telvin-bot.com/en/', 'kind': 'monitor', 'cells': [
        ALERTS, NOT_SITE, NS,
        L('Telegram only', 'Telegram uniquement', 'Nur Telegram', 'Alleen Telegram', 'Solo Telegram', 'Solo Telegram'),
        L('14-day withdrawal, lost once the service starts', 'Rétractation 14 jours, perdue dès le début du service', '14 Tage Widerruf, entfällt ab Nutzungsbeginn',
          '14 dagen herroeping, vervalt zodra de dienst start', 'Recesso 14 giorni, perso all’avvio del servizio', 'Desistimiento 14 días, se pierde al empezar el servicio'),
        money_range('4.90', '14.90'),
        L('1 keyword alert, 100 notifications', '1 alerte mot-clé, 100 notifications', '1 Stichwort-Alarm, 100 Benachrichtigungen', '1 zoekwoordmelding, 100 meldingen',
          '1 avviso per parola chiave, 100 notifiche', '1 alerta por palabra clave, 100 notificaciones')]},
    # v-tools.com (v-tools.eu is an affiliate site, never cite it)
    {'name': 'V-Tools', 'url': 'https://www.v-tools.com/', 'kind': 'autobuy', 'cells': [
        L('Autobuy, multi-account', 'Achat automatique, multi-comptes', 'Autobuy, mehrere Konten', 'Autobuy, meerdere accounts', 'Acquisto automatico, più account', 'Compra automática, varias cuentas'),
        L('Own sales CRM, no market prices listed', 'CRM de ses ventes, pas de prix du marché indiqués', 'Eigenes Verkaufs-CRM, keine Marktpreise angegeben',
          'Eigen verkoop-CRM, geen marktprijzen vermeld', 'CRM delle proprie vendite, nessun prezzo di mercato indicato', 'CRM de ventas propio, sin precios de mercado'),
        L('Yes: you connect your Vinted accounts', 'Oui : tu connectes tes comptes Vinted', 'Ja: du verbindest deine Vinted-Konten', 'Ja: je verbindt je Vinted-accounts',
          'Sì: colleghi i tuoi account Vinted', 'Sí: conectas tus cuentas de Vinted'),
        L('Its own app feed', 'Le flux de son app', 'Feed in der eigenen App', 'Feed in de eigen app', 'Feed nella sua app', 'Feed en su propia app'),
        NOT_HOME, money_range('29.99', '79.99'),
        L('None stated', 'Aucune indiquée', 'Keine angegeben', 'Geen vermeld', 'Nessuna indicata', 'Ninguna indicada')]},
    # crazed.fr: Premium 4,99 and Crazy 9,99 marked "Bientôt disponible"
    {'name': 'Crazed', 'url': 'https://crazed.fr/', 'kind': 'monitor', 'cells': [
        ALERTS, NOT_SITE, NS,
        L('In its platform; push only on a plan marked &ldquo;coming soon&rdquo;', 'Dans sa plateforme ; push seulement sur un plan « bientôt disponible »',
          'Auf der eigenen Plattform; Push nur in einem Tarif &bdquo;demnächst&ldquo;', 'Op het eigen platform; push alleen in een abonnement &lsquo;binnenkort&rsquo;',
          'Sulla sua piattaforma; push solo in un piano &laquo;in arrivo&raquo;', 'En su plataforma; push solo en un plan &laquo;próximamente&raquo;'),
        NOT_HOME,
        L('Free only; paid plans &ldquo;coming soon&rdquo;', 'Gratuit seulement ; plans payants « bientôt disponibles »', 'Nur kostenlos; Bezahltarife &bdquo;demnächst&ldquo;',
          'Alleen gratis; betaalde abonnementen &lsquo;binnenkort&rsquo;', 'Solo gratis; piani a pagamento &laquo;in arrivo&raquo;', 'Solo gratis; planes de pago &laquo;próximamente&raquo;'),
        L('3 alerts, 30 items a day', '3 alertes, 30 articles par jour', '3 Alarme, 30 Artikel pro Tag', '3 meldingen, 30 artikelen per dag', '3 avvisi, 30 articoli al giorno',
          '3 alertas, 30 artículos al día')]},
    # resellreserve.co.uk + /refund-policy + /free-vinted-bot; AutoBuy needs your Vinted token
    {'name': 'Resell Reserve', 'url': 'https://resellreserve.co.uk/', 'kind': 'autobuy', 'cells': [
        ALERTS_AUTOBUY,
        L('AI estimates, &pound;44.99 plan only', 'Estimations IA, plan à 44,99&nbsp;&pound; seulement', 'KI-Schätzungen, nur im 44,99-&pound;-Tarif',
          'AI-schattingen, alleen in het abonnement van &pound;&nbsp;44,99', 'Stime IA, solo nel piano da 44,99&nbsp;&pound;', 'Estimaciones con IA, solo en el plan de 44,99&nbsp;&pound;'),
        L('To buy, yes: you connect your Vinted token', 'Pour acheter, oui : tu connectes ton jeton Vinted', 'Zum Kaufen ja: du verbindest deinen Vinted-Token',
          'Om te kopen wel: je koppelt je Vinted-token', 'Per acquistare sì: colleghi il tuo token Vinted', 'Para comprar, sí: conectas tu token de Vinted'),
        DISCORD,
        L('Generally non-refundable; Core: conditional first-month guarantee', 'En général non remboursable ; Core : garantie conditionnelle le premier mois',
          'In der Regel keine Erstattung; Core: Garantie im ersten Monat unter Bedingungen', 'In principe geen terugbetaling; Core: voorwaardelijke garantie de eerste maand',
          'In genere non rimborsabile; Core: garanzia condizionata il primo mese', 'Por lo general sin reembolso; Core: garantía condicionada el primer mes'),
        money_range('19.99', '44.99', 'gbp'),
        L('One free Discord channel, UK only', 'Un salon Discord gratuit, Royaume-Uni seulement', 'Ein kostenloser Discord-Kanal, nur UK', 'Eén gratis Discord-kanaal, alleen VK',
          'Un canale Discord gratuito, solo Regno Unito', 'Un canal de Discord gratis, solo Reino Unido')]},
    # marktalert.nl/pricing (no terms page found)
    {'name': 'MarktAlert', 'url': 'https://marktalert.nl/pricing', 'kind': 'monitor', 'cells': [
        L('Alerts (also Marktplaats, 2dehands)', 'Alertes (aussi Marktplaats, 2dehands)', 'Benachrichtigungen (auch Marktplaats, 2dehands)', 'Meldingen (ook Marktplaats, 2dehands)',
          'Notifiche (anche Marktplaats, 2dehands)', 'Alertas (también Marktplaats, 2dehands)'),
        L('Price-drop alerts only', 'Alertes de baisse de prix seulement', 'Nur Preissenkungs-Alarme', 'Alleen prijsdalingsmeldingen', 'Solo avvisi di calo prezzo', 'Solo alertas de bajada de precio'),
        NS,
        L('Telegram, app push, email, webhooks', 'Telegram, push dans l’app, e-mail, webhooks', 'Telegram, App-Push, E-Mail, Webhooks', 'Telegram, app-push, e-mail, webhooks',
          'Telegram, push nell’app, e-mail, webhook', 'Telegram, push en la app, e-mail, webhooks'),
        NOT_SITE, money_range('6.95', '10.95'),
        L('2 alerts, checked every 15 min', '2 alertes, vérifiées toutes les 15 min', '2 Alarme, Prüfung alle 15 Min.', '2 meldingen, controle elke 15 min',
          '2 avvisi, controllo ogni 15 min', '2 alertas, revisión cada 15 min')]},
    # instantalert.me (+ /en/pricing, /en/faq, /en/terms)
    {'name': 'InstantAlert', 'url': 'https://instantalert.me/en/pricing', 'kind': 'app', 'cells': [
        ALERTS, NS,
        L('No, it says', 'Non, selon son site', 'Nein, laut Website', 'Nee, volgens de site', 'No, secondo il sito', 'No, según su web'),
        L('App push and email', 'Push dans l’app et e-mail', 'App-Push und E-Mail', 'App-push en e-mail', 'Push nell’app ed e-mail', 'Push en la app y e-mail'),
        L('Its pages disagree: 3 days (FAQ), none (terms)', 'Ses pages se contredisent : 3 jours (FAQ), aucun (CGU)', 'Widersprüchlich: 3 Tage (FAQ), keine (AGB)',
          'Tegenstrijdig: 3 dagen (FAQ), geen (voorwaarden)', 'Contraddittorio: 3 giorni (FAQ), nessuno (termini)', 'Contradictorio: 3 días (FAQ), ninguno (términos)'),
        money_range('4.99', '27.99'),
        L('3 alerts for 3 days, no card', '3 alertes pendant 3 jours, sans carte', '3 Alarme für 3 Tage, ohne Karte', '3 meldingen voor 3 dagen, zonder kaart',
          '3 avvisi per 3 giorni, senza carta', '3 alertas durante 3 días, sin tarjeta')]},
    # vinotify.me/pricing/ + /terms/
    {'name': 'Vinotify', 'url': 'https://www.vinotify.me/pricing/', 'kind': 'app', 'cells': [
        L('Alerts + price-drop alerts', 'Alertes + baisses de prix', 'Benachrichtigungen + Preissenkungen', 'Meldingen + prijsdalingen', 'Notifiche + cali di prezzo', 'Alertas + bajadas de precio'),
        NS, NS,
        L('App and email', 'App et e-mail', 'App und E-Mail', 'App en e-mail', 'App ed e-mail', 'App y e-mail'),
        WITHDRAW14, money_range('2.99', '22.99'),
        L('1 search, checked daily, expires after 14 days', '1 recherche, vérifiée une fois par jour, expire après 14 jours', '1 Suche, täglich geprüft, läuft nach 14 Tagen ab',
          '1 zoekopdracht, dagelijks gecontroleerd, verloopt na 14 dagen', '1 ricerca, controllata ogni giorno, scade dopo 14 giorni', '1 búsqueda, revisada a diario, caduca a los 14 días')]},
    # resellvault.co.uk/vintedbotmonitor + /pricing + /faq
    {'name': 'Resell Vault', 'url': 'https://resellvault.co.uk/vintedbotmonitor', 'kind': 'autobuy', 'cells': [
        ALERTS_AUTOBUY, NS,
        L('Not stated (says it does not store Vinted logins)', 'Non précisé (dit ne pas stocker d’identifiants Vinted)', 'Nicht angegeben (speichert laut Website keine Vinted-Logins)',
          'Niet vermeld (bewaart volgens de site geen Vinted-logins)', 'Non indicato (dice di non salvare i login Vinted)', 'No indicado (dice que no guarda accesos de Vinted)'),
        DISCORD,
        L('Its pages disagree: 30-day conditional guarantee vs &ldquo;no refunds&rdquo;', 'Ses pages se contredisent : garantie conditionnelle 30 jours / « no refunds »',
          'Widersprüchlich: 30-Tage-Garantie unter Bedingungen / &bdquo;no refunds&ldquo;', 'Tegenstrijdig: voorwaardelijke garantie van 30 dagen / &lsquo;no refunds&rsquo;',
          'Contraddittorio: garanzia condizionata 30 giorni / &laquo;no refunds&raquo;', 'Contradictorio: garantía condicionada de 30 días / &laquo;no refunds&raquo;'),
        money_range('28', '60', 'gbp', L(' <small>VAT incl.</small>', ' <small>TVA incl.</small>', ' <small>inkl. MwSt.</small>', ' <small>incl. btw</small>', ' <small>IVA incl.</small>', ' <small>IVA incl.</small>')),
        L('Free Discord + delayed UK sample feed', 'Discord gratuit + flux d’exemple UK en différé', 'Kostenloser Discord + verzögerter UK-Beispielfeed',
          'Gratis Discord + vertraagde Britse voorbeeldfeed', 'Discord gratuito + feed di esempio UK in differita', 'Discord gratis + feed de muestra de Reino Unido con retraso')]},
    # vinti.shop (+ /policies/refund-policy)
    {'name': 'VINTI', 'url': 'https://vinti.shop', 'kind': 'autobuy', 'cells': [
        ALERTS_AUTOBUY,
        L('&ldquo;Below market value&rdquo; label, no method stated', 'Étiquette « sous la valeur du marché », sans méthode', 'Label &bdquo;unter Marktwert&ldquo;, Methode nicht angegeben',
          'Label &lsquo;onder marktwaarde&rsquo;, methode niet vermeld', 'Etichetta &laquo;sotto il valore di mercato&raquo;, metodo non indicato', 'Etiqueta &laquo;por debajo del valor de mercado&raquo;, sin método'),
        L('Yes: you sign in to your Vinted account', 'Oui : tu te connectes à ton compte Vinted', 'Ja: du meldest dich mit deinem Vinted-Konto an', 'Ja: je logt in met je Vinted-account',
          'Sì: accedi con il tuo account Vinted', 'Sí: inicias sesión con tu cuenta de Vinted'),
        L('Discord, Telegram, desktop app', 'Discord, Telegram, app de bureau', 'Discord, Telegram, Desktop-App', 'Discord, Telegram, desktop-app', 'Discord, Telegram, app desktop', 'Discord, Telegram, app de escritorio'),
        L('No withdrawal refund once activated; 3-month minimum', 'Pas de remboursement après activation ; 3 mois minimum', 'Kein Widerruf nach Aktivierung; mindestens 3 Monate',
          'Geen herroeping na activering; minimaal 3 maanden', 'Nessun recesso dopo l’attivazione; minimo 3 mesi', 'Sin desistimiento tras la activación; mínimo 3 meses'),
        money_range('9.99', '79.99'), NS]},
    # monitorius.fr (+ /tarifs/, /centre-aide/)
    {'name': 'Monitorius', 'url': 'https://monitorius.fr/', 'kind': 'monitor', 'cells': [
        L('Alerts; purchase help, you confirm', 'Alertes ; aide à l’achat, tu valides', 'Benachrichtigungen; Kaufhilfe, du bestätigst', 'Meldingen; koophulp, jij bevestigt',
          'Notifiche; aiuto all’acquisto, confermi tu', 'Alertas; ayuda para comprar, tú confirmas'),
        NS, NS, DISCORD,
        L('Within 15 days of payment', 'Sous 15 jours après le paiement', 'Innerhalb von 15 Tagen nach Zahlung', 'Binnen 15 dagen na betaling', 'Entro 15 giorni dal pagamento', 'En los 15 días tras el pago'),
        money_range('25', None, note=L(' <small>(&euro;8/week, &euro;180/year)</small>', ' <small>(8&nbsp;&euro;/sem., 180&nbsp;&euro;/an)</small>', ' <small>(8&nbsp;&euro;/Woche, 180&nbsp;&euro;/Jahr)</small>',
                                        ' <small>(&euro;&nbsp;8/week, &euro;&nbsp;180/jaar)</small>', ' <small>(8&nbsp;&euro;/sett., 180&nbsp;&euro;/anno)</small>', ' <small>(8&nbsp;&euro;/sem., 180&nbsp;&euro;/año)</small>')),
        L('7-day trial with a code', 'Essai 7 jours avec un code', '7 Tage Test mit Code', '7 dagen proef met een code', 'Prova di 7 giorni con un codice', 'Prueba de 7 días con un código')]},
    # bot-vinted.com (tool at app.bot-vinted.com)
    {'name': 'Bot Vinted', 'url': 'https://bot-vinted.com', 'kind': 'monitor', 'cells': [
        ALERTS, NS, NS,
        L('Push via its home-screen app', 'Push via son app sur l’écran d’accueil', 'Push über die Homescreen-App', 'Push via de app op het beginscherm', 'Push tramite la sua app sulla schermata Home',
          'Push mediante su app en la pantalla de inicio'),
        L('Possible if the service fails, no window stated', 'Possible si le service ne tient pas ses promesses, sans délai indiqué', 'Möglich, wenn der Dienst nicht liefert; keine Frist angegeben',
          'Mogelijk als de dienst tekortschiet; geen termijn vermeld', 'Possibile se il servizio non funziona; nessun termine indicato', 'Posible si el servicio falla; sin plazo indicado'),
        L('Not shown (&ldquo;temporarily unavailable&rdquo;)', 'Non affiché (« momentanément indisponibles »)', 'Nicht angezeigt (&bdquo;vorübergehend nicht verfügbar&ldquo;)',
          'Niet getoond (&lsquo;tijdelijk niet beschikbaar&rsquo;)', 'Non mostrato (&laquo;momentaneamente non disponibili&raquo;)', 'No se muestra (&laquo;temporalmente no disponibles&raquo;)'),
        L('None stated', 'Aucune indiquée', 'Keine angegeben', 'Geen vermeld', 'Nessuna indicata', 'Ninguna indicada')]},
    # copmarket.fr (Belgian operator; luxury radar Japan + Vinted)
    {'name': 'CopMarket', 'url': 'https://copmarket.fr/', 'kind': 'autobuy', 'cells': [
        L('Luxury radar (Japan + Vinted), autobuy on Pro', 'Radar luxe (Japon + Vinted), achat auto sur Pro', 'Luxus-Radar (Japan + Vinted), Autobuy bei Pro', 'Luxeradar (Japan + Vinted), autobuy bij Pro',
          'Radar del lusso (Giappone + Vinted), acquisto automatico con Pro', 'Radar de lujo (Japón + Vinted), compra automática en Pro'),
        L('Yes: median of recent comparable listings', 'Oui : médiane d’annonces récentes comparables', 'Ja: Median vergleichbarer neuer Anzeigen', 'Ja: mediaan van recente vergelijkbare advertenties',
          'Sì: mediana di annunci recenti simili', 'Sí: mediana de anuncios recientes comparables'),
        L('Radar no; autobuy uses your Vinted session', 'Radar non ; l’achat auto utilise ta session Vinted', 'Radar nein; Autobuy nutzt deine Vinted-Sitzung', 'Radar nee; autobuy gebruikt je Vinted-sessie',
          'Radar no; l’acquisto automatico usa la tua sessione Vinted', 'Radar no; la compra automática usa tu sesión de Vinted'),
        L('Push, Discord, Telegram, email', 'Push, Discord, Telegram, e-mail', 'Push, Discord, Telegram, E-Mail', 'Push, Discord, Telegram, e-mail', 'Push, Discord, Telegram, e-mail', 'Push, Discord, Telegram, e-mail'),
        L('Current period not refunded', 'Période entamée non remboursée', 'Laufender Zeitraum wird nicht erstattet', 'Lopende periode niet terugbetaald', 'Periodo in corso non rimborsato', 'El periodo en curso no se reembolsa'),
        money_range('24.99', '49.99'),
        L('7-day trial, no card', 'Essai 7 jours, sans carte', '7 Tage Test, ohne Karte', '7 dagen proef, zonder kaart', 'Prova di 7 giorni, senza carta', 'Prueba de 7 días, sin tarjeta')]},
    # vintagelab.org/pricing
    {'name': 'VintageLab', 'url': 'https://www.vintagelab.org/pricing', 'kind': 'autobuy', 'cells': [
        ALERTS_AUTOBUY,
        L('Free price check, method not stated', 'Vérification de prix gratuite, sans méthode', 'Kostenloser Price-Check, Methode nicht angegeben', 'Gratis prijscheck, methode niet vermeld',
          'Controllo prezzi gratuito, metodo non indicato', 'Comprobación de precio gratis, sin método'),
        NS, DISCORD, WITHDRAW14, money_range('14.99', '29.99'),
        L('Community + delayed public feed', 'Communauté + flux public en différé', 'Community + öffentlicher Feed mit Verzögerung', 'Community + vertraagde openbare feed',
          'Community + feed pubblico in differita', 'Comunidad + feed público con retraso')]},
    # dealfindr.app (+ /prijzen, /functies, /voorwaarden)
    {'name': 'DealFindr', 'url': 'https://dealfindr.app/', 'kind': 'app', 'cells': [
        L('Alerts (Marktplaats + Vinted)', 'Alertes (Marktplaats + Vinted)', 'Benachrichtigungen (Marktplaats + Vinted)', 'Meldingen (Marktplaats + Vinted)', 'Notifiche (Marktplaats + Vinted)', 'Alertas (Marktplaats + Vinted)'),
        L('Market trends and resale estimates', 'Tendances du marché et estimations de revente', 'Markttrends und Wiederverkaufsschätzungen', 'Markttrends en doorverkoopschattingen',
          'Tendenze di mercato e stime di rivendita', 'Tendencias del mercado y estimaciones de reventa'),
        NS,
        L('App push (iOS)', 'Push dans l’app (iOS)', 'App-Push (iOS)', 'App-push (iOS)', 'Push nell’app (iOS)', 'Push en la app (iOS)'),
        L('14-day withdrawal, minus days used', 'Rétractation 14 jours, moins les jours utilisés', '14 Tage Widerruf, abzüglich genutzter Tage', '14 dagen herroeping, min gebruikte dagen',
          'Recesso 14 giorni, meno i giorni usati', 'Desistimiento 14 días, menos los días usados'),
        money_range('4.99', '24.99'),
        L('3 searches, hourly, alerts 30 min late', '3 recherches, toutes les heures, alertes avec 30 min de retard', '3 Suchen, stündlich, Alarme 30 Min. verzögert',
          '3 zoekopdrachten, elk uur, meldingen 30 min later', '3 ricerche, ogni ora, avvisi in ritardo di 30 min', '3 búsquedas, cada hora, alertas con 30 min de retraso')]},
    # github.com/drego85/VintedScanner (GPL-3.0, self-hosted; no hosted product)
    {'name': 'Vinted Scanner', 'url': 'https://github.com/drego85/VintedScanner', 'kind': 'script', 'cells': [
        L('Open-source script you host yourself', 'Script open source à héberger toi-même', 'Open-Source-Skript zum Selbst-Hosten', 'Opensource-script dat je zelf host',
          'Script open source da ospitare da te', 'Script de código abierto que alojas tú'),
        NS, NO,
        L('Email, Slack, Telegram', 'E-mail, Slack, Telegram', 'E-Mail, Slack, Telegram', 'E-mail, Slack, Telegram', 'E-mail, Slack, Telegram', 'E-mail, Slack, Telegram'),
        DASH, FREE,
        L('Free, you run it', 'Gratuit, tu le fais tourner', 'Kostenlos, du betreibst es', 'Gratis, je draait het zelf', 'Gratis, lo fai girare tu', 'Gratis, lo ejecutas tú')]},
    {'name': L('Vinted saved searches', 'Recherches sauvegardées Vinted', 'Gespeicherte Suchen auf Vinted', 'Opgeslagen zoekopdrachten op Vinted',
               'Ricerche salvate su Vinted', 'Búsquedas guardadas de Vinted'), 'url': None, 'kind': 'builtin', 'cells': [
        L('Built into Vinted', 'Intégré à Vinted', 'In Vinted eingebaut', 'Ingebouwd in Vinted', 'Integrato in Vinted', 'Integrado en Vinted'),
        NO,
        L('Your own account', 'Ton propre compte', 'Dein eigenes Konto', 'Je eigen account', 'Il tuo account', 'Tu propia cuenta'),
        L('&ldquo;+N&rdquo; counter, no alert', 'Compteur « +N », pas d’alerte', 'Zähler &bdquo;+N&ldquo;, kein Alarm', 'Teller &lsquo;+N&rsquo;, geen melding', 'Contatore &laquo;+N&raquo;, nessun avviso',
          'Contador &laquo;+N&raquo;, sin alerta'),
        DASH, FREE,
        L('Yes', 'Oui', 'Ja', 'Ja', 'Sì', 'Sí')]},
]


def name(c, lang):
    n = c['name']
    return n[lang] if isinstance(n, dict) else n


def others_count():
    """Competitors on the page, without SNYPD and Vinted's own saved searches."""
    return sum(1 for c in COMPETITORS if not c.get('us') and c.get('kind') != 'builtin')


# Vinted help centre article 435 "save your searches", per site (read 10 Oct 2026)
HELP435 = {'en': 'https://www.vinted.co.uk/help/435-save-your-searches', 'fr': 'https://www.vinted.fr/help/435', 'de': 'https://www.vinted.de/help/435',
           'nl': 'https://www.vinted.nl/help/435', 'it': 'https://www.vinted.it/help/435', 'es': 'https://www.vinted.es/help/435'}
HELP433 = {'en': 'https://www.vinted.co.uk/help/433', 'fr': 'https://www.vinted.fr/help/433', 'de': 'https://www.vinted.de/help/433',
           'nl': 'https://www.vinted.nl/help/433', 'it': 'https://www.vinted.it/help/433', 'es': 'https://www.vinted.es/help/433'}
# The words of each help page, quoted on the alert pages (verbatim, 10 Oct 2026)
HELP435_QUOTE = {
    'de': 'eine Zahl mit einem Pluszeichen angezeigt. Sie gibt an, wie viele neue Artikel nach deiner letzten Suchanfrage hochgeladen wurden',
    'nl': 'zie je een nummer met een +. Dit plusteken laat zien hoeveel nieuwe artikelen er zijn geüpload sinds de laatste keer dat je de zoekopdracht bekeek',
    'it': 'vedrai un numero con il segno più, che indica quanti nuovi articoli sono stati caricati dall’ultima volta che hai controllato quella ricerca',
    'es': 'verás un número con el signo de “+”; esto indica cuántos artículos nuevos se han subido desde la última vez que realizaste esa búsqueda',
}
HELP435_TITLE = {'de': 'Suchanfragen speichern', 'nl': 'Zoekopdrachten opslaan', 'it': 'Salvare le ricerche', 'es': 'Guardar tus búsquedas'}

# "Every way to get a Vinted alert": (name, what you get, how it reaches you, cost, source url). Facts as in COMPETITORS.
ALERT_WAYS = [
    {'name': L('Vinted saved searches', 'Recherches sauvegardées Vinted', 'Gespeicherte Suchen auf Vinted', 'Opgeslagen zoekopdrachten op Vinted', 'Ricerche salvate su Vinted', 'Búsquedas guardadas de Vinted'),
     'src': HELP435,
     'get': L('A &ldquo;+N&rdquo; count of new items the next time you open the search bar', 'Un compteur « +N » de nouveaux articles à ta prochaine ouverture de la barre de recherche',
              'Ein Zähler &bdquo;+N&ldquo; mit neuen Artikeln, wenn du das Suchfeld wieder öffnest', 'Een teller &lsquo;+N&rsquo; met nieuwe artikelen als je de zoekbalk weer opent',
              'Un contatore &laquo;+N&raquo; dei nuovi articoli quando riapri la barra di ricerca', 'Un contador &laquo;+N&raquo; de artículos nuevos cuando vuelves a abrir la barra de búsqueda'),
     'how': L('Inside the app, no push', 'Dans l’app, sans push', 'In der App, kein Push', 'In de app, geen push', 'Nell’app, nessun push', 'Dentro de la app, sin push'),
     'cost': FREE},
    {'name': L('Following a seller on Vinted', 'Suivre un vendeur sur Vinted', 'Einem Mitglied auf Vinted folgen', 'Een lid volgen op Vinted', 'Seguire un membro su Vinted', 'Seguir a un miembro en Vinted'),
     'src': HELP433,
     'get': L('A notification when that member lists a new item', 'Une notification quand ce membre met un article en ligne', 'Eine Benachrichtigung, wenn dieses Mitglied einen neuen Artikel hochlädt',
              'Een notificatie als dat lid een nieuw artikel plaatst', 'Una notifica quando quel membro carica un nuovo articolo', 'Una notificación cuando ese miembro sube un artículo nuevo'),
     'how': L('Vinted notifications', 'Notifications Vinted', 'Vinted-Benachrichtigungen', 'Vinted-notificaties', 'Notifiche Vinted', 'Notificaciones de Vinted'),
     'cost': FREE},
    {'name': 'InstantAlert', 'src': 'https://instantalert.me/en/pricing',
     'get': L('New listings for your alerts', 'Les nouvelles annonces de tes alertes', 'Neue Anzeigen für deine Alarme', 'Nieuwe advertenties voor je meldingen', 'Nuovi annunci per i tuoi avvisi', 'Anuncios nuevos para tus alertas'),
     'how': L('Its app (iOS, Android) and email', 'Son app (iOS, Android) et e-mail', 'Eigene App (iOS, Android) und E-Mail', 'Eigen app (iOS, Android) en e-mail', 'La sua app (iOS, Android) ed e-mail', 'Su app (iOS, Android) y e-mail'),
     'cost': money_range('4.99', '27.99', note=L(' / month; 3 alerts free for 3 days', ' / mois ; 3 alertes gratuites 3 jours', ' / Monat; 3 Alarme 3 Tage gratis', ' / maand; 3 meldingen 3 dagen gratis',
                                                 ' / mese; 3 avvisi gratis per 3 giorni', ' / mes; 3 alertas gratis durante 3 días'))},
    {'name': 'Vinotify', 'src': 'https://www.vinotify.me/pricing/',
     'get': L('New listings and price drops', 'Nouvelles annonces et baisses de prix', 'Neue Anzeigen und Preissenkungen', 'Nieuwe advertenties en prijsdalingen', 'Nuovi annunci e cali di prezzo', 'Anuncios nuevos y bajadas de precio'),
     'how': L('Its app (iOS, Android) and email', 'Son app (iOS, Android) et e-mail', 'Eigene App (iOS, Android) und E-Mail', 'Eigen app (iOS, Android) en e-mail', 'La sua app (iOS, Android) ed e-mail', 'Su app (iOS, Android) y e-mail'),
     'cost': money_range('2.99', '22.99', note=L(' / month; free: 1 search checked daily', ' / mois ; gratuit : 1 recherche vérifiée chaque jour', ' / Monat; gratis: 1 Suche, täglich geprüft',
                                                 ' / maand; gratis: 1 zoekopdracht, dagelijks gecontroleerd', ' / mese; gratis: 1 ricerca controllata ogni giorno', ' / mes; gratis: 1 búsqueda revisada a diario'))},
    {'name': 'Clothing Alerts', 'src': 'https://clothing-alerts.com/',
     'get': L('New listings for saved searches', 'Nouvelles annonces de recherches sauvegardées', 'Neue Anzeigen für gespeicherte Suchen', 'Nieuwe advertenties voor opgeslagen zoekopdrachten',
              'Nuovi annunci per le ricerche salvate', 'Anuncios nuevos de búsquedas guardadas'),
     'how': L('Its app (iOS, Android)', 'Son app (iOS, Android)', 'Eigene App (iOS, Android)', 'Eigen app (iOS, Android)', 'La sua app (iOS, Android)', 'Su app (iOS, Android)'),
     'cost': L('Free with ads; paid options, prices not stated', 'Gratuit avec pub ; options payantes, prix non indiqués', 'Gratis mit Werbung; Bezahloptionen ohne Preisangabe',
               'Gratis met advertenties; betaalde opties, prijzen niet vermeld', 'Gratis con pubblicità; opzioni a pagamento, prezzi non indicati', 'Gratis con anuncios; opciones de pago sin precios')},
    {'name': 'Telvin Bot', 'src': 'https://www.telvin-bot.com/en/',
     'get': L('New listings for keyword alerts', 'Nouvelles annonces pour des alertes mots-clés', 'Neue Anzeigen für Stichwort-Alarme', 'Nieuwe advertenties voor zoekwoordmeldingen',
              'Nuovi annunci per avvisi a parola chiave', 'Anuncios nuevos para alertas por palabra clave'),
     'how': L('Telegram', 'Telegram', 'Telegram', 'Telegram', 'Telegram', 'Telegram'),
     'cost': money_range('4.90', '14.90', note=L(' / month; free: 1 alert, 100 notifications', ' / mois ; gratuit : 1 alerte, 100 notifications', ' / Monat; gratis: 1 Alarm, 100 Benachrichtigungen',
                                                 ' / maand; gratis: 1 melding, 100 notificaties', ' / mese; gratis: 1 avviso, 100 notifiche', ' / mes; gratis: 1 alerta, 100 notificaciones'))},
    {'name': 'Resell Reserve', 'src': 'https://resellreserve.co.uk/',
     'get': L('Listings in its item channels, plus autobuy', 'Annonces dans ses salons par type d’article, plus achat auto', 'Anzeigen in Kanälen nach Artikeltyp, plus Autobuy',
              'Advertenties in kanalen per artikeltype, plus autobuy', 'Annunci nei canali per tipo di articolo, più acquisto automatico', 'Anuncios en canales por tipo de artículo, más compra automática'),
     'how': DISCORD,
     'cost': money_range('19.99', '44.99', 'gbp', note=L(' / month', ' / mois', ' / Monat', ' / maand', ' / mese', ' / mes'))},
    {'name': 'SNYPD', 'src': SITE + '/plans', 'us': True,
     'get': L('Every new listing for the Vinted search link you paste, all filters kept', 'Chaque nouvelle annonce du lien de recherche Vinted que tu colles, tous filtres gardés',
              'Jede neue Anzeige zu dem Vinted-Suchlink, den du einfügst, mit allen Filtern', 'Elke nieuwe advertentie voor de Vinted-zoeklink die je plakt, met alle filters',
              'Ogni nuovo annuncio del link di ricerca Vinted che incolli, con tutti i filtri', 'Cada anuncio nuevo del enlace de búsqueda de Vinted que pegues, con todos los filtros'),
     'how': L('Push to phone and computer, no app store', 'Push sur téléphone et ordinateur, sans store', 'Push auf Handy und Computer, ohne App-Store', 'Push op telefoon en computer, zonder app store',
              'Push su telefono e computer, senza app store', 'Push en móvil y ordenador, sin tienda de apps'),
     'cost': L('Free: 1 search, 24/7 for @@trial_days@@ days; paid from @@price:solo@@ / month, or @@price:pass@@ once for @@pass_days@@ days',
               'Gratuit : 1 recherche, 24h/24 pendant @@trial_days@@ jours ; payant dès @@price:solo@@ / mois, ou @@price:pass@@ en une fois pour @@pass_days@@ jours',
               'Gratis: 1 Suche, @@trial_days@@ Tage rund um die Uhr; bezahlt ab @@price:solo@@ / Monat oder @@price:pass@@ einmalig für @@pass_days@@ Tage',
               'Gratis: 1 zoekopdracht, @@trial_days@@ dagen 24/7; betaald vanaf @@price:solo@@ / maand of @@price:pass@@ eenmalig voor @@pass_days@@ dagen',
               'Gratis: 1 ricerca, 24 ore su 24 per @@trial_days@@ giorni; a pagamento da @@price:solo@@ / mese o @@price:pass@@ una tantum per @@pass_days@@ giorni',
               'Gratis: 1 búsqueda, 24/7 durante @@trial_days@@ días; de pago desde @@price:solo@@ / mes o @@price:pass@@ en un único pago por @@pass_days@@ días')},
]
ALERT_WAYS_HEAD = {
    'en': ['WAY', 'WHAT YOU GET', 'HOW IT REACHES YOU', 'COST', 'SOURCE'],
    'fr': ['MOYEN', 'CE QUE TU REÇOIS', 'COMMENT ÇA T’ARRIVE', 'PRIX', 'SOURCE'],
    'de': ['WEG', 'WAS DU BEKOMMST', 'WIE ES DICH ERREICHT', 'KOSTEN', 'QUELLE'],
    'nl': ['MANIER', 'WAT JE KRIJGT', 'HOE HET JE BEREIKT', 'KOSTEN', 'BRON'],
    'it': ['MODO', 'COSA RICEVI', 'COME TI ARRIVA', 'COSTO', 'FONTE'],
    'es': ['FORMA', 'QUÉ RECIBES', 'CÓMO TE LLEGA', 'COSTE', 'FUENTE'],
}
SOURCE_WORD = L('own site', 'son site', 'eigene Website', 'eigen site', 'sito ufficiale', 'web oficial')
VINTED_HELP_WORD = L('Vinted help', 'aide Vinted', 'Vinted-Hilfe', 'Vinted-hulp', 'aiuto Vinted', 'ayuda de Vinted')
