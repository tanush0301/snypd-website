"""French app text: whole English on-screen text -> French. Tu-form, like the French SEO pages.

Keys must be the text exactly as it appears on screen (whitespace collapsed). Find missing ones
with ?i18n_collect=1 (see gen_i18n.py). French typography: no-break space (NB) before
? ! : ; and inside guillemets. Never: "instantane", "temps reel", "le plus rapide", "sur",
"autorise par Vinted" (fact-sheet rules apply here too).
Scope 9 Oct 2026 (phase 1): sign-up/login/reset, cookie banner, dashboard main screen, first-hunt
wizard, hunt sheet + link errors, alerts step, feed basics. Phase 2 (History, Market Insights,
XP/ranks, claim sheets, profile details) is not here yet and stays English.
"""

NB = ' '

FR = {
    # ---------------------------------------------------------------- auth pages (auth.js + template)
    'Sign up free - SNYPD Vinted Monitor': 'Inscription gratuite - SNYPD, monitor Vinted',
    'Log in to SNYPD': 'Connexion à SNYPD',
    'Reset your password - SNYPD': 'Réinitialiser ton mot de passe - SNYPD',
    'Set a new password - SNYPD': 'Nouveau mot de passe - SNYPD',
    'Reset link expired - SNYPD': 'Lien expiré - SNYPD',
    '← BACK TO SITE': '← RETOUR AU SITE',
    'Create your free account': 'Crée ton compte gratuit',
    'Free plan, no card.': 'Plan gratuit, sans carte.',
    'SELECTED OFFER': 'OFFRE CHOISIE',
    '€3.99 once · 30 days · no automatic renewal': '3,99' + NB + '€ en une fois · 30 jours · sans renouvellement automatique',
    '€5.99/month · renews monthly until you cancel': '5,99' + NB + '€/mois · renouvelé chaque mois jusqu’à résiliation',
    '€14.99/month · renews monthly until you cancel': '14,99' + NB + '€/mois · renouvelé chaque mois jusqu’à résiliation',
    '€24.99/month · renews monthly until you cancel': '24,99' + NB + '€/mois · renouvelé chaque mois jusqu’à résiliation',
    '€34.99/month · renews monthly until you cancel': '34,99' + NB + '€/mois · renouvelé chaque mois jusqu’à résiliation',
    'Account first, then your hunt and secure checkout. Creating your account does not take a payment.':
        'D’abord le compte, puis ta recherche et le paiement sécurisé. La création du compte n’entraîne aucun paiement.',
    'Switch to Solo for €5.99/month, or buy another €3.99 Pass after this one expires. Until then, your current Pass keeps running.':
        'Passe à Solo pour 5,99' + NB + '€/mois, ou achète un autre Pass à 3,99' + NB + '€ après son expiration. D’ici là, ton Pass actuel reste actif.',
    'See options': 'Voir les options',
    'Hunt Pass: €3.99 once for 30 days, with no automatic renewal. Paid access starts when your payment is activated.':
        'Pass 30 jours' + NB + ': 3,99' + NB + '€ en une fois pour 30 jours, sans renouvellement automatique. L’accès payant commence à l’activation de ton paiement.',
    'Solo: €5.99/month, renewed monthly until you cancel. Paid access starts when your payment is activated.':
        'Solo' + NB + ': 5,99' + NB + '€/mois, renouvelé chaque mois jusqu’à résiliation. L’accès payant commence à l’activation de ton paiement.',
    'all 100 founding spots claimed': 'les 100 places fondateur sont prises',
    'You picked': 'Tu as choisi',
    '. You start on Free; upgrade in one click from the dashboard.': '. Tu commences en Free' + NB + '; passe au plan payant en un clic depuis le tableau de bord.',
    'Reset your password': 'Réinitialise ton mot de passe',
    "Enter your account email. We'll send a link to set a new password.": 'Saisis l’e-mail de ton compte. On t’envoie un lien pour choisir un nouveau mot de passe.',
    'Check your inbox': 'Regarde ta boîte mail',
    'If an account exists for': 'Si un compte existe pour',
    ", we've sent a password reset link.": ', on vient d’envoyer un lien de réinitialisation.',
    'ACCOUNT CREATED · 1 STEP LEFT': 'COMPTE CRÉÉ · ENCORE 1 ÉTAPE',
    'Check your email': 'Regarde tes e-mails',
    'We sent a confirmation link to': 'On a envoyé un lien de confirmation à',
    '. Open it to finish, then set up your first hunt.': '. Ouvre-le pour terminer, puis crée ta première recherche.',
    '✓ SAVED': '✓ ENREGISTRÉ',
    'Password updated': 'Mot de passe modifié',
    "You're signed in with your new password.": 'Tu es connecté avec ton nouveau mot de passe.',
    'This reset link has expired': 'Ce lien a expiré',
    'Reset links work once and expire after a while. Send yourself a new one.': 'Les liens de réinitialisation ne servent qu’une fois et expirent au bout d’un moment. Envoie-toi un nouveau lien.',
    'SEND A NEW LINK': 'ENVOYER UN NOUVEAU LIEN',
    'You opened this inside Instagram or another app. Google sign-in does not work here, so use your email below. Prefer Google? Tap the':
        'Tu as ouvert cette page dans Instagram ou une autre app. La connexion Google n’y fonctionne pas, utilise donc ton e-mail ci-dessous. Tu préfères Google' + NB + '? Touche le menu',
    'menu at the top and open this page in your browser.': 'en haut et ouvre cette page dans ton navigateur.',
    'CONTINUE WITH GOOGLE': 'CONTINUER AVEC GOOGLE',
    'OR': 'OU',
    'EMAIL': 'E-MAIL',
    'PASSWORD': 'MOT DE PASSE',
    'NEW PASSWORD': 'NOUVEAU MOT DE PASSE',
    'CONFIRM PASSWORD': 'CONFIRME LE MOT DE PASSE',
    'Forgot password?': 'Mot de passe oublié' + NB + '?',
    'At least 6 characters': 'Au moins 6 caractères',
    'Show password': 'Afficher le mot de passe',
    'Hide password': 'Masquer le mot de passe',
    'SHOW': 'AFFICHER',
    'HIDE': 'MASQUER',
    'Email me product updates, Vinted tips and occasional offers.': 'Envoie-moi par e-mail les nouveautés du produit, des astuces Vinted et des offres ponctuelles.',
    # "How did you find SNYPD?" on /signup (27 Oct 2026); brand names (ChatGPT, Claude, TikTok...) stay as they are.
    'HOW DID YOU FIND SNYPD?': 'COMMENT AS-TU CONNU SNYPD' + NB + '?',
    '(optional)': '(facultatif)',
    'Choose one': 'Choisis une réponse',
    'Another AI assistant': 'Un autre assistant IA',
    'Google search': 'Recherche Google',
    'A friend': 'Un ami',
    'Somewhere else': 'Ailleurs',
    'LOG IN': 'SE CONNECTER',
    'LOGGING IN…': 'CONNEXION…',
    'CREATE ACCOUNT': 'CRÉER MON COMPTE',
    'CREATING ACCOUNT…': 'CRÉATION DU COMPTE…',
    'SEND RESET LINK': 'ENVOYER LE LIEN',
    'SENDING…': 'ENVOI…',
    'SAVE PASSWORD': 'ENREGISTRER LE MOT DE PASSE',
    'SAVING…': 'ENREGISTREMENT…',
    'RESEND EMAIL': 'RENVOYER L’E-MAIL',
    'RESEND LINK': 'RENVOYER LE LIEN',
    'Still working. Your connection looks slow; keep this tab open.': 'Toujours en cours. Ta connexion semble lente' + NB + '; garde cet onglet ouvert.',
    'By creating an account you agree to the': 'En créant un compte, tu acceptes les',
    'Terms': 'Conditions',
    'and': 'et la',
    'Privacy Policy': 'Politique de confidentialité',
    'Nothing yet? Check spam or Promotions. It can take a minute.': 'Toujours rien' + NB + '? Regarde dans les spams ou Promotions. Ça peut prendre une minute.',
    'No account?': 'Pas de compte' + NB + '?',
    'Create one free': 'Crées-en un gratuitement',
    'Already have an account?': 'Déjà un compte' + NB + '?',
    'Log in': 'Se connecter',
    '← Back to log in': '← Retour à la connexion',
    'Wrong email?': 'Mauvais e-mail' + NB + '?',
    'Start again': 'Recommencer',
    'Never asks for your Vinted password - never logs into your account - only reads public listings.':
        'Ne demande jamais ton mot de passe Vinted - ne se connecte jamais à ton compte - lit uniquement les annonces publiques.',
    'EXAMPLE MATCHES': 'EXEMPLES D’ANNONCES TROUVÉES',
    'EXAMPLE MATCH': 'EXEMPLE',
    'DASHBOARD LAYOUT · SAMPLE LISTINGS': 'TABLEAU DE BORD · ANNONCES D’EXEMPLE',
    'What a match looks like.': 'À quoi ressemble une annonce trouvée.',
    # validation + banners
    'Enter your email.': 'Saisis ton e-mail.',
    'Enter a full email, like name@example.com.': 'Saisis un e-mail complet, comme nom@exemple.com.',
    'Enter your password.': 'Saisis ton mot de passe.',
    'Choose a password (at least 6 characters).': 'Choisis un mot de passe (au moins 6 caractères).',
    'At least 6 characters.': 'Au moins 6 caractères.',
    "Passwords don't match.": 'Les mots de passe ne correspondent pas.',
    "Couldn't reach SNYPD. Check your connection and try again.": 'Impossible de joindre SNYPD. Vérifie ta connexion et réessaie.',
    'Too many attempts in a short time. Wait a minute, then try again.': 'Trop de tentatives en peu de temps. Attends une minute, puis réessaie.',
    "That email and password don't match. Check both, or reset your password.": 'Cet e-mail et ce mot de passe ne correspondent pas. Vérifie les deux, ou réinitialise ton mot de passe.',
    'Reset password': 'Réinitialiser le mot de passe',
    'Resend confirmation email': 'Renvoyer l’e-mail de confirmation',
    'Your session expired. Log in to get back to your hunts.': 'Ta session a expiré. Connecte-toi pour retrouver tes recherches.',
    'That email link has expired or was already used. Log in below, and if your email still needs confirming we will offer a new link.':
        'Ce lien a expiré ou a déjà servi. Connecte-toi ci-dessous' + NB + '; si ton e-mail doit encore être confirmé, on te proposera un nouveau lien.',
    'Signed in. Opening your dashboard…': 'Connecté. Ouverture de ton tableau de bord…',
    'This email already has an account. Taking you to log in…': 'Cet e-mail a déjà un compte. On t’emmène vers la connexion…',
    'Go now': 'Y aller',
    'Sent again. It can take a minute to arrive.': 'Renvoyé. Il peut mettre une minute à arriver.',
    'Something went wrong. Try again.': 'Un problème est survenu. Réessaie.',

    # ---------------------------------------------------------------- cookie banner (consent.js)
    'Cookies.': 'Cookies.',
    'SNYPD only stores what it needs to keep you signed in. With your OK we also use Google Analytics to see how the site is used, and the Whop pixel and Meta Pixel to measure sign-ups from ads and partner links.':
        'SNYPD n’enregistre que ce qu’il faut pour te garder connecté. Avec ton accord, on utilise aussi Google Analytics pour voir comment le site est utilisé, ainsi que le pixel Whop et le pixel Meta pour mesurer les inscriptions venues des pubs et des liens partenaires.',
    'Cookie policy': 'Politique cookies',
    'REJECT ALL': 'TOUT REFUSER',
    'ACCEPT ALL': 'TOUT ACCEPTER',
    'SETTINGS': 'RÉGLAGES',
    'SAVE CHOICES': 'ENREGISTRER MES CHOIX',
    'Cookie choices': 'Choix des cookies',
    'Cookie settings': 'Paramètres des cookies',
    'Full list of cookies': 'Liste complète des cookies',
    'Choose what SNYPD may store on this device. You can change it any time on the cookie policy page or with the "Cookie settings" link in the homepage footer.':
        'Choisis ce que SNYPD peut enregistrer sur cet appareil. Tu peux changer d’avis à tout moment sur la page cookies ou avec le lien «' + NB + 'Paramètres des cookies' + NB + '» en bas de la page d’accueil.',
    'NECESSARY': 'NÉCESSAIRES',
    'ANALYTICS': 'MESURE D’AUDIENCE',
    'MARKETING': 'MARKETING',
    'Keeps you signed in, remembers the plan you picked before checkout and your dashboard settings. The site cannot work without these, so they are always on.':
        'Te gardent connecté, retiennent le plan choisi avant le paiement et les réglages de ton tableau de bord. Le site ne peut pas fonctionner sans eux, ils sont donc toujours actifs.',
    'Google Analytics 4: which pages are visited and how people find SNYPD. Google receives your IP address and browser details.':
        'Google Analytics 4' + NB + ': les pages visitées et la façon dont on trouve SNYPD. Google reçoit ton adresse IP et les infos de ton navigateur.',
    'Whop pixel and Meta Pixel: measure sign-ups that came from ads (including Facebook and Instagram ads) and partner links. Meta receives your IP address, browser details and the SNYPD pages you visit. Also remembers the partner code in a partner link you arrived through.':
        'Pixel Whop et pixel Meta' + NB + ': mesurent les inscriptions venues des pubs (y compris Facebook et Instagram) et des liens partenaires. Meta reçoit ton adresse IP, les infos de ton navigateur et les pages SNYPD que tu visites. Retient aussi le code partenaire du lien par lequel tu es arrivé.',

    # ---------------------------------------------------------------- dashboard: top bar, status, plan
    'SNYPD Dashboard': 'Tableau de bord SNYPD',
    'Feed': 'Flux',
    'History': 'Historique',
    'Market Insights': 'Market Insights',
    'Open profile': 'Ouvrir le profil',
    'Profile': 'Profil',
    'Idle': 'Inactif',
    'Running': 'En cours',
    'Stopped': 'Arrêté',
    'Not watching': 'Hors surveillance',
    'SNYPD offline': 'SNYPD hors ligne',
    'Status: Idle': 'Statut' + NB + ': inactif',
    'Status: idle': 'Statut' + NB + ': inactif',
    'Status: running': 'Statut' + NB + ': en cours',
    'Status: stopped': 'Statut' + NB + ': arrêté',
    'Status: activation needed': 'Statut' + NB + ': activation requise',
    'Last check: —': 'Dernière vérification' + NB + ': —',
    'Plan: —': 'Plan' + NB + ': —',
    'Plan: NOT ACTIVE': 'Plan' + NB + ': NON ACTIF',
    'Founding member': 'Membre fondateur',
    'Language': 'Langue',
    'Email': 'E-mail',
    'Joined': 'Inscription',
    'Plan': 'Plan',
    'Sign out': 'Se déconnecter',
    'Account settings': 'Paramètres du compte',
    'Support': 'Support',
    'Notifications': 'Notifications',
    'Push alerts': 'Alertes push',
    'Sold': 'Vendu',
    'Quiet hours': 'Heures calmes',
    'Not available on this device': 'Indisponible sur cet appareil',
    'Yes': 'Oui',
    'No': 'Non',
    # activation panel (account without a plan)
    'Unlock Your Arsenal': 'Débloque ton arsenal',
    'Your SNYPD account is ready. Start the free plan to save your first Vinted search.': 'Ton compte SNYPD est prêt. Active le plan gratuit pour enregistrer ta première recherche Vinted.',
    'Activate Free Plan': 'Activer le plan Free',
    'View Plans': 'Voir les plans',
    'View plans': 'Voir les plans',
    'See plans': 'Voir les plans',
    'Use the same email as your SNYPD account.': 'Utilise le même e-mail que ton compte SNYPD.',
    # feed panel
    'Pull to refresh': 'Tire pour actualiser',
    'Refreshing': 'Actualisation',
    'Start Sniping': 'Démarrer',
    'Running…': 'En cours…',
    'Stop': 'Arrêter',
    'Enable alerts': 'Activer les alertes',
    'Saved vs median': 'Économisé vs médiane',
    'Saved vs median: —': 'Économisé vs médiane' + NB + ': —',
    'Realised profit': 'Bénéfice réalisé',
    'Realised profit: —': 'Bénéfice réalisé' + NB + ': —',
    'Hunts running': 'Recherches actives',
    'Holding': 'En stock',
    "Paid plans hunt while you're away": 'Les plans payants cherchent même quand tu n’es pas là',
    'Free only checks while this tab is open. Paid plans keep hunting 24/7, tab closed or not.': 'Free ne vérifie que lorsque cet onglet est ouvert. Les plans payants cherchent 24h/24, onglet ouvert ou fermé.',
    'Your hunt keeps running with this tab closed until then. After that, Free only checks while this tab is open; paid plans keep hunting 24/7.':
        'D’ici là, ta recherche continue même onglet fermé. Ensuite, Free ne vérifie que lorsque cet onglet est ouvert' + NB + '; les plans payants cherchent 24h/24.',
    "⚠ Can't reach Vinted right now": '⚠ Vinted est injoignable pour le moment',
    "Your hunts are still saved. We'll pick up automatically - nothing found in the meantime is lost, it just isn't shown yet.":
        'Tes recherches sont toujours enregistrées. On reprend automatiquement - rien de ce qui est trouvé entre-temps n’est perdu, ce n’est juste pas encore affiché.',
    "✕ SNYPD offline": '✕ SNYPD hors ligne',
    "We can't reach SNYPD's own servers, so nothing is being checked right now. Your hunts and history are safe - this is on our side, not yours.":
        'On n’arrive pas à joindre les serveurs de SNYPD, donc rien n’est vérifié pour le moment. Tes recherches et ton historique sont en sécurité - le problème vient de chez nous, pas de toi.',
    'No successful sync yet this session': 'Aucune synchro réussie pour l’instant',
    'Retry': 'Réessayer',
    'Tapping': 'Appuyer sur',
    'Claim': 'J’ai acheté',
    'Stock tab': 'Onglet Stock',
    'Show': 'Afficher',
    'Could not load Stock. Reload the page.': 'Impossible de charger le Stock. Recharge la page.',
    'marks an item as bought and tracks it in your': 'marque un article comme acheté et le suit dans ton onglet',
    'tab, where you can later mark it sold, mark it still listed, or remove it if you claimed it by mistake.':
        '— tu pourras ensuite le marquer vendu, toujours en vente, ou le retirer si tu l’as marqué par erreur.',
    'Got it': 'Compris',
    'No results yet. Press “Start Sniping Now”.': 'Aucun résultat pour l’instant. Appuie sur «' + NB + 'Démarrer' + NB + '».',
    'No results yet. Sniping is running…': 'Aucun résultat pour l’instant. La recherche tourne…',
    'A hunt is one saved Vinted search. SNYPD checks it every 30 seconds to 5 minutes and every new match lands here, newest first.':
        'Une recherche SNYPD, c’est une recherche Vinted enregistrée. SNYPD la vérifie toutes les 30 secondes à 5 minutes et chaque nouvelle annonce arrive ici, la plus récente en premier.',
    'Add your first hunt': 'Ajoute ta première recherche',
    'No hunts yet': 'Aucune recherche pour l’instant',
    'No hunts yet. Add one below.': 'Aucune recherche pour l’instant. Ajoutes-en une ci-dessous.',
    '1 new match': '1 nouvelle annonce',
    # feed cards
    'Promoted': 'Sponsorisé',
    'New': 'Nouveau',
    'Drop': 'Baisse',
    'Gone - may have sold': 'Disparu - peut-être vendu',
    'Gone · may have sold': 'Disparu · peut-être vendu',
    'Price unavailable': 'Prix indisponible',
    'View listing': 'Voir l’annonce',
    'Check price': 'Vérifier le prix',
    'Open on Vinted': 'Ouvrir sur Vinted',
    'OPEN ON VINTED': 'OUVRIR SUR VINTED',
    '✓ Claimed': '✓ Acheté',
    'Claimed': 'Acheté',
    'Uploaded on Vinted': 'Publié sur Vinted',
    'First seen by SNYPD': 'Repéré par SNYPD',

    # ---------------------------------------------------------------- hunt sheet (Filters)
    'Filters ·': 'Filtres ·',
    'Your hunts': 'Tes recherches',
    '+ New hunt — brand, size, price cap': '+ Nouvelle recherche — marque, taille, prix max',
    'Set your filters on Vinted in a browser (brand, size, price), copy the address bar and paste it below.':
        'Règle tes filtres sur Vinted dans un navigateur (marque, taille, prix), copie la barre d’adresse et colle-la ci-dessous.',
    'On a phone, the quick search is easiest. To paste a link instead: open Vinted in your browser (not the app), search and set filters, then copy the address bar.':
        'Sur téléphone, la recherche rapide est le plus simple. Pour coller un lien à la place' + NB + ': ouvre Vinted dans ton navigateur (pas l’app), lance ta recherche avec tes filtres, puis copie la barre d’adresse.',
    'Quick search: what are you looking for?': 'Recherche rapide' + NB + ': que cherches-tu' + NB + '?',
    'Which Vinted country': 'Quel pays Vinted',
    'Max price': 'Prix max',
    'Maximum price (optional)': 'Prix maximum (facultatif)',
    'Name — e.g. Ralph Lauren shirts': 'Nom — ex. chemises Ralph Lauren',
    'or paste a Vinted search link': 'ou colle un lien de recherche Vinted',
    'Paste /catalog?... link': 'Colle le lien /catalog?...',
    'Minimum price': 'Prix minimum',
    'Save search': 'Enregistrer la recherche',
    'Done': 'Terminé',
    'PAUSE': 'PAUSE',
    'PAUSED': 'EN PAUSE',
    'LIVE': 'ACTIVE',
    'ACTIVATE': 'ACTIVER',
    'DELETE': 'SUPPRIMER',
    'TITLE MATCH ONLY': 'TITRE UNIQUEMENT',
    'SHOW ALL VINTED RESULTS': 'TOUS LES RÉSULTATS VINTED',
    'Showing everything Vinted returns, including listings that only mention your words in the description.':
        'Affiche tout ce que Vinted renvoie, y compris les annonces qui ne citent tes mots que dans la description.',
    'Showing listings with every word of your search in the title or brand. Vinted also returns listings that only mention it in the description.':
        'Affiche les annonces qui ont tous les mots de ta recherche dans le titre ou la marque. Vinted renvoie aussi des annonces qui ne les citent que dans la description.',
    "You're using all your active searches. Pause one, or upgrade for more.": 'Tu utilises toutes tes recherches actives. Mets-en une en pause, ou passe à un plan supérieur pour en avoir plus.',
    'Delete this hunt?': 'Supprimer cette recherche' + NB + '?',
    'Vinted search': 'Recherche Vinted',
    'This link sets its own minimum price, so yours is kept as-is.': 'Ce lien fixe déjà son propre prix minimum, il est donc gardé tel quel.',
    'No minimum set. Most Vinted items under about EUR30 are fast fashion, not resale stock.': 'Aucun minimum. La plupart des articles Vinted à moins d’environ 30 EUR sont de la fast fashion, pas du stock à revendre.',
    # link errors (what the dashboard says about a pasted link)
    'SNYPD needs a normal https Vinted link. Copy it again from the address bar.': 'SNYPD a besoin d’un lien Vinted https normal. Copie-le à nouveau depuis la barre d’adresse.',
    'This is not a Vinted search link. Run the search on Vinted and copy the address of the results page.': 'Ce n’est pas un lien de recherche Vinted. Lance la recherche sur Vinted et copie l’adresse de la page de résultats.',
    'The price in this link is not a plain number. Set the price again on Vinted and copy the link.': 'Le prix dans ce lien n’est pas un simple nombre. Règle à nouveau le prix sur Vinted et copie le lien.',
    'Type what you are looking for in the quick search above, or paste a Vinted search link.': 'Tape ce que tu cherches dans la recherche rapide au-dessus, ou colle un lien de recherche Vinted.',
    'That is not a complete link. Copy the whole address from Vinted, starting with https://': 'Ce lien n’est pas complet. Copie toute l’adresse depuis Vinted, en commençant par https://',
    'That is not a link. Type your words in the quick search above instead.': 'Ce n’est pas un lien. Tape plutôt tes mots dans la recherche rapide au-dessus.',
    'That is not a Vinted link. Search on Vinted in your browser and copy the address of the results page.': 'Ce n’est pas un lien Vinted. Lance ta recherche sur Vinted dans ton navigateur et copie l’adresse de la page de résultats.',
    'That is one listing, not a search. Search on Vinted, then copy the address of the results page.': 'C’est une annonce, pas une recherche. Lance une recherche sur Vinted, puis copie l’adresse de la page de résultats.',
    'That is not a Vinted search link. Run a search on Vinted and copy the address of the results page (it contains /catalog).': 'Ce n’est pas un lien de recherche Vinted. Lance une recherche sur Vinted et copie l’adresse de la page de résultats (elle contient /catalog).',
    'This search has no words or filters yet. Add at least one on Vinted, then copy the link again.': 'Cette recherche n’a encore ni mots ni filtres. Ajoutes-en au moins un sur Vinted, puis copie à nouveau le lien.',
    # countries (the quick-search country list)
    'Austria': 'Autriche', 'Belgium': 'Belgique', 'Croatia': 'Croatie', 'Czechia': 'Tchéquie', 'Denmark': 'Danemark',
    'Estonia': 'Estonie', 'Finland': 'Finlande', 'Germany': 'Allemagne', 'Greece': 'Grèce', 'Hungary': 'Hongrie',
    'Ireland': 'Irlande', 'Italy': 'Italie', 'Latvia': 'Lettonie', 'Lithuania': 'Lituanie', 'Netherlands': 'Pays-Bas',
    'Poland': 'Pologne', 'Romania': 'Roumanie', 'Slovakia': 'Slovaquie', 'Slovenia': 'Slovénie', 'Spain': 'Espagne',
    'Sweden': 'Suède', 'United Kingdom': 'Royaume-Uni', 'United States': 'États-Unis',

    # ---------------------------------------------------------------- first-hunt wizard
    'Step 1 of 2': 'Étape 1 sur 2',
    'Step 2 / 2': 'Étape 2 / 2',
    'What are you hunting?': 'Que cherches-tu' + NB + '?',
    'Type what you want. SNYPD runs that search on Vinted for you, no link needed. You can add more from Filters anytime.':
        'Tape ce que tu veux. SNYPD lance cette recherche sur Vinted pour toi, sans lien. Tu peux en ajouter d’autres depuis Filtres à tout moment.',
    'e.g. ralph lauren, jordan 4, carhartt jacket': 'ex. ralph lauren, jordan 4, veste carhartt',
    'What are you looking for?': 'Que cherches-tu' + NB + '?',
    'Start this hunt': 'Lancer cette recherche',
    'I have a Vinted link': 'J’ai un lien Vinted',
    'Type at least one word, for example a brand.': 'Tape au moins un mot, par exemple une marque.',
    'How should we tell you?': 'Comment te prévenir' + NB + '?',
    'We check your hunt every 30 s to 5 min and send a push when a new listing matches.': 'On vérifie ta recherche toutes les 30 s à 5 min et on t’envoie une notification push quand une nouvelle annonce correspond.',
    'Push notification': 'Notification push',
    'on your phone or computer': 'sur ton téléphone ou ton ordinateur',
    'Turn on alerts & start hunting': 'Activer les alertes et démarrer',
    'Set this up later': 'Plus tard',
    'Free plan: SNYPD checks only while it is open on this device. Paid plans run 24/7.': 'Plan Free' + NB + ': SNYPD ne vérifie que lorsqu’il est ouvert sur cet appareil. Les plans payants tournent 24h/24.',
    'Turning alerts on...': 'Activation des alertes...',
    'Continue without alerts': 'Continuer sans alertes',
    'Alerts could not be turned on on this device.': 'Impossible d’activer les alertes sur cet appareil.',
    'I have read that, let me in': 'J’ai lu, je continue',

    # ---------------------------------------------------------------- alerts (push) messages
    'Working...': 'Un instant...',
    'Checking this device...': 'Vérification de cet appareil...',
    'Alerts on - turn off': 'Alertes activées - désactiver',
    'Alerts unavailable': 'Alertes indisponibles',
    'Alerts blocked': 'Alertes bloquées',
    'Open in Safari for alerts': 'Ouvre dans Safari pour les alertes',
    'Add to Home Screen for alerts': 'Ajoute à l’écran d’accueil pour les alertes',
    'Still setting up alerts.': 'Configuration des alertes en cours.',
    'Alerts are not available in this browser.': 'Les alertes ne sont pas disponibles dans ce navigateur.',
    'Notifications are blocked for this site. Turn them back on in your browser settings for snypd.store, then press the button again.':
        'Les notifications sont bloquées pour ce site. Réactive-les dans les réglages de ton navigateur pour snypd.store, puis appuie à nouveau sur le bouton.',
    'Your browser did not allow notifications. Allow them for snypd.store, then press Enable alerts on the dashboard.':
        'Ton navigateur n’a pas autorisé les notifications. Autorise-les pour snypd.store, puis appuie sur Activer les alertes dans le tableau de bord.',
    'This device will be alerted when a listing matches, even with the browser closed.': 'Cet appareil sera prévenu quand une annonce correspond, même navigateur fermé.',
    'Alerts are on for this device.': 'Les alertes sont activées sur cet appareil.',
    'Alerts are off for this device.': 'Les alertes sont désactivées sur cet appareil.',
    'Alerts are already on for this device.': 'Les alertes sont déjà activées sur cet appareil.',
    'Alerts are already off for this device.': 'Les alertes sont déjà désactivées sur cet appareil.',
    'Could not turn alerts off. Try again.': 'Impossible de désactiver les alertes. Réessaie.',
    'You opened SNYPD inside Instagram or Facebook, which cannot add it to your Home Screen. Tap the ... menu at the top, open this page in Safari, then tap Share and "Add to Home Screen".':
        'Tu as ouvert SNYPD dans Instagram ou Facebook, qui ne peuvent pas l’ajouter à ton écran d’accueil. Touche le menu ... en haut, ouvre cette page dans Safari, puis touche Partager et «' + NB + 'Sur l’écran d’accueil' + NB + '».',
    'On iPhone and iPad, alerts only work once SNYPD is on your Home Screen. Tap the Share button, then "Add to Home Screen", and open SNYPD from that icon. Apple does not allow websites to do this step for you.':
        'Sur iPhone et iPad, les alertes ne fonctionnent qu’une fois SNYPD sur ton écran d’accueil. Touche le bouton Partager, puis «' + NB + 'Sur l’écran d’accueil' + NB + '», et ouvre SNYPD depuis cette icône. Apple ne permet pas à un site de faire cette étape à ta place.',
    'Alerts are not available in this app right now. Try removing SNYPD from your Home Screen and adding it again.':
        'Les alertes ne sont pas disponibles dans cette app pour le moment. Retire SNYPD de ton écran d’accueil et ajoute-le à nouveau.',
    'Alerts are not available in this app. Remove SNYPD from your Home Screen and add it again.':
        'Les alertes ne sont pas disponibles dans cette app. Retire SNYPD de ton écran d’accueil et ajoute-le à nouveau.',
    'You opened SNYPD inside Instagram or Facebook, which cannot deliver alerts. Tap the ... menu at the top and open this page in Chrome or your phone browser.':
        'Tu as ouvert SNYPD dans Instagram ou Facebook, qui ne peuvent pas recevoir d’alertes. Touche le menu ... en haut et ouvre cette page dans Chrome ou le navigateur de ton téléphone.',
    'This browser cannot deliver alerts. Chrome or Edge on desktop can, and so can SNYPD installed to a phone home screen.':
        'Ce navigateur ne peut pas recevoir d’alertes. Chrome ou Edge sur ordinateur le peuvent, tout comme SNYPD installé sur l’écran d’accueil d’un téléphone.',
    'You opened SNYPD inside Instagram or Facebook. Tap the ... menu at the top, open this page in Safari, then tap Share and Add to Home Screen.':
        'Tu as ouvert SNYPD dans Instagram ou Facebook. Touche le menu ... en haut, ouvre cette page dans Safari, puis touche Partager et Sur l’écran d’accueil.',
    'On iPhone and iPad, alerts only work once SNYPD is on your Home Screen. Tap Share, then Add to Home Screen, and open SNYPD from that icon. Apple does not let a website do this step for you.':
        'Sur iPhone et iPad, les alertes ne fonctionnent qu’une fois SNYPD sur ton écran d’accueil. Touche Partager, puis Sur l’écran d’accueil, et ouvre SNYPD depuis cette icône. Apple ne permet pas à un site de faire cette étape à ta place.',
    'You opened SNYPD inside Instagram or Facebook. Tap the ... menu at the top, open this page in Safari, then tap Share and Add to Home Screen. Then log in once more inside the new SNYPD icon and tap Enable alerts. Your hunt keeps running in the meantime.':
        'Tu as ouvert SNYPD dans Instagram ou Facebook. Touche le menu ... en haut, ouvre cette page dans Safari, puis touche Partager et Sur l’écran d’accueil. Connecte-toi ensuite une fois de plus depuis la nouvelle icône SNYPD et touche Activer les alertes. Ta recherche continue de tourner en attendant.',
    'On iPhone and iPad, alerts only work once SNYPD is on your Home Screen. Tap Share, then Add to Home Screen, and open SNYPD from that icon. Apple does not let a website do this step for you. Then log in once more inside the new SNYPD icon and tap Enable alerts. Your hunt keeps running in the meantime.':
        'Sur iPhone et iPad, les alertes ne fonctionnent qu’une fois SNYPD sur ton écran d’accueil. Touche Partager, puis Sur l’écran d’accueil, et ouvre SNYPD depuis cette icône. Apple ne permet pas à un site de faire cette étape à ta place. Connecte-toi ensuite une fois de plus depuis la nouvelle icône SNYPD et touche Activer les alertes. Ta recherche continue de tourner en attendant.',
    'Alerts are not ready on this account yet. Try again shortly.': 'Les alertes ne sont pas encore prêtes sur ce compte. Réessaie dans un instant.',
    'Could not reach the alert service. Try again shortly.': 'Impossible de joindre le service d’alertes. Réessaie dans un instant.',
    'Notifications are blocked for snypd.store in this browser. Re-allow them in your browser settings to use alerts.':
        'Les notifications sont bloquées pour snypd.store dans ce navigateur. Réautorise-les dans les réglages de ton navigateur pour utiliser les alertes.',
    'Your browser has blocked notifications for snypd.store. Re-allow them in browser settings, then try again.':
        'Ton navigateur a bloqué les notifications pour snypd.store. Réautorise-les dans ses réglages, puis réessaie.',
    'Tip: add SNYPD to your Home Screen (Share -> Add to Home Screen) so alerts keep arriving when Safari is closed.':
        'Astuce' + NB + ': ajoute SNYPD à ton écran d’accueil (Partager -> Sur l’écran d’accueil) pour que les alertes arrivent même Safari fermé.',
    'Add SNYPD to your Home Screen to get alerts.': 'Ajoute SNYPD à ton écran d’accueil pour recevoir les alertes.',
    'Alerts could not be set up on this device.': 'Impossible de configurer les alertes sur cet appareil.',
}

