/**
 * ============================================================
 *  CARONTE v1.0 — Il traghettatore — Progetto Virgilio
 * ============================================================
 *  Motore principale del sistema. Gestisce:
 *
 *  — doPost()              endpoint webhook (form Virgilio → creazione pratica)
 *  — caronteTraghetta()    polling Gmail ogni 5 minuti → staging nel Limbo
 *  — creaCartellaPratica() struttura Drive da template Adamo
 *  — èAllegatoReale()      filtro allegati email
 *  — gestioneEtichette     helpers Gmail
 *
 *  Dipendenze: bucoliche.gs, notifiche.gs
 * ============================================================
 */


// ── CONFIGURAZIONE ────────────────────────────────────────────────────────────

// ── CREDENZIALI — lette da PropertiesService, MAI nel codice ─────────────────
// Eseguire setup.gs → caronteSetupCredenziali() una volta per caricarle.
const _PROPS = PropertiesService.getScriptProperties();

const CONFIG = {

  // ── ID Drive/Sheets — non segreti, ok nel codice ──
  // ID Google Sheets "Bucoliche"
  BUCOLICHE_ID: '1HFtu4nLExP3K1S1qiAIkQ8okW1hfSbubFJm3WE2-fdU',
  BUCOLICHE_TAB: 'bucoliche',

  // ID cartella Drive radice "Empireo" (01_commesse_Sigma+)
  EMPIREO_ID: '1-F_vr1waW2MJp1hyQxAKZy0t5hM3qPem',

  // ID cartella template "Adamo"
  ADAMO_ID: '1T_bSvPtqomoOguvIpiQxkBzVl66i4BsG',

  // ID cartella staging "Limbo" (dentro Empireo)
  LIMBO_ID: '1y36QA5OUgp2vDMAOD2T7LdPds9_7kk5i',

  // ── Etichette Gmail ──
  ETICHETTA_TRIGGER:  'da-traghettare',
  ETICHETTA_ELABORATA: 'traghettate',

  // ── Credenziali — lette da PropertiesService a runtime ──
  // NON inserire mai valori reali qui sotto.
  // Usare caronteSetupCredenziali() in setup.gs per caricarli.
  VIRGILIO_TOKEN:   _PROPS.getProperty('VIRGILIO_TOKEN'),
  WEBHOOK_CHAT:     _PROPS.getProperty('WEBHOOK_CHAT'),
  TELEGRAM_TOKEN:   _PROPS.getProperty('TELEGRAM_TOKEN'),
  TELEGRAM_CHAT_ID: _PROPS.getProperty('TELEGRAM_CHAT_ID'),

  // Utenti Gmail da monitorare
  UTENTI: [
    'marco@sigmapiu.it',
    // 'nnnnnnnnnnnnn@sigmapiu.it',
    // 'nnnnnnnnnnnnn@sigmapiu.it',
  ],

  // Dimensione massima allegato accettata (MB)
  MAX_ALLEGATO_MB: 25,

  // Numero massimo di giorni entro cui gli allegati presenti nel Limbo
  // vengono spostati automaticamente nella pratica appena aperta.
  //
  // ATTENZIONE:
  // Caronte sposta TUTTI i file recenti presenti nel Limbo,
  // senza ancora distinguere automaticamente cliente e pratica.
  //
  // Per il prototipo tenere una finestra breve: 1 o 2 giorni.
  GIORNI_LIMBO_DA_SPOSTARE: 2,

  // Sotto-cartelle da creare se Adamo non è disponibile (fallback)
  SOTTOCARTELLE_DEFAULT: [
    '00_autorizzazioni',
    '01_dati-ditta',
    '02_corrispondenza',
  ],

  // Vocabolario tipi pratica ammessi
  TIPI_PRATICA: [
    'AUA','AIA','VIA','EoW','TR',
    'bonifica','emissioni','rifiuti',
    'sottoprodotti','PEI','PEE','reportAIA','assistenza',
  ],

  // URL pubblico del form Virgilio (Web App /exec)
  // Inserire l'URL ottenuto dopo il deploy in Distribuisci → Gestisci distribuzioni
  URL_FORM: _PROPS.getProperty('URL_FORM') || '[DA_INSERIRE_URL_FORM]',
};


// ── MODULO 1 — ENDPOINT WEBHOOK ───────────────────────────────────────────────

/**
 * Endpoint HTTP POST — riceve i dati dal form Virgilio (e in futuro da VTEnext).
 * Crea la cartella pratica, avvisa il team, registra sulle Bucoliche.
 *
 * @param {Object} e - Evento Apps Script Web App
 * @returns {GoogleAppsScript.Content.TextOutput} JSON response
 */
