// Design check 5 Nov 2026 (outreach/38 in the website folder), gaps 1-6: return/write-off sheets, item detail (timeline + money),
// Items values, Quick add condition buttons + Manage categories. Merged LAST by stock_strings.cjs, so a key here replaces an earlier one.
// UTF-8 with real accents, informal "tu". Wording follows the Claude Design boards (Round I Ia/Ib, Round C Cb).
const en = {
  'ret.eRevP': 'On {date}: revenue −{refund}, profit {p}.',
  'f.condition.opt': 'Condition · optional', 'cond.clear': 'Clear',
  'cat.manage': 'Manage categories', 'cat.title': 'Categories', 'cat.hide': 'Hide', 'cat.show': 'Show', 'cat.add': 'Add', 'cat.ph': 'New category', 'cat.done': 'Done', 'cat.hiddenTag': 'Hidden',
  'dt.notlisted': 'not listed', 'dt.timeline': 'Timeline',
  'dt.s.bought': 'Bought', 'dt.s.listed': 'Listed', 'dt.s.reserved': 'Reserved', 'dt.s.sold': 'Sold', 'dt.gap': '+{n}d',
  'dt.money': 'Money', 'dt.fee': 'Platform fee', 'dt.net': 'Net profit',
  'dt.note.open': 'Net profit appears when you mark it sold.',
  'dt.note.nocost': 'No buy price, so no net profit yet. Add it under Edit details.',
  'dt.note.nofee': 'No platform fee entered, so net profit is before fees.',
  'dt.edit': 'Edit details', 'dt.save': 'Save changes',
  'meta.bought': 'bought {c}',
  // live check on the real account (5 Nov 2026): fixes 1-10
  'dt.day1': '1 day', 'dt.days': '{n} days', 'wo.line': '{st} · in stock {days} · cost {cost}',
  'ret.e4': 'Net profit, last 30 days: {a} → {b}.',
  'ch.total': 'Total {amount}',
  'ov.lanes.none': 'Nothing needs you today.',
  'ov.cur.ok': 'OK',
  'cat.note': 'Rename, add or hide. Changes save right away; hidden categories keep their items.',
  'act.details': 'Details', 'age.soldin': 'sold in {n} d'
};
const fr = {
  'ret.eRevP': 'Le {date} : chiffre d’affaires −{refund}, bénéfice {p}.',
  'f.condition.opt': 'État · facultatif', 'cond.clear': 'Effacer',
  'cat.manage': 'Gérer les catégories', 'cat.title': 'Catégories', 'cat.hide': 'Masquer', 'cat.show': 'Afficher', 'cat.add': 'Ajouter', 'cat.ph': 'Nouvelle catégorie', 'cat.done': 'Terminé', 'cat.hiddenTag': 'Masquée',
  'dt.notlisted': 'pas en vente', 'dt.timeline': 'Chronologie',
  'dt.s.bought': 'Acheté', 'dt.s.listed': 'En vente', 'dt.s.reserved': 'Réservé', 'dt.s.sold': 'Vendu', 'dt.gap': '+{n} j',
  'dt.money': 'Argent', 'dt.fee': 'Frais de plateforme', 'dt.net': 'Bénéfice net',
  'dt.note.open': 'Le bénéfice net apparaît quand tu le marques vendu.',
  'dt.note.nocost': 'Pas de prix d’achat, donc pas encore de bénéfice net. Ajoute-le dans Modifier les détails.',
  'dt.note.nofee': 'Aucuns frais de plateforme saisis : le bénéfice net est avant frais.',
  'dt.edit': 'Modifier les détails', 'dt.save': 'Enregistrer les modifications',
  'meta.bought': 'acheté {c}',
  'dt.day1': '1 jour', 'dt.days': '{n} jours', 'wo.line': '{st} · en stock depuis {days} · coût {cost}',
  'ret.e4': 'Bénéfice net, 30 derniers jours : {a} → {b}.',
  'ch.total': 'Total : {amount}',
  'ov.lanes.none': 'Rien ne t’attend aujourd’hui.',
  'ov.cur.ok': 'OK',
  'cat.note': 'Renomme, ajoute ou masque. Les changements sont enregistrés tout de suite ; les catégories masquées gardent leurs articles.',
  'act.details': 'Détails', 'age.soldin': 'vendu en {n} j'
};
module.exports = { en, fr };
