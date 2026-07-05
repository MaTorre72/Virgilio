/** Schema e setup esplicito del tab operativo Virgilio_Inbox. */

const VIRGILIO_INBOX_SPREADSHEET_PROPERTY = 'VIRGILIO_INBOX_SPREADSHEET_ID';
const VIRGILIO_INBOX_SHEET_PROPERTY = 'VIRGILIO_INBOX_SHEET_NAME';
const VIRGILIO_INBOX_DEFAULT_SHEET = 'Virgilio_Inbox';
const VIRGILIO_INBOX_INTAKE_ACTION = 'intake_virgilio_inbox';
const VIRGILIO_INBOX_COLUMN_WIDTHS = [
  170, 170, 120, 220, 150, 220, 220, 130, 150, 170, 170,
  220, 220, 170, 170, 240, 220, 180, 180, 180, 240, 280
];

function caronteGetVirgilioInboxSchema() {
  return {
    spreadsheet_property: VIRGILIO_INBOX_SPREADSHEET_PROPERTY,
    sheet_property: VIRGILIO_INBOX_SHEET_PROPERTY,
    default_sheet_name: VIRGILIO_INBOX_DEFAULT_SHEET,
    intake_action: VIRGILIO_INBOX_INTAKE_ACTION,
    fields: VIRGILIO_INBOX_FIELDS.slice(),
  };
}

/** Setup esplicito: crea o consolida solo il tab separato Virgilio_Inbox. */
function caronteSetupVirgilioInbox(spreadsheetId, sheetName) {
  const resolvedSpreadsheetId = _virgilioInboxResolveSpreadsheetId_(spreadsheetId);
  const resolvedSheetName = _virgilioInboxResolveSheetName_(sheetName);
  const ss = SpreadsheetApp.openById(resolvedSpreadsheetId);
  let sheet = ss.getSheetByName(resolvedSheetName);
  let created = false;
  if (!sheet) {
    sheet = ss.insertSheet(resolvedSheetName);
    created = true;
  }
  const headerState = _virgilioInboxEnsureHeader_(sheet, VIRGILIO_INBOX_FIELDS);
  PropertiesService.getScriptProperties().setProperties({
    [VIRGILIO_INBOX_SPREADSHEET_PROPERTY]: resolvedSpreadsheetId,
    [VIRGILIO_INBOX_SHEET_PROPERTY]: resolvedSheetName,
  });
  return {
    ok: true,
    spreadsheet_id: resolvedSpreadsheetId,
    sheet_name: resolvedSheetName,
    created: created,
    header_action: headerState.action,
    fields: VIRGILIO_INBOX_FIELDS.slice(),
  };
}

function caronteRegistraVirgilioInbox(payload) {
  const validation = _virgilioInboxValidateIntakePayload_(payload);
  if (!validation.ok) return validation.response;

  try {
    const visibility = _driveStagingVerifyInboxVisibility_(payload);
    if (!visibility.ok) {
      return _virgilioInboxIntakeResponse_(
        payload, false, '', false, false, false, 0,
        'Presa in carico inbox rifiutata: file non verificato come visibile su Drive.',
        visibility.errors
      );
    }
    const spreadsheetId = _virgilioInboxResolveSpreadsheetId_();
    const sheetName = _virgilioInboxResolveSheetName_();
    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      return _virgilioInboxIntakeResponse_(
        payload, false, '', false, false, false, 0,
        'Tab Virgilio_Inbox non presente; eseguire prima il setup esplicito.',
        [_driveStagingError_(
          'VIRGILIO_INBOX_NOT_CONFIGURED',
          'Creare il tab con caronteSetupVirgilioInbox prima della presa in carico.'
        )]
      );
    }

    _virgilioInboxEnsureHeader_(sheet, VIRGILIO_INBOX_FIELDS);
    const draft = caronteBuildVirgilioInboxDraftFromManifest(payload.manifest, {
      drive_file_id: visibility.drive_file_id,
      manifest_file_id: visibility.manifest_file_id,
      form_url: _virgilioInboxStringOrEmpty_(payload.form_url),
    });
    const result = _virgilioInboxUpsertDraft_(sheet, draft, {
      now: new Date(),
    });
    return _virgilioInboxIntakeResponse_(
      payload, true, result.inbox_id, result.created, result.updated,
      result.idempotent, result.row,
      result.idempotent
        ? 'Presa in carico inbox gia registrata; nessuna duplicazione creata.'
        : 'Presa in carico inbox registrata senza contenuti binari o path locali.',
      []
    );
  } catch (err) {
    return _virgilioInboxIntakeResponse_(
      payload, false, '', false, false, false, 0,
      'Presa in carico inbox non completata.',
      [_driveStagingError_(
        'VIRGILIO_INBOX_WRITE_FAILED',
        _virgilioInboxStringOrEmpty_(err && err.message) || 'Scrittura Virgilio_Inbox non riuscita.'
      )]
    );
  }
}

function caronteRegistraVirgilioInboxDaGmail(payload) {
  const validation = _virgilioInboxValidateGmailPayload_(payload);
  if (!validation.ok) return validation.response;

  try {
    const spreadsheetId = _virgilioInboxResolveSpreadsheetId_();
    const sheetName = _virgilioInboxResolveSheetName_();
    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      return _virgilioInboxIntakeResponse_(
        validation.payload, false, '', false, false, false, 0,
        'Tab Virgilio_Inbox non presente; eseguire prima il setup esplicito.',
        [_driveStagingError_(
          'VIRGILIO_INBOX_NOT_CONFIGURED',
          'Creare il tab con caronteSetupVirgilioInbox prima dell intake Gmail.'
        )]
      );
    }

    _virgilioInboxEnsureHeader_(sheet, VIRGILIO_INBOX_FIELDS);
    const draft = caronteBuildVirgilioInboxDraftFromGmail(validation.payload, {
      drive_file_id: validation.payload.drive_file_id,
      form_url: validation.payload.form_url,
    });
    const result = _virgilioInboxUpsertDraft_(sheet, draft, {
      now: new Date(),
      inboxIdFactory: validation.payload.inboxIdFactory,
    });
    return _virgilioInboxIntakeResponse_(
      validation.payload,
      true,
      result.inbox_id,
      result.created,
      result.updated,
      result.idempotent,
      result.row,
      result.idempotent
        ? 'Presa in carico inbox Gmail gia registrata; nessuna duplicazione creata.'
        : 'Presa in carico inbox Gmail registrata nel tab Da archiviare.',
      []
    );
  } catch (err) {
    return _virgilioInboxIntakeResponse_(
      validation.payload,
      false,
      '',
      false,
      false,
      false,
      0,
      'Presa in carico inbox Gmail non completata.',
      [_driveStagingError_(
        'VIRGILIO_INBOX_GMAIL_WRITE_FAILED',
        _virgilioInboxStringOrEmpty_(err && err.message) ||
          'Scrittura Virgilio_Inbox da Gmail non riuscita.'
      )]
    );
  }
}