_MONTHS_EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
_MONTHS_FR = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']

# (JS regex on the collapsed text, replacement with $1..). They run in order and each one sees the
# previous result, so later ones can finish what an earlier one left in English.
FR_PATTERNS = [
    # numbers and plans
    (r'^Last check: (.+)$', 'Dernière vérification' + NB + ': $1'),
    (r'^Plan: (FREE|SOLO|KICKSTART|PRO|ELITE)$', 'Plan' + NB + ': $1'),
    (r'^(\d+) OF (\d+) · (FREE|SOLO|KICKSTART|PRO|ELITE)$', '$1 SUR $2 · $3'),
    (r'^Founding #(\d+)$', 'Fondateur #$1'),
    (r'^(\d+) new matches$', '$1 nouvelles annonces'),
    (r'^Saved vs median · 1 claims?$', 'Économisé vs médiane · 1 achat'),
    (r'^Saved vs median · (\d+) claims$', 'Économisé vs médiane · $1 achats'),
    (r'^Realised profit · (\d+) sold$', 'Bénéfice réalisé · $1 vendu(s)'),
    (r'^(\d+) · (\d+) stale$', '$1 · $2 ancien(s)'),
    (r'(^|\s)Day (\d+)( ·)', '$1Jour $2$3'),
    (r'^Day (\d+) of the hunt$', 'Jour $1 de traque'),
    (r'^Yes · #(\d+)$', 'Oui · #$1'),
    (r'^Hold alerts (.+) UTC$', 'Pause des alertes $1 UTC'),
    (r'^(\d[\d,]*) XP to (.+)$', 'encore $1 XP pour $2'),
    # trial
    (r'^Free 24/7 trial: 1 day left$', 'Essai Free 24h/24' + NB + ': encore 1 jour'),
    (r'^Free 24/7 trial: (\d+) days left$', 'Essai Free 24h/24' + NB + ': encore $1 jours'),
    (r'^Free plan: for the next 1 day this hunt runs 24/7, even with SNYPD closed, and alerts reach this device\. After that, Free checks only while SNYPD is open\.$',
     'Plan Free' + NB + ': pendant encore 1 jour, cette recherche tourne 24h/24, même SNYPD fermé, et les alertes arrivent sur cet appareil. Ensuite, Free ne vérifie que lorsque SNYPD est ouvert.'),
    (r'^Free plan: for the next (\d+) days this hunt runs 24/7, even with SNYPD closed, and alerts reach this device\. After that, Free checks only while SNYPD is open\.$',
     'Plan Free' + NB + ': pendant les $1 prochains jours, cette recherche tourne 24h/24, même SNYPD fermé, et les alertes arrivent sur cet appareil. Ensuite, Free ne vérifie que lorsque SNYPD est ouvert.'),
    # price floor notes
    (r"^Like Vinted's own search, this includes listings that mention your words only in the description\. Starts at about (.+?) to skip cheap fast fashion; change it later in Filters\.$",
     'Comme la recherche de Vinted, elle inclut les annonces qui citent tes mots seulement dans la description. Elle démarre à environ $1 pour écarter la fast fashion bon marché' + NB + '; tu peux changer ça plus tard dans Filtres.'),
    (r"^Like Vinted's own search, this includes listings that mention your words only in the description\. Starts at (.+?) to skip cheap fast fashion; change it later in Filters\.$",
     'Comme la recherche de Vinted, elle inclut les annonces qui citent tes mots seulement dans la description. Elle démarre à $1 pour écarter la fast fashion bon marché' + NB + '; tu peux changer ça plus tard dans Filtres.'),
    (r'^Will watch items from (.+) up\. Clear the box to watch everything\.$', 'Surveille les articles à partir de $1. Vide la case pour tout surveiller.'),
    # link errors with a value in them
    (r'^SNYPD cannot read the "(.+)" filter in this link( yet)?, so it would never run\. Remove that filter on Vinted and copy the link again\.$',
     'SNYPD ne sait pas lire le filtre «' + NB + '$1' + NB + '» de ce lien, la recherche ne tournerait donc jamais. Retire ce filtre sur Vinted et copie à nouveau le lien.'),
    (r'^This link sets "(.+)" twice with different values\. Copy it again from Vinted\.$',
     'Ce lien définit «' + NB + '$1' + NB + '» deux fois avec des valeurs différentes. Copie-le à nouveau depuis Vinted.'),
    (r'^This link is set to (\w+), but (\S+) lists prices in (\w+), so SNYPD cannot run it\. Switch the currency to (\w+) on Vinted and copy the link again\.$',
     'Ce lien est en $1, mais $2 affiche les prix en $3, donc SNYPD ne peut pas le lancer. Passe la devise en $4 sur Vinted et copie à nouveau le lien.'),
    (r'^This link asks for items from (.+?) to (.+?), so the lowest price is above the highest and Vinted returns nothing\. Fix the price range on Vinted and copy the link again\.$',
     'Ce lien demande des articles de $1 à $2, donc le prix le plus bas est au-dessus du prix le plus haut et Vinted ne renvoie rien. Corrige la fourchette de prix sur Vinted et copie à nouveau le lien.'),
    (r'^(\S+) is not a Vinted site SNYPD watches\. SNYPD watches every Vinted site in Europe and the US: search on one of those and paste that link\.$',
     '$1 n’est pas un site Vinted surveillé par SNYPD. SNYPD surveille tous les sites Vinted d’Europe et des États-Unis' + NB + ': lance ta recherche sur l’un d’eux et colle ce lien.'),
    (r'^(\S+) is not a Vinted site SNYPD watches, so this hunt cannot find anything\. Recreate it with a link from a Vinted site in Europe or the US\.$',
     '$1 n’est pas un site Vinted surveillé par SNYPD, cette recherche ne peut donc rien trouver. Recrée-la avec un lien d’un site Vinted d’Europe ou des États-Unis.'),
    (r'^This hunt cannot run\. (.+) Then delete this hunt and add the new link\.$', 'Cette recherche ne peut pas tourner. $1 Supprime-la ensuite et ajoute le nouveau lien.'),
    (r'^Could not save this hunt(.*)\. Check your connection and try again\.$', 'Impossible d’enregistrer cette recherche$1. Vérifie ta connexion et réessaie.'),
    # alert errors with a reason in them (the reason itself stays as the browser wrote it)
    (r'^Alerts are not ready on this account yet \(status (\d+)\)\. Try again shortly\.$', 'Les alertes ne sont pas encore prêtes sur ce compte (statut $1). Réessaie dans un instant.'),
    (r'^Could not turn alerts on: (.+)$', 'Impossible d’activer les alertes' + NB + ': $1'),
    (r'^Could not set up alerts on this device: (.+)$', 'Impossible de configurer les alertes sur cet appareil' + NB + ': $1'),
    (r'^Could not set up alerts: (.+)$', 'Impossible de configurer les alertes' + NB + ': $1'),
    (r'^Could not check alert status: (.+)$', 'Impossible de vérifier l’état des alertes' + NB + ': $1'),
    (r'unknown error\.?$', 'erreur inconnue.'),
    # sign-up / login with a value in them
    (r'^FOUNDING · (\d+) of the first 100 spots left$', 'FONDATEUR · encore $1 places sur les 100 premières'),
    (r'^RESEND IN 0:(\d\d)$', 'RENVOYER DANS 0:$1'),
    (r'^Confirm your email first\. We sent a link to (.+)\.$', 'Confirme d’abord ton e-mail. On a envoyé un lien à $1.'),
    (r'^You already have an account with (.+)\. Log in below\.$', 'Tu as déjà un compte avec $1. Connecte-toi ci-dessous.'),
    (r'^Something went wrong: (.+)\. Try again\.$', 'Un problème est survenu' + NB + ': $1. Réessaie.'),
    # time
    (r'^Quiet right now — last match (.+) ago\.$', 'Calme pour l’instant — dernière annonce il y a $1.'),
    (r'il y a under a minute', 'il y a moins d’une minute'),
    (r'il y a a while', 'il y a un moment'),
    (r'il y a 1 hour\b', 'il y a 1 heure'),
    (r'il y a (\d+) hours\b', 'il y a $1 heures'),
    (r'^Last sync (\S+) · ', 'Dernière synchro $1 · '),
    (r'· just now$', '· à l’instant'),
    (r'· 1 min ago$', '· il y a 1 min'),
    (r'· (\d+) min ago$', '· il y a $1 min'),
    (r'· 1 hour ago$', '· il y a 1 heure'),
    (r'· (\d+) hours ago$', '· il y a $1 heures'),
    # feed card line: "brand • size • condition • Promoted • Seen 5m ago"
    (r'(^|• )Promoted( •|$)', '$1Sponsorisé$2'),
    (r'(^|• )Seen just now$', '$1vu à l’instant'),
    (r'(^|• )Seen (\d+)m ago$', '$1vu il y a $2 min'),
    (r'(^|• )Seen (\d+)h ago$', '$1vu il y a $2 h'),
    (r'(^|• )Seen (\d+)d ago$', '$1vu il y a $2 j'),
    (r'(^|• )just now$', '$1à l’instant'),
    (r'(^|• )(\d+)m ago$', '$1il y a $2 min'),
    (r'(^|• )(\d+)h ago$', '$1il y a $2 h'),
    (r'(^|• )(\d+)d ago$', '$1il y a $2 j'),
    (r'^(.+) incl\. protection$', '$1 protection incluse'),
]

