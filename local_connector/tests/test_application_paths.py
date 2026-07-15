import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from virgilio_connector.application_paths import ApplicationPaths
from virgilio_connector.local_paths import LocalDataPaths


def test_windows_roots_define_configuration_and_data_directories(tmp_path):
    roaming = tmp_path / "roaming"
    local = tmp_path / "local"

    paths = ApplicationPaths.from_environment({"APPDATA": str(roaming), "LOCALAPPDATA": str(local)})

    assert paths.config_dir == roaming / "Caronte"
    assert paths.configuration_file == roaming / "Caronte" / "config.yaml"
    assert paths.data_dir == local / "Caronte"


def test_paths_do_not_depend_on_repository_or_working_directory(tmp_path, monkeypatch):
    working_dir = tmp_path / "unrelated"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)

    paths = ApplicationPaths.from_environment({
        "APPDATA": str(tmp_path / "roaming"),
        "LOCALAPPDATA": str(tmp_path / "local"),
    })

    assert working_dir not in paths.config_dir.parents
    assert working_dir not in paths.data_dir.parents


def test_roots_are_injectable_and_created_in_temporary_filesystem(tmp_path):
    paths = ApplicationPaths(tmp_path / "config", tmp_path / "data")

    paths.create()

    assert paths.config_dir.is_dir()
    assert paths.data_dir.is_dir()
    assert LocalDataPaths(paths.data_dir).root == tmp_path / "data"


def test_process_start_from_different_working_directory_uses_windows_roots(tmp_path):
    working_dir = tmp_path / "launch"
    working_dir.mkdir()
    env = os.environ.copy()
    env.pop("VIRGILIO_CONFIG_DIR", None)
    env.pop("VIRGILIO_LOCAL_DATA_DIR", None)
    env["APPDATA"] = str(tmp_path / "roaming")
    env["LOCALAPPDATA"] = str(tmp_path / "local")
    package_root = Path(__file__).parents[1] / "src"
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(package_root), env.get("PYTHONPATH"))))

    completed = subprocess.run(
        [sys.executable, "-c", (
            "import json; from virgilio_connector.application_paths import default_application_paths; "
            "p=default_application_paths(); print(json.dumps([str(p.config_dir), str(p.data_dir)]))"
        )],
        cwd=working_dir,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == [
        str(tmp_path / "roaming" / "Caronte"),
        str(tmp_path / "local" / "Caronte"),
    ]


def test_explicit_environment_overrides_are_supported(tmp_path):
    paths = ApplicationPaths.from_environment({
        "VIRGILIO_CONFIG_DIR": str(tmp_path / "custom-config"),
        "VIRGILIO_LOCAL_DATA_DIR": str(tmp_path / "custom-data"),
    })

    assert paths == ApplicationPaths(tmp_path / "custom-config", tmp_path / "custom-data")


def test_relative_override_cannot_reintroduce_working_directory_dependency(tmp_path):
    with pytest.raises(ValueError, match="must be absolute"):
        ApplicationPaths.from_environment({
            "APPDATA": str(tmp_path / "roaming"),
            "LOCALAPPDATA": str(tmp_path / "local"),
            "VIRGILIO_LOCAL_DATA_DIR": "relative-data",
        })
