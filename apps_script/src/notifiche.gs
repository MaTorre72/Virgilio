/**
 * ============================================================
 *  NOTIFICHE — Avvisi team Progetto Virgilio v1.0
 *  Variante Telegram HTML
 * ============================================================
 *  Gestisce l'invio di notifiche al team su due canali:
 *  — Google Chat tramite webhook
 *  — Telegram tramite Bot API con parse_mode HTML
 *
 *  Scelta tecnica:
 *  - Google Chat riceve un messaggio con formattazione Markdown leggera.
 *  - Telegram riceve un messaggio HTML dedicato, con escape dei campi dinamici.
 *
 *  Motivo:
 *  Telegram è rigido nella gestione di Markdown e HTML. I valori dinamici
 *  come "2026_assistenza", "_TEST_CLIENTE_" o note con caratteri speciali
 *  possono rompere il parsing se non vengono trattati correttamente.
 *
 *  Se un canale fallisce, l'altro continua indisturbato.
 *  Nessuna notifica mancata blocca l'operazione principale.
 *
 *  Dipendenze: CONFIG (definito in caronte.gs)
 * ============================================================
 */


/**
 * Avvisa il team su tutti i canali configurati.
 * Orchestratore principale — chiamato da doPost() dopo la creazione cartella.
 *
 * @param {string}   cliente      - Ragione sociale cliente
 * @param {string}   sito         - Sito/stabilimento
 * @param {string}   pratica      - Tipo pratica (es. 'AUA')
 * @param {string}   anno         - Anno apertura pratica
 * @param {string[]} tecnici      - Array di nomi tecnici (può essere vuoto)
 * @param {string}   note         - Note per il team (può essere vuoto)
 * @param {string}   urlCartella  - URL della cartella Drive appena creata
 */
function avvisaTeam(cliente, sito, pratica, anno, tecnici, note, urlCartella) {
  // PATCH:
  // Non usiamo più un unico messaggio per entrambi i canali.
  // Google Chat e Telegram hanno regole diverse di formattazione.
  const messaggioChat = _costruisciMessaggioChat(
    cliente,
    sito,
    pratica,
    anno,
    tecnici,
    note,
    urlCartella
  );

  const messaggioTelegram = _costruisciMessaggioTelegramHtml(
    cliente,
    sito,
    pratica,
    anno,
    tecnici,
    note,
    urlCartella
  );

  // Invia su Google Chat — errore non bloccante.
  try {
    avvisaChat(messaggioChat);
  } catch (err) {
    Logger.log(`[Notifiche] ERRORE Google Chat: ${err.message}`);
  }

  // Invia su Telegram — errore non bloccante.
  try {
    avvisaTelegram(messaggioTelegram);
  } catch (err) {
    Logger.log(`[Notifiche] ERRORE Telegram: ${err.message}`);
  }
}

/**
 * Avvisa il team dell'esito finale di un record Virgilio_Inbox archiviato.
 *
 * @param {Object} esito
 */
function avvisaArchiviazioneVirgilioInbox(esito) {
  const payload = esito && typeof esito === 'object' && !Array.isArray(esito)
    ? esito
    : {};
  const messaggioChat = _costruisciMessaggioArchiviazioneInboxChat(payload);
  const messaggioTelegram = _costruisciMessaggioArchiviazioneInboxTelegram(payload);

  try {
    avvisaChat(messaggioChat);
  } catch (err) {
    Logger.log(`[Notifiche] ERRORE Google Chat: ${err.message}`);
  }

  try {
    avvisaTelegram(messaggioTelegram);
  } catch (err) {
    Logger.log(`[Notifiche] ERRORE Telegram: ${err.message}`);
  }
}


/**
 * Invia un messaggio al webhook Google Chat dello spazio team Sigma+.
 *
 * @param {string} messaggio - Testo del messaggio per Google Chat.
 */
function avvisaChat(messaggio) {
  if (!CONFIG.WEBHOOK_CHAT) {
    Logger.log('[Notifiche] WEBHOOK_CHAT non configurato — Chat saltata.');
    return;
  }

  const payload = JSON.stringify({ text: messaggio });

  const risposta = UrlFetchApp.fetch(CONFIG.WEBHOOK_CHAT, {
    method: 'post',
    contentType: 'application/json',
    payload: payload,
    muteHttpExceptions: true,
  });

  const codice = risposta.getResponseCode();

  if (codice !== 200) {
    throw new Error(`Chat ha risposto HTTP ${codice}: ${risposta.getContentText()}`);
  }

  Logger.log(`[Notifiche] Google Chat: messaggio inviato (HTTP ${codice})`);
}


