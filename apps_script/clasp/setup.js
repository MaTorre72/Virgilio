/**
 * ============================================================
 *  SETUP — Configurazione trigger Progetto Virgilio v1.0
 * ============================================================
 *  Eseguire caronteSetupTrigger() UNA SOLA VOLTA dopo aver
 *  superato caronteTest() con tutti i check verdi.
 *
 *  Crea il trigger temporale che esegue caronteTraghetta()
 *  ogni 5 minuti in modo automatico e continuo.
 *
 *  Dipendenze: CONFIG (caronte.gs)
 * ============================================================
 */


/**
 * Configura il trigger temporale per caronteTraghetta().
 * Rimuove eventuali trigger duplicati prima di crearne uno nuovo.
 * Eseguire una sola volta dopo il deploy.
 */
function caronteSetupTrigger() {
  Logger.log('[Setup] Configurazione trigger Caronte...');

  // Rimuove tutti i trigger esistenti per caronteTraghetta (evita duplicati)
  const triggers = ScriptApp.getProjectTriggers();
  let rimossi = 0;

  for (const trigger of triggers) {
    if (trigger.getHandlerFunction() === 'caronteTraghetta') {
      ScriptApp.deleteTrigger(trigger);
      rimossi++;
    }
  }

  if (rimossi > 0) {
    Logger.log(`[Setup] ${rimossi} trigger precedente/i rimosso/i`);
  }

  // Crea il nuovo trigger ogni 5 minuti
  ScriptApp.newTrigger('caronteTraghetta')
    .timeBased()
    .everyMinutes(5)
    .create();

  Logger.log('[Setup] ✓ Trigger attivato — Caronte scansionerà ogni 5 minuti');
  Logger.log('[Setup] Per disattivare: Progetto → Trigger → elimina manualmente');
}


/**
 * Rimuove tutti i trigger attivi per caronteTraghetta.
 * Utile per mettere in pausa il sistema senza toccare il codice.
 */
function caronteStopTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  let rimossi = 0;

  for (const trigger of triggers) {
    if (trigger.getHandlerFunction() === 'caronteTraghetta') {
      ScriptApp.deleteTrigger(trigger);
      rimossi++;
    }
  }

  if (rimossi > 0) {
    Logger.log(`[Setup] ✓ ${rimossi} trigger rimosso/i — Caronte in pausa`);
  } else {
    Logger.log('[Setup] Nessun trigger attivo trovato per caronteTraghetta');
  }
}


/**
 * Mostra i trigger attivi nel log. Utile per verificare lo stato.
 */
function caronteStatoTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  const attivi = triggers.filter(t => t.getHandlerFunction() === 'caronteTraghetta');

  if (attivi.length === 0) {
    Logger.log('[Setup] Nessun trigger attivo per caronteTraghetta — sistema in pausa');
  } else {
    Logger.log(`[Setup] ${attivi.length} trigger attivo/i per caronteTraghetta:`);
    attivi.forEach((t, i) => {
      Logger.log(`  ${i + 1}. ID: ${t.getUniqueId()} | Tipo: ${t.getTriggerSource()}`);
    });
  }
}

/**
 * Mostra un riepilogo sintetico della configurazione operativa.
 *
 * Le informazioni sensibili non vengono mai stampate: il log indica solo
 * se ogni valore richiesto e' presente e quale passo fare in caso contrario.
 */
