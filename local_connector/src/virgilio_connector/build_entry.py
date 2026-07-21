"""Executable entry point for the standalone Caronte distribution."""

from __future__ import annotations

import os
import sys

from virgilio_connector.build_info import BuildInfoError, build_info_json, load_build_info


def _write_line(value: str, *, error: bool = False) -> None:
    """Write from both console and windowed PyInstaller executables."""

    stream = sys.stderr if error else sys.stdout
    if stream is not None:
        print(value, file=stream, flush=True)
        return
    if os.name != "nt":
        return
    import ctypes

    data = (value + "\r\n").encode("utf-8")
    written = ctypes.c_ulong(0)
    handle = ctypes.windll.kernel32.GetStdHandle(-12 if error else -11)
    if handle not in (0, -1):
        ctypes.windll.kernel32.WriteFile(handle, data, len(data), ctypes.byref(written), None)


def main() -> int:
    """Open Caronte, while retaining internal commands for owned workers."""

    if sys.argv[1:] == ["--build-info"]:
        try:
            _write_line(build_info_json(load_build_info()))
        except BuildInfoError:
            _write_line("Informazioni build assenti o non valide.", error=True)
            return 2
        return 0

    if sys.argv[1:] == ["--smoke-about-available"]:
        try:
            from virgilio_connector.user_app.about import ABOUT_TITLE, visible_build_information

            info = load_build_info()
            if ABOUT_TITLE != "Informazioni su Caronte" or len(visible_build_information(info)) != 4:
                return 3
        except (BuildInfoError, ImportError):
            return 3
        return 0

    demo_args = sys.argv[1:]
    if demo_args and demo_args[0] == "--demo":
        from virgilio_connector.user_app import launch_user_app

        screen = "welcome"
        scale = None
        for argument in demo_args[1:]:
            if argument.startswith("--demo-screen="):
                screen = argument.removeprefix("--demo-screen=")
            elif argument.startswith("--demo-scale="):
                scale = float(argument.removeprefix("--demo-scale="))
            else:
                return 2
        return launch_user_app(demo=True, demo_screen=screen, demo_scale=scale)

    if len(sys.argv) > 1:
        from virgilio_connector.__main__ import main as command_main

        result = command_main()
        return int(result or 0)

    from virgilio_connector.user_app import launch_user_app

    return launch_user_app()


if __name__ == "__main__":
    raise SystemExit(main())
