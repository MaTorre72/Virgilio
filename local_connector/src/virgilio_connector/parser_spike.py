"""Isolated parser comparison spike for synthetic fixture snapshots."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile


@dataclass(frozen=True)
class ParserFixtureExpectation:
    fixture_id: str
    source_file: str
    format: str
    required_terms: tuple[str, ...]
    expected_table_headers: tuple[str, ...]
    notes: str = ""


WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
SHEET_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _load_catalog(path: Path) -> tuple[ParserFixtureExpectation, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    fixtures = raw.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ValueError("fixture catalog must contain a non-empty fixtures list")
    items: list[ParserFixtureExpectation] = []
    for entry in fixtures:
        if not isinstance(entry, dict):
            raise ValueError("fixture catalog entries must be objects")
        fixture_id = str(entry.get("fixture_id", "")).strip()
        source_file = str(entry.get("source_file", "")).strip()
        fmt = str(entry.get("format", "")).strip().lower()
        required_terms = tuple(str(item).strip() for item in entry.get("required_terms", ()))
        expected_headers = tuple(str(item).strip() for item in entry.get("expected_table_headers", ()))
        if not fixture_id or not source_file or not fmt:
            raise ValueError("fixture catalog entries require fixture_id, source_file and format")
        items.append(ParserFixtureExpectation(
            fixture_id=fixture_id,
            source_file=source_file,
            format=fmt,
            required_terms=required_terms,
            expected_table_headers=expected_headers,
            notes=str(entry.get("notes", "")).strip(),
        ))
    return tuple(items)


def _load_snapshot(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"invalid parser snapshot: {path}")
    return raw


def _unescape_pdf_literal(value: str) -> str:
    escapes = {
        r"\n": "\n",
        r"\r": "\r",
        r"\t": "\t",
        r"\b": "\b",
        r"\f": "\f",
        r"\(": "(",
        r"\)": ")",
        r"\\": "\\",
    }
    for source, target in escapes.items():
        value = value.replace(source, target)
    return value


def _extract_pdf_text(path: Path) -> tuple[str, list[str]]:
    data = path.read_bytes()
    warnings: list[str] = []
    chunks: list[str] = []
    for match in re.finditer(rb"\((?:\\.|[^\\)])*\)\s*Tj", data):
        literal = match.group(0).rsplit(b")", 1)[0][1:]
        chunks.append(_unescape_pdf_literal(literal.decode("latin-1", errors="ignore")))
    for match in re.finditer(rb"\[(.*?)\]\s*TJ", data, flags=re.DOTALL):
        array_data = match.group(1)
        pieces = re.findall(rb"\((?:\\.|[^\\)])*\)", array_data)
        if not pieces:
            continue
        chunks.append("".join(_unescape_pdf_literal(item[1:-1].decode("latin-1", errors="ignore"))
                              for item in pieces))
    if not chunks:
        warnings.append("no_text_operators_found")
    return "\n".join(chunk.strip() for chunk in chunks if chunk.strip()).strip(), warnings


def _infer_tables_from_text(text: str) -> list[list[list[str]]]:
    rows = [[token for token in line.split() if token] for line in text.splitlines()]
    rows = [row for row in rows if len(row) >= 2]
    return [rows] if rows else []


def _docx_paragraph_text(root: ET.Element) -> list[str]:
    lines: list[str] = []
    for paragraph in root.findall(".//w:body/w:p", WORD_NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", WORD_NS)).strip()
        if text:
            lines.append(text)
    return lines


def _extract_docx(path: Path) -> tuple[str, list[list[list[str]]], list[str]]:
    with ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml")
    root = ET.fromstring(document_xml)
    tables: list[list[list[str]]] = []
    for table in root.findall(".//w:tbl", WORD_NS):
        rows: list[list[str]] = []
        for row in table.findall("./w:tr", WORD_NS):
            cells = ["".join(node.text or "" for node in cell.findall(".//w:t", WORD_NS)).strip()
                     for cell in row.findall("./w:tc", WORD_NS)]
            rows.append(cells)
        tables.append(rows)
    text_lines = _docx_paragraph_text(root)
    return "\n".join(text_lines), tables, []


def _xlsx_shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall("./main:si", SHEET_NS):
        values.append("".join(node.text or "" for node in item.findall(".//main:t", SHEET_NS)))
    return values


def _xlsx_sheet_paths(archive: ZipFile) -> list[str]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rel_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rel_root.findall("./r:Relationship", REL_NS)
        if rel.attrib.get("Id") and rel.attrib.get("Target")
    }
    paths: list[str] = []
    for sheet in workbook.findall("./main:sheets/main:sheet", SHEET_NS):
        rel_id = sheet.attrib.get(f"{{{SHEET_NS['rel']}}}id")
        target = rel_map.get(rel_id, "")
        if target:
            paths.append(f"xl/{target.lstrip('/')}")
    return paths


def _xlsx_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//main:t", SHEET_NS))
    value = cell.findtext("./main:v", default="", namespaces=SHEET_NS)
    if cell_type == "s" and value.isdigit():
        index = int(value)
        if 0 <= index < len(shared_strings):
            return shared_strings[index]
    return value


def _extract_xlsx(path: Path) -> tuple[str, list[list[list[str]]], list[str]]:
    with ZipFile(path) as archive:
        shared_strings = _xlsx_shared_strings(archive)
        tables: list[list[list[str]]] = []
        text_lines: list[str] = []
        for sheet_path in _xlsx_sheet_paths(archive):
            sheet_root = ET.fromstring(archive.read(sheet_path))
            rows: list[list[str]] = []
            for row in sheet_root.findall(".//main:sheetData/main:row", SHEET_NS):
                values = [_xlsx_cell_value(cell, shared_strings).strip()
                          for cell in row.findall("./main:c", SHEET_NS)]
                if any(value for value in values):
                    rows.append(values)
                    text_lines.append(" ".join(value for value in values if value))
            tables.append(rows)
    return "\n".join(text_lines), tables, []


def extract_fixture_snapshot(path: Path, fmt: str) -> dict[str, object]:
    normalized = fmt.strip().lower()
    if normalized == "pdf":
        text, warnings = _extract_pdf_text(path)
        tables = _infer_tables_from_text(text)
    elif normalized == "docx":
        text, tables, warnings = _extract_docx(path)
    elif normalized == "xlsx":
        text, tables, warnings = _extract_xlsx(path)
    else:
        raise ValueError(f"unsupported fixture format: {fmt}")
    return {
        "text": text,
        "tables": tables,
        "warnings": warnings,
    }


def _snapshot_index(snapshot_root: Path) -> dict[str, dict[str, dict[str, object]]]:
    index: dict[str, dict[str, dict[str, object]]] = {}
    for parser_dir in sorted(item for item in snapshot_root.iterdir() if item.is_dir()):
        parser_name = parser_dir.name
        parser_items: dict[str, dict[str, object]] = {}
        for snapshot_path in sorted(parser_dir.glob("*.json")):
            snapshot = _load_snapshot(snapshot_path)
            fixture_id = str(snapshot.get("fixture_id", "")).strip()
            if not fixture_id:
                raise ValueError(f"missing fixture_id in snapshot: {snapshot_path}")
            parser_items[fixture_id] = snapshot
        index[parser_name] = parser_items
    if not index:
        raise ValueError("snapshot directory does not contain parser subdirectories")
    return index


def _extract_table_text(snapshot: dict[str, object]) -> str:
    tables = snapshot.get("tables", [])
    flattened: list[str] = []
    if isinstance(tables, list):
        for table in tables:
            if isinstance(table, list):
                for row in table:
                    if isinstance(row, list):
                        flattened.extend(str(cell) for cell in row)
                    else:
                        flattened.append(str(row))
            else:
                flattened.append(str(table))
    return _normalize(" ".join(flattened))


def _score_fixture(expectation: ParserFixtureExpectation,
                   snapshot: dict[str, object] | None) -> dict[str, object]:
    if snapshot is None:
        return {
            "status": "missing_snapshot",
            "quality_score": 0.0,
            "term_coverage": 0.0,
            "table_header_coverage": 0.0 if expectation.expected_table_headers else None,
            "matched_terms": [],
            "missing_terms": list(expectation.required_terms),
            "matched_table_headers": [],
            "missing_table_headers": list(expectation.expected_table_headers),
            "warnings": ["missing parser snapshot for fixture"],
        }
    text = _normalize(str(snapshot.get("text", "")))
    table_text = _extract_table_text(snapshot)
    matched_terms = [term for term in expectation.required_terms if _normalize(term) in text]
    missing_terms = [term for term in expectation.required_terms if term not in matched_terms]
    term_coverage = round(len(matched_terms) / len(expectation.required_terms), 3) if expectation.required_terms else 1.0
    matched_headers = [header for header in expectation.expected_table_headers
                       if _normalize(header) in table_text]
    missing_headers = [header for header in expectation.expected_table_headers if header not in matched_headers]
    if expectation.expected_table_headers:
        header_coverage = round(len(matched_headers) / len(expectation.expected_table_headers), 3)
        quality_score = round((term_coverage * 0.7) + (header_coverage * 0.3), 3)
    else:
        header_coverage = None
        quality_score = term_coverage
    warnings = [str(item) for item in snapshot.get("warnings", [])]
    return {
        "status": "ok",
        "quality_score": quality_score,
        "term_coverage": term_coverage,
        "table_header_coverage": header_coverage,
        "matched_terms": matched_terms,
        "missing_terms": missing_terms,
        "matched_table_headers": matched_headers,
        "missing_table_headers": missing_headers,
        "warnings": warnings,
    }


def compare_parser_fixtures(catalog_path: Path, snapshot_root: Path) -> dict[str, object]:
    expectations = _load_catalog(catalog_path)
    snapshots = _snapshot_index(snapshot_root)
    parser_names = sorted(snapshots)
    fixtures_report: list[dict[str, object]] = []
    parser_scores = {name: [] for name in parser_names}
    parser_warning_counts = {name: 0 for name in parser_names}
    parser_best_fixtures = {name: 0 for name in parser_names}
    for expectation in expectations:
        parser_results: dict[str, dict[str, object]] = {}
        for parser_name in parser_names:
            result = _score_fixture(expectation, snapshots.get(parser_name, {}).get(expectation.fixture_id))
            parser_results[parser_name] = result
            parser_scores[parser_name].append(float(result["quality_score"]))
            parser_warning_counts[parser_name] += len(result["warnings"])
        best_parser = min(
            parser_names,
            key=lambda name: (-float(parser_results[name]["quality_score"]),
                              len(parser_results[name]["warnings"]), name),
        )
        parser_best_fixtures[best_parser] += 1
        fixtures_report.append({
            "fixture_id": expectation.fixture_id,
            "source_file": expectation.source_file,
            "format": expectation.format,
            "notes": expectation.notes,
            "best_parser": best_parser,
            "results": parser_results,
        })
    parser_summary = []
    for parser_name in parser_names:
        scores = parser_scores[parser_name]
        parser_summary.append({
            "parser": parser_name,
            "fixtures_compared": len(scores),
            "average_quality_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
            "best_fixture_count": parser_best_fixtures[parser_name],
            "warning_count": parser_warning_counts[parser_name],
        })
    parser_summary.sort(key=lambda item: (-float(item["average_quality_score"]),
                                          -int(item["best_fixture_count"]),
                                          int(item["warning_count"]),
                                          str(item["parser"])))
    return {
        "status": "ok",
        "catalog_path": str(catalog_path),
        "snapshot_root": str(snapshot_root),
        "fixtures_compared": len(expectations),
        "parsers": parser_summary,
        "fixtures": fixtures_report,
    }


def extract_local_fixtures(catalog_path: Path, source_root: Path | None = None) -> dict[str, object]:
    expectations = _load_catalog(catalog_path)
    base_root = source_root or catalog_path.parent
    fixtures_report: list[dict[str, object]] = []
    quality_scores: list[float] = []
    warning_count = 0
    for expectation in expectations:
        source_path = (base_root / expectation.source_file).resolve()
        snapshot = extract_fixture_snapshot(source_path, expectation.format)
        evaluation = _score_fixture(expectation, snapshot)
        quality_scores.append(float(evaluation["quality_score"]))
        warning_count += len(snapshot["warnings"]) + len(evaluation["warnings"])
        fixtures_report.append({
            "fixture_id": expectation.fixture_id,
            "source_file": str(source_path),
            "format": expectation.format,
            "notes": expectation.notes,
            "extraction": {
                "parser": "stdlib_local",
                **snapshot,
            },
            "evaluation": evaluation,
        })
    return {
        "status": "ok",
        "parser": "stdlib_local",
        "catalog_path": str(catalog_path),
        "source_root": str(base_root),
        "fixtures_compared": len(expectations),
        "average_quality_score": round(sum(quality_scores) / len(quality_scores), 3) if quality_scores else 0.0,
        "warning_count": warning_count,
        "fixtures": fixtures_report,
    }


def parser_spike_human_summary(report: dict[str, object]) -> list[str]:
    lines = [f"Parser spike: {report['fixtures_compared']} fixture confrontate"]
    for parser in report.get("parsers", []):
        lines.append(
            f"{parser['parser']}: score medio {parser['average_quality_score']}, "
            f"best fixture {parser['best_fixture_count']}, warning {parser['warning_count']}"
        )
    for fixture in report.get("fixtures", []):
        lines.append(f"{fixture['fixture_id']}: migliore {fixture['best_parser']}")
    return lines


def extracted_fixtures_human_summary(report: dict[str, object]) -> list[str]:
    lines = [
        f"Parser locale: {report['fixtures_compared']} fixture estratte",
        f"Score medio: {report['average_quality_score']}; warning: {report['warning_count']}",
    ]
    for fixture in report.get("fixtures", []):
        evaluation = fixture["evaluation"]
        lines.append(
            f"{fixture['fixture_id']}: score {evaluation['quality_score']}, "
            f"termini ok {len(evaluation['matched_terms'])}/{len(evaluation['matched_terms']) + len(evaluation['missing_terms'])}"
        )
    return lines