# "As of 9 Oct 2026" and "... since 17 Sept 2026" on the sign-up/login stats panel.
for _en, _fr in zip(_MONTHS_EN, _MONTHS_FR):
    FR_PATTERNS.append((r'^As of (\d+) ' + _en + r' (\d{4})$', 'Au $1 ' + _fr + ' $2'))
    FR_PATTERNS.append((r"^Vinted listings matched to users' searches since (\d+) " + _en + r' (\d{4})$',
                        'Annonces Vinted correspondant aux recherches des utilisateurs depuis le $1 ' + _fr + ' $2'))

# ====================================================================== phase 2 (9 Oct 2026, Session 51)
# History, claim/review sheets, profile, ranks, Market Insights. Rank names (Bronze Hunter ...) stay English
# on purpose: they are names, like the plan names.
FR.update({
    # History tab
    'All': 'Tout',
    'Claimed item': 'Article acheté',
    'Sold for': 'Vendu à',
    'Mark sold': 'Marquer vendu',
    'Remove': 'Retirer',
    'still listed': 'toujours en vente',
    'sold elsewhere': 'vendu ailleurs',
    '→ sold': '→ vendu',
    'Claimed by mistake? Remove it.': 'Marqué par erreur' + NB + '? Retire-le.',
    'Quality bonus pending market data': 'Bonus qualité en attente des données du marché',
    'Nothing in Holding yet. Claim a catch from the Feed to start tracking it here.': 'Rien en stock pour l’instant. Marque une trouvaille comme achetée depuis le Flux pour la suivre ici.',
    'Nothing marked sold yet.': 'Rien de marqué vendu pour l’instant.',
    'Could not load your history. Try switching tabs again.': 'Impossible de charger ton historique. Change d’onglet puis reviens.',
    'Remove this from your history? This cannot be undone.': 'Retirer ceci de ton historique' + NB + '? C’est définitif.',
    'Export history as CSV': 'Exporter l’historique en CSV',
    'Could not save - try again': 'Échec de l’enregistrement - réessaie',
    'Saving...': 'Enregistrement...',
    'Profit — not yet': 'Bénéfice — pas encore',
    '1 item held 45 days or more — still yours?': '1 article en stock depuis 45 jours ou plus — tu l’as encore' + NB + '?',
    # review (reconcile) sheet
    'Review': 'Vérifier',
    'Still holding these?': 'Tu as encore ces articles' + NB + '?',
    "These have sat in Holding for 45 days or more. Clearing them keeps your profit number honest - it doesn't affect your saved total or streak.":
        'Ils sont en stock depuis 45 jours ou plus. Les trier garde ton bénéfice exact - ça ne change ni ton total économisé ni ta série.',
    'Still listed': 'Toujours en vente',
    'Sold elsewhere': 'Vendu ailleurs',
    'Add price': 'Ajouter le prix',
    'Sold elsewhere with no price logs the sale and leaves profit blank - you can fill it in later from History.':
        '«' + NB + 'Vendu ailleurs' + NB + '» sans prix enregistre la vente et laisse le bénéfice vide - tu pourras le compléter plus tard depuis l’Historique.',
    "Everything's still listed": 'Tout est encore en vente',
    'Ask me again in 30 days': 'Redemande-moi dans 30 jours',
    # profile
    'On for this device': 'Activées sur cet appareil',
    'Off for this device': 'Désactivées sur cet appareil',
    'Could not change alerts. Try again.': 'Impossible de modifier les alertes. Réessaie.',
    'Could not save quiet hours. Try again.': 'Impossible d’enregistrer les heures calmes. Réessaie.',
    'Top tier reached': 'Rang maximum atteint',
    'Go Elite': 'Passer à Elite',
    'Heartbeat failed': 'Serveur injoignable',
    'Fetch error': 'Erreur de chargement',
    'Show more': 'Voir plus',
    'Recent': 'Récentes',
    'Remove from history': 'Retirer de l’historique',
    # Market Insights
    'Pro & Elite': 'Pro et Elite',
    'Pro & Elite only': 'Pro et Elite uniquement',
    'Median asking price and sample size for any item, computed live across current Vinted listings, broken down by condition.':
        'Prix demandé médian et taille de l’échantillon pour n’importe quel article, calculés en direct sur les annonces Vinted actuelles, détaillés par état.',
    'Search an item, e.g. jordan 1 mid': 'Cherche un article, ex. jordan 1 mid',
    'Market Report is part of Pro and Elite': 'Le Market Report est inclus dans Pro et Elite',
    'See the typical asking price of an item across Vinted right now, broken down by condition, with a warning when the listings are too mixed to trust a single price.':
        'Vois le prix demandé typique d’un article sur Vinted en ce moment, détaillé par état, avec un avertissement quand les annonces sont trop hétérogènes pour donner un seul prix.',
    'Try one of these': 'Essaie l’une de ces recherches',
    'Checking real listings across every condition…': 'Analyse des vraies annonces dans tous les états…',
    'Trusted price': 'Prix fiable',
    'Rough guide only': 'Simple estimation',
    'Not enough data yet': 'Pas encore assez de données',
    'Too mixed to trust': 'Trop hétérogène',
    'Not a real market': 'Pas un vrai marché',
    'See detail': 'Voir le détail',
    'Price by condition': 'Prix par état',
    'Where your price would sit': 'Où se situerait ton prix',
    'Midpoint of what few listings exist': 'Point médian des rares annonces existantes',
    'typical': 'typique',
    'Based on': 'Basé sur',
    'Found': 'On a trouvé',
    'Only': 'Seulement',
    'listings from': 'annonces de',
    'sellers.': 'vendeurs.',
    'sellers, but they run from': 'vendeurs, mais elles vont de',
    'to': 'à',
    'No listings matching': 'Aucune annonce pour',
    'yet. We are not going to invent a price -- if this is a real item, we have started watching it and data should build up.':
        'pour l’instant. On ne va pas inventer un prix -- si c’est un vrai article, on a commencé à le surveiller et les données vont arriver.',
    'listing to go on, running from': 'annonce pour se faire une idée, de',
    'listings to go on, running from': 'annonces pour se faire une idée, de',
    'listing to go on. Rare items are thin here because they are rare on Vinted, so this is a starting point rather than a settled price.':
        'annonce pour se faire une idée. Les articles rares ont peu d’annonces parce qu’ils sont rares sur Vinted' + NB + ': c’est un point de départ, pas un prix établi.',
    'listings to go on. Rare items are thin here because they are rare on Vinted, so this is a starting point rather than a settled price.':
        'annonces pour se faire une idée. Les articles rares ont peu d’annonces parce qu’ils sont rares sur Vinted' + NB + ': c’est un point de départ, pas un prix établi.',
    '. Rare items are thin here because they are rare on Vinted, so this is a starting point rather than a settled price.':
        '. Les articles rares ont peu d’annonces parce qu’ils sont rares sur Vinted' + NB + ': c’est un point de départ, pas un prix établi.',
    'listing found so far -- too few to call a price honestly.': 'annonce trouvée pour l’instant -- trop peu pour annoncer un prix honnêtement.',
    'listings found so far -- too few to call a price honestly.': 'annonces trouvées pour l’instant -- trop peu pour annoncer un prix honnêtement.',
    '. That spread usually means fakes mixed in with real ones, or several different products sharing the same words. No single price would be honest here.':
        '. Un tel écart signifie en général des contrefaçons mêlées aux vrais articles, ou plusieurs produits différents qui partagent les mêmes mots. Aucun prix unique ne serait honnête ici.',
    'of them belong to one seller. That is one seller setting the price, not a market.': 'appartiennent à un seul vendeur. C’est un vendeur qui fixe le prix, pas un marché.',
    'You have used your searches for now. Try again a bit later.': 'Tu as utilisé tes recherches pour le moment. Réessaie un peu plus tard.',
    'That search is too broad. Add a model name or colourway.': 'Cette recherche est trop large. Ajoute un nom de modèle ou un coloris.',
    'Your session expired. Refresh the page and sign in again.': 'Ta session a expiré. Actualise la page et reconnecte-toi.',
    'Could not complete that search. Nothing changed.': 'Impossible de terminer cette recherche. Rien n’a changé.',
    'Could not reach the server.': 'Impossible de joindre le serveur.',
    # condition labels and price bands sent by the backend
    'New, with tag': 'Neuf avec étiquette',
    'New, no tag': 'Neuf sans étiquette',
    'New with tags': 'Neuf avec étiquette',
    'New without tags': 'Neuf sans étiquette',
    'Very good': 'Très bon état',
    'Good': 'Bon état',
    'Satisfactory': 'Satisfaisant',
    'Cheapest quarter': 'Quart le moins cher',
    'Below median': 'Sous la médiane',
    'Above median': 'Au-dessus de la médiane',
    'Below typical': 'Sous le prix typique',
    'Above typical': 'Au-dessus du prix typique',
    'Most expensive quarter': 'Quart le plus cher',
})

