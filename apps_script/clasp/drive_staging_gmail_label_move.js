/** Idempotent P4 Gmail label transition for the pilot attachment source thread. */

const DRIVE_STAGING_GMAIL_LABEL_MOVE_ACTION = 'move_gmail_thread_to_traghettate';

function caronteCompletaMailboxPilotaP4(payload, deps) {
  const validation = _driveStagingGmailLabelMoveValidatePayload_(payload);
  if (!validation.ok) return validation.response;

  try {
    const sheet = deps && deps.sheet ? deps.sheet : _aprifoglioBucoliche();
    const gate = _p4ValidateBucolicheGate_(sheet, payload);
    if (!gate.ok) {
      return _driveStagingGmailLabelMoveResponse_(
        payload, false, false, 0, false, false, false,
        false, false, false, false, '', gate.existing_row, gate.state,
        'Prerequisiti P4 non soddisfatti.', gate.errors
      );
    }

    const labels = deps && deps.labels ? deps.labels : _p4ResolveRequiredLabels_();
    if (!labels.ok) {
      return _driveStagingGmailLabelMoveResponse_(
        payload, false, false, 0, false, false, false,
        false, false, false, false, '', gate.existing_row, gate.state,
        'Label Gmail del pilota non disponibili.', labels.errors
      );
    }

    const resolved = deps && deps.resolveThread
      ? deps.resolveThread(payload.source_message_id)
      : _p4FindUniqueThreadBySourceMessageId_(payload.source_message_id);
    if (!resolved.ok) {
      return _driveStagingGmailLabelMoveResponse_(
        payload, false, false, resolved.matched_thread_count || 0, false, false, false,
        false, false, false, false, '', gate.existing_row, gate.state,
        'Thread Gmail pilota non trovato o ambiguo.', resolved.errors
      );
    }

    const thread = resolved.thread;
    const beforeTrigger = _p4ThreadHasLabel_(thread, labels.trigger_name);
    const beforeDone = _p4ThreadHasLabel_(thread, labels.done_name);
    const unreadBefore = _p4CaptureUnreadState_(thread);

    if (!beforeTrigger && beforeDone) {
      return _driveStagingGmailLabelMoveResponse_(
        payload, true, true, resolved.matched_thread_count, false, true, true,
        true, beforeTrigger, beforeDone, true, resolved.thread_id, gate.existing_row,
        gate.state, 'Thread gia traghettato; nessuna nuova modifica Gmail.', []
      );
    }

    if (!beforeTrigger && !beforeDone) {
      return _driveStagingGmailLabelMoveResponse_(
        payload, false, true, resolved.matched_thread_count, false, false, false,
        false, beforeTrigger, beforeDone, false, resolved.thread_id, gate.existing_row,
        gate.state, 'Thread Gmail non in stato compatibile con P4.', [
          _driveStagingError_(
            'THREAD_NOT_IN_EXPECTED_LABEL_STATE',
            `Il thread deve avere ${labels.trigger_name} oppure risultare gia ${labels.done_name}.`
          )
        ]
      );
    }

    labels.trigger.removeFromThread(thread);
    if (!beforeDone) labels.done.addToThread(thread);

    const afterTrigger = _p4ThreadHasLabel_(thread, labels.trigger_name);
    const afterDone = _p4ThreadHasLabel_(thread, labels.done_name);
    const unreadAfter = _p4CaptureUnreadState_(thread);
    const seenPreserved = _p4UnreadStateEquals_(unreadBefore, unreadAfter);

    if (afterTrigger || !afterDone) {
      return _driveStagingGmailLabelMoveResponse_(
        payload, false, true, resolved.matched_thread_count, false, false, false,
        seenPreserved, beforeTrigger, beforeDone, afterDone, resolved.thread_id,
        gate.existing_row, gate.state, 'Transizione Gmail non completata.', [
          _driveStagingError_(
            'GMAIL_LABEL_TRANSITION_FAILED',
            `Il thread deve terminare senza ${labels.trigger_name} e con ${labels.done_name}.`
          )
        ]
      );
    }

    return _driveStagingGmailLabelMoveResponse_(
      payload, true, true, resolved.matched_thread_count, true, false, true,
      seenPreserved, beforeTrigger, beforeDone, afterDone, resolved.thread_id,
      gate.existing_row, gate.state, 'Thread Gmail spostato in traghettate.', []
    );
  } catch (err) {
    return _driveStagingGmailLabelMoveResponse_(
      payload, false, false, 0, false, false, false,
      false, false, false, false, '', 0, '',
      'Transizione Gmail P4 non completata.', [
        _driveStagingError_(
          'P4_GMAIL_MOVE_FAILED',
          'Lookup Gmail o cambio etichette non riusciti.'
        )
      ]
    );
  }
}

