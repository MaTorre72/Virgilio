/**
 * Bridge metadata-only per il Local IMAP Connector.
 * Non usa Drive, Gmail, Sheets, notifiche o altri servizi con effetti persistenti.
 */

const CARONTE_DRY_RUN_ACTION = 'local_imap_dry_run';
const CARONTE_DRY_RUN_SCHEMA = '1.0';
const CARONTE_DRY_RUN_CONNECTOR = 'local_imap';
const CARONTE_DRY_RUN_REQUESTED_ACTION = 'stage_attachments_in_limbo';
const CARONTE_DRY_RUN_FORBIDDEN_FIELDS = [
  'local_path', 'file_path', 'staged_path', 'manifest_path',
  'file_bytes', 'base64', 'content', 'raw'
];
const VIRGILIO_INBOX_DEFAULT_STATUS = 'da_lavorare';
const VIRGILIO_INBOX_FIELDS = [
  'inbox_id', 'created_at', 'status', 'command_id', 'account_alias',
  'source_email', 'source_message_id', 'source_message_uid', 'attachment_id',
  'fingerprint', 'sha256', 'original_filename', 'staged_filename',
  'drive_file_id', 'manifest_file_id', 'source_subject', 'source_sender',
  'suggested_cliente', 'suggested_sito', 'suggested_pratica', 'form_url', 'notes'
];
const CARONTE_MANIFEST_TO_VIRGILIO_INBOX_MAP = Object.freeze({
  inbox_id: { source: null, stage: 'later', note: 'Generato dallo schema inbox.' },
  created_at: { source: 'created_at|staged_at', stage: 'now', note: 'Timestamp del manifest o staging.' },
  status: { source: null, stage: 'now', note: 'Valore fisso da_lavorare.' },
  command_id: { source: 'command_id', stage: 'now', note: 'Vuoto se il manifest non lo trasporta ancora.' },
  account_alias: { source: 'account_alias', stage: 'now', note: 'Alias locale non segreto.' },
  source_email: { source: 'source_email', stage: 'now', note: 'Email operativa locale.' },
  source_message_id: { source: 'source_message_id', stage: 'now', note: 'Header Message-ID di correlazione.' },
  source_message_uid: { source: 'source_message_uid', stage: 'now', note: 'UID IMAP nel contesto mailbox.' },
  attachment_id: { source: 'attachment_id', stage: 'now', note: 'Identificativo allegato stabile.' },
  fingerprint: { source: 'fingerprint', stage: 'now', note: 'Chiave tecnica primaria per idempotenza futura.' },
  sha256: { source: 'sha256', stage: 'now', note: 'Hash contenuto allegato.' },
  original_filename: { source: 'original_filename', stage: 'now', note: 'Nome file originale.' },
  staged_filename: { source: 'staged_filename', stage: 'now', note: 'Nome file nello staging condiviso.' },
  drive_file_id: { source: null, stage: 'later', note: 'Disponibile solo dopo verifica/lookup Drive.' },
  manifest_file_id: { source: null, stage: 'later', note: 'Disponibile solo dopo lookup manifest su Drive.' },
  source_subject: { source: 'subject', stage: 'now', note: 'Oggetto email del manifest locale.' },
  source_sender: { source: 'source_sender', stage: 'now', note: 'Mittente email del manifest locale.' },
  suggested_cliente: { source: null, stage: 'later', note: 'Resta vuoto fino a suggerimenti controllati.' },
  suggested_sito: { source: null, stage: 'later', note: 'Resta vuoto fino a suggerimenti controllati.' },
  suggested_pratica: { source: null, stage: 'later', note: 'Resta vuoto fino a suggerimenti controllati.' },
  form_url: { source: null, stage: 'later', note: 'Disponibile dopo apertura form correlata.' },
  notes: { source: 'note+status_reason+source_mailbox+source_message_date+scan_result+policy_rule', stage: 'now', note: 'Compatta metadati utili non modellati come colonne.' },
});

/**
 * Valida un comando gia' parsato e restituisce esclusivamente un esito dry-run.
 *
 * @param {Object} payload Comando conforme al contratto Caronte 1.0.
 * @returns {Object} Risposta metadata-only senza identificativi Drive/Bucoliche.
 */
