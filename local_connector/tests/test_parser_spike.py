from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile

from virgilio_connector.parser_spike import compare_parser_fixtures, extract_local_fixtures


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "parser_spike"


def _write_pdf(path: Path) -> None:
    content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R>>endobj
4 0 obj<</Length 86>>stream
BT
/F1 12 Tf
72 150 Td
(Invoice 2026 Total EUR) Tj
0 -16 Td
(Item Qty Price) Tj
ET
endstream
endobj
trailer<</Root 1 0 R>>
%%EOF
"""
    path.write_bytes(content)


def _write_docx(path: Path) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    document = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Meeting Minutes</w:t></w:r></w:p>
    <w:p><w:r><w:t>Decision Approved</w:t></w:r></w:p>
    <w:tbl>
      <w:tr><w:tc><w:p><w:r><w:t>Owner</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Task</w:t></w:r></w:p></w:tc></w:tr>
      <w:tr><w:tc><w:p><w:r><w:t>Tecnico 1</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Follow up</w:t></w:r></w:p></w:tc></w:tr>
    </w:tbl>
  </w:body>
</w:document>"""
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)


def _write_xlsx(path: Path) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
    workbook = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
    shared_strings = """<?xml version="1.0" encoding="UTF-8"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="6" uniqueCount="6">
  <si><t>Account</t></si><si><t>Status</t></si><si><t>Alpha</t></si>
  <si><t>Ready</t></si><si><t>Beta</t></si><si><t>Blocked</t></si>
</sst>"""
    sheet = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>
    <row r="2"><c r="A2" t="s"><v>2</v></c><c r="B2" t="s"><v>3</v></c></row>
    <row r="3"><c r="A3" t="s"><v>4</v></c><c r="B3" t="s"><v>5</v></c></row>
  </sheetData>
</worksheet>"""
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/sharedStrings.xml", shared_strings)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def _build_local_fixture_catalog(tmp_path: Path) -> Path:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    _write_pdf(fixtures_dir / "invoice.pdf")
    _write_docx(fixtures_dir / "minutes.docx")
    _write_xlsx(fixtures_dir / "status.xlsx")
    catalog = {
        "fixtures": [
            {
                "fixture_id": "invoice_pdf",
                "source_file": "fixtures/invoice.pdf",
                "format": "pdf",
                "required_terms": ["Invoice", "Total", "EUR"],
                "expected_table_headers": ["Item", "Qty", "Price"],
            },
            {
                "fixture_id": "minutes_docx",
                "source_file": "fixtures/minutes.docx",
                "format": "docx",
                "required_terms": ["Meeting", "Decision", "Approved"],
                "expected_table_headers": ["Owner", "Task"],
            },
            {
                "fixture_id": "status_xlsx",
                "source_file": "fixtures/status.xlsx",
                "format": "xlsx",
                "required_terms": ["Alpha", "Ready", "Beta"],
                "expected_table_headers": ["Account", "Status"],
            },
        ]
    }
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    return catalog_path


def test_compare_parser_fixtures_scores_and_selects_best_parser() -> None:
    report = compare_parser_fixtures(
        FIXTURE_ROOT / "catalog.json",
        FIXTURE_ROOT / "snapshots",
    )

    assert report["status"] == "ok"
    assert report["fixtures_compared"] == 2
    assert report["parsers"][0]["parser"] == "docling"
    by_fixture = {item["fixture_id"]: item for item in report["fixtures"]}
    assert by_fixture["invoice_pdf"]["best_parser"] == "docling"
    assert by_fixture["minutes_docx"]["best_parser"] == "unstructured"
    assert by_fixture["invoice_pdf"]["results"]["unstructured"]["missing_table_headers"] == ["Price"]


def test_compare_parser_fixtures_cli_human_output() -> None:
    env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "virgilio_connector",
            "compare-parser-fixtures",
            "--catalog",
            str(FIXTURE_ROOT / "catalog.json"),
            "--snapshots-dir",
            str(FIXTURE_ROOT / "snapshots"),
            "--human",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 0
    assert "Parser spike: 2 fixture confrontate" in completed.stdout
    assert "invoice_pdf: migliore docling" in completed.stdout


def test_compare_parser_fixtures_json_output_is_machine_readable() -> None:
    env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "virgilio_connector",
            "compare-parser-fixtures",
            "--catalog",
            str(FIXTURE_ROOT / "catalog.json"),
            "--snapshots-dir",
            str(FIXTURE_ROOT / "snapshots"),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["parsers"][0]["parser"] == "docling"


def test_extract_local_fixtures_reads_pdf_docx_xlsx(tmp_path: Path) -> None:
    catalog_path = _build_local_fixture_catalog(tmp_path)

    report = extract_local_fixtures(catalog_path)

    assert report["status"] == "ok"
    assert report["fixtures_compared"] == 3
    by_fixture = {item["fixture_id"]: item for item in report["fixtures"]}
    assert by_fixture["invoice_pdf"]["evaluation"]["quality_score"] == 1.0
    assert by_fixture["minutes_docx"]["evaluation"]["matched_table_headers"] == ["Owner", "Task"]
    assert by_fixture["status_xlsx"]["extraction"]["tables"][0][0] == ["Account", "Status"]


def test_extract_local_fixtures_cli_human_output(tmp_path: Path) -> None:
    catalog_path = _build_local_fixture_catalog(tmp_path)
    env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "virgilio_connector",
            "extract-local-fixtures",
            "--catalog",
            str(catalog_path),
            "--human",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 0
    assert "Parser locale: 3 fixture estratte" in completed.stdout
    assert "invoice_pdf: score 1.0" in completed.stdout


def test_extract_local_fixtures_cli_json_output_is_machine_readable(tmp_path: Path) -> None:
    catalog_path = _build_local_fixture_catalog(tmp_path)
    env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "virgilio_connector",
            "extract-local-fixtures",
            "--catalog",
            str(catalog_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["parser"] == "stdlib_local"
    assert payload["fixtures"][2]["fixture_id"] == "status_xlsx"
