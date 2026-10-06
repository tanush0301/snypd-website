# Body text for privacy.html and terms.html. Every factual statement here was
# checked against the running system on 2026-09-27 (see CLAUDE.md, Session 27) and
# again on 2026-10-04 when the pages went live (operator, Meta Pixel, log retention).
# Still open: address + KBO/VAT number once SNYPD is registered, and a lawyer's read.

DRAFT_NOTE = ''

OPERATOR = """
<div class="lg-box">
  <p><strong>Operator:</strong> Tanush Khandelwal, Belgium</p>
  <p><strong>Contact:</strong> <a href="mailto:{email}">{email}</a></p>
</div>
"""

PRIVACY_TOC = [
    ('who', 'Who we are'), ('collect', 'What we collect'), ('why', 'Why, and the legal basis'),
    ('vinted', 'Data from Vinted'), ('share', 'Who helps us'), ('transfers', 'Outside the EU'),
    ('keep', 'How long we keep it'), ('rights', 'Your rights'), ('security', 'Security'),
    ('age', 'Age'), ('changes', 'Changes'),
]


def privacy_body(email, discord):
    op = OPERATOR.format(email=email)
    return f"""{DRAFT_NOTE}
<section id="who">
  <h2>Who we are</h2>
  <p>SNYPD is a web service that watches the Vinted searches you save and alerts you when new matching listings appear. The operator named below decides why and how your personal data is used (the "controller" under the GDPR).</p>
  {op}
  <p>SNYPD is independent and not affiliated with or endorsed by Vinted.</p>
</section>
<section id="collect">
  <h2>What we collect</h2>
  <h3>ACCOUNT</h3>
  <ul>
    <li>Your email address and a password, which our database provider stores only in hashed form. We never see it.</li>
    <li>If you sign in with Google: the name, email address and profile picture link Google shares with us.</li>
    <li>The plan you picked before signing up, and the partner code if you arrived through a partner link and allowed marketing cookies.</li>
    <li>If you arrived through a Whop partner link (an address ending in <code>?a=</code> and a name): that partner's Whop username. It is saved with your account and passed to Whop's checkout, so Whop can pay the partner. Your browser keeps it only if you allowed marketing cookies.</li>
    <li>Your founding-member number, if you are one of the first 100 accounts.</li>
    <li>If you arrived through a link with campaign tags in the address (for example one of our ads): those tags, which name the source, campaign and ad, not you. They come from the link only; nothing is stored on your device for this.</li>
  </ul>
  <h3>WHAT YOU DO IN SNYPD</h3>
  <ul>
    <li>The Vinted search links you save, their names and whether they are paused.</li>
    <li>Listings you mark as bought or sold, with the prices you enter.</li>
    <li>Points, streaks and ranks, including how many seconds per day your dashboard is open (this decides streaks).</li>
    <li>Your alert settings, such as quiet hours.</li>
    <li>While your dashboard is open it tells our server every 30 seconds that you are online, so monitoring runs for you.</li>
  </ul>
  <h3>ALERTS</h3>
  <p>If you turn on alerts, the push address your browser creates, its encryption keys and your browser's user-agent string.</p>
  <h3>PAYMENTS</h3>
  <p>Payments are handled by <strong>Whop</strong>. We never see your card details. Whop tells us your membership and plan, its status, the renewal date and the email address used at checkout, so we can give your account the right plan.</p>
  <h3>TECHNICAL</h3>
  <ul>
    <li>Our server's access logs: IP address, time, the address requested and browser details.</li>
    <li>Our database provider's sign-in records, which include the IP address of each sign-in.</li>
    <li>When someone opens a partner link: the partner code and the page they came from. No identifier of the visitor is stored with it.</li>
  </ul>
  <h3>ONLY WITH YOUR CONSENT</h3>
  <p>Google Analytics, the Whop pixel and the Meta Pixel. See the <a href="/cookies">cookie policy</a> for exactly what they store.</p>
  <h3>WHEN YOU CONTACT US</h3>
  <p>What you write to us by email or in our Discord server, and your contact details.</p>
</section>
<section id="why">
  <h2>Why, and the legal basis</h2>
  <ul>
    <li><strong>To run the service you signed up for</strong>: your account, searches, alerts, dashboard, plan and payments. Legal basis: the contract with you (GDPR article 6(1)(b)).</li>
    <li><strong>To keep SNYPD secure and working</strong>: server logs, sign-in records, preventing abuse and fixing faults. Legal basis: our legitimate interest in a secure, working service (article 6(1)(f)).</li>
    <li><strong>To see which ads and links bring sign-ups</strong>, using the campaign tags above. Legal basis: our legitimate interest in knowing which marketing works (article 6(1)(f)).</li>
    <li><strong>To credit partners</strong> who send you to SNYPD, and to count partner-link visits. Legal basis: our legitimate interest in running the partner programme, and your consent for anything stored on your device.</li>
    <li><strong>Analytics and ad measurement</strong>. Legal basis: your consent (article 6(1)(a)), which you can withdraw at any time in the <a href="/cookies">cookie settings</a>.</li>
    <li><strong>Invoices and tax</strong>: keeping payment records the law requires. Legal basis: legal obligation (article 6(1)(c)).</li>
    <li><strong>Replying to you</strong> when you contact us. Legal basis: our legitimate interest in answering, or the contract if it concerns your account.</li>
  </ul>
  <p>We do not sell your data, and we make no decisions about you by automated means that have legal or similarly significant effects.</p>
</section>
<section id="vinted">
  <h2>Data from Vinted</h2>
  <p>To find listings and build price estimates, SNYPD reads public Vinted search results: titles, prices, brands, sizes, condition, photos and links. These can include the seller's public Vinted username and account number. We use them only to show matching listings and to calculate market prices, never to follow or profile a specific seller. SNYPD rejects saved searches that point at a seller's profile instead of a catalogue search. Market-price data is deleted after 14 days. Legal basis: our legitimate interest in providing the service. If you are a Vinted seller and want to object or ask what we hold, email us.</p>
</section>
<section id="share">
  <h2>Who helps us</h2>
  <p>These providers process personal data for us, each only for the purpose listed:</p>
  <ul>
    <li><strong>Supabase</strong>: database and sign-in. Our database runs in the EU (Paris).</li>
    <li><strong>IONOS</strong>: the server that runs monitoring and alerts, in Frankfurt, Germany.</li>
    <li><strong>Vercel</strong>: hosts this website and delivers it through its global network.</li>
    <li><strong>Whop</strong>: checkout, payments and subscriptions. Its checkout, which loads only when you open one, also runs Whop's own measurement script. The Whop pixel on the rest of the site runs only with your consent.</li>
    <li><strong>Meta</strong>: the Meta Pixel, only with your consent. It tells Meta which SNYPD pages you visit and that a sign-up happened, so we can see which Facebook or Instagram ads work.</li>
    <li><strong>Google</strong>: sign in with Google, Google Analytics (only with consent) and, in Chrome, delivery of alerts. Other browsers deliver alerts through their maker's push service, such as Apple, Mozilla or Microsoft.</li>
    <li><strong>jsDelivr</strong>: delivers the sign-in library to your browser.</li>
    <li><strong>Discord</strong>: only if you join our <a href="{discord}">Discord server</a>.</li>
    <li><strong>Gmail</strong> (Google): if you email us.</li>
  </ul>
  <p>We may also disclose data if the law requires it, or to protect our rights in a dispute.</p>
</section>
<section id="transfers">
  <h2>Outside the EU</h2>
  <p>Several of these providers are based in the United States or use servers outside the European Economic Area. Where data leaves the EEA, the transfer relies on the safeguards the provider offers, such as certification under the EU-US Data Privacy Framework or the European Commission's Standard Contractual Clauses.</p>
</section>
<section id="keep">
  <h2>How long we keep it</h2>
  <ul>
    <li><strong>Account and everything in it</strong>: while your account exists. When you ask us to delete it, we delete it within 30 days.</li>
    <li><strong>Listings shown in your feed</strong>: removed automatically within an hour.</li>
    <li><strong>Market-price data</strong>: 14 days after a listing was last seen.</li>
    <li><strong>Push address</strong>: until you turn alerts off, or your browser tells us the address no longer works.</li>
    <li><strong>Server logs</strong>, including access logs: emptied automatically on the 1st of every month, so they are never more than about a month old.</li>
    <li><strong>Payment records</strong>: as long as tax law requires, which in Belgium is up to 10 years.</li>
    <li><strong>Emails and support messages</strong>: as long as needed to help you, then up to one year.</li>
  </ul>
</section>
<section id="rights">
  <h2>Your rights</h2>
  <p>You can ask us to show you the data we hold about you, correct it, delete it, limit how we use it, or give it to you in a portable format. You can object to uses based on our legitimate interest, and withdraw consent at any time without affecting what happened before. Email <a href="mailto:{email}">{email}</a> from the address on your account. We answer within one month.</p>
  <p>If you think we handle your data wrongly, you can complain to the Belgian Data Protection Authority (<a href="https://www.dataprotectionauthority.be">dataprotectionauthority.be</a>) or the authority where you live.</p>
</section>
<section id="security">
  <h2>Security</h2>
  <p>Traffic to SNYPD is encrypted, passwords are stored only in hashed form, and database rules make sure each account can only read its own data. No system is perfectly secure. If a breach puts your data at risk, we will tell you and the authority as the law requires.</p>
</section>
<section id="age">
  <h2>Age</h2>
  <p>SNYPD is for people aged 16 and over. If you believe a younger child has given us personal data, email us and we will delete it.</p>
</section>
<section id="changes">
  <h2>Changes</h2>
  <p>When this policy changes, the date at the top changes too. If a change matters for how we use your data, we will tell you by email or in the dashboard before it takes effect.</p>
</section>"""


