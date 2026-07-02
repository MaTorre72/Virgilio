/** Idempotent P3 move from Drive staging to the pilot practice correspondence folder. */

const DRIVE_STAGING_PRACTICE_MOVE_ACTION = 'move_drive_staging_to_practice';
const BUCOLICHE_PRACTICE_STATE = 'archiviato_pratica';
const BUCOLICHE_ATTACHMENT_MOVE_NOTE_PREFIX = '[virgilio_local_connector_move';

function caronteSpostaStagingInPraticaPilota(payload) {
  const validation = _driveStagingPracticeMoveValidatePayload_(payload);
  if (!validation.ok) return validation.response;

  try {
    const sheet = _aprifoglioBucoliche();
    _assicuraIntestazione(sheet);
    const existingRow = _trovaRigaBucolichePerAttachmentId_(sheet, payload.attachment_id);
    if (existingRow === 0) {
      return _driveStagingPracticeMoveResponse_(
        payload, false, false, false, false, false, false, '', '', 0, '',
        'Riga Bucoliche non trovata per l attachment richiesto.', [
          _driveStagingError_('BUCOLICHE_ROW_NOT_FOUND',
            'Eseguire prima la registrazione P1 su Bucoliche reale.')
        ]
      );
    }

    const existingSha256 = _leggiSha256BucolicheRiga_(sheet, existingRow);
    if (existingSha256 !== payload.sha256) {
      return _driveStagingPracticeMoveResponse_(
        payload, false, false, false, false, false, false, '', '', existingRow, '',
        'attachment_id gia registrato in Bucoliche con SHA-256 differente.', [
          _driveStagingError_('ATTACHMENT_SHA256_CONFLICT',
            'Lo stesso attachment_id risulta associato a un SHA-256 diverso.')
        ]
      );
    }

    const target = _p3ResolvePracticeTarget_(payload);
    if (!target.ok) {
      return _driveStagingPracticeMoveResponse_(
        payload, false, false, false, false, false, false, '', '',
        existingRow, '', 'Cartella pratica pilota non valida.', target.errors
      );
    }

    const rowState = String(sheet.getRange(existingRow, BUCOLICHE_COLS.stato).getValue() || '').trim();
    const moveMarker = _p3LeggiMarkerSpostamento_(sheet, existingRow, payload.attachment_id);
    if (moveMarker.present && rowState === BUCOLICHE_PRACTICE_STATE) {
      return _driveStagingPracticeMoveResponse_(
        payload, true, false, true, true, false, true,
        moveMarker.moved_file_id || String(sheet.getRange(existingRow, BUCOLICHE_COLS.id_drive).getValue() || '').trim(),
        target.corrispondenzaFolder.getId(), existingRow, BUCOLICHE_PRACTICE_STATE,
        'Allegato gia spostato nella pratica pilota; nessun nuovo move.', []
      );
    }

    if (rowState !== BUCOLICHE_LIMBO_STATE) {
      return _driveStagingPracticeMoveResponse_(
        payload, false, false, false, false, false, false, '', '',
        existingRow, rowState, 'Stato Bucoliche non compatibile con P3.', [
          _driveStagingError_('INVALID_BUCOLICHE_STATE',
            'Lo spostamento P3 richiede stato limbo_registrato.')
        ]
      );
    }

    const preflight = carontePreflightP3P4(payload);
    if (!preflight || preflight.ready_for_p3 !== true) {
      return _driveStagingPracticeMoveResponse_(
        payload, false, false, false, false, false, false, '', '',
        existingRow, rowState, 'Preflight P3 non superato.', Array.isArray(preflight && preflight.blocking_errors)
          ? preflight.blocking_errors
          : [_driveStagingError_('P3_PREREQUISITES_INVALID',
            'Prerequisiti P3 non soddisfatti.')]
      );
    }

    const folderId = PropertiesService.getScriptProperties()
      .getProperty(DRIVE_STAGING_FOLDER_PROPERTY);
    if (!folderId) {
      return _driveStagingPracticeMoveResponse_(
        payload, false, false, false, false, false, false, '', '',
        existingRow, rowState, 'Cartella staging Drive non configurata.', [
          _driveStagingError_('STAGING_FOLDER_NOT_CONFIGURED',
            'Configurare VIRGILIO_DRIVE_STAGING_FOLDER_ID nelle Script Properties.')
        ]
      );
    }

    const stagingFolder = DriveApp.getFolderById(folderId);
    const checked = _intakeTestInspectFolder_(payload, stagingFolder);
    if (!checked.ok) {
      return _driveStagingPracticeMoveResponse_(
        payload, false,
        Boolean(checked.staged && checked.staged.file),
        Boolean(checked.manifestFile && checked.manifestFile.file),
        checked.ok === true,
        false, false, '', '', existingRow, rowState,
        'Validazione staging non superata.', checked.response && Array.isArray(checked.response.errors)
          ? checked.response.errors : []
      );
    }

    const movedFile = checked.staged.file;
    movedFile.moveTo(target.corrispondenzaFolder);
    _aggiornaRigaBucolichePerP3_(sheet, existingRow, movedFile, payload, target);

    return _driveStagingPracticeMoveResponse_(
      payload, true, true, true, true, true, false,
      movedFile.getId(), target.corrispondenzaFolder.getId(), existingRow,
      BUCOLICHE_PRACTICE_STATE,
      'Allegato spostato nella pratica pilota e Bucoliche aggiornate.', []
    );
  } catch (err) {
    return _driveStagingPracticeMoveResponse_(
      payload, false, false, false, false, false, false, '', '', 0, '',
      'Spostamento P3 non completato.', [
        _driveStagingError_('PRACTICE_MOVE_FAILED',
          'Lettura staging, move Drive o update Bucoliche non riusciti.')
      ]
    );
  }
}

