"""Polish and Swedish copy: the Vinted bot page and the alert hub (18 Oct 2026).

Why these two: sign-ups already arrive from vinted.pl and vinted.se searches with no page in
their language; Google autocomplete shows "bot vinted pl", "vinted alerty", "vinted powiadomienia",
"vinted bevakning", "skapa bevakning vinted" (outreach/research-2026-10-18/autocomplete-new-markets.json).
Claude's translation, same facts as the Spanish pages (Tanush: "Poland + Sweden", 18 Oct 2026).

Vinted help quotes are verbatim from vinted.pl/help/435, vinted.se/help/435 and /433, fetched
18 Oct 2026 (outreach/research-2026-10-18/vinted-help/). Competitor facts are the ones checked on
10 Oct 2026 for the other languages (compare_data.COMPARE_CHECKED).

gen_content calls install(globals()) once; it adds 'pl' and 'sv' to the shared dicts there and in
compare_data / copy_alerts_compare, so page_notify_x() renders the alert hub unchanged, and
page_bot() hands these two languages to page_bot_pl_sv() below.
"""
G = None  # gen_content's globals, set by install()

LANGS = ('pl', 'sv')
SLUG_BOT = {'pl': '/pl/bot-vinted', 'sv': '/sv/vinted-bot'}
SLUG_NOTIFY = {'pl': '/pl/powiadomienia-vinted-nowe-ogloszenia', 'sv': '/sv/vinted-bevakning'}

# Genitive in Polish dates ("18 października 2026").
MONTHS = {'pl': ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca', 'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia'],
          'sv': ['januari', 'februari', 'mars', 'april', 'maj', 'juni', 'juli', 'augusti', 'september', 'oktober', 'november', 'december']}
SPAN_SAME = {'pl': '%d–%d %s %d', 'sv': '%d–%d %s %d'}
SPAN_TWO = {'pl': 'od %d %s do %d %s %d', 'sv': '%d %s–%d %s %d'}

SPEED_TPL = {
    'pl': 'Zmierzone w naszych własnych logach (%s, %s sprawdzeń w %d wyszukiwaniach): mediana odstępu między dwoma sprawdzeniami tego samego wyszukiwania wynosiła %d sekund, a %d%% sprawdzeń nastąpiło w ciągu 2 minut.',
    'sv': 'Uppmätt i våra egna loggar (%s, %s kontroller av %d sökningar): mediantiden mellan två kontroller av samma sökning var %d sekunder, och %d\xa0%% av kontrollerna kom inom 2 minuter.',
}
VINTED_LAG = {
    'pl': 'To częstotliwość, z jaką SNYPD sprawdza, a nie czas, w jakim ogłoszenie do ciebie dociera: sam Vinted pokazuje nowe ogłoszenie w wyszukiwarce kilka minut po jego dodaniu, dla każdego narzędzia.',
    'sv': 'Så ofta tittar SNYPD, inte så snabbt en annons når dig: Vinted visar själv en ny annons i sökningen några minuter efter att den lagts upp, för alla verktyg.',
}
TRIAL = {
    'pl': 'Przez pierwsze @@trial_days@@ dni od zapisania pierwszego wyszukiwania plan Free działa 24/7 z powiadomieniami, jak plan płatny.',
    'sv': 'Under de första @@trial_days@@ dagarna efter att du sparat din första sökning körs Free dygnet runt med notiser, som ett betalt abonnemang.',
}


def ui(discord):
    return {
        'pl': dict(locale='pl_PL', toc='NA TEJ STRONIE', updated='Zaktualizowano', by='SNYPD, tworzony przez belgijskiego resellera sneakersów',
                   nav=[('bot', 'BOT VINTED'), ('/plans', 'CENY'), (discord, 'DISCORD')],
                   login='ZALOGUJ', start='ZACZNIJ',
                   foot_tag='SNYPD &middot; NIEPOWIĄZANY Z VINTED', foot_t='Czyta tylko publiczne ogłoszenia.',
                   foot=[('bot', 'Bot Vinted'), ('notify', 'Powiadomienia Vinted o nowych ogłoszeniach'), ('notwork', 'Powiadomienia Vinted nie działają'),
                         ('compare', 'Porównanie botów Vinted'), ('/vinted-price-guide', 'Ceny na Vinted (EN)'), ('monitor', 'Monitor Vinted'), ('fees', 'Opłaty Vinted'),
                         ('/faq', 'FAQ (EN)'), ('/support', 'Pomoc (EN)'), (discord, 'Discord')],
                   legal='<a href="/privacy">Prywatność</a><a href="/terms">Regulamin</a><a href="mailto:snypd@gmail.com">Kontakt</a><a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Ustawienia cookies</a>',
                   home='Strona główna'),
        'sv': dict(locale='sv_SE', toc='PÅ DEN HÄR SIDAN', updated='Uppdaterad', by='Av SNYPD, byggt av en belgisk sneakerreseller',
                   nav=[('bot', 'VINTED BOT'), ('/plans', 'PRISER'), (discord, 'DISCORD')],
                   login='LOGGA IN', start='KOM IGÅNG',
                   foot_tag='SNYPD &middot; INTE KOPPLAT TILL VINTED', foot_t='Läser bara offentliga annonser.',
                   foot=[('bot', 'Vinted bot'), ('notify', 'Vinted bevakning'), ('notwork', 'Vinted-notiser fungerar inte'), ('saved', 'Sparade sökningar på Vinted'), ('saved', 'Zapisane wyszukiwania Vinted'), ('compare', 'Vinted botar jämförda'),
                         ('/vinted-price-guide', 'Vinted-priser (EN)'), ('monitor', 'Vinted monitor'), ('fees', 'Vinted-avgifter'),
                         ('/faq', 'FAQ (EN)'), ('/support', 'Support (EN)'), (discord, 'Discord')],
                   legal='<a href="/privacy">Integritet</a><a href="/terms">Villkor</a><a href="mailto:snypd@gmail.com">Kontakt</a><a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Cookie-inställningar</a>',
                   home='Start'),
    }


CTA = {
    'pl': ('<div class="lg-box lg-mint"><p><strong>Zacznij za darmo od jednego wyszukiwania.</strong> Bez karty, bez limitu czasu, bez limitu powiadomień. Przez pierwsze @@trial_days@@ dni działa 24/7 z powiadomieniami. '
           'Przejdź na plan płatny, gdy chcesz, żeby wyszukiwanie działało także przy zamkniętym panelu.</p>'
           '<p class="ct-note">Rejestracja i płatność są na razie po angielsku. Ceny planów są w euro.</p>'
           '<div class="ct-actions"><a class="ct-btn" href="/signup">ZACZNIJ ZA DARMO</a>'
           '<a class="ct-btn ct-ghost" href="/plans">ZOBACZ PLANY</a></div></div>'),
    'sv': ('<div class="lg-box lg-mint"><p><strong>Börja gratis med en sökning.</strong> Inget kort, ingen tidsgräns, ingen gräns för notiser. De första @@trial_days@@ dagarna körs den dygnet runt med notiser. '
           'Uppgradera när du vill att sökningen ska fortsätta med panelen stängd.</p>'
           '<p class="ct-note">Registrering och betalning är på engelska tills vidare. Abonnemangen kostar i euro.</p>'
           '<div class="ct-actions"><a class="ct-btn" href="/signup">BÖRJA GRATIS</a>'
           '<a class="ct-btn ct-ghost" href="/plans">SE ABONNEMANG</a></div></div>'),
}

