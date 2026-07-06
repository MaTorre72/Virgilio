/**
 * ============================================================
 *  ANAGRAFICA — Dati di riferimento Progetto Virgilio v1.0
 * ============================================================
 *  Gestisce tre tab di anagrafica all'interno del file Bucoliche:
 *
 *    Clienti_Siti  — coppie cliente/sito registrate
 *    Team          — tecnici Sigma+
 *    TipiPratica   — vocabolario pratiche con descrizioni
 *
 *  Questi tab sono la fonte di verità per i dropdown del form
 *  Virgilio e per i futuri moduli AI di classificazione.
 *
 *  In v1.1 sarà aggiunto uno script di sincronizzazione con VTEnext.
 *
 *  Dipendenze: CONFIG (definito in caronte.gs), _timestampLocale() (bucoliche.gs)
 * ============================================================
 */


// ── COSTANTI ──────────────────────────────────────────────────────────────────

const ANAGRAFICA_TABS = {
  CLIENTI_SITI: 'Clienti_Siti',
  TEAM:         'Team',
  TIPI_PRATICA: 'TipiPratica',
};

// Dati default Team — verificare e correggere le email dopo inizializzazione
const _TEAM_DEFAULT = [
  { nome: 'Tecnico 1',     email: 'account.1@example.invalid',     ruolo: 'Tecnico' },
  { nome: 'Tecnico 2',    email: 'account.2@example.invalid',    ruolo: 'Tecnico' },
  { nome: 'Tecnico 3', email: 'account.3@example.invalid', ruolo: 'Tecnico' },
  { nome: 'Tecnico 4',      email: 'account.4@example.invalid',      ruolo: 'Tecnico' },
  { nome: 'Tecnico 5',      email: 'account.5@example.invalid',      ruolo: 'Tecnico' },
];

// Vocabolario pratiche — specchio di CONFIG.TIPI_PRATICA con descrizioni
const _TIPI_PRATICA_DEFAULT = [
  { codice: 'AUA',           descrizione: 'Autorizzazione Unica Ambientale'    },
  { codice: 'AIA',           descrizione: 'Autorizzazione Integrata Ambientale' },
  { codice: 'VIA',           descrizione: 'Valutazione di Impatto Ambientale'  },
  { codice: 'EoW',           descrizione: 'End of Waste'                       },
  { codice: 'TR',            descrizione: 'Terre e Rocce da Scavo'             },
  { codice: 'bonifica',      descrizione: 'Bonifica siti contaminati'          },
  { codice: 'emissioni',     descrizione: 'Emissioni in atmosfera'             },
  { codice: 'rifiuti',       descrizione: 'Gestione rifiuti'                   },
  { codice: 'sottoprodotti', descrizione: 'Sottoprodotti D.Lgs 152'            },
  { codice: 'PEI',           descrizione: 'Piano Emergenza Interno'            },
  { codice: 'PEE',           descrizione: 'Piano Emergenza Esterno'            },
  { codice: 'reportAIA',     descrizione: 'Report annuale AIA'                 },
  { codice: 'assistenza',    descrizione: 'Assistenza tecnica'                 },
];


// ── API PUBBLICA ──────────────────────────────────────────────────────────────

/**
 * Restituisce l'anagrafica completa al form Virgilio.
 * Chiamata da virgilio.html tramite google.script.run.getAnagraficaVirgilio().
 *
 * In caso di errore su un singolo tab restituisce array vuoto per quel campo
 * senza bloccare il form (usa i fallback hardcoded in virgilio.html).
 *
 * @returns {{
 *   clienti:     string[],
 *   siti:        Object.<string, string[]>,
 *   team:        Array<{nome:string, email:string, ruolo:string}>,
 *   tipiPratica: Array<{codice:string, descrizione:string}>
 * }}
 */
function getAnagraficaVirgilio() {
  const ss = SpreadsheetApp.openById(CONFIG.BUCOLICHE_ID);

  return {
    clienti:     _leggiClienti(ss),
    siti:        _leggiSiti(ss),
    team:        _leggiTeam(ss),
    tipiPratica: _leggiTipiPratica(ss),
  };
}


/**
 * Aggiunge un nuovo cliente-sito al tab Clienti_Siti se non già presente.
 * Chiamata da virgilio.html dopo apertura pratica con cliente nuovo.
 * Operazione idempotente: non duplica se la coppia esiste già.
 *
 * @param {string} cliente
 * @param {string} sito
 */
