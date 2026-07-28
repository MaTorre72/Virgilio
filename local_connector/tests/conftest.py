"""Inventario vincolante dei livelli della suite locale."""

from pathlib import Path

import pytest


CONTRACT_MODULES = {
    "test_application_credentials.py",
    "test_build_info.py",
    "test_caronte_build.py",
    "test_caronte_http.py",
    "test_caronte_installer.py",
    "test_cli_surface.py",
    "test_contract.py",
    "test_files_policy.py",
    "test_no_network.py",
    "test_package_api.py",
    "test_registry_configuration.py",
    "test_traceability.py",
    "test_user_app_bucoliche_startup.py",
    "test_windows_credentials.py",
}

INTEGRATION_OFFLINE_MODULES = {
    "test_account_connection.py",
    "test_bucoliche.py",
    "test_caronte_dry_run.py",
    "test_da_archiviare_intake.py",
    "test_drive_staging_intake_test.py",
    "test_drive_staging_verify.py",
    "test_google_mailbox_oauth.py",
    "test_google_sheets_oauth.py",
    "test_multi_account.py",
    "test_operational_connection.py",
    "test_operational_handoff.py",
    "test_orchestrator.py",
    "test_pilot_readiness.py",
    "test_reset_local_state.py",
    "test_synthetic_emails.py",
    "test_test_environment_reset.py",
    "test_user_app.py",
    "test_user_app_home_control.py",
    "test_user_app_operational_feedback.py",
}

UNIT_MODULES = {
    "test_ack.py",
    "test_application_configuration.py",
    "test_application_paths.py",
    "test_imap_readonly.py",
    "test_maintenance_gui.py",
    "test_quarantine.py",
    "test_readonly_quarantine.py",
    "test_readonly_state_migrations.py",
    "test_scanner.py",
    "test_staging_transport.py",
    "test_state_db.py",
    "test_state_models.py",
    "test_user_app_accounts.py",
    "test_user_app_activity.py",
    "test_user_app_home.py",
    "test_user_app_limbo.py",
    "test_user_app_settings.py",
    "test_user_app_vertical_corrections.py",
    "test_windows_task.py",
}

LEVELS = {
    "unit": UNIT_MODULES,
    "contract": CONTRACT_MODULES,
    "integration_offline": INTEGRATION_OFFLINE_MODULES,
}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    del config
    test_root = Path(__file__).parent
    discovered = {path.name for path in test_root.glob("test_*.py")}
    inventoried = set().union(*LEVELS.values())
    duplicates = {
        name
        for name in inventoried
        if sum(name in modules for modules in LEVELS.values()) != 1
    }
    missing = discovered - inventoried
    stale = inventoried - discovered
    if duplicates or missing or stale:
        raise pytest.UsageError(
            "invalid test level inventory: "
            f"duplicates={sorted(duplicates)}, missing={sorted(missing)}, "
            f"stale={sorted(stale)}"
        )

    for item in items:
        module_name = Path(str(item.path)).name
        level = next(name for name, modules in LEVELS.items() if module_name in modules)
        item.add_marker(getattr(pytest.mark, level))
