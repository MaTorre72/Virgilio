/** Coordinated, resumable reset of assets explicitly marked TEST. */

const TEST_ENVIRONMENT_RESET_ACTION = 'reset_test_environment';
const TEST_RESET_STATE_PREFIX = 'VIRGILIO_TEST_RESET_';

function caronteResetTestEnvironment(payload) {
  const validation = _testResetValidateRequest_(payload);
  if (!validation.ok) return validation.response;
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return _testResetResponse_(payload, false, 'blocked', false,
    {}, {}, [{ code: 'RESET_BUSY', message: 'Un altro reset TEST e in corso.' }]);
  try {
    return _testResetRun_(payload, _testResetGasAdapter_());
  } catch (err) {
    return _testResetResponse_(payload, false, 'blocked', false, {}, {}, [{
      code: 'RESET_FAILED', message: String(err && err.message || err)
    }]);
  } finally {
    lock.releaseLock();
  }
}

function _testResetRun_(payload, adapter) {
  const targets = adapter.inspect();
  _testResetAssertTargets_(targets);
  let state = adapter.loadState(payload.reset_id);
  if (payload.mode === 'preview') {
    state = state || { phase: 'preview', backups: {} };
    return _testResetResponse_(payload, true, state.phase, state.phase === 'completed', targets,
      state.backups, []);
  }
  if (!state) {
    state = { phase: 'preview', backups: {}, backup_stamp: adapter.backupStamp() };
    adapter.saveState(payload.reset_id, state);
  }
  if (!state.backups.registry_file_id) {
    state.backups.registry_file_id = adapter.backupRegistry(
      payload.reset_id, targets, state.backup_stamp);
    state.phase = 'registry_backed_up'; adapter.saveState(payload.reset_id, state);
  }
  if (!state.backups.limbo_folder_id) {
    state.backups.limbo_folder_id = adapter.backupLimbo(
      payload.reset_id, targets, state.backup_stamp);
    state.phase = 'prepared'; adapter.saveState(payload.reset_id, state);
  }
  if (payload.mode === 'prepare') {
    return _testResetResponse_(payload, true, 'prepared', false, targets, state.backups, []);
  }
  if (state.phase === 'prepared') {
    adapter.clearRegistry(targets); state.phase = 'registry_cleared';
    adapter.saveState(payload.reset_id, state);
  }
  if (state.phase === 'registry_cleared') {
    adapter.clearInbox(targets); state.phase = 'inbox_cleared';
    adapter.saveState(payload.reset_id, state);
  }
  if (state.phase === 'inbox_cleared') {
    adapter.clearLimbo(targets); state.phase = 'completed';
    adapter.saveState(payload.reset_id, state);
  }
  return _testResetResponse_(payload, true, state.phase, state.phase === 'completed',
    adapter.inspect(), state.backups, []);
}

function _testResetValidateRequest_(payload) {
  const ok = payload && typeof payload === 'object' && !Array.isArray(payload) &&
    payload.action === TEST_ENVIRONMENT_RESET_ACTION && payload.test_mode === true &&
    /^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$/.test(payload.reset_id || '') &&
    ['preview', 'prepare', 'execute'].indexOf(payload.mode) >= 0;
  return { ok: ok, response: ok ? null : _testResetResponse_(payload || {}, false,
    'blocked', false, {}, {}, [{ code: 'INVALID_TEST_RESET', message: 'Richiesta reset TEST non valida.' }]) };
}

