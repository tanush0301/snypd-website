#!/usr/bin/env python3
"""/faq and /support (English only), on the same lg-* article template as the SEO pages.

    python ops/seo/gen_help.py

Replaced the Webflow-era pages on 10 Oct 2026 (work order 18, step 2): no <main>, an old
Discord invite, "Pilot Name / Transmission" wording and a supabase-js script that did nothing
useful here. The FAQPage JSON-LD is built from the same (question, answer) pairs as the
visible text, so the two cannot drift. Plan numbers are plans.py tokens, filled by write().
Facts: outreach/00-fact-sheet.md only. ops/ is in .vercelignore: never deploys.
"""
import json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_content as gc  # noqa: E402
from gen_content import SLUGS, PAGE_MODIFIED, DISCORD, esc, faq_ld, faq_html, write  # noqa: E402

SLUGS['faq'] = {'en': '/faq', 'fr': '/fr/faq'}
SLUGS['support'] = {'en': '/support', 'fr': '/fr/support'}
PAGE_MODIFIED['faq'] = '2026-10-10'
PAGE_MODIFIED['support'] = '2026-10-10'
EMAIL = 'heysnypd@gmail.com'
REPLY = 'within 24 hours'  # Tanush's commitment, 10 Oct 2026
MANAGE = 'https://whop.com/@me/settings/orders/'
# Shown under every email button: a mailto link does nothing on a computer without a mail app.
NO_APP = ('<p>Button does not open your mail app? <a href="#write">Use the form</a>, or write to '
          '<a href="mailto:%s">%s</a> from any email service.</p>' % (EMAIL, EMAIL))

FAQ = [
    ('start', 'Getting started', [
        ('How do I start?',
         'Create a free account, paste a Vinted search link (with your brand, size, price and condition filters) and save it. '
         'New matches appear in your dashboard, and with alerts turned on you get a push notification on your phone or computer.'),
        ('Do I need my Vinted login?',
         'No. SNYPD never asks for your Vinted password and never signs in to your account. It reads public listings only, never buys and never messages sellers. '
         'An alert opens the listing on Vinted, where you buy it yourself.'),
        ('Is SNYPD affiliated with Vinted?',
         'No. SNYPD is an independent tool built by a Belgian sneaker reseller. It is not affiliated with, endorsed by or connected to Vinted.'),
        ('Which Vinted countries does it work with?',
         'Every Vinted site in Europe and the US, 26 in all: vinted.fr, vinted.be, vinted.de, vinted.nl, vinted.it, vinted.es, vinted.pl, vinted.co.uk, vinted.com and the rest. '
         'Paste a search link from the site you shop on; prices show in that site&rsquo;s currency.'),
        ('Can I use any Vinted filter?',
         'Yes. Every filter in the link you paste is kept. If a link contains something SNYPD cannot read, it is refused with the reason instead of being quietly trimmed, '
         'so a search never runs with fewer filters than you set.'),
    ]),
    ('alerts', 'Speed and alerts', [
        ('How often does SNYPD check my search?',
         'About every @@median_s@@ seconds (the measured median), slowing to at most 5 minutes on searches that go quiet. Same on every plan. '
         + gc.VINTED_LAG['en']),
        ('Will I get the same listing twice?',
         'No: one alert per listing, and several finds close together arrive as one notification. If a seller deletes an item and lists it again, '
         'Vinted gives it a new listing, so SNYPD can alert you about it again.'),
        ('Do push notifications work on iPhone?',
         'Yes, once SNYPD is on your Home Screen: open snypd.store in Safari, tap Share, then Add to Home Screen, and turn on alerts from the installed app. '
         'Apple only allows web push for Home Screen apps. On Android, Windows and Mac, alerts work straight from the browser.'),
        ('Does it keep running with my laptop closed?',
         'Paid plans, always. Free: 24/7 for the first @@trial_days@@ days after you save your first search, then only while your dashboard is open.'),
        ('Can SNYPD alert me on Discord, Telegram or email?',
         'Discord: yes. Your matches can also go to a private thread in the SNYPD Discord that only you can see. '
         'Connect it in Dashboard &rarr; Profile &rarr; Notifications. Every paid plan and the Hunt Pass include it, and so does the free trial. '
         'Telegram and email: no. Steps and fixes: <a href="/support#discord">Discord alerts</a>.'),
    ]),
    ('plans', 'Plans and billing', [
        ('How many searches can I run?',
         'Active searches per plan: Free @@searches:free@@, Solo @@searches:solo@@, Kickstart @@searches:kickstart@@, Pro @@searches:pro@@, Elite @@searches:elite@@. '
         'Pause any search to free its slot.'),
        ('Is there a free plan or a trial?',
         'Yes. Free has no time limit and needs no card. Your first search runs 24/7 with alerts for @@trial_days@@ days (@@trial_hours@@ h) from when you save it. '
         'If it finds nothing in that time, we add @@trial_ext_days@@ more days once. After that, Free checks it while your dashboard is open.'),
        ('What do the paid plans cost?',
         'Solo @@price:solo@@, Kickstart @@price:kickstart@@, Pro @@price:pro@@ and Elite @@price:elite@@ a month, VAT included. Paid plans keep checking 24/7 with your dashboard closed. '
         'Billed monthly through Whop; cancel any time. <a href="/plans">Compare plans</a>.'),
        ('Can I pay once, without a subscription?',
         'Yes: the Hunt Pass. One payment of @@price:pass@@, VAT included, and 1 Vinted search is watched 24/7 with push alerts for @@pass_days@@ days, like Solo. '
         'Then it simply ends: no renewal, no subscription, nothing to cancel. It suits hunting one specific item, like a console or a jacket in your size. '
         'Full refund within @@refund_days@@ days of the payment. For ongoing hunting, Solo is @@price:solo@@ a month.'),
        ('Can I get a refund?',
         'Yes. Email <a href="mailto:' + EMAIL + '">' + EMAIL + '</a> within @@refund_days@@ days of your first payment for a plan and we refund it in full.'),
        ('What is the Market Report?',
         'Included with Pro and Elite: type an item and see its typical Vinted asking price, split by condition. Asking prices, not sold prices. '
         'It shows no price when the data is too thin or too mixed to trust. Free examples: <a href="/vinted-price-guide">Vinted price guide</a>.'),
    ]),
    ('community', 'Community', [
        ('Is there a SNYPD Discord?',
         'Yes, and it is free to join on every plan. Ask a question, get help from other members and, once you connect it, receive your alerts there in a private thread. '
         'Paid plans also get the paid channels. Push alerts work without it. '
         '<a href="' + DISCORD + '">Join the Discord</a>.'),
    ]),
]


