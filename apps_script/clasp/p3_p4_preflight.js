/** Read-only preflight for unattended P3/P4 sessions. */

const P3P4_PRACTICE_STATE = 'archiviato_pratica';
const P3P4_CORRISPONDENZA_FOLDER = '02_corrispondenza';
const DRIVE_STAGING_P3P4_PREFLIGHT_ACTION = 'preflight_drive_staging_p3_p4';

function carontePreflightP3P4(options) {
  const validation = _p3p4ValidateOptions_(options);
  if (!validation.ok) return validation.response;

  const snapshot = {
    attachment_id: options.attachment_id,
    staged_filename: options.staged_filename,
    practice_folder_id: options.practice_folder_id,
    checks: {},
    blocking_errors: [],
    warnings: []
  };

  try {
    const folderId = PropertiesService.getScriptProperties()
      .getProperty(DRIVE_STAGING_FOLDER_PROPERTY);
    if (!folderId) {
      snapshot.blocking_errors.push(_driveStagingError_(
        'STAGING_FOLDER_NOT_CONFIGURED',
        'Configurare VIRGILIO_DRIVE_STAGING_FOLDER_ID prima delle sessioni notturne.'
      ));
    } else {
      const stagingFolder = DriveApp.getFolderById(folderId);
      const payload = Object.assign({}, options, {
        action: DRIVE_STAGING_NOTIFY_ACTION,
        test_mode: false,
        connector_type: options.connector_type || 'local_imap',
        account_alias: options.account_alias || '',
        source_message_id: options.source_message_id || '',
        source_message_uid: options.source_message_uid || '',
        original_filename: options.original_filename || '',
        mime_type: options.mime_type || 'application/octet-stream',
        scan_engine: options.scan_engine || 'unknown',
        scan_result: options.scan_result || 'unknown',
        quarantine_status: options.quarantine_status || 'ready_for_caronte',
        note: options.note || ''
      });
      const checked = _intakeTestInspectFolder_(payload, stagingFolder);
      snapshot.checks.staging = {
        folder_id: folderId,
        drive_file_found: Boolean(checked.staged && checked.staged.file),
        manifest_found: Boolean(checked.manifestFile && checked.manifestFile.file),
        manifest_consistent: checked.ok === true
      };
      if (!checked.ok && checked.response && Array.isArray(checked.response.errors)) {
        snapshot.blocking_errors = snapshot.blocking_errors.concat(checked.response.errors);
      }
    }
  } catch (err) {
    snapshot.blocking_errors.push(_driveStagingError_(
      'STAGING_PREFLIGHT_FAILED',
      'Impossibile leggere la cartella staging Drive.'
    ));
  }

  try {
    const sheet = _aprifoglioBucoliche();
    const row = _trovaRigaBucolichePerAttachmentId_(sheet, options.attachment_id);
    if (row === 0) {
      snapshot.blocking_errors.push(_driveStagingError_(
        'BUCOLICHE_ROW_NOT_FOUND',
        'La riga Bucoliche non esiste: P1/P2 non risultano pronti.'
      ));
    } else {
      const note = String(sheet.getRange(row, BUCOLICHE_COLS.note).getValue() || '');
      const state = String(sheet.getRange(row, BUCOLICHE_COLS.stato).getValue() || '').trim();
      const fileId = String(sheet.getRange(row, BUCOLICHE_COLS.id_drive).getValue() || '').trim();
      const url = String(sheet.getRange(row, BUCOLICHE_COLS.url_cartella).getValue() || '').trim();
      const p1Count = _p3p4CountMarker_(note, BUCOLICHE_ATTACHMENT_NOTE_PREFIX, options.attachment_id);
      const p2Count = _p3p4CountMarker_(note, DRIVE_STAGING_NOTIFY_NOTE_PREFIX, options.attachment_id);
      snapshot.checks.bucoliche = {
        row: row,
        state: state,
        drive_file_id: fileId,
        drive_url: url,
        p1_marker_count: p1Count,
        p2_marker_count: p2Count,
        p2_channels: _driveStagingNotifyChannelsFromNote_({
          getRange: () => ({ getValue: () => note })
        }, row)
      };
      if (state !== BUCOLICHE_LIMBO_STATE) {
        snapshot.blocking_errors.push(_driveStagingError_(
          'INVALID_BUCOLICHE_STATE',
          `La riga Bucoliche deve essere ${BUCOLICHE_LIMBO_STATE} prima di P3.`
        ));
      }
      if (p1Count !== 1) {
        snapshot.blocking_errors.push(_driveStagingError_(
          'P1_MARKER_COUNT_INVALID',
          'La nota Bucoliche deve contenere un solo marker P1.'
        ));
      }
      if (p2Count !== 1) {
        snapshot.blocking_errors.push(_driveStagingError_(
          'P2_MARKER_COUNT_INVALID',
          'La nota Bucoliche deve contenere un solo marker P2.'
        ));
      }
      if (!_p3p4NoteHasSha_(note, options.sha256)) {
        snapshot.blocking_errors.push(_driveStagingError_(
          'BUCOLICHE_SHA_MISMATCH',
          'La nota Bucoliche non conferma lo SHA-256 atteso.'
        ));
      }
    }
  } catch (err) {
    snapshot.blocking_errors.push(_driveStagingError_(
      'BUCOLICHE_PREFLIGHT_FAILED',
      'Impossibile leggere Bucoliche durante il preflight.'
    ));
  }

  try {
    const practice = DriveApp.getFolderById(options.practice_folder_id);
    const parents = practice.getParents();
    if (!parents.hasNext()) {
      snapshot.blocking_errors.push(_driveStagingError_(
        'PRACTICE_PARENT_MISSING',
        'La cartella pratica non ha parent navigabile.'
      ));
    } else {
      const siteFolder = parents.next();
      const matches = siteFolder.getFoldersByName(P3P4_CORRISPONDENZA_FOLDER);
      const found = [];
      while (matches.hasNext()) found.push(matches.next());
      snapshot.checks.practice = {
        practice_folder_id: practice.getId(),
        practice_folder_name: practice.getName(),
        site_folder_name: siteFolder.getName(),
        corrispondenza_count: found.length,
        corrispondenza_folder_id: found.length === 1 ? found[0].getId() : ''
      };
      if (typeof options.expected_practice_folder_name === 'string' &&
          options.expected_practice_folder_name.trim() &&
          practice.getName() !== options.expected_practice_folder_name.trim()) {
        snapshot.blocking_errors.push(_driveStagingError_(
          'PRACTICE_FOLDER_NAME_MISMATCH',
          'La cartella pratica reale non corrisponde al nome atteso del pilota.'
        ));
      }
      if (typeof options.expected_site_folder_name === 'string' &&
          options.expected_site_folder_name.trim() &&
          siteFolder.getName() !== options.expected_site_folder_name.trim()) {
        snapshot.blocking_errors.push(_driveStagingError_(
          'SITE_FOLDER_NAME_MISMATCH',
          'Il parent della pratica non corrisponde al sito atteso del pilota.'
        ));
      }
      if (found.length !== 1) {
        snapshot.blocking_errors.push(_driveStagingError_(
          'CORRISPONDENZA_FOLDER_INVALID',
          'La cartella 02_corrispondenza deve esistere una sola volta prima di P3.'
        ));
      } else if (typeof options.expected_corrispondenza_folder_id === 'string' &&
          options.expected_corrispondenza_folder_id.trim() &&
          found[0].getId() !== options.expected_corrispondenza_folder_id.trim()) {
        snapshot.blocking_errors.push(_driveStagingError_(
          'CORRISPONDENZA_FOLDER_ID_MISMATCH',
          'La cartella 02_corrispondenza trovata non corrisponde all ID atteso del pilota.'
        ));
      }
    }
  } catch (err) {
    snapshot.blocking_errors.push(_driveStagingError_(
      'PRACTICE_FOLDER_NOT_ACCESSIBLE',
      'La cartella pratica pilota non e leggibile con l identita Apps Script.'
    ));
  }

  try {
    const trigger = GmailApp.getUserLabelByName(CONFIG.ETICHETTA_TRIGGER);
    const done = GmailApp.getUserLabelByName(CONFIG.ETICHETTA_ELABORATA);
    snapshot.checks.gmail = {
      trigger_label: CONFIG.ETICHETTA_TRIGGER,
      trigger_exists: Boolean(trigger),
      done_label: CONFIG.ETICHETTA_ELABORATA,
      done_exists: Boolean(done)
    };
    if (!trigger) {
      snapshot.blocking_errors.push(_driveStagingError_(
        'TRIGGER_LABEL_MISSING',
        `La label Gmail ${CONFIG.ETICHETTA_TRIGGER} manca prima di P4.`
      ));
    }
    if (!done) {
      snapshot.blocking_errors.push(_driveStagingError_(
        'DONE_LABEL_MISSING',
        `La label Gmail ${CONFIG.ETICHETTA_ELABORATA} manca prima di P4.`
      ));
    }
  } catch (err) {
    snapshot.blocking_errors.push(_driveStagingError_(
      'GMAIL_PREFLIGHT_FAILED',
      'Impossibile leggere le label Gmail del pilota.'
    ));
  }

  return _p3p4EvaluateReadiness_(snapshot);
}