function doPost(e) {
  let dati = {};

  try {
    // 1. Parsing del body JSON
    dati = JSON.parse(e.postData.contents);
  } catch (err) {
    Logger.log(`[Caronte] doPost — body non valido: ${err.message}`);
    return _rispostaJSON({ status: 'error', messaggio: 'Body JSON non valido' });
  }

  // Bridge Local IMAP metadata-only. Questo ramo precede intenzionalmente il
  // flusso operativo e non usa token, Drive, Bucoliche, notifiche o Gmail.
  if (dati.action === CARONTE_DRY_RUN_ACTION) {
    return _rispostaJSON(caronteRiceviComandoDryRun(dati.payload));
  }

  // Verifica read-only della cartella Drive Desktop sincronizzata.
  if (dati.action === DRIVE_STAGING_VERIFY_ACTION) {
    return _rispostaJSON(caronteVerificaStagingDriveDryRun(dati));
  }

  if (dati.action === DRIVE_STAGING_INTAKE_TEST_ACTION) {
    return _rispostaJSON(caronteRegistraStagingDriveTest(dati));
  }

  // 2. Verifica token di sicurezza
  // ⚠ Non loggare mai CONFIG.VIRGILIO_TOKEN — usare solo nomi simbolici nei log
  if (!CONFIG.VIRGILIO_TOKEN || dati.token !== CONFIG.VIRGILIO_TOKEN) {
    Logger.log('[Caronte] doPost — token non autorizzato');
    return _rispostaJSON({ status: 'error', messaggio: 'Non autorizzato' });
  }

  // 2b. Rate limiting — max 1 richiesta ogni 10 secondi
  try {
    _verificaRateLimit();
  } catch (err) {
    Logger.log(`[Caronte] doPost — rate limit: ${err.message}`);
    return _rispostaJSON({ status: 'error', messaggio: err.message });
  }

  // 3. Validazione campi obbligatori
  const campiObbligatori = ['cliente', 'sito', 'pratica', 'anno'];
  const campiMancanti = campiObbligatori.filter(c => !dati[c] || !dati[c].toString().trim());

  if (campiMancanti.length > 0) {
    Logger.log(`[Caronte] doPost — campi mancanti: ${campiMancanti.join(', ')}`);
    return _rispostaJSON({
      status:    'error',
      messaggio: `Campi obbligatori mancanti: ${campiMancanti.join(', ')}`,
    });
  }

  // 3b. Validazione lunghezze campi
  try {
    _validaLunghezze(dati);
  } catch (err) {
    Logger.log(`[Caronte] doPost — validazione lunghezze: ${err.message}`);
    return _rispostaJSON({ status: 'error', messaggio: err.message });
  }

  // 4. Validazione tipo pratica
  if (!CONFIG.TIPI_PRATICA.includes(dati.pratica)) {
    Logger.log(`[Caronte] doPost — tipo pratica non valido: ${dati.pratica}`);
    return _rispostaJSON({
      status:    'error',
      messaggio: `Tipo pratica non valido: "${dati.pratica}". Valori ammessi: ${CONFIG.TIPI_PRATICA.join(', ')}`,
    });
  }

  const inboxId = dati.inbox_id ? dati.inbox_id.toString().trim() : '';
  let inboxLink = null;
  if (inboxId) {
    inboxLink = caronteCollegaSubmitVirgilioInbox({
      inbox_id: inboxId,
      cliente: dati.cliente.toString().trim(),
      sito: dati.sito.toString().trim(),
      pratica: dati.pratica.toString().trim(),
      anno: dati.anno.toString().trim(),
      note: dati.note ? dati.note.toString() : '',
      tecnici: Array.isArray(dati.tecnici) ? dati.tecnici : [],
      submitted_at: _timestampLocale(),
    });
    if (!inboxLink || inboxLink.ok !== true) {
      Logger.log(`[Caronte] doPost — inbox non collegata: ${inboxId}`);
      return _rispostaJSON({
        status: 'error',
        messaggio: inboxLink && inboxLink.message
          ? inboxLink.message
          : 'Impossibile collegare il submit al record Virgilio_Inbox.',
      });
    }
  }

  // 5. Esecuzione operazioni principali
  try {
    // Crea cartella pratica nell'Empireo
    const cartella = creaCartellaPratica(
      dati.cliente.trim(),
      dati.sito.trim(),
      dati.anno.toString().trim(),
      dati.pratica.trim()
    );

    // Sposta gli allegati dal Limbo nella cartella pratica appena creata.
    // Con inbox_id attivo usa l allegato esplicito del record inbox; senza
    // inbox_id mantiene il fallback legacy per i casi storici.
    const spostamento = inboxId
      ? _archiviaAllegatoVirgilioInbox_(
        inboxId,
        dati.cliente,
        dati.sito,
        cartella.id,
        cartella.url
      )
      : _spostaAllegatiDalLimbo(
        dati.cliente,
        dati.sito,
        cartella.id
      );

    // Avvisa il team su Chat e Telegram
    avvisaTeam(
      dati.cliente,
      dati.sito,
      dati.pratica,
      dati.anno,
      dati.tecnici || [],
      dati.note    || '',
      cartella.url
    );

    // Registra sulle Bucoliche
    registraSuBucoliche({
      origine:     dati.origine || 'form_virgilio',
      cliente:     dati.cliente,
      sito:        dati.sito,
      pratica:     dati.pratica,
      anno:        dati.anno,
      tecnici:     dati.tecnici || [],
      note:        dati.note    || '',
      urlCartella: cartella.url,
      idDrive:  cartella.id,
    });

    // Aggiorna le righe gmail_staging → gmail_archiviato (senza nuove righe duplicate)
    if (spostamento.fileIds.length > 0) {
      aggiornaRigheAllegati(spostamento.fileIds, {
        cliente:     dati.cliente,
        sito:        dati.sito,
        pratica:     dati.pratica,
        anno:        dati.anno,
        urlCartella: cartella.url,
      });
    }

    Logger.log(`[Caronte] doPost — pratica aperta: ${dati.cliente} / ${dati.sito} / ${dati.anno}_${dati.pratica} (${spostamento.count} allegati dal Limbo)`);

    return _rispostaJSON({
      status:           'ok',
      cartella:         cartella.url,
      id:               cartella.id,
      allegatiSpostati: spostamento.count,
      inbox_id:         inboxId,
      inbox_status:     inboxLink && inboxLink.status ? inboxLink.status : '',
    });

  } catch (err) {
    Logger.log(`[Caronte] doPost — ERRORE: ${err.message}`);

    registraErrore('doPost', err.message, {
      cliente: dati.cliente,
      sito:    dati.sito,
      pratica: dati.pratica,
      anno:    dati.anno,
    });

    return _rispostaJSON({ status: 'error', messaggio: err.message });
  }
}