# ====================================================================== phase 3: /plans (9 Oct 2026)
# Facts must stay identical to the English page (prices, limits, refund, trial). Plan names stay English.
FR.update({
    'SNYPD Pricing - Vinted Bot Plans from Free to €34.99/month': 'Tarifs SNYPD - plans du bot Vinted, de Free à 34,99' + NB + '€/mois',
    'PLANS & PRICING': 'PLANS ET TARIFS',
    'PRICING': 'TARIFS',
    'Plans': 'Plans',
    'Pick how much SNYPD watches.': 'Choisis combien SNYPD surveille.',
    'Same alert speed on every plan. Paid plans add searches and keep hunting with your dashboard closed. Prices per month, VAT included.':
        'Même vitesse d’alerte sur tous les plans. Les plans payants ajoutent des recherches et continuent de chercher tableau de bord fermé. Prix par mois, TVA incluse.',
    'FIRST 100 ACCOUNTS KEEP PRO PRICING FOR LIFE': 'LES 100 PREMIERS COMPTES GARDENT LE PRIX PRO À VIE',
    'Vinted listings matched for SNYPD hunters so far.': 'annonces Vinted trouvées pour les utilisateurs de SNYPD jusqu’ici.',
    'Jump to a plan': 'Aller à un plan',
    'Show plan': 'Voir le plan',
    'FREE': 'FREE', 'SOLO': 'SOLO', 'KICKSTART': 'KICKSTART', 'PRO': 'PRO', 'ELITE': 'ELITE',
    'For the one or two items you always hunt.': 'Pour les un ou deux articles que tu cherches toujours.',
    'For hunting many brands, sizes or markets at once.': 'Pour chercher plusieurs marques, tailles ou pays à la fois.',
    'For resellers sourcing every day.': 'Pour les revendeurs qui sourcent tous les jours.',
    'Start on one search.': 'Commence avec une recherche.',
    'No card. No time limit.': 'Sans carte. Sans limite de durée.',
    'Everything in Free, plus:': 'Tout Free, plus' + NB + ':',
    'Everything in Kickstart, plus:': 'Tout Kickstart, plus' + NB + ':',
    'Everything in Pro, plus:': 'Tout Pro, plus' + NB + ':',
    '1 active Vinted search': '1 recherche Vinted active',
    '2 active Vinted searches, not 1': '2 recherches Vinted actives, au lieu d’1',
    '5 active Vinted searches, not 2': '5 recherches Vinted actives, au lieu de 2',
    '10 active Vinted searches, not 5': '10 recherches Vinted actives, au lieu de 5',
    '5 active searches': '5 recherches actives',
    '€3.50 per search a month, the lowest of any plan': '3,50' + NB + '€ par recherche et par mois, le plus bas de tous les plans',
    '24/7 for the first 3 days, then while your dashboard is open': '24h/24 les 3 premiers jours, puis tant que ton tableau de bord est ouvert',
    'Keep hunting with the tab closed': 'Continue de chercher onglet fermé',
    'Keeps hunting with the tab closed': 'Continue de chercher onglet fermé',
    'Push alerts around the clock': 'Alertes push 24h/24',
    'Market Report: typical price by condition, before you buy': 'Market Report' + NB + ': prix typique par état, avant d’acheter',
    'Check typical prices before buying': 'Vérifie les prix typiques avant d’acheter',
    'Up to 100 price checks a day': 'Jusqu’à 100 vérifications de prix par jour',
    'Paid Discord channels': 'Salons Discord payants',
    'Free Discord community': 'Communauté Discord gratuite',
    'START FREE': 'COMMENCER GRATUITEMENT',
    'START KICKSTART': 'CHOISIR KICKSTART',
    'START PRO': 'CHOISIR PRO',
    'START ELITE': 'CHOISIR ELITE',
    'Open dashboard →': 'Ouvrir le tableau de bord →',
    'Code applied at checkout for Kickstart and Pro:': 'Code appliqué au paiement pour Kickstart et Pro' + NB + ':',
    'Manage subscription →': 'Gérer l’abonnement →',
    'Your plan:': 'Ton plan' + NB + ':',
    'Free stops when you close the tab.': 'Free s’arrête quand tu fermes l’onglet.',
    'Free has no time limit. Upgrade here when it pays for itself.': 'Free n’a pas de limite de durée. Passe à un plan payant ici quand il est rentable.',
    'Nothing to cancel': 'Rien à résilier',
    'Monthly': 'Mensuel',
    '/ mo': '/ mois',
    'Renews': 'Renouvellement',
    'Until you cancel.': 'Jusqu’à ta résiliation.',
    'Card needed': 'Carte nécessaire',
    # fit quiz
    'YOUR FIT': 'TON PLAN',
    'Not sure? Start with your goal.': 'Tu hésites' + NB + '? Commence par ton objectif.',
    "We'll point at the smallest plan that fits.": 'On t’indique le plus petit plan qui convient.',
    'HOW MANY SEARCHES?': 'COMBIEN DE RECHERCHES' + NB + '?',
    'Try SNYPD on one real search.': 'Essaie SNYPD sur une vraie recherche.',
    'Pause one any time to free the slot.': 'Mets-en une en pause à tout moment pour libérer la place.',
    # comparison table
    'Every detail, side by side.': 'Chaque détail, côte à côte.',
    'SNYPD plans compared. Prices per month, VAT included.': 'Les plans SNYPD comparés. Prix par mois, TVA incluse.',
    'FEATURE': 'FONCTION',
    'Price per month': 'Prix par mois',
    'VAT included.': 'TVA incluse.',
    'Active Vinted searches': 'Recherches Vinted actives',
    'Runs 24/7, dashboard closed': 'Tourne 24h/24, tableau de bord fermé',
    'Runs with your dashboard closed': 'Tourne tableau de bord fermé',
    'Tab open only': 'Onglet ouvert seulement',
    'First 3 days only': '3 premiers jours seulement',
    '24/7 for 3 days, then dashboard open': '24h/24 pendant 3 jours, puis tableau de bord ouvert',
    'Free: 24/7 for the first 3 days after you save your first search, then only while your dashboard is open.':
        'Free' + NB + ': 24h/24 pendant les 3 premiers jours après ta première recherche enregistrée, puis seulement tant que ton tableau de bord est ouvert.',
    'Check speed': 'Vitesse de vérification',
    'About every 30 s (measured median), up to 5 min on quiet searches. Same on every plan.':
        'Environ toutes les 30 s (médiane mesurée), jusqu’à 5 min sur les recherches calmes. Pareil sur tous les plans.',
    'Same': 'Pareil',
    'Push notifications': 'Notifications push',
    'Phone and desktop. On iPhone, add SNYPD to your Home Screen first.': 'Téléphone et ordinateur. Sur iPhone, ajoute d’abord SNYPD à ton écran d’accueil.',
    'Matches in your dashboard': 'Annonces dans ton tableau de bord',
    'Kept about 30 minutes while the listing is up.': 'Gardées environ 30 minutes tant que l’annonce est en ligne.',
    'One alert per listing': 'Une alerte par annonce',
    'The same listing never alerts you twice.': 'La même annonce ne te prévient jamais deux fois.',
    'Every Vinted site in Europe and the US': 'Tous les sites Vinted d’Europe et des États-Unis',
    '26 sites. Prices in that site’s currency.': '26 sites. Prix dans la devise du site.',
    'Market Report price checks': 'Vérifications de prix Market Report',
    'Typical asking price and range, split by condition. Shows no price when the data is too thin.':
        'Prix demandé typique et fourchette, par état. N’affiche aucun prix quand les données sont trop maigres.',
    'Price checks per day': 'Vérifications de prix par jour',
    'Up to 20 an hour.': 'Jusqu’à 20 par heure.',
    'No pushes overnight, if you want.': 'Pas de notifications la nuit, si tu veux.',
    'Founding member': 'Membre fondateur',
    'First 100 accounts, free included. Keep Pro at €24.99 a month for life.': 'Les 100 premiers comptes, gratuits compris. Gardent Pro à 24,99' + NB + '€ par mois à vie.',
    'Included': 'Inclus',
    'Not included': 'Non inclus',
    'YES': 'OUI',
    'Cancel any time': 'Résiliable à tout moment',
    'VAT incl. · monthly · cancel any time': 'TVA incl. · mensuel · résiliable à tout moment',
    # how billing works
    'How billing works.': 'Comment marche la facturation.',
    'BILLING': 'FACTURATION',
    'VAT INCLUDED': 'TVA INCLUSE',
    'The price you see is the price you pay each month. Checkout runs through Whop, which handles the payment and the VAT.':
        'Le prix affiché est celui que tu paies chaque mois. Le paiement passe par Whop, qui gère le paiement et la TVA.',
    'MONTHLY, UNTIL YOU CANCEL': 'MENSUEL, JUSQU’À TA RÉSILIATION',
    'Paid plans renew every month. No annual lock-in, no set-up fee.': 'Les plans payants se renouvellent chaque mois. Pas d’engagement annuel, pas de frais d’installation.',
    '14-DAY REFUND': 'REMBOURSEMENT SOUS 14 JOURS',
    '14-day refund': 'Remboursement sous 14 jours',
    'Not happy? Email': 'Pas satisfait' + NB + '? Écris à',
    'within 14 days of your first payment for a plan and we refund it in full.': 'dans les 14 jours suivant ton premier paiement pour un plan et on te rembourse intégralement.',
    'CANCEL ANY TIME': 'RÉSILIABLE À TOUT MOMENT',
    'In your': 'Dans ton',
    'Whop account': 'compte Whop',
    ', or Account → Manage subscription in SNYPD. Your plan runs to the end of the month you paid for.':
        ', ou Compte → Gérer l’abonnement dans SNYPD. Ton plan continue jusqu’à la fin du mois payé.',
    'Access runs to the end of the paid month.': 'L’accès continue jusqu’à la fin du mois payé.',
    'On your first payment for a plan.': 'Sur ton premier paiement pour un plan.',
    'USE YOUR SNYPD EMAIL': 'UTILISE TON E-MAIL SNYPD',
    'Checkout is filled in with your account email. Keep it, so your plan links to your account straight away.':
        'Le paiement est prérempli avec l’e-mail de ton compte. Garde-le, pour que ton plan soit lié à ton compte tout de suite.',
    'Close checkout': 'Fermer le paiement',
    'KICKSTART checkout': 'Paiement KICKSTART',
    'PRO checkout': 'Paiement PRO',
    'ELITE checkout': 'Paiement ELITE',
    # other tiles / sections
    'HOW IT WORKS': 'COMMENT ÇA MARCHE',
    'MONITORING': 'SURVEILLANCE',
    'ALERTS': 'ALERTES',
    'PRICE DATA': 'DONNÉES DE PRIX',
    'COMMUNITY': 'COMMUNAUTÉ',
    'YOUR VINTED ACCOUNT': 'TON COMPTE VINTED',
    'BUILT FOR DAILY SOURCING': 'CONÇU POUR SOURCER CHAQUE JOUR',
    'Never needed. SNYPD reads public listings only. You buy on Vinted yourself.': 'Jamais nécessaire. SNYPD lit uniquement les annonces publiques. Tu achètes toi-même sur Vinted.',
    'JOIN THE DISCORD': 'REJOINDRE LE DISCORD',
    'DISCORD': 'DISCORD',
    # FAQ
    'FAQ': 'FAQ',
    'Plan questions.': 'Questions sur les plans.',
    'Is Free actually free?': 'Free est vraiment gratuit' + NB + '?',
    'Yes. No card and no time limit. One search: for the first 3 days after you save it, it runs 24/7 with alerts like a paid plan; after that it is checked while your dashboard is open.':
        'Oui. Sans carte et sans limite de durée. Une recherche' + NB + ': pendant les 3 premiers jours après l’avoir enregistrée, elle tourne 24h/24 avec les alertes comme un plan payant' + NB + '; ensuite elle est vérifiée tant que ton tableau de bord est ouvert.',
    'Is there a free trial?': 'Y a-t-il un essai gratuit' + NB + '?',
    'Yes. Free runs your first search 24/7 with alerts for 3 days (72 h), counted from when you save it, with no card. If it finds nothing in that time, we add 2 more days once. After that, Free keeps that one search for as long as you like, checked while your dashboard is open.':
        'Oui. Free fait tourner ta première recherche 24h/24 avec les alertes pendant 3 jours (72' + NB + 'h), à compter de son enregistrement, sans carte. Si elle ne trouve rien pendant ce temps, on ajoute 2 jours de plus, une seule fois. Ensuite, Free garde cette recherche aussi longtemps que tu veux, vérifiée tant que ton tableau de bord est ouvert.',
    'Do paid plans find listings faster?': 'Les plans payants trouvent-ils les annonces plus vite' + NB + '?',
    'No. Every plan checks about every 30 seconds (measured median), up to 5 minutes on quiet searches. Paid plans add searches and keep checking with your dashboard closed.':
        'Non. Tous les plans vérifient environ toutes les 30 secondes (médiane mesurée), jusqu’à 5 minutes sur les recherches calmes. Les plans payants ajoutent des recherches et continuent de vérifier tableau de bord fermé.',
    'Do you need my Vinted login?': 'Vous avez besoin de mes identifiants Vinted' + NB + '?',
    'Never. SNYPD reads public listings only. It never logs in, buys or messages anyone.': 'Jamais. SNYPD lit uniquement les annonces publiques. Il ne se connecte jamais, n’achète rien et n’écrit à personne.',
    'How do I pay?': 'Comment je paie' + NB + '?',
    'By card, or Apple Pay or Google Pay on devices that support them, through Whop’s secure checkout on this page. SNYPD never sees your card details.':
        'Par carte, ou avec Apple Pay ou Google Pay sur les appareils compatibles, via le paiement sécurisé de Whop sur cette page. SNYPD ne voit jamais les données de ta carte.',
    'Does the price include VAT?': 'Le prix inclut-il la TVA' + NB + '?',
    'Yes. €5.99, €14.99, €24.99 and €34.99 a month are the full prices, VAT included. Buying for a company? Tick "buying on behalf of a company" at checkout.':
        'Oui. 5,99' + NB + '€, 14,99' + NB + '€, 24,99' + NB + '€ et 34,99' + NB + '€ par mois sont les prix complets, TVA incluse. Tu achètes pour une entreprise' + NB + '? Coche «' + NB + 'buying on behalf of a company' + NB + '» au moment du paiement.',
    'Does my plan renew automatically?': 'Mon plan se renouvelle-t-il automatiquement' + NB + '?',
    'Yes, every month, until you cancel. Cancel any time in your Whop account.': 'Oui, chaque mois, jusqu’à ta résiliation. Résilie à tout moment dans ton compte Whop.',
    'What happens when I cancel?': 'Que se passe-t-il quand je résilie' + NB + '?',
    'Your plan keeps running to the end of the month you paid for, then your account goes back to Free.': 'Ton plan continue jusqu’à la fin du mois payé, puis ton compte repasse en Free.',
    'Can I get a refund?': 'Puis-je être remboursé' + NB + '?',
    'Yes. Email': 'Oui. Écris à',
    'within 14 days of your first payment for a plan and we refund that payment in full.': 'dans les 14 jours suivant ton premier paiement pour un plan et on rembourse ce paiement intégralement.',
    'Can I change plan later?': 'Puis-je changer de plan plus tard' + NB + '?',
    'Upgrade here any time. To move between paid plans, manage your subscription in Whop, or email': 'Passe à un plan supérieur ici à tout moment. Pour changer entre plans payants, gère ton abonnement dans Whop, ou écris à',
    'and we will help you switch.': 'et on t’aidera à changer.',
    'What is a founding member?': 'C’est quoi un membre fondateur' + NB + '?',
    'The first 100 SNYPD accounts, free accounts included. If the Pro price ever goes up, founding members can keep Pro at €24.99 a month for as long as their account exists.':
        'Les 100 premiers comptes SNYPD, comptes gratuits compris. Si le prix de Pro augmente un jour, les membres fondateurs peuvent garder Pro à 24,99' + NB + '€ par mois aussi longtemps que leur compte existe.',
    'Paid plans renew every month until you cancel. Cancel any time. Full refund within 14 days of your first payment.':
        'Les plans payants se renouvellent chaque mois jusqu’à ta résiliation. Résiliable à tout moment. Remboursement intégral dans les 14 jours suivant ton premier paiement.',
    'Renews every month until you cancel. Cancel any time in your Whop account. Full refund within 14 days of your first payment: email help@snypd.store.':
        'Se renouvelle chaque mois jusqu’à ta résiliation. Résilie à tout moment dans ton compte Whop. Remboursement intégral dans les 14 jours suivant ton premier paiement' + NB + ': écris à help@snypd.store.',
    'Loading secure checkout...': 'Chargement du paiement sécurisé…',
    'Payment not completed. You were not charged. You can try again below.':
        'Paiement non abouti. Tu n’as pas été débité. Tu peux réessayer ci-dessous.',
    'Something else?': 'Autre chose' + NB + '?',
    ', the': ', le',
    'or the': 'ou la',
    'full FAQ': 'FAQ complète',
    # nav / footer
    'MENU': 'MENU', 'Menu': 'Menu', 'Main': 'Principal', 'Footer': 'Pied de page',
    'SNYPD · NOT AFFILIATED WITH VINTED': 'SNYPD · NON AFFILIÉ À VINTED',
    'Reads public listings only.': 'Lit uniquement les annonces publiques.',
    'Discord': 'Discord',
    'Privacy': 'Confidentialité',
    'Contact': 'Contact',
    'Cookies': 'Cookies',
})