function _driveStagingGmailLabelMoveValidatePayload_(payload) {
  const errors = [];
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    errors.push(_driveStagingError_('INVALID_PAYLOAD', 'Payload non valido.'));
  } else {
    if (payload.action !== DRIVE_STAGING_GMAIL_LABEL_MOVE_ACTION) {
      errors.push(_driveStagingError_('INVALID_ACTION', 'action non supportata.'));
    }
    if (payload.test_mode !== false) {
      errors.push(_driveStagingError_('TEST_MODE_MUST_BE_FALSE', 'test_mode deve essere false.'));
    }
    const required = ['connector_type', 'account_alias', 'source_message_id',
      'source_message_uid', 'attachment_id', 'original_filename', 'staged_filename',
      'sha256', 'mime_type', 'scan_engine', 'scan_result', 'quarantine_status'];
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
    response: errors.length === 0 ? null : _driveStagingGmailLabelMoveResponse_(
      payload || {}, false, false, 0, false, false, false,
      false, false, false, false, '', 0, '',
      'Richiesta P4 Gmail rifiutata.', errors
    )
  };
}

function _p4ValidateBucolicheGate_(sheet, payload) {
  const existingRow = _trovaRigaBucolichePerAttachmentId_(sheet, payload.attachment_id);
  if (existingRow === 0) {
    return {
      ok: false,
      existing_row: 0,
      state: '',
      errors: [_driveStagingError_(
        'BUCOLICHE_ROW_NOT_FOUND',
        'Eseguire prima P1, P2 e P3 per l attachment richiesto.'
      )]
    };
  }

  const existingSha256 = _leggiSha256BucolicheRiga_(sheet, existingRow);
  if (existingSha256 !== payload.sha256) {
    return {
      ok: false,
      existing_row: existingRow,
      state: '',
      errors: [_driveStagingError_(
        'ATTACHMENT_SHA256_CONFLICT',
        'Lo stesso attachment_id risulta associato a un SHA-256 diverso.'
      )]
    };
  }

  const note = String(sheet.getRange(existingRow, BUCOLICHE_COLS.note).getValue() || '');
  const state = String(sheet.getRange(existingRow, BUCOLICHE_COLS.stato).getValue() || '').trim();
  const p1Count = _p3p4CountMarker_(note, BUCOLICHE_ATTACHMENT_NOTE_PREFIX, payload.attachment_id);
  const p2Count = _p3p4CountMarker_(note, DRIVE_STAGING_NOTIFY_NOTE_PREFIX, payload.attachment_id);
  const p3Marker = _p3LeggiMarkerSpostamento_(sheet, existingRow, payload.attachment_id);
  const errors = [];

  if (state !== BUCOLICHE_PRACTICE_STATE) {
    errors.push(_driveStagingError_(
      'INVALID_BUCOLICHE_STATE',
      `La riga Bucoliche deve essere ${BUCOLICHE_PRACTICE_STATE} prima di P4.`
    ));
  }
  if (p1Count !== 1) {
    errors.push(_driveStagingError_(
      'P1_MARKER_COUNT_INVALID',
      'La nota Bucoliche deve contenere un solo marker P1.'
    ));
  }
  if (p2Count !== 1) {
    errors.push(_driveStagingError_(
      'P2_MARKER_COUNT_INVALID',
      'La nota Bucoliche deve contenere un solo marker P2.'
    ));
  }
  if (!p3Marker.present) {
    errors.push(_driveStagingError_(
      'P3_MARKER_MISSING',
      'La nota Bucoliche deve contenere il marker P3 prima di P4.'
    ));
  }
  if (!_p3p4NoteHasSha_(note, payload.sha256)) {
    errors.push(_driveStagingError_(
      'BUCOLICHE_SHA_MISMATCH',
      'La nota Bucoliche non conferma lo SHA-256 atteso.'
    ));
  }

  return {
    ok: errors.length === 0,
    existing_row: existingRow,
    state: state,
    errors: errors
  };
}

