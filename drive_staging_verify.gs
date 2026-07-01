/**
 * Verifica read-only della visibilita' cloud dello staging Drive Desktop.
 * Legge metadati Drive e il solo manifest JSON; non modifica alcun servizio.
 */

const DRIVE_STAGING_VERIFY_ACTION = 'verify_drive_staging';
const DRIVE_STAGING_FOLDER_PROPERTY = 'VIRGILIO_DRIVE_STAGING_FOLDER_ID';

/**
 * Configurazione manuale una tantum dell'ID della cartella Limbo_Test_Local.
 * La funzione non crea cartelle e non verifica/sincronizza file.
 */
function caronteConfiguraCartellaStagingDriveTest(folderId) {
  if (typeof folderId !== 'string' || !folderId.trim()) {
    throw new Error('ID cartella staging Drive di test obbligatorio.');
  }
  PropertiesService.getScriptProperties().setProperty(
    DRIVE_STAGING_FOLDER_PROPERTY,
    folderId.trim()
  );
}

/**
 * Endpoint applicativo read-only.
 *
 * @param {Object} payload Richiesta metadata-only.
 * @returns {Object} Esito standard della verifica cloud.
 */
function caronteVerificaStagingDriveDryRun(payload) {
  const validation = _driveStagingValidatePayload_(payload);
  if (!validation.ok) return validation.response;

  const folderId = PropertiesService.getScriptProperties()
    .getProperty(DRIVE_STAGING_FOLDER_PROPERTY);
  if (!folderId) {
    return _driveStagingResponse_(payload, false, false, false, false, null,
      'Cartella staging Drive di test non configurata.', [
        _driveStagingError_('STAGING_FOLDER_NOT_CONFIGURED',
          'Configurare VIRGILIO_DRIVE_STAGING_FOLDER_ID nelle Script Properties.')
      ]);
  }

  try {
    const folder = DriveApp.getFolderById(folderId);
    return _driveStagingVerifyInFolder_(payload, folder);
  } catch (err) {
    return _driveStagingResponse_(payload, false, false, false, false, null,
      'Verifica Drive non completata.', [
        _driveStagingError_('DRIVE_READ_FAILED', 'Cartella staging non leggibile.')
      ]);
  }
}

function _driveStagingValidatePayload_(payload) {
  const errors = [];
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    errors.push(_driveStagingError_('INVALID_PAYLOAD', 'Payload non valido.'));
  } else {
    if (payload.action !== DRIVE_STAGING_VERIFY_ACTION) {
      errors.push(_driveStagingError_('INVALID_ACTION', 'action non supportata.'));
    }
    if (payload.dry_run !== true) {
      errors.push(_driveStagingError_('DRY_RUN_REQUIRED', 'dry_run deve essere true.'));
    }
    if (typeof payload.attachment_id !== 'string' ||
        !/^att-[A-Za-z0-9._-]+$/.test(payload.attachment_id)) {
      errors.push(_driveStagingError_('INVALID_ATTACHMENT_ID', 'attachment_id non valido.'));
    }
    if (typeof payload.staged_filename !== 'string' ||
        !payload.staged_filename.trim() || /[\\/]/.test(payload.staged_filename)) {
      errors.push(_driveStagingError_('INVALID_STAGED_FILENAME', 'staged_filename non valido.'));
    }
    if (typeof payload.sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(payload.sha256)) {
      errors.push(_driveStagingError_('INVALID_SHA256', 'sha256 non valido.'));
    }
    if (!Number.isInteger(payload.size_bytes) || payload.size_bytes < 0) {
      errors.push(_driveStagingError_('INVALID_SIZE', 'size_bytes non valido.'));
    }
  }
  return {
    ok: errors.length === 0,
    response: errors.length === 0 ? null : _driveStagingResponse_(
      payload || {}, false, false, false, false, null,
      'Richiesta verifica staging rifiutata.', errors)
  };
}

function _driveStagingVerifyInFolder_(payload, folder) {
  const staged = _driveStagingFindUnique_(folder, payload.staged_filename);
  const manifestName = `${payload.staged_filename}.manifest.json`;
  const manifestFile = _driveStagingFindUnique_(folder, manifestName);
  const errors = [];

  if (!staged.file) {
    errors.push(_driveStagingError_(
      staged.duplicate ? 'STAGED_FILE_DUPLICATE' : 'STAGED_FILE_NOT_FOUND',
      staged.duplicate ? 'Piu file staged con lo stesso nome.' : 'File staged non trovato.'
    ));
  }
  if (!manifestFile.file) {
    errors.push(_driveStagingError_(
      manifestFile.duplicate ? 'MANIFEST_DUPLICATE' : 'MANIFEST_NOT_FOUND',
      manifestFile.duplicate ? 'Piu manifest con lo stesso nome.' : 'Manifest non trovato.'
    ));
  }

  let manifestConsistent = false;
  let inboxPreview = null;
  if (manifestFile.file) {
    try {
      const manifest = JSON.parse(manifestFile.file.getBlob().getDataAsString('UTF-8'));
      manifestConsistent =
        manifest.attachment_id === payload.attachment_id &&
        manifest.staged_filename === payload.staged_filename &&
        manifest.sha256 === payload.sha256 &&
        manifest.size_bytes === payload.size_bytes;
      if (manifestConsistent) {
        inboxPreview = caronteBuildVirgilioInboxDraftFromManifest(manifest, {
          drive_file_id: staged.file ? _driveStagingGetFileIdSafe_(staged.file) : '',
          manifest_file_id: _driveStagingGetFileIdSafe_(manifestFile.file),
        });
      }
      if (!manifestConsistent) {
        errors.push(_driveStagingError_(
          'MANIFEST_MISMATCH', 'Manifest non coerente con i metadati richiesti.'
        ));
      }
    } catch (err) {
      errors.push(_driveStagingError_('MANIFEST_INVALID', 'Manifest JSON non valido.'));
    }
  }

  if (staged.file && staged.file.getSize() !== payload.size_bytes) {
    errors.push(_driveStagingError_(
      'STAGED_SIZE_MISMATCH', 'Dimensione Drive non coerente con il payload.'
    ));
  }

  const ok = errors.length === 0;
  return _driveStagingResponse_(
    payload, ok, Boolean(staged.file), Boolean(manifestFile.file), manifestConsistent, inboxPreview,
    ok
      ? 'File e manifest visibili su Drive; nessuna presa in carico eseguita.'
      : 'Verifica cloud staging non superata.',
    errors
  );
}

