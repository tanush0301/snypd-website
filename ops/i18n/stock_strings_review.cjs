// Review 3 Nov 2026 (outreach/32 in the website folder): wording fixes + strings of the profit-first Overview, the held default, the fee field and
// "records to fix". Merged LAST into assets/stock-i18n.js by gen_stock_i18n.cjs, so a key here replaces the same key from the earlier files.
// UTF-8 with real accents, informal "tu".
const en = {
  // one meaning of "in stock" everywhere = everything you hold; the status of an item that is held but not listed is "Not listed"
  'status.stock': 'Not listed', 'chip.held': 'In stock',
  'ov.split': '{a} not listed · {b} listed · {c} reserved',
  'it.sub': '{held} in stock · {rows} rows', 'it.sub3': '{held} in stock · {sold} sold · {rows} rows',
  // records to fix
  'ov.partial.note': '{a} of {b} sales count toward profit. {c} miss a cost or a sale price.', 'ov.avg.cap': '{a} of {b} counted',
  'fix.btn': 'Fix them', 'fix.note': 'Sales left out of profit: {n}. Open one to add its cost or sale price.',
  'fix.none': 'Every sale has a cost and a price. Nothing to fix.', 'fix.checked': 'Checked the {n} newest sales of {total}.',
  // Mark sold: Vinted charges sellers nothing (Vinted help 26, read 3 Nov 2026); other platforms get an optional fee field
  'f.fee.sale': 'Platform fee · optional', 'prev.title2': 'Profit', 'prev.f.fee': '{v} fee',
  'sold.formula': 'Profit = sold price − buy price − extra costs − platform fee − shipping you paid.',
  'sold.nofees': 'No fee entered: this is your profit before the platform’s fee.',
  'sold.fee.vinted': 'Vinted charges sellers no selling fee, so this is your profit. Paid boosts go in extra costs.',
  'sold.fee.set': 'Platform fee included.',
  'sold.ctx.listed0': 'listed {v}', 'sold.ctx.price': 'asking {v}',
  // phone item cards and inputs
  'meta.price': 'price {v}', 'meta.profit': 'profit {v}', 'ph.money': 'e.g. {v}', 'tools.btn': 'Filters',
  // 071: sort + claim photo
  'sort.label': 'Sort', 'sort.oldest': 'Longest in stock first', 'sort.newest': 'Newest bought first', 'detail.photo': 'Photo from the Vinted listing'
};
const fr = {
  'status.stock': 'Pas en vente', 'chip.held': 'En stock',
  'ov.split': '{a} pas en vente · {b} en vente · {c} réservés',
  'it.sub': '{held} en stock · {rows} lignes', 'it.sub3': '{held} en stock · {sold} vendus · {rows} lignes',
  'ov.partial.note': '{a} ventes sur {b} comptent dans le bénéfice. {c} n’ont pas de coût ou de prix de vente.', 'ov.avg.cap': '{a} sur {b} comptées',
  'fix.btn': 'Les compléter', 'fix.note': 'Ventes exclues du bénéfice : {n}. Ouvre-en une pour ajouter son coût ou son prix de vente.',
  'fix.none': 'Chaque vente a un coût et un prix. Rien à compléter.', 'fix.checked': 'Vérifié : les {n} ventes les plus récentes sur {total}.',
  'f.fee.sale': 'Frais de la plateforme · facultatif', 'prev.title2': 'Bénéfice', 'prev.f.fee': '{v} frais',
  'sold.formula': 'Bénéfice = prix de vente − prix d’achat − frais en plus − frais de plateforme − port payé.',
  'sold.nofees': 'Aucun frais saisi : c’est ton bénéfice avant les frais de la plateforme.',
  'sold.fee.vinted': 'Vinted ne prend pas de frais de vente au vendeur : c’est ton bénéfice. Les boosts payés vont dans les frais en plus.',
  'sold.fee.set': 'Frais de plateforme inclus.',
  'sold.ctx.listed0': 'affiché {v}', 'sold.ctx.price': 'prix demandé {v}',
  'meta.price': 'prix {v}', 'meta.profit': 'bénéfice {v}', 'ph.money': 'ex. {v}', 'tools.btn': 'Filtres',
  // typo fixes of the step-5 French (coùt, jusqu'è, régles) and an English word left in French
  'lane.meta.cost': 'coût {c}', 'exp.btn': 'Exporter',
  'sort.label': 'Trier', 'sort.oldest': 'Les plus anciens en stock d’abord', 'sort.newest': 'Derniers achats d’abord', 'detail.photo': 'Photo de l’annonce Vinted'
};
module.exports = { en, fr };
