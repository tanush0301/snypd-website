#!/usr/bin/env python3
"""/faq and /support (English only), on the same lg-* article template as the SEO pages.

    python ops/seo/gen_help.py

Replaced the Webflow-era pages on 10 Oct 2026 (work order 18, step 2): no <main>, an old
Discord invite, "Pilot Name / Transmission" wording and a supabase-js script that did nothing
useful here. The FAQPage JSON-LD is built from the same (question, answer) pairs as the
visible text, so the two cannot drift. Plan numbers are plans.py tokens, filled by write().
Facts: outreach/00-fact-sheet.md only. ops/ is in .vercelignore: never deploys.
"""
import os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_content as gc  # noqa: E402
from gen_content import SLUGS, PAGE_MODIFIED, DISCORD, esc, faq_ld, faq_html, write  # noqa: E402

SLUGS['faq'] = {'en': '/faq'}
SLUGS['support'] = {'en': '/support'}
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


def page_faq():
    pairs = [qa for _, _, qs in FAQ for qa in qs]
    body = ''.join('<section id="%s"><h2>%s</h2>%s</section>' % (sid, esc(title), faq_html(qs)) for sid, title, qs in FAQ)
    body += ('<section id="help"><h2>Still stuck?</h2><p>The <a href="/support">support page</a> lists the common problems and how to fix them. '
             'Or email <a href="mailto:%s">%s</a>: we answer every email %s.</p></section>' % (EMAIL, EMAIL, REPLY))
    return gc.page('faq', 'en', 'SNYPD FAQ: Vinted alerts, plans and push notifications',
                   'Straight answers about SNYPD, the Vinted alert bot: how often it checks, push on iPhone, the free plan and @@trial_days@@-day trial, prices and refunds.',
                   'FAQ', 'SNYPD questions, answered',
                   'How the Vinted monitor works, what each plan includes and how to get alerts on your phone.',
                   [(sid, title) for sid, title, _ in FAQ] + [('help', 'Still stuck?')], body, [gc.faq_ld(pairs)])