function caronteLogPreflightP3P4(options) {
  const result = carontePreflightP3P4(options);
  Logger.log(JSON.stringify(result, null, 2));
  return result;
}

function carontePreflightP3P4FromPayload(payload) {
  const validation = _p3p4ValidatePayload_(payload);
  if (!validation.ok) return validation.response;
  return carontePreflightP3P4(payload);
}

function caronteRunPilotPreflightP3P4() {
  return caronteLogPreflightP3P4({
    attachment_id: 'att-14-1-1-c005f6d2b696',
    staged_filename: 'att-14-1-1-c005f6d2b696-2026_25_CAMPEDELLI_MARMI_-_2_Acconto.pdf',
    sha256: 'c005f6d2b696e2cfa98ceecb24e1cc68706e4a270b94b7bd5847c6642ec6e35c',
    size_bytes: 309097,
    practice_folder_id: '1M6S4hmXDaMBiCPEXuR--z1V-f65djfpL',
    expected_practice_folder_name: '2026_AIA',
    expected_site_folder_name: 'San Pietro di Morubio',
    expected_corrispondenza_folder_id: '1eP8bmSskz40uhhnJETHKXBOBfKwawlAU',
    connector_type: 'local_imap',
    account_alias: 'gmail-test',
    source_message_id: '<8b2df824-a13a-4092-82cd-92b0749b84ec@gmail.com>',
    source_message_uid: '1',
    original_filename: '2026_25_CAMPEDELLI MARMI - 2 Acconto.pdf',
    mime_type: 'application/pdf',
    scan_engine: 'windows_defender',
    scan_result: 'clean',
    quarantine_status: 'ready_for_caronte',
    note: 'File copiato in cartella locale sincronizzata; sync cloud non verificata.'
  });
}

