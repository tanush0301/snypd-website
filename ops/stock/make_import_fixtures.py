"""Generates the .xlsx fixtures for ops/test_stock_import.cjs with openpyxl (a real spreadsheet writer, so the own reader is tested on real files).
   python ops/stock/make_import_fixtures.py        -> ops/stock/import/*.xlsx   (committed; regenerate only when the cases change)
Cases:
  template-en.xlsx   the 17 template columns, real date cells (two number formats), numbers, a second empty sheet, a blank row between data rows
  template-fr.xlsx   French headers, dates and amounts as TEXT ("27/10/2026", "12,50 EUR"), an unknown condition, a new category, quantity 3
  mixed-types.xlsx   inline-ish cases: shared strings with entities and a rich-text cell, booleans, formulas with cached values, big numbers, sheet names with spaces
"""
import datetime as dt
import os
from openpyxl import Workbook
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'import')
os.makedirs(OUT, exist_ok=True)

EN = ['Item', 'Brand', 'Size', 'Condition', 'Category', 'Quantity', 'Bought', 'Buy price', 'Extra costs', 'Source', 'Platform', 'List price', 'Sold price', 'Sold date', 'Fees', 'Shipping paid', 'Notes']
wb = Workbook(); ws = wb.active; ws.title = 'Items'; ws.append(EN)
d = dt.date
ws.append(['Carhartt Detroit jacket, L', 'Carhartt WIP', 'L', 'Very good', 'Outerwear', 1, d(2026, 9, 1), 30, 0, 'Charity shop', 'Vinted', 85, 80, d(2026, 9, 20), 4, 3.5, 'small mark'])
ws.append(['Levis 501, W32', "Levi's", 'W32', 'Good', 'Bottoms', 2, d(2026, 9, 14), 12.5, 1.2, 'Car boot', 'eBay', 38, None, None, None, None, None])
ws.append([None] * 17)   # a blank row in the middle: row numbers must stay the sheet's own
ws.append(['Nike ACG fleece', 'Nike', 'S', 'New with tag', 'Tops', None, d(2026, 10, 3), 16, None, 'hunt nike acg', None, None, None, None, None, None, None])
ws.append(['Stussy tee', 'Stussy', 'L', None, 'Tops', 1, d(2026, 10, 5), None, None, None, 'Depop', 32, None, None, None, None, None])
for r in (2, 3, 5, 6):
    ws.cell(row=r, column=7).number_format = 'yyyy-mm-dd' if r % 2 == 0 else 'dd/mm/yyyy'
ws2 = wb.create_sheet('Lists'); ws2.append(['New with tag', 'New, no tag', 'Very good', 'Good', 'Satisfactory'])
wb.save(os.path.join(OUT, 'template-en.xlsx'))

FR = ['Article', 'Marque', 'Taille', 'État', 'Catégorie', 'Quantité', "Date d'achat", "Prix d'achat", 'Frais en plus', 'Source', 'Plateforme', 'Prix affiché', 'Prix de vente', 'Date de vente', 'Frais', 'Envoi payé', 'Notes']
wb = Workbook(); ws = wb.active; ws.title = 'Stock'; ws.append(FR)
ws.append(['Veste Barbour Bedale', 'Barbour', '38', 'Très bon état', 'Vestes et manteaux', '1', '27/10/2026', '36,50', '', 'Friperie', 'Vinted', '110', '', '', '', '', ''])
ws.append(['Pull Ralph Lauren', 'Ralph Lauren', 'M', 'Comme neuf', 'Vintage', '3', '03/10/2026', '12 EUR', '1,5', 'Vide-grenier', '', '', '', '', '', '', 'x3'])
ws.append(['Jean Levis 501', "Levi's", 'W32', 'Bon état', 'Bas', '', '15/09/2026', '10,00', '', 'Kringloop', 'Vinted', '30', '28', '30/09/2026', '1,40', '3,50', ''])
wb.save(os.path.join(OUT, 'template-fr.xlsx'))

wb = Workbook(); ws = wb.active; ws.title = 'My items & more'; ws.append(['Item', 'Buy price', 'Notes', 'Bought', 'Quantity'])
ws.append(['Jacket <special> & "quoted"', 25, 'café – notes', d(2026, 8, 3), 1])
ws.append([CellRichText('Rich ', TextBlock(InlineFont(b=True), 'bold'), ' text item'), 1234567.89, None, d(2026, 8, 4), 1])
ws.append(['Formula item', '=10+5', 'TRUE', d(2026, 8, 5), 2])
ws.append(['Boolean notes item', 9, True, None, 1])
wb.save(os.path.join(OUT, 'mixed-types.xlsx'))
print('wrote', sorted(os.listdir(OUT)))
