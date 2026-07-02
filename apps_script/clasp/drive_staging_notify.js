/** Idempotent pilot notification for a validated staged attachment. */

const DRIVE_STAGING_NOTIFY_ACTION = 'notify_drive_staging_pilot';
const DRIVE_STAGING_NOTIFY_NOTE_PREFIX = '[virgilio_local_connector_notify';

function caronteNotificaPilotaDaStaging(payload) {
  const validation = _driveStagingNotifyValidatePayload_(payload);
  if (!validation.ok) return validation.response;

  const folderId = PropertiesService.getScriptProperties()
    .getProperty(DRIVE_STAGING_FOLDER_PROPERTY);
  if (!folderId) {
    return _driveStagingNotifyResponse_(payload, false, false, false, false, false, '',
      'Cartella staging Drive non configurata.', [
        _driveStagingError_('STAGING_FOLDER_NOT_CONFIGURED',
          'Configurare VIRGILIO_DRIVE_STAGING_FOLDER_ID nelle Script Properties.')
      ]);
  }

  try {
    const folder = DriveApp.getFolderById(folderId);
    const checked = _intakeTestInspectFolder_(payload, folder);
    if (!checked.ok) {
      return _driveStagingNotifyResponse_(
        payload, false, Boolean(checked.staged.file), Boolean(checked.manifestFile.file),
        false, false, '', 'Validazione staging non superata.',
        checked.response && Array.isArray(checked.response.errors) ? checked.response.errors : []
      );
    }

    const sheet = _aprifoglioBucoliche();
    _assicuraIntestazione(sheet);
    return _notificaStagingPilotaIdempotente_(sheet, payload, checked);
  } catch (err) {
    return _driveStagingNotifyResponse_(payload, false, false, false, false, false, '',
      'Notifica pilota non completata.', [
        _driveStagingError_('PILOT_NOTIFICATION_FAILED',
          'Invio notifica o lettura staging non riusciti.')
      ]);
  }
}

function _driveStagingNotifyValidatePayload_(payload) {
  const errors = [];
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    errors.push(_driveStagingError_('INVALID_PAYLOAD', 'Payload non valido.'));
  } else {
    if (payload.action !== DRIVE_STAGING_NOTIFY_ACTION) {
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
    response: errors.length === 0 ? null : _driveStagingNotifyResponse_(
      payload || {}, false, false, false, false, false, '',
      'Richiesta notifica pilota rifiutata.', errors
    )
  };
}

function _notificaStagingPilotaIdempotente_(sheet, payload, checked, deps) {
  const existingRow = _trovaRigaBucolichePerAttachmentId_(sheet, payload.attachment_id);
  if (existingRow === 0) {
    return _driveStagingNotifyResponse_(payload, false, true, true, false, false, '',
      'Riga Bucoliche non trovata per l attachment richiesto.', [
        _driveStagingError_('BUCOLICHE_ROW_NOT_FOUND',
          'Eseguire prima la registrazione P1 su Bucoliche reale.')
      ]);
  }

  const existingSha256 = _leggiSha256BucolicheRiga_(sheet, existingRow);
  if (existingSha256 !== payload.sha256) {
    return _driveStagingNotifyResponse_(payload, false, true, true, true, false, '',
      'attachment_id gia registrato in Bucoliche con SHA-256 differente.', [
        _driveStagingError_('ATTACHMENT_SHA256_CONFLICT',
          'Lo stesso attachment_id risulta associato a un SHA-256 diverso.')
      ], false, true, existingRow);
  }

  const currentState = String(sheet.getRange(existingRow, BUCOLICHE_COLS.stato).getValue() || '').trim();
  if (currentState !== BUCOLICHE_LIMBO_STATE) {
    return _driveStagingNotifyResponse_(payload, false, true, true, true, false, currentState,
      'Stato Bucoliche non compatibile con P2.', [
        _driveStagingError_('INVALID_BUCOLICHE_STATE',
          'La notifica pilota richiede stato limbo_registrato.')
      ], false, false, existingRow);
  }

  if (_bucolicheNotaContieneNotifica_(sheet, existingRow, payload)) {
    return _driveStagingNotifyResponse_(payload, true, true, true, true, false, currentState,
      'Notifica pilota gia registrata; nessun nuovo invio.', [],
      true, true, existingRow, _driveStagingNotifyChannelsFromNote_(sheet, existingRow));
  }

  const driveUrl = String(sheet.getRange(existingRow, BUCOLICHE_COLS.url_cartella).getValue() || '').trim();
  const notification = (deps && deps.notify ? deps.notify : avvisaRegistrazionePilotaTeam)({
    attachmentId: payload.attachment_id,
    stagedFilename: payload.staged_filename,
    state: currentState,
    driveUrl: driveUrl,
    accountAlias: payload.account_alias
  });

  if (!notification.ok) {
    return _driveStagingNotifyResponse_(payload, false, true, true, true, false, currentState,
      'Notifica pilota non inviata.', notification.errors || [],
      false, false, existingRow, notification.channels || []);
  }

  _appendiNotaNotificaBucoliche_(sheet, existingRow, payload, notification.channels || []);
  return _driveStagingNotifyResponse_(payload, true, true, true, true, true, currentState,
    'Notifica pilota inviata e marcata in Bucoliche.', [],
    false, false, existingRow, notification.channels || []);
}