PLANS_ROWS = {
    'pl': [['Free', '<span class="ct-num">@@price:free@@</span>', '@@searches:free@@', 'Pierwsze @@trial_days@@ dni, potem tylko przy otwartym panelu', 'Nie'],
           ['Solo', '<span class="ct-num">@@price:solo@@</span>', '@@searches:solo@@', 'Tak, 24/7', 'Nie'],
           ['Kickstart', '<span class="ct-num">@@price:kickstart@@</span>', '@@searches:kickstart@@', 'Tak, 24/7', 'Nie'],
           ['Pro', '<span class="ct-num">@@price:pro@@</span>', '@@searches:pro@@', 'Tak, 24/7', 'Tak'],
           ['Elite', '<span class="ct-num">@@price:elite@@</span>', '@@searches:elite@@', 'Tak, 24/7', 'Tak']],
    'sv': [['Free', '<span class="ct-num">@@price:free@@</span>', '@@searches:free@@', 'Första @@trial_days@@ dagarna, sedan bara med panelen öppen', 'Nej'],
           ['Solo', '<span class="ct-num">@@price:solo@@</span>', '@@searches:solo@@', 'Ja, dygnet runt', 'Nej'],
           ['Kickstart', '<span class="ct-num">@@price:kickstart@@</span>', '@@searches:kickstart@@', 'Ja, dygnet runt', 'Nej'],
           ['Pro', '<span class="ct-num">@@price:pro@@</span>', '@@searches:pro@@', 'Ja, dygnet runt', 'Ja'],
           ['Elite', '<span class="ct-num">@@price:elite@@</span>', '@@searches:elite@@', 'Ja, dygnet runt', 'Ja']],
}
PLANS_HEAD = {'pl': ['PLAN', 'MIESIĘCZNIE, Z VAT', 'AKTYWNE WYSZUKIWANIA', 'SPRAWDZA PRZY ZAMKNIĘTYM PANELU', 'MARKET REPORT'],
              'sv': ['ABONNEMANG', 'PER MÅNAD, INKL. MOMS', 'AKTIVA SÖKNINGAR', 'BEVAKAR MED PANELEN STÄNGD', 'MARKET REPORT']}

SHOT_FEED = {
    'pl': ('Panel SNYPD z nowymi ogłoszeniami z Vinted: cena, cena z Ochroną Kupujących, stan i czas znalezienia',
           'Feed SNYPD podczas prawdziwej sesji 2 października 2026: nowe ogłoszenia z jednego wyszukiwania, każde z ceną, ceną z Ochroną Kupujących Vinted, stanem i momentem znalezienia. Zdjęcia są rozmyte, bo należą do sprzedających. Interfejs po angielsku.'),
    'sv': ('SNYPD-panelen med nya annonser från Vinted: pris, pris med Köparskydd, skick och när annonsen hittades',
           'SNYPD-flödet under en riktig session den 2 oktober 2026: nya annonser från en sökning, var och en med pris, pris inklusive Vinteds Köparskydd, skick och när den hittades. Bilderna är suddade eftersom de tillhör säljarna. Gränssnittet är på engelska.'),
}

# ------------------------------------------------------------------ alert hub data (page_notify_x)
COMPARE_CHECKED = {'pl': '10 października 2026', 'sv': '10 oktober 2026'}
HELP435 = {'pl': 'https://www.vinted.pl/help/435', 'sv': 'https://www.vinted.se/help/435'}
HELP433 = {'pl': 'https://www.vinted.pl/help/433', 'sv': 'https://www.vinted.se/help/433'}
HELP435_QUOTE = {
    'pl': 'zobaczysz liczbę poprzedzoną plusem, która wskaże, ile nowych przedmiotów z tej kategorii dodano od twojego ostatniego wyszukiwania',
    'sv': 'ser du ett nummer med ett plustecken som anger hur många nya artiklar som annonserats sedan du senast kontrollerade sökningen',
}
HELP435_TITLE = {'pl': 'Jak zapisać wyszukiwanie', 'sv': 'Spara dina sökningar'}
ALERT_WAYS_HEAD = {'pl': ['SPOSÓB', 'CO DOSTAJESZ', 'JAK DO CIEBIE DOCIERA', 'KOSZT', 'ŹRÓDŁO'],
                   'sv': ['SÄTT', 'VAD DU FÅR', 'HUR DET NÅR DIG', 'KOSTNAD', 'KÄLLA']}