# ====================================================================== account page (/account)
FR.update({
    'account': 'compte',
    'Account': 'Compte',
    'Back to Dashboard': 'Retour au tableau de bord',
    'Dashboard': 'Tableau de bord',
    'Filters': 'Filtres',
    'filters': 'filtres',
    'Overview': 'Aperçu',
    'Billing': 'Facturation',
    'Billing status': 'Statut de facturation',
    'Active': 'Actif',
    'active': 'actif',
    'Help': 'Aide',
    'How it works': 'Comment ça marche',
    'Pricing': 'Tarifs',
    'Sync': 'Synchroniser',
    'Manage': 'Gérer',
    'Manage billing': 'Gérer la facturation',
    'Manage subscription': 'Gérer l’abonnement',
    'Start now': 'Commencer',
    'Loading…': 'Chargement…',
    'Last updated —': 'Dernière mise à jour —',
    'Membership managed by Whop.': 'Abonnement géré par Whop.',
    'Need to change your plan or payment method?': 'Besoin de changer de plan ou de moyen de paiement' + NB + '?',
    'Plan limit': 'Limite du plan',
    'Pro pricing locked for life': 'Prix Pro garanti à vie',
    'Questions? Email': 'Des questions' + NB + '? Écris à',
    'Renews on': 'Renouvellement le',
    'Your current plan supports up to:': 'Ton plan actuel permet jusqu’à' + NB + ':',
    'Be first. Stay ahead.': 'Sois le premier. Garde une longueur d’avance.',
    'PLAN': 'PLAN',
    'Couldn’t load account.': 'Impossible de charger le compte.',
    'Couldn’t load': 'Impossible de charger',
    'Couldn’t load billing information.': 'Impossible de charger les informations de facturation.',
    'No active membership. Upgrade to unlock SNYPD tracking.': 'Aucun abonnement actif. Passe à un plan payant pour débloquer la surveillance SNYPD.',
    '© 2026 SNYPD. Not affiliated with Vinted.': '© 2026 SNYPD. Non affilié à Vinted.',
})

