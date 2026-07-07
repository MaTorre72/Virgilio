/**
 * ============================================================
 *  BUCOLICHE — Registro operazioni Progetto Virgilio v1.1
 * ============================================================
 *  Schema a 17 colonne che separano i dati ML (colonne 11-17)
 *  dai dati operativi (1-10). Le righe gmail_staging vengono
 *  arricchite con il contesto pratica al momento dell'archiviazione,
 *  senza creare righe duplicate.
 *
 *  Dipendenze: CONFIG (definito in caronte.gs)
 *
 *  PRIVACY: dominio mittente soltanto (no email completa cliente).
 *  Retention policy: righe > 2 anni andrebbero archiviate.
 * ============================================================
 */


// ── SCHEMA COLONNE ────────────────────────────────────────────────────────────

/**
 * Indici colonne Bucoliche (1-based, compatibili con sheet.getRange()).
 * Usati sia in registraSuBucoliche() che in aggiornaRigheAllegati().
 */
const BUCOLICHE_COLS = {
  timestamp:                1,   // Data/ora evento (fuso Europe/Rome)
  origine:                  2,   // gmail_staging | gmail_archiviato | form_virgilio | vtenext
  cliente:                  3,   // Ragione sociale
  sito:                     4,   // Sito/stabilimento
  pratica:                  5,   // Tipo pratica (AUA, AIA…)
  anno:                     6,   // Anno apertura
  tecnici:                  7,   // Tecnici assegnati
  note:                     8,   // Note libere
  url_cartella:             9,   // URL cartella/file Drive
  id_drive:                10,   // ID Drive (file per staging, cartella per pratica)
  // ── Colonne ML — popolate solo per gmail_staging ──
  mittente_dominio:        11,   // Dominio mittente (es. "fomet" da fomet@fomet.it)
  oggetto_email:           12,   // Oggetto email
  nome_file:               13,   // Nome originale del file allegato
  estensione:              14,   // Estensione file (pdf, xlsx…)
  dimensione_kb:           15,   // Dimensione allegato in KB (int)
  stato:                   16,   // in_limbo | archiviato | errore
  timestamp_archiviazione: 17,   // Data/ora spostamento Limbo → pratica
};
const BUCOLICHE_NUM_COLS = 17;


// ── SCRITTURA ─────────────────────────────────────────────────────────────────

/**
 * Registra una riga di operazione sulle Bucoliche.
 *
 * Campi core (tutti i tipi di riga):
 *   origine, cliente, sito, pratica, anno, tecnici, note, urlCartella, idDrive
 *
 * Campi ML (solo gmail_staging):
 *   mittenteDominio, oggettoEmail, nomeFile, estensione, dimensioneKb, stato
 *
 * @param {Object} riga
 */
function registraSuBucoliche(riga) {
  try {
    const sheet = _aprifoglioBucoliche();
    _assicuraIntestazione(sheet);

    sheet.appendRow([
      _timestampLocale(),                                                        //  1
      riga.origine              || '',                                           //  2
      riga.cliente              || '',                                           //  3
      riga.sito                 || '',                                           //  4
      riga.pratica              || '',                                           //  5
      riga.anno                 || '',                                           //  6
      Array.isArray(riga.tecnici) ? riga.tecnici.join(', ') : (riga.tecnici || ''), //  7
      riga.note                 || '',                                           //  8
      riga.urlCartella          || '',                                           //  9
      riga.idDrive              || '',                                           // 10
      riga.mittenteDominio      || '',                                           // 11
      riga.oggettoEmail         || '',                                           // 12
      riga.nomeFile             || '',                                           // 13
      riga.estensione           || '',                                           // 14
      riga.dimensioneKb !== undefined ? riga.dimensioneKb : '',                 // 15
      riga.stato                || '',                                           // 16
      riga.timestampArchiviazione || '',                                         // 17
    ]);

    Logger.log(`[Bucoliche] Riga registrata: ${riga.origine} | ${riga.cliente || riga.mittenteDominio}`);

  } catch (err) {
    Logger.log(`[Bucoliche] ERRORE in registraSuBucoliche: ${err.message}`);
    // Non rilancia — la mancata scrittura non deve bloccare l'operazione principale
  }
}


/**
 * Aggiorna in blocco le righe gmail_staging corrispondenti ai fileId forniti.
 * Chiamata da doPost() dopo lo spostamento Limbo → 02_corrispondenza.
 *
 * Legge tutta la griglia, modifica in memoria, riscrive in un unico setValues().
 *
 * @param {string[]} fileIds       - Array di Drive file ID da aggiornare
 * @param {Object}   datiPratica   - { cliente, sito, pratica, anno, urlCartella }
 * @returns {number} Numero di righe aggiornate
 */