SOURCE_WORD = {'pl': 'strona narzędzia', 'sv': 'egen webbplats'}
VINTED_HELP_WORD = {'pl': 'pomoc Vinted', 'sv': 'Vinteds hjälp'}
_FREE = {'pl': 'Za darmo', 'sv': 'Gratis'}
_APP_MAIL = {'pl': 'Własna aplikacja (iOS, Android) i e-mail', 'sv': 'Egen app (iOS, Android) och e-post'}
_M = {'pl': '&nbsp;/ mies.', 'sv': '&nbsp;/ mån.'}
# Cells per row of compare_data.ALERT_WAYS, matched by the English name (prices as checked 10 Oct 2026).
WAY_CELLS = {
    'Vinted saved searches': dict(
        name={'pl': 'Zapisane wyszukiwania Vinted', 'sv': 'Sparade sökningar på Vinted'},
        get={'pl': 'Licznik „+N” nowych przedmiotów przy następnym otwarciu paska wyszukiwania', 'sv': 'En räknare ”+N” med nya artiklar nästa gång du öppnar sökfältet'},
        how={'pl': 'W aplikacji, bez push', 'sv': 'I appen, ingen push'}, cost=_FREE),
    'Following a seller on Vinted': dict(
        name={'pl': 'Obserwowanie użytkownika na Vinted', 'sv': 'Följa en medlem på Vinted'},
        get={'pl': 'Powiadomienie, gdy ten użytkownik doda nowe ogłoszenie', 'sv': 'En notis när medlemmen laddar upp en ny artikel'},
        how={'pl': 'Powiadomienia Vinted', 'sv': 'Vinteds notiser'}, cost=_FREE),
    'InstantAlert': dict(
        get={'pl': 'Nowe ogłoszenia dla twoich alertów', 'sv': 'Nya annonser för dina bevakningar'}, how=_APP_MAIL,
        cost={'pl': '4,99&ndash;27,99&nbsp;&euro;' + _M['pl'] + '; 3 alerty za darmo przez 3 dni',
              'sv': '4,99&ndash;27,99&nbsp;&euro;' + _M['sv'] + '; 3 bevakningar gratis i 3 dagar'}),
    'Vinotify': dict(
        get={'pl': 'Nowe ogłoszenia i obniżki cen', 'sv': 'Nya annonser och prissänkningar'}, how=_APP_MAIL,
        cost={'pl': '2,99&ndash;22,99&nbsp;&euro;' + _M['pl'] + '; za darmo: 1 wyszukiwanie sprawdzane raz dziennie',
              'sv': '2,99&ndash;22,99&nbsp;&euro;' + _M['sv'] + '; gratis: 1 sökning som kontrolleras dagligen'}),
    'Clothing Alerts': dict(
        get={'pl': 'Nowe ogłoszenia dla zapisanych wyszukiwań', 'sv': 'Nya annonser för sparade sökningar'},
        how={'pl': 'Własna aplikacja (iOS, Android)', 'sv': 'Egen app (iOS, Android)'},
        cost={'pl': 'Za darmo z reklamami; opcje płatne, ceny nie podane', 'sv': 'Gratis med reklam; betalda alternativ, priser anges inte'}),
    'Telvin Bot': dict(
        get={'pl': 'Nowe ogłoszenia dla alertów na słowa kluczowe', 'sv': 'Nya annonser för sökordsbevakningar'},
        how={'pl': 'Telegram', 'sv': 'Telegram'},
        cost={'pl': '4,90&ndash;14,90&nbsp;&euro;' + _M['pl'] + '; za darmo: 1 alert, 100 powiadomień',
              'sv': '4,90&ndash;14,90&nbsp;&euro;' + _M['sv'] + '; gratis: 1 bevakning, 100 notiser'}),
    'Resell Reserve': dict(
        get={'pl': 'Ogłoszenia na kanałach według typu przedmiotu, plus autobuy', 'sv': 'Annonser i kanaler per typ av artikel, plus autobuy'},
        how={'pl': 'Discord', 'sv': 'Discord'},
        cost={'pl': '19,99&ndash;44,99&nbsp;&pound;' + _M['pl'], 'sv': '19,99&ndash;44,99&nbsp;&pound;' + _M['sv']}),
    'SNYPD': dict(
        get={'pl': 'Każde nowe ogłoszenie z wklejonego linku wyszukiwania Vinted, ze wszystkimi filtrami', 'sv': 'Varje ny annons för söklänken från Vinted som du klistrar in, med alla filter'},
        how={'pl': 'Push na telefon i komputer, bez sklepu z aplikacjami', 'sv': 'Push till mobil och dator, ingen appbutik'},
        cost={'pl': 'Za darmo: 1 wyszukiwanie, 7 dni 24/7; płatnie od @@price:solo@@ / mies.', 'sv': 'Gratis: 1 sökning, dygnet runt i 7 dagar; betalt från @@price:solo@@ / mån.'}),
}

PUSH = {
    'pl': dict(h='Włącz powiadomienia push', ios='Na iPhonie lub iPadzie', android='Na Androidzie', desk='Na komputerze',
               ios_steps=['Otwórz snypd.store w <strong>Safari</strong> i zaloguj się.', 'Stuknij <strong>Udostępnij</strong>, a potem <strong>Do ekranu początkowego</strong>.',
                          'Otwórz SNYPD z nowej ikony na ekranie początkowym.', 'Stuknij <strong>Enable alerts</strong> (przycisk jest na razie po angielsku) i zezwól na powiadomienia.'],
               android_steps=['Otwórz snypd.store w <strong>Chrome</strong> i zaloguj się.', 'Stuknij <strong>Enable alerts</strong> i zezwól na powiadomienia.',
                              'Opcjonalnie: w menu Chrome stuknij <strong>Dodaj do ekranu głównego</strong>, żeby otwierać SNYPD jednym stuknięciem.'],
               desk_p='Chrome, Edge, Firefox i Safari na Macu działają bezpośrednio w przeglądarce: zaloguj się, kliknij <strong>Enable alerts</strong> i zezwól na powiadomienia.',
               why='Apple pozwala na powiadomienia web tylko aplikacjom webowym dodanym do ekranu początkowego; dlatego iPhone wymaga dodatkowego kroku.'),
    'sv': dict(h='Slå på pushnotiser', ios='På iPhone eller iPad', android='På Android', desk='På datorn',
               ios_steps=['Öppna snypd.store i <strong>Safari</strong> och logga in.', 'Tryck på <strong>Dela</strong> och sedan <strong>Lägg till på hemskärmen</strong>.',
                          'Öppna SNYPD från den nya symbolen på hemskärmen.', 'Tryck på <strong>Enable alerts</strong> (knappen är på engelska än så länge) och tillåt notiser.'],
               android_steps=['Öppna snypd.store i <strong>Chrome</strong> och logga in.', 'Tryck på <strong>Enable alerts</strong> och tillåt notiser.',
                              'Valfritt: tryck på <strong>Lägg till på startskärmen</strong> i Chromes meny för att öppna SNYPD med ett tryck.'],
               desk_p='Chrome, Edge, Firefox och Safari på Mac fungerar direkt i webbläsaren: logga in, klicka på <strong>Enable alerts</strong> och tillåt notiser.',
               why='Apple tillåter webbnotiser bara för webbappar som lagts till på hemskärmen; därför kräver iPhone ett extra steg.'),
}

WAYS = {
    'pl': dict(h='Wszystkie sposoby na alert z Vinted', intro='Co wysyła każda opcja i jak do ciebie dociera, według centrum pomocy Vinted i strony każdego narzędzia, sprawdzone {date}:',
               note='Ceny miesięczne, chyba że podano inaczej; zmieniają się, więc sprawdź je przed zapłatą. Szybkość celowo pomijamy, bo każdy dostawca mierzy ją po swojemu. Wszystkie narzędzia obok siebie: <a href="{compare}">porównanie botów Vinted</a> (po angielsku).'),
    'sv': dict(h='Alla sätt att få bevakning på Vinted', intro='Vad varje alternativ skickar och hur det når dig, enligt Vinteds hjälpcenter och varje verktygs egen webbplats, kontrollerat {date}:',
               note='Priser per månad om inget annat anges, och de ändras: kontrollera innan du betalar. Hastighet utelämnas med avsikt, eftersom varje leverantör mäter på sitt eget sätt. Alla verktyg sida vid sida: <a href="{compare}">jämförelse av Vinted botar</a> (på engelska).'),
}

