"""Copy for two help guides (18 Oct 2026): 'saved' (Vinted saved searches, 8 languages) and
'pricedrop' (does Vinted tell you when a price drops?, EN FR DE NL). Data only; a generator renders it.

Targets (Google autocomplete): "vinted saved searches", "vinted saved searches disappeared", "how many saved
searches can you have on vinted", "where are saved searches on vinted", "retrouver recherche enregistrée vinted",
"vinted gespeicherte suche finden", "vinted opgeslagen zoekopdrachten", "vinted ricerca salvata", "vinted búsquedas
guardadas", "vinted gdzie zapisane wyszukiwania", "vinted zapisane wyszukiwania", "vinted sparade sökningar",
"skapa bevakning vinted"; "vinted price drop notification", "vinted favourites price drop", "vinted notification
baisse de prix", "vinted preis reduziert benachrichtigung", "vinted melding prijs verlaagd".

SOURCES. Every statement about Vinted is a short verbatim quote or a faithful paraphrase of Vinted's own help
centre IN THE PAGE'S LANGUAGE, fetched from this machine on 18 Oct 2026 (curl, desktop Chrome UA, 8 s apart; all
HTTP 200 with the article body, no challenge page). Raw HTML + extracted article text:
C:\\Users\\Tanus\\website\\outreach\\research-2026-10-18\\vinted-help\\ (<lang>-help-<id>.html, articles-2026-10-18.txt).
  435 "Save your searches": co.uk, fr, de, nl, it, es (fetched 18 Oct), pl, se (saved earlier on 18 Oct).
      Steps (search bar -> Save icon; DE: Fähnchen-Icon), unlimited number, removed after 6 months if never
      opened, "+N" counter of new items since you last checked, reset when you view the search, remove by
      unmarking the icon.
  433 "Managing your notifications": same 8 sites. Notification list includes: members you follow list new
      items, price of a favourited item reduced, favourited item sold. New saved-search results are NOT listed.
      Push settings: Profile > Settings > Push notifications, daily limit for non-high-priority ones.
  258 "Making an offer": co.uk, fr, de, nl (fetched 18 Oct; en/fr/de identical to copy_sold.QUOTES of 10 Oct).
      Seller can offer a buyer a lower price in the conversation, up to 40% less; visible only to that buyer;
      others can still buy until that buyer presses Buy now.
Nothing here says Vinted's notifications are unreliable. SNYPD facts only from outreach/00-fact-sheet.md; plan
numbers are plans.py tokens (@@trial_days@@, @@price:solo@@). SNYPD does NOT track price drops and the pages say so.
One short verbatim quote (< 15 words) per page; everything else is paraphrase with a link to the article.

Claude's translation note: written per language by Claude (not machine-translated), informal tu/du/je/tu/tú/ty/du
like the existing pages; Vinted's own UI words per site (FR "Sauvegarder", DE "Fähnchen-Icon", PL "polubiony",
SV "favoritmarkerat"). Not reviewed by a native speaker yet.

Placeholders (.format): {h433} {h435} {h258} {read} {bot} {notify} {notwork} {sold} {saved} {pricedrop}.
{pricedrop} is used only in EN/FR/DE/NL, {sold} only in EN/FR/DE (the pages that exist in those languages).
"""
HELP_READ = '2026-10-18'

HELP = {  # url per (article, lang)
    ('435', 'en'): 'https://www.vinted.co.uk/help/435', ('435', 'fr'): 'https://www.vinted.fr/help/435',
    ('435', 'de'): 'https://www.vinted.de/help/435', ('435', 'nl'): 'https://www.vinted.nl/help/435',
    ('435', 'it'): 'https://www.vinted.it/help/435', ('435', 'es'): 'https://www.vinted.es/help/435',
    ('435', 'pl'): 'https://www.vinted.pl/help/435', ('435', 'sv'): 'https://www.vinted.se/help/435',
    ('433', 'en'): 'https://www.vinted.co.uk/help/433', ('433', 'fr'): 'https://www.vinted.fr/help/433',
    ('433', 'de'): 'https://www.vinted.de/help/433', ('433', 'nl'): 'https://www.vinted.nl/help/433',
    ('433', 'it'): 'https://www.vinted.it/help/433', ('433', 'es'): 'https://www.vinted.es/help/433',
    ('433', 'pl'): 'https://www.vinted.pl/help/433', ('433', 'sv'): 'https://www.vinted.se/help/433',
    ('258', 'en'): 'https://www.vinted.co.uk/help/258', ('258', 'fr'): 'https://www.vinted.fr/help/258',
    ('258', 'de'): 'https://www.vinted.de/help/258', ('258', 'nl'): 'https://www.vinted.nl/help/258',
}

# Article titles exactly as each help page shows them (18 Oct 2026); used inside the <cite> links below.
HELP_TITLE = {
    ('435', 'en'): 'Save your searches', ('435', 'fr'): 'Comment sauvegarder une recherche\xa0?',
    ('435', 'de'): 'Suchanfragen speichern', ('435', 'nl'): 'Zoekopdrachten opslaan',
    ('435', 'it'): 'Salvare le ricerche', ('435', 'es'): 'Guardar tus búsquedas',
    ('435', 'pl'): 'Jak zapisać wyszukiwanie', ('435', 'sv'): 'Spara dina sökningar',
    ('433', 'en'): 'Managing your notifications', ('433', 'fr'): 'Comment gérer tes notifications\xa0?',
    ('433', 'de'): 'Verwaltung deiner Benachrichtigungen', ('433', 'nl'): 'Notificaties beheren',
    ('433', 'it'): 'Gestione delle notifiche', ('433', 'es'): 'Cómo gestionar tus notificaciones',
    ('433', 'pl'): 'Jak zarządzać powiadomieniami', ('433', 'sv'): 'Hantera dina notifikationer',
    ('258', 'en'): 'Making an offer (suggesting a different price)', ('258', 'fr'): 'Comment faire une offre (proposer un prix différent)\xa0?',
    ('258', 'de'): 'Verhandeln (einen anderen Preis vorschlagen)', ('258', 'nl'): 'Een bod doen (een andere prijs voorstellen)',
}

