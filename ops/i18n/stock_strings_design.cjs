// Design check 5 Nov 2026 (outreach/38 in the website folder), gaps 1-6: return/write-off sheets, item detail (timeline + money),
// Items values, Quick add condition buttons + Manage categories. Merged LAST by stock_strings.cjs, so a key here replaces an earlier one.
// UTF-8 with real accents, informal "tu". Wording follows the Claude Design boards (Round I Ia/Ib, Round C Cb).
const en = {
  'ret.eRevP': 'On {date}: revenue −{refund}, profit {p}.',
  'f.condition.opt': 'Condition · optional', 'cond.clear': 'Clear',
  'cat.manage': 'Manage categories', 'cat.title': 'Categories', 'cat.note': 'Rename, add or hide. Hidden categories keep their items.',
  'cat.hide': 'Hide', 'cat.show': 'Show', 'cat.add': 'Add', 'cat.ph': 'New category', 'cat.done': 'Done', 'cat.hiddenTag': 'Hidden',
  'dt.notlisted': 'not listed', 'dt.timeline': 'Timeline',
  'dt.s.bought': 'Bought', 'dt.s.listed': 'Listed', 'dt.s.reserved': 'Reserved', 'dt.s.sold': 'Sold', 'dt.gap': '+{n}d',
  'dt.money': 'Money', 'dt.fee': 'Platform fee', 'dt.net': 'Net profit',
  'dt.note.open': 'Net profit appears when you mark it sold.',
  'dt.note.nocost': 'No buy price, so no net profit yet. Add it under Edit details.',
  'dt.note.nofee': 'No platform fee entered, so net profit is before fees.',
  'dt.edit': 'Edit details', 'dt.save': 'Save changes',
  'meta.bought': 'bought {c}'
};
const fr = {
  'ret.eRevP': 'Le {date} : chiffre d’affaires −{refund}, bénéfice {p}.',
  'f.condition.opt': 'État · facultatif', 'cond.clear': 'Effacer',
  'cat.manage': 'Gérer les catégories', 'cat.title': 'Catégories', 'cat.note': 'Renomme, ajoute ou masque. Les catégories masquées gardent leurs articles.',
  'cat.hide': 'Masquer', 'cat.show': 'Afficher', 'cat.add': 'Ajouter', 'cat.ph': 'Nouvelle catégorie', 'cat.done': 'Terminé', 'cat.hiddenTag': 'Masquée',
  'dt.notlisted': 'pas en vente', 'dt.timeline': 'Chronologie',
  'dt.s.bought': 'Acheté', 'dt.s.listed': 'En vente', 'dt.s.reserved': 'Réservé', 'dt.s.sold': 'Vendu', 'dt.gap': '+{n} j',
  'dt.money': 'Argent', 'dt.fee': 'Frais de plateforme', 'dt.net': 'Bénéfice net',
  'dt.note.open': 'Le bénéfice net apparaît quand tu le marques vendu.',
  'dt.note.nocost': 'Pas de prix d’achat, donc pas encore de bénéfice net. Ajoute-le dans Modifier les détails.',
  'dt.note.nofee': 'Aucuns frais de plateforme saisis : le bénéfice net est avant frais.',
  'dt.edit': 'Modifier les détails', 'dt.save': 'Enregistrer les modifications',
  'meta.bought': 'acheté {c}'
};
module.exports = { en, fr };