function _bucolicheNotaContieneNotifica_(sheet, row, payload) {
  const note = String(sheet.getRange(row, BUCOLICHE_COLS.note).getValue() || '');
  const marker = `attachment_id=${payload.attachment_id}`;
  const sha = `sha256=${payload.sha256}`;
  return note.includes(DRIVE_STAGING_NOTIFY_NOTE_PREFIX) && note.includes(marker) && note.includes(sha);
}

function _driveStagingNotifyChannelsFromNote_(sheet, row) {
  const note = String(sheet.getRange(row, BUCOLICHE_COLS.note).getValue() || '');
  const match = note.match(/channels=([a-z,]+)/);
  if (!match || !match[1]) return [];
  return match[1].split(',').filter(Boolean);
}

function _appendiNotaNotificaBucoliche_(sheet, row, payload, channels) {
  const previous = String(sheet.getRange(row, BUCOLICHE_COLS.note).getValue() || '').trim();
  const channelText = Array.isArray(channels) && channels.length ? channels.join(',') : 'none';
  const marker = `${DRIVE_STAGING_NOTIFY_NOTE_PREFIX} attachment_id=${payload.attachment_id}` +
    ` sha256=${payload.sha256} channels=${channelText}]`;
  sheet.getRange(row, BUCOLICHE_COLS.note).setValue(previous ? `${previous}\n${marker}` : marker);
}

function _driveStagingNotifyResponse_(payload, ok, driveFileFound, manifestFound,
                                      manifestConsistent, notificationSent, state,
                                      message, errors, idempotent,
                                      alreadyNotified, existingRow, channelsNotified) {
  return {
    ok: ok,
    action: DRIVE_STAGING_NOTIFY_ACTION,
    test_mode: false,
    attachment_id: payload.attachment_id || '',
    staged_filename: payload.staged_filename || '',
    drive_file_found: driveFileFound,
    manifest_found: manifestFound,
    manifest_consistent: manifestConsistent,
    notification_sent: notificationSent,
    idempotent: idempotent === true,
    already_notified: alreadyNotified === true,
    existing_row: Number.isInteger(existingRow) ? existingRow : 0,
    state: state,
    channels_notified: Array.isArray(channelsNotified) ? channelsNotified : [],
    message: message,
    errors: errors
  };
}

/** Pure tests: no Drive, Gmail, UrlFetch or live notifications. */
function testDriveStagingNotifyPilot() {
  const payload = Object.assign(_driveStagingTestPayload_(), {
    action: DRIVE_STAGING_NOTIFY_ACTION,
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
  _driveStagingAssert_(_driveStagingNotifyValidatePayload_(payload).ok, 'payload P2 valido');
  _driveStagingAssert_(!_driveStagingNotifyValidatePayload_(
    Object.assign({}, payload, { test_mode: true })).ok, 'test_mode true vietato P2');

  const rows = [];
  const fakeSheet = _bucolicheNotifyFakeSheet_(rows);
  const checked = _intakeTestInspectFolder_(payload, _intakeTestFakeFolder_(payload, true, true, false));
  const registered = _registraBucolicheStagingIdempotente_(fakeSheet, payload, checked);
  _driveStagingAssert_(registered.ok && registered.bucoliche_row_written, 'riga Bucoliche base');

  const sent = _notificaStagingPilotaIdempotente_(fakeSheet, payload, checked, {
    notify: details => avvisaRegistrazionePilotaTeam(details, {
      chatConfigured: true,
      telegramConfigured: true,
      sendChat: () => {},
      sendTelegram: () => {}
    })
  });
  _driveStagingAssert_(sent.ok && sent.notification_sent &&
    sent.channels_notified.length === 2, 'prima notifica pilota');
  _driveStagingAssert_(_bucolicheNotaContieneNotifica_(fakeSheet, 2, payload),
    'marker notifica presente');

  const same = _notificaStagingPilotaIdempotente_(fakeSheet, payload, checked, {
    notify: details => avvisaRegistrazionePilotaTeam(details, {
      chatConfigured: true,
      telegramConfigured: true,
      sendChat: () => {},
      sendTelegram: () => {}
    })
  });
  _driveStagingAssert_(same.ok && same.idempotent && same.already_notified &&
    !same.notification_sent && same.existing_row === 2, 'retry idempotente P2');

  const conflict = _notificaStagingPilotaIdempotente_(fakeSheet,
    Object.assign({}, payload, { sha256: 'b'.repeat(64) }), checked, {
      notify: details => avvisaRegistrazionePilotaTeam(details, {
        chatConfigured: true,
        telegramConfigured: true,
        sendChat: () => {},
        sendTelegram: () => {}
      })
    });
  _driveStagingAssert_(!conflict.ok && conflict.errors[0].code === 'ATTACHMENT_SHA256_CONFLICT',
    'conflitto sha256 P2');

  const missingRow = _notificaStagingPilotaIdempotente_(
    _bucolicheNotifyFakeSheet_([]), payload, checked);
  _driveStagingAssert_(!missingRow.ok && missingRow.errors[0].code === 'BUCOLICHE_ROW_NOT_FOUND',
    'richiede P1 completato');
  Logger.log('testDriveStagingNotifyPilot: OK');
}

function _bucolicheNotifyFakeSheet_(rows) {
  return {
    appendRow: row => rows.push(row),
    getLastRow: () => rows.length + 1,
    getRange: (row, column, numRows) => ({
      getValues: () => rows.slice(row - 2, row - 2 + numRows)
        .map(value => [value[column - 1]]),
      getValue: () => rows[row - 2][column - 1],
      setValue: value => { rows[row - 2][column - 1] = value; }
    })
  };
}
