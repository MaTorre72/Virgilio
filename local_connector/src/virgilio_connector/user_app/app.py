"""Minimal, independent shell for the Caronte user application."""

from __future__ import annotations

from pathlib import Path
from tkinter import ttk
from typing import Any

from ..application.account_connection import (
    AccountConnectionRequest,
    ReadonlyAccountConnectionService,
)
from ..application.account_management import AccountManagementService
from ..application.activity import ActivityService
from ..application.configuration import ConfigurationService
from ..application.home_status import AccountHomeStatusService, HomeStatus, HomeStatusService
from ..application.home_control import HomeRunController
from ..application.google_oauth import GoogleMailboxOAuthService
from ..application.operation_runner import ManagedOperationRunner
from ..application.settings import DisabledStartupAdapter, SettingsService
from ..application.bucoliche_startup import (
    BucolicheStartupService,
    ExistingBucolicheGateway,
    WindowsAutomaticControlGateway,
)
from ..application.windows_startup import WindowsStartupAdapter
from ..application.windows_credentials import create_account_credential_service
from ..application_paths import default_application_paths
from .home import HomeView, StaticHomeStatusService
from .demo import DemoState
from .activity import ActivitySource, ActivityView, EmptyActivitySource
from .navigation import UserRoute, initial_route
from .settings import SettingsView
from .bucoliche_startup import BucolicheStartupView
from .wizard import AccountForm, FirstRunController
from .about import show_about_dialog


WINDOW_TITLE = "Caronte"
USER_VIEWS = (
    "Primo avvio", "Home", "Attivita e problemi", "Impostazioni",
    "Registro e avvio",
)


class DemoHomeControl:
    """No-op control surface that keeps the demonstration isolated."""

    def check_now(self) -> None:
        return None

    def start(self) -> None:
        return None

    def pause(self) -> None:
        return None

    def close(self) -> None:
        return None

    def drain_feedback(self) -> tuple[object, ...]:
        return ()

    def set_interval_seconds(self, interval_seconds: int) -> None:
        return None

class UserAppShell:
    """Own the root window and route to the first user-facing screen."""

    def __init__(
        self,
        root: Any,
        configuration: ConfigurationService,
        *,
        ttk_module: Any = ttk,
        readonly_test: Any | None = None,
        google_access: Any | None = None,
        account_service: AccountManagementService | None = None,
        home_status: HomeStatusService | None = None,
        home_control: HomeRunController | None = None,
        activity_service: ActivitySource | None = None,
        settings_service: SettingsService | None = None,
        bucoliche_startup_service: BucolicheStartupService | None = None,
        demo: DemoState | None = None,
    ) -> None:
        self.root = root
        self._ttk = ttk_module
        self._readonly_test = readonly_test
        self._google_access = google_access
        self._account_service = account_service
        self._demo = demo
        self._settings_service = (
            None
            if demo is not None
            else settings_service or SettingsService(configuration, DisabledStartupAdapter())
        )
        self._bucoliche_startup_service = bucoliche_startup_service
        self._minimize_on_close = False
        interval_seconds = 300
        if demo is None and configuration.exists() and settings_service is not None:
            current_settings = self._settings_service.load()
            self._minimize_on_close = current_settings.minimize_on_close
            interval_seconds = current_settings.interval_minutes * 60
        self._home_control = (
            DemoHomeControl()
            if demo is not None
            else home_control or HomeRunController(
                configuration.store.source,
                ManagedOperationRunner(
                    environment_provider=(
                        account_service.protected_runtime_environment
                        if account_service is not None
                        else None
                    )
                ),
                interval_seconds=interval_seconds,
            )
        )
        self.route = UserRoute.FIRST_RUN if demo is not None else initial_route(configuration)
        self.root.title(WINDOW_TITLE)
        self.root.minsize(720, 480)
        self.current_frame: Any | None = None
        self.first_run: FirstRunController | None = None
        self.home: HomeView | None = None
        self.activity: ActivityView | None = None
        self.settings: SettingsView | None = None
        self.bucoliche_startup: BucolicheStartupView | None = None
        self._activity_service = activity_service or EmptyActivitySource()
        self._home_status = home_status or (
            StaticHomeStatusService(
                HomeStatus("Pronto per la dimostrazione", len(demo.accounts))
            )
            if demo is not None
            else AccountHomeStatusService(account_service)
            if account_service is not None
            else StaticHomeStatusService(HomeStatus("Pronto", 0))
        )
        self._render()
        self._schedule_home_poll()
        if hasattr(self.root, "protocol"):
            self.root.protocol("WM_DELETE_WINDOW", self.close_window)

    def _render(self, *, open_existing: bool = False) -> None:
        if self.current_frame is not None:
            self.current_frame.destroy()
        frame = self._ttk.Frame(
            self.root, padding=16 if self.route is UserRoute.FIRST_RUN else 32
        )
        frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame = frame
        controls = self._ttk.Frame(frame)
        controls.grid(row=0, column=0, sticky="e")
        self._ttk.Button(
            controls, text="Informazioni", command=self.show_about
        ).grid(row=0, column=0, padx=(0, 8))
        self._ttk.Button(
            controls, text="Riduci a icona", command=self.minimize
        ).grid(row=0, column=1, padx=(0, 8))
        self._ttk.Button(controls, text="Chiudi Caronte", command=self.close).grid(
            row=0, column=2
        )
        content = self._ttk.Frame(frame)
        content.grid(row=1, column=0, sticky="nsew")
        if self.route is UserRoute.FIRST_RUN:
            self.first_run = FirstRunController(
                content, ttk_module=self._ttk, readonly_test=self._readonly_test,
                google_access=self._google_access,
                account_service=self._account_service,
                on_complete=self.show_home,
                open_existing=open_existing,
                demo=self._demo,
            )
            return
        if self.route is UserRoute.ACTIVITY:
            self.activity = ActivityView(
                content,
                self._activity_service,
                ttk_module=self._ttk,
                go_home=self.show_home,
            )
            return
        if self.route is UserRoute.SETTINGS:
            self.settings = SettingsView(
                content,
                self._settings_service,
                ttk_module=self._ttk,
                go_home=self.show_home,
                on_saved=self._apply_settings,
            )
            return
        if self.route is UserRoute.BUCOLICHE_STARTUP:
            self.bucoliche_startup = BucolicheStartupView(
                content,
                self._bucoliche_startup_service,
                ttk_module=self._ttk,
                go_home=self.show_home,
            )
            return
        self.home = HomeView(
            content,
            self._home_status,
            ttk_module=self._ttk,
            check_now=self._home_control.check_now,
            start=self._home_control.start,
            pause=self._home_control.pause,
            open_configuration=self.open_configuration,
            open_activity=self.show_activity,
            open_settings=self.show_settings,
            open_bucoliche_startup=self.show_bucoliche_startup,
            demo=self._demo,
        )

    def poll_home_operations(self) -> int:
        feedback_items = self._home_control.drain_feedback()
        if self.route is not UserRoute.HOME or self.home is None:
            return len(feedback_items)
        for feedback in feedback_items:
            self._record_activity_feedback(feedback)
            activity_count = None
            if feedback.refresh_activity or feedback.activity:
                try:
                    activity_count = len(self._activity_service.list_activities())
                except Exception:
                    activity_count = None
            self.home.apply_feedback(feedback, activity_count=activity_count)
        return len(feedback_items)

    def _record_activity_feedback(self, feedback: object) -> None:
        record = getattr(self._activity_service, "record_control_feedback", None)
        activity = getattr(feedback, "activity", "")
        if callable(record) and activity:
            record(
                activity=activity,
                message=feedback.message,
                state=feedback.state,
                occurred_at=feedback.last_check,
            )

    def _schedule_home_poll(self) -> None:
        after = getattr(self.root, "after", None)
        if after is None:
            return

        def poll() -> None:
            self.poll_home_operations()
            if not getattr(self.root, "destroyed", False):
                after(100, poll)

        after(100, poll)

    def show_home(self) -> None:
        self.route = UserRoute.HOME
        self.first_run = None
        self._render()

    def open_configuration(self) -> None:
        self.route = UserRoute.FIRST_RUN
        self.home = None
        self._render(open_existing=True)

    def show_activity(self) -> None:
        self.route = UserRoute.ACTIVITY
        self.home = None
        self._render()

    def show_settings(self) -> None:
        self.route = UserRoute.SETTINGS
        self.home = None
        self._render()

    def show_bucoliche_startup(self) -> None:
        self.route = UserRoute.BUCOLICHE_STARTUP
        self.home = None
        self._render()

    def _apply_settings(self, interval_seconds: int, minimize_on_close: bool) -> None:
        self._home_control.set_interval_seconds(interval_seconds)
        self._minimize_on_close = minimize_on_close

    def minimize(self) -> None:
        self.root.iconify()

    def show_about(self) -> None:
        show_about_dialog(self.root)

    def close(self) -> None:
        """Stop the owned worker before closing the window."""

        self._home_control.close()
        self.root.destroy()

    def close_window(self) -> None:
        if self._minimize_on_close:
            self.minimize()
            return
        self.close()


