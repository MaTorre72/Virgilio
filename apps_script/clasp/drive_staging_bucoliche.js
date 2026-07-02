/** Registrazione idempotente su Bucoliche reale per allegati staged e validati. */

const DRIVE_STAGING_BUCOLICHE_ACTION = 'register_drive_staging_bucoliche';
const BUCOLICHE_LIMBO_STATE = 'limbo_registrato';
const BUCOLICHE_ATTACHMENT_NOTE_PREFIX = '[virgilio_local_connector';

function caronteRegistraBucolicheDaStaging(payload) {
  const validation = _bucolicheStagingValidatePayload_(payload);
  if (!validation.ok) return validation.response;

  const folderId = PropertiesService.getScriptProperties()
    .getProperty(DRIVE_STAGING_FOLDER_PROPERTY);
  if (!folderId) {
    return _bucolicheStagingResponse_(payload, false, false, false, false, false, '',
      'Cartella staging Drive non configurata.', [
        _driveStagingError_('STAGING_FOLDER_NOT_CONFIGURED',
          'Configurare VIRGILIO_DRIVE_STAGING_FOLDER_ID nelle Script Properties.')
      ]);
  }

  try {
    const folder = DriveApp.getFolderById(folderId);
    const checked = _intakeTestInspectFolder_(payload, folder);
    if (!checked.ok) {
      return _bucolicheStagingResponse_(
        payload, false, Boolean(checked.staged.file), Boolean(checked.manifestFile.file),
        false, false, '', 'Validazione staging non superata.',
        checked.response && Array.isArray(checked.response.errors) ? checked.response.errors : []
      );
    }
    const sheet = _aprifoglioBucoliche();
    _assicuraIntestazione(sheet);
    return _registraBucolicheStagingIdempotente_(sheet, payload, checked);
  } catch (err) {
    return _bucolicheStagingResponse_(payload, false, false, false, false, false, '',
      'Registrazione Bucoliche non completata.', [
        _driveStagingError_('BUCOLICHE_REGISTRATION_FAILED',
          'Scrittura su Bucoliche o lettura staging non riuscita.')
      ]);
  }
}

function _bucolicheStagingValidatePayload_(payload) {
  const errors = [];
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    errors.push(_driveStagingError_('INVALID_PAYLOAD', 'Payload non valido.'));
  } else {
    if (payload.action !== DRIVE_STAGING_BUCOLICHE_ACTION) {
      errors.push(_driveStagingError_('INVALID_ACTION', 'action non supportata.'));
    }
    if (payload.test_mode !== false) {
      errors.push(_driveStagingError_('TEST_MODE_MUST_BE_FALSE', 'test_mode deve essere false.'));
    }
    const required = ['connector_type', 'account_alias', 'attachment_id',
      'original_filename', 'staged_filename', 'sha256', 'mime_type',
      'scan_engine', 'scan_result', 'quarantine_status'];
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
    response: errors.length === 0 ? null : _bucolicheStagingResponse_(
      payload || {}, false, false, false, false, false, '',
      'Richiesta registrazione Bucoliche rifiutata.', errors
    )
  };
}

function _registraBucolicheStagingIdempotente_(sheet, payload, checked) {
  const existingRow = _trovaRigaBucolichePerAttachmentId_(sheet, payload.attachment_id);
  if (existingRow > 0) {
    const existingSha256 = _leggiSha256BucolicheRiga_(sheet, existingRow);
    if (existingSha256 !== payload.sha256) {
      return _bucolicheStagingResponse_(payload, false, true, true, true, false, '',
        'attachment_id gia registrato in Bucoliche con SHA-256 differente.', [
          _driveStagingError_('ATTACHMENT_SHA256_CONFLICT',
            'Lo stesso attachment_id risulta associato a un SHA-256 diverso.')
        ], true, true, existingRow);
    }
    return _bucolicheStagingResponse_(payload, true, true, true, true, false,
      BUCOLICHE_LIMBO_STATE, 'Riga Bucoliche gia registrata; nessuna nuova riga.',
      [], true, true, existingRow);
  }

  const manifest = checked.manifest;
  const file = checked.staged.file;
  const originalName = String(manifest.original_filename || '');
  const extension = originalName.includes('.')
    ? originalName.split('.').pop().toLowerCase().substring(0, 10)
    : '';
  const row = [
    _timestampLocale(),
    'local_imap_staging',
    '— in attesa —',
    '',
    '',
    '',
    '',
    _bucolicheAttachmentNote_(manifest),
    `https://drive.google.com/file/d/${file.getId()}`,
    file.getId(),
    String(manifest.account_alias || ''),
    '',
    originalName,
    extension,
    Math.round(Number(manifest.size_bytes || 0) / 1024),
    BUCOLICHE_LIMBO_STATE,
    ''
  ];
  sheet.appendRow(row);
  return _bucolicheStagingResponse_(payload, true, true, true, true, true,
    BUCOLICHE_LIMBO_STATE, 'Riga Bucoliche registrata; nessun file spostato.',
    [], false, false, sheet.getLastRow());
}