function aggiornaRigheAllegati(fileIds, datiPratica) {
  if (!fileIds || fileIds.length === 0) return 0;

  try {
    const sheet    = _aprifoglioBucoliche();
    const numRighe = sheet.getLastRow();
    if (numRighe <= 1) return 0;   // solo header o vuoto

    const range = sheet.getRange(2, 1, numRighe - 1, BUCOLICHE_NUM_COLS);
    const dati  = range.getValues();

    const adesso = _timestampLocale();
    let aggiornate = 0;

    // Indici 0-based per l'array in memoria
    const C = {};
    for (const [nome, idx] of Object.entries(BUCOLICHE_COLS)) C[nome] = idx - 1;

    for (let r = 0; r < dati.length; r++) {
      const fileId = dati[r][C.id_drive];
      if (!fileIds.includes(fileId)) continue;

      dati[r][C.origine]                  = 'gmail_archiviato';
      dati[r][C.cliente]                  = datiPratica.cliente;
      dati[r][C.sito]                     = datiPratica.sito;
      dati[r][C.pratica]                  = datiPratica.pratica;
      dati[r][C.anno]                     = datiPratica.anno;
      dati[r][C.url_cartella]             = datiPratica.urlCartella;
      dati[r][C.stato]                    = 'archiviato';
      dati[r][C.timestamp_archiviazione]  = adesso;
      aggiornate++;
    }

    if (aggiornate > 0) {
      range.setValues(dati);
      Logger.log(`[Bucoliche] ${aggiornate} righe aggiornate → archiviato`);
    } else {
      Logger.log('[Bucoliche] aggiornaRigheAllegati: nessuna riga corrispondente trovata.');
    }

    return aggiornate;

  } catch (err) {
    Logger.log(`[Bucoliche] ERRORE in aggiornaRigheAllegati: ${err.message}`);
    return 0;
  }
}


/**
 * Registra un errore sui supporti Bucoliche come evento di Registro.
 *
 * @param {string} origine   - Modulo che ha generato l'errore
 * @param {string} messaggio - Descrizione errore
 * @param {Object} contesto  - Dati parziali disponibili (opzionale)
 */
function registraErrore(origine, messaggio, contesto) {
  _bucolicheRegistraEventoRegistro_('errore', origine, messaggio, contesto, '#FCE4D6');
}

/**
 * Registra un conflitto sui supporti Bucoliche come evento di Registro.
 *
 * @param {string} origine   - Modulo che ha generato il conflitto
 * @param {string} messaggio - Descrizione conflitto
 * @param {Object} contesto  - Dati parziali disponibili (opzionale)
 */
function registraConflitto(origine, messaggio, contesto) {
  _bucolicheRegistraEventoRegistro_('conflitto', origine, messaggio, contesto, '#FFF2CC');
}

function _bucolicheRegistraEventoRegistro_(tipo, origine, messaggio, contesto, sfondo) {
  try {
    const sheet = _aprifoglioBucoliche();
    _assicuraIntestazione(sheet);

    const ultimaRiga = sheet.getLastRow() + 1;
    const row = _bucolicheEventoRegistroRow_(tipo, origine, messaggio, contesto);

    sheet.appendRow(row);
    sheet.getRange(ultimaRiga, 1, 1, BUCOLICHE_NUM_COLS).setBackground(sfondo || '#FCE4D6');

    Logger.log(`[Bucoliche] ${tipo} registrato: ${_bucolicheStringOrEmpty_(messaggio)}`);

  } catch (err) {
    Logger.log(`[Bucoliche] ERRORE CRITICO — impossibile scrivere su Bucoliche: ${err.message}`);
  }
}

function _bucolicheEventoRegistroRow_(tipo, origine, messaggio, contesto) {
  const ctx = contesto || {};
  const livello = tipo === 'conflitto' ? 'CONFLITTO' : 'ERRORE';
  return [
    _timestampLocale(),                                        //  1
    `${livello} — ${_bucolicheStringOrEmpty_(origine) || 'sconosciuto'}`, //  2
    _bucolicheStringOrEmpty_(ctx.cliente),                     //  3
    _bucolicheStringOrEmpty_(ctx.sito),                        //  4
    _bucolicheStringOrEmpty_(ctx.pratica),                     //  5
    _bucolicheStringOrEmpty_(ctx.anno),                        //  6
    '',                                                        //  7
    _bucolicheEventoRegistroNota_(tipo, origine, messaggio, ctx), //  8
    _bucolicheStringOrEmpty_(ctx.urlCartella),                 //  9
    _bucolicheStringOrEmpty_(ctx.idDrive),                     // 10
    '', '', '', '', '',                                         // 11-15
    'errore',                                                  // 16
    '',                                                        // 17
  ];
}

function _bucolicheEventoRegistroNota_(tipo, origine, messaggio, contesto) {
  const parts = [];
  const testo = _bucolicheStringOrEmpty_(messaggio);
  if (testo) parts.push(testo);
  parts.push(`fase=${_bucolicheStringOrEmpty_(tipo) || 'errore'}`);
  parts.push(`origine=${_bucolicheStringOrEmpty_(origine) || 'sconosciuto'}`);
  const correlazioni = _bucolicheEventoRegistroCorrelazioni_(contesto);
  if (correlazioni) parts.push(`correlazioni=${correlazioni}`);
  return parts.join('; ');
}