// ── MODULO 1B — BRIDGE INTERNO PER VIRGILIO SENZA DEPLOY ─────────────────────

/**
 * Apre una pratica partendo dai dati del form Virgilio eseguito come HtmlService.
 *
 * Serve per testare il form SENZA deploy pubblico:
 * l'HTML chiama questa funzione con google.script.run e questa funzione riusa doPost(),
 * simulando internamente la stessa chiamata JSON che arriverà poi da una Web App.
 *
 * @param {Object} dati - Dati raccolti dal form Virgilio.
 * @returns {Object} Risposta JSON parsata: {status, cartella, id, messaggio?}
 */
function apriPraticaDaVirgilio(dati) {
  dati = dati || {};

  const eventoFinto = {
    postData: {
      contents: JSON.stringify({
        token: CONFIG.VIRGILIO_TOKEN,
        cliente: dati.cliente || '',
        sito: dati.sito || '',
        pratica: dati.pratica || '',
        anno: dati.anno || new Date().getFullYear().toString(),
        tecnici: Array.isArray(dati.tecnici) ? dati.tecnici : [],
        note: dati.note || '',
        inbox_id: dati.inbox_id || '',
        origine: 'form_virgilio_interno'
      })
    }
  };

  const risposta = doPost(eventoFinto);
  return JSON.parse(risposta.getContent());
}

/**
 * Test server-side del form Virgilio, senza aprire l'interfaccia grafica.
 *
 * Eseguire da Apps Script: testVirgilioSenzaDeploy()
 * Verifica che il bridge apriPraticaDaVirgilio() funzioni e arrivi fino a Caronte.
 */
function testVirgilioSenzaDeploy() {
  Logger.log('--- TEST VIRGILIO SENZA DEPLOY ---');

  const risposta = apriPraticaDaVirgilio({
    cliente: '_TEST_CLIENTE_FORM_',
    sito: '_TEST_SITO_FORM_',
    pratica: 'assistenza',
    anno: new Date().getFullYear().toString(),
    tecnici: ['Test'],
    note: 'Test form Virgilio senza deploy — cartella da eliminare manualmente'
  });

  Logger.log(JSON.stringify(risposta, null, 2));

  if (!risposta || risposta.status !== 'ok') {
    throw new Error('Test Virgilio senza deploy fallito: ' + JSON.stringify(risposta));
  }

  Logger.log('✓ Virgilio senza deploy: pratica aperta correttamente');
  Logger.log('⚠ Eliminare la cartella di test "_TEST_CLIENTE_FORM_" dall\'Empireo');
}


// ── MODULO 2 — CREAZIONE CARTELLA PRATICA ─────────────────────────────────────

/**
 * Crea la struttura cartelle per una nuova pratica nell'Empireo.
 *
 * STRUTTURA CORRETTA:
 *
 * Empireo / Cliente / Sito /
 * ├─ 00_autorizzazioni
 * ├─ 01_dati-ditta
 * ├─ 02_corrispondenza
 * └─ Anno_Pratica
 *
 * Le tre cartelle documentali sono trasversali al sito:
 * NON vengono create dentro ogni singola pratica.
 *
 * @param {string} cliente - Ragione sociale cliente
 * @param {string} sito    - Sito/stabilimento
 * @param {string} anno    - Anno apertura pratica
 * @param {string} pratica - Tipo pratica, ad esempio "AUA"
 * @returns {{ id: string, url: string }}
 *   ID e URL della cartella pratica creata o già esistente
 */
function creaCartellaPratica(cliente, sito, anno, pratica) {
  // Apre Empireo.
  let empireo;

  try {
    empireo = DriveApp.getFolderById(CONFIG.EMPIREO_ID);
  } catch (err) {
    throw new Error(
      `[Caronte] Empireo non raggiungibile ` +
      `(ID: ${CONFIG.EMPIREO_ID}): ${err.message}`
    );
  }

  // Trova o crea la cartella del cliente.
  const cartellaCliente = _trovaOCrea(
    empireo,
    cliente
  );

  Logger.log(
    `[Caronte] Cartella cliente: "${cliente}"`
  );

  // Trova o crea la cartella del sito.
  const cartellaSito = _trovaOCrea(
    cartellaCliente,
    sito
  );

  Logger.log(
    `[Caronte] Cartella sito: "${sito}"`
  );

  // PATCH STRUTTURA:
  // Crea o verifica le cartelle trasversali direttamente
  // dentro la cartella del sito.
  //
  // La funzione è idempotente:
  // se le cartelle esistono già, non le duplica.
  _assicuraStrutturaTrasversaleSito(
    cartellaSito
  );

  // Nome della cartella relativa alla singola pratica.
  const nomePratica = `${anno}_${pratica}`;

  // Se la pratica esiste già, restituisce quella esistente.
  const esistenti =
    cartellaSito.getFoldersByName(nomePratica);

  if (esistenti.hasNext()) {
    const esistente = esistenti.next();

    Logger.log(
      `[Caronte] AVVISO — cartella pratica già esistente: ` +
      `"${nomePratica}" — restituita quella esistente`
    );

    return {
      id: esistente.getId(),
      url: esistente.getUrl()
    };
  }

  // PATCH STRUTTURA:
  // La singola pratica viene creata come cartella autonoma e vuota,
  // allo stesso livello delle cartelle trasversali.
  const cartellaPratica =
    cartellaSito.createFolder(nomePratica);

  Logger.log(
    `[Caronte] Cartella pratica creata: ` +
    `"${nomePratica}" (ID: ${cartellaPratica.getId()})`
  );

  return {
    id: cartellaPratica.getId(),
    url: cartellaPratica.getUrl()
  };
}