FR_PATTERNS += [
    (r'^PLAN [-—] (FREE|SOLO|KICKSTART|PRO|ELITE)$', 'PLAN — $1'),
    (r'^(€[\d.]+) / mo$', '$1 / mois'),
    (r'^(.+) · (€[\d.]+) / MO INCL\. VAT$', '$1 · $2 / MOIS TTC'),
    (r'^· (€[\d.]+) / mo incl\. VAT$', '· $1 / mois TTC'),
    (r'^· €0, no card$', '· 0' + NB + '€, sans carte'),
]

FR_PATTERNS += [
    # history / profile / ranks
    (r'^(\d+) items held 45 days or more — still yours\?$', '$1 articles en stock depuis 45 jours ou plus — tu les as encore' + NB + '?'),
    (r'^⚠ Held (\d+)d — still yours\?$', '⚠ En stock depuis $1 j — tu l’as encore' + NB + '?'),
    (r'^Held (\d+)d$', 'En stock depuis $1 j'),
    (r'· bought (.+) → sold (.+)$', '· acheté $1 → vendu $2'),
    (r'· HELD (\d+)D$', '· EN STOCK $1 J'),
    (r'^\+(\d+) XP quality bonus$', '+$1 XP bonus qualité'),
    (r'^DAY (\d+)$', 'JOUR $1'),
    (r'^For the (\d+) selected$', 'Pour les $1 sélectionnés'),
    (r'^Founding member #(\d+)$', 'Membre fondateur #$1'),
    (r'^Realised profit: (.+)$', 'Bénéfice réalisé' + NB + ': $1'),
    (r'^Rank up — (.+)$', 'Nouveau rang — $1'),
    (r'^Show more \((\d+) older\)$', 'Voir plus ($1 plus anciennes)'),
    (r'^(\d+) new$', '$1 nouvelles'),
    # Market Insights
    (r'^(\d+) of (\d+) price checks left this hour$', 'encore $1 vérifications de prix sur $2 cette heure-ci'),
    (r'^(\d+) of (\d+) price check left this hour$', 'encore $1 vérification de prix sur $2 cette heure-ci'),
    (r'^(\d+) price checks left this hour$', 'encore $1 vérifications de prix cette heure-ci'),
    (r'^(\d+) price check left this hour$', 'encore $1 vérification de prix cette heure-ci'),
    (r'^Found (\d[\d,]*) listings, but$', 'On a trouvé $1 annonces, mais'),
    (r'^Most sit between (.+) and (.+)$', 'La plupart entre $1 et $2'),
    (r'^· (\d[\d,]*) listings$', '· $1 annonces'),
    (r'· only (\d[\d,]*) listings(\)?)$', '· seulement $1 annonces$2'),
    (r'^1 listing, not enough on its own$', '1 annonce, pas assez à elle seule'),
    (r'^(\d[\d,]*) listings, not enough on its own$', '$1 annonces, pas assez à elles seules'),
    (r'^under (.+) · ([Pp])riced to move fast$', 'moins de $1 · se vend vite'),
    (r'^to (.+) · [Cc]ompetitive$', 'jusqu’à $1 · compétitif'),
    (r'^to (.+) · Expect to wait$', 'jusqu’à $1 · attends-toi à patienter'),
    (r'^to (.+) · patient sellers$', 'jusqu’à $1 · vendeurs patients'),
    (r'^over (.+) · [Ll]ikely to sit unsold$', 'plus de $1 · risque de rester invendu'),
    (r'^(\d+)% of listings have already dropped their price since we started watching\.$',
     '$1' + NB + '% des annonces ont déjà baissé leur prix depuis qu’on les surveille.'),
    (r'^(\d+)% of these sellers have already cut their price since we started watching, by a median of (\d+)%\. Expect to negotiate, and price with that room built in\.$',
     '$1' + NB + '% de ces vendeurs ont déjà baissé leur prix depuis qu’on les surveille, de $2' + NB + '% en médiane. Attends-toi à négocier et prévois cette marge dans ton prix.'),
    (r'^(\d+)% have cut their price since we started watching, by a median of (\d+)%\.$',
     '$1' + NB + '% ont baissé leur prix depuis qu’on les surveille, de $2' + NB + '% en médiane.'),
    (r'^(\d+)% have cut their price since we started watching\.$', '$1' + NB + '% ont baissé leur prix depuis qu’on les surveille.'),
]

# Recoverable first-hunt and device-alert setup (October 2026).
FR.update({'Finish setting up alerts on this device': 'Termine la configuration des alertes sur cet appareil', 'Your hunt is saved. Set up notifications so you can hear about matching listings without watching the feed.': 'Ta recherche est enregistrée. Configure les notifications pour être prévenu des annonces correspondantes sans surveiller le flux.', 'Set up alerts': 'Configurer les alertes', 'Alerts are set up on this device. Background monitoring depends on your plan or trial.': 'Les alertes sont configurées sur cet appareil. La surveillance en arrière-plan dépend de ton plan ou de ton essai.', 'Your alert registration could not be confirmed. Try again.': 'La configuration de tes alertes n’a pas pu être confirmée. Réessaie.', 'Still setting up alerts. Wait a moment, then try again.': 'Configuration des alertes en cours. Patiente un instant, puis réessaie.', 'Alerts are ready to set up. Tap Try again to allow notifications.': 'Les alertes sont prêtes à être configurées. Appuie sur Réessayer pour autoriser les notifications.', 'Could not save this hunt. Check your connection and try again.': 'Impossible d’enregistrer cette recherche. Vérifie ta connexion et réessaie.', 'Try again': 'Réessayer'})

FR.update({'Your Free trial runs 24/7. Enable alerts on this device to receive matching listings. After the trial, Free checks while your dashboard is open.': 'Ton essai Free fonctionne 24h/24. Active les alertes sur cet appareil pour recevoir les annonces correspondantes. Après l’essai, Free vérifie les annonces tant que ton tableau de bord est ouvert.', 'Your seven-day background-monitoring trial starts when you save your first hunt. Alerts must be enabled on this device.': 'Ton essai de sept jours de surveillance en arrière-plan commence quand tu enregistres ta première recherche. Les alertes doivent être activées sur cet appareil.', 'Your 3-day background-monitoring trial starts when you save your first hunt. Alerts must be enabled on this device.': 'Ton essai de 3 jours de surveillance en arrière-plan commence quand tu enregistres ta première recherche. Les alertes doivent être activées sur cet appareil.', 'Could not check your trial status. Your hunt is saved; try again shortly.': 'Impossible de vérifier le statut de ton essai. Ta recherche est enregistrée ; réessaie dans un instant.'})
# Recoverable signup confirmation (15 October 2026).
FR.update({
    'Confirm your email': 'Confirme ton e-mail',
    'Enter your account email and the code from your latest SNYPD confirmation email. If an older email only has a link, request a new email below.': 'Saisis l’e-mail de ton compte et le code du dernier e-mail de confirmation SNYPD. Si un ancien e-mail contient seulement un lien, demande un nouvel e-mail ci-dessous.',
    'CONFIRMATION CODE': 'CODE DE CONFIRMATION',
    'CONFIRM EMAIL': 'CONFIRMER MON E-MAIL',
    'CONFIRMING…': 'CONFIRMATION…',
    'Enter the code from your latest confirmation email.': 'Saisis le code de ton dernier e-mail de confirmation.',
    'That confirmation could not be completed. Use the code from your latest email, or request a new email below. Already confirmed? Go back to log in.': 'La confirmation n’a pas abouti. Utilise le code du dernier e-mail ou demande un nouvel e-mail ci-dessous. Déjà confirmé ? Retourne à la connexion.',
    'Confirm your email to finish signing up. Enter your latest code below, or request a new email.': 'Confirme ton e-mail pour terminer ton inscription. Saisis ton dernier code ci-dessous ou demande un nouvel e-mail.',
    'Confirmation email requested. Use only the latest email; earlier codes may no longer work.': 'E-mail de confirmation demandé. Utilise uniquement le dernier e-mail ; les anciens codes peuvent ne plus fonctionner.',
})

# Solo plan + trial-ended offer (18 Oct 2026). Offer text approved by Tanush 17 Oct
# (outreach/21-conversion-plan.md); amounts checked in Whop's checkout 18 Oct.
FR.update({
    'Your one search, watched around the clock.': 'Ta recherche, surveillée 24h/24.',
    'Everything in Solo, plus:': 'Tout Solo, plus' + NB + ':',
    'START SOLO': 'CHOISIR SOLO',
    'SOLO checkout': 'Paiement SOLO',
    'MANAGE SUBSCRIPTION': 'GÉRER L’ABONNEMENT',
    'CHANGE PLAN IN WHOP': 'CHANGER DE PLAN DANS WHOP',
    'CANCEL IN WHOP': 'RÉSILIER DANS WHOP',
    'Your trial ended: 50% off your first month': 'Ton essai est terminé' + NB + ': -50' + NB + '% sur ton premier mois',
})
FR_PATTERNS += [
    (r'^UPGRADE TO (SOLO|KICKSTART|PRO|ELITE)$', 'PASSER À $1'),
    (r'^Until (.+): Kickstart €7\.49 or Pro €12\.49 for the first month, code SNYPD50 already applied\. Or Solo, €5\.99/month for 1 search 24/7\.$',
     'Jusqu’au $1' + NB + ': Kickstart 7,49' + NB + '€ ou Pro 12,49' + NB + '€ le premier mois, code SNYPD50 déjà appliqué. Ou Solo, 5,99' + NB + '€/mois pour 1 recherche 24h/24.'),
]

# ====================================================================== marketing-email consent (19 Oct 2026)
FR.update({
    'Get SNYPD news by email?': 'Recevoir les nouvelles de SNYPD par e-mail' + NB + '?',
    'Product updates, Vinted tips and occasional offers. Unsubscribe in one click, or change it any time on your Account page.':
        'Nouveautés du produit, astuces Vinted et offres ponctuelles. Désabonne-toi en un clic, ou change d’avis quand tu veux sur ta page Compte.',
    'Yes, email me': 'Oui, écris-moi',
    'No thanks': 'Non merci',
    "Couldn't save your choice. Try again.": 'Impossible d’enregistrer ton choix. Réessaie.',
    'Email updates': 'Nouvelles par e-mail',
    'Product updates, Vinted tips and occasional offers': 'Nouveautés du produit, astuces Vinted et offres ponctuelles',
    "Couldn't save your email preference. Try again.": 'Impossible d’enregistrer ta préférence e-mail. Réessaie.',
    'Email updates on.': 'Nouvelles par e-mail activées.',
    'Email updates off. It can take up to an hour to apply.': 'Nouvelles par e-mail désactivées. La prise en compte peut prendre jusqu’à une heure.',
})

# ====================================================================== conversion Phase 0 (19 Oct 2026, migration 061)
# Dashboard: trial in hours under 2 days, what the hunt caught (my_trial_stats), paused state, plan after the first
# hunt, activation after checkout, "LIVE WHILE OPEN" for a Free hunt after the trial.
FR.update({
    'Your hunt is paused in the background': 'Ta recherche est en pause en arrière-plan',
    'Free only checks while this tab is open. Solo keeps one search running 24/7 for €5.99/month.':
        'Free ne vérifie que lorsque cet onglet est ouvert. Solo garde une recherche active 24h/24 pour 5,99' + NB + '€/mois.',
    'We added 2 days because your hunt found nothing in 3 days. Widen it: fewer filters or a higher max price.':
        'Nous avons ajouté 2 jours, car ta recherche n’a rien trouvé en 3 jours. Élargis-la' + NB + ': moins de filtres ou un prix max plus haut.',
    'Your hunt has not matched a new listing yet. A wider search (fewer filters, a higher max price) finds more.':
        'Ta recherche n’a encore trouvé aucune nouvelle annonce. Une recherche plus large (moins de filtres, un prix max plus haut) en trouve plus.',
    'Your hunt has not matched a new listing yet. If it finds nothing in 3 days, we add 2 more days, once.':
        'Ta recherche n’a encore trouvé aucune nouvelle annonce. Si elle ne trouve rien en 3 jours, nous ajoutons 2 jours, une fois.',
    'Your hunt is live. Keep it running after the trial': 'Ta recherche est lancée. Garde-la active après l’essai',
    'Activating your plan...': 'Activation de ton plan…',
    'Payment received. Your plan usually switches on within a minute; this page checks every 5 seconds.':
        'Paiement reçu. Ton plan s’active en général en moins d’une minute' + NB + '; cette page vérifie toutes les 5 secondes.',
    'Still waiting for Whop. Check that you paid with your SNYPD account email. If your plan is not on within 15 minutes, use the Support page and we will link it by hand.':
        'Toujours en attente de Whop. Vérifie que tu as payé avec l’e-mail de ton compte SNYPD. Si ton plan n’est pas actif dans 15 minutes, passe par la page Support et nous le relierons à la main.',
    'LIVE WHILE OPEN': 'ACTIVE ONGLET OUVERT',
    '24/7 for 3 days, then while your dashboard is open': '24h/24 pendant 3 jours, puis tant que ton tableau de bord est ouvert',
})
FR_PATTERNS += [
    (r'^Free 24/7 trial: (\d+) h left$', 'Essai Free 24h/24' + NB + ': encore $1' + NB + 'h'),
    (r'^Your hunt has matched 1 new listing since (.+)\.$', 'Ta recherche a trouvé 1 nouvelle annonce depuis le $1.'),
    (r'^Your hunt has matched (.+) new listings since (.+)\.$', 'Ta recherche a trouvé $1 nouvelles annonces depuis le $2.'),
    (r'^(.+) new listings matched your hunt since your trial ended, while it was paused\. Cheapest: (.+)\.$',
     '$1 nouvelles annonces correspondaient à ta recherche depuis la fin de l’essai, pendant sa pause. La moins chère' + NB + ': $2.'),
    (r'^(.+) new listings matched your hunt since your trial ended, while it was paused\.$',
     '$1 nouvelles annonces correspondaient à ta recherche depuis la fin de l’essai, pendant sa pause.'),
    (r'^During your trial, your hunt matched (.+) new listings\.$', 'Pendant ton essai, ta recherche a trouvé $1 nouvelles annonces.'),
    (r'^You picked (Solo|Kickstart|Pro|Elite) at sign-up\. Start it now and your hunt keeps running 24/7 when the trial ends\.$',
     'Tu as choisi $1 à l’inscription. Démarre-le maintenant et ta recherche reste active 24h/24 à la fin de l’essai.'),
    (r'^Start (Solo|Kickstart|Pro|Elite)$', 'Démarrer $1'),
]