function _bucolicheAttachmentNote_(manifest) {
  const prefix = `${BUCOLICHE_ATTACHMENT_NOTE_PREFIX} attachment_id=${manifest.attachment_id}` +
    ` sha256=${manifest.sha256} account_alias=${manifest.account_alias || ''}` +
    ` source_message_uid=${manifest.source_message_uid || ''}]`;
  const note = typeof manifest.note === 'string' ? manifest.note.trim() : '';
  return note ? `${note}\n${prefix}` : prefix;
}

function _trovaRigaBucolichePerAttachmentId_(sheet, attachmentId) {
  if (typeof attachmentId !== 'string' || !attachmentId.trim()) return 0;
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return 0;
  const values = sheet.getRange(2, BUCOLICHE_COLS.note, lastRow - 1, 1).getValues();
  const marker = `attachment_id=${attachmentId}`;
  for (let index = 0; index < values.length; index++) {
    const note = String(values[index][0] || '');
    if (note.includes(BUCOLICHE_ATTACHMENT_NOTE_PREFIX) && note.includes(marker)) {
      return index + 2;
    }
  }
  return 0;
}

function _leggiSha256BucolicheRiga_(sheet, row) {
  const note = String(sheet.getRange(row, BUCOLICHE_COLS.note).getValue() || '');
  const match = note.match(/sha256=([0-9a-f]{64})/);
  return match ? match[1] : '';
}

function _bucolicheStagingResponse_(payload, ok, driveFileFound, manifestFound,
                                    manifestConsistent, rowWritten, state,
                                    message, errors, idempotent,
                                    alreadyRegistered, existingRow) {
  return {
    ok: ok,
    action: DRIVE_STAGING_BUCOLICHE_ACTION,
    test_mode: false,
    attachment_id: payload.attachment_id || '',
    staged_filename: payload.staged_filename || '',
    drive_file_found: driveFileFound,
    manifest_found: manifestFound,
    manifest_consistent: manifestConsistent,
    bucoliche_row_written: rowWritten,
    idempotent: idempotent === true,
    already_registered: alreadyRegistered === true,
    existing_row: Number.isInteger(existingRow) ? existingRow : 0,
    state: state,
    message: message,
    errors: errors
  };
}

/** Test puri: nessun accesso a Drive, Gmail, notifiche o Bucoliche reale. */
function testDriveStagingBucolicheRegistration() {
  const payload = Object.assign(_driveStagingTestPayload_(), {
    action: DRIVE_STAGING_BUCOLICHE_ACTION,
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
    note: 'test'
  });
  _driveStagingAssert_(_bucolicheStagingValidatePayload_(payload).ok,
    'payload P1 valido');
  _driveStagingAssert_(!_bucolicheStagingValidatePayload_(
    Object.assign({}, payload, { test_mode: true })).ok, 'test_mode true vietato');

  const rows = [];
  const fakeSheet = _bucolicheFakeSheet_(rows);
  const checked = _intakeTestInspectFolder_(payload, _intakeTestFakeFolder_(payload, true, true, false));
  const first = _registraBucolicheStagingIdempotente_(fakeSheet, payload, checked);
  _driveStagingAssert_(first.ok && first.bucoliche_row_written &&
    rows.length === 1 && rows[0][15] === BUCOLICHE_LIMBO_STATE, 'prima registrazione');
  _driveStagingAssert_(_trovaRigaBucolichePerAttachmentId_(fakeSheet, payload.attachment_id) === 2,
    'attachment_id trovato in Bucoliche');
  _driveStagingAssert_(_leggiSha256BucolicheRiga_(fakeSheet, 2) === payload.sha256,
    'sha256 letto dalla nota');

  const same = _registraBucolicheStagingIdempotente_(fakeSheet, payload, checked);
  _driveStagingAssert_(same.ok && same.idempotent && same.already_registered &&
    !same.bucoliche_row_written && same.existing_row === 2, 'retry idempotente Bucoliche');

  const conflict = _registraBucolicheStagingIdempotente_(fakeSheet,
    Object.assign({}, payload, { sha256: 'b'.repeat(64) }), checked);
  _driveStagingAssert_(!conflict.ok && conflict.errors[0].code === 'ATTACHMENT_SHA256_CONFLICT',
    'conflitto sha256 Bucoliche');
  Logger.log('testDriveStagingBucolicheRegistration: OK');
}

function _bucolicheFakeSheet_(rows) {
  return {
    appendRow: row => rows.push(row),
    getLastRow: () => rows.length + 1,
    getRange: (row, column, numRows) => ({
      getValues: () => rows.slice(row - 2, row - 2 + numRows)
        .map(value => [value[column - 1]]),
      getValue: () => rows[row - 2][column - 1]
    })
  };
}
