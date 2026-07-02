/**
 * Bridge metadata-only per il Local IMAP Connector.
 * Non usa Drive, Gmail, Sheets, notifiche o altri servizi con effetti persistenti.
 */

const CARONTE_DRY_RUN_ACTION = 'local_imap_dry_run';
const CARONTE_DRY_RUN_SCHEMA = '1.0';
const CARONTE_DRY_RUN_CONNECTOR = 'local_imap';
const CARONTE_DRY_RUN_REQUESTED_ACTION = 'stage_attachments_in_limbo';
const CARONTE_DRY_RUN_FORBIDDEN_FIELDS = [
  'local_path', 'file_path', 'file_bytes', 'base64', 'content', 'raw'
];

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

function _caronteDryRunAssert_(condition, label) {
  if (!condition) throw new Error(`Test fallito: ${label}`);
}