# ===== Phase 1 site (Hunt Pass, Solo offer)
# /plans (20 Oct 2026): the Hunt Pass (FR name "Pass 30 jours", owner-approved), EUR 3.99 once, 1 search 24/7 for
# 30 days, no renewal; the trial-ended code now also covers Solo. Texts with a price are PATTERNS (the price comes
# from plans.json and money() turns "€3.99" into "3,99 €"); texts with 30 / 14 days are exact keys (re-check after a
# change to plans.json passes[].days or refund.days).
FR.update({
    'Code applied at checkout for Solo, Kickstart and Pro:': 'Code appliqué au paiement pour Solo, Kickstart et Pro' + NB + ':',
    'HUNT PASS': 'PASS 30 JOURS',
    'PASS': 'PASS',
    'NO SUBSCRIPTION': 'SANS ABONNEMENT',
    'once': 'en une fois',
    'VAT incl. · one-time payment · nothing to cancel': 'TVA incl. · paiement unique · rien à résilier',
    'One item to find? Pay once and hunt it for 30 days.': 'Un seul article à trouver' + NB + '? Paie une fois et cherche-le pendant 30 jours.',
    'Same as Solo, for 30 days:': 'Comme Solo, pendant 30 jours' + NB + ':',
    'Ends after 30 days: no renewal, nothing to cancel': 'S’arrête après 30 jours' + NB + ': pas de renouvellement, rien à résilier',
    'GET HUNT PASS': 'PRENDRE LE PASS 30 JOURS',
    'INCLUDED IN YOUR PLAN': 'INCLUS DANS TON PLAN',
    'HUNT PASS checkout': 'Paiement PASS 30 JOURS',
    'Paid plans renew every month until you cancel. Cancel any time. Full refund within 14 days of your first payment. The Hunt Pass is paid once and does not renew.':
        'Les plans payants se renouvellent chaque mois jusqu’à ta résiliation. Résiliable à tout moment. Remboursement intégral dans les 14 jours suivant ton premier paiement. Le Pass 30 jours se paie une seule fois et ne se renouvelle pas.',
    'Everything in the Solo column for 30 days, paid once, VAT included. No renewal, nothing to cancel. Full refund within 14 days of the payment.':
        'Tout ce que contient la colonne Solo, pendant 30 jours, payé une seule fois, TVA incluse. Pas de renouvellement, rien à résilier. Remboursement intégral dans les 14 jours suivant le paiement.',
    'Yes, every month, until you cancel. Cancel any time in your Whop account. The Hunt Pass is the exception: it is paid once and ends after 30 days.':
        'Oui, chaque mois, jusqu’à ta résiliation. Résilie à tout moment dans ton compte Whop. Seule exception' + NB + ': le Pass 30 jours se paie une seule fois et s’arrête après 30 jours.',
    'Can I pay once, without a subscription?': 'Puis-je payer une seule fois, sans abonnement' + NB + '?',
    'One payment. 1 search watched 24/7 for 30 days, then it ends: no renewal, nothing to cancel. Full refund within 14 days of the payment: email help@snypd.store.':
        'Un seul paiement. 1 recherche surveillée 24h/24 pendant 30 jours, puis elle s’arrête' + NB + ': pas de renouvellement, rien à résilier. Remboursement intégral dans les 14 jours suivant le paiement' + NB + ': écris à help@snypd.store.',
})
FR_PATTERNS += [
    (r'^One item, no subscription\? Hunt Pass: (€[\d.]+) once, (\d+) days →$',
     'Un seul article, sans abonnement' + NB + '? Pass 30 jours' + NB + ': $1 en une fois, $2 jours →'),
    (r'^HUNT PASS · (€[\d.]+) ONCE$', 'PASS 30 JOURS · $1 EN UNE FOIS'),
    (r'^HUNT PASS · (€[\d.]+) ONCE INCL\. VAT$', 'PASS 30 JOURS · $1 EN UNE FOIS TTC'),
    (r'^Yes: the Hunt Pass\. One payment of (€[\d.]+), VAT included, and 1 Vinted search is watched 24/7 with push alerts for (\d+) days, like Solo\. Then it simply ends: no renewal, no subscription, nothing to cancel\. It suits hunting one specific item, like a console or a jacket in your size\. Full refund within (\d+) days of the payment\. For ongoing hunting, Solo is (€[\d.]+) a month\.$',
     'Oui' + NB + ': le Pass 30 jours. Un seul paiement de $1, TVA incluse, et 1 recherche Vinted est surveillée 24h/24 avec alertes push pendant $2 jours, comme avec Solo. '
     'Ensuite, il s’arrête tout simplement' + NB + ': pas de renouvellement, pas d’abonnement, rien à résilier. Idéal pour chercher un article précis, comme une console ou une veste à ta taille. '
     'Remboursement intégral dans les $3 jours suivant le paiement. Pour chercher en continu, Solo coûte $4 par mois.'),
]

# ===== Phase 1 dashboard (Hunt Pass holder, STAY50 offer incl. Solo, broad-hunt notice), 20 Oct 2026
FR.update({
    'Free only checks while this tab is open. Solo keeps one search running 24/7 for €5.99/month, or €3.99 once for a 30-day Hunt Pass.':
        'Free ne vérifie que lorsque cet onglet est ouvert. Solo garde une recherche active 24h/24 pour 5,99' + NB + '€/mois, ou le Pass 30 jours pour 3,99' + NB + '€ en une fois.',
    'After that your hunt only runs while this tab is open. Keep it 24/7: another 30-day pass for €3.99, or Solo at €5.99/month.':
        'Ensuite, ta recherche ne tourne que lorsque cet onglet est ouvert. Garde-la 24h/24' + NB + ': un nouveau Pass 30 jours pour 3,99' + NB + '€, ou Solo à 5,99' + NB + '€/mois.',
    'Renew': 'Renouveler',
    'This hunt is very broad': 'Cette recherche est très large',
    'Edit hunt': 'Modifier la recherche',
    'Keep it': 'La garder',
    'Plan: HUNT PASS': 'Plan' + NB + ': PASS 30 JOURS',
    'Start Hunt Pass': 'Prendre le Pass 30 jours',
})
FR_PATTERNS += [
    (r'^Until (.+): Solo €2\.99, Kickstart €7\.49 or Pro €12\.49 for the first month, code ([A-Z0-9]+) already applied\. Or a 30-day Hunt Pass, €3\.99 once\.$',
     'Jusqu’au $1' + NB + ': Solo 2,99' + NB + '€, Kickstart 7,49' + NB + '€ ou Pro 12,49' + NB + '€ le premier mois, code $2 déjà appliqué. Ou le Pass 30 jours, 3,99' + NB + '€ en une fois.'),
    (r'^Your Hunt Pass ends on (.+)$', 'Ton Pass 30 jours se termine le $1'),
    (r'^About (\d+) new listings an hour match "(.+)": more than anyone can open, so alerts become noise\. On Vinted, add a size or a max price, copy the link and paste it into this hunt\.$',
     'Environ $1 nouvelles annonces par heure correspondent à «' + NB + '$2' + NB + '»' + NB + ': plus que personne ne peut en ouvrir, et les alertes deviennent du bruit. Sur Vinted, ajoute une taille ou un prix max, copie le lien et colle-le dans cette recherche.'),
    (r'^You picked Hunt Pass at sign-up\. Start it now and your hunt keeps running 24/7 when the trial ends\.$',
     'Tu as choisi le Pass 30 jours à l’inscription. Prends-le maintenant et ta recherche reste active 24h/24 à la fin de l’essai.'),
]

# ===== Calm mode (migration 064, 23 Oct 2026): per-hunt alert style in the first-hunt wizard (new step 2 of 3)
# and in the Filters sheet. "Every match" = today's behaviour; "Calm" = first find at once, then at most one
# summary per 15 or 30 min (backend push.py; the push text itself is translated in sw.js).
FR.update({
    'Step 1 of 3': 'Étape 1 sur 3',
    'Step 2 / 3': 'Étape 2 / 3',
    'Step 3 / 3': 'Étape 3 / 3',
    'How should we alert you?': 'Comment veux-tu être prévenu' + NB + '?',
    'We still check this hunt every 30 s to 5 min. This only sets how often your phone buzzes. Change it anytime in Filters.':
        'On vérifie toujours ta recherche toutes les 30 s à 5 min. Ce choix règle seulement la fréquence des notifications. Tu peux le changer à tout moment dans Filtres.',
    'Alert style': 'Type d’alerte',
    'Every match': 'Chaque annonce',
    'Be first on every new listing. Best for resellers.': 'Sois le premier sur chaque nouvelle annonce. Idéal pour les revendeurs.',
    'Calm': 'Calme',
    'The first find right away, then at most one summary every 15 or 30 min.':
        'La première trouvaille tout de suite, puis au plus un résumé toutes les 15 ou 30 min.',
    'Summary every': 'Résumé toutes les',
    'Continue': 'Continuer',
    'Could not save this choice. Try again; your hunt is already running.':
        'Impossible d’enregistrer ce choix. Réessaie' + NB + '; ta recherche tourne déjà.',
    'ALERTS': 'ALERTES',
    'Alerts for this hunt': 'Alertes pour cette recherche',
})
FR_PATTERNS += [
    (r'^Calm - (\d+) min$', 'Calme - $1 min'),
    (r'^Calm: the first find right away, then at most one summary every (\d+) min\.$',
     'Calme' + NB + ': la première trouvaille tout de suite, puis au plus un résumé toutes les $1 min.'),
]

# ===== Broad-hunt notice: Switch to Calm (23 Oct 2026). Sets that hunt to Calm / 15 min (migration 064).
FR.update({
    'Switch to Calm': 'Passer en Calme',
    'Could not switch this hunt. Try again, or change it in Filters.':
        'Impossible de changer cette recherche. Réessaie, ou change-la dans Filtres.',
})
FR_PATTERNS += [
    (r'^Done: "(.+)" now sends at most one summary every 15 min\. Change it anytime in Filters\.$',
     'C’est fait' + NB + ': «' + NB + '$1' + NB + '» envoie désormais au plus un résumé toutes les 15 min. Tu peux le changer à tout moment dans Filtres.'),
]

# ===== /plans chooser by goal (23 Oct 2026): nothing preselected; one item -> Hunt Pass, one search ongoing -> Solo,
# reselling -> Kickstart and up (count of searches + optional price checks).
FR.update({
    'WHAT ARE YOU HUNTING FOR?': 'QUE CHERCHES-TU' + NB + '?',
    'ONE ITEM, THEN DONE': 'UN ARTICLE, PUIS C’EST FINI',
    'A console, a jacket in your size: find it and stop.': 'Une console, une veste à ta taille' + NB + ': tu la trouves, tu arrêtes.',
    'ONE SEARCH, ONGOING': 'UNE RECHERCHE, EN CONTINU',
    'Keep watching the same search, month after month.': 'Surveiller la même recherche, mois après mois.',
    'STOCK TO RESELL': 'DU STOCK À REVENDRE',
    'Several searches to source items you sell on.': 'Plusieurs recherches pour trouver des articles à revendre.',
    "Pick what you're hunting for and we'll show the plan that fits.": 'Choisis ce que tu cherches et on t’indique le plan qui convient.',
    '1 active search': '1 recherche active',
    'Renews monthly, cancel any time': 'Renouvelé chaque mois, résiliable à tout moment',
    'NO': 'NON',
})
FR_PATTERNS += [
    (r'^(\d+) active searches$', '$1 recherches actives'),
    (r'^(€[\d.]+) once$', '$1 en une fois'),
    (r'^· (€[\d.]+) once incl\. VAT$', '· $1 en une fois TTC'),
    (r'^Still hunting after (\d+) days\? Solo: (€[\d.]+) / mo →$', 'Encore en chasse après $1 jours' + NB + '? Solo' + NB + ': $2 / mois →'),
]


# First-hunt price controls, 23 October 2026.
FR.update({
    'Minimum price (optional)': 'Prix minimum (facultatif)',
    "Lower or clear the minimum to include cheaper items. Like Vinted's search, matches can include words in the description.": 'Baisse ou efface le minimum pour inclure les articles moins chers. Comme sur Vinted, les résultats peuvent contenir les mots dans la description.',
    'Use a minimum of zero or more and a maximum above zero, or leave them blank.': 'Indique un minimum de zéro ou plus et un maximum supérieur à zéro, ou laisse les champs vides.',
    'Minimum price must be below maximum price. Lower or clear the minimum.': 'Le prix minimum doit être inférieur au maximum. Baisse ou efface le minimum.',
})
FR_PATTERNS += [(r'^Min ([A-Z]{3})$', 'Min $1')]

# Checkout recovery: keep these keys aligned with plans.html.
FR.update({
    "RELOAD TO CHECK PLAN": "RECHARGER POUR VÉRIFIER LE PLAN",
    "CHECKING YOUR PLAN": "VÉRIFICATION DE TON PLAN",
    "PLAN UNAVAILABLE": "PLAN INDISPONIBLE",
    "Checkout could not load here. Continue on Whop using your SNYPD account email:": "Le paiement n’a pas pu charger ici. Continue sur Whop avec l’e-mail de ton compte SNYPD :",
    "Enter promo code": "Saisis le code promo",
    "and check the total before paying.": "et vérifie le total avant de payer.",
    "CONTINUE TO WHOP": "CONTINUER SUR WHOP"
})

