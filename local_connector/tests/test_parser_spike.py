from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from virgilio_connector.parser_spike import compare_parser_fixtures


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "parser_spike"


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