function caronteGetVirgilioInboxForForm(inboxId) {
  const normalizedInboxId = _virgilioInboxStringOrEmpty_(inboxId);
  if (!normalizedInboxId) {
    return { ok: false, inbox_id: '', found: false, message: 'inbox_id mancante.' };
  }

  try {
    const spreadsheetId = _virgilioInboxResolveSpreadsheetId_();
    const sheetName = _virgilioInboxResolveSheetName_();
    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      return {
        ok: false,
        inbox_id: normalizedInboxId,
        found: false,
        message: 'Tab Virgilio_Inbox non configurato.',
      };
    }
    _virgilioInboxEnsureHeader_(sheet, VIRGILIO_INBOX_FIELDS);
    return _virgilioInboxFindFormContextByInboxId_(sheet, normalizedInboxId);
  } catch (err) {
    return {
      ok: false,
      inbox_id: normalizedInboxId,
      found: false,
      message: _virgilioInboxStringOrEmpty_(err && err.message) ||
        'Lookup Virgilio_Inbox non riuscito.',
    };
  }
}

function caronteCollegaSubmitVirgilioInbox(payload) {
  const normalized = _virgilioInboxNormalizeSubmitPayload_(payload);
  if (!normalized.ok) return normalized.response;

  try {
    const spreadsheetId = _virgilioInboxResolveSpreadsheetId_();
    const sheetName = _virgilioInboxResolveSheetName_();
    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      return {
        ok: false,
        inbox_id: normalized.payload.inbox_id,
        linked: false,
        updated: false,
        status: '',
        message: 'Tab Virgilio_Inbox non configurato.',
      };
    }
    _virgilioInboxEnsureHeader_(sheet, VIRGILIO_INBOX_FIELDS);
    const match = _virgilioInboxFindRowByInboxId_(sheet, normalized.payload.inbox_id);
    if (!match.found) {
      return {
        ok: false,
        inbox_id: normalized.payload.inbox_id,
        linked: false,
        updated: false,
        status: '',
        message: 'inbox_id non trovato in Virgilio_Inbox.',
      };
    }

    const linked = _virgilioInboxApplySubmitToEntry_(match.entry, normalized.payload);
    const changed = !_virgilioInboxEntriesEqual_(match.entry, linked);
    if (changed) {
      _virgilioInboxWriteEntry_(sheet, match.row, linked);
    }
    return {
      ok: true,
      inbox_id: linked.inbox_id,
      linked: true,
      updated: changed,
      status: linked.status,
      message: changed
        ? 'Submit form collegato al record Virgilio_Inbox.'
        : 'Submit form gia collegato al record Virgilio_Inbox.',
    };
  } catch (err) {
    return {
      ok: false,
      inbox_id: normalized.payload.inbox_id,
      linked: false,
      updated: false,
      status: '',
      message: _virgilioInboxStringOrEmpty_(err && err.message) ||
        'Aggancio submit Virgilio_Inbox non riuscito.',
    };
  }
}

function caronteGetVirgilioInboxForArchive(inboxId) {
  const normalizedInboxId = _virgilioInboxStringOrEmpty_(inboxId);
  if (!normalizedInboxId) {
    return {
      ok: false,
      inbox_id: '',
      found: false,
      message: 'inbox_id mancante per l archiviazione.',
    };
  }

  try {
    const spreadsheetId = _virgilioInboxResolveSpreadsheetId_();
    const sheetName = _virgilioInboxResolveSheetName_();
    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      return {
        ok: false,
        inbox_id: normalizedInboxId,
        found: false,
        message: 'Tab Virgilio_Inbox non configurato.',
      };
    }
    _virgilioInboxEnsureHeader_(sheet, VIRGILIO_INBOX_FIELDS);
    return _virgilioInboxFindArchiveContextByInboxId_(sheet, normalizedInboxId);
  } catch (err) {
    return {
      ok: false,
      inbox_id: normalizedInboxId,
      found: false,
      message: _virgilioInboxStringOrEmpty_(err && err.message) ||
        'Lookup archiviazione Virgilio_Inbox non riuscito.',
    };
  }
}

function caronteArchiviaVirgilioInbox(payload) {
  const normalized = _virgilioInboxNormalizeArchivePayload_(payload);
  if (!normalized.ok) return normalized.response;

  try {
    const spreadsheetId = _virgilioInboxResolveSpreadsheetId_();
    const sheetName = _virgilioInboxResolveSheetName_();
    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      return {
        ok: false,
        inbox_id: normalized.payload.inbox_id,
        archived: false,
        updated: false,
        status: '',
        message: 'Tab Virgilio_Inbox non configurato.',
      };
    }
    _virgilioInboxEnsureHeader_(sheet, VIRGILIO_INBOX_FIELDS);
    const match = _virgilioInboxFindRowByInboxId_(sheet, normalized.payload.inbox_id);
    if (!match.found) {
      return {
        ok: false,
        inbox_id: normalized.payload.inbox_id,
        archived: false,
        updated: false,
        status: '',
        message: 'inbox_id non trovato in Virgilio_Inbox.',
      };
    }

    const archived = _virgilioInboxApplyArchiveToEntry_(match.entry, normalized.payload);
    const changed = !_virgilioInboxEntriesEqual_(match.entry, archived);
    if (changed) {
      _virgilioInboxWriteEntry_(sheet, match.row, archived);
    }
    return {
      ok: true,
      inbox_id: archived.inbox_id,
      archived: true,
      updated: changed,
      status: archived.status,
      message: changed
        ? 'Record Virgilio_Inbox marcato come archiviato.'
        : 'Record Virgilio_Inbox gia archiviato.',
    };
  } catch (err) {
    return {
      ok: false,
      inbox_id: normalized.payload.inbox_id,
      archived: false,
      updated: false,
      status: '',
      message: _virgilioInboxStringOrEmpty_(err && err.message) ||
        'Archiviazione Virgilio_Inbox non riuscita.',
    };
  }
}