/**
 * Invia un messaggio al gruppo Telegram Sigma+ via Bot API.
 *
 * @param {string} messaggioHtml - Testo del messaggio in HTML Telegram sicuro.
 */
function avvisaTelegram(messaggioHtml) {
  if (!CONFIG.TELEGRAM_TOKEN || !CONFIG.TELEGRAM_CHAT_ID) {
    Logger.log('[Notifiche] TELEGRAM_TOKEN o TELEGRAM_CHAT_ID non configurati — Telegram saltato.');
    return;
  }

  const url = `https://api.telegram.org/bot${CONFIG.TELEGRAM_TOKEN}/sendMessage`;

  const payload = JSON.stringify({
    chat_id: CONFIG.TELEGRAM_CHAT_ID,
    text: messaggioHtml,
    parse_mode: 'HTML',

    // PATCH:
    // Disattiva l'anteprima automatica del link Drive.
    // La notifica resta più compatta dentro Telegram.
    disable_web_page_preview: true,
  });

  const risposta = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    payload: payload,
    muteHttpExceptions: true,
  });

  const codice = risposta.getResponseCode();
  const body = JSON.parse(risposta.getContentText());

  if (!body.ok) {
    throw new Error(`Telegram ha risposto HTTP ${codice}: ${JSON.stringify(body)}`);
  }

  Logger.log(`[Notifiche] Telegram: messaggio inviato (HTTP ${codice})`);
}


// ── FUNZIONI PRIVATE ──────────────────────────────────────────────────────────

/**
 * Costruisce il testo per Google Chat.
 * Può usare Markdown leggero perché Google Chat lo gestisce diversamente
 * da Telegram e non ha generato l'errore osservato nei test.
 *
 * @returns {string} Messaggio per Google Chat.
 */
function _costruisciMessaggioChat(cliente, sito, pratica, anno, tecnici, note, urlCartella) {
  const nomePratica = `${anno}_${pratica}`;
  const tecniciStr = (Array.isArray(tecnici) && tecnici.length)
    ? tecnici.join(', ')
    : 'nessuno assegnato';

  let msg =
    `📁 *Nuova pratica aperta*\n` +
    `Cliente: ${cliente} — Sito: ${sito}\n` +
    `Pratica: ${nomePratica}\n` +
    `Tecnici: ${tecniciStr}\n`;

  if (note && note.toString().trim()) {
    msg += `Note: ${note.toString().trim()}\n`;
  }

  msg += `🔗 Cartella Drive: ${urlCartella}`;
  // Link Virgilio rimosso: la pratica è già stata aperta, non serve qui.

  return msg;
}


/**
 * Costruisce il testo per Telegram in HTML.
 * Tutti i campi dinamici passano da _escapeTelegramHtml().
 *
 * Questo evita errori con:
 * - underscore: 2026_assistenza, _TEST_CLIENTE_
 * - asterischi
 * - parentesi
 * - simboli < > &
 * - note libere scritte dall'utente
 *
 * @returns {string} Messaggio HTML per Telegram.
 */
function _costruisciMessaggioTelegramHtml(cliente, sito, pratica, anno, tecnici, note, urlCartella) {
  const nomePratica = `${anno}_${pratica}`;
  const tecniciStr = (Array.isArray(tecnici) && tecnici.length)
    ? tecnici.join(', ')
    : 'nessuno assegnato';

  let msg =
    `📁 <b>Nuova pratica aperta</b>\n` +
    `Cliente: ${_escapeTelegramHtml(cliente)}\n` +
    `Sito: ${_escapeTelegramHtml(sito)}\n` +
    `Pratica: ${_escapeTelegramHtml(nomePratica)}\n` +
    `Tecnici: ${_escapeTelegramHtml(tecniciStr)}\n`;

  if (note && note.toString().trim()) {
    msg += `Note: ${_escapeTelegramHtml(note.toString().trim())}\n`;
  }

  // FIX: link cliccabile invece di URL crudo.
  // FIX: link Virgilio rimosso — la pratica è già stata aperta.
  msg += `<a href="${_escapeTelegramHtml(urlCartella)}">📁 Apri la cartella Drive</a>`;

  return msg;
}