NOTIFY = {
    'pl': dict(
        title='Powiadomienia Vinted o nowych ogłoszeniach: jak je dostać (2026) | SNYPD',
        desc='Zapisane wyszukiwania Vinted pokazują tylko licznik +N. Co mówi pomoc Vinted, które aplikacje i boty powiadamiają i jak dostać push przy każdym nowym ogłoszeniu.',
        eyebrow='POWIADOMIENIA VINTED', h1='Powiadomienie, gdy na Vinted pojawi się nowy przedmiot',
        lead='Vinted zapisuje twoje wyszukiwania, ale według jego centrum pomocy nie wysyła powiadomień o nowych wynikach. Oto co dokładnie robi Vinted, jakie są inne sposoby i jak dostać push na telefon przy każdym nowym pasującym ogłoszeniu.',
        toc=[('odpowiedz', 'Krótka odpowiedź'), ('vinted', 'Co robi Vinted'), ('sposoby', 'Wszystkie sposoby'), ('wystarczy', 'Kiedy wystarczy'), ('alerty', 'Prawdziwe alerty'), ('push', 'Włącz push'), ('pytania', 'Pytania')],
        h_answer='Krótka odpowiedź',
        answer='Zapisane wyszukiwania Vinted pokazują licznik, a nie powiadomienie. Według pomocy Vinted przy następnym otwarciu paska wyszukiwania obok zapisanego wyszukiwania widzisz liczbę z plusem („+N”) dla nowych przedmiotów; licznik zeruje się, gdy obejrzysz wyniki. Vinted nie opisuje powiadomienia push o każdym nowym wyniku: do tego potrzebujesz narzędzia, które sprawdza wyszukiwanie za ciebie.',
        h_vinted='Co robią zapisane wyszukiwania Vinted',
        vinted_intro='Pomoc Vinted opisuje to tak: następnym razem po kliknięciu paska wyszukiwania',
        cite='Pomoc Vinted',
        bullets=['Możesz zapisać nieograniczoną liczbę wyszukiwań.', 'Licznik zeruje się za każdym razem, gdy obejrzysz wyniki wyszukiwania.', 'Zapisane wyszukiwania znikają po 6 miesiącach, jeśli ani razu ich nie otworzysz.'],
        follow='Vinted wysyła powiadomienia m.in. wtedy, gdy obserwowani użytkownicy dodadzą nowe ogłoszenia oraz gdy polubiony przedmiot stanieje albo zostanie sprzedany (<a href="{h433}" rel="nofollow noopener">pomoc Vinted</a>). Nowych wyników zapisanego wyszukiwania nie ma na tej liście.',
        h_enough='Kiedy wystarczą funkcje Vinted',
        enough=['Otwierasz aplikację kilka razy dziennie: licznik mówi ci, gdzie zajrzeć.', 'Chcesz nowe przedmioty konkretnego użytkownika: zaobserwuj go, a Vinted da ci znać.',
                'Czekasz na obniżkę ceny jednego przedmiotu: polub go, a Vinted powiadomi cię, gdy stanieje.'],
        h_alerts='Kiedy potrzebujesz prawdziwych alertów',
        alerts_intro='Resellerzy tracą najlepsze okazje zwykle między dwoma spojrzeniami na licznik. Narzędzie do alertów sprawdza wyszukiwanie za ciebie i daje znać, gdy tylko pojawi się coś nowego i pasującego. W SNYPD to to samo wyszukiwanie, które masz na Vinted:',
        steps=['Otwórz wyszukiwanie na Vinted w przeglądarce, z filtrami (marka, rozmiar, cena, stan).', 'Skopiuj adres z paska przeglądarki. Zawiera <code>/catalog?</code>.',
               'Wklej go do SNYPD i włącz wyszukiwanie.', 'SNYPD sprawdza je mniej więcej co 30 sekund i wysyła push na telefon albo komputer, gdy tylko pojawi się nowe pasujące ogłoszenie. Powiadomienie otwiera ogłoszenie na Vinted.'],
        after='SNYPD nigdy nie prosi o hasło do Vinted, niczego nie kupuje i nie pisze do sprzedających. Plan darmowy sprawdza jedno wyszukiwanie: przez pierwsze 7 dni 24/7, potem gdy masz otwarty panel; plany płatne od @@price:solo@@ miesięcznie sprawdzają 24/7. Więcej: <a href="{bot}">SNYPD, bot Vinted do powiadomień</a>.',
        faq=[('Czy Vinted powiadamia mnie o nowych przedmiotach z zapisanego wyszukiwania?',
              'Według pomocy Vinted nie przez push: widzisz licznik „+N” przy następnym otwarciu paska wyszukiwania. Vinted opisuje powiadomienia o obserwowanych użytkownikach, polubionych przedmiotach, wiadomościach i opiniach.'),
             ('Czy jest darmowy sposób?',
              'Tak, z ograniczeniami. Według ich własnych stron, sprawdzonych {date}: SNYPD Free sprawdza 1 wyszukiwanie bez limitu czasu, przez pierwsze 7 dni 24/7, a potem gdy panel jest otwarty; Vinotify ma darmowy plan z 1 wyszukiwaniem sprawdzanym raz dziennie; Telvin Bot daje 1 alert na słowo kluczowe ze 100 powiadomieniami na Telegramie.'),
             ('Czy potrzebuję aplikacji ze sklepu?',
              'Do SNYPD nie: działa w przeglądarce i wysyła powiadomienia web. Na iPhonie dodajesz SNYPD raz do ekranu początkowego, bo tylko tak Apple pozwala na powiadomienia web.'),
             ('Dlaczego nie dostaję powiadomień z Vinted?',
              'Najczęściej powiadomienia push Vinted są wyłączone w aplikacji albo w ustawieniach telefonu, albo działa dzienny limit powiadomień, który Vinted pozwala ustawić (pomoc Vinted). Sprawdź ustawienia powiadomień push w aplikacji Vinted i zgodę na powiadomienia od Vinted w telefonie. Pamiętaj też, że nowe wyniki zapisanego wyszukiwania pojawiają się jako licznik, a nie jako push.')],
        h_faq='Częste pytania', h_start='Wypróbuj na jednym wyszukiwaniu'),
    'sv': dict(
        title='Vinted bevakning av nya annonser: så får du notiser (2026) | SNYPD',
        desc='Sparade sökningar på Vinted visar bara en räknare +N. Vad Vinteds hjälp säger, vilka appar och botar som skickar notiser och hur du får en push för varje ny annons.',
        eyebrow='VINTED BEVAKNING', h1='Få en notis när en ny artikel läggs upp på Vinted',
        lead='Vinted sparar dina sökningar, men enligt hjälpcentret skickar det inga notiser om nya träffar. Här är exakt vad Vinted gör, vilka andra sätt som finns och hur du får en push i mobilen för varje ny annons som matchar.',
        toc=[('svar', 'Kort svar'), ('vinted', 'Vad Vinted gör'), ('satt', 'Alla sätt'), ('racker', 'När det räcker'), ('bevakning', 'Riktig bevakning'), ('push', 'Slå på push'), ('fragor', 'Frågor')],
        h_answer='Kort svar',
        answer='Sparade sökningar på Vinted visar en räknare, inte en notis. Enligt Vinteds hjälp ser du nästa gång du öppnar sökfältet ett nummer med ett plustecken (”+N”) bredvid den sparade sökningen för nya artiklar; räknaren nollställs när du tittar. Vinted beskriver ingen pushnotis för varje ny träff: för det behöver du ett verktyg som kontrollerar sökningen åt dig.',
        h_vinted='Vad sparade sökningar på Vinted gör',
        vinted_intro='Vinteds hjälp förklarar det så här: nästa gång du besöker sökfältet',
        cite='Vinteds hjälp',
        bullets=['Du kan spara ett obegränsat antal sökningar.', 'Räknaren nollställs varje gång du visar sökningen.', 'Sparade sökningar försvinner efter sex månader om du aldrig öppnar dem.'],
        follow='Vinted skickar notiser bland annat när medlemmar du följer laddar upp nya artiklar och när en artikel du favoritmarkerat sänks i pris eller säljs (<a href="{h433}" rel="nofollow noopener">Vinteds hjälp</a>). Nya träffar i en sparad sökning finns inte med bland dem.',
        h_enough='När Vinteds funktioner räcker',
        enough=['Du öppnar appen flera gånger om dagen: räknaren visar var du ska titta.', 'Du vill ha nya artiklar från en viss medlem: följ medlemmen så meddelar Vinted dig.',
                'Du väntar på att en artikel ska sänkas i pris: favoritmarkera den så meddelar Vinted dig när priset sänks.'],
        h_alerts='När du behöver riktig bevakning',
        alerts_intro='Den som säljer vidare missar oftast de bästa fynden mellan två kontroller av räknaren. Ett bevakningsverktyg kontrollerar sökningen åt dig och säger till så fort något nytt matchar. Med SNYPD är det samma sökning som du har på Vinted:',
        steps=['Öppna sökningen på Vinted i webbläsaren, med dina filter (märke, storlek, pris, skick).', 'Kopiera adressen i adressfältet. Den innehåller <code>/catalog?</code>.',
               'Klistra in den i SNYPD och slå på sökningen.', 'SNYPD kontrollerar den ungefär var 30:e sekund och skickar en push till mobilen eller datorn så fort en ny annons matchar. Notisen öppnar annonsen på Vinted.'],
        after='SNYPD frågar aldrig efter ditt Vinted-lösenord, köper ingenting och skriver inte till säljare. Gratisplanen kontrollerar en sökning: dygnet runt de första 7 dagarna, sedan medan din panel är öppen; betalda abonnemang från @@price:solo@@ i månaden kontrollerar dygnet runt. Mer: <a href="{bot}">SNYPD, Vinted boten för bevakning</a>.',
        faq=[('Meddelar Vinted mig om nya artiklar i en sparad sökning?',
              'Enligt Vinteds hjälp inte med en push: du ser en räknare ”+N” nästa gång du öppnar sökfältet. Vinted beskriver notiser för medlemmar du följer, favoritmarkerade artiklar, meddelanden och omdömen.'),
             ('Finns det ett gratis sätt?',
              'Ja, med begränsningar. Enligt deras egna webbplatser, kontrollerade {date}: SNYPD Free kontrollerar 1 sökning utan tidsgräns, dygnet runt de första 7 dagarna och sedan medan panelen är öppen; Vinotify har en gratisplan med 1 sökning som kontrolleras en gång om dagen; Telvin Bot ger 1 sökordsbevakning med 100 notiser i Telegram.'),
             ('Behöver jag en app från appbutiken?',
              'Inte för SNYPD: det fungerar i webbläsaren och skickar webbnotiser. På iPhone lägger du till SNYPD på hemskärmen en gång, eftersom Apple bara tillåter webbnotiser så.'),
             ('Varför får jag inga notiser från Vinted?',
              'Oftast är Vinteds pushnotiser avstängda i appen eller i telefonens inställningar, eller så har du nått den dagliga gränsen för notiser som Vinted låter dig ställa in (Vinteds hjälp). Kontrollera notisinställningarna i Vinted-appen och att telefonen tillåter notiser från Vinted. Kom också ihåg att nya träffar i en sparad sökning visas som en räknare, inte som en push.')],
        h_faq='Vanliga frågor', h_start='Prova med en sökning'),
}