/**
 * Verifica e completa la struttura trasversale del sito.
 *
 * Le cartelle contenute nel template Adamo vengono copiate
 * DIRETTAMENTE dentro la cartella del sito.
 *
 * La funzione non crea duplicati:
 * - se una cartella esiste già, la mantiene;
 * - se manca, la crea;
 * - se Adamo non è disponibile, usa CONFIG.SOTTOCARTELLE_DEFAULT.
 *
 * Eventuali file presenti direttamente dentro Adamo vengono copiati
 * nella cartella del sito solo se non esiste già un file con lo stesso nome.
 *
 * @param {GoogleAppsScript.Drive.Folder} cartellaSito
 *   Cartella del sito nella quale creare la struttura trasversale
 */
function _assicuraStrutturaTrasversaleSito(cartellaSito) {
  try {
    const adamo =
      DriveApp.getFolderById(CONFIG.ADAMO_ID);

    // Copia le sotto-cartelle trasversali di Adamo dentro il sito.
    const sottoCartelle = adamo.getFolders();

    while (sottoCartelle.hasNext()) {
      const cartellaTemplate =
        sottoCartelle.next();

      _trovaOCrea(
        cartellaSito,
        cartellaTemplate.getName()
      );
    }

    // Copia gli eventuali file presenti direttamente in Adamo.
    // Non duplica file già esistenti con lo stesso nome.
    const files = adamo.getFiles();

    while (files.hasNext()) {
      const fileTemplate = files.next();
      const stessoNome =
        cartellaSito.getFilesByName(
          fileTemplate.getName()
        );

      if (!stessoNome.hasNext()) {
        fileTemplate.makeCopy(
          fileTemplate.getName(),
          cartellaSito
        );
      }
    }

    Logger.log(
      `[Caronte] Struttura trasversale verificata nel sito: ` +
      `"${cartellaSito.getName()}"`
    );

  } catch (err) {
    // Fallback:
    // se Adamo non è disponibile, crea almeno le cartelle standard.
    Logger.log(
      `[Caronte] AVVISO — Adamo non disponibile ` +
      `(${err.message}) — uso struttura default`
    );

    CONFIG.SOTTOCARTELLE_DEFAULT.forEach(
      nome => _trovaOCrea(cartellaSito, nome)
    );

    Logger.log(
      `[Caronte] Struttura trasversale default verificata nel sito: ` +
      `"${cartellaSito.getName()}"`
    );
  }
}


// ── MODULO 5 — POLLING GMAIL ──────────────────────────────────────────────────

/**
 * Punto di ingresso del trigger temporale (ogni 5 minuti).
 * Scansiona le caselle Gmail degli utenti configurati,
 * trova le mail etichettate "da-traghettare" e deposita
 * gli allegati reali nel Limbo (staging area).
 *
 * NON crea cartelle pratica — quella operazione avviene solo via doPost().
 */
function caronteTraghetta() {
  let totaleAllegati = 0;

  for (const utente of CONFIG.UTENTI) {
    try {
      Logger.log(`[Caronte] Scansiono: ${utente}`);
      const n = _processaMailUtente(utente);
      totaleAllegati += n;
    } catch (err) {
      Logger.log(`[Caronte] ERRORE su ${utente}: ${err.message}`);
      registraErrore('caronteTraghetta', err.message, { cliente: utente });
    }
  }

  Logger.log(`[Caronte] Elaborazione completata — ${totaleAllegati} allegati traghettati nel Limbo.`);
}


/**
 * Analizza tutte le mail etichettate "da-traghettare"
 * nella casella Gmail dell'utente che esegue lo script.
 *
 * Per ogni thread:
 * - esamina tutti i messaggi;
 * - salva nel Limbo gli allegati validi;
 * - registra ogni file nelle Bucoliche;
 * - invia una notifica riepilogativa;
 * - sostituisce l'etichetta Gmail SOLO se almeno un allegato
 *   è stato effettivamente salvato.
 *
 * @param {string} utente
 *   Indirizzo dell'utente, usato nei log e nelle notifiche.
 *
 * @returns {number}
 *   Numero totale di allegati salvati nel Limbo.
 */
