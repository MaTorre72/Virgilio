/**
 * ============================================================
 * WEB APP - Interfaccia Virgilio
 * ============================================================
 *
 * Gestisce:
 * - apertura della Web App tramite doGet();
 * - creazione del form HTML con logo incorporato;
 * - caricamento dell'immagine Virgilio da Google Drive.
 */

// ID del FILE immagine Virgilio su Google Drive.
// Deve essere l'ID del singolo file PNG/GIF/JPEG/WebP, non di una cartella.
const VIRGILIO_ICON_FILE_ID = '1hYTL7KS6ZbOMSRhB_PQgF0OvDbtXJOJH';


/**
 * Endpoint GET della Web App.
 *
 * @param {Object=} e
 * @returns {GoogleAppsScript.HTML.HtmlOutput}
 */
function doGet(e) {
  return _creaOutputVirgilio_(e);
}


/**
 * Genera l'interfaccia Virgilio completa.
 *
 * Questa funzione e utilizzata sia dalla Web App sia dalla finestra
 * interna aperta dal menu del foglio Google Sheets.
 *
 * @param {Object=} e
 * @returns {GoogleAppsScript.HTML.HtmlOutput}
 */
function _creaOutputVirgilio_(e) {
  const template = HtmlService.createTemplateFromFile('virgilio');
  template.virgilioInboxContextJson = JSON.stringify(
    _caronteBuildVirgilioInboxTemplateContext_(e)
  );

  try {
    template.virgilioIconDataUri =
      _creaDataUriImmagine_(VIRGILIO_ICON_FILE_ID);

  } catch (err) {
    Logger.log(
      `[WebApp] Logo non caricato (${err.message}) - uso fallback "V"`
    );

    // Il form resta utilizzabile anche se l'immagine non e disponibile.
    template.virgilioIconDataUri = '';
  }

  return template
    .evaluate()
    .setTitle('Virgilio - Sigma+');
}

function _caronteBuildVirgilioInboxTemplateContext_(e) {
  const inboxId = _caronteReadInboxIdParameter_(e);
  if (!inboxId) {
    return {
      enabled: false,
      inbox_id: '',
      found: false,
      message: '',
    };
  }

  const lookup = caronteGetVirgilioInboxForForm(inboxId);
  return {
    enabled: true,
    inbox_id: inboxId,
    found: lookup && lookup.found === true,
    status: lookup && lookup.status || '',
    source_subject: lookup && lookup.source_subject || '',
    source_sender: lookup && lookup.source_sender || '',
    original_filename: lookup && lookup.original_filename || '',
    staged_filename: lookup && lookup.staged_filename || '',
    suggested_cliente: lookup && lookup.suggested_cliente || '',
    suggested_sito: lookup && lookup.suggested_sito || '',
    suggested_pratica: lookup && lookup.suggested_pratica || '',
    message: lookup && lookup.message || '',
  };
}

function _caronteReadInboxIdParameter_(e) {
  if (!e || !e.parameter) return '';
  return String(e.parameter.inbox_id || '').trim();
}


/**
 * Legge un'immagine da Google Drive e restituisce una data URI.
 *
 * Il file non deve essere pubblico:
 * viene letto dal server Apps Script e incorporato nell'HTML.
 *
 * @param {string} fileId
 * @returns {string}
 */
function _creaDataUriImmagine_(fileId) {
  if (!fileId) {
    throw new Error(
      'Configurare VIRGILIO_ICON_FILE_ID nel file webapp.gs.'
    );
  }

  const blob = DriveApp.getFileById(fileId).getBlob();
  const mimeType = blob.getContentType();

  if (!mimeType || !mimeType.startsWith('image/')) {
    throw new Error(
      `Il file selezionato non e un'immagine. MIME type: ${mimeType}`
    );
  }

  const base64 = Utilities.base64Encode(blob.getBytes());

  return `data:${mimeType};base64,${base64}`;
}