function _testResetAssertTargets_(targets) {
  if (!targets || targets.environment !== 'TEST') throw new Error('Ambiente non marcato TEST.');
  const assets = [targets.registry, targets.inbox, targets.limbo];
  assets.forEach(asset => {
    if (!asset || !asset.id || !/TEST/i.test(asset.name || '')) {
      throw new Error('Ogni asset deve essere identificato e marcato TEST.');
    }
  });
  const expectedAnagrafiche = [
    ANAGRAFICA_TABS.CLIENTI_SITI,
    ANAGRAFICA_TABS.TEAM,
    ANAGRAFICA_TABS.TIPI_PRATICA,
  ];
  const actualAnagrafiche = (targets.registry.anagrafiche || []).map(item => item.sheet);
  if (expectedAnagrafiche.some(name => actualAnagrafiche.indexOf(name) < 0)) {
    throw new Error('Le tre anagrafiche canoniche devono esistere prima del reset TEST.');
  }
  if (targets.limbo.id === targets.registry.id || targets.limbo.id === targets.inbox.id) {
    throw new Error('Il Limbo TEST deve avere un identificativo distinto dagli spreadsheet TEST.');
  }
  if (targets.registry.id === targets.inbox.id) {
    const registrySheets = new Set((targets.registry.schema || []).map(item => item.sheet));
    if (!targets.inbox.sheet_name || registrySheets.has(targets.inbox.sheet_name)) {
      throw new Error('Registro e Da archiviare TEST condivisi devono usare tab distinti.');
    }
  }
}

function _testResetGasAdapter_() {
  const props = PropertiesService.getScriptProperties();
  return {
    inspect: () => _testResetInspectGas_(props),
    loadState: resetId => { const raw = props.getProperty(TEST_RESET_STATE_PREFIX + resetId);
      return raw ? JSON.parse(raw) : null; },
    saveState: (resetId, state) => props.setProperty(TEST_RESET_STATE_PREFIX + resetId,
      JSON.stringify(state)),
    backupStamp: () => Utilities.formatDate(new Date(), 'Europe/Rome', 'yyyyMMdd-HHmmss'),
    backupRegistry: (resetId, targets, stamp) => _testResetBackupFile_(
      targets.registry.id, resetId, stamp),
    backupLimbo: (resetId, targets, stamp) => _testResetBackupFolder_(
      targets.limbo.id, resetId, stamp),
    clearRegistry: targets => _testResetClearSheets_(targets.registry.id,
      [CONFIG.BUCOLICHE_TAB]),
    clearInbox: targets => _testResetClearSheets_(targets.inbox.id, [targets.inbox.sheet_name]),
    clearLimbo: targets => _testResetClearFolder_(targets.limbo.id)
  };
}

function _testResetInspectGas_(props) {
  const registryId = props.getProperty('VIRGILIO_BUCOLICHE_SPREADSHEET_ID') || '';
  const inboxId = props.getProperty(VIRGILIO_INBOX_SPREADSHEET_PROPERTY) || '';
  const sheetName = props.getProperty(VIRGILIO_INBOX_SHEET_PROPERTY) || '';
  const limboId = props.getProperty('VIRGILIO_LIMBO_ID') || '';
  const registry = SpreadsheetApp.openById(registryId);
  const inbox = SpreadsheetApp.openById(inboxId);
  const limbo = DriveApp.getFolderById(limboId);
  const registrySheets = [CONFIG.BUCOLICHE_TAB];
  return {
    environment: props.getProperty('VIRGILIO_ENVIRONMENT') || '',
    registry: { id: registryId, name: registry.getName(),
      rows: _testResetRows_(registry, registrySheets),
      schema: _testResetSchema_(registry, registrySheets),
      anagrafiche: _testResetAnagrafiche_(registry) },
    inbox: { id: inboxId, name: `${inbox.getName()} ${sheetName}`, sheet_name: sheetName,
      rows: _testResetRows_(inbox, [sheetName]), schema: _testResetSchema_(inbox, [sheetName]) },
    limbo: { id: limboId, name: limbo.getName(), files: _testResetFiles_(limbo) }
  };
}

function _testResetAnagrafiche_(spreadsheet) {
  const names = [
    ANAGRAFICA_TABS.CLIENTI_SITI,
    ANAGRAFICA_TABS.TEAM,
    ANAGRAFICA_TABS.TIPI_PRATICA,
  ];
  return names.map(name => {
    const sheet = spreadsheet.getSheetByName(name);
    if (!sheet) throw new Error(`Tab anagrafico canonico mancante: ${name}`);
    const columns = sheet.getLastColumn();
    return {
      sheet: name,
      header: columns ? sheet.getRange(1, 1, 1, columns).getValues()[0] : [],
      rows: Math.max(0, sheet.getLastRow() - 1),
    };
  });
}