function _virgilioInboxResolveSpreadsheetId_(spreadsheetId) {
  const props = PropertiesService.getScriptProperties();
  const value = _virgilioInboxStringOrEmpty_(spreadsheetId) ||
    _virgilioInboxStringOrEmpty_(props.getProperty(VIRGILIO_INBOX_SPREADSHEET_PROPERTY));
  if (!value) {
    throw new Error(
      'ID spreadsheet Virgilio_Inbox obbligatorio. Impostare ' +
      'VIRGILIO_INBOX_SPREADSHEET_ID nelle Script Properties.'
    );
  }
  return value;
}

function _virgilioInboxResolveSheetName_(sheetName) {
  const props = PropertiesService.getScriptProperties();
  const value = _virgilioInboxStringOrEmpty_(sheetName) ||
    _virgilioInboxStringOrEmpty_(props.getProperty(VIRGILIO_INBOX_SHEET_PROPERTY)) ||
    VIRGILIO_INBOX_DEFAULT_SHEET;
  const bucolicheTab = typeof CONFIG !== 'undefined' && CONFIG
    ? _virgilioInboxStringOrEmpty_(CONFIG.BUCOLICHE_TAB)
    : '';
  if (!value) throw new Error('Nome tab Virgilio_Inbox obbligatorio.');
  if (value === bucolicheTab) {
    throw new Error('Virgilio_Inbox deve restare separato dal tab Bucoliche.');
  }
  if (typeof INTAKE_TEST_DEFAULT_SHEET !== 'undefined' && value === INTAKE_TEST_DEFAULT_SHEET) {
    throw new Error('Virgilio_Inbox non puo usare il tab di test Staging_Local_Test.');
  }
  return value;
}

function _virgilioInboxEnsureHeader_(sheet, headers) {
  const lastRow = sheet.getLastRow();
  if (lastRow === 0) {
    sheet.appendRow(headers);
    _virgilioInboxFormatSheet_(sheet, headers.length);
    return { action: 'created' };
  }
  const current = sheet.getRange(1, 1, 1, headers.length).getValues()[0]
    .map(_virgilioInboxStringOrEmpty_);
  if (_virgilioInboxHeadersEqual_(current, headers)) {
    _virgilioInboxFormatSheet_(sheet, headers.length);
    return { action: 'unchanged' };
  }
  if (lastRow > 1) {
    throw new Error('Header Virgilio_Inbox incompatibile con righe dati esistenti.');
  }
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  _virgilioInboxFormatSheet_(sheet, headers.length);
  return { action: 'rewritten' };
}

function _virgilioInboxValidateIntakePayload_(payload) {
  const errors = [];
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    errors.push(_driveStagingError_('INVALID_PAYLOAD', 'Payload Virgilio_Inbox non valido.'));
  } else {
    if (payload.action !== VIRGILIO_INBOX_INTAKE_ACTION) {
      errors.push(_driveStagingError_('INVALID_ACTION', 'action non supportata.'));
    }
    const forbidden = _caronteDryRunFindForbidden_(payload, '$');
    forbidden.forEach(path => {
      errors.push(_driveStagingError_(
        'FORBIDDEN_FIELD',
        `Campo vietato nel payload metadata-only: ${path}`
      ));
    });
    if (!payload.manifest || typeof payload.manifest !== 'object' || Array.isArray(payload.manifest)) {
      errors.push(_driveStagingError_('INVALID_MANIFEST', 'manifest obbligatorio.'));
    } else {
      const draft = caronteBuildVirgilioInboxDraftFromManifest(payload.manifest, {
        drive_file_id: _virgilioInboxStringOrEmpty_(payload.drive_file_id),
        manifest_file_id: _virgilioInboxStringOrEmpty_(payload.manifest_file_id),
        form_url: _virgilioInboxStringOrEmpty_(payload.form_url),
      });
      if (!draft.attachment_id) {
        errors.push(_driveStagingError_('MISSING_ATTACHMENT_ID', 'attachment_id mancante nel manifest.'));
      }
      if (!draft.sha256 || !/^[0-9a-f]{64}$/.test(draft.sha256)) {
        errors.push(_driveStagingError_('INVALID_SHA256', 'sha256 non valido.'));
      }
      if (!Number.isInteger(payload.manifest.size_bytes) || payload.manifest.size_bytes < 0) {
        errors.push(_driveStagingError_('INVALID_SIZE_BYTES', 'size_bytes non valido nel manifest.'));
      }
      if (!draft.fingerprint && !draft.attachment_id) {
        errors.push(_driveStagingError_(
          'MISSING_IDEMPOTENCY_KEY',
          'fingerprint o attachment_id obbligatori per idempotenza.'
        ));
      }
      ['drive_file_id', 'manifest_file_id'].forEach(field => {
        const value = _virgilioInboxStringOrEmpty_(payload[field]);
        if (!value) {
          errors.push(_driveStagingError_('MISSING_FIELD', `${field} obbligatorio dopo la verify Drive.`));
        } else if (/[\\/]/.test(value)) {
          errors.push(_driveStagingError_('INVALID_FIELD', `${field} non puo contenere path.`));
        }
      });
    }
  }
  return {
    ok: errors.length === 0,
    response: errors.length === 0
      ? null
      : _virgilioInboxIntakeResponse_(
        payload || {}, false, '', false, false, false, 0,
        'Richiesta intake inbox rifiutata.', errors
      )
  };
}

