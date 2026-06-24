/** Controlled test-only intake for Drive Desktop staging. */

const DRIVE_STAGING_INTAKE_TEST_ACTION = 'intake_drive_staging_test';
const INTAKE_TEST_SPREADSHEET_PROPERTY = 'VIRGILIO_INTAKE_TEST_SPREADSHEET_ID';
const INTAKE_TEST_SHEET_PROPERTY = 'VIRGILIO_INTAKE_TEST_SHEET_NAME';
const INTAKE_TEST_DEFAULT_SHEET = 'Staging_Local_Test';
const INTAKE_TEST_HEADERS = [
  'timestamp', 'connector_type', 'account_alias', 'source_message_id',
  'source_message_uid', 'attachment_id', 'original_filename', 'staged_filename',
  'sha256', 'size_bytes', 'mime_type', 'scan_engine', 'scan_result',
  'quarantine_status', 'drive_file_found', 'manifest_found',
  'manifest_consistent', 'drive_file_id', 'manifest_file_id', 'stato', 'note'
];

/** Explicit setup only. Never called by intake. */
function caronteSetupStagingDriveTestIntake(spreadsheetId, sheetName) {
  const props = PropertiesService.getScriptProperties();
  spreadsheetId = spreadsheetId || props.getProperty(INTAKE_TEST_SPREADSHEET_PROPERTY);
  sheetName = sheetName || props.getProperty(INTAKE_TEST_SHEET_PROPERTY) ||
    INTAKE_TEST_DEFAULT_SHEET;
  const name = sheetName.trim();
  if (typeof spreadsheetId !== 'string' || !spreadsheetId.trim()) {
    throw new Error('ID spreadsheet test obbligatorio.');
  }
  if (!name || name === CONFIG.BUCOLICHE_TAB) {
    throw new Error('Il tab test deve essere distinto da Bucoliche reale.');
  }
  const ss = SpreadsheetApp.openById(spreadsheetId.trim());
  let sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  if (sheet.getLastRow() === 0) sheet.appendRow(INTAKE_TEST_HEADERS);
  props.setProperties({
    [INTAKE_TEST_SPREADSHEET_PROPERTY]: spreadsheetId.trim(),
    [INTAKE_TEST_SHEET_PROPERTY]: name
  });
  return { ok: true, sheet_name: name };
}

function caronteRegistraStagingDriveTest(payload) {
  const validation = _intakeTestValidatePayload_(payload);
  if (!validation.ok) return validation.response;
  const props = PropertiesService.getScriptProperties();
  const folderId = props.getProperty(DRIVE_STAGING_FOLDER_PROPERTY);
  const spreadsheetId = props.getProperty(INTAKE_TEST_SPREADSHEET_PROPERTY);
  const sheetName = props.getProperty(INTAKE_TEST_SHEET_PROPERTY);
  if (!folderId || !spreadsheetId || !sheetName || sheetName === CONFIG.BUCOLICHE_TAB) {
    return _intakeTestResponse_(payload, false, false, false, false, false, '',
      'Configurazione intake test assente o non sicura.', [
        _driveStagingError_('INTAKE_TEST_NOT_CONFIGURED', 'Eseguire il setup esplicito del tab test.')
      ]);
  }
  try {
    const folder = DriveApp.getFolderById(folderId);
    const checked = _intakeTestInspectFolder_(payload, folder);
    if (!checked.ok) return checked.response;
    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      return _intakeTestResponse_(payload, false, true, true, true, false, '',
        'Tab test non presente; intake rifiutato.', [
          _driveStagingError_('INTAKE_TEST_SHEET_MISSING', 'Il tab deve essere creato dal setup esplicito.')
        ]);
    }
    _intakeTestAppendRow_(sheet, checked.manifest, checked.staged.file.getId(),
      checked.manifestFile.file.getId(), new Date());
    return _intakeTestResponse_(payload, true, true, true, true, true,
      'presa_in_carico_test', 'Presa in carico di test registrata; nessun file spostato.', []);
  } catch (err) {
    return _intakeTestResponse_(payload, false, false, false, false, false, '',
      'Presa in carico di test non completata.', [
        _driveStagingError_('INTAKE_TEST_FAILED', 'Verifica o scrittura test non riuscita.')
      ]);
  }
}