function aggiungiClienteSito(cliente, sito) {
  try {
    if (!cliente || !sito) return;

    const ss    = SpreadsheetApp.openById(CONFIG.BUCOLICHE_ID);
    const sheet = _getFoglioAnagrafica(ss, ANAGRAFICA_TABS.CLIENTI_SITI);
    const dati  = sheet.getDataRange().getValues();

    // Controlla se la coppia esiste già (case-insensitive)
    for (let r = 1; r < dati.length; r++) {
      if (
        dati[r][0].toString().trim().toLowerCase() === cliente.trim().toLowerCase() &&
        dati[r][1].toString().trim().toLowerCase() === sito.trim().toLowerCase()
      ) {
        Logger.log(`[Anagrafica] Coppia già presente: "${cliente}" / "${sito}"`);
        return;
      }
    }

    sheet.appendRow([cliente.trim(), sito.trim(), true, _timestampLocale()]);
    Logger.log(`[Anagrafica] Aggiunto: "${cliente}" / "${sito}"`);

  } catch (err) {
    Logger.log(`[Anagrafica] ERRORE aggiungiClienteSito: ${err.message}`);
  }
}


/**
 * Crea i tre tab di anagrafica nel file Bucoliche se non esistono.
 * Popola Team e TipiPratica con i dati default.
 * Clienti_Siti parte vuoto: compilare manualmente o tramite il form Virgilio.
 *
 * Idempotente: non sovrascrive tab già esistenti con dati.
 * Eseguire da setup.gs → caronteSetupAnagrafica() una volta sola.
 */
function inizializzaAnagrafica() {
  const ss = SpreadsheetApp.openById(CONFIG.BUCOLICHE_ID);

  _assicuraTabClientiSiti(ss);
  _assicuraTabTeam(ss);
  _assicuraTabTipiPratica(ss);

  Logger.log('[Anagrafica] Tab verificati/creati in Bucoliche:');
  Logger.log(`  → ${ANAGRAFICA_TABS.CLIENTI_SITI} (compilare con i clienti reali)`);
  Logger.log(`  → ${ANAGRAFICA_TABS.TEAM} (verificare le email)`);
  Logger.log(`  → ${ANAGRAFICA_TABS.TIPI_PRATICA} (vocabolario completo)`);
}


// ── LETTURA DATI ──────────────────────────────────────────────────────────────

function _leggiClienti(ss) {
  try {
    const sheet = _getFoglioAnagrafica(ss, ANAGRAFICA_TABS.CLIENTI_SITI);
    const dati  = sheet.getDataRange().getValues();
    const clienti = new Set();

    for (let r = 1; r < dati.length; r++) {
      // Colonna 3 (indice 2) = attivo — includi se != false e non vuoto
      if (dati[r][0] && dati[r][2] !== false) {
        clienti.add(dati[r][0].toString().trim());
      }
    }

    return [...clienti].sort();
  } catch (err) {
    Logger.log(`[Anagrafica] AVVISO _leggiClienti: ${err.message}`);
    return [];
  }
}


function _leggiSiti(ss) {
  try {
    const sheet = _getFoglioAnagrafica(ss, ANAGRAFICA_TABS.CLIENTI_SITI);
    const dati  = sheet.getDataRange().getValues();
    const sitiPerCliente = {};

    for (let r = 1; r < dati.length; r++) {
      if (!dati[r][0] || dati[r][2] === false) continue;

      const cliente = dati[r][0].toString().trim();
      const sito    = dati[r][1].toString().trim();

      if (!sitiPerCliente[cliente]) sitiPerCliente[cliente] = [];
      if (sito && !sitiPerCliente[cliente].includes(sito)) {
        sitiPerCliente[cliente].push(sito);
      }
    }

    return sitiPerCliente;
  } catch (err) {
    Logger.log(`[Anagrafica] AVVISO _leggiSiti: ${err.message}`);
    return {};
  }
}


function _leggiTeam(ss) {
  try {
    const sheet = _getFoglioAnagrafica(ss, ANAGRAFICA_TABS.TEAM);
    const dati  = sheet.getDataRange().getValues();
    const team  = [];

    for (let r = 1; r < dati.length; r++) {
      if (!dati[r][0] || dati[r][3] === false) continue;
      team.push({
        nome:  dati[r][0].toString().trim(),
        email: dati[r][1].toString().trim(),
        ruolo: dati[r][2].toString().trim(),
      });
    }

    return team;
  } catch (err) {
    Logger.log(`[Anagrafica] AVVISO _leggiTeam: ${err.message}`);
    return [];
  }
}