function _virgilioInboxValidateGmailPayload_(payload) {
  const normalized = payload && typeof payload === 'object' && !Array.isArray(payload)
    ? {
      action: _virgilioInboxStringOrEmpty_(payload.action) || 'gmail_inbox_intake',
      created_at: _virgilioInboxStringOrEmpty_(payload.created_at),
      command_id: _virgilioInboxStringOrEmpty_(payload.command_id),
      account_alias: _virgilioInboxStringOrEmpty_(payload.account_alias),
      source_email: _virgilioInboxStringOrEmpty_(payload.source_email),
      source_mailbox: _virgilioInboxStringOrEmpty_(payload.source_mailbox),
      source_message_id: _virgilioInboxStringOrEmpty_(payload.source_message_id),
      source_message_uid: _virgilioInboxStringOrEmpty_(payload.source_message_uid),
      attachment_index: Number.isInteger(payload.attachment_index)
        ? payload.attachment_index
        : 0,
      attachment_id: _virgilioInboxStringOrEmpty_(payload.attachment_id),
      fingerprint: _virgilioInboxStringOrEmpty_(payload.fingerprint),
      sha256: _virgilioInboxStringOrEmpty_(payload.sha256),
      original_filename: _virgilioInboxStringOrEmpty_(payload.original_filename),
      staged_filename: _virgilioInboxStringOrEmpty_(payload.staged_filename),
      drive_file_id: _virgilioInboxStringOrEmpty_(payload.drive_file_id),
      form_url: _virgilioInboxStringOrEmpty_(payload.form_url),
      source_subject: _virgilioInboxStringOrEmpty_(payload.source_subject),
      source_sender: _virgilioInboxStringOrEmpty_(payload.source_sender),
      source_message_date: _virgilioInboxStringOrEmpty_(payload.source_message_date),
      note: _virgilioInboxStringOrEmpty_(payload.note),
      status_reason: _virgilioInboxStringOrEmpty_(payload.status_reason),
      scan_result: _virgilioInboxStringOrEmpty_(payload.scan_result),
      policy_rule: _virgilioInboxStringOrEmpty_(payload.policy_rule),
      inboxIdFactory: payload.inboxIdFactory,
    }
    : null;

  const errors = [];
  if (!normalized) {
    errors.push(_driveStagingError_('INVALID_PAYLOAD', 'Payload Gmail Virgilio_Inbox non valido.'));
  } else {
    ['drive_file_id', 'source_message_id', 'original_filename', 'staged_filename', 'source_sender']
      .forEach(field => {
        if (!_virgilioInboxStringOrEmpty_(normalized[field])) {
          errors.push(_driveStagingError_('MISSING_FIELD', `${field} obbligatorio per l intake Gmail.`));
        }
      });
    if (normalized.attachment_index < 0) {
      errors.push(_driveStagingError_('INVALID_FIELD', 'attachment_index non valido.'));
    }
  }

  return {
    ok: errors.length === 0,
    payload: normalized || {},
    response: errors.length === 0
      ? null
      : _virgilioInboxIntakeResponse_(
        normalized || {}, false, '', false, false, false, 0,
        'Richiesta intake inbox Gmail rifiutata.', errors
      )
  };
}

function _virgilioInboxUpsertDraft_(sheet, draft, options) {
  const settings = options && typeof options === 'object' && !Array.isArray(options)
    ? options
    : {};
  const existing = _virgilioInboxFindExistingRow_(
    sheet,
    _virgilioInboxEntryKey_(draft),
    _virgilioInboxStringOrEmpty_(draft.sha256)
  );
  if (existing.conflict) {
    registraConflitto('virgilioInboxUpsertDraft', existing.conflict, {
      account_alias: draft.account_alias,
      source_email: draft.source_email,
      source_message_id: draft.source_message_id,
      source_message_uid: draft.source_message_uid,
      source_subject: draft.source_subject,
      source_sender: draft.source_sender,
      attachment_id: draft.attachment_id,
      fingerprint: draft.fingerprint,
      sha256: draft.sha256,
      original_filename: draft.original_filename,
      staged_filename: draft.staged_filename,
      drive_file_id: draft.drive_file_id,
      manifest_file_id: draft.manifest_file_id,
      inbox_id: draft.inbox_id,
    });
    throw new Error(existing.conflict);
  }
  if (existing.row > 0) {
    const merged = _virgilioInboxMergeEntry_(existing.entry, draft);
    const changed = !_virgilioInboxEntriesEqual_(existing.entry, merged);
    if (changed) {
      _virgilioInboxWriteEntry_(sheet, existing.row, merged);
    }
    return {
      inbox_id: merged.inbox_id,
      row: existing.row,
      created: false,
      updated: changed,
      idempotent: !changed,
    };
  }

  const newEntry = _virgilioInboxMergeEntry_({}, draft);
  newEntry.inbox_id = _virgilioInboxGenerateId_(settings.now, settings.inboxIdFactory);
  _virgilioInboxAppendEntry_(sheet, newEntry);
  return {
    inbox_id: newEntry.inbox_id,
    row: sheet.getLastRow(),
    created: true,
    updated: false,
    idempotent: false,
  };
}

function _virgilioInboxFindExistingRow_(sheet, key, sha256) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return { row: 0, entry: null, conflict: '' };
  const values = sheet.getRange(2, 1, lastRow - 1, VIRGILIO_INBOX_FIELDS.length).getValues();
  let match = null;
  for (let index = 0; index < values.length; index += 1) {
    const rowNumber = index + 2;
    const entry = _virgilioInboxEntryFromRow_(values[index]);
    const entryKey = _virgilioInboxEntryKey_(entry);
    if (!entryKey) continue;
    if (entryKey !== key) continue;
    if (match) {
      return { row: 0, entry: null, conflict: 'Chiave inbox duplicata su piu righe esistenti.' };
    }
    if (_virgilioInboxStringOrEmpty_(entry.sha256) !== sha256) {
      return {
        row: 0,
        entry: null,
        conflict: 'Fingerprint o attachment_id gia registrato con SHA-256 differente.',
      };
    }
    match = { row: rowNumber, entry: entry, conflict: '' };
  }
  return match || { row: 0, entry: null, conflict: '' };
}