# ---------------------------------------------------------------- price check on Feed cards (Session 66, 4 Nov 2026)
FR.update({
    'Sort': 'Trier',
    'Newest': 'Plus récentes',
    'Best price first': 'Meilleur prix d’abord',
    'Cheapest 25% only': 'Les 25' + NB + '% les moins chères',
    'Price checks on every find: Solo and up': 'Le prix comparé sur chaque trouvaille' + NB + ': dès Solo',
    'No find in the cheapest 25% right now.': 'Aucune trouvaille dans les 25' + NB + '% les moins chères pour l’instant.',
    'Price check · Solo and up': 'Prix comparé · dès Solo',
})
FR_PATTERNS += [
    (r"^Cheaper than (\d+)% of this hunt's finds this week$", 'Moins cher que $1' + NB + '% des trouvailles de cette recherche cette semaine'),
    (r"^Pricier than (\d+)% of this hunt's finds this week$", 'Plus cher que $1' + NB + '% des trouvailles de cette recherche cette semaine'),
    (r"^(\d+) new listings$", '$1 nouvelles annonces'),
    (r"^(\d+) listings$", '$1 annonces'),
    (r"^(\d+) new listings found by your hunts\.$", '$1 nouvelles annonces trouvées par tes recherches.'),
    (r"^([+-]?\d+)%$", '$1' + NB + '%'),
    (r"^Only (\d+)% of this hunt's finds this week cost more$", 'Seulement $1' + NB + '% des trouvailles de cette recherche cette semaine coûtent plus cher'),
    (r"^Not found in any listing of the last 14 days, so left out of this price: (.+)$",
     'Absent de toutes les annonces des 14 derniers jours, donc pas pris en compte dans ce prix' + NB + ': $1'),
    (r'^same condition · (\d+) finds compared$', 'même état · $1 annonces comparées'),
]

# ---------------------------------------------------------------- Market price fix (Session 66, 4 Nov 2026)
FR.update({
    'Compared on:': 'Comparé sur' + NB + ':',
    'Ignored (tap to add back):': 'Ignoré (touche pour remettre)' + NB + ':',
    'Too few listings with every word. Try without:': 'Trop peu d’annonces avec tous ces mots. Essaie sans' + NB + ':',
    'size': 'taille', 'colour': 'couleur', 'year': 'année', 'condition': 'état', 'filler': 'mot vide',
    'not in our listings': 'absent de nos annonces', 'left out to find more': 'retiré pour trouver plus',
    # Weekly hunt report (Session 66 P6)
    'Your hunts this week': 'Tes recherches cette semaine',
    'vs last week': 'vs semaine dernière',
    'Cheapest find': 'Trouvaille la moins chère',
    'Open on Vinted': 'Ouvrir sur Vinted',
    'typical': 'typique',
    'Too mixed for one price': 'Trop mélangé pour un seul prix',
    'Too few to price yet': 'Encore trop peu pour un prix',
    'Other condition': 'Autre état',
    'No new listings this week yet.': 'Pas encore de nouvelle annonce cette semaine.',
    'No active hunts. Start a hunt to get this report.': 'Aucune recherche active. Lance une recherche pour avoir ce rapport.',
    'Could not load your weekly report right now.': 'Impossible de charger ton rapport de la semaine pour le moment.',
    '1 new listing': '1 nouvelle annonce',
    '1 listing': '1 annonce',
    '1 new listing found by your hunts.': '1 nouvelle annonce trouvée par tes recherches.',
    'The full report (typical price per condition, the cheapest find with its link, change vs last week) is part of Pro and Elite.':
        'Le rapport complet (prix typique par état, la trouvaille la moins chère avec son lien, évolution vs semaine dernière) fait partie de Pro et Elite.',
    'Asking prices of the new listings your hunts found in the last 7 days (UTC days), not sold prices. The cheapest find comes from the prices we keep: up to 400 a day per condition.':
        'Prix demandés des nouvelles annonces trouvées par tes recherches ces 7 derniers jours (jours UTC), pas les prix réellement payés. La trouvaille la moins chère vient des prix que nous gardons' + NB + ': jusqu’à 400 par jour et par état.',
    'On the Free plan every match comes through.': 'Avec le plan Free, toutes les annonces arrivent.',
    'Only the cheap ones': 'Seulement les moins chères',
    'Only the cheap ones (paid plans)': 'Seulement les moins chères (plans payants)',
    "Only the cheap ones: a push only for a find cheaper than 75% of this hunt's finds this week. Finds without a price check yet still come through. The Feed shows everything.":
        'Seulement les moins chères' + NB + ': une notification seulement pour une trouvaille moins chère que 75' + NB + '% des trouvailles de cette recherche cette semaine. Les trouvailles sans vérification de prix arrivent quand même. Le Feed montre tout.',
    "The priciest of this hunt's finds this week": 'La plus chère des trouvailles de cette recherche cette semaine',
    'Few listings: a rough guide.': 'Peu d’annonces' + NB + ': une estimation approximative.',
    'Quick sale': 'Vente rapide', 'Typical': 'Typique', 'Patient': 'Patient',
    'Asking prices, not sold prices.': 'Prix demandés, pas les prix réellement payés.',
    'Pay at most': 'Paie au maximum', 'Margin': 'Marge',
    '% at the typical asking price': NB + '% sur le prix demandé typique',
    '(this item)': '(cet article)',
    'Price check': 'Vérifier le prix',
    'Price checks are part of Pro and Elite.': 'La vérification des prix fait partie de Pro et Elite.',
})
FR_PATTERNS += [
    (r'^For this condition \((.+)\)\. Asking prices, not sold prices\.$', 'Pour cet état ($1). Prix demandés, pas les prix réellement payés.'),
    (r'^Asking prices on (\S+) \(EU listings\), in ([A-Z]{3}), last (\d+) days\.$',
     'Prix demandés sur $1 (annonces UE), en $2, $3 derniers jours.'),
    (r'^Asking prices on (\S+) \(EU listings\), in ([A-Z]{3}), last (\d+) days\. Your feed has listings from (.+): these prices are not from there\.$',
     'Prix demandés sur $1 (annonces UE), en $2, $3 derniers jours. Ton flux contient des annonces de $4' + NB + ': ces prix n’en viennent pas.'),
]
FR.update({
    "Typical asking prices from listings SNYPD saw on Vinted's EU site in the last 14 days, by condition. Type a brand and model; sizes and colours are ignored.":
        'Prix demandés typiques des annonces que SNYPD a vues sur le site UE de Vinted ces 14 derniers jours, par état. Tape une marque et un modèle' + NB + '; tailles et couleurs sont ignorées.',
})
FR_PATTERNS += [
    (r'^Typical asking price for (.+) \(all conditions: (.+)\)$', 'Prix demandé typique pour $1 (tous états' + NB + ': $2)'),
]

# ---------------------------------------------------------------- Market board (Session 67, 5 Nov 2026)
FR.update({
    "What's moving": 'Ce qui bouge',
    'EU asking prices (EUR)': 'Prix demandés UE (EUR)',
    'Asking prices rising': 'Prix demandés en hausse',
    'Asking prices falling': 'Prix demandés en baisse',
    'Nothing rising by 10% or more right now.': 'Rien en hausse de 10' + NB + '% ou plus en ce moment.',
    'Nothing falling by 10% or more right now.': 'Rien en baisse de 10' + NB + '% ou plus en ce moment.',
    'Price cuts': 'Baisses de prix',
    'Sneakers': 'Baskets', 'Jackets & coats': 'Vestes et manteaux', 'Tops & knitwear': 'Hauts et pulls',
    'Trousers': 'Pantalons', 'Bags': 'Sacs', 'Accessories': 'Accessoires',
    'See every tracked item with its 5-week trend, price cuts and what hunters watch: part of Pro and Elite.':
        'Chaque article suivi avec sa tendance sur 5 semaines, les baisses de prix et ce que surveillent les utilisateurs' + NB + ': inclus dans Pro et Elite.',
    '1 item hidden: the mix of listings changed too much to call a direction.':
        '1 article masqué' + NB + ': le mélange des annonces a trop changé pour dire dans quel sens va le prix.',
    'Hide the list': 'Masquer la liste',
    'What hunters watch': 'Ce que surveillent les utilisateurs',
    'Brands that 5 or more SNYPD users hunt right now, counted once per user.':
        'Marques que 5 utilisateurs de SNYPD ou plus recherchent en ce moment, chaque utilisateur compté une fois.',
    'Typical asking price over the last 7 days of listings on vinted.be (EU site, EUR), for the items SNYPD tracks. Rising or falling = the last 3 days against 8 to 21 days ago, by 10% or more and by at least 5% on each of the last 3 days. Asking prices, not sold prices: a description, not a forecast.':
        'Prix demandé typique sur les 7 derniers jours d’annonces de vinted.be (site UE, EUR), pour les articles que SNYPD suit. En hausse ou en baisse = les 3 derniers jours comparés à il y a 8 à 21 jours, d’au moins 10' + NB + '% et d’au moins 5' + NB + '% chacun des 3 derniers jours. Prix demandés, pas les prix réellement payés' + NB + ': une description, pas une prévision.',
    'Search words:': 'Mots de recherche' + NB + ':',
    'Line: typical asking price. Band: normal range (the middle half of asking prices). Bars: listings seen. Gaps: days too mixed to price.':
        'Ligne' + NB + ': prix demandé typique. Bande' + NB + ': fourchette normale (la moitié centrale des prix demandés). Barres' + NB + ': annonces vues. Trous' + NB + ': jours trop mélangés pour un prix.',
    'Typical now': 'Typique maintenant', 'Normal range': 'Fourchette normale', 'Listings (7 days)': 'Annonces (7 jours)',
    'Sellers': 'Vendeurs', 'Price cuts this week': 'Baisses de prix cette semaine',
    'Good time to list if you hold some. Sourcing costs more than it did.':
        'Bon moment pour mettre en vente si tu en as. Trouver du stock coûte plus cher qu’avant.',
    "Cheaper to source now, but check it's not fading: look at the listings count and the price cuts.":
        'Moins cher à trouver maintenant, mais vérifie que l’intérêt ne retombe pas' + NB + ': regarde le nombre d’annonces et les baisses de prix.',
    "The mix of listings changed a lot, so we don't call a direction.":
        'Le mélange des annonces a beaucoup changé, alors on ne donne pas de sens.',
    'Asking prices held steady: within 10% of 8 to 21 days ago.':
        'Prix demandés stables' + NB + ': à 10' + NB + '% près d’il y a 8 à 21 jours.',
    'Hunt this below': 'Chercher en dessous de',
    'Hunt this item': 'Lancer une recherche',
    'That is the quick-sale price: only a quarter of listings ask less. You check the hunt before it is saved.':
        'C’est le bas de la fourchette' + NB + ': seulement un quart des annonces demandent moins. Tu vérifies la recherche avant qu’elle soit enregistrée.',
    'Your hunts are on a non-euro Vinted site, so no maximum price is filled in: set your own.':
        'Tes recherches sont sur un site Vinted hors euro, donc aucun prix maximum n’est rempli' + NB + ': fixe le tien.',
    'Could not load what is moving right now.': 'Impossible de charger ce qui bouge pour le moment.',
    '5-week trend': 'Tendance sur 5 semaines', 'Margin in percent': 'Marge en pourcentage', 'Close': 'Fermer',
})
FR_PATTERNS += [
    (r'^(\d+) items on the board today\.$', '$1 articles sur le tableau aujourd’hui.'),
    (r'^(\d+) items hidden: the mix of listings changed too much to call a direction\.$',
     '$1 articles masqués' + NB + ': le mélange des annonces a trop changé pour dire dans quel sens va le prix.'),
    (r'^See all (\d+) items$', 'Voir les $1 articles'),
    (r'^(\d+) hunters$', '$1 utilisateurs'),
    (r'^Sellers now ask (\d+)% more than 8 to 21 days ago \((.+) to (.+)\)\.$',
     'Les vendeurs demandent maintenant $1' + NB + '% de plus qu’il y a 8 à 21 jours ($2 puis $3).'),
    (r'^Sellers now ask (\d+)% less than 8 to 21 days ago \((.+) to (.+)\)\.$',
     'Les vendeurs demandent maintenant $1' + NB + '% de moins qu’il y a 8 à 21 jours ($2 puis $3).'),
    (r'^(\d+)% of listings had a price cut this week: buyers are taking their time\.$',
     '$1' + NB + '% des annonces ont baissé leur prix cette semaine' + NB + ': les acheteurs prennent leur temps.'),
]

# ---------------------------------------------------------------- Live review fixes (Session 67, 5 Nov 2026)
FR.update({
    'Alerts on': 'Alertes activées',
    'Alerts blocked: how to fix': 'Alertes bloquées' + NB + ': comment corriger',
    'Details': 'Détails', 'Hide details': 'Masquer les détails',
    'Get a push when your hunts find something, without keeping SNYPD open.':
        'Reçois une notification quand tes recherches trouvent quelque chose, sans garder SNYPD ouvert.',
    'Not now': 'Pas maintenant',
    'Send a test notification': 'Envoyer une notification de test',
    'Alert setup guide': 'Guide de configuration des alertes',
    'No alerts 23:00 - 08:00 your time, then one summary.': 'Aucune alerte de 23:00 à 08:00 (ton heure), puis un résumé.',
    'Test sent. Check this device’s notifications.': 'Test envoyé. Vérifie les notifications de cet appareil.',
    'The test could not be shown. Check this device’s notification settings.':
        'Le test n’a pas pu s’afficher. Vérifie les réglages de notification de cet appareil.',
    '1 more listing in other conditions: too few to price yet.': '1 autre annonce dans d’autres états' + NB + ': encore trop peu pour un prix.',
    'Too few listings yet to price by condition.': 'Encore trop peu d’annonces pour un prix par état.',
    'Show fewer': 'Voir moins',
})
FR_PATTERNS += [
    (r'^No alerts 23:00 - 08:00 \((.+)\), then one summary\.$', 'Aucune alerte de 23:00 à 08:00 ($1), puis un résumé.'),
    (r'^(\d+) more listings in other conditions: too few to price yet\.$', '$1 autres annonces dans d’autres états' + NB + ': encore trop peu pour un prix.'),
    (r'^Show all (\d+) brands$', 'Voir les $1 marques'),
]