function _processaMailUtente(utente) {
  // Usa le virgolette intorno all'etichetta Gmail.
  // È più robusto con etichette contenenti trattini o spazi.
  const threads = GmailApp.search(
    `label:"${CONFIG.ETICHETTA_TRIGGER}"`
  );

  if (threads.length === 0) {
    Logger.log(
      `[Caronte] Nessuna mail da traghettare per ${utente}`
    );

    return 0;
  }

  Logger.log(
    `[Caronte] ${threads.length} thread trovati per ${utente}`
  );

  let contatoreAllegati = 0;
  const dettagliNotifica = [];
  const limbo = _apriLimbo();

  for (const thread of threads) {
    const messaggi = thread.getMessages();

    // PATCH PRINCIPALE:
    // Conteggia quanti allegati validi sono stati effettivamente
    // salvati per questo specifico thread Gmail.
    //
    // Serve per evitare che una mail venga marcata come "traghettata"
    // quando non contiene allegati utili oppure quando il salvataggio
    // fallisce.
    let allegatiSalvatiNelThread = 0;

    for (const messaggio of messaggi) {
      const allegati = messaggio.getAttachments();
      const nomiFileMessaggio = [];

      for (const allegato of allegati) {
        // Filtra firme, immagini incorporate, file di servizio
        // e allegati troppo piccoli.
        if (!èAllegatoReale(allegato)) {
          Logger.log(
            `[Caronte] Scartato: ${allegato.getName()} (non reale)`
          );

          continue;
        }

        // Scarta allegati superiori al limite configurato.
        const dimensioneMB =
          allegato.getSize() / (1024 * 1024);

        if (dimensioneMB > CONFIG.MAX_ALLEGATO_MB) {
          Logger.log(
            `[Caronte] Scartato: ${allegato.getName()} ` +
            `(${dimensioneMB.toFixed(1)} MB — troppo grande)`
          );

          registraErrore(
            'caronteTraghetta',
            `Allegato troppo grande: ${allegato.getName()} ` +
            `(${dimensioneMB.toFixed(1)} MB)`,
            {
              cliente: _estraiDominio(messaggio.getFrom())
            }
          );

          continue;
        }

        try {
          const fileId = _salvaAllegatoInLimbo(
            allegato,
            messaggio,
            limbo
          );

          // Estrae metadati per le colonne ML di Bucoliche
          const nomeFileOriginale = allegato.getName();
          const estensione = nomeFileOriginale.includes('.')
            ? nomeFileOriginale.split('.').pop().toLowerCase().substring(0, 10)
            : '';

          registraSuBucoliche({
            origine:          'gmail_staging',
            cliente:          '— in attesa —',
            sito:             '',
            pratica:          '',
            anno:             '',
            tecnici:          [],
            note:             '',
            urlCartella:      `https://drive.google.com/file/d/${fileId}`,
            idDrive:          fileId,
            // ── Campi ML ──
            mittenteDominio:  _estraiDominio(messaggio.getFrom()),
            oggettoEmail:     messaggio.getSubject().substring(0, 200),
            nomeFile:         nomeFileOriginale,
            estensione:       estensione,
            dimensioneKb:     Math.round(allegato.getSize() / 1024),
            stato:            'in_limbo',
            timestampArchiviazione: '',
          });

          nomiFileMessaggio.push(
            allegato.getName()
          );

          // Incrementa sia il totale generale
          // sia il conteggio del singolo thread.
          contatoreAllegati++;
          allegatiSalvatiNelThread++;

          Logger.log(
            `[Caronte] Traghettato nel Limbo: ${allegato.getName()}`
          );

        } catch (err) {
          Logger.log(
            `[Caronte] ERRORE su allegato ` +
            `"${allegato.getName()}": ${err.message}`
          );

          registraErrore(
            'caronteTraghetta',
            `${allegato.getName()}: ${err.message}`,
            {
              cliente: _estraiDominio(messaggio.getFrom())
            }
          );
        }
      }

      // Costruisce il dettaglio della notifica
      // soltanto se almeno un allegato del messaggio è stato salvato.
      if (nomiFileMessaggio.length > 0) {
        dettagliNotifica.push({
          mittente:
            _estraiDominio(messaggio.getFrom()),

          oggetto:
            messaggio.getSubject().substring(0, 80),

          nomiFile:
            nomiFileMessaggio,
        });
      }
    }

    // PATCH PRINCIPALE:
    // Cambia etichetta SOLO se almeno un allegato valido
    // del thread è arrivato effettivamente nel Limbo.
    if (allegatiSalvatiNelThread > 0) {
      _rimuoviEtichetta(
        thread,
        CONFIG.ETICHETTA_TRIGGER
      );

      _aggiungiEtichetta(
        thread,
        CONFIG.ETICHETTA_ELABORATA
      );

      Logger.log(
        `[Caronte] Thread elaborato: ` +
        `${allegatiSalvatiNelThread} allegati salvati`
      );

    } else {
      // La mail conserva l'etichetta "da-traghettare".
      // In questo modo resta visibile e può essere verificata manualmente.
      Logger.log(
        '[Caronte] Thread lasciato da verificare: ' +
        'nessun allegato valido salvato nel Limbo.'
      );
    }
  }

  // Invia una sola notifica riepilogativa
  // dopo aver elaborato tutti i thread.
  if (contatoreAllegati > 0) {
    _avvisaTraghettamento(
      contatoreAllegati,
      utente,
      dettagliNotifica
    );
  }

  return contatoreAllegati;
}

/**
 * Invia una notifica leggera al team dopo il traghettamento nel Limbo.
 * Delega la costruzione dei messaggi a notifiche.gs (avvisaTraghettamentoTeam)
 * che gestisce formati separati per Chat (Markdown) e Telegram (HTML+link).
 *
 * @param {number} totale       - Numero di allegati traghettati
 * @param {string} utente       - Casella Gmail che ha generato il traghettamento
 * @param {Array}  dettagliMail - Array di {mittente, oggetto, nomiFile[]}
 */
function _avvisaTraghettamento(totale, utente, dettagliMail) {
  try {
    avvisaTraghettamentoTeam(totale, dettagliMail);
    Logger.log(`[Caronte] Notifica traghettamento inviata (${totale} allegati)`);
  } catch (err) {
    Logger.log(`[Caronte] AVVISO — notifica traghettamento fallita: ${err.message}`);
  }
}


/**
 * Salva un allegato nella cartella Limbo con nome prefissato.
 * Formato nome: AAAA-MM-GG_[dominio-mittente]_[nome-originale]
 *
 * @param {GoogleAppsScript.Gmail.GmailAttachment} allegato
 * @param {GoogleAppsScript.Gmail.GmailMessage}    messaggio
 * @param {GoogleAppsScript.Drive.Folder}          limbo
 * @returns {string} ID del file creato su Drive
 */