function _costruisciMessaggioArchiviazioneInboxChat(esito) {
  const nomePratica = `${esito.anno}_${esito.pratica}`;
  const tecniciStr = _notificheTecniciToString_(esito.tecnici);
  let msg =
    `📁 *Pratica aperta e documento archiviato*\n` +
    `Cliente: ${esito.cliente} — Sito: ${esito.sito}\n` +
    `Pratica: ${nomePratica}\n` +
    `Documento: ${esito.fileName || 'documento staged'}\n` +
    `Tecnici: ${tecniciStr}\n`;

  if (esito.inboxId) {
    msg += `Inbox: ${esito.inboxId}\n`;
  }
  if (esito.note && esito.note.toString().trim()) {
    msg += `Note: ${esito.note.toString().trim()}\n`;
  }
  if (_virgilioInboxStringOrEmptyForNotifications_(esito.inboxStatus)) {
    msg += `Stato finale: ${esito.inboxStatus}\n`;
  }

  msg += `📂 Cartella pratica: ${esito.urlCartella}`;
  if (esito.urlCorrispondenza && esito.urlCorrispondenza !== esito.urlCartella) {
    msg += `\n📎 Corrispondenza: ${esito.urlCorrispondenza}`;
  }
  return msg;
}

function _costruisciMessaggioArchiviazioneInboxTelegram(esito) {
  const nomePratica = `${esito.anno}_${esito.pratica}`;
  const tecniciStr = _notificheTecniciToString_(esito.tecnici);
  let msg =
    `📁 <b>Pratica aperta e documento archiviato</b>\n` +
    `Cliente: ${_escapeTelegramHtml(esito.cliente)}\n` +
    `Sito: ${_escapeTelegramHtml(esito.sito)}\n` +
    `Pratica: ${_escapeTelegramHtml(nomePratica)}\n` +
    `Documento: ${_escapeTelegramHtml(esito.fileName || 'documento staged')}\n` +
    `Tecnici: ${_escapeTelegramHtml(tecniciStr)}\n`;

  if (_virgilioInboxStringOrEmptyForNotifications_(esito.inboxId)) {
    msg += `Inbox: ${_escapeTelegramHtml(esito.inboxId)}\n`;
  }
  if (_virgilioInboxStringOrEmptyForNotifications_(esito.note)) {
    msg += `Note: ${_escapeTelegramHtml(esito.note.toString().trim())}\n`;
  }
  if (_virgilioInboxStringOrEmptyForNotifications_(esito.inboxStatus)) {
    msg += `Stato finale: ${_escapeTelegramHtml(esito.inboxStatus)}\n`;
  }

  msg += `<a href="${_escapeTelegramHtml(esito.urlCartella || '')}">📂 Apri la cartella pratica</a>`;
  if (esito.urlCorrispondenza && esito.urlCorrispondenza !== esito.urlCartella) {
    msg += `\n<a href="${_escapeTelegramHtml(esito.urlCorrispondenza)}">📎 Apri 02_corrispondenza</a>`;
  }
  return msg;
}


/**
 * Escape minimo per testo inserito in messaggi HTML Telegram.
 *
 * Telegram accetta solo alcuni tag HTML. Tutto ciò che arriva dai dati
 * dinamici deve essere trattato come testo puro, non come markup.
 *
 * @param {*} value - Valore da rendere sicuro per HTML Telegram.
 * @returns {string}
 */
/**
 * Restituisce l'URL pubblico del form Virgilio da CONFIG.
 * Ritorna null se non è ancora configurato (placeholder non sostituito).
 *
 * @returns {string|null}
 */
function _getUrlForm() {
  const url = typeof CONFIG !== 'undefined' && CONFIG.URL_FORM;
  if (!url || url === '[DA_INSERIRE_URL_FORM]') return null;
  return url;
}


function _escapeTelegramHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function _notificheTecniciToString_(tecnici) {
  return (Array.isArray(tecnici) && tecnici.length)
    ? tecnici.join(', ')
    : 'nessuno assegnato';
}

function _virgilioInboxStringOrEmptyForNotifications_(value) {
  return String(value || '').trim();
}

/**
 * Invia un messaggio semplice al team su tutti i canali.
 * Usato per notifiche di servizio generiche dove non serve il formato completo.
 *
 * @param {string} messaggio - Testo già formattato da inviare
 */
function avvisaTeamSemplice(messaggio) {
  try { avvisaChat(messaggio); }
  catch (err) { Logger.log(`[Notifiche] Chat fallita: ${err.message}`); }

  try {avvisaTelegram(_escapeTelegramHtml(messaggio));}
  catch (err) { Logger.log(`[Notifiche] Telegram fallito: ${err.message}`); }
}


/**
 * Notifica traghettamento con messaggi distinti per Chat e Telegram.
 * Sostituisce la chiamata a avvisaTeamSemplice() in _avvisaTraghettamento():
 * Chat usa Markdown + URL raw (auto-linkato), Telegram usa HTML con <a href>.
 *
 * @param {number}   totale      - Numero allegati traghettati
 * @param {Array}    dettagliMail - Array di {mittente, oggetto, nomiFile[]}
 */
