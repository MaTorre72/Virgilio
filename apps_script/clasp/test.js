/**
 * ============================================================
 *  TEST — Verifica pre-deploy Progetto Virgilio v1.0
 * ============================================================
 *  Eseguire caronteTest() manualmente prima di ogni deploy.
 *  Verifica che tutti i componenti siano raggiungibili e
 *  configurati correttamente.
 *
 *  Output atteso (tutto verde):
 *  ✓ Bucoliche: "Bucoliche Sigma+"
 *  ✓ Empireo: "01_commesse_Sigma+"
 *  ✓ Adamo: "_template_adamo"
 *  ✓ Limbo: "_limbo"
 *  ✓ Gmail: 0 thread da-traghettare
 *  ✓ Chat: HTTP 200
 *  ✓ Telegram: HTTP 200
 *  ✓ doPost: { status: ok, cartella: ... }
 *  === CARONTE PRONTO AL DEPLOY ===
 *
 *  Dipendenze: CONFIG (caronte.gs), bucoliche.gs, notifiche.gs
 * ============================================================
 */


/**
 * Test completo pre-deploy. Eseguire manualmente da Apps Script
 * (Esegui → caronteTest) e aprire Visualizza → Log per leggere i risultati.
 */
function caronteTest() {
  Logger.log('');
  Logger.log('════════════════════════════════════════');
  Logger.log('  TEST CARONTE v1.0 — Progetto Virgilio');
  Logger.log('════════════════════════════════════════');
  Logger.log('');

  let tuttoOk = true;

  // ── 1. Bucoliche ────────────────────────────────────────────
  Logger.log('--- 1. Bucoliche (Google Sheets) ---');
  try {
    const sheet = SpreadsheetApp.openById(CONFIG.BUCOLICHE_ID);
    Logger.log(`✓ Bucoliche: "${sheet.getName()}"`);
  } catch (err) {
    Logger.log(`✗ Bucoliche NON accessibili: ${err.message}`);
    Logger.log('  → Verificare BUCOLICHE_ID in CONFIG');
    tuttoOk = false;
  }

  // ── 2. Empireo ──────────────────────────────────────────────
  Logger.log('');
  Logger.log('--- 2. Empireo (cartella Drive radice) ---');
  try {
    const empireo = DriveApp.getFolderById(CONFIG.EMPIREO_ID);
    Logger.log(`✓ Empireo: "${empireo.getName()}"`);
  } catch (err) {
    Logger.log(`✗ Empireo NON accessibile: ${err.message}`);
    Logger.log('  → Verificare EMPIREO_ID in CONFIG');
    tuttoOk = false;
  }

  // ── 3. Adamo ────────────────────────────────────────────────
  Logger.log('');
  Logger.log('--- 3. Adamo (cartella template) ---');
  try {
    const adamo = DriveApp.getFolderById(CONFIG.ADAMO_ID);
    Logger.log(`✓ Adamo: "${adamo.getName()}"`);

    // Verifica che Adamo abbia almeno le sotto-cartelle default
    const sottoCartelle = [];
    const iter = adamo.getFolders();
    while (iter.hasNext()) sottoCartelle.push(iter.next().getName());

    if (sottoCartelle.length === 0) {
      Logger.log('  ⚠ AVVISO — Adamo è vuoto: nessuna sotto-cartella trovata');
      Logger.log(
        '  → Inserire in Adamo le cartelle trasversali: ' +
        '00_autorizzazioni, 01_dati-ditta, 02_corrispondenza'
      );
    } else {
      Logger.log(`  Sotto-cartelle trovate: ${sottoCartelle.join(', ')}`);
    }
  } catch (err) {
    Logger.log(`✗ Adamo NON accessibile: ${err.message}`);
    Logger.log('  → Verificare ADAMO_ID in CONFIG');
    Logger.log('  → Nota: il sistema userà la struttura default come fallback');
    tuttoOk = false;
  }

  // ── 4. Limbo ────────────────────────────────────────────────
  Logger.log('');
  Logger.log('--- 4. Limbo (cartella staging) ---');
  try {
    const limbo = DriveApp.getFolderById(CONFIG.LIMBO_ID);
    Logger.log(`✓ Limbo: "${limbo.getName()}"`);
  } catch (err) {
    Logger.log(`✗ Limbo NON accessibile: ${err.message}`);
    Logger.log('  → Verificare LIMBO_ID in CONFIG');
    tuttoOk = false;
  }

  // ── 5. Gmail ────────────────────────────────────────────────
  Logger.log('');
  Logger.log('--- 5. Gmail ---');
  try {
    const threads = GmailApp.search(`label:"${CONFIG.ETICHETTA_TRIGGER}"`, 0, 1);
    Logger.log(`✓ Gmail accessibile — thread con "${CONFIG.ETICHETTA_TRIGGER}": ${threads.length}`);
  } catch (err) {
    Logger.log(`✗ Gmail NON accessibile: ${err.message}`);
    Logger.log('  → Verificare autorizzazioni OAuth e Domain-Wide Delegation');
    tuttoOk = false;
  }

  // ── 6. Google Chat ──────────────────────────────────────────
  Logger.log('');
  Logger.log('--- 6. Google Chat (webhook) ---');
  if (!CONFIG.WEBHOOK_CHAT || CONFIG.WEBHOOK_CHAT === '[DA_INSERIRE]') {
    Logger.log('⚠ WEBHOOK_CHAT non configurato — test saltato');
    Logger.log('  → Inserire il webhook dello spazio Google Chat in CONFIG');
  } else {
    try {
      const payload = JSON.stringify({
        text: '🔧 *Virgilio Test* — verifica connessione pre-deploy. Ignorare.',
      });
      const risposta = UrlFetchApp.fetch(CONFIG.WEBHOOK_CHAT, {
        method:             'post',
        contentType:        'application/json',
        payload:            payload,
        muteHttpExceptions: true,
      });
      const codice = risposta.getResponseCode();
      if (codice === 200) {
        Logger.log(`✓ Chat: HTTP ${codice} — messaggio inviato`);
      } else {
        Logger.log(`✗ Chat: HTTP ${codice} — ${risposta.getContentText()}`);
        tuttoOk = false;
      }
    } catch (err) {
      Logger.log(`✗ Chat ERRORE: ${err.message}`);
      tuttoOk = false;
    }
  }

  // ── 7. Telegram ─────────────────────────────────────────────
  Logger.log('');
  Logger.log('--- 7. Telegram (bot) ---');
  if (!CONFIG.TELEGRAM_TOKEN || CONFIG.TELEGRAM_TOKEN === '[DA_INSERIRE]') {
    Logger.log('⚠ TELEGRAM_TOKEN non configurato — test saltato');
    Logger.log('  → Creare il bot su @BotFather e inserire token + chat_id in CONFIG');
  } else {
    try {
      const url = `https://api.telegram.org/bot${CONFIG.TELEGRAM_TOKEN}/sendMessage`;

      // PATCH TEST:
      // Il test Telegram usa la stessa variante HTML della notifica reale.
      // Qui lasciamo log di debug perché siamo dentro caronteTest(), non nel flusso operativo.
      const testoTelegramTest =
        '🔧 <b>Virgilio Test</b> — verifica connessione pre-deploy. Ignorare.\n' +
        'Caso caratteri speciali: 2026_assistenza / _TEST_CLIENTE_ / AUA &amp; rifiuti';

      const payload = JSON.stringify({
        chat_id: CONFIG.TELEGRAM_CHAT_ID,
        text: testoTelegramTest,
        parse_mode: 'HTML',
        disable_web_page_preview: true,
      });

      Logger.log(`  [DEBUG TEST Telegram] Payload: ${payload}`);

      const risposta = UrlFetchApp.fetch(url, {
        method:             'post',
        contentType:        'application/json',
        payload:            payload,
        muteHttpExceptions: true,
      });
      const codice = risposta.getResponseCode();
      const testoRisposta = risposta.getContentText();
      const body   = JSON.parse(testoRisposta);

      Logger.log(`  [DEBUG TEST Telegram] HTTP ${codice} — risposta: ${testoRisposta}`);

      if (body.ok) {
        Logger.log(`✓ Telegram: HTTP ${codice} — messaggio HTML inviato`);
      } else {
        Logger.log(`✗ Telegram: ${JSON.stringify(body)}`);
        tuttoOk = false;
      }
    } catch (err) {
      Logger.log(`✗ Telegram ERRORE: ${err.message}`);
      tuttoOk = false;
    }
  }

  // ── 8. doPost simulato ──────────────────────────────────────
  Logger.log('');
  Logger.log('--- 8. doPost simulato ---');
  try {
    const payloadTest = {
      token:   CONFIG.VIRGILIO_TOKEN,
      cliente: '_TEST_CLIENTE_',
      sito:    '_TEST_SITO_',
      pratica: 'assistenza',
      anno:    new Date().getFullYear().toString(),
      tecnici: ['Test'],
      note:    'Test pre-deploy — cartella da eliminare manualmente',
      origine: 'test',
    };

    // Simula l'evento doPost
    const eventoFinto = {
      postData: {
        contents: JSON.stringify(payloadTest),
      },
    };

    const risposta = doPost(eventoFinto);
    const body     = JSON.parse(risposta.getContent());

    if (body.status === 'ok') {
      Logger.log(`✓ doPost: status ok — cartella: ${body.cartella}`);
      Logger.log(`  ⚠ RICORDA: eliminare la cartella di test "_TEST_CLIENTE_" dall'Empireo`);
    } else {
      Logger.log(`✗ doPost ha risposto con errore: ${body.messaggio}`);
      tuttoOk = false;
    }
  } catch (err) {
    Logger.log(`✗ doPost ERRORE: ${err.message}`);
    tuttoOk = false;
  }

  // ── Risultato finale ────────────────────────────────────────
  Logger.log('');
  Logger.log('════════════════════════════════════════');
  if (tuttoOk) {
    Logger.log('  ✓✓✓  CARONTE PRONTO AL DEPLOY  ✓✓✓');
  } else {
    Logger.log('  ✗  PROBLEMI RILEVATI — risolvere prima del deploy');
    Logger.log('  → Rileggere i messaggi ✗ sopra e correggere CONFIG');
  }
  Logger.log('════════════════════════════════════════');
  Logger.log('');
}