function _p3p4ValidateOptions_(options) {
  const errors = [];
  if (!options || typeof options !== 'object' || Array.isArray(options)) {
    errors.push(_driveStagingError_('INVALID_OPTIONS', 'Opzioni preflight non valide.'));
  } else {
    if (typeof options.attachment_id !== 'string' || !options.attachment_id.trim()) {
      errors.push(_driveStagingError_('INVALID_ATTACHMENT_ID', 'attachment_id obbligatorio.'));
    }
    if (typeof options.staged_filename !== 'string' || !options.staged_filename.trim()) {
      errors.push(_driveStagingError_('INVALID_STAGED_FILENAME', 'staged_filename obbligatorio.'));
    }
    if (typeof options.sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(options.sha256)) {
      errors.push(_driveStagingError_('INVALID_SHA256', 'sha256 obbligatorio e valido.'));
    }
    if (typeof options.practice_folder_id !== 'string' || !options.practice_folder_id.trim()) {
      errors.push(_driveStagingError_(
        'INVALID_PRACTICE_FOLDER_ID',
        'practice_folder_id obbligatorio per il preflight P3/P4.'
      ));
    }
    if (!Number.isInteger(options.size_bytes) || options.size_bytes < 0) {
      errors.push(_driveStagingError_('INVALID_SIZE', 'size_bytes obbligatorio e valido.'));
    }
  }
  return {
    ok: errors.length === 0,
    response: {
      ok: false,
      ready_for_p3: false,
      ready_for_p4: false,
      blocking_errors: errors,
      warnings: [],
      checks: {}
    }
  };
}