function _intakeTestValidatePayload_(payload) {
  const errors = [];
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    errors.push(_driveStagingError_('INVALID_PAYLOAD', 'Payload non valido.'));
  } else {
    if (payload.action !== DRIVE_STAGING_INTAKE_TEST_ACTION) {
      errors.push(_driveStagingError_('INVALID_ACTION', 'action non supportata.'));
    }
    if (payload.test_mode !== true) {
      errors.push(_driveStagingError_('TEST_MODE_REQUIRED', 'test_mode deve essere true.'));
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
  return { ok: errors.length === 0, response: errors.length ?
    _intakeTestResponse_(payload || {}, false, false, false, false, false, '',
      'Richiesta intake test rifiutata.', errors) : null };
}

function _intakeTestInspectFolder_(payload, folder) {
  const staged = _driveStagingFindUnique_(folder, payload.staged_filename);
  const manifestFile = _driveStagingFindUnique_(folder,
    `${payload.staged_filename}.manifest.json`);
  const errors = [];
  if (!staged.file) errors.push(_driveStagingError_('STAGED_FILE_NOT_FOUND', 'File staged non trovato.'));
  if (!manifestFile.file) errors.push(_driveStagingError_('MANIFEST_NOT_FOUND', 'Manifest non trovato.'));
  let manifest = null;
  let consistent = false;
  if (manifestFile.file) {
    try {
      manifest = JSON.parse(manifestFile.file.getBlob().getDataAsString('UTF-8'));
      const fields = ['connector_type', 'account_alias', 'source_message_id',
        'source_message_uid', 'attachment_id', 'original_filename', 'staged_filename',
        'sha256', 'size_bytes', 'mime_type', 'scan_engine', 'scan_result',
        'quarantine_status', 'note'];
      consistent = fields.every(name => manifest[name] === payload[name]);
      if (!consistent) errors.push(_driveStagingError_('MANIFEST_MISMATCH', 'Manifest incoerente.'));
    } catch (err) {
      errors.push(_driveStagingError_('MANIFEST_INVALID', 'Manifest JSON non valido.'));
    }
  }
  if (staged.file && staged.file.getSize() !== payload.size_bytes) {
    errors.push(_driveStagingError_('STAGED_SIZE_MISMATCH', 'Dimensione Drive incoerente.'));
  }
  const ok = errors.length === 0;
  return { ok: ok, staged: staged, manifestFile: manifestFile, manifest: manifest,
    response: ok ? null : _intakeTestResponse_(payload, false, Boolean(staged.file),
      Boolean(manifestFile.file), consistent, false, '', 'Validazione staging non superata.', errors) };
}

function _intakeTestAppendRow_(sheet, manifest, driveFileId, manifestFileId, now) {
  if (sheet.getName && sheet.getName() === CONFIG.BUCOLICHE_TAB) {
    throw new Error('Scrittura su Bucoliche reale vietata.');
  }
  sheet.appendRow([
    Utilities.formatDate(now, 'Europe/Rome', 'yyyy-MM-dd HH:mm:ss'),
    manifest.connector_type, manifest.account_alias, manifest.source_message_id || '',
    manifest.source_message_uid || '', manifest.attachment_id,
    manifest.original_filename, manifest.staged_filename, manifest.sha256,
    manifest.size_bytes, manifest.mime_type, manifest.scan_engine,
    manifest.scan_result, manifest.quarantine_status, true, true, true,
    driveFileId, manifestFileId, 'presa_in_carico_test', manifest.note || ''
  ]);
}

function _intakeTestResponse_(payload, ok, fileFound, manifestFound, consistent,
                              rowWritten, state, message, errors) {
  return { ok: ok, test_mode: true, action: DRIVE_STAGING_INTAKE_TEST_ACTION,
    attachment_id: payload.attachment_id || '', staged_filename: payload.staged_filename || '',
    drive_file_found: fileFound, manifest_found: manifestFound,
    manifest_consistent: consistent, test_row_written: rowWritten,
    state: state, message: message, errors: errors };
}

/** Pure tests: no Drive, Sheets, Gmail or notifications. */
function testDriveStagingIntakeTest() {
  const payload = Object.assign(_driveStagingTestPayload_(), {
    action: DRIVE_STAGING_INTAKE_TEST_ACTION, test_mode: true,
    connector_type: 'local_imap', account_alias: 'test',
    source_message_id: '<test@example.invalid>', source_message_uid: '42',
    original_filename: 'document.pdf', mime_type: 'application/pdf',
    scan_engine: 'test_scanner', scan_result: 'clean',
    quarantine_status: 'ready_for_caronte', note: 'test'
  });
  _driveStagingAssert_(_intakeTestValidatePayload_(payload).ok, 'payload valido');
  _driveStagingAssert_(!_intakeTestValidatePayload_(Object.assign({}, payload,
    { test_mode: false })).ok, 'test_mode false');
  const noMode = Object.assign({}, payload); delete noMode.test_mode;
  _driveStagingAssert_(!_intakeTestValidatePayload_(noMode).ok, 'test_mode mancante');
  _driveStagingAssert_(!_intakeTestValidatePayload_(Object.assign({}, payload,
    { action: 'other' })).ok, 'action errata');
  const folder = _intakeTestFakeFolder_(payload, true, true, false);
  _driveStagingAssert_(_intakeTestInspectFolder_(payload, folder).ok, 'file e manifest validi');
  _driveStagingAssert_(!_intakeTestInspectFolder_(payload,
    _intakeTestFakeFolder_(payload, false, true, false)).ok, 'file mancante');
  _driveStagingAssert_(!_intakeTestInspectFolder_(payload,
    _intakeTestFakeFolder_(payload, true, false, false)).ok, 'manifest mancante');
  _driveStagingAssert_(!_intakeTestInspectFolder_(payload,
    _intakeTestFakeFolder_(payload, true, true, true)).ok, 'manifest incoerente');
  const rows = [];
  _intakeTestAppendRow_({ getName: () => 'Staging_Local_Test', appendRow: row => rows.push(row) },
    payload, 'drive-id', 'manifest-id', new Date(0));
  _driveStagingAssert_(rows.length === 1 && rows[0][19] === 'presa_in_carico_test',
    'scrittura tab test');
  Logger.log('testDriveStagingIntakeTest: OK');
}

function _intakeTestFakeFolder_(payload, includeFile, includeManifest, mismatch) {
  const manifest = Object.assign({}, payload); delete manifest.action; delete manifest.test_mode;
  if (mismatch) manifest.sha256 = 'b'.repeat(64);
  const files = {};
  if (includeFile) files[payload.staged_filename] = [_intakeTestFakeFile_('', payload.size_bytes, 'f')];
  if (includeManifest) files[`${payload.staged_filename}.manifest.json`] = [
    _intakeTestFakeFile_(JSON.stringify(manifest), 10, 'm')
  ];
  return { getFilesByName: name => { const values = (files[name] || []).slice();
    return { hasNext: () => values.length > 0, next: () => values.shift() }; } };
}

function _intakeTestFakeFile_(content, size, id) {
  return { getSize: () => size, getId: () => id,
    getBlob: () => ({ getDataAsString: () => content }) };
}
