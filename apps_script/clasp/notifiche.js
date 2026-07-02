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
 * Invia la notifica pilota P2 per un allegato gia registrato in Bucoliche.
 * Restituisce l'esito per consentire idempotenza e verifiche locali.
 *
 * @param {Object} options
 * @param {Object=} deps
 * @returns {{ok: boolean, channels: string[], errors: Object[]}}
 */
function avvisaRegistrazionePilotaTeam(options, deps) {
  const details = options || {};
  const injected = deps || {};
  const channels = [];
  const errors = [];
  const chatMessage = _costruisciNotificaPilotaChat_(details);
  const telegramMessage = _costruisciNotificaPilotaTelegram_(details);
  const chatConfigured = Object.prototype.hasOwnProperty.call(injected, 'chatConfigured')
    ? injected.chatConfigured
    : Boolean(CONFIG.WEBHOOK_CHAT);
  const telegramConfigured = Object.prototype.hasOwnProperty.call(injected, 'telegramConfigured')
    ? injected.telegramConfigured
    : Boolean(CONFIG.TELEGRAM_TOKEN && CONFIG.TELEGRAM_CHAT_ID);
  const sendChat = injected.sendChat || avvisaChat;
  const sendTelegram = injected.sendTelegram || avvisaTelegram;

  if (chatConfigured) {
    try {
      sendChat(chatMessage);
      channels.push('chat');
    } catch (err) {
      errors.push(_driveStagingError_('CHAT_NOTIFICATION_FAILED', String(err.message || err)));
    }
  }

  if (telegramConfigured) {
    try {
      sendTelegram(telegramMessage);
      channels.push('telegram');
    } catch (err) {
      errors.push(_driveStagingError_('TELEGRAM_NOTIFICATION_FAILED', String(err.message || err)));
    }
  }

  if (channels.length === 0 && errors.length === 0) {
    errors.push(_driveStagingError_('NOTIFICATION_CHANNELS_NOT_CONFIGURED',
      'Configurare almeno un canale Chat o Telegram per il pilota.'));
  }

  return { ok: channels.length > 0 && errors.length === 0, channels: channels, errors: errors };
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

function _costruisciNotificaPilotaChat_(details) {
  const link = details.driveUrl ? `\n📎 Drive: ${details.driveUrl}` : '';
  return `📌 *Virgilio staging pilota registrato*\n` +
    `Attachment: ${details.attachmentId || ''}\n` +
    `File: ${details.stagedFilename || ''}\n` +
    `Account: ${details.accountAlias || ''}\n` +
    `Stato: ${details.state || ''}${link}`;
}

function _costruisciNotificaPilotaTelegram_(details) {
  const link = details.driveUrl
    ? `\n<a href="${_escapeTelegramHtml(details.driveUrl)}">📎 Apri il file Drive</a>`
    : '';
  return `📌 <b>Virgilio staging pilota registrato</b>\n` +
    `Attachment: ${_escapeTelegramHtml(details.attachmentId || '')}\n` +
    `File: ${_escapeTelegramHtml(details.stagedFilename || '')}\n` +
    `Account: ${_escapeTelegramHtml(details.accountAlias || '')}\n` +
    `Stato: ${_escapeTelegramHtml(details.state || '')}${link}`;
}