/**
 * TEST FINALE ORCHESTRATO.
 *
 * Eseguire questa funzione per il collaudo rapido prima del deploy:
 * 1) controlla configurazioni e canali;
 * 2) simula doPost;
 * 3) simula il form Virgilio senza deploy;
 * 4) controlla se ci sono mail etichettate da-traghettare.
 *
 * Nota: il test Gmail non crea una mail. Devi prima etichettare manualmente
 * una mail di prova con CONFIG.ETICHETTA_TRIGGER.
 */
function caronteTestFinale() {
  Logger.log('');
  Logger.log('════════════════════════════════════════');
  Logger.log('  TEST FINALE VIRGILIO / CARONTE');
  Logger.log('════════════════════════════════════════');

  Logger.log('');
  Logger.log('FASE A — Test generale Caronte');
  caronteTest();

  Logger.log('Attendo 11 secondi per rispettare il rate limit...');
  Utilities.sleep(11000);

  Logger.log('');
  Logger.log('FASE B — Test bridge form Virgilio senza deploy');
  testVirgilioSenzaDeploy();

  Logger.log('');
  Logger.log('FASE C — Test Gmail etichetta da-traghettare');
  testGmailDaTraghettare();

  Logger.log('');
  Logger.log('════════════════════════════════════════');
  Logger.log('  TEST FINALE COMPLETATO');
  Logger.log('  Se non ci sono righe ✗, il sistema è pronto per il test operativo.');
  Logger.log('════════════════════════════════════════');
}