function caronteRiceviComandoDryRun(payload) {
  const errors = [];
  const command = payload && typeof payload === 'object' && !Array.isArray(payload)
    ? payload
    : null;

  if (!command) {
    errors.push(_caronteDryRunError_('INVALID_PAYLOAD', 'Payload JSON non valido.'));
    return _caronteDryRunResponse_(false, 0, 0, 'Comando dry-run rifiutato.', errors);
  }

  const forbidden = _caronteDryRunFindForbidden_(command, '$');
  forbidden.forEach(path => errors.push(_caronteDryRunError_(
    'FORBIDDEN_FIELD', `Campo vietato nel payload metadata-only: ${path}`
  )));

  if (command.schema_version !== CARONTE_DRY_RUN_SCHEMA) {
    errors.push(_caronteDryRunError_('INVALID_SCHEMA_VERSION', 'schema_version non supportata.'));
  }
  if (command.connector_type !== CARONTE_DRY_RUN_CONNECTOR) {
    errors.push(_caronteDryRunError_('INVALID_CONNECTOR_TYPE', 'connector_type deve essere local_imap.'));
  }
  if (command.dry_run !== true) {
    errors.push(_caronteDryRunError_('DRY_RUN_REQUIRED', 'dry_run deve essere true.'));
  }
  if (command.requested_action !== CARONTE_DRY_RUN_REQUESTED_ACTION) {
    errors.push(_caronteDryRunError_('INVALID_REQUESTED_ACTION', 'requested_action non supportata.'));
  }
  if (!Array.isArray(command.attachments)) {
    errors.push(_caronteDryRunError_('INVALID_ATTACHMENTS', 'attachments deve essere un array.'));
  }

  const attachments = Array.isArray(command.attachments) ? command.attachments : [];
  attachments.forEach((attachment, index) => {
    const prefix = `attachments[${index}]`;
    if (!attachment || typeof attachment !== 'object' || Array.isArray(attachment)) {
      errors.push(_caronteDryRunError_('INVALID_ATTACHMENT', `${prefix} non e' un oggetto.`));
      return;
    }
    if (typeof attachment.local_temp_id !== 'string' || !attachment.local_temp_id.trim()) {
      errors.push(_caronteDryRunError_('MISSING_LOCAL_TEMP_ID', `${prefix}.local_temp_id mancante.`));
    }
    if (typeof attachment.sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(attachment.sha256)) {
      errors.push(_caronteDryRunError_('INVALID_SHA256', `${prefix}.sha256 non valido.`));
    }
    if (attachment.quarantine_status !== 'ready_for_caronte') {
      errors.push(_caronteDryRunError_(
        'ATTACHMENT_NOT_READY', `${prefix}.quarantine_status deve essere ready_for_caronte.`
      ));
    }
  });

  if (errors.length > 0) {
    return _caronteDryRunResponse_(
      false, 0, attachments.length, 'Comando dry-run rifiutato.', errors
    );
  }
  return _caronteDryRunResponse_(
    true, attachments.length, 0, 'Comando dry-run validato; nessun effetto operativo.', []
  );
}

function _caronteDryRunResponse_(ok, accepted, rejected, message, errors) {
  return {
    ok: ok,
    dry_run: true,
    accepted_attachments: accepted,
    rejected_attachments: rejected,
    limbo_drive_ids: [],
    bucoliche_rows: [],
    message: message,
    errors: errors
  };
}

function _caronteDryRunError_(code, message) {
  return { code: code, message: message };
}

function _caronteDryRunFindForbidden_(value, path) {
  const found = [];
  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      found.push(..._caronteDryRunFindForbidden_(item, `${path}[${index}]`));
    });
    return found;
  }
  if (!value || typeof value !== 'object') return found;
  Object.keys(value).forEach(key => {
    if (CARONTE_DRY_RUN_FORBIDDEN_FIELDS.includes(key.toLowerCase())) {
      found.push(`${path}.${key}`);
    }
    found.push(..._caronteDryRunFindForbidden_(value[key], `${path}.${key}`));
  });
  return found;
}

function caronteGetVirgilioInboxFieldMap() {
  return {
    fields: VIRGILIO_INBOX_FIELDS.slice(),
    mapping: JSON.parse(JSON.stringify(CARONTE_MANIFEST_TO_VIRGILIO_INBOX_MAP)),
  };
}

function caronteBuildVirgilioInboxDraftFromManifest(manifest, options) {
  if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest)) {
    throw new Error('Manifest Virgilio inbox non valido.');
  }
  const extra = options && typeof options === 'object' && !Array.isArray(options)
    ? options
    : {};
  const createdAt = _carontePickFirstString_(manifest, ['created_at', 'staged_at']);
  return {
    inbox_id: '',
    created_at: createdAt,
    status: VIRGILIO_INBOX_DEFAULT_STATUS,
    command_id: _caronteStringOrEmpty_(manifest.command_id),
    account_alias: _caronteStringOrEmpty_(manifest.account_alias),
    source_email: _caronteStringOrEmpty_(manifest.source_email),
    source_message_id: _caronteStringOrEmpty_(manifest.source_message_id),
    source_message_uid: _caronteStringOrEmpty_(manifest.source_message_uid),
    attachment_id: _caronteStringOrEmpty_(manifest.attachment_id),
    fingerprint: _caronteStringOrEmpty_(manifest.fingerprint),
    sha256: _caronteStringOrEmpty_(manifest.sha256),
    original_filename: _caronteStringOrEmpty_(manifest.original_filename),
    staged_filename: _caronteStringOrEmpty_(manifest.staged_filename),
    drive_file_id: _caronteStringOrEmpty_(extra.drive_file_id),
    manifest_file_id: _caronteStringOrEmpty_(extra.manifest_file_id),
    source_subject: _caronteStringOrEmpty_(manifest.subject),
    source_sender: _caronteStringOrEmpty_(manifest.source_sender),
    suggested_cliente: '',
    suggested_sito: '',
    suggested_pratica: '',
    form_url: _caronteStringOrEmpty_(extra.form_url),
    notes: _caronteInboxNotes_(manifest),
  };
}