function _virgilioInboxFindFormContextByInboxId_(sheet, inboxId) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    return {
      ok: false,
      inbox_id: inboxId,
      found: false,
      message: 'Virgilio_Inbox vuoto.',
    };
  }
  const values = sheet.getRange(2, 1, lastRow - 1, VIRGILIO_INBOX_FIELDS.length).getValues();
  for (let index = 0; index < values.length; index += 1) {
    const entry = _virgilioInboxEntryFromRow_(values[index]);
    if (_virgilioInboxStringOrEmpty_(entry.inbox_id) !== inboxId) continue;
    return {
      ok: true,
      inbox_id: inboxId,
      found: true,
      status: _virgilioInboxStringOrEmpty_(entry.status),
      source_subject: _virgilioInboxStringOrEmpty_(entry.source_subject),
      source_sender: _virgilioInboxStringOrEmpty_(entry.source_sender),
      original_filename: _virgilioInboxStringOrEmpty_(entry.original_filename),
      staged_filename: _virgilioInboxStringOrEmpty_(entry.staged_filename),
      suggested_cliente: _virgilioInboxStringOrEmpty_(entry.suggested_cliente),
      suggested_sito: _virgilioInboxStringOrEmpty_(entry.suggested_sito),
      suggested_pratica: _virgilioInboxStringOrEmpty_(entry.suggested_pratica),
    };
  }
  return {
    ok: false,
    inbox_id: inboxId,
    found: false,
    message: 'inbox_id non trovato in Virgilio_Inbox.',
  };
}

function _virgilioInboxFindRowByInboxId_(sheet, inboxId) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    return { found: false, row: 0, entry: null };
  }
  const values = sheet.getRange(2, 1, lastRow - 1, VIRGILIO_INBOX_FIELDS.length).getValues();
  for (let index = 0; index < values.length; index += 1) {
    const entry = _virgilioInboxEntryFromRow_(values[index]);
    if (_virgilioInboxStringOrEmpty_(entry.inbox_id) !== inboxId) continue;
    return {
      found: true,
      row: index + 2,
      entry: entry,
    };
  }
  return { found: false, row: 0, entry: null };
}

function _virgilioInboxFindArchiveContextByInboxId_(sheet, inboxId) {
  const match = _virgilioInboxFindRowByInboxId_(sheet, inboxId);
  if (!match.found) {
    return {
      ok: false,
      inbox_id: inboxId,
      found: false,
      message: 'inbox_id non trovato in Virgilio_Inbox.',
    };
  }
  return {
    ok: true,
    inbox_id: inboxId,
    found: true,
    status: _virgilioInboxStringOrEmpty_(match.entry.status),
    drive_file_id: _virgilioInboxStringOrEmpty_(match.entry.drive_file_id),
    original_filename: _virgilioInboxStringOrEmpty_(match.entry.original_filename),
    staged_filename: _virgilioInboxStringOrEmpty_(match.entry.staged_filename),
    source_subject: _virgilioInboxStringOrEmpty_(match.entry.source_subject),
    source_sender: _virgilioInboxStringOrEmpty_(match.entry.source_sender),
  };
}

function _virgilioInboxEntryKey_(entry) {
  const fingerprint = _virgilioInboxStringOrEmpty_(entry && entry.fingerprint);
  if (fingerprint) return `fingerprint:${fingerprint}`;
  const attachmentId = _virgilioInboxStringOrEmpty_(entry && entry.attachment_id);
  return attachmentId ? `attachment_id:${attachmentId}` : '';
}

function _virgilioInboxNormalizeSubmitPayload_(payload) {
  const normalized = payload && typeof payload === 'object' && !Array.isArray(payload)
    ? {
      inbox_id: _virgilioInboxStringOrEmpty_(payload.inbox_id),
      cliente: _virgilioInboxStringOrEmpty_(payload.cliente),
      sito: _virgilioInboxStringOrEmpty_(payload.sito),
      pratica: _virgilioInboxStringOrEmpty_(payload.pratica),
      anno: _virgilioInboxStringOrEmpty_(payload.anno),
      note: _virgilioInboxStringOrEmpty_(payload.note),
      tecnici: Array.isArray(payload.tecnici)
        ? payload.tecnici.map(_virgilioInboxStringOrEmpty_).filter(Boolean)
        : [],
      submitted_at: _virgilioInboxStringOrEmpty_(payload.submitted_at),
    }
    : null;
  if (!normalized) {
    return {
      ok: false,
      response: {
        ok: false,
        inbox_id: '',
        linked: false,
        updated: false,
        status: '',
        message: 'Payload submit inbox non valido.',
      }
    };
  }
  if (!normalized.inbox_id) {
    return {
      ok: false,
      response: {
        ok: false,
        inbox_id: '',
        linked: false,
        updated: false,
        status: '',
        message: 'inbox_id obbligatorio per collegare il submit.',
      }
    };
  }
  return { ok: true, payload: normalized };
}

function _virgilioInboxNormalizeArchivePayload_(payload) {
  const normalized = payload && typeof payload === 'object' && !Array.isArray(payload)
    ? {
      inbox_id: _virgilioInboxStringOrEmpty_(payload.inbox_id),
      archived_at: _virgilioInboxStringOrEmpty_(payload.archived_at),
      archived_file_id: _virgilioInboxStringOrEmpty_(payload.archived_file_id),
      destination_folder_id: _virgilioInboxStringOrEmpty_(payload.destination_folder_id),
      destination_folder_url: _virgilioInboxStringOrEmpty_(payload.destination_folder_url),
      pratica_folder_id: _virgilioInboxStringOrEmpty_(payload.pratica_folder_id),
      pratica_folder_url: _virgilioInboxStringOrEmpty_(payload.pratica_folder_url),
    }
    : null;
  if (!normalized) {
    return {
      ok: false,
      response: {
        ok: false,
        inbox_id: '',
        archived: false,
        updated: false,
        status: '',
        message: 'Payload archiviazione inbox non valido.',
      }
    };
  }
  if (!normalized.inbox_id) {
    return {
      ok: false,
      response: {
        ok: false,
        inbox_id: '',
        archived: false,
        updated: false,
        status: '',
        message: 'inbox_id obbligatorio per archiviare il record.',
      }
    };
  }
  if (!normalized.archived_file_id) {
    return {
      ok: false,
      response: {
        ok: false,
        inbox_id: normalized.inbox_id,
        archived: false,
        updated: false,
        status: '',
        message: 'archived_file_id obbligatorio per archiviare il record.',
      }
    };
  }
  if (!normalized.destination_folder_id) {
    return {
      ok: false,
      response: {
        ok: false,
        inbox_id: normalized.inbox_id,
        archived: false,
        updated: false,
        status: '',
        message: 'destination_folder_id obbligatorio per archiviare il record.',
      }
    };
  }
  return { ok: true, payload: normalized };
}

