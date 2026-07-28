/**
 * Verifica read-only della visibilita' cloud dello staging Drive Desktop.
 * Legge metadati Drive e il solo manifest JSON; non modifica alcun servizio.
 */

const DRIVE_STAGING_VERIFY_ACTION = 'verify_drive_staging';
const DRIVE_STAGING_FOLDER_PROPERTY = 'VIRGILIO_LIMBO_ID';

/**
 * Configurazione manuale una tantum dell'ID della cartella Limbo configurata.
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

  const resolvedFolder = _driveStagingResolveFolder_();
  if (!resolvedFolder.ok) {
    return _driveStagingResponse_(payload, false, false, false, false, null,
      resolvedFolder.message, resolvedFolder.errors);
  }
  return _driveStagingVerifyInFolder_(payload, resolvedFolder.folder);
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

function _driveStagingVerifyInboxVisibility_(payload) {
  const resolvedFolder = _driveStagingResolveFolder_();
  if (!resolvedFolder.ok) {
    return {
      ok: false,
      drive_file_id: '',
      manifest_file_id: '',
      errors: resolvedFolder.errors.slice(),
    };
  }
  return _driveStagingVerifyInboxVisibilityInFolder_(payload, resolvedFolder.folder);
}

function _driveStagingVerifyInboxVisibilityInFolder_(payload, folder) {
  const manifest = payload && payload.manifest && typeof payload.manifest === 'object' &&
    !Array.isArray(payload.manifest)
    ? payload.manifest
    : null;
  if (!manifest) {
    return {
      ok: false,
      drive_file_id: '',
      manifest_file_id: '',
      errors: [_driveStagingError_('INVALID_MANIFEST', 'manifest obbligatorio per verificare Drive.')],
    };
  }

  const verifyPayload = _driveStagingBuildVerifyPayloadFromManifest_(manifest);
  if (!verifyPayload.ok) {
    return {
      ok: false,
      drive_file_id: '',
      manifest_file_id: '',
      errors: verifyPayload.errors,
    };
  }

  const verification = _driveStagingVerifyInFolder_(verifyPayload.payload, folder);
  const preview = verification.inbox_preview || {};
  const actualDriveFileId = _caronteStringOrEmpty_(preview.drive_file_id);
  const actualManifestFileId = _caronteStringOrEmpty_(preview.manifest_file_id);
  const expectedDriveFileId = _caronteStringOrEmpty_(payload.drive_file_id);
  const expectedManifestFileId = _caronteStringOrEmpty_(payload.manifest_file_id);
  const errors = (verification.errors || []).slice();

  if (!verification.cloud_visible) {
    return {
      ok: false,
      drive_file_id: actualDriveFileId,
      manifest_file_id: actualManifestFileId,
      errors: errors,
    };
  }
  if (expectedDriveFileId !== actualDriveFileId) {
    errors.push(_driveStagingError_(
      'DRIVE_FILE_ID_MISMATCH',
      'drive_file_id non corrisponde al file staged visibile su Drive.'
    ));
  }
  if (expectedManifestFileId !== actualManifestFileId) {
    errors.push(_driveStagingError_(
      'MANIFEST_FILE_ID_MISMATCH',
      'manifest_file_id non corrisponde al manifest visibile su Drive.'
    ));
  }
  return {
    ok: errors.length === 0,
    drive_file_id: actualDriveFileId,
    manifest_file_id: actualManifestFileId,
    errors: errors,
  };
}

function _driveStagingBuildVerifyPayloadFromManifest_(manifest) {
  const attachmentId = _caronteStringOrEmpty_(manifest.attachment_id);
  const stagedFilename = _caronteStringOrEmpty_(manifest.staged_filename);
  const sha256 = _caronteStringOrEmpty_(manifest.sha256);
  const sizeBytes = manifest && Number.isInteger(manifest.size_bytes) ? manifest.size_bytes : null;
  const errors = [];

  if (!attachmentId) {
    errors.push(_driveStagingError_(
      'MISSING_ATTACHMENT_ID',
      'attachment_id mancante nel manifest per la verifica Drive.'
    ));
  }
  if (!stagedFilename) {
    errors.push(_driveStagingError_(
      'MISSING_STAGED_FILENAME',
      'staged_filename mancante nel manifest per la verifica Drive.'
    ));
  }
  if (!/^[0-9a-f]{64}$/.test(sha256)) {
    errors.push(_driveStagingError_(
      'INVALID_SHA256',
      'sha256 del manifest non valido per la verifica Drive.'
    ));
  }
  if (!Number.isInteger(sizeBytes) || sizeBytes < 0) {
    errors.push(_driveStagingError_(
      'INVALID_SIZE_BYTES',
      'size_bytes del manifest non valido per la verifica Drive.'
    ));
  }

  return {
    ok: errors.length === 0,
    payload: errors.length === 0 ? {
      action: DRIVE_STAGING_VERIFY_ACTION,
      dry_run: true,
      attachment_id: attachmentId,
      staged_filename: stagedFilename,
      sha256: sha256,
      size_bytes: sizeBytes,
    } : null,
    errors: errors,
  };
}

function _driveStagingResolveFolder_() {
  const folderId = PropertiesService.getScriptProperties()
    .getProperty(DRIVE_STAGING_FOLDER_PROPERTY);
  if (!folderId) {
    return {
      ok: false,
      folder: null,
      message: 'Cartella staging Drive di test non configurata.',
      errors: [
        _driveStagingError_(
          'STAGING_FOLDER_NOT_CONFIGURED',
          'Configurare VIRGILIO_LIMBO_ID nelle Script Properties.'
        )
      ],
    };
  }
  try {
    return {
      ok: true,
      folder: DriveApp.getFolderById(folderId),
      message: '',
      errors: [],
    };
  } catch (err) {
    return {
      ok: false,
      folder: null,
      message: 'Verifica Drive non completata.',
      errors: [
        _driveStagingError_('DRIVE_READ_FAILED', 'Cartella staging non leggibile.')
      ],
    };
  }
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

  const inboxPayload = {
    action: 'intake_virgilio_inbox',
    manifest: _caronteInboxManifestSample_(),
    drive_file_id: 'fake-file-id',
    manifest_file_id: 'fake-file-id',
  };
  _driveStagingAssert_(_driveStagingVerifyInboxVisibilityInFolder_(inboxPayload, validFolder).ok,
    'visibilita inbox verificata');
  const wrongDriveFileId = Object.assign({}, inboxPayload, { drive_file_id: 'other-file-id' });
  _driveStagingAssert_(
    !_driveStagingVerifyInboxVisibilityInFolder_(wrongDriveFileId, validFolder).ok,
    'drive_file_id incoerente'
  );
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