# Contact form (15 Nov 2026). Posts to the backend route /api/v1/support/contact, which sends one
# email to the support inbox (backend src/support_contact.py: 3 per address per hour, 8 a day in
# total, hidden "website" field against bots). Topic keys must match TOPICS in that file.
# /support exists in English and French (/fr/support); every text lives in L below.
FORM_API = 'https://api.snypd.store/api/v1/support/contact'
# problem section id -> form topic key (the section's 'Use the form' button preselects it)
TOPIC_OF = {'no-alerts': 'alerts', 'discord': 'discord', 'missing-listing': 'listing', 'link-refused': 'link', 'plan': 'plan', 'billing': 'billing'}
FORM_CSS = """<style>
.sf { display: flex; flex-direction: column; gap: 14px; max-width: 560px; }
.sf label { display: flex; flex-direction: column; gap: 6px; font-size: 12px; letter-spacing: .06em; color: #A9ADB1; }
.sf input, .sf select, .sf textarea { width: 100%; box-sizing: border-box; min-height: 48px; padding: 12px 14px; font: inherit; font-size: 16px; letter-spacing: 0; color: #FFFFFF; background: #0A0A0B; border: 1px solid #3A3A40; border-radius: 0; }
.sf textarea { min-height: 150px; resize: vertical; line-height: 1.5; }
.sf input:focus-visible, .sf select:focus-visible, .sf textarea:focus-visible { outline: 2px solid #00E5A0; outline-offset: 1px; }
.sf button { align-self: flex-start; border: 0; cursor: pointer; font: inherit; font-size: 12px; }
.sf button[disabled] { opacity: .55; cursor: default; }
.sf-hp { position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden; }
.sf-note { margin: 0; min-height: 22px; font-size: 14px; line-height: 1.5; }
.sf-note.ok { color: #00E5A0; }
.sf-note.err { color: #FFB4A8; }
.sf-small { margin: 0; font-size: 12px; line-height: 1.6; color: #8A8E93; }
</style>"""
FORM_JS = """<script>
(function () {
  var f = document.getElementById('sf'); if (!f) return;
  var st = document.getElementById('sf-status'), btn = document.getElementById('sf-send');
  var T = @@T@@, busy = false;
  function say(t, cls) { st.textContent = t; st.className = 'sf-note ' + (cls || ''); }
  var hint = document.getElementById('sf-hint');
  function showHint() { if (hint && T.hints.hasOwnProperty(f.topic.value)) hint.textContent = T.hints[f.topic.value]; }
  f.topic.addEventListener('change', showHint);
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[data-topic]') : null; if (!a) return;
    f.topic.value = a.getAttribute('data-topic'); showHint();
    setTimeout(function () { f.message.focus(); }, 50);
  });
  f.addEventListener('submit', function (e) {
    e.preventDefault(); if (busy) return;
    var email = f.email.value.trim(), msg = f.message.value.trim();
    if (email.indexOf('@') < 1 || email.indexOf('.') < 0) { say(T.err.bad_email, 'err'); f.email.focus(); return; }
    if (msg.length < 10) { say(T.err.message_too_short, 'err'); f.message.focus(); return; }
    busy = true; btn.disabled = true; say(T.sending, '');
    fetch('@@API@@', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, topic: f.topic.value, message: msg, website: f.website.value, page: location.pathname }) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { return { s: r.status, b: b || {} }; }); })
      .then(function (x) {
        busy = false; btn.disabled = false;
        if (x.s === 200 && x.b.ok === true) { f.reset(); showHint(); say(T.sent, 'ok'); return; }
        var code = x.b.detail && x.b.detail.error;
        say((typeof code === 'string' && T.err.hasOwnProperty(code) && T.err[code]) || T.failed, 'err');
      })
      .catch(function () { busy = false; btn.disabled = false; say(T.failed, 'err'); });
  });
})();
</script>"""

NBSP = chr(160)


def nb(s):
    """French spacing: a no-break space before ? ! : ;"""
    for ch in '?!:;':
        s = s.replace(' ' + ch, NBSP + ch)
    return s