function _virgilioInboxApplySubmitToEntry_(entry, payload) {
  const linked = _virgilioInboxMergeEntry_(entry, {});
  linked.status = 'in_lavorazione';
  linked.suggested_cliente = payload.cliente || linked.suggested_cliente;
  linked.suggested_sito = payload.sito || linked.suggested_sito;
  linked.suggested_pratica = payload.pratica || linked.suggested_pratica;
  linked.notes = _virgilioInboxUpsertNotes_(linked.notes, {
    form_cliente: payload.cliente,
    form_sito: payload.sito,
    form_pratica: payload.pratica,
    form_anno: payload.anno,
    form_tecnici: payload.tecnici.join(', '),
    form_note: payload.note,
    form_submitted_at: payload.submitted_at,
  });
  return linked;
}

function _virgilioInboxApplyArchiveToEntry_(entry, payload) {
  const archived = _virgilioInboxMergeEntry_(entry, {});
  archived.status = 'archiviato';
  archived.notes = _virgilioInboxUpsertNotes_(archived.notes, {
    archived_at: payload.archived_at,
    archived_file_id: payload.archived_file_id,
    destination_folder_id: payload.destination_folder_id,
    destination_folder_url: payload.destination_folder_url,
    pratica_folder_id: payload.pratica_folder_id,
    pratica_folder_url: payload.pratica_folder_url,
  });
  return archived;
}

function _virgilioInboxUpsertNotes_(notes, updates) {
  const parts = [];
  const seen = {};
  _virgilioInboxStringOrEmpty_(notes)
    .split(';')
    .map(item => _virgilioInboxStringOrEmpty_(item))
    .filter(Boolean)
    .forEach(item => {
      const separator = item.indexOf('=');
      if (separator <= 0) {
        parts.push(item);
        return;
      }
      const key = _virgilioInboxStringOrEmpty_(item.slice(0, separator));
      const value = _virgilioInboxStringOrEmpty_(item.slice(separator + 1));
      if (!key) return;
      seen[key] = parts.length;
      parts.push(`${key}=${value}`);
    });

  Object.keys(updates || {}).forEach(key => {
    const value = _virgilioInboxNormalizeNoteValue_(updates[key]);
    if (!value) return;
    const entry = `${key}=${value}`;
    if (Object.prototype.hasOwnProperty.call(seen, key)) {
      parts[seen[key]] = entry;
    } else {
      seen[key] = parts.length;
      parts.push(entry);
    }
  });

  return parts.join('; ');
}

function _virgilioInboxMergeEntry_(existing, draft) {
  const merged = {};
  VIRGILIO_INBOX_FIELDS.forEach(field => {
    const currentValue = _virgilioInboxStringOrEmpty_(existing && existing[field]);
    const draftValue = _virgilioInboxStringOrEmpty_(draft && draft[field]);
    switch (field) {
      case 'inbox_id':
        merged[field] = currentValue || draftValue;
        break;
      case 'created_at':
        merged[field] = currentValue || draftValue;
        break;
      case 'status':
        merged[field] = currentValue || draftValue || VIRGILIO_INBOX_DEFAULT_STATUS;
        break;
      case 'suggested_cliente':
      case 'suggested_sito':
      case 'suggested_pratica':
      case 'form_url':
        merged[field] = currentValue || draftValue;
        break;
      default:
        merged[field] = draftValue || currentValue;
        break;
    }
  });
  return merged;
}

function _virgilioInboxEntriesEqual_(left, right) {
  return VIRGILIO_INBOX_FIELDS.every(field =>
    _virgilioInboxStringOrEmpty_(left && left[field]) ===
      _virgilioInboxStringOrEmpty_(right && right[field])
  );
}

function _virgilioInboxEntryFromRow_(row) {
  const entry = {};
  VIRGILIO_INBOX_FIELDS.forEach((field, index) => {
    entry[field] = _virgilioInboxStringOrEmpty_(row && row[index]);
  });
  return entry;
}

function _virgilioInboxWriteEntry_(sheet, row, entry) {
  sheet.getRange(row, 1, 1, VIRGILIO_INBOX_FIELDS.length)
    .setValues([_virgilioInboxEntryToRow_(entry)]);
}

function _virgilioInboxAppendEntry_(sheet, entry) {
  sheet.appendRow(_virgilioInboxEntryToRow_(entry));
}

function _virgilioInboxEntryToRow_(entry) {
  return VIRGILIO_INBOX_FIELDS.map(field => _virgilioInboxStringOrEmpty_(entry[field]));
}

function _virgilioInboxGenerateId_(now, customFactory) {
  if (typeof customFactory === 'function') return customFactory();
  const prefix = Utilities.formatDate(now || new Date(), 'UTC', "yyyyMMddHHmmss");
  return `inbox-${prefix}-${Utilities.getUuid()}`;
}

function _virgilioInboxIntakeResponse_(payload, ok, inboxId, created, updated,
                                       idempotent, row, message, errors) {
  return {
    ok: ok,
    action: payload && payload.action || '',
    inbox_id: inboxId,
    created: created === true,
    updated: updated === true,
    idempotent: idempotent === true,
    row: Number.isInteger(row) ? row : 0,
    message: message,
    errors: Array.isArray(errors) ? errors : [],
  };
}