TERMS_TOC = [
    ('about', 'About these terms'), ('service', 'What SNYPD does'), ('account', 'Your account'),
    ('plans', 'Plans and billing'), ('founding', 'Founding members'), ('refund', 'Refunds and withdrawal'),
    ('use', 'Fair use'), ('market', 'Market prices'), ('liability', 'Liability'),
    ('end', 'Ending the agreement'), ('law', 'Law and disputes'), ('changes', 'Changes'),
]


def terms_body(email, discord):
    op = OPERATOR.format(email=email)
    form = (
        "To: SNYPD, " + email + "\n"
        "I hereby give notice that I withdraw from my contract for the following service: SNYPD subscription\n"
        "Ordered on: ...\n"
        "Name: ...\n"
        "Email address used for the account: ...\n"
        "Date: ...")
    return f"""{DRAFT_NOTE}
<section id="about">
  <h2>About these terms</h2>
  <p>These terms apply when you create a SNYPD account or buy a plan. By doing either, you accept them. They are offered by:</p>
  {op}
  <p>If you use SNYPD as a consumer, nothing in these terms takes away the rights consumer law gives you.</p>
</section>
<section id="service">
  <h2>What SNYPD does</h2>
  <p>You save Vinted catalogue searches in SNYPD. SNYPD checks them regularly, shows new matching listings in your dashboard and, if you turn alerts on, sends notifications.</p>
  <ul>
    <li>SNYPD <strong>never</strong> asks for your Vinted password, logs into your Vinted account, buys, makes offers or messages sellers. Every purchase is yours to make on Vinted, under Vinted's own terms.</li>
    <li>SNYPD is independent and <strong>not affiliated with or endorsed by Vinted</strong>.</li>
    <li>Searches are checked between every 30 seconds and every few minutes, faster for busier searches. We work hard to catch every new listing quickly, but we cannot guarantee that you see every listing or that you see it before anyone else. Vinted can change or limit its website at any time, which can slow or interrupt SNYPD.</li>
  </ul>
</section>
<section id="account">
  <h2>Your account</h2>
  <p>You must be at least 16. Give a real email address, keep your password to yourself, and use one account per person. You are responsible for what happens under your account. Tell us straight away if you think someone else has access to it.</p>
</section>
<section id="plans">
  <h2>Plans and billing</h2>
  <div class="lg-rows">
    <div class="lg-row lg-rh"><span>Plan</span><span>What you get</span><span>Price</span></div>
    <div class="lg-row"><span>Free</span><span data-l="WHAT:">1 search, checked only while your dashboard is open</span><span data-l="PRICE:">&euro;0</span></div>
    <div class="lg-row"><span>Kickstart</span><span data-l="WHAT:">2 searches, checked 24/7, even with your dashboard closed</span><span data-l="PRICE:">&euro;14.99 / month</span></div>
    <div class="lg-row"><span>Pro</span><span data-l="WHAT:">5 searches, checked 24/7, Market Report price checks, paid Discord access</span><span data-l="PRICE:">&euro;24.99 / month</span></div>
    <div class="lg-row"><span>Elite</span><span data-l="WHAT:">Everything in Pro, with 10 searches</span><span data-l="PRICE:">&euro;34.99 / month</span></div>
  </div>
  <p>Prices include VAT. Paid plans are sold through <strong>Whop</strong>, which takes the payment by card, Apple Pay or Google Pay and renews your plan every month until you cancel. Your receipt shows who charged the payment and the VAT.</p>
  <p>You can cancel any time in your Whop account (the "Manage subscription" link in SNYPD). Your plan then stays active until the end of the month you paid for and does not renew. We do not refund the rest of a month after you cancel, except under the 14-day refund below.</p>
  <p>If we raise the price of a plan you have, we tell you at least 30 days before your next renewal at the new price, and you can cancel before then.</p>
</section>
<section id="founding">
  <h2>Founding members</h2>
  <p>The first 100 SNYPD accounts, free accounts included, are founding members and keep Pro pricing for life: if the price of the Pro plan ever goes up, a founding member can keep subscribing to Pro at &euro;24.99 a month for as long as their SNYPD account exists.</p>
</section>
<section id="refund">
  <h2>Refunds and withdrawal</h2>
  <p><strong>14-day refund.</strong> If you are not happy, email us within 14 days of the first payment for a plan and we refund that payment in full, no questions asked. We refund to the payment method you used, within 14 days of your request. This includes, and goes further than, the right of withdrawal that EU consumers have for online contracts.</p>
  <p>To withdraw, send us a clear statement, for example an email to <a href="mailto:{email}">{email}</a>. You can use this model form, but you do not have to:</p>
  <div class="lg-form">{form}</div>
  <p>A refund ends the plan it paid for; your account returns to the free plan.</p>
</section>
<section id="use">
  <h2>Fair use</h2>
  <p>Do not:</p>
  <ul>
    <li>use SNYPD to follow or collect data about a particular person or seller;</li>
    <li>share, resell or rent out your account or access to it;</li>
    <li>copy, scrape or overload SNYPD, or get around its plan limits or security;</li>
    <li>use SNYPD for anything illegal.</li>
  </ul>
  <p>If you break these rules, we may suspend or close your account.</p>
</section>
<section id="market">
  <h2>Market prices</h2>
  <p>The Market Report shows estimates calculated from public Vinted listings over the last 14 days, including listings that did not sell. They are a guide, not a promise that you will buy or sell at that price, and not financial advice.</p>
</section>
<section id="liability">
  <h2>Liability</h2>
  <p>SNYPD is provided as it is. We are not responsible for purchases you make on Vinted, for listings you miss, or for what Vinted or sellers do. Our total liability to you is limited to what you paid us in the 12 months before the problem. These limits do not apply where the law does not allow them, for example for death or personal injury we cause, for fraud, for intent or gross negligence, or for rights you have as a consumer that cannot be excluded.</p>
</section>
<section id="end">
  <h2>Ending the agreement</h2>
  <p>You can stop at any time: cancel your plan, and ask us to delete your account. We may end the free plan or the service with 30 days' notice. If we end a paid plan, we refund the unused part.</p>
</section>
<section id="law">
  <h2>Law and disputes</h2>
  <p>These terms are governed by Belgian law. If you are a consumer living in another EU country, you also keep the protection of your own country's mandatory consumer law, and you can take a dispute to the courts where you live. Please contact us first: most problems are solved faster by email or in our <a href="{discord}">Discord</a>.</p>
</section>
<section id="changes">
  <h2>Changes</h2>
  <p>We may update these terms, for example when SNYPD gains new features. If a change affects you, we tell you at least 30 days in advance by email or in the dashboard. If you do not agree, you can cancel before it takes effect.</p>
</section>"""