function _driveStagingPracticeMoveValidatePayload_(payload) {
  const errors = [];
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    errors.push(_driveStagingError_('INVALID_PAYLOAD', 'Payload non valido.'));
  } else {
    if (payload.action !== DRIVE_STAGING_PRACTICE_MOVE_ACTION) {
      errors.push(_driveStagingError_('INVALID_ACTION', 'action non supportata.'));
    }
    if (payload.test_mode !== false) {
      errors.push(_driveStagingError_('TEST_MODE_MUST_BE_FALSE', 'test_mode deve essere false.'));
    }
    const required = ['connector_type', 'account_alias', 'attachment_id',
      'original_filename', 'staged_filename', 'sha256', 'mime_type',
      'scan_engine', 'scan_result', 'quarantine_status', 'practice_folder_id'];
    required.forEach(name => {
      if (typeof payload[name] !== 'string' || !payload[name].trim()) {
        errors.push(_driveStagingError_('INVALID_FIELD', `${name} non valido.`));
      }
    });
    if (!Number.isInteger(payload.size_bytes) || payload.size_bytes < 0) {
      errors.push(_driveStagingError_('INVALID_SIZE', 'size_bytes non valido.'));
    }
    if (typeof payload.staged_filename === 'string' && /[\\/]/.test(payload.staged_filename)) {
      errors.push(_driveStagingError_('INVALID_STAGED_FILENAME', 'staged_filename non valido.'));
    }
    if (typeof payload.sha256 === 'string' && !/^[0-9a-f]{64}$/.test(payload.sha256)) {
      errors.push(_driveStagingError_('INVALID_SHA256', 'sha256 non valido.'));
    }
  }
  return {
    ok: errors.length === 0,
    response: errors.length === 0 ? null : _driveStagingPracticeMoveResponse_(
      payload || {}, false, false, false, false, false, false, '', '', 0, '',
      'Richiesta spostamento P3 rifiutata.', errors
    )
  };
}