function caronteStatoConfigurazione() {
  const props = PropertiesService.getScriptProperties();
  const controlli = [
    {
      chiave: 'VIRGILIO_BUCOLICHE_SPREADSHEET_ID',
      etichetta: 'Workbook condiviso',
      hint: "Impostare un solo file per Bucoliche, Virgilio_Inbox e Staging_Local_Test.",
    },
    {
      chiave: 'VIRGILIO_BUCOLICHE_TAB',
      etichetta: 'Tab Bucoliche',
      hint: "Tenere il tab canonico nel workbook condiviso.",
    },
    {
      chiave: 'VIRGILIO_INBOX_SHEET_NAME',
      etichetta: 'Tab Inbox',
      hint: "Tenere Virgilio_Inbox nello stesso workbook condiviso.",
    },
    {
      chiave: 'VIRGILIO_INTAKE_TEST_SHEET_NAME',
      etichetta: 'Tab test',
      hint: "Tenere Staging_Local_Test nello stesso workbook condiviso.",
    },
    {
      chiave: 'VIRGILIO_EMPIREO_ID',
      etichetta: 'Cartella Empireo',
      hint: "Impostare l'ID della cartella Drive radice nelle Script Properties.",
    },
    {
      chiave: 'VIRGILIO_ADAMO_ID',
      etichetta: 'Cartella Adamo',
      hint: "Impostare l'ID della cartella template nelle Script Properties.",
    },
    {
      chiave: 'VIRGILIO_LIMBO_ID',
      etichetta: 'Cartella Limbo',
      hint: "Impostare l'ID della cartella staging condivisa nelle Script Properties.",
    },
    {
      chiave: 'VIRGILIO_TOKEN',
      etichetta: 'Token Virgilio',
      hint: "Eseguire generaToken() e poi caronteSetupCredenziali().",
    },
    {
      chiave: 'WEBHOOK_CHAT',
      etichetta: 'Webhook Google Chat',
      hint: "Inserire l'URL del webhook nella setup credenziali.",
    },
    {
      chiave: 'TELEGRAM_TOKEN',
      etichetta: 'Token Telegram',
      hint: "Recuperare il token e salvarlo con caronteSetupCredenziali().",
    },
    {
      chiave: 'TELEGRAM_CHAT_ID',
      etichetta: 'Chat ID Telegram',
      hint: "Inserire l'ID della chat nel setup credenziali.",
    },
    {
      chiave: 'URL_FORM',
      etichetta: 'URL form Virgilio',
      hint: "Copiare l'URL /exec della Web App nel setup credenziali.",
    },
  ];

  Logger.log('[Setup] Riepilogo configurazione operativa:');
  controlli.forEach(({ chiave, etichetta, hint }) => {
    const valore = props.getProperty(chiave);
    if (!valore || valore.startsWith('[SOSTITUIRE')) {
      Logger.log(`  ✗ ${etichetta}: non configurato`);
      Logger.log(`    -> ${hint}`);
    } else {
      Logger.log(`  ✓ ${etichetta}: configurato (${valore.length} caratteri)`);
    }
  });

  const urlForm = props.getProperty('URL_FORM');
  if (!urlForm || urlForm.startsWith('[SOSTITUIRE')) {
    Logger.log('  → Endpoint webapp: non configurato');
  } else {
    Logger.log(`  → Endpoint webapp: pronto (${urlForm})`);
  }
}


// ── UI INTERNA VIRGILIO — TEST SENZA DEPLOY PUBBLICO ─────────────────────────

/**
 * Menu interno, utile se questo progetto Apps Script è collegato a Google Sheets.
 * Dopo il reload del file Bucoliche compare: Virgilio → Apri form Virgilio.
 */
function onOpen() {
  try {
    SpreadsheetApp.getUi()
      .createMenu('Virgilio')
      .addItem('Apri form Virgilio', 'mostraVirgilio')
      .addSeparator()
      .addItem('Test backend Virgilio', 'testVirgilioSenzaDeploy')
      .addItem('Test Gmail da-traghettare', 'testGmailDaTraghettare')
      .addToUi();
  } catch (err) {
    Logger.log('[UI Virgilio] onOpen non disponibile in progetto standalone: ' + err.message);
  }
}

/**
 * Apre il form Virgilio come finestra interna di Google Sheets.
 *
 * Usa lo stesso generatore HTML della Web App.
 * In questo modo il template viene valutato correttamente
 * e il logo viene incorporato anche nella finestra interna.
 */
function mostraVirgilio() {
  const html = _creaOutputVirgilio_()
    .setWidth(980)
    .setHeight(860);

  SpreadsheetApp
    .getUi()
    .showModalDialog(html, 'Virgilio — Apertura pratica');
}

