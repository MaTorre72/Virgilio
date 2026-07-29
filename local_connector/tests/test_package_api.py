from __future__ import annotations

import importlib

import virgilio_connector


def test_package_root_exposes_only_the_intentional_public_api() -> None:
    assert virgilio_connector.__all__ == ["__version__"]
    assert virgilio_connector.__version__ == "1.1.0"


def test_supported_entry_modules_remain_importable() -> None:
    for module_name in (
        "virgilio_connector.__main__",
        "virgilio_connector.build_entry",
        "virgilio_connector.maintenance_gui",
        "virgilio_connector.user_app",
    ):
        assert importlib.import_module(module_name).__name__ == module_name
