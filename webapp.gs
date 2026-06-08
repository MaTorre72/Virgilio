/**
 * ============================================================
 * WEB APP — Interfaccia Virgilio
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
 */
function doGet() {
  return _creaOutputVirgilio_();
}


/**
 * Genera l'interfaccia Virgilio completa.
 *
 * Questa funzione è utilizzata sia dalla Web App sia dalla finestra
 * interna aperta dal menu del foglio Google Sheets.
 *
 * @returns {GoogleAppsScript.HTML.HtmlOutput}
 */
function _creaOutputVirgilio_() {
  const template = HtmlService.createTemplateFromFile('virgilio');

  try {
    template.virgilioIconDataUri =
      _creaDataUriImmagine_(VIRGILIO_ICON_FILE_ID);

  } catch (err) {
    Logger.log(
      `[WebApp] Logo non caricato (${err.message}) — uso fallback "V"`
    );

    // Il form resta utilizzabile anche se l'immagine non è disponibile.
    template.virgilioIconDataUri = '';
  }

  return template
    .evaluate()
    .setTitle('Virgilio — Sigma+');
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
      `Il file selezionato non è un'immagine. MIME type: ${mimeType}`
    );
  }

  const base64 = Utilities.base64Encode(blob.getBytes());

  return `data:${mimeType};base64,${base64}`;
}