function avvisaTraghettamentoTeam(totale, dettagliMail) {
  const msgChat     = _costruisciTraghettamentoChat(totale, dettagliMail);
  const msgTelegram = _costruisciTraghettamentoTelegram(totale, dettagliMail);

  try { avvisaChat(msgChat); }
  catch (err) { Logger.log(`[Notifiche] Chat fallita: ${err.message}`); }

  try { avvisaTelegram(msgTelegram); }
  catch (err) { Logger.log(`[Notifiche] Telegram fallito: ${err.message}`); }
}


/**
 * Costruisce il messaggio traghettamento per Google Chat.
 * Usa Markdown leggero e URL raw (auto-linkato da Chat).
 *
 * @returns {string}
 */
function _costruisciTraghettamentoChat(totale, dettagliMail) {
  const limboUrl = `https://drive.google.com/drive/folders/${CONFIG.LIMBO_ID}`;

  let msg =
    `⚓ *Caronte ha traghettato*\n` +
    `${totale} allegato/i depositati nel Limbo.\n`;

  if (dettagliMail && dettagliMail.length > 0) {
    dettagliMail.forEach(d => {
      msg += `\n📧 Da: ${d.mittente}\n   Oggetto: ${d.oggetto}\n   File: ${d.nomiFile.join(', ')}`;
    });
  }

  msg += `\n\n📂 Limbo: ${limboUrl}`;

  const urlForm = _getUrlForm();
  if (urlForm) msg += `\n🗂 Apri Virgilio: ${urlForm}`;

  return msg;
}


/**
 * Costruisce il messaggio traghettamento per Telegram in HTML.
 * Usa <b> per grassetto e <a href> per link cliccabili.
 * Tutti i campi dinamici sono escapati con _escapeTelegramHtml().
 *
 * @returns {string}
 */
function _costruisciTraghettamentoTelegram(totale, dettagliMail) {
  const limboUrl = `https://drive.google.com/drive/folders/${CONFIG.LIMBO_ID}`;

  let msg =
    `⚓ <b>Caronte ha traghettato</b>\n` +
    `${totale} allegato/i depositati nel Limbo.\n`;

  if (dettagliMail && dettagliMail.length > 0) {
    dettagliMail.forEach(d => {
      const nomiEscapati = d.nomiFile.map(n => _escapeTelegramHtml(n)).join(', ');
      msg +=
        `\n📧 Da: ${_escapeTelegramHtml(d.mittente)}` +
        `\n   Oggetto: ${_escapeTelegramHtml(d.oggetto)}` +
        `\n   File: ${nomiEscapati}`;
    });
  }
 
  msg += `\n\n<a href="${limboUrl}">📂 Apri il Limbo</a>`;

  const urlForm = _getUrlForm();
  if (urlForm) msg += `\n<a href="${_escapeTelegramHtml(urlForm)}">🗂 Apri Virgilio</a>`;

  return msg;
}

function testNotificheArchiviazioneInbox() {
  const payload = {
    cliente: 'Cliente Demo',
    sito: 'Sito Demo',
    pratica: 'AIA',
    anno: '2026',
    tecnici: ['Tecnico 1', 'Tecnico 2'],
    note: 'nota <urgente>',
    urlCartella: 'https://drive.google.com/drive/folders/folder-pratica',
    urlCorrispondenza: 'https://drive.google.com/drive/folders/folder-corrispondenza',
    inboxId: 'inbox-1',
    fileName: 'analisi.pdf',
    inboxStatus: 'archiviato',
  };
  const chat = _costruisciMessaggioArchiviazioneInboxChat(payload);
  const telegram = _costruisciMessaggioArchiviazioneInboxTelegram(payload);
  if (chat.indexOf('Documento: analisi.pdf') < 0) {
    throw new Error('Messaggio Chat archiviazione inbox incompleto.');
  }
  if (chat.indexOf('Stato finale: archiviato') < 0) {
    throw new Error('Messaggio Chat archiviazione inbox senza stato finale.');
  }
  if (telegram.indexOf('Inbox: inbox-1') < 0 || telegram.indexOf('&lt;urgente&gt;') < 0) {
    throw new Error('Messaggio Telegram archiviazione inbox non escapato correttamente.');
  }
  if (telegram.indexOf('Stato finale: archiviato') < 0) {
    throw new Error('Messaggio Telegram archiviazione inbox senza stato finale.');
  }
  Logger.log('testNotificheArchiviazioneInbox: OK');
}