function _salvaAllegatoInLimbo(allegato, messaggio, limbo) {
  const data         = Utilities.formatDate(new Date(), 'Europe/Rome', 'yyyy-MM-dd');
  const dominio      = _estraiDominio(messaggio.getFrom());
  const nomeOriginale = allegato.getName();
  const idMessaggio = messaggio.getId().substring(0, 10);
  const nomeFile = `${data}_${dominio}_${idMessaggio}_${_sanitizzaNomeFile(nomeOriginale)}`;

  const blob = allegato.copyBlob().setName(nomeFile);
  const file = limbo.createFile(blob);

  return file.getId();
}


// ── MODULO 6 — FILTRO ALLEGATI ────────────────────────────────────────────────

/**
 * Determina se un allegato è un documento reale o va scartato.
 * Scarta immagini di firma, file di servizio, allegati crittografici.
 *
 * @param {GoogleAppsScript.Gmail.GmailAttachment} allegato
 * @returns {boolean} true se l'allegato è reale, false se va scartato
 */
function èAllegatoReale(allegato) {
  const nome        = allegato.getName().toLowerCase();
  const dimensione  = allegato.getSize();
  const contentType = allegato.getContentType().toLowerCase();

  // Scarta allegati troppo piccoli (< 5KB)
  if (dimensione < 5 * 1024) return false;

  // Scarta immagini piccole (tipicamente firme email < 50KB)
  const èImmagine = ['image/png', 'image/jpeg', 'image/gif', 'image/jpg'].includes(contentType);
  if (èImmagine && dimensione < 50 * 1024) return false;

  // Scarta per nome (pattern firme e loghi)
  const patternDaScartare = [
    /^image\d+\./i,      // image001.png, image002.jpg
    /^logo\./i,          // logo.png
    /^signature\./i,     // signature.png
    /^firma\./i,         // firma.jpg
    /^icon\./i,          // icon.gif
  ];
  if (patternDaScartare.some(p => p.test(nome))) return false;

  // Scarta file crittografici di firma email
  if (nome.endsWith('.p7s') || nome.endsWith('.smime')) return false;

  return true;
}


// ── HELPERS GMAIL ─────────────────────────────────────────────────────────────

/**
 * Rimuove un'etichetta da un thread Gmail.
 * Fail silenzioso se l'etichetta non esiste.
 *
 * @param {GoogleAppsScript.Gmail.GmailThread} thread
 * @param {string} nomeEtichetta
 */
function _rimuoviEtichetta(thread, nomeEtichetta) {
  try {
    const etichetta = GmailApp.getUserLabelByName(nomeEtichetta);
    if (etichetta) etichetta.removeFromThread(thread);
  } catch (err) {
    Logger.log(`[Caronte] Impossibile rimuovere etichetta "${nomeEtichetta}": ${err.message}`);
  }
}


/**
 * Aggiunge un'etichetta a un thread Gmail.
 * Crea l'etichetta automaticamente se non esiste.
 *
 * @param {GoogleAppsScript.Gmail.GmailThread} thread
 * @param {string} nomeEtichetta
 */
function _aggiungiEtichetta(thread, nomeEtichetta) {
  try {
    let etichetta = GmailApp.getUserLabelByName(nomeEtichetta);
    if (!etichetta) {
      etichetta = GmailApp.createLabel(nomeEtichetta);
      Logger.log(`[Caronte] Etichetta creata: "${nomeEtichetta}"`);
    }
    etichetta.addToThread(thread);
  } catch (err) {
    Logger.log(`[Caronte] Impossibile aggiungere etichetta "${nomeEtichetta}": ${err.message}`);
  }
}


// ── HELPERS DRIVE ─────────────────────────────────────────────────────────────

/**
 * Trova una sotto-cartella per nome dentro parent.
 * Se non esiste, la crea.
 *
 * @param {GoogleAppsScript.Drive.Folder} parent
 * @param {string} nome
 * @returns {GoogleAppsScript.Drive.Folder}
 */
function _trovaOCrea(parent, nome) {
  const iter = parent.getFoldersByName(nome);
  if (iter.hasNext()) return iter.next();
  Logger.log(`[Caronte] Creo cartella: "${nome}"`);
  return parent.createFolder(nome);
}



/**
 * Cerca la cartella trasversale 02_corrispondenza
 * allo stesso livello della cartella pratica.
 *
 * STRUTTURA:
 *
 * Sito /
 * ├─ 02_corrispondenza
 * └─ 2026_PEE
 *
 * Se 02_corrispondenza non esiste, la crea.
 *
 * @param {string} idCartellaPratica
 *   ID della cartella relativa alla singola pratica
 *
 * @returns {GoogleAppsScript.Drive.Folder}
 *   Cartella trasversale 02_corrispondenza
 */
function _trovaCartellaCorrispondenza(idCartellaPratica) {
  const cartellaPratica =
    DriveApp.getFolderById(idCartellaPratica);

  const parents =
    cartellaPratica.getParents();

  if (!parents.hasNext()) {
    throw new Error(
      `[Caronte] Impossibile risalire alla cartella del sito ` +
      `dalla pratica ID: ${idCartellaPratica}`
    );
  }

  const cartellaSito =
    parents.next();

  return _trovaOCrea(
    cartellaSito,
    '02_corrispondenza'
  );
}


/**
 * Apre la cartella Limbo. Errore bloccante se non raggiungibile.
 *
 * @returns {GoogleAppsScript.Drive.Folder}
 */
function _apriLimbo() {
  try {
    return DriveApp.getFolderById(CONFIG.LIMBO_ID);
  } catch (err) {
    throw new Error(`[Caronte] Limbo non raggiungibile (ID: ${CONFIG.LIMBO_ID}): ${err.message}`);
  }
}

