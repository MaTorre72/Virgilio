/** Schema e setup esplicito del tab operativo Virgilio_Inbox. */

const VIRGILIO_INBOX_SPREADSHEET_PROPERTY = 'VIRGILIO_INBOX_SPREADSHEET_ID';
const VIRGILIO_INBOX_SHEET_PROPERTY = 'VIRGILIO_INBOX_SHEET_NAME';
const VIRGILIO_INBOX_DEFAULT_SHEET = 'Virgilio_Inbox';
const VIRGILIO_INBOX_COLUMN_WIDTHS = [
  170, 170, 120, 220, 150, 220, 220, 130, 150, 170, 170,
  220, 220, 170, 170, 240, 220, 180, 180, 180, 240, 280
];

function caronteGetVirgilioInboxSchema() {
  return {
    spreadsheet_property: VIRGILIO_INBOX_SPREADSHEET_PROPERTY,
    sheet_property: VIRGILIO_INBOX_SHEET_PROPERTY,
    default_sheet_name: VIRGILIO_INBOX_DEFAULT_SHEET,
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

function _virgilioInboxResolveSpreadsheetId_(spreadsheetId) {
  const props = PropertiesService.getScriptProperties();
  const configSpreadsheetId = typeof CONFIG !== 'undefined' && CONFIG
    ? _virgilioInboxStringOrEmpty_(CONFIG.BUCOLICHE_ID)
    : '';
  const value = _virgilioInboxStringOrEmpty_(spreadsheetId) ||
    _virgilioInboxStringOrEmpty_(props.getProperty(VIRGILIO_INBOX_SPREADSHEET_PROPERTY)) ||
    configSpreadsheetId;
  if (!value) throw new Error('ID spreadsheet Virgilio_Inbox obbligatorio.');
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
  Logger.log('testVirgilioInboxSchema: OK');
}

function _virgilioInboxFakeSheet_(lastRow, rows) {
  return {
    rows: rows,
    appendRow: row => rows.push(row),
    getLastRow: () => lastRow === 0 ? rows.length : Math.max(lastRow, rows.length),
    getRange: (row, column) => ({
      getValues: () => [rows[row - 1] || []],
      setValues: values => {
        rows[row - 1] = values[0].slice();
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