# ------------------------------------------------------------------ Vinted bot page
def _bot_copy(lang):
    S, L, T = G['SPEED_MEASURED'][lang], G['VINTED_LAG'][lang], G['TRIAL'][lang]
    compare_en, monitor_en, notify = G['SLUGS']['compare']['en'], G['SLUGS']['monitor']['en'], G['href']('notify', lang)
    if lang == 'pl':
        faq = [
            ('Czy SNYPD kupuje za mnie?', 'Nie. SNYPD znajduje nowe ogłoszenia i cię powiadamia. Otwierasz ogłoszenie na Vinted i sam kupujesz albo składasz ofertę, przez zwykłą płatność Vinted.'),
            ('Czy muszę podać SNYPD hasło do Vinted?', 'Nie. SNYPD nigdy nie prosi o dane logowania do Vinted i nigdy nie loguje się na twoje konto. Do konta SNYPD potrzebujesz tylko adresu e-mail.'),
            ('Czy Vinted sam nie powiadamia o nowych ogłoszeniach?', 'Według centrum pomocy Vinted zapisane wyszukiwanie pokazuje liczbę z plusem („+N”) przy następnym otwarciu paska wyszukiwania, a licznik zeruje się, gdy obejrzysz wyniki. Vinted wysyła powiadomienia m.in. wtedy, gdy obserwowany użytkownik doda nowe ogłoszenie. SNYPD sprawdza twoje wyszukiwanie mniej więcej co 30 sekund i wysyła push przy nowych pasujących ogłoszeniach. Szczegóły: <a href="%s">powiadomienia Vinted o nowych ogłoszeniach</a>.' % notify),
            ('Jak często SNYPD sprawdza moje wyszukiwanie?', 'Mniej więcej co 30 sekund. ' + S + ' Spokojne wyszukiwania zwalniają, maksymalnie do 5 minut. Tempo jest takie samo we wszystkich planach.'),
            ('Czy działa na iPhonie?', 'Tak, gdy SNYPD jest na ekranie początkowym: otwórz snypd.store w Safari, stuknij Udostępnij, potem „Do ekranu początkowego”, i włącz powiadomienia w zainstalowanej aplikacji. Apple pozwala na powiadomienia web tylko w aplikacjach z ekranu początkowego. Na Androidzie, Windowsie i Macu powiadomienia działają prosto z przeglądarki.'),
            ('Czy jest darmowy plan?', 'Tak. Free obejmuje jedno wyszukiwanie, bez limitu czasu i bez karty. ' + T + ' Potem sprawdza, gdy masz otwarty panel SNYPD; plany płatne od @@price:solo@@ miesięcznie sprawdzają 24/7, także przy zamkniętym panelu.'),
            ('Czy działa z vinted.pl?', 'Tak. SNYPD działa ze wszystkimi serwisami Vinted w Europie i USA, łącznie 26, w tym vinted.pl, vinted.cz, vinted.lt, vinted.de i vinted.fr. Wklej link do wyszukiwania z serwisu, na którym kupujesz; ceny pojawiają się w walucie tego serwisu, na vinted.pl w złotych.'),
        ]
        body = f"""
<section id="podsumowanie">
  <h2>SNYPD w jednym akapicie</h2>
  <div class="lg-box lg-mint"><p>SNYPD to bot Vinted do powiadomień, nazywany też monitorem Vinted, dla resellerów. Wklejasz link do wyszukiwania na Vinted ze swoimi filtrami (marka, rozmiar, cena, stan), a SNYPD sprawdza to wyszukiwanie mniej więcej co 30 sekund. Gdy pojawi się nowe pasujące ogłoszenie, trafia do twojego panelu, a ty dostajesz powiadomienie push na telefon albo komputer. SNYPD nigdy nie prosi o hasło do Vinted, nigdy nie loguje się na twoje konto, niczego nie kupuje i nie pisze do sprzedających. Plan darmowy obsługuje jedno wyszukiwanie: 24/7 przez pierwsze 7 dni, potem tak długo, jak masz otwarty panel. Plany płatne, od @@price:solo@@ miesięcznie, pilnują 24/7.</p></div>
</section>
<section id="rodzaje">
  <h2>Trzy rodzaje botów Vinted</h2>
  <p>„Bot Vinted” to nazwa narzędzi, które robią bardzo różne rzeczy. Najważniejsza różnica: czy działają przez twoje konto Vinted?</p>
  <h3>BOTY POWIADOMIEŃ, CZYLI MONITORY VINTED</h3>
  <p>Pilnują twoich wyszukiwań i dają znać, gdy pojawi się coś nowego; resellerzy nazywają je też monitorami. Kupujesz sam, więc nie muszą niczego robić przez twoje konto Vinted. SNYPD, Telvin Bot i Crazed to narzędzia do powiadomień.</p>
  <h3>BOTY AUTOBUY I AUTOCOP</h3>
  <p>Kupują albo płacą za ciebie. Zakup na Vinted wymaga zalogowanego konta, więc te narzędzia działają przez twoje; V-Tools na przykład podaje, że podłączasz własne konta Vinted. Souk, V-Tools i Resell Reserve sprzedają funkcje autobuy.</p>
  <h3>SKRYPTY DO SAMODZIELNEGO URUCHOMIENIA</h3>
  <p>Projekty open source z GitHuba, które uruchamiasz sam i które zwykle wysyłają wyniki na Discorda albo Telegrama. Darmowe, ale serwerem zarządzasz ty i to ty go naprawiasz, gdy Vinted coś zmieni.</p>
  <p>Ceny, kanały powiadomień i darmowe plany każdego narzędzia obok siebie: <a href="{compare_en}">porównanie botów Vinted</a> (po angielsku). Jak działa monitor krok po kroku: <a href="{monitor_en}">czym jest monitor Vinted?</a> (po angielsku)</p>
</section>
<section id="automatyzacja">
  <h2>Automatyzacja Vinted: strona kupującego, nie sprzedającego</h2>
  <p>„Automatyzacja Vinted” to zwykle narzędzia dla sprzedających: ponownie wystawiają albo podbijają twoje przedmioty, wysyłają oferty osobom, które dodały je do ulubionych, albo piszą opisy. Działają na twoich własnych ogłoszeniach, więc działają przez twoje konto Vinted.</p>
  <p>SNYPD automatyzuje tylko stronę kupującego: pilnuje wyszukiwań i mówi ci, co jest nowe. Nie dotyka twoich ogłoszeń ani wiadomości i nigdy się nie loguje. Jeśli chcesz podbijać albo ponownie wystawiać własne ogłoszenia, SNYPD nie jest do tego narzędziem.</p>
</section>
<section id="jak-dziala">
  <h2>Jak działa SNYPD</h2>
  <ol>
    <li>W przeglądarce wyszukaj na swoim Vinted (na przykład vinted.pl) i ustaw filtry: marka, rozmiar, cena, stan.</li>
    <li>Skopiuj adres z paska przeglądarki. Adres wyszukiwania zawiera <code>/catalog?</code>.</li>
    <li>Wklej go do SNYPD, nadaj krótką nazwę i włącz.</li>
    <li>SNYPD sprawdza je mniej więcej co 30 sekund. Nowe wyniki trafiają do twojego panelu, a jeśli włączysz powiadomienia, także na telefon albo komputer. Kilka znalezisk w krótkim czasie przychodzi w jednym powiadomieniu.</li>
    <li>Stuknij powiadomienie. Otworzy ogłoszenie na Vinted, gdzie kupujesz albo składasz ofertę.</li>
  </ol>
  {G['figure']('feed', 'pl')}
</section>
<section id="szybkosc">
  <h2>Jak szybko to działa?</h2>
  <p>SNYPD sprawdza każde aktywne wyszukiwanie mniej więcej co 30 sekund. {S} {L} Wyszukiwania, które często znajdują nowe przedmioty, utrzymują to tempo; te, które ucichną, są sprawdzane rzadziej, maksymalnie co około 5 minut, i przyspieszają, gdy tylko coś znajdą. Tempo jest takie samo we wszystkich planach: płacąc, dostajesz więcej wyszukiwań i pilnowanie 24/7, a nie szybsze sprawdzanie.</p>
  <p>Niektóre narzędzia reklamują powiadomienia w milisekundach. SNYPD tego nie obiecuje. Obiecuje coś innego: płatne wyszukiwanie działa dalej, gdy laptop jest zamknięty, a telefon w kieszeni, czyli wtedy, gdy przepada najwięcej okazji.</p>
</section>
<section id="cena">
  <h2>Ile to kosztuje</h2>
  {G['table'](PLANS_HEAD['pl'], PLANS_ROWS['pl'])}
  <p>Płatność co miesiąc, rezygnujesz, kiedy chcesz. Ceny w euro, z VAT. Market Report pokazuje typową cenę, jakiej sprzedający żądają za przedmiot na Vinted, według stanu; przykład w <a href="/vinted-price-guide">przewodniku po cenach Vinted</a> (po angielsku). Wszystkie szczegóły na <a href="/plans">stronie planów</a> (po angielsku).</p>
</section>
<section id="konto">
  <h2>Czego SNYPD od ciebie potrzebuje</h2>
  <p>Adresu e-mail do konta SNYPD. Bez hasła do Vinted, bez logowania do Vinted i bez rozszerzenia przeglądarki. SNYPD czyta publiczne ogłoszenia własnymi systemami: te same wyniki wyszukiwania, które każdy może otworzyć na Vinted bez konta.</p>
  <p>Ponieważ SNYPD nigdy nie loguje się jako ty, nic z tego nie dzieje się na twoim koncie Vinted. Kupujesz przez Vinted jak każdy inny kupujący.</p>
</section>
<section id="pytania">
  <h2>Pytania</h2>
  {G['faq_html'](faq)}
</section>
<section id="wyprobuj">
  <h2>Wypróbuj na jednym wyszukiwaniu</h2>
  {G['cta']('pl')}
</section>"""
        head = ('Bot Vinted: powiadomienia o nowych ogłoszeniach, bez autobuy | SNYPD',
                'SNYPD to bot Vinted, który pilnuje twoich wyszukiwań i wysyła powiadomienie push, gdy pojawi się pasujące ogłoszenie. Bez logowania do Vinted, bez autobuy.',
                'BOT VINTED', 'Bot Vinted, który powiadamia i nigdy nie dotyka twojego konta.',
                'Większość botów Vinted sprzedaje się dzięki automatycznemu kupowaniu, czyli działaniu w twoim imieniu. SNYPD robi drugą część pracy: pilnuje twoich wyszukiwań na Vinted i daje ci znać, gdy pojawi się coś nowego. Ty decydujesz i kupujesz na Vinted.',
                [('podsumowanie', 'W jednym akapicie'), ('rodzaje', 'Trzy rodzaje botów'), ('automatyzacja', 'Automatyzacja'), ('jak-dziala', 'Jak działa'), ('szybkosc', 'Jak szybko'), ('cena', 'Cena'), ('konto', 'Twoje konto Vinted'), ('pytania', 'Pytania')])
        return head, body, faq
    faq = [
        ('Köper SNYPD åt mig?', 'Nej. SNYPD hittar nya annonser och säger till. Du öppnar annonsen på Vinted och köper eller lägger ett bud själv, via Vinteds vanliga betalning.'),
        ('Måste jag ge SNYPD mitt Vinted-lösenord?', 'Nej. SNYPD frågar aldrig efter dina inloggningsuppgifter till Vinted och loggar aldrig in på ditt konto. För ditt SNYPD-konto behöver du bara en e-postadress.'),
        ('Har inte Vinted redan bevakning av nya annonser?', 'Enligt Vinteds hjälpcenter visar en sparad sökning ett nummer med ett plustecken (”+N”) nästa gång du öppnar sökfältet, och räknaren nollställs när du tittar. Vinted skickar notiser bland annat när en medlem du följer laddar upp nya artiklar. SNYPD kontrollerar din sökning ungefär var 30:e sekund och skickar en push för nya matchande annonser. Mer om det: <a href="%s">Vinted bevakning av nya annonser</a>.' % notify),
        ('Hur ofta kontrollerar SNYPD min sökning?', 'Ungefär var 30:e sekund. ' + S + ' Lugna sökningar saktar ner, som mest till 5 minuter. Takten är densamma i alla abonnemang.'),
        ('Fungerar det på iPhone?', 'Ja, när SNYPD ligger på hemskärmen: öppna snypd.store i Safari, tryck på Dela och sedan ”Lägg till på hemskärmen”, och slå på notiser i den installerade appen. Apple tillåter webbnotiser bara för appar på hemskärmen. På Android, Windows och Mac fungerar notiserna direkt i webbläsaren.'),
        ('Finns det en gratisplan?', 'Ja. Free ger en sökning, utan tidsgräns och utan kort. ' + T + ' Därefter kontrollerar den medan din SNYPD-panel är öppen; betalda abonnemang från @@price:solo@@ i månaden kontrollerar dygnet runt även när den är stängd.'),
        ('Fungerar det med vinted.se?', 'Ja. SNYPD fungerar med alla Vinted-sajter i Europa och USA, 26 totalt, bland annat vinted.se, vinted.dk, vinted.fi, vinted.de och vinted.fr. Klistra in en söklänk från sajten du handlar på; priserna visas i den sajtens valuta, på vinted.se i kronor.'),
    ]
    body = f"""
<section id="sammanfattning">
  <h2>SNYPD i ett stycke</h2>
  <div class="lg-box lg-mint"><p>SNYPD är en Vinted bot för bevakning, även kallad Vinted monitor, för dig som köper för att sälja vidare. Du klistrar in en söklänk från Vinted med dina filter (märke, storlek, pris, skick) och SNYPD kontrollerar sökningen ungefär var 30:e sekund. När en ny annons matchar dyker den upp i din panel och du får en pushnotis i mobilen eller datorn. SNYPD frågar aldrig efter ditt Vinted-lösenord, loggar aldrig in på ditt konto, köper ingenting och skriver inte till säljare. Gratisplanen bevakar en sökning: dygnet runt de första 7 dagarna, sedan så länge din panel är öppen. Betalda abonnemang, från @@price:solo@@ i månaden, bevakar dygnet runt.</p></div>
</section>
<section id="typer">
  <h2>Tre sorters Vinted botar</h2>
  <p>”Vinted bot” används om verktyg som gör väldigt olika saker. Den viktiga skillnaden: agerar de via ditt Vinted-konto?</p>
  <h3>BEVAKNINGSBOTAR ELLER VINTED MONITORS</h3>
  <p>De bevakar dina sökningar och säger till när något nytt dyker upp; resellers kallar dem också monitors. Du köper själv, så de behöver inte göra något via ditt Vinted-konto. SNYPD, Telvin Bot och Crazed är bevakningsverktyg.</p>
  <h3>AUTOBUY- OCH AUTOCOP-BOTAR</h3>
  <p>De köper eller betalar åt dig. Att köpa på Vinted kräver ett inloggat konto, så de här verktygen agerar via ditt; V-Tools skriver till exempel att du kopplar dina egna Vinted-konton. Souk, V-Tools och Resell Reserve säljer autobuy.</p>
  <h3>SKRIPT DU KÖR SJÄLV</h3>
  <p>Öppen källkod på GitHub som du kör själv och som oftast postar till Discord eller Telegram. Gratis, men du sköter servern och lagar den när Vinted ändrar något.</p>
  <p>Priser, notiskanaler och gratisalternativ för varje verktyg sida vid sida: <a href="{compare_en}">jämförelse av Vinted botar</a> (på engelska). Hur en monitor fungerar steg för steg: <a href="{monitor_en}">vad är en Vinted monitor?</a> (på engelska)</p>
</section>
<section id="automatisering">
  <h2>Vinted-automatisering: köparsidan, inte säljarsidan</h2>
  <p>”Vinted-automatisering” betyder oftast verktyg för säljare: de lägger upp eller lyfter dina artiklar igen, skickar erbjudanden till dem som favoritmarkerat dem eller skriver dina beskrivningar. De arbetar med dina egna annonser, så de agerar via ditt Vinted-konto.</p>
  <p>SNYPD automatiserar bara köparsidan: det bevakar sökningar och berättar vad som är nytt. Det rör inte dina annonser eller meddelanden och loggar aldrig in. Vill du lyfta eller lägga upp dina egna annonser igen är SNYPD inte rätt verktyg.</p>
</section>
<section id="sa-fungerar-det">
  <h2>Så fungerar SNYPD</h2>
  <ol>
    <li>Sök på din Vinted-sajt (till exempel vinted.se) i webbläsaren och ställ in filtren: märke, storlek, pris, skick.</li>
    <li>Kopiera adressen i adressfältet. En sökadress innehåller <code>/catalog?</code>.</li>
    <li>Klistra in den i SNYPD, ge den ett kort namn och slå på den.</li>
    <li>SNYPD kontrollerar den ungefär var 30:e sekund. Nya träffar hamnar i din panel och, om du slagit på notiser, i mobilen eller datorn. Flera träffar tätt efter varandra kommer i en enda notis.</li>
    <li>Tryck på notisen. Den öppnar annonsen på Vinted, där du köper eller lägger ett bud.</li>
  </ol>
  {G['figure']('feed', 'sv')}
</section>
<section id="hastighet">
  <h2>Hur snabbt går det?</h2>
  <p>SNYPD kontrollerar varje aktiv sökning ungefär var 30:e sekund. {S} {L} Sökningar som ofta hittar nya artiklar behåller den takten; de som blir lugna kontrolleras mer sällan, som mest ungefär var 5:e minut, och snabbar upp igen så fort de hittar något. Takten är densamma i alla abonnemang: betalar du får du fler sökningar och bevakning dygnet runt, inte snabbare kontroller.</p>
  <p>Vissa verktyg lovar notiser på millisekunder. Det lovar inte SNYPD. Det SNYPD lovar: en betald sökning fortsätter när datorn är stängd och mobilen ligger i fickan, alltså just när flest fynd går förlorade.</p>
</section>
<section id="pris">
  <h2>Vad det kostar</h2>
  {G['table'](PLANS_HEAD['sv'], PLANS_ROWS['sv'])}
  <p>Betalning varje månad, avsluta när du vill. Priserna är i euro inklusive moms. Market Report visar det typiska begärda priset för en artikel på Vinted per skick; ett exempel i <a href="/vinted-price-guide">prisguiden för Vinted</a> (på engelska). Alla detaljer på <a href="/plans">abonnemangssidan</a> (på engelska).</p>
</section>
<section id="konto">
  <h2>Vad SNYPD behöver från dig</h2>
  <p>En e-postadress för ditt SNYPD-konto. Inget Vinted-lösenord, ingen inloggning på Vinted och inget webbläsartillägg. SNYPD läser offentliga annonser med egna system: samma sökresultat som vem som helst kan öppna på Vinted utan konto.</p>
  <p>Eftersom SNYPD aldrig loggar in som du händer inget av detta på ditt Vinted-konto. När du köper gör du det via Vinted som vilken köpare som helst.</p>
</section>
<section id="fragor">
  <h2>Frågor</h2>
  {G['faq_html'](faq)}
</section>
<section id="prova">
  <h2>Prova med en sökning</h2>
  {G['cta']('sv')}
</section>"""
    head = ('Vinted bot: bevakning av nya annonser, utan autobuy | SNYPD',
            'SNYPD är en Vinted bot som bevakar dina sökningar och skickar en pushnotis när en ny annons matchar. Ingen inloggning på Vinted, ingen autobuy.',
            'VINTED BOT', 'En Vinted bot som säger till och aldrig rör ditt konto.',
            'De flesta Vinted botar säljs på att köpa automatiskt, alltså på att agera åt dig. SNYPD gör den andra delen av jobbet: bevakar dina sökningar på Vinted och säger till när något nytt dyker upp. Du bestämmer och köper själv på Vinted.',
            [('sammanfattning', 'I ett stycke'), ('typer', 'Tre sorters botar'), ('automatisering', 'Automatisering'), ('sa-fungerar-det', 'Så fungerar det'), ('hastighet', 'Hur snabbt'), ('pris', 'Pris'), ('konto', 'Ditt Vinted-konto'), ('fragor', 'Frågor')])
    return head, body, faq


