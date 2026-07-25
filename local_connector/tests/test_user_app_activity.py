from datetime import date

from virgilio_connector.application.activity import (
    ActivityFilters,
    ActivityService,
    filter_activities,
    project_activity,
)
from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.user_app.app import UserAppShell

from test_user_app import (
    FakeButton,
    FakeEntry,
    FakeFrame,
    FakeLabel,
    FakeRoot,
    FakeTreeview,
    FakeTtk,
)


def _event(**changes):
    values = {
        "created_at": "2026-07-16T08:30:00+00:00",
        "account_alias": "Casella studio",
        "event_type": "attachment_staged",
        "result": "staged",
        "staged_filename": "fattura.pdf",
        "conflict_type": "",
    }
    values.update(changes)
    return values


class StaticActivityService:
    def __init__(self, rows):
        self.rows = rows

    def list_activities(self):
        return self.rows


def _shell(tmp_path, rows):
    config = tmp_path / "config.yaml"
    config.write_text("present: true\n", encoding="utf-8")
    shell = UserAppShell(
        FakeRoot(),
        ConfigurationService.for_file(config),
        ttk_module=FakeTtk,
        activity_service=StaticActivityService(rows),
    )
    shell.show_activity()
    return shell


def test_activity_projection_and_combined_filters_are_user_facing():
    rows = tuple(project_activity(item) for item in (
        _event(),
        _event(event_type="failed", result="failed"),
        _event(account_alias="Casella famiglia", created_at="2026-07-15T08:30:00+00:00"),
    ))

    selected = filter_activities(rows, ActivityFilters(
        account="Casella studio", outcome="Problema", day=date(2026, 7, 16)
    ))

    assert len(selected) == 1
    assert selected[0].recommended_action == "Riprova il controllo; se il problema continua, chiedi assistenza."


def test_activity_service_reads_existing_events_without_exposing_raw_data(tmp_path):
    raw = _event(
        event_type='failed{"password":"segreto"}',
        result="failed",
        staged_filename="C:/riservato/fattura.pdf",
        details_json='{"password":"segreto","path":"C:/riservato"}',
    )
    service = ActivityService(tmp_path / "state.db", event_reader=lambda _: [raw])

    row = service.list_activities()[0]

    visible = " ".join(row.visible_values)
    assert row.attachment == "fattura.pdf"
    assert "{" not in visible and "segreto" not in visible and "C:/" not in visible
    assert "{" not in row.technical_detail and "segreto" not in row.technical_detail


def test_activity_view_has_table_filters_and_no_json(tmp_path):
    row = project_activity(_event())
    shell = _shell(tmp_path, (row,))

    tree = FakeTreeview.created[-1]
    assert tuple(tree.headings) == ("quando", "casella", "documento", "attivita", "esito", "azione")
    assert tree.rows["0"] == row.visible_values
    labels = " ".join(widget.kwargs.get("text", "") for widget in FakeLabel.created)
    assert "Filtra per casella" in labels
    assert "Filtra per esito" in labels
    assert "Data (gg/mm/aaaa)" in labels
    assert "json" not in labels.lower()
    assert shell.activity.technical_panel_open is False
    assert shell.activity.technical_label.grid_options is None


def test_activity_view_applies_account_outcome_and_date_filters(tmp_path):
    rows = tuple(project_activity(item) for item in (
        _event(),
        _event(event_type="failed", result="failed"),
        _event(account_alias="Casella famiglia", created_at="2026-07-15T08:30:00+00:00"),
    ))
    shell = _shell(tmp_path, rows)
    view = shell.activity
    view.account_filter.insert(0, "Casella studio")
    view.outcome_filter.insert(0, "Problema")
    view.day_filter.insert(0, "16/07/2026")

    view.apply_filters()

    assert len(view.table.rows) == 1
    assert next(iter(view.table.rows.values()))[-2:] == (
        "Problema",
        "Riprova il controllo; se il problema continua, chiedi assistenza.",
    )


def test_problem_has_recommended_action_and_technical_detail_is_opt_in(tmp_path):
    row = project_activity(_event(event_type="conflict_duplicate", conflict_type="duplicate"))
    shell = _shell(tmp_path, (row,))
    view = shell.activity
    view.table.select("0")

    assert row.recommended_action == "Controlla il documento prima di riprovare."
    assert view.technical_label.grid_options is None

    view.toggle_technical_detail()

    assert view.technical_panel_open is True
    assert view.technical_label.grid_options is not None
    assert view.technical_label.config["text"].startswith("Tipo evento:")
    assert "{" not in view.technical_label.config["text"]


def test_da_archiviare_events_show_delivery_waiting_and_problem_states():
    delivered = project_activity(_event(
        event_type="da_archiviare_intake", result="idempotent"
    ))
    waiting = project_activity(_event(
        event_type="da_archiviare_intake", result="waiting"
    ))
    failed = project_activity(_event(
        event_type="da_archiviare_intake", result="failed"
    ))

    assert delivered.visible_values[-3:] == (
        "Lavoro disponibile in Virgilio",
        "In attesa",
        "Completa la decisione in Da archiviare.",
    )
    assert waiting.visible_values[-3:] == (
        "Sincronizzazione del Limbo",
        "In attesa",
        "Attendi la sincronizzazione; Caronte riprovera automaticamente.",
    )
    assert failed.visible_values[-3:] == (
        "Invio a Da archiviare",
        "Problema",
        "Riprova il controllo; se il problema continua, chiedi assistenza.",
    )


def test_activity_labels_distinguish_acquisition_available_work_and_archiving():
    acquired = project_activity(_event(event_type="attachment_quarantined"))
    available = project_activity(_event(
        event_type="da_archiviare_intake", result="created"
    ))
    archived = project_activity(_event(event_type="message_completed", result="completed"))

    assert acquired.activity == "Documento acquisito"
    assert available.activity == "Lavoro disponibile in Virgilio"
    assert archived.activity == "Pratica archiviata"