function _p3p4ValidatePayload_(payload) {
  const validation = _p3p4ValidateOptions_(payload);
  if (!validation.ok) return validation;
  const errors = [];
  if (payload.action !== DRIVE_STAGING_P3P4_PREFLIGHT_ACTION) {
    errors.push(_driveStagingError_('INVALID_ACTION', 'action non supportata.'));
  }
  if (payload.test_mode !== false) {
    errors.push(_driveStagingError_('TEST_MODE_MUST_BE_FALSE', 'test_mode deve essere false.'));
  }
  return {
    ok: errors.length === 0,
    response: {
      ok: false,
      ready_for_p3: false,
      ready_for_p4: false,
      blocking_errors: errors,
      warnings: [],
      checks: {}
    }
  };
}

function _p3p4EvaluateReadiness_(snapshot) {
  const readyForP3 = snapshot.blocking_errors.length === 0;
  const readyForP4 = readyForP3 &&
    snapshot.checks.gmail &&
    snapshot.checks.gmail.trigger_exists === true &&
    snapshot.checks.gmail.done_exists === true;
  return {
    ok: readyForP3,
    ready_for_p3: readyForP3,
    ready_for_p4: readyForP4,
    next_state_after_p3: readyForP3 ? P3P4_PRACTICE_STATE : '',
    attachment_id: snapshot.attachment_id,
    staged_filename: snapshot.staged_filename,
    practice_folder_id: snapshot.practice_folder_id,
    checks: snapshot.checks,
    blocking_errors: snapshot.blocking_errors,
    warnings: snapshot.warnings
  };
}

function _p3p4CountMarker_(note, prefix, attachmentId) {
  const exactPrefix = `${prefix} attachment_id=`;
  const marker = `attachment_id=${attachmentId}`;
  return String(note || '').split('\n')
    .filter(line => String(line || '').trim().startsWith(exactPrefix) && line.includes(marker)).length;
}

function _p3p4NoteHasSha_(note, sha256) {
  return String(note || '').includes(`sha256=${sha256}`);
}

/** Test puri della sola valutazione readiness; nessun accesso ai servizi reali. */
function testP3P4PreflightEvaluation() {
  const ready = _p3p4EvaluateReadiness_({
    attachment_id: 'att-test-1',
    staged_filename: 'att-test-1-document.pdf',
    practice_folder_id: 'practice-1',
    checks: {
      gmail: { trigger_exists: true, done_exists: true },
      practice: {
        practice_folder_name: '2026_AIA',
        site_folder_name: 'San Pietro di Morubio',
        corrispondenza_folder_id: 'corr-1'
      }
    },
    blocking_errors: [],
    warnings: []
  });
  _driveStagingAssert_(ready.ok && ready.ready_for_p3 && ready.ready_for_p4,
    'snapshot pronto');

  const blocked = _p3p4EvaluateReadiness_({
    attachment_id: 'att-test-1',
    staged_filename: 'att-test-1-document.pdf',
    practice_folder_id: 'practice-1',
    checks: { gmail: { trigger_exists: true, done_exists: false } },
    blocking_errors: [_driveStagingError_('X', 'errore')],
    warnings: []
  });
  _driveStagingAssert_(!blocked.ok && !blocked.ready_for_p3 && !blocked.ready_for_p4,
    'snapshot bloccato');
  const payloadValidation = _p3p4ValidatePayload_(Object.assign({
    action: DRIVE_STAGING_P3P4_PREFLIGHT_ACTION,
    test_mode: false
  }, {
    attachment_id: 'att-test-1',
    staged_filename: 'att-test-1-document.pdf',
    sha256: 'a'.repeat(64),
    size_bytes: 1,
    practice_folder_id: 'practice-1'
  }));
  _driveStagingAssert_(payloadValidation.ok, 'payload preflight valido');
  _driveStagingAssert_(_p3p4CountMarker_(
    '[virgilio_local_connector attachment_id=att-test-1]\n' +
    '[virgilio_local_connector_notify attachment_id=att-test-1]',
    '[virgilio_local_connector_notify', 'att-test-1'
  ) === 1, 'conteggio marker');
  _driveStagingAssert_(_p3p4CountMarker_(
    '[virgilio_local_connector attachment_id=att-test-1]\n' +
    '[virgilio_local_connector_notify attachment_id=att-test-1]',
    '[virgilio_local_connector', 'att-test-1'
  ) === 1, 'conteggio marker P1 esatto');
  Logger.log('testP3P4PreflightEvaluation: OK');
}