function _p4ResolveRequiredLabels_() {
  try {
    const trigger = GmailApp.getUserLabelByName(CONFIG.ETICHETTA_TRIGGER);
    const done = GmailApp.getUserLabelByName(CONFIG.ETICHETTA_ELABORATA);
    const errors = [];
    if (!trigger) {
      errors.push(_driveStagingError_(
        'TRIGGER_LABEL_MISSING',
        `La label Gmail ${CONFIG.ETICHETTA_TRIGGER} manca prima di P4.`
      ));
    }
    if (!done) {
      errors.push(_driveStagingError_(
        'DONE_LABEL_MISSING',
        `La label Gmail ${CONFIG.ETICHETTA_ELABORATA} manca prima di P4.`
      ));
    }
    return {
      ok: errors.length === 0,
      trigger: trigger,
      done: done,
      trigger_name: CONFIG.ETICHETTA_TRIGGER,
      done_name: CONFIG.ETICHETTA_ELABORATA,
      errors: errors
    };
  } catch (err) {
    return {
      ok: false,
      trigger: null,
      done: null,
      trigger_name: CONFIG.ETICHETTA_TRIGGER,
      done_name: CONFIG.ETICHETTA_ELABORATA,
      errors: [_driveStagingError_(
        'GMAIL_LABEL_LOOKUP_FAILED',
        'Impossibile leggere le label Gmail del pilota.'
      )]
    };
  }
}

function _p4FindUniqueThreadBySourceMessageId_(sourceMessageId) {
  const raw = String(sourceMessageId || '').trim();
  const bare = raw.replace(/^<+|>+$/g, '');
  const queries = [];
  [bare, raw].forEach(value => {
    if (!value) return;
    queries.push(`in:anywhere rfc822msgid:${value}`);
    queries.push(`in:anywhere rfc822msgid:"${value}"`);
    queries.push(`in:anywhere label:"${CONFIG.ETICHETTA_TRIGGER}" rfc822msgid:${value}`);
    queries.push(`in:anywhere label:"${CONFIG.ETICHETTA_TRIGGER}" rfc822msgid:"${value}"`);
    queries.push(`in:anywhere label:"${CONFIG.ETICHETTA_ELABORATA}" rfc822msgid:${value}`);
    queries.push(`in:anywhere label:"${CONFIG.ETICHETTA_ELABORATA}" rfc822msgid:"${value}"`);
  });

  const seen = {};
  const threads = [];
  queries.forEach(query => {
    const matches = GmailApp.search(query, 0, 5);
    matches.forEach(thread => {
      const id = String(thread.getId());
      if (!seen[id]) {
        seen[id] = true;
        threads.push(thread);
      }
    });
  });

  if (threads.length !== 1) {
    return {
      ok: false,
      matched_thread_count: threads.length,
      thread: null,
      thread_id: '',
      errors: [threads.length === 0
        ? _driveStagingError_(
          'SOURCE_THREAD_NOT_FOUND',
          'Nessun thread Gmail corrisponde al source_message_id del manifest.'
        )
        : _driveStagingError_(
          'SOURCE_THREAD_NOT_UNIQUE',
          'Il source_message_id del manifest corrisponde a piu thread Gmail.'
        )]
    };
  }

  return {
    ok: true,
    matched_thread_count: 1,
    thread: threads[0],
    thread_id: String(threads[0].getId()),
    errors: []
  };
}

function _p4ThreadHasLabel_(thread, labelName) {
  return thread.getLabels().some(label => String(label.getName()) === labelName);
}

function _p4CaptureUnreadState_(thread) {
  return thread.getMessages().map(message => message.isUnread() === true);
}

function _p4UnreadStateEquals_(before, after) {
  return JSON.stringify(before || []) === JSON.stringify(after || []);
}

function _driveStagingGmailLabelMoveResponse_(payload, ok, threadFound, matchedThreadCount,
                                              labelMoveCompleted, idempotent,
                                              readyForP5, seenStatePreserved,
                                              triggerLabelPresentBefore,
                                              doneLabelPresentBefore,
                                              doneLabelPresentAfter, threadId,
                                              existingRow, state, message, errors) {
  return {
    ok: ok,
    action: DRIVE_STAGING_GMAIL_LABEL_MOVE_ACTION,
    test_mode: false,
    attachment_id: payload.attachment_id || '',
    staged_filename: payload.staged_filename || '',
    source_message_id: payload.source_message_id || '',
    thread_found: threadFound === true,
    matched_thread_count: Number.isInteger(matchedThreadCount) ? matchedThreadCount : 0,
    label_move_completed: labelMoveCompleted === true,
    idempotent: idempotent === true,
    already_traghettata: idempotent === true,
    ready_for_p5: readyForP5 === true,
    seen_state_preserved: seenStatePreserved === true,
    trigger_label_present_before: triggerLabelPresentBefore === true,
    done_label_present_before: doneLabelPresentBefore === true,
    done_label_present_after: doneLabelPresentAfter === true,
    thread_id: threadId || '',
    existing_row: Number.isInteger(existingRow) ? existingRow : 0,
    state: state || '',
    message: message,
    errors: errors
  };
}

