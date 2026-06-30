"""Isolated parser comparison spike for synthetic fixture snapshots."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class ParserFixtureExpectation:
    fixture_id: str
    source_file: str
    format: str
    required_terms: tuple[str, ...]
    expected_table_headers: tuple[str, ...]
    notes: str = ""


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
