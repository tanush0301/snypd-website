// Writes ops/stock/import/shared-strings.xlsx with SheetJS (any version; bookSST:true = a shared-strings table, like Excel, Google Sheets and LibreOffice write).
// openpyxl (make_import_fixtures.py) writes inline strings, so this second, independent writer covers the other layout.
//   node ops/stock/make_sst_fixture.cjs [path-to-xlsx-package]      (used only to MAKE the fixture; never shipped)
const path = require('node:path');
const X = require(process.argv[2] || process.env.SNYPD_XLSX || 'C:/Users/Tanus/papa/node_modules/xlsx');
const E = String.fromCharCode(0xe9);
const aoa = [
  ['Item', 'Brand', 'Cat' + E + 'gorie', 'Buy price', 'Bought', 'Notes', 'Quantity'],
  ['Barbour jacket & co', 'Barbour', 'Outerwear', 12.5, new Date(Date.UTC(2026, 9, 27)), 'repeat', 2],
  ['Second item', 'Barbour', 'Outerwear', 8, new Date(Date.UTC(2026, 9, 3)), 'repeat', 1],
  ['Third <item>', 'Nike', 'Tops', 5, new Date(Date.UTC(2026, 8, 15)), 'caf' + E, 1]
];
const ws = X.utils.aoa_to_sheet(aoa, { cellDates: true });
['E2', 'E3', 'E4'].forEach(a => { ws[a].z = 'dd/mm/yyyy'; });
const wb = X.utils.book_new(); X.utils.book_append_sheet(wb, ws, 'Stock list');
X.writeFile(wb, path.join(__dirname, 'import', 'shared-strings.xlsx'), { bookSST: true, cellDates: true });
console.log('wrote shared-strings.xlsx');