function _archiviaAllegatoVirgilioInbox_(inboxId, cliente, sito, idCartellaPratica, urlCartellaPratica) {
  const inbox = caronteGetVirgilioInboxForArchive(inboxId);
  if (!inbox || inbox.ok !== true || !inbox.found) {
    throw new Error(
      inbox && inbox.message
        ? inbox.message
        : 'Record Virgilio_Inbox non disponibile per l archiviazione finale.'
    );
  }
  if (!inbox.drive_file_id) {
    throw new Error('drive_file_id mancante nel record Virgilio_Inbox.');
  }

  const corrispondenza = _trovaCartellaCorrispondenza(idCartellaPratica);
  const file = DriveApp.getFileById(inbox.drive_file_id);
  const destinationFolderId = corrispondenza.getId();
  const alreadyInDestination = _cartellaContieneFileId_(corrispondenza, file.getId());

  if (!alreadyInDestination) {
    file.moveTo(corrispondenza);
    Logger.log(
      `[Caronte] Spostato inbox ${inboxId} in 02_corrispondenza: ${file.getName()}`
    );
  } else {
    Logger.log(
      `[Caronte] Inbox ${inboxId} gia presente in 02_corrispondenza: ${file.getName()}`
    );
  }

  const archived = caronteArchiviaVirgilioInbox({
    inbox_id: inboxId,
    archived_at: _timestampLocale(),
    archived_file_id: file.getId(),
    destination_folder_id: destinationFolderId,
    destination_folder_url: corrispondenza.getUrl(),
    pratica_folder_id: idCartellaPratica,
    pratica_folder_url: urlCartellaPratica,
  });
  if (!archived || archived.ok !== true) {
    throw new Error(
      archived && archived.message
        ? archived.message
        : 'Aggiornamento finale Virgilio_Inbox non riuscito.'
    );
  }

  return { count: 1, fileIds: [file.getId()] };
}

function _cartellaContieneFileId_(folder, fileId) {
  const files = folder.getFiles();
  while (files.hasNext()) {
    if (files.next().getId() === fileId) return true;
  }
  return false;
}


/**
 * Estrae il dominio da un indirizzo email.
 * Es: "Mario Rossi <mario@cliente.it>" → "cliente"
 *
 * @param {string} mittente
 * @returns {string}
 */
function _estraiDominio(mittente) {
  const match = mittente.match(/@([^.>]+)/);
  return match ? match[1] : 'sconosciuto';
}


// ── HELPER RISPOSTA ───────────────────────────────────────────────────────────

/**
 * Costruisce una risposta JSON per doPost().
 *
 * @param {Object} obj - Oggetto da serializzare
 * @returns {GoogleAppsScript.Content.TextOutput}
 */