function _p3ResolvePracticeTarget_(payload) {
  try {
    const practiceFolder = DriveApp.getFolderById(payload.practice_folder_id);
    const siteParents = practiceFolder.getParents();
    if (!siteParents.hasNext()) {
      return {
        ok: false,
        errors: [_driveStagingError_(
          'PRACTICE_PARENT_MISSING',
          'La cartella pratica non ha parent navigabile.'
        )]
      };
    }
    const siteFolder = siteParents.next();
    const customerParents = siteFolder.getParents();
    const customerFolder = customerParents.hasNext() ? customerParents.next() : null;
    const matches = siteFolder.getFoldersByName(P3P4_CORRISPONDENZA_FOLDER);
    const found = [];
    while (matches.hasNext()) found.push(matches.next());
    const errors = [];
    if (typeof payload.expected_practice_folder_name === 'string' &&
        payload.expected_practice_folder_name.trim() &&
        practiceFolder.getName() !== payload.expected_practice_folder_name.trim()) {
      errors.push(_driveStagingError_(
        'PRACTICE_FOLDER_NAME_MISMATCH',
        'La cartella pratica reale non corrisponde al nome atteso del pilota.'
      ));
    }
    if (typeof payload.expected_site_folder_name === 'string' &&
        payload.expected_site_folder_name.trim() &&
        siteFolder.getName() !== payload.expected_site_folder_name.trim()) {
      errors.push(_driveStagingError_(
        'SITE_FOLDER_NAME_MISMATCH',
        'Il parent della pratica non corrisponde al sito atteso del pilota.'
      ));
    }
    if (found.length !== 1) {
      errors.push(_driveStagingError_(
        'CORRISPONDENZA_FOLDER_INVALID',
        'La cartella 02_corrispondenza deve esistere una sola volta prima di P3.'
      ));
    } else if (typeof payload.expected_corrispondenza_folder_id === 'string' &&
        payload.expected_corrispondenza_folder_id.trim() &&
        found[0].getId() !== payload.expected_corrispondenza_folder_id.trim()) {
      errors.push(_driveStagingError_(
        'CORRISPONDENZA_FOLDER_ID_MISMATCH',
        'La cartella 02_corrispondenza trovata non corrisponde all ID atteso del pilota.'
      ));
    }
    return {
      ok: errors.length === 0,
      errors: errors,
      practiceFolder: practiceFolder,
      siteFolder: siteFolder,
      customerFolder: customerFolder,
      corrispondenzaFolder: found.length === 1 ? found[0] : null
    };
  } catch (err) {
    return {
      ok: false,
      errors: [_driveStagingError_(
        'PRACTICE_FOLDER_NOT_ACCESSIBLE',
        'La cartella pratica pilota non e leggibile con l identita Apps Script.'
      )]
    };
  }
}

function _aggiornaRigaBucolichePerP3_(sheet, row, movedFile, payload, target) {
  const practiceName = target.practiceFolder.getName();
  const parsedPractice = _p3ParsePracticeName_(practiceName);
  const noteRange = sheet.getRange(row, BUCOLICHE_COLS.note);
  const previousNote = String(noteRange.getValue() || '').trim();
  const marker = `${BUCOLICHE_ATTACHMENT_MOVE_NOTE_PREFIX} attachment_id=${payload.attachment_id}` +
    ` sha256=${payload.sha256} practice_folder_id=${target.practiceFolder.getId()}` +
    ` corrispondenza_folder_id=${target.corrispondenzaFolder.getId()}` +
    ` moved_file_id=${movedFile.getId()}]`;
  noteRange.setValue(previousNote ? `${previousNote}\n${marker}` : marker);
  sheet.getRange(row, BUCOLICHE_COLS.cliente).setValue(
    target.customerFolder ? target.customerFolder.getName() : ''
  );
  sheet.getRange(row, BUCOLICHE_COLS.sito).setValue(target.siteFolder.getName());
  sheet.getRange(row, BUCOLICHE_COLS.pratica).setValue(parsedPractice.pratica);
  sheet.getRange(row, BUCOLICHE_COLS.anno).setValue(parsedPractice.anno);
  sheet.getRange(row, BUCOLICHE_COLS.url_cartella).setValue(
    `https://drive.google.com/drive/folders/${target.corrispondenzaFolder.getId()}`
  );
  sheet.getRange(row, BUCOLICHE_COLS.id_drive).setValue(movedFile.getId());
  sheet.getRange(row, BUCOLICHE_COLS.stato).setValue(BUCOLICHE_PRACTICE_STATE);
  sheet.getRange(row, BUCOLICHE_COLS.timestamp_archiviazione).setValue(_timestampLocale());
}

function _p3ParsePracticeName_(practiceName) {
  const match = String(practiceName || '').match(/^(\d{4})_(.+)$/);
  if (!match) {
    return { anno: '', pratica: String(practiceName || '').trim() };
  }
  return { anno: match[1], pratica: match[2] };
}

function _p3LeggiMarkerSpostamento_(sheet, row, attachmentId) {
  const note = String(sheet.getRange(row, BUCOLICHE_COLS.note).getValue() || '');
  const marker = `attachment_id=${attachmentId}`;
  const lines = note.split('\n').filter(line =>
    line.includes(BUCOLICHE_ATTACHMENT_MOVE_NOTE_PREFIX) && line.includes(marker)
  );
  if (lines.length !== 1) return { present: false, moved_file_id: '' };
  const fileIdMatch = lines[0].match(/moved_file_id=([A-Za-z0-9\-_]+)/);
  return { present: true, moved_file_id: fileIdMatch ? fileIdMatch[1] : '' };
}

