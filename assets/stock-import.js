/*
 * SNYPD Stock - import engine (step 4). Pure functions, no DOM, no network: runs in the browser (loaded when the user opens Import) and in node tests.
 * Pure ASCII: aliases are written in their normalised ASCII form (lower case, accents stripped), see norm().
 *
 *   parseCsv(text)                     rows of strings; delimiter , ; or tab detected, quotes, BOM, CRLF
 *   readXlsx(arrayBuffer)              {sheets:[{name, rows}]}: an own small .xlsx reader (zip + inflate via DecompressionStream, regex tokenizer for the few XML
 *                                      parts needed). No library: no licence question, no CVEs. Old .xls (OLE2) is refused with a clear code.
 *   buildPlan(table, opts)             header mapping, per-row values (dates, money, condition, category, platform, quantity, status), and the REVIEW numbers
 *   toRpcRows(plan)                    the rows stock_import_rows() takes, with the file row number kept for error reports
 * Money is never converted: every amount is read as the account currency (symbols of another currency are counted and warned about).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SnypdStockImport = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const LIMITS = { fileBytes: 10 * 1024 * 1024, rows: 5000, batch: 500, quantity: 50, xlsxEntryBytes: 60 * 1024 * 1024, sheetRows: 20000 };
  const FIELDS = ['title', 'brand', 'size', 'condition', 'category', 'quantity', 'bought', 'buy', 'extra', 'source', 'platform', 'list', 'sold', 'soldon', 'fee', 'ship', 'notes', 'link', 'status'];   // status last: it never takes a header an older field already matches
  // normalised header -> field. The template's 17 columns (EN) + French + the 8 aliases the landing page promises (handoff landing.importAliasesToAdd)
  // + Dutch and German (Nov 2026, before opening Stock to everyone: a Dutch sheet was refused with no_title_column). Ambiguous single words
  // ('prijs', 'kosten', 'preis') are left out on purpose; 'verkocht op' / 'verkauft am' are dates, never a platform.
  const ALIASES = {
    title: ['item', 'items', 'article', 'title', 'titre', 'name', 'nom', 'product', 'produit', 'description',
      'artikel', 'naam', 'omschrijving', 'beschrijving', 'produkt', 'bezeichnung', 'beschreibung', 'artikelname'],
    brand: ['brand', 'marque', 'merk', 'marke'],
    size: ['size', 'taille', 'maat', 'grosse', 'groesse', 'konfektionsgrosse'],
    condition: ['condition', 'etat', 'state', 'staat', 'conditie', 'toestand', 'zustand'],
    category: ['category', 'categorie', 'type', 'kategorie', 'soort'],
    quantity: ['quantity', 'qty', 'quantite', 'qte', 'nombre', 'units', 'aantal', 'stuks', 'anzahl', 'menge', 'stuck', 'stueck'],
    bought: ['bought', 'bought on', 'date bought', 'purchase date', 'date of purchase', 'date achat', 'date d achat', 'achete le', 'date',
      'aankoopdatum', 'gekocht op', 'datum aankoop', 'inkoopdatum', 'datum', 'kaufdatum', 'gekauft am', 'einkaufsdatum'],
    buy: ['buy price', 'buy', 'bought price', 'purchase price', 'cost', 'cost price', 'prix achat', 'prix d achat', 'cout', 'achat',
      'aankoopprijs', 'aankoop', 'inkoopprijs', 'inkoop', 'kostprijs', 'betaald', 'einkaufspreis', 'einkauf', 'kaufpreis', 'ek', 'bezahlt'],
    extra: ['extra costs', 'extra cost', 'extra', 'frais en plus', 'frais supplementaires', 'additional costs',
      'extra kosten', 'bijkomende kosten', 'zusatzkosten', 'nebenkosten'],
    source: ['source', 'origin', 'origine', 'bought from', 'where', 'lieu', 'achete chez', 'bron', 'herkomst', 'gekocht bij', 'quelle', 'gekauft bei', 'herkunft'],
    platform: ['platform', 'plateforme', 'marketplace', 'sold on', 'sold via', 'verkocht via', 'plattform', 'verkauft uber', 'verkauft ueber'],
    list: ['list price', 'listed price', 'asking price', 'asking', 'prix affiche', 'prix demande', 'prix annonce',
      'vraagprijs', 'advertentieprijs', 'angebotspreis', 'inseratspreis', 'listenpreis'],
    sold: ['sold price', 'sale price', 'selling price', 'sold for', 'prix de vente', 'prix vente', 'vendu a', 'sold',
      'verkoopprijs', 'verkocht voor', 'verkaufspreis', 'verkauft fur', 'verkauft fuer', 'vk'],
    soldon: ['sold date', 'date sold', 'sale date', 'date of sale', 'date vente', 'date de vente', 'vendu le',
      'verkoopdatum', 'verkocht op', 'datum verkoop', 'verkaufsdatum', 'verkauft am'],
    fee: ['fees', 'fee', 'platform fees', 'frais', 'frais de plateforme', 'commission', 'platformkosten', 'commissie', 'gebuhren', 'gebuehren', 'provision'],
    ship: ['shipping paid', 'shipping', 'postage', 'envoi paye', 'envoi', 'frais d envoi', 'frais de port', 'verzendkosten', 'verzending', 'porto', 'versand', 'versandkosten'],
    notes: ['notes', 'note', 'comment', 'comments', 'commentaire', 'commentaires', 'remarks', 'notities', 'opmerking', 'opmerkingen', 'notizen', 'bemerkung', 'kommentar'],
    link: ['link', 'url', 'lien'],
    status: ['status', 'statut', 'stage', 'verkoopstatus', 'verkaufsstatus', 'state of sale']
  };
  // values of a Status column (normalised). Anything else = unknown -> the old price/date rule decides (counted in stats.statusUnknown).
  const STATUS_MAP = {
    'sold': 'sold', 'vendu': 'sold', 'vendue': 'sold', 'verkocht': 'sold', 'verkauft': 'sold', 'sale': 'sold', 'done': 'sold', 'gone': 'sold',
    'listed': 'listed', 'online': 'listed', 'live': 'listed', 'active': 'listed', 'for sale': 'listed', 'en ligne': 'listed', 'en vente': 'listed', 'annonce': 'listed',
    'te koop': 'listed', 'actief': 'listed', 'aangeboden': 'listed', 'inseriert': 'listed', 'aktiv': 'listed', 'zu verkaufen': 'listed',
    'stock': 'stock', 'in stock': 'stock', 'en stock': 'stock', 'held': 'stock', 'unlisted': 'stock', 'not listed': 'stock', 'not for sale': 'stock', 'pas en vente': 'stock',
    'voorraad': 'stock', 'op voorraad': 'stock', 'in voorraad': 'stock', 'niet online': 'stock', 'lager': 'stock', 'auf lager': 'stock', 'nicht inseriert': 'stock' };
  function statusOf(raw) { return STATUS_MAP[norm(raw)] || null; }
  const COND_MAP = { 'new with tag': 'new_with_tag', 'new with tags': 'new_with_tag', 'nwt': 'new_with_tag', 'neuf avec etiquette': 'new_with_tag', 'neuf avec etiquettes': 'new_with_tag', 'new_with_tag': 'new_with_tag',
    'new no tag': 'new_no_tag', 'new without tag': 'new_no_tag', 'new without tags': 'new_no_tag', 'nwot': 'new_no_tag', 'neuf sans etiquette': 'new_no_tag', 'neuf sans etiquettes': 'new_no_tag', 'neuf': 'new_no_tag', 'new_no_tag': 'new_no_tag',
    'very good': 'very_good', 'tres bon etat': 'very_good', 'tres bon': 'very_good', 'tbe': 'very_good', 'very_good': 'very_good',
    'good': 'good', 'bon etat': 'good', 'bon': 'good',
    'satisfactory': 'satisfactory', 'satisfaisant': 'satisfactory', 'etat satisfaisant': 'satisfactory',
    // Dutch + German (Vinted's own labels) and common English words that used to fall into the manual review step
    'nieuw met label': 'new_with_tag', 'nieuw met labels': 'new_with_tag', 'nieuw met kaartje': 'new_with_tag', 'neu mit etikett': 'new_with_tag', 'neu mit etiketten': 'new_with_tag',
    'nieuw zonder label': 'new_no_tag', 'nieuw zonder labels': 'new_no_tag', 'nieuw': 'new_no_tag', 'neu ohne etikett': 'new_no_tag', 'neu ohne etiketten': 'new_no_tag', 'neu': 'new_no_tag',
    'zeer goed': 'very_good', 'zeer goede staat': 'very_good', 'als nieuw': 'very_good', 'sehr gut': 'very_good', 'wie neu': 'very_good', 'like new': 'very_good', 'excellent': 'very_good', 'mint': 'very_good',
    'goed': 'good', 'goede staat': 'good', 'gut': 'good',
    // 'used' / 'gebruikt' / 'gebraucht' / 'porte' are left out on purpose: they can mean good OR satisfactory, so they go to the review step where the user picks once
    'redelijk': 'satisfactory', 'zufriedenstellend': 'satisfactory', 'fair': 'satisfactory' };
  const PLAT_MAP = { 'vinted': 'vinted', 'ebay': 'ebay', 'depop': 'depop', 'vestiaire': 'vestiaire', 'vestiaire collective': 'vestiaire', 'marktplaats': 'marktplaats', 'facebook': 'facebook', 'facebook marketplace': 'facebook', 'fb marketplace': 'facebook', 'fb': 'facebook',
    '2dehands': 'marktplaats', '2ememain': 'marktplaats', 'tweedehands': 'marktplaats' };   // the server accepts only these 7 values (065 check); everything else = 'other'
  function platformOf(raw) { const k = norm(raw); return PLAT_MAP[k] || PLAT_MAP[k.split(' ')[0]] || 'other'; }   // 'Vinted.be' / 'eBay.de' / 'facebook mp' -> first word
  const DEFAULT_CATS = { tops: ['tops', 'hauts'], bottoms: ['bottoms', 'bas'], outerwear: ['outerwear', 'vestes et manteaux'], shoes: ['shoes', 'chaussures'], bags: ['bags and accessories', 'sacs et accessoires', 'bags'], electronics: ['electronics', 'electronique'], home: ['home', 'maison'], collect: ['collectibles and games', 'objets de collection et jeux', 'collectibles'], other: ['other', 'autre'] };
  const MONTHS = { jan: 1, janv: 1, january: 1, janvier: 1, feb: 2, fev: 2, fevr: 2, february: 2, fevrier: 2, mar: 3, mars: 3, march: 3, apr: 4, avr: 4, april: 4, avril: 4, may: 5, mai: 5, jun: 6, juin: 6, june: 6, jul: 7, juil: 7, july: 7, juillet: 7,
    aug: 8, aout: 8, august: 8, sep: 9, sept: 9, september: 9, septembre: 9, oct: 10, october: 10, octobre: 10, nov: 11, november: 11, novembre: 11, dec: 12, december: 12, decembre: 12 };
  const SYMBOLS = { EUR: [String.fromCharCode(0x20ac), 'eur'], GBP: [String.fromCharCode(0xa3), 'gbp'], USD: ['$', 'usd'], SEK: ['kr', 'sek'], PLN: ['z' + String.fromCharCode(0x142), 'pln'], CZK: ['K' + String.fromCharCode(0x10d), 'czk'], RON: ['lei', 'ron'], HUF: ['Ft', 'huf'] };

  const DIACRITICS = new RegExp('[' + String.fromCharCode(0x300) + '-' + String.fromCharCode(0x36f) + ']', 'g');
  const SHARP_S = new RegExp(String.fromCharCode(0xdf), 'g');   // German sharp s has no NFD decomposition: Groesse / Grosse -> 'grosse'
  function norm(v) { return String(v == null ? '' : v).toLowerCase().replace(SHARP_S, 'ss').normalize('NFD').replace(DIACRITICS, '').replace(/[^a-z0-9_]+/g, ' ').replace(/\s+/g, ' ').trim(); }

  // ------------------------------------------------------------------ CSV
  function detectDelimiter(text) {
    const line = text.slice(0, 4000).split(/\r?\n/).find(l => l.trim() !== '') || '';
    let best = ',', bestN = -1, inQ = false; const count = { ',': 0, ';': 0, '\t': 0 };
    for (const ch of line) { if (ch === '"') inQ = !inQ; else if (!inQ && ch in count) count[ch]++; }
    for (const d of [',', ';', '\t']) if (count[d] > bestN) { best = d; bestN = count[d]; }
    return best;
  }
  function parseCsv(text, delimiter) {
    text = String(text || ''); if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);
    const d = delimiter || detectDelimiter(text), rows = []; let row = [], cell = '', q = false, i = 0;
    while (i < text.length) {
      const c = text[i];
      if (q) { if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += c; }
      else if (c === '"' && cell === '') q = true;
      else if (c === d) { row.push(cell); cell = ''; }
      else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; row.push(cell); cell = ''; rows.push(row); row = []; }
      else cell += c;
      i++;
    }
    if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
    while (rows.length && rows[rows.length - 1].every(c => String(c).trim() === '')) rows.pop();   // trailing blank lines go; blank lines in the middle stay so row numbers match the file
    return { rows: rows, delimiter: d };
  }

  // ------------------------------------------------------------------ XLSX (zip + a few XML parts)
  class ImportError extends Error { constructor(code, msg) { super(msg || code); this.name = 'ImportError'; this.code = code; } }
  const u16 = (b, o) => b[o] | (b[o + 1] << 8), u32 = (b, o) => (b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)) >>> 0;
  async function inflateRaw(bytes, maxBytes) {
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
    const reader = stream.getReader(), parts = []; let total = 0;
    for (;;) { const r = await reader.read(); if (r.done) break; total += r.value.length; if (total > maxBytes) { try { await reader.cancel(); } catch (e) {} throw new ImportError('too_big', 'A part of the file is too large'); } parts.push(r.value); }
    const out = new Uint8Array(total); let o = 0; for (const p of parts) { out.set(p, o); o += p.length; } return out;
  }
  async function unzip(buffer) {
    const b = new Uint8Array(buffer);
    if (b.length > 4 && u32(b, 0) === 0xE011CFD0) throw new ImportError('xls_unsupported', 'Old .xls files are not supported');
    let eocd = -1; for (let i = b.length - 22; i >= Math.max(0, b.length - 66000); i--) if (u32(b, i) === 0x06054b50) { eocd = i; break; }
    if (eocd < 0) throw new ImportError('not_a_spreadsheet', 'Not a .xlsx file');
    const n = u16(b, eocd + 10); let p = u32(b, eocd + 16); const files = {};
    for (let k = 0; k < n; k++) {
      if (u32(b, p) !== 0x02014b50) throw new ImportError('not_a_spreadsheet', 'Broken zip directory');
      const flags = u16(b, p + 8), method = u16(b, p + 10), csize = u32(b, p + 20), usize = u32(b, p + 24), nl = u16(b, p + 28), el = u16(b, p + 30), cl = u16(b, p + 32), lho = u32(b, p + 42);
      const name = new TextDecoder().decode(b.subarray(p + 46, p + 46 + nl));
      if (flags & 1) throw new ImportError('encrypted', 'The file is password protected');
      files[name] = { method, csize, usize, lho };
      p += 46 + nl + el + cl;
    }
    return { b, files, async text(name) {
      const f = files[name]; if (!f) return null;
      if (f.usize > LIMITS.xlsxEntryBytes) throw new ImportError('too_big', 'A part of the file is too large');
      const o = f.lho; if (u32(b, o) !== 0x04034b50) throw new ImportError('not_a_spreadsheet', 'Broken zip entry');
      const start = o + 30 + u16(b, o + 26) + u16(b, o + 28), data = b.subarray(start, start + f.csize);
      const raw = f.method === 0 ? data : (f.method === 8 ? await inflateRaw(data, LIMITS.xlsxEntryBytes) : null);
      if (!raw) throw new ImportError('not_a_spreadsheet', 'Unsupported compression');
      return new TextDecoder('utf-8').decode(raw);
    } };
  }
  function unent(s) { return s.replace(/&(#x[0-9a-fA-F]+|#[0-9]+|amp|lt|gt|quot|apos);/g, (m, e) => e === 'amp' ? '&' : e === 'lt' ? '<' : e === 'gt' ? '>' : e === 'quot' ? '"' : e === 'apos' ? "'" : String.fromCodePoint(e[1] === 'x' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10))); }
  function attrs(tag) { const o = {}; tag.replace(/([A-Za-z_:][\w:.-]*)="([^"]*)"/g, (m, k, v) => { o[k] = unent(v); return m; }); return o; }
  function textOf(xml) { let out = ''; xml.replace(/<t(?:\s[^>]*)?>([\s\S]*?)<\/t>/g, (m, t) => { out += unent(t); return m; }); return out; }
  function colIndex(ref) { const m = /^([A-Z]+)/.exec(ref); let n = 0; for (const ch of m[1]) n = n * 26 + (ch.charCodeAt(0) - 64); return n - 1; }
  const BUILTIN_DATE = new Set([14, 15, 16, 17, 18, 19, 20, 21, 22, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 45, 46, 47, 50, 51, 52, 53, 54, 55, 56, 57, 58]);
  function isDateCode(code) { const c = String(code).replace(/"[^"]*"/g, '').replace(/\[[^\]]*\]/g, '').replace(/\\./g, ''); return /[dmyhs]/i.test(c) && !/^(general|@)$/i.test(c.trim()); }
  function serialToIso(n) { const ms = Date.UTC(1899, 11, 30) + Math.floor(n) * 86400000, d = new Date(ms); return d.getUTCFullYear() + '-' + String(d.getUTCMonth() + 1).padStart(2, '0') + '-' + String(d.getUTCDate()).padStart(2, '0'); }
  async function readXlsx(buffer) {
    if (buffer.byteLength > LIMITS.fileBytes) throw new ImportError('too_big', 'File is larger than 10 MB');
    const z = await unzip(buffer);
    const wb = await z.text('xl/workbook.xml'); if (!wb) throw new ImportError('not_a_spreadsheet', 'No workbook in the file');
    const rels = {}; ((await z.text('xl/_rels/workbook.xml.rels')) || '').replace(/<Relationship\b[^>]*>/g, t => { const a = attrs(t); rels[a.Id] = a.Target; return t; });
    const sheets = []; wb.replace(/<sheet\b[^>]*>/g, t => { const a = attrs(t); sheets.push({ name: a.name, target: rels[a['r:id']] }); return t; });
    const sst = []; ((await z.text('xl/sharedStrings.xml')) || '').replace(/<si\b[^>]*>([\s\S]*?)<\/si>/g, (m, si) => { sst.push(textOf(si.replace(/<rPh\b[\s\S]*?<\/rPh>/g, ''))); return m; });
    const styles = (await z.text('xl/styles.xml')) || '', custom = {};
    styles.replace(/<numFmt\b[^>]*>/g, t => { const a = attrs(t); custom[a.numFmtId] = a.formatCode; return t; });
    const xfs = []; const cx = /<cellXfs\b[^>]*>([\s\S]*?)<\/cellXfs>/.exec(styles);
    if (cx) cx[1].replace(/<xf\b[^>]*>/g, t => { const id = +attrs(t).numFmtId || 0; xfs.push(BUILTIN_DATE.has(id) || (custom[id] != null && isDateCode(custom[id]))); return t; });
    const out = [];
    for (const sh of sheets) {
      if (!sh.target) continue;
      const path = sh.target.charAt(0) === '/' ? sh.target.slice(1) : 'xl/' + sh.target.replace(/^\.\//, '');
      const xml = await z.text(path); if (xml == null) continue;
      const rows = [];
      xml.replace(/<row\b[^>]*?(?:\/>|>([\s\S]*?)<\/row>)/g, (m, inner) => {
        if (rows.length >= LIMITS.sheetRows) return m;
        const rn = +(attrs(m.slice(0, m.indexOf('>') + 1)).r || (rows.length + 1)), cells = [];
        (inner || '').replace(/<c\b([^>]*?)(?:\/>|>([\s\S]*?)<\/c>)/g, (mc, at, body) => {
          const a = attrs(at), ci = colIndex(a.r || 'A1'), t = a.t || 'n', v = body && /<v>([\s\S]*?)<\/v>/.exec(body);
          let val = '';
          if (t === 's') val = v ? (sst[+v[1]] || '') : '';
          else if (t === 'inlineStr') val = body ? textOf(body) : '';
          else if (t === 'str') val = v ? unent(v[1]) : '';
          else if (t === 'b') val = v ? (v[1] === '1' ? 'TRUE' : 'FALSE') : '';
          else if (t === 'e') val = '';
          else if (t === 'd') val = v ? unent(v[1]).slice(0, 10) : '';   // ISO 8601 date cell (some writers): the date part as written
          else if (v && v[1] !== '') { const num = Number(v[1]); val = xfs[+a.s || 0] && isFinite(num) ? serialToIso(num) : (isFinite(num) ? num : unent(v[1])); }
          while (cells.length < ci) cells.push('');
          cells[ci] = val; return mc;
        });
        while (rows.length < rn - 1) rows.push([]);
        rows[rn - 1] = cells; return m;
      });
      out.push({ name: sh.name, rows: Array.from(rows, r => r || []) });   // blank rows stay, so row numbers in reports are the spreadsheet's own
    }
    if (!out.length) throw new ImportError('not_a_spreadsheet', 'No sheet found');
    return { sheets: out };
  }

  // ------------------------------------------------------------------ values
  function mapHeaders(headers) {
    const taken = {}, map = headers.map((h, col) => {
      const parts = [norm(h)].concat(String(h == null ? '' : h).split(/[\/|]/).map(norm)).filter(Boolean); let field = null;
      for (const f of FIELDS) { if (taken[f]) continue; if (ALIASES[f].some(a => parts.indexOf(a) >= 0)) { field = f; break; } }
      if (field) taken[field] = true;
      return { col: col, header: String(h == null ? '' : h).trim(), field: field };
    });
    return map;
  }
  function symbolsIn(text, currency) {   // currencies named in a money cell that are NOT the account currency
    const s = String(text), low = s.toLowerCase(), found = [];
    for (const cur of Object.keys(SYMBOLS)) { if (cur === currency) continue; const sym = SYMBOLS[cur][0]; if (s.indexOf(sym) >= 0 && !(cur === 'SEK' && /kr/i.test(s) === false)) { if (cur === 'SEK' ? /(^|[^a-z])kr([^a-z]|$)/i.test(s) : true) found.push(cur); } else if (new RegExp('(^|[^a-z])' + SYMBOLS[cur][1] + '([^a-z]|$)').test(low)) found.push(cur); }
    return found;
  }
  function parseMoneyCell(v, lang, decimalLang) {   // -> {cents, empty, bad}
    if (v == null || v === '') return { empty: true };
    if (typeof v === 'number') return v >= 0 && isFinite(v) ? { cents: Math.round(v * 100) } : { bad: true };
    const C = (typeof window !== 'undefined' && window.SnypdStock) || (typeof require === 'function' ? require('./stock-core.js') : null);
    const r = C.parseMoneyInput(v, decimalLang || lang);
    return r.empty ? { empty: true } : (r.ok ? { cents: r.cents } : { bad: true });
  }
  function dateParts(v) {   // -> {a,b,y} for numeric d/m/y style, or {iso}, or {bad}
    if (v == null || v === '') return { empty: true };
    if (typeof v === 'number') return v > 20000 && v < 80000 ? { iso: serialToIso(v) } : { bad: true };
    const s = String(v).trim();
    let m = /^(\d{4})[-\/.](\d{1,2})[-\/.](\d{1,2})(?:[T\s].*)?$/.exec(s); if (m) return { y: +m[1], mo: +m[2], d: +m[3], iso: true };
    m = /^(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2}|\d{4})(?:[T\s].*)?$/.exec(s); if (m) return { a: +m[1], b: +m[2], y: m[3].length === 2 ? 2000 + +m[3] : +m[3] };
    m = /^(\d{1,2})\s+([^\s\d,/.-]+\.?)\s+(\d{4})$/.exec(s) || null; if (m) { const mo = MONTHS[norm(m[2])]; if (mo) return { y: +m[3], mo: mo, d: +m[1], iso: true }; }
    m = /^([A-Za-z.]+)\s+(\d{1,2}),?\s+(\d{4})$/.exec(s); if (m) { const mo = MONTHS[norm(m[1])]; if (mo) return { y: +m[3], mo: mo, d: +m[2], iso: true }; }
    return { bad: true };
  }
  function toIso(p, order, now) {
    if (p.empty || p.bad) return null;
    if (typeof p.iso === 'string') return p.iso;
    let y = p.y, mo, d;
    if (p.iso === true) { mo = p.mo; d = p.d; } else if (order === 'mdy') { mo = p.a; d = p.b; } else { d = p.a; mo = p.b; }
    const dt = new Date(Date.UTC(y, mo - 1, d)); if (!(dt.getUTCFullYear() === y && dt.getUTCMonth() === mo - 1 && dt.getUTCDate() === d)) return null;
    const iso = y + '-' + String(mo).padStart(2, '0') + '-' + String(d).padStart(2, '0');
    if (y < 2000 || iso > now) return null;
    return iso;
  }
  function detectOrder(tables, lang) {   // looks at every numeric d/m/y cell of the date columns
    let dmy = 0, mdy = 0, sample = null;
    for (const v of tables) { const p = dateParts(v); if (p.a == null) continue; if (p.a > 12 && p.b <= 12) { dmy++; sample = sample || v; } else if (p.b > 12 && p.a <= 12) { mdy++; sample = sample || v; } }
    if (dmy && !mdy) return { order: 'dmy', certain: true, sample: sample };
    if (mdy && !dmy) return { order: 'mdy', certain: true, sample: sample };
    if (dmy && mdy) return { order: 'dmy', certain: false, mixed: true, sample: sample };
    return { order: 'dmy', certain: false, sample: null };   // nothing tells them apart: day first, like fr and en-GB; the screen asks
  }

  // ------------------------------------------------------------------ the plan
  function slugKey(name, taken) { let base = 'c-' + norm(name).replace(/ /g, '-').slice(0, 34); if (base === 'c-') base = 'c-cat'; let k = base, i = 2; while (taken.has(k)) k = base.slice(0, 36) + '-' + i++; taken.add(k); return k; }
  function buildPlan(table, opts) {
    opts = opts || {};
    const lang = opts.lang || 'en', currency = opts.currency || 'EUR', now = opts.today || new Date().toISOString().slice(0, 10);
    const indexed = (table.rows || []).map((r, i) => ({ r: r || [], n: i + 1 })).filter(x => x.r.some(c => String(c == null ? '' : c).trim() !== '')), rows = indexed.map(x => x.r);
    const plan = { mapping: [], rows: [], stats: {}, review: {}, errors: [], delimiter: table.delimiter || null };
    if (!rows.length) { plan.errors.push('empty'); return plan; }

    plan.mapping = opts.mapping || mapHeaders(rows[0]);
    if (!opts.mapping) {   // 'Sold on' / 'Sold via' style header that holds DATES (>= 80% of filled cells): it is the sale date, not the platform. Shown in review.remapped.
      const pm = plan.mapping.filter(m => m.field === 'platform')[0];
      if (pm && !plan.mapping.some(m => m.field === 'soldon')) {
        const vals = indexed.slice(1, 201).map(x => x.r[pm.col]).filter(v => v != null && String(v).trim() !== '');
        const dated = vals.filter(v => !dateParts(v).bad).length;
        if (vals.length && dated / vals.length >= 0.8) { pm.field = 'soldon'; plan.review.remapped = [{ header: pm.header, from: 'platform', to: 'soldon' }]; }
      }
    }
    const colOf = {}; plan.mapping.forEach(m => { if (m.field) colOf[m.field] = m.col; });
    if (colOf.title == null) { plan.errors.push('no_title_column'); return plan; }
    const data = indexed.slice(1, 1 + LIMITS.rows); plan.truncated = indexed.length - 1 > LIMITS.rows ? indexed.length - 1 - LIMITS.rows : 0;
    const decimalLang = (table.delimiter === ';') ? 'fr' : lang;
    const cell = (r, f) => (colOf[f] == null ? '' : (r[colOf[f]] == null ? '' : r[colOf[f]]));
    // date order
    const dateCells = []; data.forEach(it => { dateCells.push(cell(it.r, 'bought'), cell(it.r, 'soldon')); });
    const det = detectOrder(dateCells, lang), order = opts.dateOrder || det.order;
    plan.review.dateOrder = { order: order, detected: det.order, certain: det.certain, mixed: !!det.mixed, sample: det.sample, hasNumericDates: dateCells.some(v => dateParts(v).a != null) };
    // categories
    const cats = (opts.categories || []).map(c => ({ key: c.key, names: [norm(c.name)].concat(DEFAULT_CATS[c.key] || []) }));
    Object.keys(DEFAULT_CATS).forEach(k => { if (!cats.some(c => c.key === k)) cats.push({ key: k, names: DEFAULT_CATS[k] }); });
    const taken = new Set(cats.map(c => c.key)), newCats = {}, newKeys = {};
    const unrec = {}, condChoice = opts.conditionMap || {}, catChoice = opts.categoryMap || {};
    const st = { rows: data.length, skippedNoTitle: 0, items: 0, held: 0, sold: 0, listed: 0, noBuy: 0, badDates: 0, soldNoDate: 0, qtyRows: 0, badMoney: 0, mixedCells: 0, moneyCells: 0, duplicates: 0, condSet: 0, condEmpty: 0, soldNoPrice: 0, statusUnknown: 0 };
    const seen = {}, mixed = {};
    data.forEach(it => {
      const r = it.r, n = it.n;
      const title = String(cell(r, 'title')).trim();
      if (!title) { st.skippedNoTitle++; return; }
      const flags = [], p = { title: title.slice(0, 140) };
      const text = f => { const v = String(cell(r, f)).trim(); return v === '' ? null : v; };
      p.brand = text('brand'); p.size = text('size'); p.notes = text('notes'); p.link = text('link'); p.src = text('source'); if (p.src) p.src_type = 'place';
      // money
      const money = f => { const raw = cell(r, f); const m = parseMoneyCell(raw, lang, decimalLang); if (m.empty) return null; st.moneyCells++; if (typeof raw === 'string') { const s = symbolsIn(raw, currency); if (s.length) { st.mixedCells++; s.forEach(x => { mixed[x] = (mixed[x] || 0) + 1; }); } } if (m.bad) { st.badMoney++; flags.push('bad_' + f); return null; } return m.cents; };
      p.buy_cents = money('buy'); const ex = money('extra'); p.extra_cents = ex == null ? 0 : ex; p.list_cents = money('list'); p.sold_cents = money('sold'); p.fee_cents = money('fee'); p.ship_paid_cents = money('ship');
      if (p.buy_cents == null) st.noBuy++;
      // quantity
      const qraw = cell(r, 'quantity'); let q = 1;
      if (String(qraw).trim() !== '') { q = Math.round(Number(String(qraw).replace(',', '.'))); if (!(q >= 1 && q <= LIMITS.quantity)) { flags.push('bad_quantity'); q = null; } else if (q > 1) st.qtyRows++; }
      p.quantity = q;
      // dates
      const bp = dateParts(cell(r, 'bought')); let bought = toIso(bp, order, now); if (!bought && !bp.empty) { st.badDates++; flags.push('bad_bought'); }
      p.bought_on = bought;
      const sp = dateParts(cell(r, 'soldon')); let soldOn = toIso(sp, order, now); if (!soldOn && !sp.empty) { st.badDates++; flags.push('bad_soldon'); }
      // condition
      const craw = text('condition');
      if (craw) { const key = norm(craw), g = COND_MAP[key] || (condChoice[key] != null ? condChoice[key] : undefined); if (g) { p.condition = g; st.condSet++; } else if (g === '') { p.condition = null; st.condEmpty++; } else { (unrec[craw] = unrec[craw] || []).push(n); p.condition = null; st.condEmpty++; } } else { p.condition = null; st.condEmpty++; }
      // category
      const kraw = text('category');
      if (kraw) { const key = norm(kraw), hit = cats.filter(c => c.names.indexOf(key) >= 0)[0];
        if (hit) p.category = hit.key;
        else if (catChoice[key] === 'skip') p.category = null;
        else { (newCats[kraw] = newCats[kraw] || []).push(n); if (!newKeys[key]) newKeys[key] = { key: slugKey(kraw, taken), name: kraw.slice(0, 40) }; p.category = newKeys[key].key; } }
      else p.category = null;
      // platform
      const praw = text('platform'); p.platform = praw ? platformOf(praw) : null;
      // status
      // an explicit Status column wins; without one (or with a value we do not know) the old rule: a sale price/date = sold, a list price/platform = listed
      const sraw = text('status'), sv = sraw ? statusOf(sraw) : null; if (sraw && !sv) st.statusUnknown++;
      if (sv === 'sold' || (!sv && (p.sold_cents != null || soldOn))) {
        p.status = 'sold';
        if (!soldOn) { soldOn = p.bought_on || now; st.soldNoDate++; flags.push('sold_no_date'); }   // the server refuses a sold row without sold_on (066): never send null
        p.sold_on = soldOn; st.sold++;
        if (p.sold_cents == null) st.soldNoPrice++;   // counted for the review screen; no per-row flag (the UI has no label for one, and a date without a price is a valid sale)
      }
      else if (sv === 'listed' || (!sv && (p.list_cents != null || p.platform))) { p.status = 'listed'; st.listed++; st.held += q || 0; }
      else { p.status = 'stock'; st.held += q || 0; }
      if (p.status === 'sold') { /* sold rows keep platform; fee/ship stay */ } else { p.fee_cents = null; p.ship_paid_cents = null; }
      st.items += q || 0;
      const dk = norm(title) + '|' + p.buy_cents + '|' + p.bought_on; if (seen[dk]) { st.duplicates++; flags.push('duplicate'); } seen[dk] = true;
      if (flags.indexOf('duplicate') >= 0 && opts.skipDuplicates) return;
      plan.rows.push({ n: n, flags: flags, payload: p, bad: flags.indexOf('bad_quantity') >= 0 });
    });
    plan.review.unrecognisedConditions = unrec; plan.review.newCategories = newCats; plan.review.newCategoryKeys = Object.keys(newKeys).map(k => newKeys[k]);
    plan.review.mixedCurrencies = mixed; plan.stats = st;
    // free-cap preview: how many HELD items of the file fit (server enforces the same, row by row)
    const left = opts.freeLeft == null ? null : opts.freeLeft; let used = 0, over = 0;
    if (left != null) plan.rows.forEach(r => { if (r.payload.status !== 'sold' && r.payload.quantity) { if (used + r.payload.quantity <= left) used += r.payload.quantity; else over += r.payload.quantity; } });
    plan.review.freeCap = left == null ? null : { left: left, fits: used, over: over };
    return plan;
  }
  function toRpcRows(plan) {
    return plan.rows.filter(r => !r.bad).map(r => { const p = Object.assign({}, r.payload); Object.keys(p).forEach(k => { if (p[k] == null) delete p[k]; }); return { n: r.n, row: p }; });
  }
  function batches(rpcRows, size) { const out = []; for (let i = 0; i < rpcRows.length; i += (size || LIMITS.batch)) out.push(rpcRows.slice(i, i + (size || LIMITS.batch))); return out; }

  async function readFile(file) {   // browser File -> {sheets:[{name, table}]}
    if (file.size > LIMITS.fileBytes) throw new ImportError('too_big', 'File is larger than 10 MB');
    const name = String(file.name || '').toLowerCase();
    if (/\.xlsx$|\.xlsm$/.test(name)) { const x = await readXlsx(await file.arrayBuffer()); return { kind: 'xlsx', sheets: x.sheets.map(s => ({ name: s.name, table: { rows: s.rows } })) }; }
    if (/\.xls$/.test(name)) throw new ImportError('xls_unsupported', 'Old .xls files are not supported');
    const buf = new Uint8Array(await file.arrayBuffer());
    if (buf.length > 3 && buf[0] === 0x50 && buf[1] === 0x4b) { const x = await readXlsx(buf.buffer); return { kind: 'xlsx', sheets: x.sheets.map(s => ({ name: s.name, table: { rows: s.rows } })) }; }
    let text = new TextDecoder('utf-8', { fatal: false }).decode(buf);
    if (text.indexOf(String.fromCharCode(0xfffd)) >= 0) text = new TextDecoder('windows-1252').decode(buf);   // a French Excel CSV saved as ANSI
    const c = parseCsv(text); return { kind: 'csv', sheets: [{ name: file.name, table: { rows: c.rows, delimiter: c.delimiter } }] };
  }

  return { LIMITS, FIELDS, ALIASES, COND_MAP, ImportError, norm, parseCsv, detectDelimiter, readXlsx, readFile, mapHeaders, buildPlan, toRpcRows, batches, serialToIso, symbolsIn, dateParts, toIso };
});