function _rispostaJSON(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Sanitizza il nome di un file rimuovendo caratteri problematici.
 * Previene path traversal, nomi illegali su Drive, anomalie nei log.
 *
 * @param {string} nome - Nome file originale dall'allegato email
 * @returns {string} Nome file sicuro
 */
function _sanitizzaNomeFile(nome) {
  return String(nome || 'allegato')
    .replace(/[\/\\:*?"<>|]/g, '_')   // caratteri vietati nei nomi file
    .replace(/\.{2,}/g, '.')              // sequenze di punti multipli
    .replace(/\s+/g, '_')                 // spazi → underscore
    .substring(0, 150);                    // lunghezza massima ragionevole
}


// ── SMISTAMENTO LIMBO → CARTELLA PRATICA ─────────────────────────────────────

/**
 * Sposta gli allegati recenti dal Limbo nella cartella trasversale
 * 02_corrispondenza del sito.
 *
 * STRUTTURA DI DESTINAZIONE:
 *
 * Cliente / Sito /
 * ├─ 02_corrispondenza
 * └─ Anno_Pratica
 *
 * Gli allegati NON vengono inseriti dentro la cartella pratica.
 *
 * Il criterio resta volutamente semplice:
 * vengono spostati tutti i file recenti presenti nel Limbo.
 *
 * @param {string} cliente
 *   Nome cliente, utilizzato nei log
 *
 * @param {string} sito
 *   Nome sito, utilizzato nei log
 *
 * @param {string} idCartellaPratica
 *   ID della cartella pratica appena creata
 *
 * @returns {number}
 *   Numero di allegati spostati
 */
function _spostaAllegatiDalLimbo(
  cliente,
  sito,
  idCartellaPratica
) {
  try {
    const limbo =
      DriveApp.getFolderById(CONFIG.LIMBO_ID);

    // PATCH STRUTTURA:
    // Risale dalla pratica alla cartella del sito
    // e trova la cartella trasversale 02_corrispondenza.
    const corrispondenza =
      _trovaCartellaCorrispondenza(
        idCartellaPratica
      );

    // Finestra temporale prudenziale.
    //
    // Consiglio:
    // aggiungere GIORNI_LIMBO_DA_SPOSTARE: 2 in CONFIG.
    //
    // Se il parametro non esiste ancora, usa 2 giorni.
    const giorni =
      CONFIG.GIORNI_LIMBO_DA_SPOSTARE || 2;

    const soglia =
      new Date(
        Date.now() -
        giorni * 24 * 60 * 60 * 1000
      );

    const files =
      limbo.getFiles();

    let spostati = 0;
    const fileIdsSpostati = [];

    while (files.hasNext()) {
      const file =
        files.next();

      // Usa la data reale di creazione del file Drive.
      // È più robusto rispetto al confronto basato sul nome file.
      if (file.getDateCreated() >= soglia) {
        const fid = file.getId();   // cattura ID prima di spostare
        file.moveTo(corrispondenza);
        fileIdsSpostati.push(fid);
        spostati++;

        Logger.log(
          `[Caronte] Spostato in 02_corrispondenza: ` +
          `${file.getName()}`
        );
      }
    }

    if (spostati === 0) {
      Logger.log(
        `[Caronte] Nessun allegato recente nel Limbo per: ` +
        `${cliente} / ${sito}`
      );
    }

    return { count: spostati, fileIds: fileIdsSpostati };

  } catch (err) {
    Logger.log(
      `[Caronte] AVVISO — spostamento Limbo fallito: ` +
      `${err.message}`
    );

    return { count: 0, fileIds: [] };
  }
}

function testCaronteInboxArchiviazione() {
  const movedFile = {
    id: 'drive-1',
    name: 'analisi.pdf',
    movedTo: '',
    getId: function() { return this.id; },
    getName: function() { return this.name; },
    moveTo: function(folder) { this.movedTo = folder.getId(); }
  };
  const destinationFiles = [];
  const destinationFolder = {
    getId: () => 'folder-corrispondenza',
    getUrl: () => 'https://drive.google.com/drive/folders/folder-corrispondenza',
    getFiles: () => {
      const values = destinationFiles.slice();
      return { hasNext: () => values.length > 0, next: () => values.shift() };
    }
  };
  const archiveCalls = [];
  const result = _archiviaAllegatoVirgilioInboxWithDeps_({
    inboxId: 'inbox-1',
    cliente: 'Cliente Demo',
    sito: 'Sito Demo',
    idCartellaPratica: 'folder-pratica',
    urlCartellaPratica: 'https://drive.google.com/drive/folders/folder-pratica',
    getInbox: () => ({ ok: true, found: true, drive_file_id: 'drive-1' }),
    getFolder: () => destinationFolder,
    driveApp: { getFileById: () => movedFile },
    archiveInbox: payload => {
      archiveCalls.push(payload);
      return { ok: true };
    },
    nowTimestamp: () => '2026-07-01 20:10:00',
  });
  _driveStagingAssert_(result.count === 1 && result.fileIds[0] === 'drive-1',
    'archiviazione inbox restituisce file spostato');
  _driveStagingAssert_(movedFile.movedTo === 'folder-corrispondenza',
    'archiviazione inbox sposta il file nella corrispondenza');
  _driveStagingAssert_(archiveCalls.length === 1 && archiveCalls[0].destination_folder_id === 'folder-corrispondenza',
    'archiviazione inbox aggiorna il record Virgilio_Inbox');
  Logger.log('testCaronteInboxArchiviazione: OK');
}

function _archiviaAllegatoVirgilioInboxWithDeps_(deps) {
  const inbox = deps.getInbox(deps.inboxId);
  if (!inbox || inbox.ok !== true || !inbox.found) {
    throw new Error(
      inbox && inbox.message
        ? inbox.message
        : 'Record Virgilio_Inbox non disponibile per l archiviazione finale.'
    );
  }
  if (!inbox.drive_file_id) {
    throw new Error('drive_file_id mancante nel record Virgilio_Inbox.');
  }

  const corrispondenza = deps.getFolder(
    deps.idCartellaPratica,
    deps.cliente,
    deps.sito
  );
  const file = deps.driveApp.getFileById(inbox.drive_file_id);
  const destinationFolderId = corrispondenza.getId();
  const alreadyInDestination = _cartellaContieneFileId_(corrispondenza, file.getId());

  if (!alreadyInDestination) {
    file.moveTo(corrispondenza);
  }

  const archived = deps.archiveInbox({
    inbox_id: deps.inboxId,
    archived_at: deps.nowTimestamp(),
    archived_file_id: file.getId(),
    destination_folder_id: destinationFolderId,
    destination_folder_url: corrispondenza.getUrl(),
    pratica_folder_id: deps.idCartellaPratica,
    pratica_folder_url: deps.urlCartellaPratica,
  });
  if (!archived || archived.ok !== true) {
    throw new Error(
      archived && archived.message
        ? archived.message
        : 'Aggiornamento finale Virgilio_Inbox non riuscito.'
    );
  }

  return { count: 1, fileIds: [file.getId()] };
}

// ── VALIDAZIONE INPUT ─────────────────────────────────────────────────────────

/**
 * Verifica che i campi del payload non superino le lunghezze massime consentite.
 * Previene log overflow, nomi file anomali, e abusi del registro Bucoliche.
 *
 * @param {Object} dati - Payload ricevuto da doPost()
 * @throws {Error} se un campo supera il limite
 */
function _validaLunghezze(dati) {
  const LIMITI = {
    cliente: 100,
    sito:    100,
    note:    500,
    anno:    4,
  };

  for (const [campo, max] of Object.entries(LIMITI)) {
    if (dati[campo] && dati[campo].toString().length > max) {
      throw new Error(`Campo "${campo}" supera i ${max} caratteri consentiti.`);
    }
  }
}


// ── RATE LIMITING ─────────────────────────────────────────────────────────────

/**
 * Verifica che non arrivino più di una richiesta ogni 10 secondi.
 * Protegge da flooding accidentale o intenzionale sull'endpoint doPost().
 * Usa CacheService con scope script (condiviso tra tutte le esecuzioni).
 *
 * @throws {Error} se la richiesta arriva troppo presto dopo la precedente
 */
function _verificaRateLimit() {
  const cache   = CacheService.getScriptCache();
  const chiave  = 'virgilio_last_dopost';
  const adesso  = Date.now();
  const ultimaStr = cache.get(chiave);

  if (ultimaStr) {
    const secondiPassati = (adesso - parseInt(ultimaStr)) / 1000;
    if (secondiPassati < 10) {
      throw new Error(
        `Rate limit: attendere ${Math.ceil(10 - secondiPassati)} secondi prima di aprire un\'altra pratica.`
      );
    }
  }

  // Registra timestamp corrente, valido per 60 secondi
  cache.put(chiave, adesso.toString(), 60);
}