# Contact form (15 Nov 2026). Posts to the backend route /api/v1/support/contact, which sends one
# email to the support inbox (backend src/support_contact.py: 3 per address per hour, 8 a day in
# total, hidden "website" field against bots). Topic keys must match TOPICS in that file.
FORM_API = 'https://api.snypd.store/api/v1/support/contact'
FORM_TOPICS = [('alerts', 'Alerts are not arriving'), ('discord', 'Discord alerts'), ('listing', 'A listing did not show up'),
               ('link', 'My search link was refused'), ('plan', 'I paid but my plan did not change'),
               ('billing', 'Cancel, refund or change plan'), ('other', 'Something else')]
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
  var MAIL = '@@MAIL@@', busy = false;
  function say(t, cls) { st.textContent = t; st.className = 'sf-note ' + (cls || ''); }
  var TEXT = {
    bad_email: 'Check your email address: we need it to answer you.',
    message_too_short: 'Tell us a little more, so we can help.',
    message_too_long: 'That message is too long. Shorten it, or email ' + MAIL + '.',
    too_many: 'You have sent several messages already. We will answer those. For anything urgent, email ' + MAIL + '.',
    busy: 'The form has reached its limit for today. Please email ' + MAIL + ' instead.'
  };
  f.addEventListener('submit', function (e) {
    e.preventDefault(); if (busy) return;
    var email = f.email.value.trim(), msg = f.message.value.trim();
    if (email.indexOf('@') < 1 || email.indexOf('.') < 0) { say(TEXT.bad_email, 'err'); f.email.focus(); return; }
    if (msg.length < 10) { say(TEXT.message_too_short, 'err'); f.message.focus(); return; }
    busy = true; btn.disabled = true; say('Sending...', '');
    fetch('@@API@@', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, topic: f.topic.value, message: msg, website: f.website.value, page: location.pathname }) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { return { s: r.status, b: b || {} }; }); })
      .then(function (x) {
        busy = false;
        if (x.s === 200 && x.b.ok === true) {
          f.reset(); btn.disabled = false;
          say('Message sent. We answer @@REPLY@@, at the address you gave.', 'ok');
          return;
        }
        btn.disabled = false;
        var code = x.b.detail && x.b.detail.error;
        say(TEXT[code] || ('We could not send your message. Please email ' + MAIL + ' instead.'), 'err');
      })
      .catch(function () {
        busy = false; btn.disabled = false;
        say('We could not send your message. Please email ' + MAIL + ' instead.', 'err');
      });
  });
})();
</script>"""


def form_section():
    opts = ''.join('<option value="%s">%s</option>' % (k, esc(t)) for k, t in FORM_TOPICS)
    js = FORM_JS.replace('@@MAIL@@', EMAIL).replace('@@API@@', FORM_API).replace('@@REPLY@@', REPLY)
    return ('<section id="write"><h2>Write to us here</h2>'
            '<p>No mail app needed. Fill this in and your message goes straight to our inbox. We answer %s.</p>'
            '<form class="sf" id="sf" novalidate>'
            '<label for="sf-email">YOUR EMAIL (THE ONE OF YOUR SNYPD ACCOUNT)'
            '<input id="sf-email" name="email" type="email" autocomplete="email" inputmode="email" maxlength="254" required></label>'
            '<label for="sf-topic">WHAT IS IT ABOUT?<select id="sf-topic" name="topic">%s</select></label>'
            '<label for="sf-msg">YOUR MESSAGE<textarea id="sf-msg" name="message" rows="6" maxlength="4000" required></textarea></label>'
            '<div class="sf-hp" aria-hidden="true"><label>Website<input name="website" type="text" tabindex="-1" autocomplete="off"></label></div>'
            '<button class="ct-btn" id="sf-send" type="submit">SEND MESSAGE</button>'
            '<p class="sf-note" id="sf-status" role="status" aria-live="polite"></p>'
            '<p class="sf-small">We use your address and message only to answer you. Never send a password.</p>'
            '</form>%s</section>' % (REPLY, opts, js))


def mail(subject, lines):
    q = urllib.parse.urlencode({'subject': subject, 'body': '\n'.join(lines) + '\n'}, quote_via=urllib.parse.quote)
    return 'mailto:%s?%s' % (EMAIL, q)


# (id, problem, steps to fix it, (email subject, what to include))
PROBLEMS = [
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
]


def page_support():
    blocks = []
    for pid, title, steps, (subj, lines) in PROBLEMS:
        blocks.append('<section id="%s"><h2>%s</h2><ol>%s</ol><p><a class="ct-btn ct-ghost" href="%s">EMAIL US ABOUT THIS</a></p>%s</section>'
                      % (pid, esc(title), ''.join('<li>%s</li>' % s for s in steps), esc(mail('SNYPD: ' + subj, lines)), NO_APP))
    intro = ('<section id="person"><h2>Reach a person</h2><div class="lg-box lg-mint"><p>Email <a href="mailto:%s">%s</a>. '
             'We answer every email %s. Use the email address of your SNYPD account, so we can find it.</p>'
             '<p>Prefer chat? The <a href="%s">SNYPD Discord</a> is free to join: ask a question, get help from other members and receive your alerts there.</p>'
             '<div class="ct-actions"><a class="ct-btn" href="#write">WRITE TO US HERE</a>'
             '<a class="ct-btn ct-ghost" href="mailto:%s">EMAIL US</a>'
             '<a class="ct-btn ct-ghost" href="%s" rel="noopener">JOIN THE DISCORD</a></div></div>'
             '<p>Most of the problems below can be fixed in a few steps. Each section has a button that opens an email with the details we need already listed.</p></section>'
             % (EMAIL, EMAIL, REPLY, DISCORD, EMAIL, DISCORD))
    body = intro + form_section() + ''.join(blocks) + ('<section id="more"><h2>Other questions</h2><p>How SNYPD works, plans and refunds: <a href="/faq">FAQ</a>. '
                                      'Prices and limits: <a href="/plans">plans</a>.</p></section>')
    return gc.page('support', 'en', 'SNYPD support: fix alerts, search links and billing',
                   'Help with SNYPD: alerts not arriving, a missing listing, a refused Vinted search link, plan or billing problems. Contact form and email, reply %s.' % REPLY,
                   'SUPPORT', 'Something not working?',
                   'Find your problem below and follow the steps. If that does not fix it, write to us: we answer every message %s.' % REPLY,
                   [('person', 'Reach a person'), ('write', 'Write to us here')] + [(pid, title) for pid, title, _, _ in PROBLEMS] + [('more', 'Other questions')], body, head_extra=FORM_CSS)


if __name__ == '__main__':
    write('faq.html', page_faq())
    write('support.html', page_support())
