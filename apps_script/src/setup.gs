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
      etichetta: 'Spreadsheet Bucoliche',
      hint: "Impostare l'ID del workbook condiviso nelle Script Properties.",
    },
    {
      chiave: 'VIRGILIO_INBOX_SPREADSHEET_ID',
      etichetta: 'Spreadsheet Inbox',
      hint: "Impostare l'ID del workbook della coda Virgilio_Inbox.",
    },
    {
      chiave: 'VIRGILIO_INBOX_SHEET_NAME',
      etichetta: 'Tab Inbox',
      hint: "Tenere il tab Virgilio_Inbox esplicito e configurato.",
    },
    {
      chiave: 'VIRGILIO_INTAKE_TEST_SPREADSHEET_ID',
      etichetta: 'Spreadsheet test',
      hint: "Impostare l'ID del workbook di test.",
    },
    {
      chiave: 'VIRGILIO_INTAKE_TEST_SHEET_NAME',
      etichetta: 'Tab test',
      hint: "Tenere il tab Staging_Local_Test esplicito e separato.",
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
      hint: "Eseguire generaToken() e poi impostarlo nelle Script Properties.",
    },
    {
      chiave: 'WEBHOOK_CHAT',
      etichetta: 'Webhook Google Chat',
      hint: "Impostare l'URL del webhook nelle Script Properties.",
    },
    {
      chiave: 'TELEGRAM_TOKEN',
      etichetta: 'Token Telegram',
      hint: "Impostare il token Telegram nelle Script Properties.",
    },
    {
      chiave: 'TELEGRAM_CHAT_ID',
      etichetta: 'Chat ID Telegram',
      hint: "Impostare l'ID della chat nelle Script Properties.",
    },
    {
      chiave: 'URL_FORM',
      etichetta: 'URL form Virgilio',
      hint: "Impostare l'URL /exec della Web App nelle Script Properties.",
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
 * I valori vanno impostati nelle Script Properties o passati a runtime,
 * mai scritti nel file sorgente.
 * Eseguire UNA SOLA VOLTA dopo aver ottenuto tutti i valori necessari.
 *
 * Gli identificativi operativi (Bucoliche, Inbox, test, Empireo, Adamo, Limbo e tab)
 * vanno impostati separatamente nelle Script Properties.
 *
 * ⚠ ISTRUZIONI:
 * 1. Recuperare i valori richiesti
 * 2. Impostarli nelle Script Properties oppure passarli a caronteSetupCredenziali({ ... })
 * 3. Verificare con caronteStatoCredenziali() che siano caricate
 *
 * Come ottenere i valori:
 * - VIRGILIO_TOKEN:   eseguire generaToken() e copiare l'output
 * - WEBHOOK_CHAT:     Google Chat → Spazio → Gestisci webhook → crea nuovo
 * - TELEGRAM_TOKEN:   @BotFather su Telegram → /newbot o /revoke
 * - TELEGRAM_CHAT_ID: aggiungere @userinfobot al gruppo, invia /start
 * - URL_FORM:         Apps Script → Distribuisci → Gestisci distribuzioni → copia URL /exec
 */
function caronteSetupCredenziali(valori) {
  const props = PropertiesService.getScriptProperties();

  const chiavi = ['VIRGILIO_TOKEN', 'WEBHOOK_CHAT', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'URL_FORM'];
  const daSalvare = {};

  if (valori && typeof valori === 'object' && !Array.isArray(valori)) {
    chiavi.forEach((chiave) => {
      const valore = valori[chiave];
      if (typeof valore !== 'string') return;
      const pulito = valore.trim();
      if (!pulito || pulito.startsWith('[SOSTITUIRE') || pulito.startsWith('[DA_INSERIRE')) return;
      daSalvare[chiave] = pulito;
    });
  }

  if (Object.keys(daSalvare).length === 0) {
    Logger.log('[Setup] Nessuna credenziale passata: valorizzare le Script Properties o richiamare caronteSetupCredenziali({ ... }).');
    caronteStatoCredenziali();
    return { ok: false, saved: [] };
  }

  props.setProperties(daSalvare);
  Logger.log(`[Setup] Credenziali salvate nelle Script Properties: ${Object.keys(daSalvare).join(', ')}`);
  Logger.log('[Setup] Verificare subito con caronteStatoCredenziali().');
  caronteStatoCredenziali();
  return { ok: true, saved: Object.keys(daSalvare) };
}


/**
 * Genera un token segreto robusto per VIRGILIO_TOKEN.
 * Eseguire una volta e usare il valore generato nelle Script Properties
 * o nella chiamata a caronteSetupCredenziali({ VIRGILIO_TOKEN: ... }).
 */
function generaToken() {
  const token = Utilities.getUuid().replace(/-/g, '') +
                Utilities.getUuid().replace(/-/g, '');
  Logger.log('[Setup] Token generato (64 char hex):');
  Logger.log(token);
  Logger.log('[Setup] Copiare questo valore nelle Script Properties o nella chiamata a caronteSetupCredenziali({ VIRGILIO_TOKEN: ... })');
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