GUIDES = {
  # ======================================================================== SAVED SEARCHES
  'saved': {
    'slugs': {'en': '/vinted-saved-searches', 'fr': '/fr/recherches-enregistrees-vinted', 'de': '/de/vinted-gespeicherte-suchen',
              'nl': '/nl/vinted-opgeslagen-zoekopdrachten', 'it': '/it/vinted-ricerche-salvate', 'es': '/es/vinted-busquedas-guardadas',
              'pl': '/pl/vinted-zapisane-wyszukiwania', 'sv': '/sv/vinted-sparade-sokningar'},

    # ---------------------------------------------------------------- EN
    'en': dict(
        title='Vinted saved searches: where they are, limits (2026) | SNYPD',
        desc='Where Vinted keeps your saved searches, how many you can save, why they disappear after 6 months and what +N means. Straight from Vinted’s help centre.',
        eyebrow='VINTED SAVED SEARCHES',
        h1='Vinted saved searches: where they are, how many, why they disappear',
        lead='What Vinted’s help centre says about saved searches (read {read}): saving, finding, limits, disappearing searches and the “+N” counter. Plus how to get a push alert for each new listing.',
        answer='Press the Save icon next to a search in the search bar to save it; you find it in the search bar again later. You can save an unlimited number. A saved search disappears after 6 months if you never open it. The “+N” next to it counts the new items listed since you last checked, and resets when you view the search. Vinted’s help centre describes no notification for new results of a saved search.',
        toc=[('save', 'How to save a search'), ('where', 'Where to find them'), ('how-many', 'How many you can save'),
             ('disappeared', 'Why they disappear'), ('counter', 'The +N counter'), ('not-sent', 'What Vinted does not send'),
             ('push', 'A push for each new listing')],
        sections=[
            ('save', 'How to save a search on Vinted',
             '<p>Vinted’s help centre describes two steps:</p>'
             '<ol><li>Go to the search bar. It shows the searches you made recently.</li>'
             '<li>Hover over the search you want to keep and press the <strong>Save</strong> icon next to it.</li></ol>'
             '<p>To remove a saved search later, unmark the same Save icon.</p>'),
            ('where', 'Where are saved searches on Vinted?',
             '<p>In the search bar. Vinted’s help sends you there both to save a search and to come back to it: the next time you open the search bar, a saved search shows a number with a plus next to it (more on that <a href="#counter">below</a>).</p>'),
            ('how-many', 'How many saved searches can you have on Vinted?',
             '<p>As many as you like. Vinted’s help centre says you can save an unlimited number of searches.</p>'),
            ('disappeared', 'Why did my Vinted saved searches disappear?',
             '<p>Vinted’s help names one rule: your saved searches disappear after 6 months if you never open them. The only other way one goes is by hand: unmarking its Save icon removes it.</p>'
             '<ul><li>Open the saved searches you want to keep now and then, so none sits unopened for 6 months.</li>'
             '<li>If one is gone, run the search again and save it again (steps <a href="#save">above</a>).</li></ul>'),
            ('counter', 'What the “+N” next to a saved search means',
             '<blockquote>“you’ll see a number with a plus indicating how many new items were listed”'
             '<cite>Vinted help, <a href="{h435}" rel="nofollow noopener">Save your searches</a> (read {read})</cite></blockquote>'
             '<p>The number counts the new items listed since you last checked the search. Every time you view the search, the counter goes back to zero. So “+12” means 12 new listings since your last look: not 12 items left, and not 12 price changes.</p>'),
            ('not-sent', 'What Vinted does not send for saved searches',
             '<p>Vinted’s help on notifications (<a href="{h433}" rel="nofollow noopener">Managing your notifications</a>) lists when you may get one. Among them:</p>'
             '<ul><li>members you follow list new items;</li><li>the price of an item you favourited is reduced;</li><li>an item you favourited is sold.</li></ul>'
             '<p>New results of a saved search are not on that list. A saved search gives you the counter, which you see when you open the search bar.</p>'
             '<p>For every new listing that matches a search, you need a tool that checks the search for you. All the options side by side: <a href="{notify}">Vinted alerts for new listings</a>. For favourites: <a href="{pricedrop}">Vinted price drop notifications</a>.</p>'),
            ('push', 'If you want a push for each new listing',
             '<p>SNYPD watches the same search you have on Vinted and sends a push notification to your phone or computer for each new listing that matches:</p>'
             '<ol><li>Open your search on Vinted in a browser, with your filters (brand, size, price, condition).</li>'
             '<li>Copy the address from the address bar. It contains <code>/catalog?</code>.</li>'
             '<li>Paste it into SNYPD and switch the search on.</li>'
             '<li>SNYPD checks it about every 30 seconds to a minute and sends a push when a new listing matches. The alert opens the listing on Vinted.</li></ol>'
             '<p>That is how often SNYPD looks, not a delivery time: Vinted itself shows a new listing in search a few minutes after it is posted. SNYPD never logs in to your Vinted account, never buys and never messages sellers.</p>'
             '<p>Free: 1 search, 24/7 with alerts for the first @@trial_days@@ days after your first search in SNYPD, then only while the dashboard is open. Paid plans from @@price:solo@@ per month run 24/7. On iPhone, add SNYPD to the Home Screen first (Apple allows web push only there). More: <a href="{bot}">SNYPD, the Vinted bot for alerts</a>. Every free option side by side: <a href="/free-vinted-bot">free Vinted bot</a>.</p>'),
        ],
        faq=[
            ('How many saved searches can you have on Vinted?',
             'As many as you want. Vinted’s help centre says you can save an unlimited number of searches.'),
            ('Why did my saved searches disappear on Vinted?',
             'According to Vinted’s help centre, a saved search disappears after 6 months if you never open it. It is also removed when its Save icon is unmarked. To get it back, run the search again and save it from the search bar.'),
            ('Where do I find my saved searches on Vinted?',
             'In the search bar. Open it and your saved searches are there, each with a “+N” count of new items since you last checked.'),
            ('Does Vinted notify me about new items in a saved search?',
             'Its help centre describes a counter, not a notification: a number with a plus in the search bar, reset each time you view the search. Vinted does send notifications for members you follow and for items you favourited. For a push per new listing, paste the search link into an alert tool such as <a href="{bot}">SNYPD</a>.'),
        ],
        cta_h='Get a push for your Vinted search'),

    # ---------------------------------------------------------------- FR
    'fr': dict(
        title='Recherches enregistrées Vinted\xa0: les retrouver (2026) | SNYPD',
        desc='Où retrouver tes recherches sauvegardées sur Vinted, combien tu peux en garder, pourquoi elles disparaissent après 6 mois et ce que veut dire le +N.',
        eyebrow='RECHERCHES VINTED',
        h1='Recherches sauvegardées sur Vinted\xa0: où les retrouver, combien, pourquoi elles disparaissent',
        lead='Ce que dit le centre d’aide de Vinted sur les recherches sauvegardées, ou «\xa0enregistrées\xa0» (lu le {read})\xa0: sauvegarde, emplacement, limite, disparition et compteur «\xa0+N\xa0». Et comment recevoir un push à chaque nouvelle annonce.',
        answer='Pour sauvegarder une recherche, appuie sur l’icône «\xa0Sauvegarder\xa0» à côté d’elle dans la barre de recherche\xa0; tu la retrouves ensuite au même endroit. Le nombre est illimité. Une recherche sauvegardée jamais consultée est retirée au bout de 6 mois. Le «\xa0+N\xa0» compte les nouveaux articles mis en ligne depuis ta dernière consultation et repart à zéro quand tu la consultes. Le centre d’aide ne décrit aucune notification pour les nouveaux résultats d’une recherche sauvegardée.',
        toc=[('sauvegarder', 'Sauvegarder une recherche'), ('retrouver', 'Où les retrouver'), ('combien', 'Combien en garder'),
             ('disparues', 'Pourquoi elles disparaissent'), ('compteur', 'Le compteur +N'), ('notifications', 'Ce que Vinted n’envoie pas'),
             ('push', 'Un push par nouvelle annonce')],
        sections=[
            ('sauvegarder', 'Comment sauvegarder une recherche sur Vinted',
             '<p>Le centre d’aide de Vinted décrit deux étapes\xa0:</p>'
             '<ol><li>Va dans la barre de recherche. Tu y vois les recherches que tu as faites récemment.</li>'
             '<li>Survole celle que tu veux garder et appuie sur l’icône <strong>Sauvegarder</strong> à côté.</li></ol>'
             '<p>Pour retirer une recherche sauvegardée, il suffit de décocher la même icône.</p>'),
            ('retrouver', 'Où retrouver une recherche enregistrée sur Vinted\xa0?',
             '<p>Dans la barre de recherche. L’aide de Vinted t’y envoie pour sauvegarder une recherche comme pour y revenir\xa0: la prochaine fois que tu ouvres la barre de recherche, ta recherche sauvegardée affiche un nombre suivi d’un signe plus (détails <a href="#compteur">plus bas</a>).</p>'),
            ('combien', 'Combien de recherches peux-tu sauvegarder sur Vinted\xa0?',
             '<p>Autant que tu veux. Le centre d’aide de Vinted indique que tu peux sauvegarder un nombre illimité de recherches.</p>'),
            ('disparues', 'Pourquoi mes recherches sauvegardées ont disparu\xa0?',
             '<p>L’aide de Vinted donne une règle\xa0: les recherches sauvegardées que tu ne consultes jamais sont retirées automatiquement au bout de 6 mois. L’autre façon d’en perdre une, c’est à la main\xa0: décocher son icône «\xa0Sauvegarder\xa0» la retire.</p>'
             '<ul><li>Ouvre de temps en temps les recherches que tu veux garder, pour qu’aucune ne reste 6 mois sans être consultée.</li>'
             '<li>Si l’une a disparu, refais la recherche et sauvegarde-la à nouveau (étapes <a href="#sauvegarder">plus haut</a>).</li></ul>'),
            ('compteur', 'Ce que veut dire le «\xa0+N\xa0» à côté d’une recherche',
             '<blockquote>«\xa0un nombre suivi d’un signe plus indiquant le nombre de nouveaux articles\xa0»'
             '<cite>Aide Vinted, <a href="{h435}" rel="nofollow noopener">Comment sauvegarder une recherche\xa0?</a> (lu le {read})</cite></blockquote>'
             '<p>Ce nombre compte les nouveaux articles mis en ligne depuis la dernière fois que tu as fait cette recherche. À chaque fois que tu la consultes, le compteur est remis à zéro. Donc «\xa0+12\xa0» veut dire 12 nouvelles annonces depuis ton dernier passage\xa0: pas 12 articles restants, ni 12 baisses de prix.</p>'),
            ('notifications', 'Ce que Vinted n’envoie pas pour une recherche sauvegardée',
             '<p>L’aide de Vinted sur les notifications (<a href="{h433}" rel="nofollow noopener">Comment gérer tes notifications\xa0?</a>) liste les cas où tu peux en recevoir une. Entre autres\xa0:</p>'
             '<ul><li>un membre que tu suis a mis en ligne un nouvel article\xa0;</li><li>le prix d’un article que tu as ajouté à tes favoris a baissé\xa0;</li><li>un article de tes favoris a été vendu.</li></ul>'
             '<p>Les nouveaux résultats d’une recherche sauvegardée ne figurent pas dans cette liste. Une recherche sauvegardée te donne le compteur, que tu vois en ouvrant la barre de recherche.</p>'
             '<p>Pour chaque nouvelle annonce qui correspond à une recherche, il te faut un outil qui vérifie la recherche à ta place. Toutes les options côte à côte\xa0: <a href="{notify}">alertes Vinted pour les nouvelles annonces</a>. Le guide pas à pas\xa0: <a href="/fr/alerte-vinted-nouvelle-annonce">recevoir une alerte pour chaque nouvelle annonce</a>. Pour les favoris\xa0: <a href="{pricedrop}">notification de baisse de prix sur Vinted</a>.</p>'),
            ('push', 'Pour recevoir un push à chaque nouvelle annonce',
             '<p>SNYPD surveille la même recherche que celle que tu as sur Vinted et envoie une notification push sur ton téléphone ou ton ordinateur pour chaque nouvelle annonce qui correspond\xa0:</p>'
             '<ol><li>Ouvre ta recherche sur Vinted dans un navigateur, avec tes filtres (marque, taille, prix, état).</li>'
             '<li>Copie l’adresse dans la barre d’adresse. Elle contient <code>/catalog?</code>.</li>'
             '<li>Colle-la dans SNYPD et active la recherche.</li>'
             '<li>SNYPD la vérifie environ toutes les 30 secondes à une minute et t’envoie un push dès qu’une nouvelle annonce correspond. L’alerte ouvre l’annonce sur Vinted.</li></ol>'
             '<p>C’est la fréquence à laquelle SNYPD regarde, pas un délai de livraison\xa0: Vinted lui-même affiche une nouvelle annonce dans sa recherche quelques minutes après sa mise en ligne. SNYPD ne se connecte jamais à ton compte Vinted, n’achète rien et n’écrit pas aux vendeurs.</p>'
             '<p>Gratuit\xa0: 1 recherche, 24/7 avec alertes pendant les @@trial_days@@ premiers jours après ta première recherche dans SNYPD, puis seulement quand le tableau de bord est ouvert. Plans payants dès @@price:solo@@ par mois, 24/7. Sur iPhone, ajoute d’abord SNYPD à l’écran d’accueil (Apple n’autorise les notifications web que là). En savoir plus\xa0: <a href="{bot}">SNYPD, le bot Vinted d’alertes</a>.</p>'),
        ],
        faq=[
            ('Combien de recherches peut-on sauvegarder sur Vinted\xa0?',
             'Autant que tu veux. Le centre d’aide de Vinted indique un nombre illimité de recherches sauvegardées.'),
            ('Pourquoi mes recherches sauvegardées ont disparu sur Vinted\xa0?',
             'D’après le centre d’aide de Vinted, une recherche sauvegardée que tu ne consultes jamais est retirée automatiquement au bout de 6 mois. Elle disparaît aussi si son icône «\xa0Sauvegarder\xa0» est décochée. Pour la récupérer, refais la recherche et sauvegarde-la depuis la barre de recherche.'),
            ('Comment retrouver une recherche enregistrée sur Vinted\xa0?',
             'Ouvre la barre de recherche\xa0: tes recherches sauvegardées y sont, chacune avec un compteur «\xa0+N\xa0» des nouveaux articles depuis ta dernière consultation.'),
            ('Vinted me prévient-il des nouveaux articles d’une recherche sauvegardée\xa0?',
             'Son centre d’aide décrit un compteur, pas une notification\xa0: un nombre suivi d’un signe plus dans la barre de recherche, remis à zéro à chaque consultation. Vinted envoie en revanche des notifications pour les membres que tu suis et les articles de tes favoris. Pour un push à chaque nouvelle annonce, colle le lien de ta recherche dans un outil d’alertes comme <a href="{bot}">SNYPD</a>.'),
        ],
        cta_h='Reçois un push pour ta recherche Vinted'),

    # ---------------------------------------------------------------- DE
    'de': dict(
        title='Vinted gespeicherte Suche finden: so geht’s (2026) | SNYPD',
        desc='Wo du gespeicherte Suchen auf Vinted findest, wie viele du speichern kannst, warum sie nach 6 Monaten verschwinden und was +N bedeutet. Laut Vinted-Hilfe.',
        eyebrow='VINTED GESPEICHERTE SUCHEN',
        h1='Gespeicherte Suchen auf Vinted: finden, speichern, Limit',
        lead='Was die Vinted-Hilfe über gespeicherte Suchen sagt (gelesen am {read}): speichern, wiederfinden, Limit, verschwundene Suchen und der Zähler „+N“. Dazu, wie du für jeden neuen Artikel eine Push-Nachricht bekommst.',
        answer='Du speicherst eine Suche, indem du im Suchfeld neben ihr auf das Fähnchen-Icon tippst; dort findest du sie später wieder. Du kannst so viele speichern, wie du möchtest. Eine gespeicherte Suche, die du 6 Monate lang nicht abrufst, wird entfernt. Das „+N“ daneben zählt die neuen Artikel seit deiner letzten Suche und springt auf null, sobald du die Ergebnisse ansiehst. Eine Benachrichtigung für neue Treffer einer gespeicherten Suche beschreibt die Vinted-Hilfe nicht.',
        toc=[('speichern', 'Suche speichern'), ('finden', 'Wo du sie findest'), ('anzahl', 'Wie viele gehen'),
             ('verschwunden', 'Warum sie verschwinden'), ('zaehler', 'Der Zähler +N'), ('benachrichtigungen', 'Was Vinted nicht schickt'),
             ('push', 'Push für jeden neuen Artikel')],
        sections=[
            ('speichern', 'So speicherst du eine Suche auf Vinted',
             '<p>Die Vinted-Hilfe beschreibt zwei Schritte:</p>'
             '<ol><li>Geh zum Suchfeld. Dort siehst du die Suchen, die du zuletzt gemacht hast.</li>'
             '<li>Tippe neben der Suche, die du behalten willst, auf das <strong>Fähnchen-Icon</strong>. Fertig.</li></ol>'
             '<p>Um eine gespeicherte Suche wieder zu entfernen, tippst du noch einmal auf dasselbe Fähnchen.</p>'),
            ('finden', 'Wo finde ich gespeicherte Suchen auf Vinted?',
             '<p>Im Suchfeld. Die Vinted-Hilfe schickt dich dorthin, um eine Suche zu speichern und um sie wiederzufinden: Wenn du das nächste Mal zum Suchfeld gehst, steht neben der gespeicherten Suche eine Zahl mit Pluszeichen (mehr dazu <a href="#zaehler">weiter unten</a>).</p>'),
            ('anzahl', 'Wie viele Suchen kann man auf Vinted speichern?',
             '<p>So viele du möchtest. Laut Vinted-Hilfe gibt es keine Obergrenze.</p>'),
            ('verschwunden', 'Warum sind meine gespeicherten Suchen weg?',
             '<p>Die Vinted-Hilfe nennt eine Regel: Gespeicherte Suchen werden entfernt, wenn du sie 6 Monate lang nicht abrufst. Sonst verschwindet eine Suche nur von Hand: Ein zweiter Tipp auf ihr Fähnchen entfernt die Markierung.</p>'
             '<ul><li>Öffne die Suchen, die du behalten willst, ab und zu, damit keine 6 Monate lang ungeöffnet bleibt.</li>'
             '<li>Ist eine weg, such noch einmal und speichere die Suche neu (Schritte <a href="#speichern">oben</a>).</li></ul>'),
            ('zaehler', 'Was das „+N“ neben einer gespeicherten Suche bedeutet',
             '<blockquote>„Sie gibt an, wie viele neue Artikel nach deiner letzten Suchanfrage hochgeladen wurden.“'
             '<cite>Vinted-Hilfe, <a href="{h435}" rel="nofollow noopener">Suchanfragen speichern</a> (gelesen am {read})</cite></blockquote>'
             '<p>Gemeint ist die Zahl mit Pluszeichen neben der gespeicherten Suche. Sie springt jedes Mal auf null, wenn du dir die aktuellen Ergebnisse angeschaut hast. „+12“ heißt also: 12 neue Artikel seit deinem letzten Blick, nicht 12 übrige Artikel und nicht 12 Preissenkungen.</p>'),
            ('benachrichtigungen', 'Was Vinted für gespeicherte Suchen nicht schickt',
             '<p>Die Vinted-Hilfe zu Benachrichtigungen (<a href="{h433}" rel="nofollow noopener">Verwaltung deiner Benachrichtigungen</a>) zählt auf, wann du eine bekommst. Unter anderem, wenn:</p>'
             '<ul><li>ein Mitglied, dem du folgst, einen neuen Artikel hochgeladen hat;</li><li>der Preis eines deiner Favoriten gesenkt wurde;</li><li>einer deiner Favoriten verkauft wurde.</li></ul>'
             '<p>Neue Treffer einer gespeicherten Suche stehen nicht auf dieser Liste. Eine gespeicherte Suche gibt dir den Zähler, den du beim Öffnen des Suchfelds siehst.</p>'
             '<p>Für jeden neuen Artikel, der zu einer Suche passt, brauchst du ein Tool, das die Suche für dich prüft. Alle Wege im Überblick: <a href="{notify}">Vinted-Benachrichtigung für neue Artikel</a>. Für Favoriten: <a href="{pricedrop}">Vinted-Benachrichtigung bei gesenktem Preis</a>.</p>'),
            ('push', 'Eine Push-Nachricht für jeden neuen Artikel',
             '<p>SNYPD prüft dieselbe Suche, die du auf Vinted hast, und schickt für jeden neuen passenden Artikel eine Push-Nachricht auf dein Handy oder deinen Computer:</p>'
             '<ol><li>Öffne die Suche auf Vinted im Browser, mit deinen Filtern (Marke, Größe, Preis, Zustand).</li>'
             '<li>Kopiere die Adresse aus der Adresszeile. Sie enthält <code>/catalog?</code>.</li>'
             '<li>Füge sie in SNYPD ein und schalte die Suche ein.</li>'
             '<li>SNYPD prüft sie etwa alle 30 Sekunden bis eine Minute und schickt einen Push, sobald ein neuer Artikel passt. Die Benachrichtigung öffnet die Anzeige auf Vinted.</li></ol>'
             '<p>So oft schaut SNYPD nach, das ist keine Lieferzeit: Vinted selbst zeigt einen neuen Artikel erst einige Minuten nach dem Einstellen in der Suche. SNYPD meldet sich nie in deinem Vinted-Konto an, kauft nichts und schreibt keinen Verkäufern.</p>'
             '<p>Kostenlos: 1 Suche, rund um die Uhr mit Benachrichtigungen in den ersten @@trial_days@@ Tagen nach deiner ersten Suche in SNYPD, danach nur bei geöffnetem Dashboard. Bezahlte Tarife ab @@price:solo@@ im Monat laufen rund um die Uhr. Auf dem iPhone legst du SNYPD zuerst auf den Home-Bildschirm (nur dort erlaubt Apple Web-Push). Mehr dazu: <a href="{bot}">SNYPD, der Vinted Bot für Benachrichtigungen</a>.</p>'),
        ],
        faq=[
            ('Wie viele Suchen kann ich auf Vinted speichern?',
             'So viele du möchtest. Laut Vinted-Hilfe kannst du beliebig viele Suchen speichern.'),
            ('Warum sind meine gespeicherten Suchen auf Vinted verschwunden?',
             'Laut Vinted-Hilfe werden gespeicherte Suchen entfernt, wenn du sie 6 Monate lang nicht abrufst. Außerdem verschwindet eine Suche, wenn ihr Fähnchen-Icon abgewählt wird. Such einfach noch einmal und speichere die Suche neu.'),
            ('Wo finde ich meine gespeicherte Suche auf Vinted?',
             'Im Suchfeld. Öffne es, dort stehen deine gespeicherten Suchen, jede mit einem Zähler „+N“ für neue Artikel seit deiner letzten Suche.'),
            ('Benachrichtigt mich Vinted über neue Artikel einer gespeicherten Suche?',
             'Die Vinted-Hilfe beschreibt einen Zähler, keine Benachrichtigung: eine Zahl mit Pluszeichen im Suchfeld, die beim Ansehen der Ergebnisse auf null springt. Benachrichtigungen schickt Vinted dagegen für Mitglieder, denen du folgst, und für deine Favoriten. Für einen Push bei jedem neuen Artikel fügst du den Suchlink in ein Tool wie <a href="{bot}">SNYPD</a> ein.'),
        ],
        cta_h='Push für deine Vinted-Suche bekommen'),

    # ---------------------------------------------------------------- NL
    'nl': dict(
        title='Vinted opgeslagen zoekopdrachten: vinden en bewaren | SNYPD',
        desc='Waar je opgeslagen zoekopdrachten op Vinted vindt, hoeveel je kunt bewaren, waarom ze na 6 maanden verdwijnen en wat +N betekent. Volgens de Vinted-hulp.',
        eyebrow='VINTED ZOEKOPDRACHTEN',
        h1='Opgeslagen zoekopdrachten op Vinted: waar ze staan, hoeveel, waarom ze verdwijnen',
        lead='Wat de Vinted-hulp zegt over opgeslagen zoekopdrachten (gelezen op {read}): bewaren, terugvinden, limiet, verdwenen zoekopdrachten en de teller ‘+N’. Plus hoe je een pushmelding krijgt voor elke nieuwe advertentie.',
        answer='Je bewaart een zoekopdracht door in de zoekbalk op het symbool ernaast te klikken; daar vind je hem later ook terug. Je kunt er zoveel bewaren als je wilt. Een zoekopdracht die je 6 maanden lang niet bekijkt, wordt verwijderd. De ‘+N’ ernaast telt de nieuwe artikelen sinds je hem voor het laatst bekeek en gaat terug naar 0 zodra je kijkt. Een melding voor nieuwe resultaten van een opgeslagen zoekopdracht beschrijft de Vinted-hulp niet.',
        toc=[('bewaren', 'Zoekopdracht bewaren'), ('vinden', 'Waar je ze vindt'), ('hoeveel', 'Hoeveel je kunt bewaren'),
             ('verdwenen', 'Waarom ze verdwijnen'), ('teller', 'De teller +N'), ('meldingen', 'Wat Vinted niet stuurt'),
             ('push', 'Push bij elke nieuwe advertentie')],
        sections=[
            ('bewaren', 'Zo bewaar je een zoekopdracht op Vinted',
             '<p>De Vinted-hulp beschrijft twee stappen:</p>'
             '<ol><li>Ga naar de zoekbalk. Daar zie je je laatste zoekopdrachten.</li>'
             '<li>Ga naar de zoekopdracht die je wilt bewaren en klik op het <strong>symbool</strong> ernaast. Nu is hij bewaard.</li></ol>'
             '<p>Wil je een zoekopdracht weer kwijt, klik dan opnieuw op hetzelfde symbool.</p>'),
            ('vinden', 'Waar vind je opgeslagen zoekopdrachten op Vinted?',
             '<p>In de zoekbalk. De Vinted-hulp stuurt je daarheen om een zoekopdracht te bewaren én om hem terug te zien: de volgende keer dat je naar de zoekbalk gaat, zie je bij je bewaarde zoekopdracht een nummer met een plusteken (meer daarover <a href="#teller">hieronder</a>).</p>'),
            ('hoeveel', 'Hoeveel zoekopdrachten kun je op Vinted opslaan?',
             '<p>Zoveel als je wilt. Volgens de Vinted-hulp is er geen maximum.</p>'),
            ('verdwenen', 'Waarom zijn mijn opgeslagen zoekopdrachten verdwenen?',
             '<p>De Vinted-hulp noemt één regel: je zoekopdrachten worden verwijderd als je ze 6 maanden lang niet bekijkt. Verder verdwijnt een zoekopdracht alleen als je dat zelf doet: opnieuw op het symbool klikken verwijdert hem.</p>'
             '<ul><li>Open de zoekopdrachten die je wilt houden af en toe, zodat er geen 6 maanden ongebruikt blijft staan.</li>'
             '<li>Is er een weg, zoek dan opnieuw en bewaar hem weer (stappen <a href="#bewaren">hierboven</a>).</li></ul>'),
            ('teller', 'Wat de ‘+N’ naast een opgeslagen zoekopdracht betekent',
             '<blockquote>“Dit plusteken laat zien hoeveel nieuwe artikelen er zijn geüpload”'
             '<cite>Vinted-hulp, <a href="{h435}" rel="nofollow noopener">Zoekopdrachten opslaan</a> (gelezen op {read})</cite></blockquote>'
             '<p>Het gaat om de nieuwe artikelen sinds de laatste keer dat je die zoekopdracht bekeek. Elke keer dat je de zoekopdracht bekijkt, komt de teller weer op 0. ‘+12’ betekent dus 12 nieuwe advertenties sinds je laatste blik: niet 12 artikelen die over zijn, en niet 12 prijsverlagingen.</p>'),
            ('meldingen', 'Wat Vinted niet stuurt voor opgeslagen zoekopdrachten',
             '<p>De Vinted-hulp over notificaties (<a href="{h433}" rel="nofollow noopener">Notificaties beheren</a>) somt op wanneer je er een krijgt. Onder meer wanneer:</p>'
             '<ul><li>leden die je volgt nieuwe artikelen uploaden;</li><li>een van je favoriete artikelen in prijs is verlaagd;</li><li>een van je favoriete artikelen is verkocht.</li></ul>'
             '<p>Nieuwe resultaten van een opgeslagen zoekopdracht staan niet in dat lijstje. Een opgeslagen zoekopdracht geeft je de teller, die je ziet als je de zoekbalk opent.</p>'
             '<p>Wil je elke nieuwe advertentie die bij een zoekopdracht past, dan heb je een tool nodig die de zoekopdracht voor je controleert. Alle opties naast elkaar: <a href="{notify}">Vinted-melding bij nieuwe artikelen</a>. Voor favorieten: <a href="{pricedrop}">Vinted-melding bij een verlaagde prijs</a>.</p>'),
            ('push', 'Een pushmelding voor elke nieuwe advertentie',
             '<p>SNYPD controleert dezelfde zoekopdracht die je op Vinted hebt en stuurt een pushmelding naar je telefoon of computer voor elke nieuwe advertentie die past:</p>'
             '<ol><li>Open je zoekopdracht op Vinted in je browser, met je filters (merk, maat, prijs, staat).</li>'
             '<li>Kopieer het adres uit de adresbalk. Daar staat <code>/catalog?</code> in.</li>'
             '<li>Plak het in SNYPD en zet de zoekopdracht aan.</li>'
             '<li>SNYPD controleert hem ongeveer elke 30 seconden tot een minuut en stuurt een push zodra een nieuwe advertentie past. De melding opent de advertentie op Vinted.</li></ol>'
             '<p>Zo vaak kijkt SNYPD; het is geen levertijd: Vinted toont een nieuwe advertentie zelf pas een paar minuten na het plaatsen in de zoekresultaten. SNYPD logt nooit in op je Vinted-account, koopt niets en stuurt geen berichten naar verkopers.</p>'
             '<p>Gratis: 1 zoekopdracht, 24/7 met meldingen in de eerste @@trial_days@@ dagen na je eerste zoekopdracht in SNYPD, daarna alleen zolang het dashboard open staat. Betaalde abonnementen vanaf @@price:solo@@ per maand werken 24/7. Op een iPhone zet je SNYPD eerst op je beginscherm (alleen daar staat Apple webpush toe). Meer daarover: <a href="{bot}">SNYPD, de Vinted bot voor meldingen</a>.</p>'),
        ],
        faq=[
            ('Hoeveel zoekopdrachten kun je op Vinted opslaan?',
             'Zoveel als je wilt. Volgens de Vinted-hulp kun je onbeperkt zoekopdrachten bewaren.'),
            ('Waarom zijn mijn opgeslagen zoekopdrachten op Vinted verdwenen?',
             'Volgens de Vinted-hulp worden zoekopdrachten verwijderd als je ze 6 maanden lang niet bekijkt. Ze verdwijnen ook als je opnieuw op het symbool ernaast klikt. Zoek opnieuw en bewaar de zoekopdracht weer via de zoekbalk.'),
            ('Waar vind ik mijn opgeslagen zoekopdrachten op Vinted?',
             'In de zoekbalk. Open hem en je bewaarde zoekopdrachten staan er, elk met een teller ‘+N’ voor nieuwe artikelen sinds je laatste keer kijken.'),
            ('Krijg ik een melding van Vinted bij nieuwe artikelen in een opgeslagen zoekopdracht?',
             'De Vinted-hulp beschrijft een teller, geen melding: een nummer met een plusteken in de zoekbalk, dat terug naar 0 gaat zodra je de zoekopdracht bekijkt. Notificaties stuurt Vinted wel voor leden die je volgt en voor je favorieten. Voor een push bij elke nieuwe advertentie plak je de zoeklink in een tool zoals <a href="{bot}">SNYPD</a>.'),
        ],
        cta_h='Krijg een push voor je Vinted-zoekopdracht'),

    # ---------------------------------------------------------------- IT
    'it': dict(
        title='Vinted ricerche salvate: dove sono e quante (2026) | SNYPD',
        desc='Dove trovi le ricerche salvate su Vinted, quante puoi salvarne, perché dopo 6 mesi non si vedono più e cosa significa +N. Dal centro assistenza di Vinted.',
        eyebrow='RICERCHE SALVATE VINTED',
        h1='Ricerche salvate su Vinted: dove sono, quante, perché spariscono',
        lead='Cosa dice il centro assistenza di Vinted sulle ricerche salvate (letto il {read}): salvarle, ritrovarle, il limite, perché spariscono e il contatore «+N». In più, come ricevere un push per ogni nuovo annuncio.',
        answer='Salvi una ricerca selezionando l’icona «Salva» accanto a lei nella barra di ricerca, e lì la ritrovi. Puoi salvarne un numero illimitato. Una ricerca salvata che non visualizzi mai per 6 mesi non è più visibile. Il «+N» accanto conta i nuovi articoli caricati dall’ultima volta che l’hai controllata e si azzera quando la visualizzi. L’assistenza Vinted non descrive nessuna notifica per i nuovi risultati di una ricerca salvata.',
        toc=[('salvare', 'Salvare una ricerca'), ('dove', 'Dove trovarle'), ('quante', 'Quante salvarne'),
             ('sparite', 'Perché spariscono'), ('contatore', 'Il contatore +N'), ('notifiche', 'Cosa Vinted non invia'),
             ('push', 'Un push per ogni annuncio')],
        sections=[
            ('salvare', 'Come salvare una ricerca su Vinted',
             '<p>L’assistenza Vinted descrive due passaggi:</p>'
             '<ol><li>Vai sulla barra di ricerca. Lì vedi le ricerche che hai fatto di recente.</li>'
             '<li>Vai sulla ricerca che vuoi tenere e seleziona l’icona <strong>Salva</strong> accanto.</li></ol>'
             '<p>Per togliere una ricerca salvata, basta deselezionare la stessa icona.</p>'),
            ('dove', 'Dove sono le ricerche salvate su Vinted?',
             '<p>Nella barra di ricerca. L’assistenza Vinted ti manda lì sia per salvare una ricerca sia per ritrovarla: la prossima volta che vai sulla barra di ricerca, la ricerca salvata mostra un numero con il segno più (dettagli <a href="#contatore">più sotto</a>).</p>'),
            ('quante', 'Quante ricerche puoi salvare su Vinted?',
             '<p>Quante vuoi. Secondo l’assistenza Vinted puoi salvare un numero illimitato di ricerche.</p>'),
            ('sparite', 'Perché le mie ricerche salvate su Vinted sono sparite?',
             '<p>L’assistenza Vinted indica una regola: le ricerche salvate non sono più visibili dopo 6 mesi, se nel frattempo non le hai mai visualizzate. Per il resto una ricerca sparisce solo a mano: deselezionare la sua icona «Salva» la rimuove.</p>'
             '<ul><li>Apri ogni tanto le ricerche che vuoi tenere, così nessuna resta 6 mesi senza essere visualizzata.</li>'
             '<li>Se una è sparita, rifai la ricerca e salvala di nuovo (passaggi <a href="#salvare">sopra</a>).</li></ul>'),
            ('contatore', 'Cosa significa il «+N» accanto a una ricerca salvata',
             '<blockquote>«un numero con il segno più, che indica quanti nuovi articoli sono stati caricati»'
             '<cite>Assistenza Vinted, <a href="{h435}" rel="nofollow noopener">Salvare le ricerche</a> (letto il {read})</cite></blockquote>'
             '<p>Il numero conta i nuovi articoli caricati dall’ultima volta che hai controllato quella ricerca. Ogni volta che la visualizzi, il contatore viene reimpostato. Quindi «+12» vuol dire 12 nuovi annunci dal tuo ultimo sguardo: non 12 articoli rimasti, né 12 ribassi di prezzo.</p>'),
            ('notifiche', 'Cosa Vinted non invia per le ricerche salvate',
             '<p>L’assistenza Vinted sulle notifiche (<a href="{h433}" rel="nofollow noopener">Gestione delle notifiche</a>) elenca quando puoi riceverne una. Tra gli altri casi:</p>'
             '<ul><li>gli utenti che segui caricano nuovi articoli;</li><li>il prezzo di un articolo che hai aggiunto ai Preferiti è sceso;</li><li>un articolo nei tuoi Preferiti è stato venduto.</li></ul>'
             '<p>I nuovi risultati di una ricerca salvata non sono in quell’elenco. Una ricerca salvata ti dà il contatore, che vedi quando apri la barra di ricerca.</p>'
             '<p>Per ogni nuovo annuncio che corrisponde a una ricerca ti serve uno strumento che controlli la ricerca al posto tuo. Tutte le opzioni a confronto: <a href="{notify}">notifiche Vinted per nuovi annunci</a>.</p>'),
            ('push', 'Se vuoi un push per ogni nuovo annuncio',
             '<p>SNYPD controlla la stessa ricerca che hai su Vinted e invia una notifica push al telefono o al computer per ogni nuovo annuncio che corrisponde:</p>'
             '<ol><li>Apri la ricerca su Vinted nel browser, con i tuoi filtri (marca, taglia, prezzo, condizioni).</li>'
             '<li>Copia l’indirizzo dalla barra del browser. Contiene <code>/catalog?</code>.</li>'
             '<li>Incollalo in SNYPD e attiva la ricerca.</li>'
             '<li>SNYPD la controlla circa ogni 30 secondi fino a un minuto e invia un push quando un nuovo annuncio corrisponde. La notifica apre l’annuncio su Vinted.</li></ol>'
             '<p>È la frequenza con cui SNYPD guarda, non un tempo di consegna: Vinted stesso mostra un nuovo annuncio nella ricerca qualche minuto dopo la pubblicazione. SNYPD non accede mai al tuo account Vinted, non compra nulla e non scrive ai venditori.</p>'
             '<p>Gratis: 1 ricerca, 24 ore su 24 con notifiche nei primi @@trial_days@@ giorni dopo la tua prima ricerca in SNYPD, poi solo mentre la dashboard è aperta. I piani a pagamento da @@price:solo@@ al mese funzionano 24 ore su 24. Su iPhone aggiungi prima SNYPD alla schermata Home (Apple consente le notifiche web solo lì). Per saperne di più: <a href="{bot}">SNYPD, il bot Vinted per le notifiche</a>.</p>'),
        ],
        faq=[
            ('Quante ricerche si possono salvare su Vinted?',
             'Quante vuoi. Secondo l’assistenza Vinted puoi salvare un numero illimitato di ricerche.'),
            ('Perché le mie ricerche salvate su Vinted sono sparite?',
             'Secondo l’assistenza Vinted, le ricerche salvate non sono più visibili dopo 6 mesi se nel frattempo non le hai mai visualizzate. Spariscono anche se deselezioni l’icona «Salva» accanto. Per riaverla, rifai la ricerca e salvala dalla barra di ricerca.'),
            ('Dove trovo la mia ricerca salvata su Vinted?',
             'Nella barra di ricerca. Aprila e trovi le ricerche salvate, ognuna con un contatore «+N» dei nuovi articoli dall’ultima volta che l’hai controllata.'),
            ('Vinted mi avvisa dei nuovi articoli di una ricerca salvata?',
             'L’assistenza descrive un contatore, non una notifica: un numero con il segno più nella barra di ricerca, che si azzera ogni volta che visualizzi la ricerca. Vinted invia invece notifiche per gli utenti che segui e per gli articoli nei tuoi Preferiti. Per un push a ogni nuovo annuncio, incolla il link della ricerca in uno strumento come <a href="{bot}">SNYPD</a>.'),
        ],
        cta_h='Ricevi un push per la tua ricerca Vinted'),

    # ---------------------------------------------------------------- ES
    'es': dict(
        title='Vinted búsquedas guardadas: dónde están (2026) | SNYPD',
        desc='Dónde encontrar tus búsquedas guardadas en Vinted, cuántas puedes guardar, por qué desaparecen a los 6 meses y qué significa +N. Según la ayuda de Vinted.',
        eyebrow='BÚSQUEDAS GUARDADAS VINTED',
        h1='Búsquedas guardadas en Vinted: dónde están, cuántas, por qué desaparecen',
        lead='Lo que dice el centro de ayuda de Vinted sobre las búsquedas guardadas (leído el {read}): guardarlas, encontrarlas, el límite, por qué desaparecen y el contador «+N». Además, cómo recibir un push por cada anuncio nuevo.',
        answer='Guardas una búsqueda pulsando el icono «Guardar» junto a ella en la barra de búsqueda, y ahí la vuelves a encontrar. Puedes guardar un número ilimitado. Una búsqueda guardada desaparece a los 6 meses si no la consultas en ese tiempo. El «+N» de al lado cuenta los artículos nuevos subidos desde la última vez que hiciste esa búsqueda y se reinicia cuando la abres. La ayuda de Vinted no describe ninguna notificación para los resultados nuevos de una búsqueda guardada.',
        toc=[('guardar', 'Guardar una búsqueda'), ('donde', 'Dónde encontrarlas'), ('cuantas', 'Cuántas puedes guardar'),
             ('desaparecen', 'Por qué desaparecen'), ('contador', 'El contador +N'), ('notificaciones', 'Lo que Vinted no envía'),
             ('push', 'Un push por anuncio nuevo')],
        sections=[
            ('guardar', 'Cómo guardar una búsqueda en Vinted',
             '<p>La ayuda de Vinted describe dos pasos:</p>'
             '<ol><li>Ve a la barra de búsqueda para ver tus búsquedas previas.</li>'
             '<li>Elige la búsqueda que quieres conservar y pulsa el icono <strong>Guardar</strong> que aparece junto a ella.</li></ol>'
             '<p>Para eliminar una búsqueda guardada, vuelve a pulsar ese mismo icono.</p>'),
            ('donde', '¿Dónde están las búsquedas guardadas en Vinted?',
             '<p>En la barra de búsqueda. La ayuda de Vinted te lleva ahí tanto para guardar una búsqueda como para volver a ella: la próxima vez que abras la barra de búsqueda, la búsqueda guardada muestra un número con el signo «+» (más detalles <a href="#contador">abajo</a>).</p>'),
            ('cuantas', '¿Cuántas búsquedas puedes guardar en Vinted?',
             '<p>Las que quieras. Según la ayuda de Vinted, puedes guardar un número ilimitado de búsquedas.</p>'),
            ('desaparecen', '¿Por qué han desaparecido mis búsquedas guardadas?',
             '<p>La ayuda de Vinted da una regla: las búsquedas guardadas desaparecen a los 6 meses si no las has consultado en ese tiempo. Por lo demás, una búsqueda solo se va a mano: volver a pulsar su icono «Guardar» la elimina.</p>'
             '<ul><li>Abre de vez en cuando las búsquedas que quieres conservar, para que ninguna pase 6 meses sin consultarse.</li>'
             '<li>Si una ha desaparecido, repite la búsqueda y guárdala otra vez (pasos <a href="#guardar">arriba</a>).</li></ul>'),
            ('contador', 'Qué significa el «+N» junto a una búsqueda guardada',
             '<blockquote>«un número con el signo de “+”; esto indica cuántos artículos nuevos se han subido»'
             '<cite>Ayuda de Vinted, <a href="{h435}" rel="nofollow noopener">Guardar tus búsquedas</a> (leído el {read})</cite></blockquote>'
             '<p>El número cuenta los artículos nuevos subidos desde la última vez que hiciste esa búsqueda. Cada vez que abres la búsqueda, el contador se reinicia. Así que «+12» quiere decir 12 anuncios nuevos desde tu última mirada: no 12 artículos que quedan, ni 12 bajadas de precio.</p>'),
            ('notificaciones', 'Lo que Vinted no envía para las búsquedas guardadas',
             '<p>La ayuda de Vinted sobre notificaciones (<a href="{h433}" rel="nofollow noopener">Cómo gestionar tus notificaciones</a>) enumera cuándo puedes recibir una. Entre otras situaciones:</p>'
             '<ul><li>un miembro al que sigues anuncia un artículo nuevo;</li><li>se reduce el precio de un artículo que has marcado como favorito;</li><li>se vende un artículo que has marcado como favorito.</li></ul>'
             '<p>Los resultados nuevos de una búsqueda guardada no están en esa lista. Una búsqueda guardada te da el contador, que ves al abrir la barra de búsqueda.</p>'
             '<p>Para cada anuncio nuevo que coincide con una búsqueda, necesitas una herramienta que revise la búsqueda por ti. Todas las opciones lado a lado: <a href="{notify}">alertas de Vinted para anuncios nuevos</a>.</p>'),
            ('push', 'Si quieres un push por cada anuncio nuevo',
             '<p>SNYPD vigila la misma búsqueda que tienes en Vinted y envía una notificación push a tu móvil u ordenador por cada anuncio nuevo que coincide:</p>'
             '<ol><li>Abre tu búsqueda en Vinted en el navegador, con tus filtros (marca, talla, precio, estado).</li>'
             '<li>Copia la dirección de la barra del navegador. Contiene <code>/catalog?</code>.</li>'
             '<li>Pégala en SNYPD y activa la búsqueda.</li>'
             '<li>SNYPD la revisa aproximadamente cada 30 segundos a un minuto y envía un push cuando un anuncio nuevo coincide. El aviso abre el anuncio en Vinted.</li></ol>'
             '<p>Es la frecuencia con la que SNYPD mira, no un tiempo de entrega: el propio Vinted muestra un anuncio nuevo en su búsqueda unos minutos después de publicarse. SNYPD nunca inicia sesión en tu cuenta de Vinted, no compra nada y no escribe a los vendedores.</p>'
             '<p>Gratis: 1 búsqueda, 24/7 con avisos durante los primeros @@trial_days@@ días tras tu primera búsqueda en SNYPD, y después solo mientras el panel esté abierto. Los planes de pago desde @@price:solo@@ al mes funcionan 24/7. En iPhone, añade primero SNYPD a la pantalla de inicio (Apple solo permite notificaciones web ahí). Más información: <a href="{bot}">SNYPD, el bot de Vinted para alertas</a>.</p>'),
        ],
        faq=[
            ('¿Cuántas búsquedas se pueden guardar en Vinted?',
             'Las que quieras. Según la ayuda de Vinted, puedes guardar un número ilimitado de búsquedas.'),
            ('¿Por qué han desaparecido mis búsquedas guardadas en Vinted?',
             'Según la ayuda de Vinted, las búsquedas guardadas desaparecen a los 6 meses si no las has consultado en ese tiempo. También se eliminan si vuelves a pulsar el icono «Guardar». Para recuperarla, repite la búsqueda y guárdala desde la barra de búsqueda.'),
            ('¿Dónde encuentro mis búsquedas guardadas en Vinted?',
             'En la barra de búsqueda. Ábrela y ahí están tus búsquedas guardadas, cada una con un contador «+N» de artículos nuevos desde la última vez que la hiciste.'),
            ('¿Vinted me avisa de los artículos nuevos de una búsqueda guardada?',
             'Su ayuda describe un contador, no una notificación: un número con el signo «+» en la barra de búsqueda, que se reinicia cada vez que abres la búsqueda. Vinted sí envía notificaciones por los miembros a los que sigues y por tus favoritos. Para un push por cada anuncio nuevo, pega el enlace de la búsqueda en una herramienta como <a href="{bot}">SNYPD</a>.'),
        ],
        cta_h='Recibe un push para tu búsqueda de Vinted'),

    # ---------------------------------------------------------------- PL
    'pl': dict(
        title='Vinted zapisane wyszukiwania: gdzie są (2026) | SNYPD',
        desc='Gdzie są zapisane wyszukiwania na Vinted, ile możesz ich mieć, dlaczego znikają po 6 miesiącach i co oznacza +N. Na podstawie centrum pomocy Vinted.',
        eyebrow='ZAPISANE WYSZUKIWANIA VINTED',
        h1='Zapisane wyszukiwania na Vinted: gdzie są, ile ich może być, dlaczego znikają',
        lead='Co centrum pomocy Vinted mówi o zapisanych wyszukiwaniach (stan na {read}): zapisywanie, gdzie je znaleźć, limit, znikanie i licznik „+N”. Do tego: jak dostać push o każdym nowym ogłoszeniu.',
        answer='Wyszukiwanie zapisujesz, klikając ikonę zapisu obok niego w pasku wyszukiwania; tam też je potem znajdziesz. Możesz zapisać nieograniczoną liczbę wyszukiwań. Zapisane wyszukiwanie znika po 6 miesiącach, jeśli ani razu go nie otworzysz. „+N” obok niego liczy nowe przedmioty od twojego ostatniego wyszukiwania i zeruje się, gdy obejrzysz wyniki. Pomoc Vinted nie opisuje powiadomienia o nowych wynikach zapisanego wyszukiwania.',
        toc=[('zapisz', 'Jak zapisać wyszukiwanie'), ('gdzie', 'Gdzie je znaleźć'), ('ile', 'Ile można zapisać'),
             ('zniknely', 'Dlaczego znikają'), ('licznik', 'Licznik +N'), ('powiadomienia', 'Czego Vinted nie wysyła'),
             ('push', 'Push o każdym ogłoszeniu')],
        sections=[
            ('zapisz', 'Jak zapisać wyszukiwanie na Vinted',
             '<p>Centrum pomocy Vinted opisuje dwa kroki:</p>'
             '<ol><li>Przejdź do paska wyszukiwania. Znajdziesz tam frazy, których ostatnio szukałeś.</li>'
             '<li>Najedź na frazę, którą chcesz zachować, i kliknij <strong>ikonę zapisu</strong> po jej prawej stronie.</li></ol>'
             '<p>Żeby usunąć zapisane wyszukiwanie, wystarczy odznaczyć tę samą ikonę.</p>'),
            ('gdzie', 'Gdzie są zapisane wyszukiwania na Vinted?',
             '<p>W pasku wyszukiwania. Pomoc Vinted kieruje cię tam zarówno po to, żeby zapisać wyszukiwanie, jak i żeby do niego wrócić: następnym razem po kliknięciu paska wyszukiwania zapisane wyszukiwanie pokazuje liczbę poprzedzoną plusem (więcej <a href="#licznik">niżej</a>).</p>'),
            ('ile', 'Ile wyszukiwań można zapisać na Vinted?',
             '<p>Ile chcesz. Według pomocy Vinted możesz zapisać nieograniczoną liczbę wyszukiwań.</p>'),
            ('zniknely', 'Dlaczego zniknęły moje zapisane wyszukiwania?',
             '<p>Pomoc Vinted podaje jedną zasadę: zapisane wyszukiwania znikają po upływie 6 miesięcy, jeśli ani razu ich nie otworzysz. Poza tym wyszukiwanie znika tylko wtedy, gdy sam je usuniesz: odznaczenie ikony zapisu je kasuje.</p>'
             '<ul><li>Otwieraj od czasu do czasu wyszukiwania, które chcesz zachować, żeby żadne nie leżało 6 miesięcy nieotwarte.</li>'
             '<li>Jeśli któreś zniknęło, wyszukaj jeszcze raz i zapisz ponownie (kroki <a href="#zapisz">wyżej</a>).</li></ul>'),
            ('licznik', 'Co oznacza „+N” obok zapisanego wyszukiwania',
             '<blockquote>„liczbę poprzedzoną plusem, która wskaże, ile nowych przedmiotów z tej kategorii dodano”'
             '<cite>Pomoc Vinted, <a href="{h435}" rel="nofollow noopener">Jak zapisać wyszukiwanie</a> (stan na {read})</cite></blockquote>'
             '<p>Liczba pokazuje nowe przedmioty dodane od twojego ostatniego wyszukiwania. Licznik zeruje się za każdym razem, gdy obejrzysz wyniki. „+12” oznacza więc 12 nowych ogłoszeń od ostatniego spojrzenia: nie 12 pozostałych przedmiotów i nie 12 obniżek cen.</p>'),
            ('powiadomienia', 'Czego Vinted nie wysyła przy zapisanych wyszukiwaniach',
             '<p>Pomoc Vinted o powiadomieniach (<a href="{h433}" rel="nofollow noopener">Jak zarządzać powiadomieniami</a>) wymienia, kiedy możesz je dostać. Między innymi gdy:</p>'
             '<ul><li>użytkownicy, których obserwujesz, dodadzą nowe ogłoszenia;</li><li>cena polubionego przez ciebie przedmiotu zostanie obniżona;</li><li>polubiony przez ciebie przedmiot zostanie sprzedany.</li></ul>'
             '<p>Nowych wyników zapisanego wyszukiwania nie ma na tej liście. Zapisane wyszukiwanie daje ci licznik, który widzisz po otwarciu paska wyszukiwania.</p>'
             '<p>Żeby wiedzieć o każdym nowym ogłoszeniu pasującym do wyszukiwania, potrzebujesz narzędzia, które sprawdza wyszukiwanie za ciebie. Wszystkie sposoby obok siebie: <a href="{notify}">powiadomienia Vinted o nowych ogłoszeniach</a>.</p>'),
            ('push', 'Jeśli chcesz push o każdym nowym ogłoszeniu',
             '<p>SNYPD pilnuje tego samego wyszukiwania, które masz na Vinted, i wysyła powiadomienie push na telefon albo komputer o każdym nowym pasującym ogłoszeniu. Tak tworzysz taki alert:</p>'
             '<ol><li>Otwórz wyszukiwanie na Vinted w przeglądarce, z filtrami (marka, rozmiar, cena, stan).</li>'
             '<li>Skopiuj adres z paska przeglądarki. Zawiera <code>/catalog?</code>.</li>'
             '<li>Wklej go do SNYPD i włącz wyszukiwanie.</li>'
             '<li>SNYPD sprawdza je mniej więcej co 30 sekund do minuty i wysyła push, gdy pojawi się nowe pasujące ogłoszenie. Powiadomienie otwiera ogłoszenie na Vinted.</li></ol>'
             '<p>To częstotliwość sprawdzania, a nie czas dostarczenia: sam Vinted pokazuje nowe ogłoszenie w wyszukiwarce kilka minut po jego dodaniu. SNYPD nigdy nie loguje się na twoje konto Vinted, niczego nie kupuje i nie pisze do sprzedających.</p>'
             '<p>Za darmo: 1 wyszukiwanie, 24/7 z powiadomieniami przez pierwsze @@trial_days@@ dni od pierwszego wyszukiwania w SNYPD, potem tylko przy otwartym panelu. Plany płatne od @@price:solo@@ miesięcznie działają 24/7. Na iPhonie najpierw dodaj SNYPD do ekranu początkowego (tylko tam Apple pozwala na powiadomienia web). Więcej: <a href="{bot}">SNYPD, bot Vinted do powiadomień</a>.</p>'),
        ],
        faq=[
            ('Ile wyszukiwań można zapisać na Vinted?',
             'Ile chcesz. Według pomocy Vinted możesz zapisać nieograniczoną liczbę wyszukiwań.'),
            ('Dlaczego zniknęły moje zapisane wyszukiwania na Vinted?',
             'Według pomocy Vinted zapisane wyszukiwania znikają po upływie 6 miesięcy, jeśli ani razu ich nie otworzysz. Znikają też po odznaczeniu ikony zapisu. Żeby je odzyskać, wyszukaj jeszcze raz i zapisz w pasku wyszukiwania.'),
            ('Gdzie znaleźć zapisane wyszukiwania na Vinted?',
             'W pasku wyszukiwania. Otwórz go, a zobaczysz zapisane wyszukiwania, każde z licznikiem „+N” nowych przedmiotów od twojego ostatniego wyszukiwania.'),
            ('Czy Vinted powiadamia o nowych przedmiotach z zapisanego wyszukiwania?',
             'Pomoc Vinted opisuje licznik, a nie powiadomienie: liczbę z plusem w pasku wyszukiwania, która zeruje się, gdy obejrzysz wyniki. Powiadomienia Vinted wysyła natomiast o obserwowanych użytkownikach i polubionych przedmiotach. Żeby dostać push o każdym nowym ogłoszeniu, wklej link do wyszukiwania do narzędzia takiego jak <a href="{bot}">SNYPD</a>.'),
        ],
        cta_h='Dostań push o swoim wyszukiwaniu na Vinted'),

    # ---------------------------------------------------------------- SV
    'sv': dict(
        title='Vinted sparade sökningar och bevakning (2026) | SNYPD',
        desc='Var du hittar sparade sökningar på Vinted, hur många du kan spara, varför de försvinner efter sex månader och vad +N betyder. Enligt Vinteds hjälpcenter.',
        eyebrow='SPARADE SÖKNINGAR PÅ VINTED',
        h1='Sparade sökningar på Vinted: var de finns, hur många, varför de försvinner',
        lead='Vad Vinteds hjälpcenter säger om sparade sökningar (läst {read}): spara, hitta, gräns, försvunna sökningar och räknaren ”+N”. Plus hur du skapar en bevakning med en push för varje ny annons.',
        answer='Du sparar en sökning genom att trycka på ”Spara”-ikonen bredvid den i sökfältet, och där hittar du den igen. Du kan spara ett obegränsat antal. En sparad sökning som du aldrig öppnar försvinner efter sex månader. ”+N” bredvid den räknar nya artiklar sedan du senast kontrollerade sökningen och återställs när du visar den. Vinteds hjälp beskriver ingen notis för nya träffar i en sparad sökning.',
        toc=[('spara', 'Spara en sökning'), ('hitta', 'Var du hittar dem'), ('hur-manga', 'Hur många du kan spara'),
             ('forsvunna', 'Varför de försvinner'), ('raknare', 'Räknaren +N'), ('notiser', 'Vad Vinted inte skickar'),
             ('bevakning', 'Bevakning med push')],
        sections=[
            ('spara', 'Så sparar du en sökning på Vinted',
             '<p>Vinteds hjälpcenter beskriver två steg:</p>'
             '<ol><li>Gå till sökfältet. Där ser du sökningarna du nyligen har gjort.</li>'
             '<li>Dra musen över sökbegreppet du vill behålla och tryck på <strong>Spara</strong>-ikonen bredvid det.</li></ol>'
             '<p>Vill du ta bort en sparad sökning avmarkerar du samma ikon.</p>'),
            ('hitta', 'Var finns sparade sökningar på Vinted?',
             '<p>I sökfältet. Vinteds hjälp skickar dig dit både för att spara en sökning och för att komma tillbaka till den: nästa gång du besöker sökfältet visar den sparade sökningen ett nummer med ett plustecken (mer om det <a href="#raknare">längre ner</a>).</p>'),
            ('hur-manga', 'Hur många sökningar kan du spara på Vinted?',
             '<p>Så många du vill. Enligt Vinteds hjälp kan du spara ett obegränsat antal sökningar.</p>'),
            ('forsvunna', 'Varför har mina sparade sökningar försvunnit?',
             '<p>Vinteds hjälp anger en regel: dina sparade sökningar försvinner efter sex månader om du aldrig öppnar dem. Annars försvinner en sökning bara om du tar bort den själv: att avmarkera ”Spara”-ikonen tar bort den.</p>'
             '<ul><li>Öppna de sökningar du vill behålla då och då, så att ingen blir liggande oöppnad i sex månader.</li>'
             '<li>Har en försvunnit, gör sökningen igen och spara den på nytt (stegen <a href="#spara">ovan</a>).</li></ul>'),
            ('raknare', 'Vad ”+N” bredvid en sparad sökning betyder',
             '<blockquote>”ett nummer med ett plustecken som anger hur många nya artiklar som annonserats”'
             '<cite>Vinteds hjälp, <a href="{h435}" rel="nofollow noopener">Spara dina sökningar</a> (läst {read})</cite></blockquote>'
             '<p>Numret räknar de nya artiklarna sedan du senast kontrollerade sökningen. Varje gång du visar sökningen återställs räknaren. ”+12” betyder alltså 12 nya annonser sedan du tittade sist: inte 12 artiklar kvar, och inte 12 prissänkningar.</p>'),
            ('notiser', 'Vad Vinted inte skickar för sparade sökningar',
             '<p>Vinteds hjälp om notiser (<a href="{h433}" rel="nofollow noopener">Hantera dina notifikationer</a>) räknar upp när du kan få en. Bland annat när:</p>'
             '<ul><li>medlemmar du följer laddar upp nya artiklar;</li><li>priset på en artikel du har favoritmarkerat har sänkts;</li><li>artikeln du favoritmarkerade såldes.</li></ul>'
             '<p>Nya träffar i en sparad sökning finns inte med i den listan. En sparad sökning ger dig räknaren, som du ser när du öppnar sökfältet.</p>'
             '<p>Vill du veta om varje ny annons som matchar en sökning behöver du ett verktyg som kontrollerar sökningen åt dig. Alla sätt sida vid sida: <a href="{notify}">Vinted bevakning av nya annonser</a>.</p>'),
            ('bevakning', 'Skapa en bevakning med push för varje ny annons',
             '<p>SNYPD bevakar samma sökning som du har på Vinted och skickar en pushnotis till mobilen eller datorn för varje ny annons som matchar:</p>'
             '<ol><li>Öppna sökningen på Vinted i webbläsaren, med dina filter (märke, storlek, pris, skick).</li>'
             '<li>Kopiera adressen i adressfältet. Den innehåller <code>/catalog?</code>.</li>'
             '<li>Klistra in den i SNYPD och slå på sökningen.</li>'
             '<li>SNYPD kontrollerar den ungefär var 30:e sekund till en gång i minuten och skickar en push när en ny annons matchar. Notisen öppnar annonsen på Vinted.</li></ol>'
             '<p>Så ofta tittar SNYPD, det är ingen leveranstid: Vinted visar själv en ny annons i sökningen några minuter efter att den lagts upp. SNYPD loggar aldrig in på ditt Vinted-konto, köper ingenting och skriver inte till säljare.</p>'
             '<p>Gratis: 1 sökning, dygnet runt med notiser de första @@trial_days@@ dagarna efter din första sökning i SNYPD, sedan bara medan panelen är öppen. Betalda abonnemang från @@price:solo@@ i månaden körs dygnet runt. På iPhone lägger du först till SNYPD på hemskärmen (bara där tillåter Apple webbnotiser). Mer: <a href="{bot}">SNYPD, Vinted boten för bevakning</a>.</p>'),
        ],
        faq=[
            ('Hur många sökningar kan man spara på Vinted?',
             'Så många du vill. Enligt Vinteds hjälp kan du spara ett obegränsat antal sökningar.'),
            ('Varför har mina sparade sökningar på Vinted försvunnit?',
             'Enligt Vinteds hjälp försvinner sparade sökningar efter sex månader om du aldrig öppnar dem. De försvinner också om ”Spara”-ikonen avmarkeras. Gör sökningen igen och spara den från sökfältet för att få tillbaka den.'),
            ('Var hittar jag mina sparade sökningar på Vinted?',
             'I sökfältet. Öppna det, så finns dina sparade sökningar där, var och en med en räknare ”+N” för nya artiklar sedan du senast kontrollerade.'),
            ('Hur skapar jag en bevakning på Vinted?',
             'Vinteds hjälp beskriver sparade sökningar med en räknare i sökfältet, inte en notis för varje ny träff. Notiser skickar Vinted däremot för medlemmar du följer och för favoritmarkerade artiklar. För en push vid varje ny annons klistrar du in söklänken i ett verktyg som <a href="{bot}">SNYPD</a>.'),
        ],
        cta_h='Få en push för din Vinted-sökning'),
  },

  # ======================================================================== PRICE DROP
  'pricedrop': {
    'slugs': {'en': '/vinted-price-drop-notifications', 'fr': '/fr/vinted-notification-baisse-de-prix',
              'de': '/de/vinted-preis-gesenkt-benachrichtigung', 'nl': '/nl/vinted-melding-prijs-verlaagd'},

    # ---------------------------------------------------------------- EN
    'en': dict(
        title='Vinted price drop alerts: notifications for favourites | SNYPD',
        desc='Does Vinted notify you when a price drops? Learn how alerts for favourites work, which settings to check, and how new-listing alerts differ.',
        eyebrow='VINTED PRICE DROPS',
        h1='Does Vinted tell you when a price drops?',
        lead='Yes, for items you have favourited. Here is what Vinted’s help centre says (read {read}), what it does not cover, and how to hear about new listings under the price you want to pay.',
        answer='Yes, but only for your favourites. Vinted’s help centre lists a notification when the price of an item you favourited is reduced, and another when an item you favourited is sold. It describes no notification for price changes on items you have not favourited. And a lower price a seller offers you in a conversation is visible only to you, not on the listing.',
        toc=[('favourites', 'How it works'), ('not-covered', 'What it does not cover'), ('snypd', 'Alerts under your price'),
             ('which', 'Which to use')],
        sections=[
            ('favourites', 'How Vinted’s price drop notification works',
             '<blockquote>“The price of the item you’ve favourited was reduced”'
             '<cite>Vinted help, <a href="{h433}" rel="nofollow noopener">Managing your notifications</a> (read {read})</cite></blockquote>'
             '<p>That line is one of the cases in which Vinted’s help says you may get a notification. The same list includes an item you favourited being sold, and members you follow listing new items. So to be told when one item gets cheaper, add it to your favourites.</p>'
             '<p>Notifications land in your Vinted inbox. Which ones also pop up as push notifications outside the app you choose in your profile under <strong>Settings &gt; Push notifications</strong>; there you can also set a daily limit for notifications that are not high priority. If they don’t arrive at all, see <a href="{notwork}">Vinted notifications not working</a>.</p>'),
            ('not-covered', 'What Vinted’s price drop notification does not cover',
             '<ul><li><strong>Items you have not favourited.</strong> The help centre lists price drops only for favourites, so another listing getting cheaper sends you nothing.</li>'
             '<li><strong>New listings.</strong> A new item that is already cheap is not a price drop. A saved search only shows a “+N” counter of new items in the search bar (<a href="{saved}">Vinted saved searches</a>).</li>'
             '<li><strong>Offers.</strong> Per Vinted’s help on <a href="{h258}" rel="nofollow noopener">making an offer</a>, a seller can offer you a lower price in a conversation, up to 40% below the original. The new price is visible only to you; other buyers still see the original, and they can still buy until you press Buy now. So the price on a listing is not always the price paid (<a href="{sold}">what you can see about sold items</a>).</li></ul>'),
            ('snypd', 'Alerts for new listings under your price',
             '<p>To be clear first: SNYPD does not track price drops. It does not watch listings that are already online, so a listing that gets cheaper does not trigger a SNYPD alert.</p>'
             '<p>What it does: it watches a Vinted search for new listings, and a Vinted search can carry a maximum price. So for “Nike Dunk Low under €40”:</p>'
             '<ol><li>Search for the item on Vinted in a browser and set the maximum of the price filter to 40, plus size and condition if you like.</li>'
             '<li>Copy the address from the address bar. It contains <code>/catalog?</code> and the price you set (<code>price_to=40</code>).</li>'
             '<li>Paste it into SNYPD and switch the search on.</li>'
             '<li>SNYPD checks the search about every 30 seconds to a minute and sends a push to your phone or computer for each new listing that matches, price included.</li></ol>'
             '<p>About every 30 seconds to a minute is how often SNYPD looks, not how fast a listing reaches you: Vinted itself shows a new listing in search a few minutes after it is posted. SNYPD never logs in to your Vinted account, never buys and never messages sellers. Free: 1 search, 24/7 with alerts for the first @@trial_days@@ days after you save your first search in SNYPD, then only while the dashboard is open; paid plans from @@price:solo@@ per month run 24/7. More: <a href="{bot}">SNYPD, the Vinted bot for alerts</a>.</p>'),
            ('which', 'Which one to use',
             '<ul><li><strong>One item you are waiting on:</strong> favourite it. Vinted tells you when its price is reduced or when it sells.</li>'
             '<li><strong>Any new listing of a model under your price:</strong> a Vinted search with a maximum price, watched by SNYPD.</li>'
             '<li>The two work side by side: favourites for what is already listed, a search for what gets listed next.</li></ul>'),
        ],
        faq=[
            ('Does Vinted notify you when a price drops?',
             'Yes, for items you have favourited. Vinted’s help centre lists a notification when the price of an item you favourited is reduced, and another when it is sold.'),
            ('Do I get a notification if an item I have not favourited drops in price?',
             'Vinted’s help centre describes none. Its price drop notification is for favourites, so add the item to your favourites if you want to hear about it.'),
            ('Does SNYPD track price drops on Vinted?',
             'No. SNYPD alerts you to new listings that match your Vinted search, including a maximum price you set. It does not watch prices of listings that are already online.'),
            ('Can other buyers see the lower price a seller offered me?',
             'No. According to Vinted’s help, a lower price a seller sends in a conversation is visible only to that buyer; everyone else still sees the original price.'),
        ],
        cta_h='Get alerts for new listings under your price'),

    # ---------------------------------------------------------------- FR
    'fr': dict(
        title='Vinted notification baisse de prix\xa0: comment ça marche | SNYPD',
        desc='Vinted te prévient quand le prix d’un article de tes favoris baisse ou quand il est vendu. Ce que ça ne couvre pas, et comment être alerté sous ton prix.',
        eyebrow='BAISSES DE PRIX VINTED',
        h1='Vinted te prévient-il quand un prix baisse\xa0?',
        lead='Oui, pour les articles de tes favoris. Voici ce que dit le centre d’aide de Vinted (lu le {read}), ce que cela ne couvre pas, et comment être alerté des nouvelles annonces sous le prix que tu veux payer.',
        answer='Oui, mais seulement pour tes favoris. Le centre d’aide de Vinted cite une notification quand le prix d’un article que tu as ajouté à tes favoris a baissé, et une autre quand un article de tes favoris a été vendu. Il ne décrit aucune notification pour les baisses de prix sur les articles qui ne sont pas dans tes favoris. Et un prix plus bas qu’un vendeur te propose dans une conversation n’est visible que par toi, pas sur l’annonce.',
        toc=[('favoris', 'Comment ça marche'), ('limites', 'Ce que ça ne couvre pas'), ('snypd', 'Alertes sous ton prix'),
             ('choisir', 'Quoi utiliser')],
        sections=[
            ('favoris', 'Comment marche la notification de baisse de prix sur Vinted',
             "<blockquote>«\xa0Le prix d'un article que tu as ajouté à tes favoris a baissé.\xa0»"
             '<cite>Aide Vinted, <a href="{h433}" rel="nofollow noopener">Comment gérer tes notifications\xa0?</a> (lu le {read})</cite></blockquote>'
             '<p>C’est l’un des cas où, selon l’aide de Vinted, tu peux recevoir une notification. La même liste comprend un article de tes favoris qui a été vendu, et un membre que tu suis qui met en ligne un nouvel article. Pour être prévenu quand un article baisse, ajoute-le donc à tes favoris.</p>'
             '<p>Les notifications arrivent dans ta messagerie Vinted. Celles qui s’affichent aussi en push hors de l’application se règlent dans ton profil, sous <strong>Paramètres &gt; Notifications (Mobile)</strong>\xa0; tu peux y fixer un nombre maximal de notifications non prioritaires par jour (section Notifications secondaires). Si rien n’arrive, vois <a href="{notwork}">notification Vinted qui ne fonctionne pas</a>.</p>'),
            ('limites', 'Ce que la notification de baisse de prix ne couvre pas',
             '<ul><li><strong>Les articles hors de tes favoris.</strong> Le centre d’aide ne cite les baisses de prix que pour les favoris\xa0: une autre annonce qui baisse ne t’envoie rien.</li>'
             '<li><strong>Les nouvelles annonces.</strong> Un nouvel article déjà pas cher n’est pas une baisse de prix. Une recherche sauvegardée affiche seulement un compteur «\xa0+N\xa0» dans la barre de recherche (<a href="{saved}">recherches sauvegardées Vinted</a>).</li>'
             '<li><strong>Les offres.</strong> D’après l’aide de Vinted sur <a href="{h258}" rel="nofollow noopener">les offres</a>, un vendeur peut te proposer un prix plus bas dans une conversation, jusqu’à 40\xa0% de moins que le prix d’origine. Le nouveau prix n’est visible que par toi\xa0; les autres voient toujours le prix d’origine et peuvent acheter tant que tu n’as pas cliqué sur Acheter. Le prix d’une annonce n’est donc pas toujours le prix payé (<a href="{sold}">ce qu’on peut voir des articles vendus</a>).</li></ul>'),
            ('snypd', 'Être alerté des nouvelles annonces sous ton prix',
             '<p>Soyons clairs d’abord\xa0: SNYPD ne suit pas les baisses de prix. Il ne surveille pas les annonces déjà en ligne, donc une annonce qui baisse ne déclenche pas d’alerte SNYPD.</p>'
             '<p>Ce qu’il fait\xa0: il surveille une recherche Vinted pour les nouvelles annonces, et une recherche Vinted peut avoir un prix maximum. Pour «\xa0Nike Dunk Low à moins de 40\xa0€\xa0»\xa0:</p>'
             '<ol><li>Cherche l’article sur Vinted dans un navigateur et mets le maximum du filtre de prix à 40, plus la taille et l’état si tu veux.</li>'
             '<li>Copie l’adresse dans la barre d’adresse. Elle contient <code>/catalog?</code> et le prix choisi (<code>price_to=40</code>).</li>'
             '<li>Colle-la dans SNYPD et active la recherche.</li>'
             '<li>SNYPD vérifie la recherche environ toutes les 30 secondes à une minute et t’envoie un push sur ton téléphone ou ton ordinateur pour chaque nouvelle annonce qui correspond, prix compris.</li></ol>'
             '<p>Environ toutes les 30 secondes à une minute, c’est la fréquence à laquelle SNYPD regarde, pas le temps qu’une annonce met à t’arriver\xa0: Vinted lui-même affiche une nouvelle annonce dans sa recherche quelques minutes après sa mise en ligne. SNYPD ne se connecte jamais à ton compte Vinted, n’achète rien et n’écrit pas aux vendeurs. Gratuit\xa0: 1 recherche, 24/7 avec alertes pendant les @@trial_days@@ premiers jours après ta première recherche enregistrée dans SNYPD, puis seulement quand le tableau de bord est ouvert\xa0; plans payants dès @@price:solo@@ par mois, 24/7. En savoir plus\xa0: <a href="{bot}">SNYPD, le bot Vinted d’alertes</a>.</p>'),
            ('choisir', 'Quoi utiliser',
             '<ul><li><strong>Un article précis que tu attends\xa0:</strong> ajoute-le à tes favoris. Vinted te prévient quand son prix baisse ou quand il est vendu.</li>'
             '<li><strong>Toute nouvelle annonce d’un modèle sous ton prix\xa0:</strong> une recherche Vinted avec un prix maximum, surveillée par SNYPD.</li>'
             '<li>Les deux se complètent\xa0: les favoris pour ce qui est déjà en ligne, la recherche pour ce qui arrive ensuite.</li></ul>'),
        ],
        faq=[
            ('Vinted prévient-il quand un prix baisse\xa0?',
             'Oui, pour les articles de tes favoris. Le centre d’aide de Vinted cite une notification quand le prix d’un article de tes favoris a baissé, et une autre quand il a été vendu.'),
            ('Suis-je prévenu si un article qui n’est pas dans mes favoris baisse\xa0?',
             'Le centre d’aide de Vinted n’en décrit aucune. La notification de baisse de prix concerne les favoris\xa0: ajoute l’article à tes favoris pour être prévenu.'),
            ('SNYPD suit-il les baisses de prix sur Vinted\xa0?',
             'Non. SNYPD t’alerte des nouvelles annonces qui correspondent à ta recherche Vinted, y compris le prix maximum que tu fixes. Il ne surveille pas le prix des annonces déjà en ligne.'),
            ('Les autres acheteurs voient-ils le prix plus bas que le vendeur m’a proposé\xa0?',
             'Non. D’après l’aide de Vinted, le nouveau prix proposé par le vendeur dans une conversation est visible uniquement par cet acheteur\xa0; les autres voient toujours le prix d’origine.'),
        ],
        cta_h='Sois alerté des nouvelles annonces sous ton prix'),

    # ---------------------------------------------------------------- DE
    'de': dict(
        title='Vinted Preis reduziert: Benachrichtigung bei Favoriten | SNYPD',
        desc='Vinted benachrichtigt dich, wenn der Preis eines Favoriten gesenkt oder er verkauft wurde. Was das nicht abdeckt und wie du neue Artikel unter deinem Preis siehst.',
        eyebrow='VINTED PREISSENKUNGEN',
        h1='Sagt dir Vinted, wenn ein Preis reduziert wird?',
        lead='Ja, für Artikel in deinen Favoriten. Hier steht, was die Vinted-Hilfe sagt (gelesen am {read}), was das nicht abdeckt und wie du von neuen Anzeigen unter deinem Wunschpreis erfährst.',
        answer='Ja, aber nur für deine Favoriten. Die Vinted-Hilfe nennt eine Benachrichtigung, wenn der Preis eines deiner Favoriten gesenkt wurde, und eine, wenn einer deiner Favoriten verkauft wurde. Für Preissenkungen bei Artikeln, die nicht in deinen Favoriten sind, beschreibt sie keine. Und einen niedrigeren Preis, den dir ein Verkäufer im Chat anbietet, siehst nur du, nicht die Anzeige.',
        toc=[('favoriten', 'So funktioniert es'), ('grenzen', 'Was nicht abgedeckt ist'), ('snypd', 'Alarm unter deinem Preis'),
             ('welches', 'Was du nutzen solltest')],
        sections=[
            ('favoriten', 'So funktioniert die Vinted-Benachrichtigung bei Preissenkung',
             '<blockquote>„der Preis eines deiner Favoriten gesenkt wurde“'
             '<cite>Vinted-Hilfe, <a href="{h433}" rel="nofollow noopener">Verwaltung deiner Benachrichtigungen</a> (gelesen am {read})</cite></blockquote>'
             '<p>Das ist einer der Fälle, in denen du laut Vinted-Hilfe eine Benachrichtigung bekommst. Auf derselben Liste stehen ein verkaufter Favorit und ein Mitglied, dem du folgst, das einen neuen Artikel hochlädt. Willst du erfahren, wann ein Artikel günstiger wird, speichere ihn also als Favorit.</p>'
             '<p>Benachrichtigungen landen in deiner Vinted-Inbox. Welche zusätzlich als Push außerhalb der App erscheinen, stellst du in deinem Profil unter <strong>Meine Einstellungen &gt; Push-Benachrichtigungen</strong> ein; im Bereich Andere Benachrichtigungen kannst du außerdem ein tägliches Limit festlegen. Kommt gar nichts an, lies <a href="{notwork}">Vinted-Benachrichtigung funktioniert nicht</a>.</p>'),
            ('grenzen', 'Was die Benachrichtigung bei Preissenkung nicht abdeckt',
             '<ul><li><strong>Artikel, die nicht in deinen Favoriten sind.</strong> Die Vinted-Hilfe nennt Preissenkungen nur für Favoriten: Wird eine andere Anzeige günstiger, bekommst du nichts.</li>'
             '<li><strong>Neue Anzeigen.</strong> Ein neuer Artikel, der schon günstig ist, ist keine Preissenkung. Eine gespeicherte Suche zeigt nur einen Zähler „+N“ im Suchfeld (<a href="{saved}">gespeicherte Suchen auf Vinted</a>).</li>'
             '<li><strong>Angebote.</strong> Laut Vinted-Hilfe zum <a href="{h258}" rel="nofollow noopener">Verhandeln</a> kann dir ein Verkäufer im Chat einen niedrigeren Preis anbieten, bis zu 40 % unter dem ursprünglichen. Der neue Preis ist nur für dich sichtbar; andere sehen weiter den ursprünglichen Preis und können kaufen, bis du auf „Kaufen“ tippst. Der Preis einer Anzeige ist also nicht immer der bezahlte Preis (<a href="{sold}">was du über verkaufte Artikel sehen kannst</a>).</li></ul>'),
            ('snypd', 'Alarm für neue Anzeigen unter deinem Preis',
             '<p>Vorweg: SNYPD verfolgt keine Preissenkungen. Es beobachtet keine Anzeigen, die schon online sind; wird eine Anzeige günstiger, löst das keinen SNYPD-Alarm aus.</p>'
             '<p>Was es macht: Es prüft eine Vinted-Suche auf neue Anzeigen, und eine Vinted-Suche kann einen Höchstpreis haben. Für „Nike Dunk Low unter 40\xa0€“:</p>'
             '<ol><li>Such den Artikel auf Vinted im Browser und setz den Höchstwert im Preisfilter auf 40, dazu Größe und Zustand, wenn du willst.</li>'
             '<li>Kopiere die Adresse aus der Adresszeile. Sie enthält <code>/catalog?</code> und deinen Preis (<code>price_to=40</code>).</li>'
             '<li>Füge sie in SNYPD ein und schalte die Suche ein.</li>'
             '<li>SNYPD prüft die Suche etwa alle 30 Sekunden bis eine Minute und schickt dir für jede neue passende Anzeige eine Push-Nachricht aufs Handy oder den Computer, mit Preis.</li></ol>'
             '<p>Etwa alle 30 Sekunden bis eine Minute ist, wie oft SNYPD nachschaut, nicht, wie schnell eine Anzeige bei dir ankommt: Vinted selbst zeigt einen neuen Artikel erst einige Minuten nach dem Einstellen in der Suche. SNYPD meldet sich nie in deinem Vinted-Konto an, kauft nichts und schreibt keinen Verkäufern. Kostenlos: 1 Suche, rund um die Uhr mit Benachrichtigungen in den ersten @@trial_days@@ Tagen, nachdem du deine erste Suche in SNYPD gespeichert hast, danach nur bei geöffnetem Dashboard; bezahlte Tarife ab @@price:solo@@ im Monat laufen rund um die Uhr. Mehr dazu: <a href="{bot}">SNYPD, der Vinted Bot für Benachrichtigungen</a>.</p>'),
            ('welches', 'Was du wofür nutzt',
             '<ul><li><strong>Ein bestimmter Artikel, auf den du wartest:</strong> speichere ihn als Favorit. Vinted meldet sich, wenn sein Preis gesenkt oder er verkauft wurde.</li>'
             '<li><strong>Jede neue Anzeige eines Modells unter deinem Preis:</strong> eine Vinted-Suche mit Höchstpreis, geprüft von SNYPD.</li>'
             '<li>Beides ergänzt sich: Favoriten für das, was schon online ist, die Suche für das, was als Nächstes kommt.</li></ul>'),
        ],
        faq=[
            ('Benachrichtigt Vinted, wenn ein Preis reduziert wird?',
             'Ja, für Artikel in deinen Favoriten. Die Vinted-Hilfe nennt eine Benachrichtigung, wenn der Preis eines deiner Favoriten gesenkt wurde, und eine, wenn er verkauft wurde.'),
            ('Bekomme ich eine Nachricht, wenn ein Artikel ohne Favorit günstiger wird?',
             'Die Vinted-Hilfe beschreibt keine. Die Benachrichtigung bei Preissenkung gilt für Favoriten: Speichere den Artikel als Favorit, wenn du davon erfahren willst.'),
            ('Verfolgt SNYPD Preissenkungen auf Vinted?',
             'Nein. SNYPD meldet dir neue Anzeigen, die zu deiner Vinted-Suche passen, auch mit einem Höchstpreis, den du festlegst. Die Preise von Anzeigen, die schon online sind, beobachtet es nicht.'),
            ('Sehen andere Käufer den niedrigeren Preis, den mir ein Verkäufer angeboten hat?',
             'Nein. Laut Vinted-Hilfe ist ein neuer Preis, den der Verkäufer im Chat anbietet, nur für diesen Käufer sichtbar; alle anderen sehen weiter den ursprünglichen Preis.'),
        ],
        cta_h='Alarm für neue Anzeigen unter deinem Preis'),

    # ---------------------------------------------------------------- NL
    'nl': dict(
        title='Vinted melding prijs verlaagd: zo werkt het | SNYPD',
        desc='Vinted stuurt een melding als een favoriet artikel in prijs is verlaagd of verkocht is. Wat dat niet dekt, en hoe je nieuwe advertenties onder jouw prijs ziet.',
        eyebrow='VINTED PRIJSVERLAGINGEN',
        h1='Krijg je een melding van Vinted als een prijs verlaagd is?',
        lead='Ja, voor artikelen die je als favoriet hebt gemarkeerd. Dit zegt de Vinted-hulp (gelezen op {read}), dit dekt het niet, en zo hoor je van nieuwe advertenties onder de prijs die je wilt betalen.',
        answer='Ja, maar alleen voor je favorieten. De Vinted-hulp noemt een notificatie als een van je favoriete artikelen in prijs is verlaagd, en een als een van je favoriete artikelen is verkocht. Voor prijsverlagingen van artikelen die niet in je favorieten staan, beschrijft de hulp er geen. En een lagere prijs die een verkoper je in de chat biedt, is alleen voor jou zichtbaar, niet op de advertentie.',
        toc=[('favorieten', 'Zo werkt het'), ('niet-gedekt', 'Wat het niet dekt'), ('snypd', 'Melding onder jouw prijs'),
             ('welke', 'Wat gebruik je')],
        sections=[
            ('favorieten', 'Zo werkt de Vinted-melding bij een verlaagde prijs',
             '<blockquote>“Een van je favoriete artikelen in prijs is verlaagd”'
             '<cite>Vinted-hulp, <a href="{h433}" rel="nofollow noopener">Notificaties beheren</a> (gelezen op {read})</cite></blockquote>'
             '<p>Dat is een van de gevallen waarin je volgens de Vinted-hulp een notificatie krijgt. In hetzelfde lijstje staan een favoriet die verkocht is en leden die je volgt die nieuwe artikelen uploaden. Wil je horen wanneer één artikel goedkoper wordt, markeer het dan als favoriet.</p>'
             '<p>Notificaties komen in je Vinted-inbox. Welke ook als pushmelding buiten de app verschijnen, stel je in via je profiel onder <strong>Mijn instellingen &gt; Pushmeldingen</strong>; onder Minder belangrijke notificaties kun je ook een dagelijkse limiet instellen. Komt er helemaal niets binnen, lees dan <a href="{notwork}">Vinted-meldingen werken niet</a>.</p>'),
            ('niet-gedekt', 'Wat de melding bij een verlaagde prijs niet dekt',
             '<ul><li><strong>Artikelen die niet in je favorieten staan.</strong> De Vinted-hulp noemt prijsverlagingen alleen voor favorieten: wordt een andere advertentie goedkoper, dan krijg je niets.</li>'
             '<li><strong>Nieuwe advertenties.</strong> Een nieuw artikel dat al goedkoop is, is geen prijsverlaging. Een opgeslagen zoekopdracht toont alleen een teller ‘+N’ in de zoekbalk (<a href="{saved}">opgeslagen zoekopdrachten op Vinted</a>).</li>'
             '<li><strong>Biedingen.</strong> Volgens de Vinted-hulp over <a href="{h258}" rel="nofollow noopener">een bod doen</a> kan een verkoper je in de chat een lagere prijs bieden, tot 40% onder de oorspronkelijke prijs. De nieuwe prijs is alleen voor jou zichtbaar; anderen zien nog steeds de oorspronkelijke prijs en kunnen het artikel kopen totdat jij op Kopen drukt.</li></ul>'),
            ('snypd', 'Een melding voor nieuwe advertenties onder jouw prijs',
             '<p>Eerst voor de duidelijkheid: SNYPD volgt geen prijsverlagingen. Het houdt geen advertenties in de gaten die al online staan, dus een advertentie die goedkoper wordt, geeft geen SNYPD-melding.</p>'
             '<p>Wat het wel doet: het controleert een Vinted-zoekopdracht op nieuwe advertenties, en een Vinted-zoekopdracht kan een maximumprijs hebben. Voor ‘Nike Dunk Low onder €\xa040’:</p>'
             '<ol><li>Zoek het artikel op Vinted in je browser en zet het maximum van het prijsfilter op 40, eventueel met maat en staat erbij.</li>'
             '<li>Kopieer het adres uit de adresbalk. Daar staan <code>/catalog?</code> en je prijs in (<code>price_to=40</code>).</li>'
             '<li>Plak het in SNYPD en zet de zoekopdracht aan.</li>'
             '<li>SNYPD controleert de zoekopdracht ongeveer elke 30 seconden tot een minuut en stuurt je voor elke nieuwe advertentie die past een pushmelding op je telefoon of computer, met de prijs erbij.</li></ol>'
             '<p>Ongeveer elke 30 seconden tot een minuut is hoe vaak SNYPD kijkt, niet hoe snel een advertentie bij je is: Vinted toont een nieuwe advertentie zelf pas een paar minuten na het plaatsen in de zoekresultaten. SNYPD logt nooit in op je Vinted-account, koopt niets en stuurt geen berichten naar verkopers. Gratis: 1 zoekopdracht, 24/7 met meldingen in de eerste @@trial_days@@ dagen nadat je je eerste zoekopdracht in SNYPD hebt opgeslagen, daarna alleen zolang het dashboard open staat; betaalde abonnementen vanaf @@price:solo@@ per maand werken 24/7. Meer daarover: <a href="{bot}">SNYPD, de Vinted bot voor meldingen</a>.</p>'),
            ('welke', 'Wat gebruik je waarvoor',
             '<ul><li><strong>Eén artikel waar je op wacht:</strong> markeer het als favoriet. Vinted laat het weten als de prijs is verlaagd of als het verkocht is.</li>'
             '<li><strong>Elke nieuwe advertentie van een model onder jouw prijs:</strong> een Vinted-zoekopdracht met een maximumprijs, gecontroleerd door SNYPD.</li>'
             '<li>Ze werken naast elkaar: favorieten voor wat al online staat, een zoekopdracht voor wat er nog bijkomt.</li></ul>'),
        ],
        faq=[
            ('Krijg je een melding van Vinted als een prijs verlaagd is?',
             'Ja, voor je favorieten. De Vinted-hulp noemt een notificatie als een van je favoriete artikelen in prijs is verlaagd, en een als het verkocht is.'),
            ('Krijg ik een melding als een artikel dat geen favoriet is goedkoper wordt?',
             'De Vinted-hulp beschrijft er geen. De melding bij een verlaagde prijs geldt voor favorieten: markeer het artikel als favoriet als je ervan wilt horen.'),
            ('Volgt SNYPD prijsverlagingen op Vinted?',
             'Nee. SNYPD meldt je nieuwe advertenties die bij je Vinted-zoekopdracht passen, ook met een maximumprijs die jij instelt. De prijzen van advertenties die al online staan, volgt het niet.'),
            ('Zien andere kopers de lagere prijs die een verkoper mij bood?',
             'Nee. Volgens de Vinted-hulp is een nieuwe prijs die de verkoper in de chat biedt alleen zichtbaar voor dat lid; andere potentiële kopers zien nog steeds de oorspronkelijke prijs.'),
        ],
        cta_h='Krijg een melding bij nieuwe advertenties onder jouw prijs'),
  },
  # ======================================================================== ALERT GUIDE (FR only, 21 Nov 2026)
  # Target: "comment avoir une alerte pour chaque nouvelle annonce vinted". Vinted statements = the 'saved' FR block
  # above (help 433/435, read 18 Oct 2026); SNYPD facts = outreach/00-fact-sheet.md; plan numbers = plans.py tokens.
  'alertguide': {
    'slugs': {'fr': '/fr/alerte-vinted-nouvelle-annonce'},
    'fr': dict(
        title='Alerte Vinted à chaque nouvelle annonce\xa0: le guide (2026) | SNYPD',
        desc='Recevoir une alerte pour chaque nouvelle annonce Vinted\xa0: ce que Vinted propose, la mise en place pas à pas et les bons réglages.',
        eyebrow='GUIDE ALERTES VINTED',
        h1='Comment recevoir une alerte pour chaque nouvelle annonce Vinted\xa0?',
        lead='Un guide pratique\xa0: ce que Vinted fait déjà (centre d’aide lu le {read}), comment mettre en place une alerte par nouvelle annonce en quelques minutes, et comment la régler pour ne pas être noyé sous les notifications.',
        answer='Sur Vinted, une recherche sauvegardée affiche un compteur «\xa0+N\xa0» des nouveaux articles, mais le centre d’aide ne décrit aucune notification pour chaque nouveau résultat. Pour être prévenu à chaque nouvelle annonce, il faut un outil qui vérifie ta recherche à ta place et t’envoie un push quand une annonce correspond.',
        toc=[('vinted', 'Ce que Vinted propose'), ('etapes', 'La mise en place, étape par étape'), ('ou', 'Où arrivent les alertes'),
             ('reglages', 'Régler l’alerte'), ('exemples', 'Trois exemples de recherche'), ('erreurs', 'Cinq erreurs fréquentes')],
        sections=[
            ('vinted', 'Ce que Vinted propose déjà',
             '<p>Sur Vinted, une recherche sauvegardée affiche un compteur «\xa0+N\xa0» des nouveaux articles depuis ta dernière visite (<a href="{h435}" rel="nofollow noopener">Comment sauvegarder une recherche\xa0?</a>). Mais Vinted n’envoie aucun push quand un nouveau résultat arrive\xa0: tu ne le vois qu’en ouvrant l’appli.</p>'
             '<p>Tout sur les recherches sauvegardées\xa0: <a href="{saved}">recherches enregistrées Vinted</a>. Si tes notifications Vinted habituelles n’arrivent plus\xa0: <a href="{notwork}">notification Vinted qui ne fonctionne pas</a>. Les options gratuites et leurs limites\xa0: <a href="/fr/bot-vinted-gratuit">bot Vinted gratuit</a>.</p>'),
            ('etapes', 'La mise en place avec SNYPD, étape par étape',
             '<ol><li><strong>Fais ta recherche sur Vinted</strong> dans un navigateur, avec tous tes filtres\xa0: marque, taille, état, prix maximum.</li>'
             '<li><strong>Copie le lien</strong> dans la barre d’adresse. Il contient <code>/catalog?</code>. Tous les filtres du lien sont repris tels quels\xa0; un lien avec un paramètre inconnu est refusé plutôt que coupé en silence.</li>'
             '<li><strong>Crée ton compte SNYPD</strong> (pas de carte bancaire pour le plan Free).</li>'
             '<li><strong>Colle le lien</strong> et lance la recherche. SNYPD la vérifie environ toutes les 30 secondes à une minute.</li>'
             '<li><strong>Active les alertes.</strong> Sur ordinateur, autorise les notifications quand le navigateur le demande\xa0; sur iPhone, suis d’abord le guide <a href="{phone}">alertes Vinted sur téléphone</a>.</li>'
             '<li><strong>En option, Discord</strong>\xa0: avec un abonnement, le Pass 30 jours ou un essai en cours, relie ton compte au serveur Discord SNYPD pour recevoir aussi tes alertes dans un fil privé.</li></ol>'
             '<p>La fréquence de vérification n’est pas un délai d’arrivée\xa0: Vinted affiche lui-même une nouvelle annonce dans sa recherche quelques minutes après sa mise en ligne. SNYPD ne se connecte jamais à ton compte Vinted, n’achète rien et n’écrit pas aux vendeurs. L’alerte ouvre l’annonce sur Vinted, c’est toi qui décides.</p>'),
            ('ou', 'Où arrivent les alertes',
             '<ul><li><strong>Notification push</strong> sur ton téléphone ou ton ordinateur. Plusieurs annonces trouvées à la suite arrivent groupées dans un seul push (jusqu’à 5 annonces listées).</li>'
             '<li><strong>Le tableau de bord</strong>, qui montre toutes les nouvelles annonces trouvées.</li>'
             '<li><strong>Discord</strong>\xa0: avec un abonnement, le Pass 30 jours ou un essai en cours, un fil privé sur le serveur Discord SNYPD.</li></ul>'
             '<p>Pas de Telegram, pas d’e-mail pour les alertes. Ce que valent les bots Telegram et que choisir\xa0: <a href="/fr/alerte-vinted-telegram">alerte Vinted sur Telegram</a>.</p>'),
            ('reglages', 'Régler l’alerte pour ne pas être noyé',
             '<p>Une recherche trop large peut sortir des centaines d’annonces par jour. Quatre réglages font la différence\xa0:</p>'
             '<ul><li><strong>Un prix maximum.</strong> C’est le filtre le plus efficace\xa0: mets-le dans ta recherche Vinted avant de copier le lien.</li>'
             '<li><strong>Des mots précis.</strong> La recherche Vinted demande que tous les mots soient dans une même annonce. «\xa0ralph lauren pull\xa0» fonctionne\xa0; une liste comme «\xa0Ralph Lauren, Nike, Adidas\xa0» ne trouve presque rien. Une marque = une recherche.</li>'
             '<li><strong>Le mode Calme</strong>\xa0: la première trouvaille tout de suite, puis au plus un résumé toutes les 15 ou 30 minutes au lieu du mode «\xa0Chaque annonce\xa0».</li>'
             '<li><strong>Seulement les moins chères</strong>\xa0: un push seulement pour une annonce moins chère que 75\xa0% de ce que cette recherche a trouvé dans la semaine (prix demandés, même état). Les annonces pas encore évaluées passent quand même, et le tableau de bord montre tout. Disponible sur les plans payants, le Pass 30 jours et pendant l’essai, pas sur le plan Free.</li></ul>'),
            ('exemples', 'Trois exemples de recherche',
             '<p>Des idées de structure, à adapter à ce que tu cherches. Le prix maximum, c’est toi qui le fixes selon ton budget\xa0:</p>'
             '<ul><li><strong>Marque + modèle + taille</strong>\xa0: «\xa0nike air max 90\xa0», filtre taille 42, filtre prix maximum.</li>'
             '<li><strong>Marque + type de vêtement + état</strong>\xa0: «\xa0carhartt veste\xa0», filtre état «\xa0Très bon état\xa0» ou mieux, filtre prix maximum.</li>'
             '<li><strong>Un objet précis</strong>\xa0: «\xa0ps5 manette\xa0», filtre prix maximum. Si tu ne cherches qu’un seul objet, une seule recherche bien ciblée suffit.</li></ul>'),
            ('erreurs', 'Cinq erreurs fréquentes',
             '<ol><li><strong>Plusieurs marques dans une seule recherche.</strong> Vinted veut tous les mots dans la même annonce\xa0: la recherche ne trouve presque rien. Fais une recherche par marque.</li>'
             '<li><strong>Pas de prix maximum.</strong> Tu reçois tout, y compris ce que tu n’achèteras jamais, et tu finis par ignorer les alertes.</li>'
             '<li><strong>Les alertes jamais activées.</strong> La recherche tourne, mais sans autorisation de notification, rien n’arrive sur ton appareil.</li>'
             '<li><strong>iPhone sans l’icône sur l’écran d’accueil.</strong> Sans elle, pas de notification\xa0: voir <a href="{phone}">alertes Vinted sur téléphone</a>.</li>'
             '<li><strong>Attendre une alerte à la seconde où l’annonce est postée.</strong> Vinted affiche une nouvelle annonce dans sa recherche quelques minutes après sa mise en ligne\xa0; SNYPD ne peut la voir qu’à partir de ce moment.</li></ol>'),
        ],
        faq=[
            ('Est-ce gratuit\xa0?',
             'Oui pour commencer. Le plan Free fait tourner ta première recherche 24h/24 avec les alertes pendant @@trial_days@@ jours après ta première recherche dans SNYPD. Si elle ne trouve rien pendant ce temps, on ajoute @@trial_ext_days@@ jours de plus, une seule fois. Ensuite, elle ne tourne que quand le tableau de bord est ouvert. Les plans payants tournent 24h/24 dès @@price:solo@@ par mois.'),
            ('En combien de temps arrive l’alerte\xa0?',
             'SNYPD vérifie ta recherche environ toutes les 30 secondes à une minute. C’est la fréquence de vérification, pas un délai garanti\xa0: Vinted affiche une nouvelle annonce dans sa recherche quelques minutes après sa mise en ligne.'),
            ('Vinted peut-il m’envoyer une notification pour une recherche sauvegardée\xa0?',
             'Son centre d’aide décrit un compteur «\xa0+N\xa0» dans la barre de recherche, pas une notification pour chaque nouveau résultat. Pour être prévenu à chaque nouvelle annonce, il faut un outil qui vérifie la recherche.'),
            ('Dois-je donner mon mot de passe Vinted\xa0?',
             'Non. SNYPD ne te demande jamais ton mot de passe Vinted et ne se connecte jamais à ton compte. Il n’achète rien et n’écrit pas aux vendeurs.'),
            ('Pourquoi je ne reçois rien sur mon iPhone\xa0?',
             'Sur iPhone, les alertes ne fonctionnent qu’une fois SNYPD ajouté à l’écran d’accueil et ouvert depuis cette icône. Active ensuite les alertes depuis l’appli. Pas à pas\xa0: <a href="{phone}">alertes Vinted sur téléphone</a>.'),
            ('Je reçois trop d’alertes, que faire\xa0?',
             'Ajoute un prix maximum à ta recherche, utilise des mots plus précis, ou passe la recherche en mode Calme (un résumé toutes les 15 ou 30 minutes) ou en «\xa0Seulement les moins chères\xa0» (plans payants, Pass 30 jours et essai en cours). Toutes les options d’alerte\xa0: <a href="{notify}">alertes Vinted pour les nouvelles annonces</a>.'),
        ],
        cta_h='Crée ta première alerte Vinted'),
  },
  # ======================================================================== TELEGRAM (FR only, 22 Nov 2026)
  # Target: "alerte vinted telegram". SNYPD facts = outreach/00-fact-sheet.md (line 39: no Telegram alerts);
  # Telegram tools = only what compare_data.py already states; plan numbers = plans.json tokens.
  'telegram': {
    'slugs': {'fr': '/fr/alerte-vinted-telegram'},
    'fr': dict(
        title='Alerte Vinted Telegram\xa0: bots, Discord ou push (2026) | SNYPD',
        desc='Alerte Vinted sur Telegram\xa0: ce que sont les bots Telegram pour Vinted, ce que SNYPD envoie à la place et que choisir entre Telegram, Discord et push.',
        eyebrow='GUIDE ALERTES VINTED',
        h1='Alerte Vinted sur Telegram\xa0: comment ça marche et que choisir\xa0?',
        lead='Ce que sont les bots Telegram pour Vinted, ce que SNYPD envoie à la place, et comment choisir entre Telegram, Discord et les notifications push.',
        answer='SNYPD n’envoie pas d’alertes Telegram. Il vérifie ta recherche Vinted environ toutes les 30 secondes à une minute et, pendant l’essai et sur les plans payants, t’envoie une notification push sur ton téléphone ou ton ordinateur, sans passer par un store d’applications. Après l’essai, le plan Free ne vérifie ta recherche que quand le tableau de bord est ouvert. Avec un abonnement, le Pass 30 jours ou un essai en cours, les alertes arrivent aussi dans un fil privé sur le serveur Discord SNYPD. Si tu tiens à Telegram, il faut un autre outil.',
        toc=[('bots', 'Les bots Telegram pour Vinted'), ('snypd', 'Ce que SNYPD envoie'), ('choisir', 'Telegram, Discord ou push')],
        sections=[
            ('bots', 'Les bots Telegram pour Vinted, c’est quoi\xa0?',
             '<p>Un bot d’alertes Vinted surveille une recherche et te prévient quand une nouvelle annonce correspond. Ceux qui passent par Telegram t’envoient l’annonce dans une conversation Telegram. On en trouve de deux sortes\xa0:</p>'
             '<ul><li><strong>Les scripts open source sur GitHub</strong>, que tu héberges toi-même. Certains postent sur Telegram, d’autres sur Discord ou par e-mail. Gratuits, mais c’est toi qui gères le serveur et qui répares quand Vinted change quelque chose.</li>'
             '<li><strong>Les services tiers</strong>, avec un bot Telegram auquel tu t’abonnes. Certains n’alertent que dans Telegram, d’autres proposent Telegram parmi plusieurs canaux.</li></ul>'
             '<p>Prix, canaux et plans gratuits de chaque outil, côte à côte\xa0: <a href="/fr/comparatif-bot-vinted">comparatif des bots Vinted</a>. Ce que fait un bot d’alertes en général\xa0: <a href="{bot}">SNYPD, le bot d’alertes Vinted</a>.</p>'),
            ('snypd', 'Ce que SNYPD envoie à la place',
             '<p>SNYPD liste les nouvelles annonces dans le tableau de bord et t’envoie une notification push pendant l’essai et sur les plans payants, puis, sur le plan Free, seulement quand le tableau de bord est ouvert. Avec un abonnement, le Pass 30 jours ou un essai en cours, les alertes arrivent aussi dans un fil privé sur le serveur Discord SNYPD, mais jamais sur Telegram ni par e-mail. Les canaux et la mise en place, pas à pas\xa0: <a href="/fr/alerte-vinted-nouvelle-annonce">recevoir une alerte pour chaque nouvelle annonce Vinted</a>.</p>'),
            ('choisir', 'Telegram ou Discord ou push\xa0: que choisir\xa0?',
             '<ul><li><strong>Tu veux le moins d’étapes possible</strong>\xa0: le push. Pas d’autre appli, pas d’autre compte. Il arrive pendant l’essai et sur les plans payants\xa0; après l’essai, le plan Free ne vérifie ta recherche que quand le tableau de bord est ouvert.</li>'
             '<li><strong>Tu passes déjà tes journées sur Discord</strong>\xa0: Discord, pour avoir tes trouvailles à côté du reste (abonnement, Pass 30 jours ou essai en cours).</li>'
             '<li><strong>Tu es sur iPhone et tu ne veux pas ajouter SNYPD à l’écran d’accueil</strong>\xa0: Discord, dont l’appli te prévient sans cette étape. Les alertes Discord demandent un plan payant, le Pass 30 jours ou un essai en cours.</li>'
             '<li><strong>Tu veux absolument Telegram</strong>\xa0: il te faut un autre outil, script à héberger ou service tiers\xa0; SNYPD ne l’envoie pas.</li></ul>'
             '<p>Quel que soit le canal, SNYPD vérifie ta recherche à la même fréquence\xa0: environ toutes les 30 secondes à une minute, sur tous les plans. C’est la fréquence de vérification, pas un délai d’arrivée\xa0: Vinted affiche une nouvelle annonce dans sa recherche quelques minutes après sa mise en ligne.</p>'),
        ],
        faq=[
            ('SNYPD envoie-t-il des alertes Vinted sur Telegram\xa0?',
             'Non. Les alertes SNYPD arrivent en notification push, dans le tableau de bord et, avec un abonnement, le Pass 30 jours ou un essai en cours, dans un fil privé sur le serveur Discord SNYPD.'),
            ('Un bot Telegram pour Vinted est-il gratuit\xa0?',
             'Les scripts open source sur GitHub sont gratuits, mais tu les héberges et les répares toi-même. Les services tiers ont leurs propres prix, côte à côte dans le <a href="/fr/comparatif-bot-vinted">comparatif des bots Vinted</a>.'),
            ('SNYPD est-il gratuit\xa0?',
             'Oui pour commencer. Le plan Free fait tourner ta première recherche 24h/24 avec les alertes pendant @@trial_days@@ jours après ta première recherche dans SNYPD. Si elle ne trouve rien pendant ce temps, on ajoute @@trial_ext_days@@ jours de plus, une seule fois. Ensuite, elle ne tourne que quand le tableau de bord est ouvert. Les abonnements tournent 24h/24 dès @@price:solo@@ par mois\xa0; le Pass coûte @@price:pass@@ en une fois pour @@pass_days@@ jours.'),
            ('Faut-il installer une appli pour recevoir les alertes SNYPD\xa0?',
             'Non. Les notifications push passent par ton navigateur, sans store d’applications. Sur iPhone, ajoute SNYPD à l’écran d’accueil et ouvre-le depuis cette icône. Pas à pas\xa0: <a href="{phone}">alertes Vinted sur téléphone</a>.'),
            ('Dois-je donner mon mot de passe Vinted\xa0?',
             'Non. SNYPD ne te demande jamais ton mot de passe Vinted et ne se connecte jamais à ton compte.'),
        ],
        cta_h='Crée ta première alerte Vinted'),
  },
  # ======================================================================== BOT GRATUIT (FR only, 22 Nov 2026)
  # Target: "bot vinted gratuit". Vinted statements = the 'saved' FR block above (linked, not repeated); SNYPD facts =
  # outreach/00-fact-sheet.md; plan numbers = plans.py tokens. No named rivals, no named open-source project.
  'gratuit': {
    'slugs': {'fr': '/fr/bot-vinted-gratuit'},
    'fr': dict(
        title='Bot Vinted gratuit\xa0: ce que «\xa0gratuit\xa0» veut dire | SNYPD',
        desc='Bot Vinted gratuit\xa0: recherches sauvegardées de Vinted, scripts à héberger soi-même ou essai SNYPD. Ce que chaque option fait, et ses limites.',
        eyebrow='BOT VINTED GRATUIT',
        h1='Existe-t-il un bot Vinted gratuit ?',
        lead='Trois façons d’être prévenu des nouvelles annonces Vinted sans payer, et ce que « gratuit » veut dire pour chacune : ce que Vinted fait lui-même, les scripts à héberger soi-même et l’essai SNYPD.',
        answer='Oui, mais « gratuit » ne veut pas dire la même chose partout. Les recherches sauvegardées de Vinted sont gratuites mais n’envoient pas de notification pour chaque nouvelle annonce. Les scripts open source sont gratuits, mais c’est toi qui les fais tourner et les entretiens. SNYPD a un plan Free : ta première recherche tourne 24h/24 avec les alertes pendant @@trial_days@@ jours, puis seulement quand le tableau de bord est ouvert.',
        toc=[('vinted', 'Les recherches sauvegardées de Vinted'), ('scripts', 'Les scripts à héberger soi-même'),
             ('snypd', 'Le plan Free de SNYPD'), ('choisir', 'Que choisir')],
        sections=[
            ('vinted', 'Les recherches sauvegardées de Vinted : gratuites, sans push',
             '<p>Vinted te laisse sauvegarder une recherche gratuitement. Elle affiche un compteur « +N » des nouveaux articles depuis ta dernière visite, mais son centre d’aide ne décrit aucune notification pour chaque nouveau résultat : tu le vois quand tu ouvres l’appli, pas au moment où l’annonce arrive.</p>'
             '<p>Tout le détail, avec les sources : <a href="{saved}">recherches enregistrées Vinted</a>.</p>'),
            ('scripts', 'Les scripts à héberger soi-même : logiciel gratuit, travail pour toi',
             '<p>Des projets open source surveillent une recherche Vinted et postent les nouvelles annonces, en général sur Discord ou Telegram. Le logiciel est gratuit, mais le reste est pour toi :</p>'
             '<ul><li><strong>Un serveur</strong> ou un ordinateur allumé en permanence pour que le script tourne.</li>'
             '<li><strong>Les jetons et la configuration</strong> : créer le bot Discord ou Telegram, garder ses clés, régler tes recherches dans un fichier.</li>'
             '<li><strong>Les mises à jour</strong> : quand Vinted change quelque chose, le script peut cesser de fonctionner jusqu’à ce que quelqu’un le répare.</li></ul>'
             '<p>Si tu aimes bricoler et que tu as déjà un serveur, c’est une vraie option. Sinon, le temps passé compte aussi.</p>'),
            ('snypd', 'Le plan Free de SNYPD : un essai, puis une recherche tableau de bord ouvert',
             '<p>Le plan Free fait tourner ta première recherche 24h/24 avec les alertes pendant @@trial_days@@ jours après ta première recherche dans SNYPD. Si elle ne trouve rien pendant ce temps, on ajoute @@trial_ext_days@@ jours de plus, une seule fois. Ensuite, elle ne tourne que quand le tableau de bord est ouvert. Le plan Free comprend une recherche, sans carte bancaire.</p>'
             '<ul><li><strong>Pendant l’essai</strong> : vérification environ toutes les 30 secondes à une minute, notifications push sur ton téléphone ou ton ordinateur, et alertes Discord dans un fil privé du serveur SNYPD si tu le relies.</li>'
             '<li><strong>Après l’essai</strong> : la recherche n’est vérifiée que quand le tableau de bord est ouvert, donc les alertes push n’arrivent que pendant qu’il est ouvert. Pour le push 24h/24 : un plan payant ou le Pass 30 jours. Les alertes Discord sont réservées aux plans payants, au Pass 30 jours et à un essai en cours.</li>'
             '<li><strong>Pour continuer 24h/24</strong> : un plan payant dès @@price:solo@@ par mois, ou le Pass 30 jours, @@price:pass@@ en une fois pour 1 recherche pendant @@pass_days@@ jours, sans abonnement. Détails : <a href="/plans">la page des tarifs</a>.</li></ul>'
             '<p>SNYPD ne demande jamais ton mot de passe Vinted, ne se connecte pas à ton compte, n’achète rien et n’écrit pas aux vendeurs. Plus de détails : <a href="{bot}">SNYPD, le bot d’alertes Vinted</a>.</p>'),
            ('choisir', 'Que choisir',
             '<ul><li><strong>Tu regardes Vinted de temps en temps</strong> : les recherches sauvegardées de Vinted suffisent.</li>'
             '<li><strong>Tu veux tout contrôler et tu as un serveur</strong> : un script à héberger soi-même.</li>'
             '<li><strong>Tu veux être prévenu sans rien installer</strong> : essaie le plan Free de SNYPD pendant @@trial_days@@ jours, puis décide si un plan payant ou le Pass 30 jours vaut le coup.</li></ul>'
             '<p>La mise en place pas à pas : <a href="/fr/alerte-vinted-nouvelle-annonce">recevoir une alerte pour chaque nouvelle annonce Vinted</a>.</p>'),
        ],
        faq=[
            ('Existe-t-il un bot Vinted gratuit ?',
             'Oui, avec des limites. Les recherches sauvegardées de Vinted sont gratuites mais sans notification par nouvelle annonce, les scripts open source sont gratuits mais à héberger et entretenir toi-même, et SNYPD a un plan Free avec un essai de @@trial_days@@ jours.'),
            ('Le plan Free de SNYPD, c’est vraiment gratuit ?',
             'Oui, sans carte bancaire. Le plan Free fait tourner ta première recherche 24h/24 avec les alertes pendant @@trial_days@@ jours après ta première recherche dans SNYPD. Si elle ne trouve rien pendant ce temps, on ajoute @@trial_ext_days@@ jours de plus, une seule fois. Ensuite, elle ne tourne que quand le tableau de bord est ouvert. Les plans payants tournent 24h/24 dès @@price:solo@@ par mois.'),
            ('Est-ce que je reçois des notifications push avec le plan Free ?',
             'Oui. Pendant l’essai, ta recherche tourne 24h/24. Après, elle n’est vérifiée que quand le tableau de bord est ouvert, donc les alertes push n’arrivent que pendant qu’il est ouvert. Pour le push 24h/24 : un plan payant ou le Pass 30 jours.'),
            ('Les alertes Discord sont-elles gratuites ?',
             'Seulement pendant un essai en cours. Ensuite, elles sont réservées aux plans payants et au Pass 30 jours.'),
            ('Et sans abonnement ?',
             'Le Pass 30 jours : @@price:pass@@ en une fois pour 1 recherche pendant @@pass_days@@ jours, puis il s’arrête tout seul. Rien à résilier.'),
            ('À quelle fréquence SNYPD vérifie ma recherche ?',
             'Environ toutes les 30 secondes à une minute. C’est la fréquence de vérification, pas un délai garanti : Vinted affiche une nouvelle annonce dans sa recherche quelques minutes après sa mise en ligne.'),
        ],
        cta_h='Essaie SNYPD gratuitement'),
  },
  # ======================================================================== PUSH VS DISCORD (EN only, 22 Nov 2026)
  # Target: "vinted alerts push or discord". SNYPD facts = outreach/00-fact-sheet.md; no Discord caps (in flux).
  'pushdiscord': {
    'slugs': {'en': '/vinted-alerts-push-vs-discord'},
    'en': dict(
        title='Vinted alerts: push notification or Discord? (2026) | SNYPD',
        desc='Push notification or Discord for your Vinted alerts? How each works, who can use Discord, and which to pick on iPhone, Android or a computer.',
        eyebrow='VINTED ALERTS GUIDE',
        h1='Vinted alerts: push notification or Discord, which should I use?',
        lead='A practical comparison for buyers and resellers in the UK and US: what each channel is, how SNYPD sends alerts through each one, and which to pick for the way you hunt.',
        answer='For most people, push is enough: it works on your phone or computer, needs no other app, and comes with every SNYPD plan, including Free. Pick Discord if you already live in Discord, or if you are on iPhone and do not want to add SNYPD to your Home Screen. Discord alerts come with paid plans, the Hunt Pass and a running trial. You can use both at once.',
        toc=[('channels', 'What each channel is'), ('push', 'How SNYPD push alerts work'), ('discord', 'How SNYPD Discord alerts work'),
             ('who', 'Who can use which'), ('pick', 'Which one to pick'), ('both', 'Using both'), ('others', 'Telegram, email and other apps')],
        sections=[
            ('channels', 'What each channel is',
             '<p>A Vinted alert tool watches your Vinted search for you and tells you when a new listing matches it. The watching is the same whichever channel you choose: SNYPD checks your search about every 30 seconds to a minute on every plan. That is how often it looks, not how fast an alert reaches you: Vinted itself shows a new listing in its search minutes after it is posted. What changes between channels is only where the alert lands.</p>'
             '<ul><li><strong>Push notification</strong>: a notification from your browser or from SNYPD added to your Home Screen. It shows up on your lock screen or desktop like a message from any other app.</li>'
             '<li><strong>Discord</strong>: a message in a chat app many resellers already keep open all day. The alert arrives as a Discord notification, on whichever device you run Discord.</li></ul>'
             '<p>Both also appear in the SNYPD dashboard, which lists every new find for your searches.</p>'),
            ('push', 'How SNYPD push alerts work',
             '<ol><li><strong>Paste a Vinted search link</strong> with your filters (brand, size, price, condition) into SNYPD.</li>'
             '<li><strong>Turn on alerts.</strong> On a computer or Android phone, allow notifications when the browser asks.</li>'
             '<li><strong>On iPhone, add SNYPD to the Home Screen first</strong> (Share, then &ldquo;Add to Home Screen&rdquo;), open SNYPD from that icon, then turn on alerts. Apple only allows web push for Home Screen apps, so in Safari alone nothing arrives. Step by step: <a href="{phone}">Vinted alerts on your phone</a>.</li></ol>'
             '<p>When several matches turn up close together, SNYPD batches them into one notification instead of buzzing you for each one. Tap it and the listing opens on Vinted; you decide whether to buy. Push needs no other account and no other app.</p>'),
            ('discord', 'How SNYPD Discord alerts work',
             '<ol><li><strong>Join the SNYPD Discord</strong> server.</li>'
             '<li><strong>Link your account</strong>: SNYPD gives you a code, and you send it with the <code>/link</code> command in the server.</li>'
             '<li><strong>Get your own thread.</strong> Your alerts arrive in a private thread in the SNYPD Discord, with an @mention so Discord notifies you.</li></ol>'
             '<p>The thread is private to your account. Your phone or computer notifies you the way Discord normally does, so your Discord notification settings decide what you hear.</p>'),
            ('who', 'Who can use which',
             '<ul><li><strong>Push and the dashboard</strong>: every plan, including Free.</li>'
             '<li><strong>Discord alerts</strong>: paid plans, the Hunt Pass and a running trial only. Free after the trial has push and the dashboard, not Discord.</li></ul>'
             '<p>Plans and prices: <a href="/plans">SNYPD plans</a>. Paid plans start at @@price:solo@@ a month.</p>'),
            ('pick', 'Which one to pick',
             '<ul><li><strong>iPhone, and you do not want to add SNYPD to your Home Screen</strong>: Discord. The Discord app notifies you without that step.</li>'
             '<li><strong>You already live in Discord</strong> (reseller groups, cook groups, friends): Discord, so your finds sit next to everything else you read.</li>'
             '<li><strong>You want nothing extra</strong>: push. No other app, no other account, and it works on Free.</li>'
             '<li><strong>You hunt from a computer at a desk</strong>: either works. Browser push needs only a click to allow notifications; Discord on desktop is handy if it is already open.</li>'
             '<li><strong>You are on Free after the trial</strong>: push, since Discord alerts need a paid plan, the Hunt Pass or a running trial.</li></ul>'),
            ('both', 'Using both',
             '<p>You do not have to choose. With Discord alerts on, push keeps working too: you can keep push on your phone and read the Discord thread on your computer, or the other way round. If two buzzes for one find is too much, turn notifications off in one place and keep the other as a record.</p>'
             '<p>Getting too many alerts on either channel? A maximum price in your Vinted search and more precise words cut the noise most. More settings: <a href="{notify}">Vinted alerts for new listings</a>. Hunting on vinted.co.uk or vinted.com? See <a href="/vinted-alerts-uk-us">Vinted alerts in the UK and US</a>.</p>'),
            ('others', 'Telegram, email and other apps',
             '<p>Other tools use Telegram or their own apps for alerts. SNYPD has no Telegram alerts and no email alerts: alerts arrive as push notifications, in the dashboard and, on the plans above, in Discord.</p>'
             '<p>Whatever the channel, SNYPD never asks for your Vinted password, never signs in to your Vinted account, never buys for you and never messages sellers. If your regular Vinted notifications stopped arriving, see <a href="{notwork}">Vinted notifications not working</a>.</p>'),
        ],
        faq=[
            ('Is Discord faster than push?',
             'SNYPD checks your search about every 30 seconds to a minute whichever channel you use. How quickly your device shows the notification depends on the device and its settings.'),
            ('Do I need Discord to use SNYPD?',
             'No. Push notifications and the dashboard need nothing else. Discord is optional, on paid plans, the Hunt Pass and a running trial.'),
            ('Why do I get no push alerts on my iPhone?',
             'On iPhone, push only works once SNYPD is added to the Home Screen and opened from that icon; then turn on alerts in the app. Step by step: <a href="{phone}">Vinted alerts on your phone</a>. If you would rather skip that, Discord alerts are an option on paid plans, the Hunt Pass and a running trial.'),
            ('Can other people see my Discord alerts?',
             'No. SNYPD sends them to a private thread for your account in the SNYPD Discord, with an @mention for you.'),
            ('Does SNYPD send alerts by Telegram or email?',
             'No. SNYPD alerts arrive as push notifications, in the dashboard and in Discord. Other tools use Telegram or their own apps.'),
        ],
        cta_h='Set up your first Vinted alert'),
  },
  # ======================================================================== UK / US (EN only, 22 Nov 2026)
  # Target: "vinted alerts uk / us". SNYPD facts = outreach/00-fact-sheet.md; Vinted statements = the 'saved' EN block.
  # No checkout-currency sentence (fact sheet says nothing). No price rating / Market Report claims for GBP or USD.
  'ukus': {
    'slugs': {'en': '/vinted-alerts-uk-us'},
    'en': dict(
        title='Vinted alerts for new listings in the UK and US | SNYPD',
        desc='How to get an alert for each new Vinted listing on vinted.co.uk or vinted.com: copy your search link, paste it into SNYPD, turn on push or Discord alerts.',
        eyebrow='VINTED ALERTS GUIDE',
        h1='How do I get alerts for new Vinted listings in the UK or the US?',
        lead='A step-by-step guide for buyers and resellers on Vinted UK (vinted.co.uk) and Vinted US (vinted.com): what Vinted itself gives you, how to set up an alert for each new listing, and how to keep the alerts useful.',
        answer='Open your search on vinted.co.uk or vinted.com with your filters, copy the link (it contains <code>/catalog?</code>) and paste it into SNYPD. SNYPD checks that search about every 30 seconds to a minute and sends a push notification, or a Discord alert on paid plans, the Hunt Pass and a running trial, when a new listing matches. On iPhone, add SNYPD to your Home Screen first. A saved search on Vinted gives you a counter, not an alert per listing.',
        toc=[('sites', 'Vinted UK and Vinted US'), ('vinted', 'What Vinted gives you'), ('setup', 'Set up an alert, step by step'),
             ('channels', 'Push or Discord'), ('tips', 'Tips for useful alerts'), ('prices', 'Plans and prices')],
        sections=[
            ('sites', 'Vinted UK and Vinted US: two separate sites',
             '<p>Vinted runs a separate site per country. In the UK it is <strong>vinted.co.uk</strong>, with prices in pounds (GBP). In the US it is <strong>vinted.com</strong>, with prices in dollars (USD).</p>'
             '<p>SNYPD watches searches on both. It works on every Vinted site in Europe and the US, 26 sites in all: you paste a search link from the site you shop on, and SNYPD watches that search on that site.</p>'),
            ('vinted', 'What Vinted gives you for new listings',
             '<p>Vinted lets you save a search: press the <strong>Save</strong> icon next to it in the search bar. Its help centre describes what you then get: a number with a plus next to the saved search, counting the new items listed since you last checked. The counter goes back to zero when you view the search.</p>'
             '<p>That counter only shows when you open the search bar. Vinted’s help on notifications lists messages for members you follow listing new items and for items you favourited (price reduced, sold), but not for new results of a saved search. More on this: <a href="{saved}">Vinted saved searches</a>.</p>'
             '<p>So if you want to hear about each new listing that matches your search, you need a tool that checks the search for you.</p>'),
            ('setup', 'Set up an alert for new listings, step by step',
             '<ol><li><strong>Open your search on vinted.co.uk or vinted.com</strong> in a browser and set your filters: brand, size, price, condition.</li>'
             '<li><strong>Copy the address</strong> from the address bar. It contains <code>/catalog?</code>. That link carries all your filters.</li>'
             '<li><strong>Paste it into SNYPD</strong> and switch the search on. All the Vinted filters in the link are kept.</li>'
             '<li><strong>Turn on alerts.</strong> On a computer or Android phone, allow notifications when the browser asks. On iPhone, add SNYPD to the Home Screen first (Share, then &ldquo;Add to Home Screen&rdquo;), open it from that icon, then turn on alerts: Apple only allows web push for Home Screen apps. Step by step: <a href="{phone}">Vinted alerts on your phone</a>.</li></ol>'
             '<p>From then on, SNYPD checks your search about every 30 seconds to a minute, on every plan. That is how often it looks, not how fast an alert reaches you: Vinted itself shows a new listing in its search minutes after it is posted. New matches appear in your SNYPD dashboard and as a notification; tap it and the listing opens on Vinted, where you decide whether to buy.</p>'
             '<p>SNYPD never asks for your Vinted password, never signs in to your Vinted account, never buys for you and never messages sellers.</p>'),
            ('channels', 'Push notifications or Discord',
             '<ul><li><strong>Push</strong>: on your phone or computer, on every plan including Free. No other app or account needed.</li>'
             '<li><strong>Discord</strong>: alerts in a private thread in the SNYPD Discord, on paid plans, the Hunt Pass and a running trial. Handy on iPhone if you would rather not add SNYPD to your Home Screen.</li></ul>'
             '<p>You can use both at once. Which to pick: <a href="/vinted-alerts-push-vs-discord">push or Discord for Vinted alerts</a>. SNYPD has no Telegram or email alerts.</p>'),
            ('tips', 'Tips for useful alerts in the UK and US',
             '<ul><li><strong>Set a maximum price in the search itself</strong>, in that site’s currency: pounds on vinted.co.uk, dollars on vinted.com. The alert follows the filters in your link.</li>'
             '<li><strong>Use precise words</strong>: a model name or reference finds fewer, better matches than a broad word.</li>'
             '<li><strong>Add size and condition filters</strong> before you copy the link, so you only hear about listings you would buy.</li>'
             '<li><strong>One search per item you hunt.</strong> If you shop on both sites, paste one link from vinted.co.uk and one from vinted.com: each search watches one site.</li></ul>'
             '<p>More settings: <a href="{notify}">Vinted alerts for new listings</a>. Regular Vinted notifications not arriving? See <a href="{notwork}">Vinted notifications not working</a>.</p>'),
            ('prices', 'Plans and prices',
             '<p>SNYPD’s plans are priced in euros. Free: your first search runs 24/7 with alerts for @@trial_days@@ days. If it finds nothing in that time, we add @@trial_ext_days@@ more days once. After that, Free runs only while the dashboard is open. Paid plans from @@price:solo@@ a month run 24/7. All plans: <a href="/plans">SNYPD plans</a>. More about SNYPD: <a href="{bot}">the Vinted bot for alerts</a>.</p>'),
        ],
        faq=[
            ('Does SNYPD work on Vinted UK and Vinted US?',
             'Yes. SNYPD watches searches on vinted.co.uk and vinted.com, and on every other Vinted site in Europe: 26 sites in all. Paste a search link from the site you shop on.'),
            ('Is there a free trial?',
             'Yes. Free: your first search runs 24/7 with alerts for @@trial_days@@ days. If it finds nothing in that time, we add @@trial_ext_days@@ more days once. No card needed.'),
            ('How fast does SNYPD check my search?',
             'About every 30 seconds to a minute, on every plan. That is how often SNYPD looks, not a catch time: Vinted shows a new listing in its search minutes after it is posted.'),
            ('Does Vinted send a notification for new items in a saved search?',
             'Its help centre describes a counter, not a notification: a number with a plus in the search bar, reset each time you view the search. For an alert per new listing, paste the search link into a tool such as <a href="{bot}">SNYPD</a>.'),
            ('Why do I get no alerts on my iPhone?',
             'On iPhone, push only works once SNYPD is added to the Home Screen and opened from that icon; then turn on alerts in the app. Step by step: <a href="{phone}">Vinted alerts on your phone</a>. Discord alerts are another option on paid plans, the Hunt Pass and a running trial.'),
        ],
        cta_h='Set up your first Vinted alert'),
  },
  # ======================================================================== Vinted sniper (EN only, 22 Nov 2026)
  # Target: "vinted sniper". SNYPD facts = outreach/00-fact-sheet.md; terms wording = gen_content.py compare FAQ / monitor page.
  # No terms URL, no section number, no rival named (coordinator, 22 Nov 2026).
  'sniper': {
    'slugs': {'en': '/vinted-sniper'},
    'en': dict(
        title='Vinted sniper: alert bot or auto-buy? What to know | SNYPD',
        desc='What a Vinted sniper is: alert bots versus auto-buy tools. SNYPD checks your searches about every 30 seconds to a minute and never logs in or buys for you.',
        eyebrow='VINTED SNIPER GUIDE',
        h1='What is a Vinted sniper, and what does it do on your account?',
        lead='Resellers say &ldquo;Vinted sniper&rdquo; for two different kinds of tool: bots that alert you to new listings, and bots that buy for you. Here is the difference, what Vinted’s terms say, and where SNYPD fits.',
        answer='A Vinted sniper is a tool that keeps checking Vinted searches and reports new listings that match them. Some only alert you; auto-buy tools also log in to your Vinted account and check out for you. SNYPD is an alert tool: it checks your search about every 30 seconds to a minute and sends you an alert, and you decide and buy yourself. It never logs in to your Vinted account, never buys and never messages sellers.',
        toc=[('meaning', 'Alert bot or auto-buy'), ('account', 'What happens on your account'), ('terms', 'What Vinted’s terms say'),
             ('speed', 'How fast a sniper is'), ('snypd', 'SNYPD as a Vinted sniper'), ('prices', 'Plans and prices')],
        sections=[
            ('meaning', 'Two meanings of &ldquo;Vinted sniper&rdquo;: alert bot or auto-buy',
             '<ul><li><strong>Alert bots</strong>, also called monitors, keep checking a Vinted search and tell you when a new listing matches. You open the listing and decide whether to buy.</li>'
             '<li><strong>Auto-buy bots</strong> go one step further: they buy or check out for you, following rules you set.</li></ul>'
             '<p>Both are called snipers because both aim at the same thing: seeing a good listing early. More on the first kind: <a href="/vinted-monitor">what is a Vinted monitor?</a></p>'),
            ('account', 'What a sniper does on your Vinted account',
             '<p>Buying on Vinted needs a logged-in account, so auto-buy tools log in to your Vinted account and check out for you. Whatever they do, they do as you.</p>'
             '<p>An alert bot has no reason to log in. SNYPD never asks for your Vinted password, never signs in to your Vinted account, never buys and never messages sellers. You get the alert, open the listing and buy it yourself through Vinted’s normal checkout.</p>'),
            ('terms', 'What Vinted’s terms say about bots',
             '<p>Vinted’s terms prohibit bots and scraping programs, so no tool can promise there is no risk. That applies to every sniper, SNYPD included. Read Vinted’s own terms in the Vinted app or on the Vinted site and decide for yourself.</p>'
             '<p>What does differ between tools is what happens on your account: an auto-buy tool acts through your logged-in Vinted account, while SNYPD never signs in as you.</p>'),
            ('speed', 'How fast is a Vinted sniper?',
             '<p>SNYPD checks your search about every 30 seconds to a minute, on every plan. That is how often it looks, not how fast an alert reaches you: Vinted itself shows a new listing in its search minutes after it is posted.</p>'
             '<p>Each tool measures its own speed in its own way, so compare like with like: <a href="/vinted-bot-comparison">Vinted bots compared</a>.</p>'),
            ('snypd', 'SNYPD as a Vinted sniper',
             '<ol><li><strong>Open your search on Vinted</strong> and set your filters: brand, size, price, condition.</li>'
             '<li><strong>Copy the link</strong> from the address bar (it contains <code>/catalog?</code>) and paste it into SNYPD.</li>'
             '<li><strong>Turn on alerts.</strong> Push notifications reach your phone or computer during the trial and on paid plans; after the trial, the Free plan checks only while the dashboard is open. On iPhone, add SNYPD to the Home Screen first. Step by step: <a href="{phone}">Vinted alerts on your phone</a>.</li></ol>'
             '<p>Discord alerts are an option on paid plans, the Hunt Pass and a running trial: <a href="/vinted-alerts-push-vs-discord">push or Discord for Vinted alerts</a>. SNYPD works on every Vinted site in Europe and the US, 26 sites in all.</p>'),
            ('prices', 'Plans and prices',
             '<p>Free: your first search runs 24/7 with alerts for @@trial_days@@ days (@@trial_hours@@ h). If it finds nothing in that time, we add @@trial_ext_days@@ more days once. After that, Free checks only while the dashboard is open. Paid plans from @@price:solo@@ a month run 24/7 with push alerts. All plans: <a href="/plans">SNYPD plans</a>. More about SNYPD: <a href="{bot}">the Vinted bot for alerts</a>.</p>'),
        ],
        faq=[
            ('Does SNYPD buy items for me?',
             'No. SNYPD alerts you to new listings; you decide and buy yourself through Vinted’s normal checkout. It never logs in to your Vinted account and never messages sellers.'),
            ('What is the difference between a Vinted sniper and an auto-buy bot?',
             'Some snipers only alert you to new listings. Auto-buy bots also log in to your Vinted account and check out for you. SNYPD is an alert tool.'),
            ('Are Vinted snipers against Vinted’s terms?',
             'Vinted’s terms prohibit bots and scraping programs, so no tool can promise there is no risk, SNYPD included. Read Vinted’s own terms in the app or on the site.'),
            ('How often does SNYPD check my search?',
             'About every 30 seconds to a minute, on every plan. That is how often SNYPD looks, not a catch time: Vinted shows a new listing in its search minutes after it is posted.'),
            ('Is there a free trial?',
             'Yes. Free: your first search runs 24/7 with alerts for @@trial_days@@ days (@@trial_hours@@ h). If it finds nothing in that time, we add @@trial_ext_days@@ more days once. No card needed.'),
        ],
        cta_h='Set up your first Vinted alert'),
  },
  # ======================================================================== FREE VINTED BOT (EN only, 22 Nov 2026)
  # Target: "free vinted bot". SNYPD facts = outreach/00-fact-sheet.md + ops/seo/data/plans.json (Free: push and
  # discord_alerts = 'trial'). Trial sentence verbatim from the fact sheet. No rival and no open-source project named.
  'freebot': {
    'slugs': {'en': '/free-vinted-bot'},
    'en': dict(
        title='Free Vinted bot: what free really gets you (2026) | SNYPD',
        desc='Free ways to watch Vinted searches: Vinted’s saved searches, open-source scripts you host, and SNYPD’s free trial and Free plan. What each one costs you.',
        eyebrow='FREE VINTED BOT',
        h1='Is there a free Vinted bot? What “free” really means',
        lead='Three free ways to keep an eye on new Vinted listings, and what each one costs you in time, upkeep or features: Vinted’s own saved searches, open-source scripts you host yourself, and SNYPD’s free trial and Free plan.',
        answer='Yes, in three forms. Vinted’s own saved searches are free but give you a “+N” counter, not a push. Open-source scripts are free software, but you run and maintain them. SNYPD: Free: your first search runs 24/7 with alerts for @@trial_days@@ days (@@trial_hours@@ h). If it finds nothing in that time, we add @@trial_ext_days@@ more days once. After that, the Free plan keeps 1 search, checked only while the dashboard is open. After the trial, push still works, but only while your dashboard is open, because only then is your search checked. 24/7 checking, and so 24/7 push, comes with the trial, paid plans and the Hunt Pass. Discord alerts need a paid plan, the Hunt Pass or a running trial. Paid plans from @@price:solo@@ / month.',
        toc=[('vinted', 'Vinted’s saved searches'), ('selfhost', 'Open-source scripts you host'), ('snypd', 'SNYPD’s trial and Free plan'),
             ('paid', 'When free is not enough'), ('choose', 'Which free option fits you')],
        sections=[
            ('vinted', 'Free option 1: Vinted’s own saved searches',
             '<p>Saving a search on Vinted costs nothing. You get a “+N” counter next to the saved search, counting new items since you last looked, and no push notification for new results. How it works in detail: <a href="{saved}">Vinted saved searches</a>.</p>'
             '<p>Good if you open Vinted several times a day anyway. Not enough if you want to hear about a new listing while you are away from the app.</p>'),
            ('selfhost', 'Free option 2: open-source scripts you host yourself',
             '<p>Some open-source projects check Vinted searches and post new listings to a chat app. The software is free; running it is your job:</p>'
             '<ul><li><strong>A server</strong> or a computer that stays on: the script stops when the machine does.</li>'
             '<li><strong>Tokens and setup</strong>: usually a bot token for the chat app it posts to, plus configuration files.</li>'
             '<li><strong>Updates</strong>: when Vinted changes something, the script can stop working until someone fixes it, and that someone may be you.</li></ul>'
             '<p>Good if you like running your own tools. Not a fit if you want something that works without upkeep.</p>'),
            ('snypd', 'Free option 3: SNYPD’s free trial and Free plan',
             '<p><strong>Free trial.</strong> Free: your first search runs 24/7 with alerts for @@trial_days@@ days (@@trial_hours@@ h). If it finds nothing in that time, we add @@trial_ext_days@@ more days once. No card needed. During the trial you get push notifications, and Discord alerts if you connect Discord (Discord alerts come with paid plans, the Hunt Pass and a running trial).</p>'
             '<p><strong>Free plan, after the trial.</strong> 1 search, no time limit, no card. It is checked only while your SNYPD dashboard is open, and new matches show in the dashboard. After the trial, push still works, but only while your dashboard is open, because only then is your search checked. 24/7 checking, and so 24/7 push, comes with the trial, paid plans and the Hunt Pass. Discord alerts need a paid plan, the Hunt Pass or a running trial.</p>'
             '<p>SNYPD checks a search about every 30 seconds to a minute, on every plan. That is how often it looks, not how fast an alert reaches you: Vinted itself shows a new listing in its search minutes after it is posted. SNYPD never asks for your Vinted password, never signs in to your Vinted account, never buys for you and never messages sellers.</p>'),
            ('paid', 'When free is not enough',
             '<p>If you want your search watched 24/7 after the trial: paid plans start at @@price:solo@@ / month, or the Hunt Pass costs @@price:pass@@ once for @@pass_days@@ days of one search, with no subscription. Both include push notifications. Discord alerts come with paid plans, the Hunt Pass and a running trial. All plans: <a href="/plans">SNYPD plans</a>. More about SNYPD: <a href="{bot}">the Vinted bot for alerts</a>.</p>'),
            ('choose', 'Which free option fits you',
             '<ul><li><strong>You check Vinted often and want nothing extra</strong>: saved searches.</li>'
             '<li><strong>You can run and maintain a server</strong>: an open-source script.</li>'
             '<li><strong>You want to try alerts without setup</strong>: SNYPD’s free trial, then the Free plan or a paid plan.</li></ul>'),
        ],
        faq=[
            ('Is there a free Vinted bot?',
             'Yes, in three forms. Vinted’s own saved searches are free and show a “+N” counter, with no push. Open-source scripts are free software that you host and maintain yourself. SNYPD has a free trial and a Free plan.'),
            ('Does SNYPD have a free trial?',
             'Free: your first search runs 24/7 with alerts for @@trial_days@@ days (@@trial_hours@@ h). If it finds nothing in that time, we add @@trial_ext_days@@ more days once. No card needed. During the trial you get push notifications, and Discord alerts if you connect Discord.'),
            ('What does SNYPD’s Free plan include after the trial?',
             '1 search, no time limit, no card, checked only while your SNYPD dashboard is open. Push still works, but only while your dashboard is open, because only then is your search checked. 24/7 checking, and so 24/7 push, comes with the trial, paid plans and the Hunt Pass. Discord alerts need a paid plan, the Hunt Pass or a running trial.'),
            ('Do Vinted saved searches send notifications?',
             'Vinted’s help centre describes a “+N” counter next to a saved search, not a push notification. More: <a href="{saved}">Vinted saved searches</a>.'),
            ('Are open-source Vinted bots really free?',
             'The software is free. You still need a server or computer that stays on, tokens and setup, and time to update the script when Vinted changes something.'),
            ('How often does SNYPD check my search?',
             'About every 30 seconds to a minute, on every plan. That is how often SNYPD looks, not a delivery time: Vinted shows a new listing in its search minutes after it is posted.'),
        ],
        cta_h='Start your free trial'),
  },
}