function _caronteInboxNotes_(manifest) {
  const parts = [
    ['note', manifest.note],
    ['status_reason', manifest.status_reason],
    ['source_mailbox', manifest.source_mailbox],
    ['source_message_date', manifest.source_message_date],
    ['scan_result', manifest.scan_result],
    ['policy_rule', manifest.policy_rule],
  ].filter(item => _caronteStringOrEmpty_(item[1]) !== '')
    .map(item => `${item[0]}=${_caronteStringOrEmpty_(item[1])}`);
  return parts.join('; ');
}

function _carontePickFirstString_(source, keys) {
  for (let i = 0; i < keys.length; i += 1) {
    const value = _caronteStringOrEmpty_(source[keys[i]]);
    if (value) return value;
  }
  return '';
}

function _caronteStringOrEmpty_(value) {
  return typeof value === 'string' ? value.trim() : '';
}

/** Test manuali puri: nessuna chiamata a servizi Apps Script. */
function testCaronteBridgeDryRun() {
  const valid = _caronteDryRunTestPayload_();
  _caronteDryRunAssert_(caronteRiceviComandoDryRun(valid).ok, 'payload valido');

  const withoutAttachments = _caronteDryRunTestPayload_();
  withoutAttachments.attachments = [];
  _caronteDryRunAssert_(caronteRiceviComandoDryRun(withoutAttachments).ok, 'attachments vuoto');

  const operational = _caronteDryRunTestPayload_();
  operational.dry_run = false;
  _caronteDryRunAssert_(!caronteRiceviComandoDryRun(operational).ok, 'dry_run=false');

  ['local_path', 'base64'].forEach(field => {
    const forbidden = _caronteDryRunTestPayload_();
    forbidden.attachments[0][field] = 'vietato';
    _caronteDryRunAssert_(!caronteRiceviComandoDryRun(forbidden).ok, field);
  });

  const missingHash = _caronteDryRunTestPayload_();
  delete missingHash.attachments[0].sha256;
  _caronteDryRunAssert_(!caronteRiceviComandoDryRun(missingHash).ok, 'sha256 mancante');

  const draft = caronteBuildVirgilioInboxDraftFromManifest(_caronteInboxManifestSample_(), {
    drive_file_id: 'drive-123',
    manifest_file_id: 'manifest-123',
  });
  _caronteDryRunAssert_(draft.status === VIRGILIO_INBOX_DEFAULT_STATUS, 'stato inbox default');
  _caronteDryRunAssert_(draft.attachment_id === 'att-test-1', 'attachment_id mappato');
  _caronteDryRunAssert_(draft.drive_file_id === 'drive-123', 'drive_file_id passato da verify');
  _caronteDryRunAssert_(draft.notes.indexOf('source_mailbox=Virgilio/da-traghettare') >= 0,
    'note mapping');
  Logger.log('testCaronteBridgeDryRun: OK');
}

function _caronteDryRunTestPayload_() {
  return {
    schema_version: '1.0', connector_type: 'local_imap', dry_run: true,
    requested_action: 'stage_attachments_in_limbo',
    attachments: [{
      local_temp_id: 'att-test-1', sha256: 'a'.repeat(64),
      quarantine_status: 'ready_for_caronte'
    }]
  };
}

function _caronteInboxManifestSample_() {
  return {
    schema_version: '1.0',
    connector_type: 'local_imap',
    command_id: '01900000-0000-7000-8000-000000000001',
    created_at: '2026-07-01T12:00:00+00:00',
    account_alias: 'marco_sigmapiu',
    source_email: 'marco@example.invalid',
    source_sender: 'sender@example.invalid',
    source_mailbox: 'Virgilio/da-traghettare',
    source_message_uid: '41',
    source_message_id: '<a@example.invalid>',
    source_message_date: '2026-06-25T10:00:00+00:00',
    subject: 'Documento di prova',
    attachment_id: 'att-test-1',
    fingerprint: 'fp-test-1',
    sha256: 'a'.repeat(64),
    size_bytes: 4,
    original_filename: 'documento.pdf',
    staged_filename: 'att-test-1-documento.pdf',
    note: 'sync cloud non verificata',
    status_reason: 'fake clean',
    scan_result: 'clean',
    policy_rule: 'solo-pdf',
  };
}

function _caronteDryRunAssert_(condition, label) {
  if (!condition) throw new Error(`Test fallito: ${label}`);
}