def launch_user_app(
    *, config_path: Path | None = None, demo: bool = False, demo_screen: str = "welcome",
    demo_scale: float | None = None,
) -> int:
    """Create and run the Caronte window."""

    from tkinter import Tk

    root = Tk()
    if demo_scale is not None:
        root.tk.call("tk", "scaling", demo_scale)
    if demo:
        configuration = ConfigurationService.for_file(config_path or Path("demo.yaml"))
        shell = UserAppShell(root, configuration, demo=DemoState())
        _show_demo_screen(shell, demo_screen)
        root.mainloop()
        return 0

    paths = default_application_paths()
    configuration = ConfigurationService.for_file(config_path or paths.configuration_file)
    account_service = AccountManagementService(
        configuration, create_account_credential_service()
    )
    connection = ReadonlyAccountConnectionService(paths.data_dir / "connection-check")
    google_oauth = GoogleMailboxOAuthService()
    shell = UserAppShell(
        root,
        configuration,
        readonly_test=lambda form: connection.check(_connection_request(form)),
        google_access=lambda form: google_oauth.authorize(form.email),
        account_service=account_service,
        activity_service=ActivityService(paths.data_dir / "state.db"),
        settings_service=SettingsService(
            configuration, WindowsStartupAdapter(configuration.store.source)
        ),
        bucoliche_startup_service=BucolicheStartupService(
            configuration,
            ExistingBucolicheGateway(configuration.store.source),
            WindowsAutomaticControlGateway(configuration),
        ),
    )
    root.mainloop()
    return 0


def _connection_request(form: AccountForm) -> AccountConnectionRequest:
    return AccountConnectionRequest(
        email=form.email,
        password=form.password,
        host=form.host,
        port=form.port,
        auth_mode="oauth2" if form.provider == "gmail_workspace" else "password",
    )


def _show_demo_screen(shell: UserAppShell, screen: str) -> None:
    """Advance the isolated route to one requested evidence screen."""

    steps = {"welcome": 0, "limbo": 1, "caselle": 2, "riepilogo": 3, "home": 4}
    try:
        count = steps[screen]
    except KeyError as exc:
        raise ValueError(f"Schermata demo non supportata: {screen}") from exc
    for _ in range(count):
        assert shell.first_run is not None
        shell.first_run.continue_forward()