function _driveStagingPracticeMoveResponse_(payload, ok, driveFileFound,
                                            manifestFound, manifestConsistent,
                                            moveCompleted, idempotent, movedFileId,
                                            destinationFolderId, existingRow,
                                            state, message, errors) {
  return {
    ok: ok,
    action: DRIVE_STAGING_PRACTICE_MOVE_ACTION,
    test_mode: false,
    attachment_id: payload.attachment_id || '',
    staged_filename: payload.staged_filename || '',
    drive_file_found: driveFileFound,
    manifest_found: manifestFound,
    manifest_consistent: manifestConsistent,
    move_completed: moveCompleted,
    idempotent: idempotent === true,
    already_archived: idempotent === true,
    ready_for_p4: ok === true,
    moved_file_id: movedFileId || '',
    destination_folder_id: destinationFolderId || '',
    existing_row: Number.isInteger(existingRow) ? existingRow : 0,
    state: state || '',
    message: message,
    errors: errors
  };
}

/** Pure tests: no live Drive, Bucoliche, Gmail or notifications. */
function testDriveStagingPracticeMovePilot() {
  const payload = Object.assign(_driveStagingTestPayload_(), {
    action: DRIVE_STAGING_PRACTICE_MOVE_ACTION,
    test_mode: false,
    connector_type: 'local_imap',
    account_alias: 'test',
    source_message_id: '<test@example.invalid>',
    source_message_uid: '42',
    original_filename: 'document.pdf',
    mime_type: 'application/pdf',
    scan_engine: 'test_scanner',
    scan_result: 'clean',
    quarantine_status: 'ready_for_caronte',
    note: 'test',
    practice_folder_id: 'practice-1',
    expected_practice_folder_name: '2026_AIA',
    expected_site_folder_name: 'San Pietro di Morubio',
    expected_corrispondenza_folder_id: 'corr-1'
  });
  _driveStagingAssert_(_driveStagingPracticeMoveValidatePayload_(payload).ok,
    'payload P3 valido');
  _driveStagingAssert_(!_driveStagingPracticeMoveValidatePayload_(
    Object.assign({}, payload, { test_mode: true })).ok, 'test_mode true vietato P3');
  const parsed = _p3ParsePracticeName_('2026_AIA');
  _driveStagingAssert_(parsed.anno === '2026' && parsed.pratica === 'AIA',
    'parse nome pratica');
  const rows = [];
  const fakeSheet = _bucolicheNotifyFakeSheet_(rows);
  const checked = _intakeTestInspectFolder_(payload, _intakeTestFakeFolder_(payload, true, true, false));
  _registraBucolicheStagingIdempotente_(fakeSheet, payload, checked);
  _appendiNotaNotificaBucoliche_(fakeSheet, 2, payload, ['chat', 'telegram']);
  const fakeFile = _p3FakeDriveFile_('file-1', 'document.pdf');
  const target = _p3FakeTarget_(fakeFile);
  _aggiornaRigaBucolichePerP3_(fakeSheet, 2, fakeFile, payload, target);
  const moveMarker = _p3LeggiMarkerSpostamento_(fakeSheet, 2, payload.attachment_id);
  _driveStagingAssert_(moveMarker.present && moveMarker.moved_file_id === 'file-1',
    'marker P3 presente');
  _driveStagingAssert_(
    String(fakeSheet.getRange(2, BUCOLICHE_COLS.stato).getValue()) === BUCOLICHE_PRACTICE_STATE,
    'stato Bucoliche aggiornato'
  );
  _driveStagingAssert_(
    String(fakeSheet.getRange(2, BUCOLICHE_COLS.pratica).getValue()) === 'AIA',
    'pratica Bucoliche aggiornata'
  );
  Logger.log('testDriveStagingPracticeMovePilot: OK');
}

function _p3FakeDriveFile_(id, name) {
  return {
    getId: () => id,
    getName: () => name
  };
}

function _p3FakeTarget_(file) {
  return {
    practiceFolder: { getId: () => 'practice-1', getName: () => '2026_AIA' },
    siteFolder: { getName: () => 'San Pietro di Morubio' },
    customerFolder: { getName: () => 'Campedelli Marmi' },
    corrispondenzaFolder: { getId: () => 'corr-1' }
  };
}
