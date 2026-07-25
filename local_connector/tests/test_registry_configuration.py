from virgilio_connector.application.registry_configuration import RegistryConfigurationService
from virgilio_connector.bucoliche import load_bucoliche_config


def test_administrator_selection_persists_stable_spreadsheet_id_without_external_variable(tmp_path):
    path = tmp_path / "accounts.yaml"
    path.write_text("accounts: []\nstorage: {}\n", encoding="utf-8")
    service = RegistryConfigurationService(path)

    result = service.select_register(
        "https://docs.google.com/spreadsheets/d/abcDEFGhijklmNOPQRST_uvwx/edit#gid=0"
    )

    assert result.configured is True
    assert result.spreadsheet_id == "abcDEFGhijklmNOPQRST_uvwx"
    assert service.load() == result
    assert load_bucoliche_config(path).spreadsheet_id == result.spreadsheet_id
    assert load_bucoliche_config(path).enabled is True
    assert "VIRGILIO_BUCOLICHE_SPREADSHEET_ID" not in path.read_text(encoding="utf-8")


def test_existing_selected_register_is_enabled_without_reentering_data(tmp_path):
    path = tmp_path / "accounts.yaml"
    path.write_text(
        "bucoliche:\n"
        "  enabled: false\n"
        '  spreadsheet_id: "abcDEFGhijklmNOPQRST_uvwx"\n',
        encoding="utf-8",
    )
    service = RegistryConfigurationService(path)

    service.ensure_enabled()

    assert service.load().configured
    assert load_bucoliche_config(path).enabled is True


def test_administrator_selection_rejects_non_google_sheet_reference(tmp_path):
    service = RegistryConfigurationService(tmp_path / "accounts.yaml")

    result = service.select_register("not-a-register")

    assert result.configured is False
    assert not (tmp_path / "accounts.yaml").exists()