L = {
    'en': dict(
        path='/support', file='support.html', reply=REPLY,
        title='SNYPD support: fix alerts, search links and billing',
        desc='Help with SNYPD: alerts not arriving, a missing listing, a refused Vinted search link, plan or billing problems. Contact form and email, reply %s.',
        eyebrow='SUPPORT', h1='Something not working?',
        lead='Find your problem below and follow the steps. If that does not fix it, write to us: we answer every message %s.',
        toc_person='Reach a person', toc_write='Write to us here', toc_more='Other questions',
        intro=('<section id="person"><h2>Reach a person</h2><div class="lg-box lg-mint"><p>Email <a href="mailto:%s">%s</a>. '
               'We answer every email %s. Use the email address of your SNYPD account, so we can find it.</p>'
               '<p>Prefer chat? The <a href="%s">SNYPD Discord</a> is free to join: ask a question, get help from other members and receive your alerts there.</p>'
               '<div class="ct-actions"><a class="ct-btn" href="#write">WRITE TO US HERE</a>'
               '<a class="ct-btn ct-ghost" href="mailto:%s">EMAIL US</a>'
               '<a class="ct-btn ct-ghost" href="%s" rel="noopener">JOIN THE DISCORD</a></div></div>'
               '<p>Most of the problems below can be fixed in a few steps. Each section has a button that opens an email with the details we need already listed.</p></section>'),
        more=('<section id="more"><h2>Other questions</h2><p>How SNYPD works, plans and refunds: <a href="/faq">FAQ</a>. '
              'Prices and limits: <a href="/plans">plans</a>.</p></section>'),
        email_btn='EMAIL US ABOUT THIS',
        form_btn='USE THE FORM',
        hints=dict(
            alerts='Helpful to include: your device and browser (for example iPhone Home Screen app, Chrome on Android), and whether matches still show in your dashboard.',
            discord='Helpful to include: your Discord username, and what happens (no code, code refused, or connected but no messages).',
            listing='Helpful to include: the link to the Vinted listing, which of your searches should have found it, and when you saw it.',
            link='Helpful to include: the link you pasted and the message SNYPD showed.',
            plan='Helpful to include: the email you used at Whop checkout and the plan you bought.',
            billing='Helpful to include: what you would like (cancel, refund, or change to which plan).',
            other='Tell us what you were trying to do and what happened instead.'),
        no_app=('<p>Button does not open your mail app? <a href="#write">Use the form</a>, or write to '
                '<a href="mailto:%s">%s</a> from any email service.</p>'),
        form_p='No mail app needed. Fill this in and your message goes straight to our inbox. We answer %s.',
        l_email='YOUR EMAIL (THE ONE OF YOUR SNYPD ACCOUNT)', l_topic='WHAT IS IT ABOUT?', l_msg='YOUR MESSAGE', send='SEND MESSAGE',
        small='We use your address and message only to answer you. Never send a password.',
        chat='Prefer chat? <a href="%s" rel="noopener">Join the SNYPD Discord</a>: it is free, and other members can help too.',
        topics=[('alerts', 'Alerts are not arriving'), ('discord', 'Discord alerts'), ('listing', 'A listing did not show up'),
                ('link', 'My search link was refused'), ('plan', 'I paid but my plan did not change'),
                ('billing', 'Cancel, refund or change plan'), ('other', 'Something else')],
        js=dict(sending='Sending...', sent='Message sent. We answer %(reply)s, at the address you gave.',
                failed='We could not send your message. Please email %(mail)s instead.',
                err=dict(bad_email='Check your email address: we need it to answer you.',
                         message_too_short='Tell us a little more, so we can help.',
                         message_too_long='That message is too long. Shorten it, or email %(mail)s.',
                         too_many='You have sent several messages already. We will answer those. For anything urgent, email %(mail)s.',
                         busy='The form has reached its limit for today. Please email %(mail)s instead.')),
    ),
    'fr': dict(
        path='/fr/support', file='fr/support.html', reply='sous 24 heures',
        title='Support SNYPD : alertes, liens de recherche et facturation',
        desc='Aide SNYPD : alertes qui n’arrivent pas, annonce manquante, lien de recherche Vinted refusé, plan ou facturation. Formulaire de contact et e-mail, réponse %s.',
        eyebrow='SUPPORT', h1='Quelque chose ne marche pas ?',
        lead='Trouve ton problème ci-dessous et suis les étapes. Si ça ne suffit pas, écris-nous : nous répondons à chaque message %s.',
        toc_person='Parler à quelqu’un', toc_write='Écris-nous ici', toc_more='Autres questions',
        intro=('<section id="person"><h2>Parler à quelqu’un</h2><div class="lg-box lg-mint"><p>Écris à <a href="mailto:%s">%s</a>. '
               'Nous répondons à chaque e-mail %s. Utilise l’adresse e-mail de ton compte SNYPD, pour qu’on le retrouve.</p>'
               '<p>Tu préfères le chat ? Le <a href="%s">Discord SNYPD</a> est gratuit : pose ta question, reçois l’aide des autres membres et reçois tes alertes là-bas.</p>'
               '<div class="ct-actions"><a class="ct-btn" href="#write">ÉCRIS-NOUS ICI</a>'
               '<a class="ct-btn ct-ghost" href="mailto:%s">ENVOYER UN E-MAIL</a>'
               '<a class="ct-btn ct-ghost" href="%s" rel="noopener">REJOINDRE LE DISCORD</a></div></div>'
               '<p>La plupart des problèmes ci-dessous se règlent en quelques étapes. Chaque section a un bouton qui ouvre un e-mail avec les infos dont on a besoin.</p></section>'),
        more=('<section id="more"><h2>Autres questions</h2><p>Fonctionnement de SNYPD, plans et remboursements : <a href="/fr/faq">FAQ</a>. '
              'Prix et limites : <a href="/plans">plans</a>.</p></section>'),
        email_btn='NOUS ÉCRIRE PAR E-MAIL',
        form_btn='UTILISER LE FORMULAIRE',
        hints=dict(
            alerts='Utile à préciser : ton appareil et ton navigateur (par exemple app iPhone sur l’écran d’accueil, Chrome sur Android), et si les annonces apparaissent encore dans ton tableau de bord.',
            discord='Utile à préciser : ton nom d’utilisateur Discord, et ce qui se passe (pas de code, code refusé, ou connecté mais aucun message).',
            listing='Utile à préciser : le lien de l’annonce Vinted, laquelle de tes recherches aurait dû la trouver, et quand tu l’as vue.',
            link='Utile à préciser : le lien que tu as collé et le message affiché par SNYPD.',
            plan='Utile à préciser : l’e-mail utilisé au paiement Whop et le plan acheté.',
            billing='Utile à préciser : ce que tu souhaites (résilier, remboursement, ou passer à quel plan).',
            other='Dis-nous ce que tu essayais de faire et ce qui s’est passé à la place.'),
        no_app=('<p>Le bouton n’ouvre pas ton application mail ? <a href="#write">Utilise le formulaire</a>, ou écris à '
                '<a href="mailto:%s">%s</a> depuis n’importe quelle messagerie.</p>'),
        form_p='Pas besoin d’application mail. Remplis ce formulaire et ton message arrive directement dans notre boîte. Nous répondons %s.',
        l_email='TON E-MAIL (CELUI DE TON COMPTE SNYPD)', l_topic='C’EST À QUEL SUJET ?', l_msg='TON MESSAGE', send='ENVOYER LE MESSAGE',
        small='Nous utilisons ton adresse et ton message uniquement pour te répondre. N’envoie jamais de mot de passe.',
        chat='Tu préfères le chat ? <a href="%s" rel="noopener">Rejoins le Discord SNYPD</a> : c’est gratuit, et les autres membres peuvent aussi t’aider.',
        topics=[('alerts', 'Les alertes n’arrivent pas'), ('discord', 'Alertes Discord'), ('listing', 'Une annonce n’est pas apparue'),
                ('link', 'Mon lien de recherche a été refusé'), ('plan', 'J’ai payé mais mon plan n’a pas changé'),
                ('billing', 'Résilier, remboursement ou changer de plan'), ('other', 'Autre chose')],
        js=dict(sending='Envoi...', sent='Message envoyé. Nous répondons %(reply)s, à l’adresse indiquée.',
                failed='Impossible d’envoyer ton message. Écris plutôt à %(mail)s.',
                err=dict(bad_email='Vérifie ton adresse e-mail : il nous la faut pour te répondre.',
                         message_too_short='Dis-nous en un peu plus, pour qu’on puisse t’aider.',
                         message_too_long='Ce message est trop long. Raccourcis-le, ou écris à %(mail)s.',
                         too_many='Tu as déjà envoyé plusieurs messages. Nous allons y répondre. Pour une urgence, écris à %(mail)s.',
                         busy='Le formulaire a atteint sa limite pour aujourd’hui. Écris plutôt à %(mail)s.')),
    ),
}
FORM_H = {'en': 'Write to us here', 'fr': 'Écris-nous ici'}