function _driveStagingFindUnique_(folder, name) {
  const iterator = folder.getFilesByName(name);
  if (!iterator.hasNext()) return { file: null, duplicate: false };
  const file = iterator.next();
  if (iterator.hasNext()) return { file: null, duplicate: true };
  return { file: file, duplicate: false };
}

function _driveStagingResponse_(payload, ok, fileFound, manifestFound,
                                manifestConsistent, inboxPreview, message, errors) {
  return {
    ok: ok,
    dry_run: true,
    action: DRIVE_STAGING_VERIFY_ACTION,
    attachment_id: payload.attachment_id || '',
    staged_filename: payload.staged_filename || '',
    file_found: fileFound,
    manifest_found: manifestFound,
    manifest_consistent: manifestConsistent,
    inbox_preview: inboxPreview,
    cloud_visible: ok && fileFound && manifestFound && manifestConsistent,
    message: message,
    errors: errors
  };
}

function _driveStagingGetFileIdSafe_(file) {
  return file && typeof file.getId === 'function' ? _caronteStringOrEmpty_(file.getId()) : '';
}

function _driveStagingError_(code, message) {
  return { code: code, message: message };
}

/** Test puri con folder/file in memoria; nessun accesso Drive reale. */
function testDriveStagingCloudVerify() {
  const payload = _driveStagingTestPayload_();
  const validFolder = _driveStagingFakeFolder_(payload, true, true);
  _driveStagingAssert_(_driveStagingVerifyInFolder_(payload, validFolder).ok,
    'file e manifest presenti');
  _driveStagingAssert_(_driveStagingVerifyInFolder_(payload, validFolder).inbox_preview.attachment_id ===
    payload.attachment_id, 'preview inbox coerente');

  _driveStagingAssert_(!_driveStagingVerifyInFolder_(
    payload, _driveStagingFakeFolder_(payload, false, true)).ok, 'file mancante');
  _driveStagingAssert_(!_driveStagingVerifyInFolder_(
    payload, _driveStagingFakeFolder_(payload, true, false)).ok, 'manifest mancante');

  const operational = Object.assign({}, payload, { dry_run: false });
  _driveStagingAssert_(!_driveStagingValidatePayload_(operational).ok, 'dry_run=false');
  const wrongAction = Object.assign({}, payload, { action: 'other' });
  _driveStagingAssert_(!_driveStagingValidatePayload_(wrongAction).ok, 'action errata');
  const wrongId = Object.assign({}, payload, { attachment_id: 'att-other' });
  _driveStagingAssert_(!_driveStagingVerifyInFolder_(wrongId, validFolder).ok,
    'attachment_id non coerente');
  const wrongName = Object.assign({}, payload, { staged_filename: 'other.pdf' });
  _driveStagingAssert_(!_driveStagingVerifyInFolder_(wrongName, validFolder).ok,
    'staged_filename non coerente');
  Logger.log('testDriveStagingCloudVerify: OK');
}

function _driveStagingTestPayload_() {
  return {
    action: DRIVE_STAGING_VERIFY_ACTION,
    dry_run: true,
    attachment_id: 'att-test-1',
    staged_filename: 'att-test-1-document.pdf',
    sha256: 'a'.repeat(64),
    size_bytes: 4
  };
}

function _driveStagingFakeFolder_(payload, includeFile, includeManifest) {
  const manifest = JSON.stringify({
    attachment_id: payload.attachment_id,
    staged_filename: payload.staged_filename,
    sha256: payload.sha256,
    size_bytes: payload.size_bytes
  });
  const files = {};
  if (includeFile) files[payload.staged_filename] = [_driveStagingFakeFile_('', 4)];
  if (includeManifest) {
    files[`${payload.staged_filename}.manifest.json`] = [
      _driveStagingFakeFile_(manifest, manifest.length)
    ];
  }
  return {
    getFilesByName: name => {
      const values = (files[name] || []).slice();
      return { hasNext: () => values.length > 0, next: () => values.shift() };
    }
  };
}

function _driveStagingFakeFile_(content, size) {
  return {
    getId: () => 'fake-file-id',
    getSize: () => size,
    getBlob: () => ({ getDataAsString: () => content })
  };
}

function _driveStagingAssert_(condition, label) {
  if (!condition) throw new Error(`Test fallito: ${label}`);
}