def page_bot_pl_sv(lang):
    (title, desc, eyebrow, h1, lead, toc), body, faq = _bot_copy(lang)
    return G['page']('bot', lang, title, desc, eyebrow, h1, lead, toc, body, [G['faq_ld'](faq)])


# ------------------------------------------------------------------ wiring
def install(g):
    global G
    G = g
    g['LIVE'].update(pl=True, sv=True)
    g['LANG_NAME'].update(pl='Polski', sv='Svenska')
    g['_MONTHS'].update(MONTHS)
    g['MONTHS_TXT'].update(MONTHS)
    g['_SPAN_SAME_MONTH'].update(SPAN_SAME)
    g['_SPAN_TWO_MONTHS'].update(SPAN_TWO)
    c = g['CHECK']
    sep = {'pl': '\xa0', 'sv': '\xa0'}
    for l in LANGS:
        g['SPEED_MEASURED'][l] = SPEED_TPL[l] % (g['_check_span'](l), format(c['checks'], ',').replace(',', sep[l]), c['hunts'],
                                                 c['median_seconds'], c['share_within_120s'])
    g['VINTED_LAG'].update(VINTED_LAG)
    g['TRIAL'].update(TRIAL)
    g['SLUGS']['bot'].update(SLUG_BOT)
    g['SLUGS']['notify'].update(SLUG_NOTIFY)
    g['UI'].update(ui(g['DISCORD']))
    g['PLANS_ROWS'].update(PLANS_ROWS)
    g['PLANS_HEAD'].update(PLANS_HEAD)
    for l in LANGS:
        g['SHOT_TEXT'][l] = {'feed': SHOT_FEED[l]}
    cd, cac = g['cd'], g['cac']
    cd.COMPARE_CHECKED.update(COMPARE_CHECKED)
    cd.HELP435.update(HELP435)
    cd.HELP433.update(HELP433)
    cd.HELP435_QUOTE.update(HELP435_QUOTE)
    cd.HELP435_TITLE.update(HELP435_TITLE)
    cd.ALERT_WAYS_HEAD.update(ALERT_WAYS_HEAD)
    cd.SOURCE_WORD.update(SOURCE_WORD)
    cd.VINTED_HELP_WORD.update(VINTED_HELP_WORD)
    for row in cd.ALERT_WAYS:
        en = row['name']['en'] if isinstance(row['name'], dict) else row['name']
        cells = WAY_CELLS[en]  # KeyError = a new row in compare_data.ALERT_WAYS needs its pl/sv cells here
        for field in ('name', 'get', 'how', 'cost'):
            if isinstance(row[field], dict):
                row[field] = dict(row[field], **cells[field])
    cac.PUSH.update(PUSH)
    cac.WAYS.update(WAYS)
    cac.NOTIFY.update(NOTIFY)