function _testResetRows_(spreadsheet, names) {
  const rows = [];
  names.forEach(name => { const sheet = spreadsheet.getSheetByName(name);
    if (!sheet) throw new Error(`Tab TEST mancante: ${name}`);
    for (let row = 2; row <= sheet.getLastRow(); row++) rows.push({ sheet: name, row: row });
  });
  return rows;
}

function _testResetSchema_(spreadsheet, names) {
  return names.map(name => { const sheet = spreadsheet.getSheetByName(name);
    const columns = sheet.getLastColumn();
    return { sheet: name, header: columns ? sheet.getRange(1, 1, 1, columns).getValues()[0] : [] };
  });
}

function _testResetFiles_(folder) {
  const values = [];
  _testResetCollectFiles_(folder, '', values);
  return values.sort((a, b) => a.relative_name.localeCompare(b.relative_name));
}

function _testResetCollectFiles_(folder, prefix, values) {
  const files = folder.getFiles();
  while (files.hasNext()) {
    const file = files.next(); const name = file.getName();
    values.push({ id: file.getId(), name: name,
      relative_name: prefix ? `${prefix}/${name}` : name });
  }
  const folders = folder.getFolders();
  while (folders.hasNext()) {
    const child = folders.next();
    const childPrefix = prefix ? `${prefix}/${child.getName()}` : child.getName();
    _testResetCollectFiles_(child, childPrefix, values);
  }
}

function _testResetBackupFile_(fileId, resetId, stamp) {
  const file = DriveApp.getFileById(fileId); const parents = file.getParents();
  if (!parents.hasNext()) throw new Error('Registro TEST senza cartella padre.');
  const parent = parents.next(); const name = `${file.getName()}.backup-${stamp}-${resetId}`;
  const existing = parent.getFilesByName(name);
  return existing.hasNext() ? existing.next().getId() : file.makeCopy(name, parent).getId();
}

function _testResetBackupFolder_(folderId, resetId, stamp) {
  const source = DriveApp.getFolderById(folderId); const parents = source.getParents();
  if (!parents.hasNext()) throw new Error('Limbo TEST senza cartella padre.');
  const parent = parents.next(); const name = `${source.getName()}.backup-${stamp}-${resetId}`;
  const existing = parent.getFoldersByName(name); let target;
  if (existing.hasNext()) target = existing.next();
  else target = parent.createFolder(name);
  _testResetCopyFolderContents_(source, target);
  return target.getId();
}

function _testResetCopyFolderContents_(source, target) {
  const files = source.getFiles();
  while (files.hasNext()) { const file = files.next(); const copies = target.getFilesByName(file.getName());
    if (!copies.hasNext()) file.makeCopy(file.getName(), target); }
  const folders = source.getFolders();
  while (folders.hasNext()) {
    const sourceChild = folders.next(); const matches = target.getFoldersByName(sourceChild.getName());
    const targetChild = matches.hasNext() ? matches.next() : target.createFolder(sourceChild.getName());
    _testResetCopyFolderContents_(sourceChild, targetChild);
  }
}

function _testResetClearSheets_(spreadsheetId, names) {
  const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
  names.forEach(name => { const sheet = spreadsheet.getSheetByName(name);
    if (!sheet) throw new Error(`Tab TEST mancante: ${name}`);
    if (sheet.getLastRow() > 1 && sheet.getLastColumn() > 0) {
      sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).clearContent();
    }
  });
}

function _testResetClearFolder_(folderId) {
  _testResetClearFolderContents_(DriveApp.getFolderById(folderId));
}

function _testResetClearFolderContents_(folder) {
  const files = folder.getFiles();
  while (files.hasNext()) files.next().setTrashed(true);
  const folders = folder.getFolders();
  while (folders.hasNext()) {
    const child = folders.next();
    _testResetClearFolderContents_(child);
    child.setTrashed(true);
  }
}

function _testResetResponse_(payload, ok, phase, completed, targets, backups, errors) {
  return { ok: ok, test_mode: true, action: TEST_ENVIRONMENT_RESET_ACTION,
    mode: payload.mode || '', reset_id: payload.reset_id || '', phase: phase,
    completed: completed, targets: targets, backups: backups, errors: errors };
}