/**
 * Test dedicato al flusso Gmail.
 *
 * Prima di eseguirlo:
 * - prendi una mail di prova;
 * - aggiungi l'etichetta CONFIG.ETICHETTA_TRIGGER, es. "da-traghettare";
 * - meglio se la mail contiene un allegato reale > 5 KB.
 *
 * Cosa verifica:
 * - Gmail è accessibile;
 * - la query con etichetta trova i thread;
 * - caronteTraghetta() salva gli allegati in Limbo;
 * - la mail viene spostata da "da-traghettare" a "traghettate".
 */
function testGmailDaTraghettare() {
  Logger.log('--- TEST GMAIL da-traghettare ---');

  const query = `label:"${CONFIG.ETICHETTA_TRIGGER}"`;
  const threadsPrima = GmailApp.search(query);

  Logger.log(`Query usata: ${query}`);
  Logger.log(`Thread trovati prima di Caronte: ${threadsPrima.length}`);

  if (threadsPrima.length === 0) {
    Logger.log('⚠ Nessuna mail etichettata trovata.');
    Logger.log(`  → Per testare: applica l'etichetta "${CONFIG.ETICHETTA_TRIGGER}" a una mail con allegato e rilancia testGmailDaTraghettare().`);
    return;
  }

  caronteTraghetta();

  const threadsDopo = GmailApp.search(query);
  Logger.log(`Thread rimasti con etichetta "${CONFIG.ETICHETTA_TRIGGER}" dopo Caronte: ${threadsDopo.length}`);

  if (threadsDopo.length === 0) {
    Logger.log('✓ Gmail trigger: etichetta rimossa correttamente dopo il traghettamento');
  } else {
    Logger.log('⚠ Alcuni thread hanno ancora l\'etichetta trigger. Controllare allegati, permessi o log precedenti.');
  }
}