def _nb_deep(v):
    if isinstance(v, str):
        return nb(v)
    if isinstance(v, dict):
        return {k: _nb_deep(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_nb_deep(x) for x in v]
    if isinstance(v, tuple):
        return tuple(_nb_deep(x) for x in v)
    return v


L['fr'] = _nb_deep(L['fr'])
FORM_H['fr'] = nb(FORM_H['fr'])


def form_section(lang):
    t = L[lang]
    opts = ''.join('<option value="%s">%s</option>' % (k, esc(txt)) for k, txt in t['topics'])
    fill = {'reply': t['reply'], 'mail': EMAIL}
    texts = dict(hints=t['hints'], sending=t['js']['sending'], sent=t['js']['sent'] % fill, failed=t['js']['failed'] % fill,
                 err={k: v % fill for k, v in t['js']['err'].items()})
    js = FORM_JS.replace('@@T@@', json.dumps(texts, ensure_ascii=False).replace('</', '<\\/')).replace('@@API@@', FORM_API)
    return ('<section id="write"><h2>%s</h2><p>%s</p>'
            '<form class="sf" id="sf" novalidate>'
            '<label for="sf-email">%s'
            '<input id="sf-email" name="email" type="email" autocomplete="email" inputmode="email" maxlength="254" required></label>'
            '<label for="sf-topic">%s<select id="sf-topic" name="topic" aria-describedby="sf-hint">%s</select></label>'
            '<p class="sf-small" id="sf-hint">%s</p>'
            '<label for="sf-msg">%s<textarea id="sf-msg" name="message" rows="6" maxlength="4000" required></textarea></label>'
            '<div class="sf-hp" aria-hidden="true"><label>Website<input name="website" type="text" tabindex="-1" autocomplete="off"></label></div>'
            '<button class="ct-btn" id="sf-send" type="submit">%s</button>'
            '<p class="sf-note" id="sf-status" role="status" aria-live="polite"></p>'
            '<p class="sf-small">%s</p>'
            '<p class="sf-small">%s</p>'
            '</form>%s</section>' % (esc(FORM_H[lang]), t['form_p'] % t['reply'], esc(t['l_email']), esc(t['l_topic']), opts, esc(t['hints'][t['topics'][0][0]]), esc(t['l_msg']),
                                     esc(t['send']), t['small'], t['chat'] % DISCORD, js))


def mail(subject, lines):
    q = urllib.parse.urlencode({'subject': subject, 'body': '\n'.join(lines) + '\n'}, quote_via=urllib.parse.quote)
    return 'mailto:%s?%s' % (EMAIL, q)


# (id, problem, steps to fix it, (email subject, what to include))
PROBLEMS = {'en': [
    ('no-alerts', 'Alerts are not arriving', [
        'Check that the search is <strong>Active</strong> in your dashboard and that new matches show up there. If they do, the search works and the problem is the notification.',
        'Turn alerts on from the dashboard on the device that should ring. On iPhone this only works from the SNYPD app on your Home Screen (Safari &rarr; Share &rarr; Add to Home Screen).',
        'Check that Focus or Do Not Disturb is off for SNYPD, and that your browser is allowed to show notifications.',
        'On Free after the first @@trial_days@@ days, searches run only while your dashboard is open. Paid plans keep running with it closed.',
     ], ('Alerts not arriving', ['Account email:', 'Device and browser (e.g. iPhone Home Screen app, Chrome on Android):', 'Do matches show in your dashboard? yes/no:'])),
    ('discord', 'Discord alerts: connect them or fix them', [
        'In your dashboard open Profile &rarr; Notifications and press <strong>Connect Discord</strong>. You get a short code, valid for 10 minutes.',
        'Press Open Discord and join the SNYPD server. Type <strong>/link</strong> there and paste the code.',
        'Your finds then arrive in a private thread in #alerts that only you can see. It works on Android, iPhone and computer, next to push or instead of it.',
        'Included in every paid plan, the Hunt Pass and the free trial. After the trial the thread stays but goes quiet until you pick a plan.',
        'Code refused? It has expired: press Connect Discord again for a new one. One Discord account can be linked to one SNYPD account.',
     ], ('Discord alerts', ['Account email:', 'Discord username:', 'What happens (no code / code refused / connected but no messages):'])),
    ('missing-listing', 'A listing I expected did not show up', [
        'Open your search link on Vinted and check that the listing matches every filter in it (size, price, condition, country site).',
        'Vinted itself adds a new listing to its search a few minutes after it is posted, so a very fresh listing can appear a little later.',
        'Matches stay in your dashboard for about 30 minutes while the listing is up; the push notification is the record of older ones.',
     ], ('Listing missing', ['Account email:', 'Link to the Vinted listing:', 'Which of your searches should have found it:', 'When you saw it on Vinted (time):'])),
    ('link-refused', 'My search link was refused', [
        'SNYPD keeps every filter in your link. When a link contains something it cannot read, it refuses the link and says which part, rather than running a different search.',
        'Remove that filter on Vinted, copy the link again from the address bar and paste it.',
     ], ('Search link refused', ['Account email:', 'The link you pasted:', 'The message SNYPD showed:'])),
    ('plan', 'I paid but my plan did not change', [
        'Your plan links to your SNYPD account by email: the email used at Whop checkout must be the same as your SNYPD account email.',
        'Your plan updates automatically after payment, and a check every 15 minutes catches any update that was missed: reload the dashboard. If it still shows Free, email us with your Whop receipt and we link it by hand.',
     ], ('Plan not updated', ['SNYPD account email:', 'Email used at Whop checkout:', 'Plan bought:'])),
    ('billing', 'Cancel, refund or change plan', [
        'Cancel any time in your <a href="' + MANAGE + '">Whop account</a> (Orders), or Account &rarr; Manage subscription in SNYPD. Your plan runs to the end of the month you paid for.',
        'Full refund within @@refund_days@@ days of your first payment for a plan: email us from your account email.',
        'To move between paid plans, manage your subscription in Whop, or email us and we help you switch.',
        'The Hunt Pass is one payment for @@pass_days@@ days. It ends by itself: no renewal and nothing to cancel. Full refund within @@refund_days@@ days of the payment.',
     ], ('Billing', ['SNYPD account email:', 'What you would like (cancel / refund / change to which plan):'])),
], 'fr': [
    ('no-alerts', 'Les alertes n’arrivent pas', [
        'Vérifie que la recherche est <strong>Active</strong> dans ton tableau de bord et que de nouvelles annonces y apparaissent. Si oui, la recherche fonctionne et le problème vient de la notification.',
        'Active les alertes depuis le tableau de bord, sur l’appareil qui doit sonner. Sur iPhone, ça ne marche que depuis l’app SNYPD sur ton écran d’accueil (Safari &rarr; Partager &rarr; Sur l’écran d’accueil).',
        'Vérifie que le mode Concentration ou Ne pas déranger est désactivé pour SNYPD, et que ton navigateur a le droit d’afficher des notifications.',
        'En Free, après les @@trial_days@@ premiers jours, les recherches tournent seulement tant que ton tableau de bord est ouvert. Les abonnements payants continuent quand il est fermé.',
     ], ('Alertes absentes', ['E-mail du compte :', 'Appareil et navigateur (ex. app iPhone sur l’écran d’accueil, Chrome sur Android) :', 'Les annonces apparaissent-elles dans ton tableau de bord ? oui/non :'])),
    ('discord', 'Alertes Discord : les connecter ou les réparer', [
        'Dans ton tableau de bord, ouvre Profil &rarr; Notifications et appuie sur <strong>Connecter Discord</strong>. Tu reçois un code court, valable 10 minutes.',
        'Appuie sur Ouvrir Discord et rejoins le serveur SNYPD. Tape <strong>/link</strong> (ou /lier) là-bas et colle le code.',
        'Tes trouvailles arrivent ensuite dans un fil privé dans #alerts, que toi seul peux voir. Ça marche sur Android, iPhone et ordinateur, en plus des notifications push ou à leur place.',
        'Inclus dans chaque abonnement payant, le Hunt Pass et l’essai gratuit. Après l’essai, le fil reste mais se tait jusqu’à ce que tu choisisses un plan.',
        'Code refusé ? Il a expiré : appuie de nouveau sur Connecter Discord pour en avoir un nouveau. Un compte Discord ne peut être lié qu’à un seul compte SNYPD.',
     ], ('Alertes Discord', ['E-mail du compte :', 'Nom d’utilisateur Discord :', 'Ce qui se passe (pas de code / code refusé / connecté mais aucun message) :'])),
    ('missing-listing', 'Une annonce attendue n’est pas apparue', [
        'Ouvre ton lien de recherche sur Vinted et vérifie que l’annonce correspond à tous ses filtres (taille, prix, état, site du pays).',
        'Vinted lui-même ajoute une nouvelle annonce à sa recherche quelques minutes après sa mise en ligne : une annonce très récente peut donc apparaître un peu plus tard.',
        'Les annonces restent dans ton tableau de bord environ 30 minutes tant qu’elles sont en ligne ; pour les plus anciennes, la notification push fait foi.',
     ], ('Annonce manquante', ['E-mail du compte :', 'Lien de l’annonce Vinted :', 'Laquelle de tes recherches aurait dû la trouver :', 'Quand tu l’as vue sur Vinted (heure) :'])),
    ('link-refused', 'Mon lien de recherche a été refusé', [
        'SNYPD garde tous les filtres de ton lien. Quand un lien contient quelque chose qu’il ne sait pas lire, il le refuse et indique quelle partie, plutôt que de lancer une autre recherche.',
        'Retire ce filtre sur Vinted, copie de nouveau le lien depuis la barre d’adresse et colle-le.',
     ], ('Lien de recherche refusé', ['E-mail du compte :', 'Le lien que tu as collé :', 'Le message affiché par SNYPD :'])),
    ('plan', 'J’ai payé mais mon plan n’a pas changé', [
        'Ton plan est lié à ton compte SNYPD par l’e-mail : l’e-mail utilisé au paiement Whop doit être le même que celui de ton compte SNYPD.',
        'Ton plan se met à jour automatiquement après le paiement, et une vérification toutes les 15 minutes rattrape une mise à jour manquée : recharge le tableau de bord. S’il affiche toujours Free, écris-nous avec ton reçu Whop et nous le lions à la main.',
     ], ('Plan non mis à jour', ['E-mail du compte SNYPD :', 'E-mail utilisé au paiement Whop :', 'Plan acheté :'])),
    ('billing', 'Résilier, remboursement ou changer de plan', [
        'Résilie à tout moment dans ton <a href="' + MANAGE + '">compte Whop</a> (Orders), ou via Compte &rarr; Gérer l’abonnement dans SNYPD. Ton plan court jusqu’à la fin du mois payé.',
        'Remboursement intégral dans les @@refund_days@@ jours suivant ton premier paiement pour un plan : écris-nous depuis l’e-mail de ton compte.',
        'Pour passer d’un plan payant à un autre, gère ton abonnement dans Whop, ou écris-nous et nous t’aidons à changer.',
        'Le Hunt Pass est un paiement unique pour @@pass_days@@ jours. Il s’arrête tout seul : pas de renouvellement, rien à résilier. Remboursement intégral dans les @@refund_days@@ jours suivant le paiement.',
     ], ('Facturation', ['SNYPD - e-mail du compte :', 'Ce que tu souhaites (résilier / remboursement / passer à quel plan) :'])),
]}
# French spacing in the visible text only; the pre-filled email lines stay plain.
PROBLEMS['fr'] = [(pid, nb(title), [nb(s) for s in steps], m) for pid, title, steps, m in PROBLEMS['fr']]


FAQ_FR = [
    ('start', 'Pour commencer', [
        ('Comment commencer ?',
         'Crée un compte gratuit, colle un lien de recherche Vinted (avec tes filtres de marque, taille, prix et état) et enregistre-le. '
         'Les nouvelles annonces apparaissent dans ton tableau de bord et, une fois les alertes activées, tu reçois une notification push sur ton téléphone ou ton ordinateur.'),
        ('Faut-il mon identifiant Vinted ?',
         'Non. SNYPD ne demande jamais ton mot de passe Vinted et ne se connecte jamais à ton compte. Il lit uniquement les annonces publiques, n’achète rien et n’écrit jamais aux vendeurs. '
         'Une alerte ouvre l’annonce sur Vinted, où tu achètes toi-même.'),
        ('SNYPD est-il affilié à Vinted ?',
         'Non. SNYPD est un outil indépendant créé par un revendeur de sneakers belge. Il n’est ni affilié à Vinted, ni approuvé par Vinted, ni lié à Vinted.'),
        ('Avec quels pays Vinted ça marche ?',
         'Tous les sites Vinted d’Europe et des États-Unis, 26 au total : vinted.fr, vinted.be, vinted.de, vinted.nl, vinted.it, vinted.es, vinted.pl, vinted.co.uk, vinted.com et les autres. '
         'Colle un lien de recherche du site où tu achètes ; les prix s’affichent dans la devise de ce site.'),
        ('Puis-je utiliser n’importe quel filtre Vinted ?',
         'Oui. Tous les filtres du lien que tu colles sont conservés. Si un lien contient quelque chose que SNYPD ne sait pas lire, il est refusé avec la raison au lieu d’être raccourci en silence : '
         'une recherche ne tourne jamais avec moins de filtres que ceux que tu as choisis.'),
    ]),
    ('alerts', 'Vitesse et alertes', [
        ('À quelle fréquence SNYPD vérifie-t-il ma recherche ?',
         'Environ toutes les @@median_s@@ secondes (médiane mesurée), et au plus toutes les 5 minutes sur les recherches calmes. Pareil sur tous les plans. '
         + gc.VINTED_LAG['fr']),
        ('Vais-je recevoir deux fois la même annonce ?',
         'Non : une alerte par annonce, et plusieurs trouvailles rapprochées arrivent dans une seule notification. Si un vendeur supprime un article et le remet en ligne, '
         'Vinted lui donne une nouvelle annonce : SNYPD peut donc t’alerter de nouveau.'),
        ('Les notifications push marchent-elles sur iPhone ?',
         'Oui, une fois SNYPD sur ton écran d’accueil : ouvre snypd.store dans Safari, touche Partager, puis Sur l’écran d’accueil, et active les alertes depuis l’app installée. '
         'Apple n’autorise le push web que pour les apps de l’écran d’accueil. Sur Android, Windows et Mac, les alertes marchent directement depuis le navigateur.'),
        ('Ça continue de tourner ordinateur fermé ?',
         'Avec un plan payant, toujours. En Free : 24h/24 pendant les @@trial_days@@ premiers jours après l’enregistrement de ta première recherche, puis seulement tant que ton tableau de bord est ouvert.'),
        ('SNYPD peut-il m’alerter sur Discord, Telegram ou par e-mail ?',
         'Discord : oui. Tes trouvailles peuvent aussi arriver dans un fil privé du Discord SNYPD que toi seul vois. '
         'Connecte-le dans Tableau de bord &rarr; Profil &rarr; Notifications. Tous les plans payants et le Hunt Pass l’incluent, ainsi que l’essai gratuit. '
         'Telegram et e-mail : non. Étapes et dépannage : <a href="/fr/support#discord">alertes Discord</a>.'),
    ]),
    ('plans', 'Plans et facturation', [
        ('Combien de recherches puis-je lancer ?',
         'Recherches actives par plan : Free @@searches:free@@, Solo @@searches:solo@@, Kickstart @@searches:kickstart@@, Pro @@searches:pro@@, Elite @@searches:elite@@. '
         'Mets une recherche en pause pour libérer sa place.'),
        ('Y a-t-il un plan gratuit ou un essai ?',
         'Oui. Free n’a pas de limite de durée et ne demande pas de carte. Ta première recherche tourne 24h/24 avec alertes pendant @@trial_days@@ jours (@@trial_hours@@ h) à partir de son enregistrement. '
         'Si elle ne trouve rien pendant ce temps, nous ajoutons @@trial_ext_days@@ jours, une fois. Ensuite, Free la vérifie tant que ton tableau de bord est ouvert.'),
        ('Combien coûtent les plans payants ?',
         'Solo @@price:solo@@, Kickstart @@price:kickstart@@, Pro @@price:pro@@ et Elite @@price:elite@@ par mois, TVA comprise. Les plans payants continuent de vérifier 24h/24, tableau de bord fermé. '
         'Facturation mensuelle via Whop ; résiliable à tout moment. <a href="/plans">Comparer les plans</a>.'),
        ('Puis-je payer une seule fois, sans abonnement ?',
         'Oui : le Hunt Pass. Un paiement de @@price:pass@@, TVA comprise, et 1 recherche Vinted est surveillée 24h/24 avec alertes push pendant @@pass_days@@ jours, comme Solo. '
         'Puis il s’arrête simplement : pas de renouvellement, pas d’abonnement, rien à résilier. Idéal pour chercher un article précis, comme une console ou une veste à ta taille. '
         'Remboursement intégral dans les @@refund_days@@ jours suivant le paiement. Pour chercher en continu, Solo coûte @@price:solo@@ par mois.'),
        ('Puis-je être remboursé ?',
         'Oui. Écris à <a href="mailto:' + EMAIL + '">' + EMAIL + '</a> dans les @@refund_days@@ jours suivant ton premier paiement pour un plan et nous le remboursons intégralement.'),
        ('Qu’est-ce que le Market Report ?',
         'Inclus dans Pro et Elite : tape un article et vois son prix demandé typique sur Vinted, par état. Ce sont des prix demandés, pas des prix de vente conclue. '
         'Il n’affiche aucun prix quand les données sont trop minces ou trop mélangées pour être fiables. Exemples gratuits : <a href="/fr/guide-prix-vinted">guide des prix Vinted</a>.'),
    ]),
    ('community', 'Communauté', [
        ('Y a-t-il un Discord SNYPD ?',
         'Oui, et il est gratuit sur tous les plans. Pose une question, reçois l’aide des autres membres et, une fois connecté, reçois tes alertes là-bas dans un fil privé. '
         'Les plans payants ont aussi accès aux salons payants. Les alertes push marchent sans lui. '
         '<a href="' + DISCORD + '">Rejoindre le Discord</a>.'),
    ]),
]
FAQ_FR = [(sid, nb(title), [(nb(q), nb(a_)) for q, a_ in qs]) for sid, title, qs in FAQ_FR]
FAQS = {'en': FAQ, 'fr': FAQ_FR}
FAQ_T = {
    'en': dict(title='SNYPD FAQ: Vinted alerts, plans and push notifications',
               desc='Straight answers about SNYPD, the Vinted alert bot: how often it checks, push on iPhone, the free plan and @@trial_days@@-day trial, prices and refunds.',
               eyebrow='FAQ', h1='SNYPD questions, answered',
               lead='How the Vinted monitor works, what each plan includes and how to get alerts on your phone.',
               help_h='Still stuck?',
               help_p=('The <a href="/support">support page</a> lists the common problems and how to fix them, and has a contact form. '
                       'Or email <a href="mailto:%s">%s</a>: we answer every email %s. Prefer chat? <a href="%s" rel="noopener">Join the SNYPD Discord</a>.')),
    'fr': dict(title='FAQ SNYPD : alertes Vinted, plans et notifications push',
               desc='Des réponses claires sur SNYPD, le bot d’alertes Vinted : fréquence de vérification, push sur iPhone, plan gratuit et essai de @@trial_days@@ jours, prix et remboursements.',
               eyebrow='FAQ', h1='Les réponses à tes questions sur SNYPD',
               lead='Comment fonctionne le monitor Vinted, ce que chaque plan inclut et comment recevoir les alertes sur ton téléphone.',
               help_h='Toujours bloqué ?',
               help_p=('La <a href="/fr/support">page support</a> liste les problèmes courants et comment les régler, avec un formulaire de contact. '
                       'Ou écris à <a href="mailto:%s">%s</a> : nous répondons à chaque e-mail %s. Tu préfères le chat ? <a href="%s" rel="noopener">Rejoins le Discord SNYPD</a>.')),
}
FAQ_T['fr'] = _nb_deep(FAQ_T['fr'])


def page_faq(lang='en'):
    faq, t = FAQS[lang], FAQ_T[lang]
    pairs = [qa for _, _, qs in faq for qa in qs]
    body = ''.join('<section id="%s"><h2>%s</h2>%s</section>' % (sid, esc(title), faq_html(qs)) for sid, title, qs in faq)
    body += '<section id="help"><h2>%s</h2><p>%s</p></section>' % (esc(t['help_h']), t['help_p'] % (EMAIL, EMAIL, L[lang]['reply'], DISCORD))
    return gc.page('faq', lang, t['title'], t['desc'], t['eyebrow'], t['h1'], t['lead'],
                   [(sid, title) for sid, title, _ in faq] + [('help', t['help_h'])], body, [gc.faq_ld(pairs)])


def page_support(lang='en'):
    t = L[lang]
    blocks = []
    for pid, title, steps, (subj, lines) in PROBLEMS[lang]:
        blocks.append('<section id="%s"><h2>%s</h2><ol>%s</ol><div class="ct-actions" style="margin:0 0 14px;">'
                      '<a class="ct-btn" href="#write" data-topic="%s">%s</a><a class="ct-btn ct-ghost" href="%s">%s</a></div>%s</section>'
                      % (pid, esc(title), ''.join('<li>%s</li>' % s for s in steps), TOPIC_OF[pid], esc(t['form_btn']),
                         esc(mail('SNYPD: ' + subj, lines)), esc(t['email_btn']), t['no_app'] % (EMAIL, EMAIL)))
    intro = t['intro'] % (EMAIL, EMAIL, t['reply'], DISCORD, EMAIL, DISCORD)
    body = intro + form_section(lang) + ''.join(blocks) + t['more']
    return gc.page('support', lang, t['title'], t['desc'] % t['reply'], t['eyebrow'], t['h1'], t['lead'] % t['reply'],
                   [('person', t['toc_person']), ('write', t['toc_write'])] + [(pid, title) for pid, title, _, _ in PROBLEMS[lang]]
                   + [('more', t['toc_more'])], body, head_extra=FORM_CSS)


# Contact pages in the other languages (15 Nov 2026): form, email, Discord. Texts: copy_support_langs.py.
import copy_support_langs as csl  # noqa: E402
for _l, _c in csl.C.items():
    SLUGS['support'][_l] = '/%s/support' % _l
    FORM_H[_l] = _c['toc_write']
    L[_l] = dict(reply=_c['reply'], form_p=_c['form_p'].replace('{reply}', '%s'), l_email=_c['l_email'], l_topic=_c['l_topic'],
                 l_msg=_c['l_msg'], send=_c['send'], small=_c['small'], chat=_c['chat'].replace('{discord}', '%s'),
                 topics=list(zip(csl.TOPIC_KEYS, _c['topics'])), hints=dict(zip(csl.TOPIC_KEYS, _c['hints'])),
                 js=dict(sending=_c['sending'], sent=_c['sent'], failed=_c['failed'], err=dict(zip(csl.ERR_KEYS, _c['err']))))


def page_contact(lang):
    c = csl.C[lang]
    f = lambda x: x.replace('{mail}', EMAIL).replace('{reply}', c['reply']).replace('{discord}', DISCORD)  # noqa: E731
    intro = ('<section id="person"><h2>%s</h2><div class="lg-box lg-mint"><p>%s</p><p>%s</p>'
             '<div class="ct-actions"><a class="ct-btn" href="#write">%s</a>'
             '<a class="ct-btn ct-ghost" href="mailto:%s">%s</a>'
             '<a class="ct-btn ct-ghost" href="%s" rel="noopener">%s</a></div></div></section>'
             % (esc(c['toc_person']), f(c['p_email']), f(c['p_chat']), esc(c['b_write']), EMAIL, esc(c['b_email']), DISCORD, esc(c['b_discord'])))
    more = '<section id="more"><h2>%s</h2><p>%s</p></section>' % (esc(c['toc_more']), c['more_p'])
    return gc.page('support', lang, c['title'], f(c['desc']), 'SUPPORT', c['h1'], f(c['lead']),
                   [('person', c['toc_person']), ('write', c['toc_write']), ('more', c['toc_more'])],
                   intro + form_section(lang) + more, head_extra=FORM_CSS)


if __name__ == '__main__':
    write('faq.html', page_faq('en'))
    write('fr/faq.html', page_faq('fr'))
    write('support.html', page_support('en'))
    write('fr/support.html', page_support('fr'))
    for _l in csl.C:
        write('%s/support.html' % _l, page_contact(_l))