// ── SETUP CREDENZIALI ─────────────────────────────────────────────────────────

/**
 * Carica le credenziali sensibili nelle PropertiesService dello script.
 * Eseguire UNA SOLA VOLTA dopo aver ottenuto tutti i valori necessari.
 *
 * Gli identificativi operativi del workbook condiviso e dei tab
 * vanno impostati separatamente nelle Script Properties.
 *
 * ⚠ ISTRUZIONI:
 * 1. Sostituire i placeholder qui sotto con i valori reali
 * 2. Eseguire questa funzione dalla console Apps Script
 * 3. Cancellare i valori reali da qui e salvare — le props sono persistenti
 * 4. Verificare con caronteStatoCredenziali() che siano caricate
 *
 * Come ottenere i valori:
 * - VIRGILIO_TOKEN:   eseguire generaToken() e copiare l'output
 * - WEBHOOK_CHAT:     Google Chat → Spazio → Gestisci webhook → crea nuovo
 * - TELEGRAM_TOKEN:   @BotFather su Telegram → /newbot o /revoke
 * - TELEGRAM_CHAT_ID: aggiungere @userinfobot al gruppo, invia /start
 * - URL_FORM:         Apps Script → Distribuisci → Gestisci distribuzioni → copia URL /exec
 */
function caronteSetupCredenziali() {
  const props = PropertiesService.getScriptProperties();

  props.setProperties({
    'VIRGILIO_TOKEN':   '[SOSTITUIRE — generare con generaToken()]',
    'WEBHOOK_CHAT':     '[SOSTITUIRE — URL webhook Google Chat]',
    'TELEGRAM_TOKEN':   '[SOSTITUIRE — token da @BotFather]',
    'TELEGRAM_CHAT_ID': '[SOSTITUIRE — chat ID gruppo Telegram]',
    'URL_FORM':         '[SOSTITUIRE — URL /exec della Web App Virgilio]',
  });

  Logger.log('[Setup] Credenziali salvate nelle PropertiesService.');
  Logger.log('[Setup] ⚠ Cancellare ora i valori reali da questa funzione e salvare il file.');
}


/**
 * Genera un token segreto robusto per VIRGILIO_TOKEN.
 * Eseguire una volta e copiare l'output nel campo VIRGILIO_TOKEN
 * di caronteSetupCredenziali().
 */
function generaToken() {
  const token = Utilities.getUuid().replace(/-/g, '') +
                Utilities.getUuid().replace(/-/g, '');
  Logger.log('[Setup] Token generato (64 char hex):');
  Logger.log(token);
  Logger.log('[Setup] Copiare questo valore in caronteSetupCredenziali() → VIRGILIO_TOKEN');
}


/**
 * Mostra quali credenziali sono caricate (solo i nomi, mai i valori).
 * Utile per verificare lo stato senza esporre i segreti nei log.
 */
function caronteStatoCredenziali() {
  const props = PropertiesService.getScriptProperties();
  const chiavi = ['VIRGILIO_TOKEN', 'WEBHOOK_CHAT', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'URL_FORM'];

  Logger.log('[Setup] Stato credenziali PropertiesService:');
  for (const chiave of chiavi) {
    const valore = props.getProperty(chiave);
    if (!valore || valore.startsWith('[SOSTITUIRE')) {
      Logger.log(`  ✗ ${chiave}: NON configurata`);
    } else {
      Logger.log(`  ✓ ${chiave}: configurata (${valore.length} caratteri)`);
    }
  }
  caronteStatoConfigurazione();
}


/**
 * Rimuove tutte le credenziali dalle PropertiesService.
 * Usare solo in caso di rotazione completa o dismissione del sistema.
 */
function caronteResetCredenziali() {
  const props = PropertiesService.getScriptProperties();
  props.deleteAllProperties();
  Logger.log('[Setup] ⚠ Tutte le credenziali sono state rimosse dalle PropertiesService.');
}