function _bucolicheEventoRegistroCorrelazioni_(contesto) {
  const ctx = contesto && typeof contesto === 'object' ? contesto : {};
  const keys = [
    'cliente', 'sito', 'pratica', 'anno', 'urlCartella', 'idDrive',
    'inbox_id', 'account_alias', 'source_email', 'source_message_id',
    'source_message_uid', 'attachment_id', 'fingerprint', 'sha256',
    'original_filename', 'staged_filename', 'drive_file_id', 'manifest_file_id',
  ];
  const parts = [];
  for (const key of keys) {
    const value = _bucolicheStringOrEmpty_(ctx[key]);
    if (value) parts.push(`${key}=${value}`);
  }
  return parts.join('|');
}

function _bucolicheStringOrEmpty_(value) {
  return value === null || value === undefined ? '' : String(value).trim();
}


// ── FUNZIONI PRIVATE ──────────────────────────────────────────────────────────

/**
 * Apre (o crea) il tab eventi nel file Bucoliche.
 * Usa CONFIG.BUCOLICHE_EVENTS_SHEET per trovare il tab per nome,
 * più robusto di getActiveSheet() quando ci sono più tab.
 *
 * @returns {GoogleAppsScript.Spreadsheet.Sheet}
 */
function _aprifoglioBucoliche() {
  try {
    const ss = SpreadsheetApp.openById(CONFIG.BUCOLICHE_ID);
    let sheet = ss.getSheetByName(CONFIG.BUCOLICHE_EVENTS_SHEET);
    if (!sheet) {
      sheet = ss.insertSheet(CONFIG.BUCOLICHE_EVENTS_SHEET);
      Logger.log(`[Bucoliche] Tab "${CONFIG.BUCOLICHE_EVENTS_SHEET}" creato automaticamente.`);
    }
    return sheet;
  } catch (err) {
    throw new Error(`[Bucoliche] Impossibile aprire le Bucoliche (ID: ${CONFIG.BUCOLICHE_ID}): ${err.message}`);
  }
}


/**
 * Aggiunge la riga di intestazione se il foglio è vuoto.
 * Formatta con sfondo scuro, testo bianco, grassetto, riga bloccata.
 *
 * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet
 */
function _assicuraIntestazione(sheet) {
  if (sheet.getLastRow() > 0) return;

  const intestazioni = [
    'timestamp',              //  1
    'origine',                //  2
    'cliente',                //  3
    'sito',                   //  4
    'pratica',                //  5
    'anno',                   //  6
    'tecnici',                //  7
    'note',                   //  8
    'url_cartella',           //  9
    'id_drive',               // 10
    'mittente_dominio',       // 11  ← ML features
    'oggetto_email',          // 12
    'nome_file',              // 13
    'estensione',             // 14
    'dimensione_kb',          // 15
    'stato',                  // 16
    'timestamp_archiviazione',// 17
  ];

  sheet.appendRow(intestazioni);

  const rangeInt = sheet.getRange(1, 1, 1, intestazioni.length);
  rangeInt
    .setFontWeight('bold')
    .setBackground('#1F4E79')
    .setFontColor('#FFFFFF');

  sheet.setFrozenRows(1);

  // Larghezze colonne ottimizzate
  sheet.setColumnWidth(1,  165);  // timestamp
  sheet.setColumnWidth(2,  150);  // origine
  sheet.setColumnWidth(3,  180);  // cliente
  sheet.setColumnWidth(4,  150);  // sito
  sheet.setColumnWidth(5,  100);  // pratica
  sheet.setColumnWidth(6,   55);  // anno
  sheet.setColumnWidth(7,  160);  // tecnici
  sheet.setColumnWidth(8,  220);  // note
  sheet.setColumnWidth(9,  260);  // url_cartella
  sheet.setColumnWidth(10, 160);  // id_drive
  sheet.setColumnWidth(11, 140);  // mittente_dominio
  sheet.setColumnWidth(12, 220);  // oggetto_email
  sheet.setColumnWidth(13, 200);  // nome_file
  sheet.setColumnWidth(14,  80);  // estensione
  sheet.setColumnWidth(15,  90);  // dimensione_kb
  sheet.setColumnWidth(16, 100);  // stato
  sheet.setColumnWidth(17, 165);  // timestamp_archiviazione

  Logger.log('[Bucoliche] Intestazione creata — schema v1.1 (17 colonne).');
}


/**
 * Restituisce un timestamp formattato nel fuso orario italiano.
 * Formato: "yyyy-MM-dd HH:mm:ss" — leggibile e ordinabile.
 *
 * @returns {string}
 */
function _timestampLocale() {
  return Utilities.formatDate(new Date(), 'Europe/Rome', 'yyyy-MM-dd HH:mm:ss');
}