function _leggiTipiPratica(ss) {
  try {
    const sheet = _getFoglioAnagrafica(ss, ANAGRAFICA_TABS.TIPI_PRATICA);
    const dati  = sheet.getDataRange().getValues();
    const tipi  = [];

    for (let r = 1; r < dati.length; r++) {
      if (!dati[r][0] || dati[r][2] === false) continue;
      tipi.push({
        codice:      dati[r][0].toString().trim(),
        descrizione: dati[r][1].toString().trim(),
      });
    }

    return tipi;
  } catch (err) {
    Logger.log(`[Anagrafica] AVVISO _leggiTipiPratica: ${err.message}`);
    return [];
  }
}


// ── SETUP TAB ─────────────────────────────────────────────────────────────────

function _getFoglioAnagrafica(ss, nomeTab) {
  const sheet = ss.getSheetByName(nomeTab);
  if (!sheet) throw new Error(`Tab "${nomeTab}" non trovato in Bucoliche — eseguire caronteSetupAnagrafica()`);
  return sheet;
}


function _assicuraTabClientiSiti(ss) {
  let sheet = ss.getSheetByName(ANAGRAFICA_TABS.CLIENTI_SITI);
  if (!sheet) sheet = ss.insertSheet(ANAGRAFICA_TABS.CLIENTI_SITI);

  if (sheet.getLastRow() === 0) {
    const header = ['cliente', 'sito', 'attivo', 'data_inserimento'];
    sheet.appendRow(header);
    _formattaIntestazioneAnagrafica(sheet, header.length);
    sheet.setColumnWidth(1, 200);
    sheet.setColumnWidth(2, 200);
    sheet.setColumnWidth(3,  80);
    sheet.setColumnWidth(4, 170);
    Logger.log(`[Anagrafica] Tab ${ANAGRAFICA_TABS.CLIENTI_SITI} creato — compilare con i clienti reali.`);
  }
}


function _assicuraTabTeam(ss) {
  let sheet = ss.getSheetByName(ANAGRAFICA_TABS.TEAM);
  if (!sheet) sheet = ss.insertSheet(ANAGRAFICA_TABS.TEAM);

  if (sheet.getLastRow() === 0) {
    const header = ['nome', 'email', 'ruolo', 'attivo'];
    sheet.appendRow(header);
    _formattaIntestazioneAnagrafica(sheet, header.length);
    sheet.setColumnWidth(1, 160);
    sheet.setColumnWidth(2, 220);
    sheet.setColumnWidth(3, 140);
    sheet.setColumnWidth(4,  80);

    _TEAM_DEFAULT.forEach(m => {
      sheet.appendRow([m.nome, m.email, m.ruolo, true]);
    });

    Logger.log(`[Anagrafica] Tab ${ANAGRAFICA_TABS.TEAM} creato con dati default — verificare le email.`);
  }
}


function _assicuraTabTipiPratica(ss) {
  let sheet = ss.getSheetByName(ANAGRAFICA_TABS.TIPI_PRATICA);
  if (!sheet) sheet = ss.insertSheet(ANAGRAFICA_TABS.TIPI_PRATICA);

  if (sheet.getLastRow() === 0) {
    const header = ['codice', 'descrizione', 'attivo'];
    sheet.appendRow(header);
    _formattaIntestazioneAnagrafica(sheet, header.length);
    sheet.setColumnWidth(1, 130);
    sheet.setColumnWidth(2, 300);
    sheet.setColumnWidth(3,  80);

    _TIPI_PRATICA_DEFAULT.forEach(t => {
      sheet.appendRow([t.codice, t.descrizione, true]);
    });

    Logger.log(`[Anagrafica] Tab ${ANAGRAFICA_TABS.TIPI_PRATICA} creato con vocabolario completo.`);
  }
}


function _formattaIntestazioneAnagrafica(sheet, numColonne) {
  sheet.getRange(1, 1, 1, numColonne)
    .setFontWeight('bold')
    .setBackground('#1F4E79')
    .setFontColor('#FFFFFF');
  sheet.setFrozenRows(1);
}