/** Pure tests: no live Gmail, Drive, Bucoliche or notifications. */
function testDriveStagingPilotMailboxMove() {
  const payload = Object.assign(_driveStagingTestPayload_(), {
    action: DRIVE_STAGING_GMAIL_LABEL_MOVE_ACTION,
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

  _driveStagingAssert_(_driveStagingGmailLabelMoveValidatePayload_(payload).ok, 'payload P4 valido');
  _driveStagingAssert_(!_driveStagingGmailLabelMoveValidatePayload_(
    Object.assign({}, payload, { test_mode: true })).ok, 'test_mode true vietato P4');

  const rows = [];
  const fakeSheet = _bucolicheNotifyFakeSheet_(rows);
  const checked = _intakeTestInspectFolder_(payload, _intakeTestFakeFolder_(payload, true, true, false));
  _registraBucolicheStagingIdempotente_(fakeSheet, payload, checked);
  _appendiNotaNotificaBucoliche_(fakeSheet, 2, payload, ['chat', 'telegram']);
  _aggiornaRigaBucolichePerP3_(fakeSheet, 2, _p3FakeDriveFile_('file-1', 'document.pdf'),
    payload, _p3FakeTarget_());

  const thread = _p4FakeThread_(['da-traghettare']);
  const labels = _p4FakeLabels_();
  const resolver = () => ({ ok: true, matched_thread_count: 1, thread: thread, thread_id: 'thread-1', errors: [] });

  const first = caronteCompletaMailboxPilotaP4(payload, {
    sheet: fakeSheet,
    labels: labels,
    resolveThread: resolver
  });
  _driveStagingAssert_(first.ok && first.label_move_completed && first.ready_for_p5,
    'prima transizione P4');
  _driveStagingAssert_(first.seen_state_preserved, 'seen preservato');
  _driveStagingAssert_(first.trigger_label_present_before && !first.done_label_present_before &&
    first.done_label_present_after, 'transizione label coerente');
  _driveStagingAssert_(_p4ThreadHasLabel_(thread, 'traghettate') && !_p4ThreadHasLabel_(thread, 'da-traghettare'),
    'thread etichettato correttamente');

  const retry = caronteCompletaMailboxPilotaP4(payload, {
    sheet: fakeSheet,
    labels: labels,
    resolveThread: resolver
  });
  _driveStagingAssert_(retry.ok && retry.idempotent && retry.already_traghettata &&
    !retry.label_move_completed, 'retry idempotente P4');

  const conflict = caronteCompletaMailboxPilotaP4(Object.assign({}, payload, { sha256: 'b'.repeat(64) }), {
    sheet: fakeSheet,
    labels: labels,
    resolveThread: resolver
  });
  _driveStagingAssert_(!conflict.ok && conflict.errors[0].code === 'ATTACHMENT_SHA256_CONFLICT',
    'conflitto sha256 P4');

  const noLabelThread = _p4FakeThread_([]);
  const invalidState = caronteCompletaMailboxPilotaP4(payload, {
    sheet: fakeSheet,
    labels: labels,
    resolveThread: () => ({ ok: true, matched_thread_count: 1, thread: noLabelThread, thread_id: 'thread-2', errors: [] })
  });
  _driveStagingAssert_(!invalidState.ok &&
    invalidState.errors[0].code === 'THREAD_NOT_IN_EXPECTED_LABEL_STATE',
    'stato label non valido');

  Logger.log('testDriveStagingPilotMailboxMove: OK');
}

function _p4FakeLabels_() {
  return {
    ok: true,
    trigger: {
      getName: () => 'da-traghettare',
      removeFromThread: thread => delete thread._labels['da-traghettare']
    },
    done: {
      getName: () => 'traghettate',
      addToThread: thread => thread._labels['traghettate'] = true
    },
    trigger_name: 'da-traghettare',
    done_name: 'traghettate',
    errors: []
  };
}

function _p4FakeThread_(labelNames) {
  const state = {};
  (labelNames || []).forEach(name => state[name] = true);
  return {
    _labels: state,
    getId: () => 'thread-1',
    getLabels: () => Object.keys(state).map(name => ({ getName: () => name })),
    getMessages: () => [{ isUnread: () => true }, { isUnread: () => false }]
  };
}