function _virgilioInboxFormatSheet_(sheet, headerLength) {
  const range = sheet.getRange(1, 1, 1, headerLength);
  range.setFontWeight('bold')
    .setBackground('#274C77')
    .setFontColor('#FFFFFF');
  sheet.setFrozenRows(1);
  VIRGILIO_INBOX_COLUMN_WIDTHS.slice(0, headerLength).forEach((width, index) => {
    sheet.setColumnWidth(index + 1, width);
  });
}

function _virgilioInboxHeadersEqual_(left, right) {
  if (!Array.isArray(left) || !Array.isArray(right) || left.length !== right.length) {
    return false;
  }
  for (let index = 0; index < left.length; index += 1) {
    if (_virgilioInboxStringOrEmpty_(left[index]) !== _virgilioInboxStringOrEmpty_(right[index])) {
      return false;
    }
  }
  return true;
}

function _virgilioInboxStringOrEmpty_(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function _virgilioInboxNormalizeNoteValue_(value) {
  return _virgilioInboxStringOrEmpty_(value)
    .replace(/[;=]+/g, ', ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Test puri: nessuna lettura/scrittura reale su Sheets. */
function testVirgilioInboxSchema() {
  const emptySheet = _virgilioInboxFakeSheet_(0, []);
  const created = _virgilioInboxEnsureHeader_(emptySheet, VIRGILIO_INBOX_FIELDS);
  _driveStagingAssert_(created.action === 'created', 'header creato');
  _driveStagingAssert_(emptySheet.rows[0][0] === 'inbox_id', 'prima colonna inbox_id');

  const correctSheet = _virgilioInboxFakeSheet_(1, [VIRGILIO_INBOX_FIELDS.slice()]);
  const unchanged = _virgilioInboxEnsureHeader_(correctSheet, VIRGILIO_INBOX_FIELDS);
  _driveStagingAssert_(unchanged.action === 'unchanged', 'header invariato');

  const rewriteSheet = _virgilioInboxFakeSheet_(1, [new Array(VIRGILIO_INBOX_FIELDS.length).fill('')]);
  const rewritten = _virgilioInboxEnsureHeader_(rewriteSheet, VIRGILIO_INBOX_FIELDS);
  _driveStagingAssert_(rewritten.action === 'rewritten', 'header riscritto');
  _driveStagingAssert_(rewriteSheet.rows[0][VIRGILIO_INBOX_FIELDS.length - 1] === 'notes',
    'ultima colonna notes');

  let failed = false;
  try {
    _virgilioInboxEnsureHeader_(
      _virgilioInboxFakeSheet_(2, [['legacy'], ['row']]),
      VIRGILIO_INBOX_FIELDS
    );
  } catch (err) {
    failed = err.message.indexOf('incompatibile') >= 0;
  }
  _driveStagingAssert_(failed, 'mismatch con dati esistenti');

  const payload = {
    action: VIRGILIO_INBOX_INTAKE_ACTION,
    manifest: _caronteInboxManifestSample_(),
    drive_file_id: 'drive-1',
    manifest_file_id: 'manifest-1',
  };
  _driveStagingAssert_(_virgilioInboxValidateIntakePayload_(payload).ok, 'payload intake valido');

  const rows = [VIRGILIO_INBOX_FIELDS.slice()];
  const fakeSheet = _virgilioInboxFakeSheet_(1, rows);
  const createdEntry = _virgilioInboxUpsertDraft_(
    fakeSheet,
    caronteBuildVirgilioInboxDraftFromManifest(payload.manifest, {
      drive_file_id: payload.drive_file_id,
      manifest_file_id: payload.manifest_file_id,
    }),
    { inboxIdFactory: () => 'inbox-fixed-1' }
  );
  _driveStagingAssert_(createdEntry.created && createdEntry.row === 2, 'riga inbox creata');
  _driveStagingAssert_(rows[1][0] === 'inbox-fixed-1', 'inbox_id assegnato');

  const retry = _virgilioInboxUpsertDraft_(
    fakeSheet,
    caronteBuildVirgilioInboxDraftFromManifest(payload.manifest, {
      drive_file_id: payload.drive_file_id,
      manifest_file_id: payload.manifest_file_id,
    }),
    { inboxIdFactory: () => 'inbox-fixed-2' }
  );
  _driveStagingAssert_(retry.idempotent && !retry.created && rows.length === 2,
    'retry idempotente senza duplicati');

  const updatedManifest = _caronteInboxManifestSample_();
  updatedManifest.note = 'nota aggiornata';
  const updated = _virgilioInboxUpsertDraft_(
    fakeSheet,
    caronteBuildVirgilioInboxDraftFromManifest(updatedManifest, {
      drive_file_id: payload.drive_file_id,
      manifest_file_id: payload.manifest_file_id,
    }),
    { inboxIdFactory: () => 'inbox-fixed-3' }
  );
  _driveStagingAssert_(updated.updated && rows[1][21] === 'note=nota aggiornata; status_reason=fake clean; source_mailbox=Virgilio/da-traghettare; source_message_date=2026-06-25T10:00:00+00:00; scan_result=clean; policy_rule=solo-pdf',
    'update stesso record');

  let conflict = false;
  try {
    const conflicting = _caronteInboxManifestSample_();
    conflicting.sha256 = 'b'.repeat(64);
    _virgilioInboxUpsertDraft_(fakeSheet,
      caronteBuildVirgilioInboxDraftFromManifest(conflicting, {}),
      { inboxIdFactory: () => 'inbox-fixed-4' });
  } catch (err) {
    conflict = err.message.indexOf('SHA-256 differente') >= 0;
  }
  _driveStagingAssert_(conflict, 'conflitto sha256');

  const visibilityFolder = _driveStagingFakeFolder_(_driveStagingTestPayload_(), true, true);
  _driveStagingAssert_(
    _driveStagingVerifyInboxVisibilityInFolder_(payload, visibilityFolder).ok,
    'gate visibilita drive ok'
  );
  const payloadMissingDriveId = Object.assign({}, payload);
  delete payloadMissingDriveId.drive_file_id;
  _driveStagingAssert_(
    !_virgilioInboxValidateIntakePayload_(payloadMissingDriveId).ok,
    'drive_file_id obbligatorio dopo verify'
  );

  const formContext = _virgilioInboxFindFormContextByInboxId_(fakeSheet, 'inbox-fixed-1');
  _driveStagingAssert_(formContext.ok && formContext.found, 'lookup inbox_id per form');
  _driveStagingAssert_(formContext.original_filename === 'documento.pdf', 'filename esposto al form');
  const missingContext = _virgilioInboxFindFormContextByInboxId_(fakeSheet, 'missing');
  _driveStagingAssert_(!missingContext.ok && !missingContext.found, 'lookup inbox_id mancante');
  const linkedEntry = _virgilioInboxApplySubmitToEntry_(_virgilioInboxEntryFromRow_(rows[1]), {
    cliente: 'Cliente Demo',
    sito: 'Sito Demo',
    pratica: 'AIA',
    anno: '2026',
    note: 'nota utente',
    tecnici: ['Marco', 'Sara'],
    submitted_at: '2026-07-01 20:00:00',
  });
  _driveStagingAssert_(linkedEntry.status === 'in_lavorazione', 'submit cambia stato inbox');
  _driveStagingAssert_(linkedEntry.suggested_cliente === 'Cliente Demo', 'submit salva cliente');
  _driveStagingAssert_(linkedEntry.notes.indexOf('form_pratica=AIA') >= 0, 'submit traccia pratica');
  const archivedEntry = _virgilioInboxApplyArchiveToEntry_(linkedEntry, {
    archived_at: '2026-07-01 20:05:00',
    archived_file_id: 'drive-1',
    destination_folder_id: 'folder-corrispondenza',
    destination_folder_url: 'https://drive.google.com/drive/folders/folder-corrispondenza',
    pratica_folder_id: 'folder-pratica',
    pratica_folder_url: 'https://drive.google.com/drive/folders/folder-pratica',
  });
  _driveStagingAssert_(archivedEntry.status === 'archiviato', 'archiviazione cambia stato inbox');
  _driveStagingAssert_(archivedEntry.notes.indexOf('destination_folder_id=folder-corrispondenza') >= 0,
    'archiviazione traccia cartella finale');

  const gmailDraft = caronteBuildVirgilioInboxDraftFromGmail({
    created_at: '2026-07-03T10:00:00Z',
    command_id: 'gmail_staging',
    account_alias: 'marco@sigmapiu.it',
    source_email: 'marco@sigmapiu.it',
    source_message_id: 'msg-gmail-123',
    source_message_uid: 'thread-gmail-123',
    attachment_index: 0,
    original_filename: 'analisi.pdf',
    staged_filename: '2026-07-03_cliente_msg-gmail-123_analisi.pdf',
    source_subject: 'Documento da archiviare',
    source_sender: 'Mario Rossi <mario@example.com>',
    source_mailbox: 'marco@sigmapiu.it',
    source_message_date: '2026-07-03 10:00:00',
    note: 'salvato dal polling Gmail',
  }, {
    drive_file_id: 'drive-gmail-123',
  });
  _driveStagingAssert_(gmailDraft.status === VIRGILIO_INBOX_DEFAULT_STATUS, 'gmail stato inbox default');
  _driveStagingAssert_(gmailDraft.command_id === 'gmail_staging', 'gmail command id');
  _driveStagingAssert_(gmailDraft.attachment_id === 'gmail:msg-gmail-123:0:analisi.pdf', 'gmail attachment key');
  _driveStagingAssert_(gmailDraft.fingerprint === gmailDraft.attachment_id, 'gmail fingerprint allineato');
  _driveStagingAssert_(gmailDraft.manifest_file_id === '', 'gmail senza manifest file');
  _driveStagingAssert_(gmailDraft.notes.indexOf('policy_rule=da_archiviare') >= 0, 'gmail note mapping');

  const gmailRows = [VIRGILIO_INBOX_FIELDS.slice()];
  const gmailSheet = _virgilioInboxFakeSheet_(1, gmailRows);
  const gmailCreated = _virgilioInboxUpsertDraft_(
    gmailSheet,
    gmailDraft,
    { inboxIdFactory: () => 'inbox-gmail-1' }
  );
  _driveStagingAssert_(gmailCreated.created && gmailCreated.row === 2, 'gmail inbox creata');
  const gmailRetry = _virgilioInboxUpsertDraft_(
    gmailSheet,
    gmailDraft,
    { inboxIdFactory: () => 'inbox-gmail-2' }
  );
  _driveStagingAssert_(gmailRetry.idempotent && gmailRows.length === 2, 'gmail retry idempotente');
  Logger.log('testVirgilioInboxSchema: OK');
}

function _virgilioInboxFakeSheet_(lastRow, rows) {
  return {
    rows: rows,
    getName: () => VIRGILIO_INBOX_DEFAULT_SHEET,
    appendRow: row => rows.push(row),
    getLastRow: () => lastRow === 0 ? rows.length : Math.max(lastRow, rows.length),
    getRange: (row, column, numRows, numColumns) => ({
      getValues: () => {
        if (numRows && numColumns) {
          return rows.slice(row - 1, row - 1 + numRows)
            .map(value => (value || []).slice(column - 1, column - 1 + numColumns));
        }
        return [rows[row - 1] || []];
      },
      setValues: values => {
        for (let index = 0; index < values.length; index += 1) {
          const targetRow = row - 1 + index;
          rows[targetRow] = rows[targetRow] || [];
          for (let columnIndex = 0; columnIndex < values[index].length; columnIndex += 1) {
            rows[targetRow][column - 1 + columnIndex] = values[index][columnIndex];
          }
        }
      },
      setFontWeight: () => ({
        setBackground: () => ({
          setFontColor: () => null
        })
      })
    }),
    setFrozenRows: value => {
      rows._frozen = value;
    },
    setColumnWidth: (index, width) => {
      rows._widths = rows._widths || [];
      rows._widths[index - 1] = width;
    }
  };
}