/** Pure harness: no Drive, Sheets, network or credentials. */
function testTestEnvironmentReset() {
  const target = { environment: 'TEST', registry: { id: 'r', name: 'Registro TEST', rows: [2], schema: ['h'],
    anagrafiche: [
      { sheet: 'Clienti_Siti', header: ['cliente'], rows: 1 },
      { sheet: 'Team', header: ['nome'], rows: 1 },
      { sheet: 'TipiPratica', header: ['codice'], rows: 1 }
    ] },
    inbox: { id: 'i', name: 'Da archiviare TEST', rows: [2], schema: ['h'] },
    limbo: { id: 'l', name: 'Limbo TEST', files: [{ id: 'f', name: 'doc.pdf' }] } };
  ['preview', 'registry_backed_up', 'prepared', 'registry_cleared', 'inbox_cleared', 'completed']
    .forEach(phase => {
      let state = phase === 'preview' ? null : { phase: phase, backup_stamp: '20260726-174500', backups: {
        registry_file_id: 'br', limbo_folder_id: phase === 'registry_backed_up' ? '' : 'bl' } };
      const adapter = { inspect: () => target, loadState: () => state,
        saveState: (id, value) => { state = JSON.parse(JSON.stringify(value)); },
        backupStamp: () => '20260726-174500',
        backupRegistry: () => 'br', backupLimbo: () => 'bl', clearRegistry: () => {},
        clearInbox: () => {}, clearLimbo: () => {} };
      const result = _testResetRun_({ action: TEST_ENVIRONMENT_RESET_ACTION, test_mode: true,
        reset_id: 'reset-12345678', mode: 'execute' }, adapter);
      if (!result.completed || result.phase !== 'completed') throw new Error(`Ripresa fallita da ${phase}`);
    });
  let current = JSON.parse(JSON.stringify(target)); const order = []; let saved = null;
  const adapter = { inspect: () => JSON.parse(JSON.stringify(current)), loadState: () => saved,
    saveState: (id, value) => { saved = JSON.parse(JSON.stringify(value)); },
    backupStamp: () => '20260726-174500',
    backupRegistry: () => { order.push('backup_registry'); return 'br'; },
    backupLimbo: () => { order.push('backup_limbo'); return 'bl'; },
    clearRegistry: () => { order.push('clear_registry'); current.registry.rows = []; },
    clearInbox: () => { order.push('clear_inbox'); current.inbox.rows = []; },
    clearLimbo: () => { order.push('clear_limbo'); current.limbo.files = []; } };
  const completed = _testResetRun_({ action: TEST_ENVIRONMENT_RESET_ACTION, test_mode: true,
    reset_id: 'reset-12345678', mode: 'execute' }, adapter);
  if (order.join(',') !== 'backup_registry,backup_limbo,clear_registry,clear_inbox,clear_limbo') {
    throw new Error('Ordine backup/reset non valido.');
  }
  if (completed.targets.registry.rows.length || completed.targets.inbox.rows.length ||
      completed.targets.limbo.files.length) throw new Error('Asset TEST non vuoti.');
  try {
    _testResetAssertTargets_(Object.assign({}, target, { environment: 'PROD' }));
    throw new Error('Ambiente PROD accettato.');
  } catch (err) { if (String(err.message).indexOf('non marcato TEST') < 0) throw err; }
  const sharedSpreadsheet = JSON.parse(JSON.stringify(target));
  sharedSpreadsheet.inbox.id = sharedSpreadsheet.registry.id;
  sharedSpreadsheet.inbox.sheet_name = 'Inbox TEST';
  _testResetAssertTargets_(sharedSpreadsheet);
  try {
    const duplicate = JSON.parse(JSON.stringify(target)); duplicate.limbo.id = duplicate.registry.id;
    _testResetAssertTargets_(duplicate); throw new Error('Limbo duplicato accettato.');
  } catch (err) { if (String(err.message).indexOf('distinto') < 0) throw err; }
}
