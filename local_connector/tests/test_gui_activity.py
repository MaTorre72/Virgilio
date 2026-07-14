from datetime import date

from virgilio_connector.gui_activity import (
    ActivityFilters,
    filter_activities,
    project_activity,
)


def event(**changes):
    values = {
        "created_at": "2026-07-14T16:30:00+00:00",
        "account_alias": "account_1",
        "event_type": "attachment_staged",
        "result": "staged",
        "staged_filename": "fattura.pdf",
        "conflict_type": "",
    }
    values.update(changes)
    return values


def test_projection_uses_rome_time_and_readable_fields():
    row = project_activity(event())

    assert row.occurred_text == "14/07/2026 18:30:00"
    assert row.day == date(2026, 7, 14)
    assert row.account == "account_1"
    assert row.message == "Pronto in Da archiviare"
    assert row.attachment == "fattura.pdf"
    assert row.action == "Allegato preparato"
    assert row.outcome == "Riuscito"
    assert row.problem == ""


def test_projection_makes_failures_actionable_without_json_or_paths():
    row = project_activity(event(
        event_type="failed", result="failed", staged_filename="C:/private/fattura.pdf",
        details_json='{"password":"very-secret","path":"C:/private"}',
    ))

    assert row.outcome == "Problema"
    assert "Diagnostica avanzata" in row.problem
    assert row.attachment == "fattura.pdf"
    assert "very-secret" not in " ".join((row.message, row.action, row.problem))
    assert "{" not in " ".join((row.message, row.action, row.problem))


def test_projection_applies_configured_redaction_to_visible_values():
    row = project_activity(event(account_alias="secret-account", staged_filename="secret.pdf"),
                           redact=lambda value: value.replace("secret", "<redacted>"))

    assert row.account == "<redacted>-account"
    assert row.attachment == "<redacted>.pdf"


def test_combined_filters_cover_account_outcome_day_and_errors():
    rows = tuple(project_activity(item) for item in (
        event(account_alias="account_1"),
        event(account_alias="account_1", event_type="failed", result="failed"),
        event(account_alias="account_2", created_at="2026-07-13T21:30:00+00:00"),
    ))

    selected = filter_activities(rows, ActivityFilters(
        account="account_1", outcome="Problema", day=date(2026, 7, 14), errors="only",
    ))
    assert len(selected) == 1
    assert selected[0].problem

    without_errors = filter_activities(rows, ActivityFilters(errors="without"))
    assert len(without_errors) == 2
    assert all(not row.problem for row in without_errors)


def test_rows_are_newest_first_after_filtering():
    rows = tuple(project_activity(item) for item in (
        event(created_at="2026-07-14T10:00:00+00:00"),
        event(created_at="2026-07-14T12:00:00+00:00"),
    ))

    selected = filter_activities(rows, ActivityFilters())
    assert selected[0].occurred_text == "14/07/2026 14:00:00"
