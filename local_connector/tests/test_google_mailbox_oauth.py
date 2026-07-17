import json
import time

import pytest

from virgilio_connector.application.account_connection import (
    AccountConnectionRequest,
    ReadonlyAccountConnectionService,
    _safe_connection_error,
)
from virgilio_connector.application.google_oauth import (
    GoogleAuthorization,
    GoogleMailboxOAuthService,
    GoogleOAuthConfigurationError,
)
from virgilio_connector.application.account_management import AccountManagementService
from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.application.credentials import AccountCredentialService, FakeCredentialStore
from virgilio_connector.imap_readonly import ImapReadonlyConfig, ImapReadonlyMailbox
from virgilio_connector.user_app.wizard import AccountView, FirstRunController

from test_user_app import FakeButton, FakeEntry, FakeLabel, FakeRoot, FakeTtk


class FakeCredentials:
    def __init__(self, *, token="synthetic-access-token"):
        self.token = token
        self.valid = True
        self.expired = False
        self.refresh_token = "synthetic-refresh-token"

    def to_json(self):
        return json.dumps({
            "token": self.token,
            "refresh_token": self.refresh_token,
            "client_id": "synthetic-client-id",
            "client_secret": "synthetic-client-secret",
            "token_uri": "https://oauth2.googleapis.invalid/token",
        })


class FakeFlow:
    def __init__(self):
        self.calls = []

    def run_local_server(self, **kwargs):
        self.calls.append(kwargs)
        return FakeCredentials()


def _open_account_view(tmp_path, **kwargs):
    controller = FirstRunController(FakeRoot(), ttk_module=FakeTtk, **kwargs)
    controller.continue_forward()
    controller.current_view.folder_entry.set(str(tmp_path))
    controller.continue_forward()
    return controller, controller.current_view


def test_google_oauth_uses_official_installed_app_flow_and_returns_opaque_credentials():
    flow = FakeFlow()
    client_config = {
        "installed": {
            "client_id": "synthetic-client-id",
            "client_secret": "synthetic-client-secret",
            "auth_uri": "https://accounts.google.invalid/auth",
            "token_uri": "https://oauth2.googleapis.invalid/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    service = GoogleMailboxOAuthService(
        lambda: client_config,
        flow_factory=lambda config, scopes: flow,
    )

    result = service.authorize("person@example.invalid")

    assert isinstance(result, GoogleAuthorization)
    assert result.access_token == "synthetic-access-token"
    assert json.loads(result.credentials_json)["refresh_token"] == "synthetic-refresh-token"
    assert flow.calls == [{"host": "127.0.0.1", "port": 0, "open_browser": True}]
    assert "synthetic-access-token" not in repr(result)


def test_google_oauth_rejects_missing_or_non_desktop_client_configuration():
    with pytest.raises(GoogleOAuthConfigurationError):
        GoogleMailboxOAuthService(lambda: None).authorize("person@example.invalid")
    with pytest.raises(GoogleOAuthConfigurationError):
        GoogleMailboxOAuthService(lambda: {"web": {}}).authorize("person@example.invalid")


def test_gmail_view_offers_google_access_without_password_path(tmp_path):
    controller, view = _open_account_view(tmp_path, google_access=lambda form: None)

    assert isinstance(view, AccountView)
    assert view.provider == "gmail_workspace"
    assert view.password_entry.grid_options is None
    assert view.password_label.grid_options is None
    assert "Password" not in view.visible_fields()
    assert any(
        button.kwargs.get("text") == "Accedi con Google"
        for button in FakeButton.created
    )
    view.email_entry.set("person@example.invalid")
    assert controller._account_validator.validate(view.form_value()).message == (
        "Accedi con Google per collegare la casella."
    )


def test_generic_imap_keeps_provider_specific_host_port_and_password(tmp_path):
    _controller, view = _open_account_view(tmp_path)

    view.use_generic_provider()
    view.email_entry.set("person@example.invalid")
    view.password_entry.set("synthetic-password")
    view.host_entry.set("imap.example.invalid")
    view.port_entry.set("1993")
    form = view.form_value()

    assert view.provider == "custom_imap"
    assert view.password_entry.grid_options is not None
    assert form.password == "synthetic-password"
    assert (form.host, form.port) == ("imap.example.invalid", 1993)


def test_google_connection_uses_xoauth2_and_never_password_login(tmp_path):
    operations = []

    class FakeImap:
        def __init__(self, host, port, timeout):
            operations.append(("create", host, port, timeout))

        def authenticate(self, mechanism, callback):
            operations.append(("authenticate", mechanism, callback(None)))
            return "OK", [b"authenticated"]

        def login(self, username, password):
            raise AssertionError("Google must not use password login")

        def select(self, mailbox, readonly):
            return "OK", [b"0"]

        def uid(self, *args):
            return "OK", [b""]

        def close(self):
            return "OK", []

        def logout(self):
            return "BYE", []

    config = ImapReadonlyConfig(
        host="imap.gmail.com",
        username="person@example.invalid",
        password="synthetic-access-token",
        auth_mode="oauth2",
    )
    mailbox = ImapReadonlyMailbox(config, tmp_path, client_factory=FakeImap)

    assert mailbox.list_pending() == ()
    assert operations[1][0:2] == ("authenticate", "XOAUTH2")
    payload = operations[1][2].decode("utf-8")
    assert payload == (
        "user=person@example.invalid\x01auth=Bearer synthetic-access-token\x01\x01"
    )


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (GoogleOAuthConfigurationError("missing"), "Collegamento Google non configurato."),
        (PermissionError("access denied"), "Accesso Google rifiutato."),
        (TimeoutError("network timeout"), "Casella non raggiungibile."),
    ],
)
def test_connection_errors_distinguish_incomplete_rejected_and_network(error, expected):
    assert _safe_connection_error(error).startswith(expected)


def test_connection_request_marks_google_access_as_oauth2(tmp_path):
    captured = []

    class FakeMailbox:
        def __init__(self, config, root):
            captured.append(config)

        def list_pending(self):
            return ()

    service = ReadonlyAccountConnectionService(tmp_path, mailbox_factory=FakeMailbox)
    service.check(AccountConnectionRequest(
        email="person@example.invalid",
        password="synthetic-access-token",
        host="imap.gmail.com",
        auth_mode="oauth2",
    ))

    assert captured[0].auth_mode == "oauth2"


def test_google_credentials_are_persisted_only_in_protected_store(tmp_path):
    config_path = tmp_path / "config.yaml"
    store = FakeCredentialStore()
    accounts = AccountManagementService(
        ConfigurationService.for_file(config_path), AccountCredentialService(store)
    )
    authorization = GoogleAuthorization(
        credentials_json=json.dumps({
            "token": "synthetic-access-token",
            "refresh_token": "synthetic-refresh-token",
        }),
        access_token="synthetic-access-token",
    )
    controller = FirstRunController(
        FakeRoot(),
        ttk_module=FakeTtk,
        account_service=accounts,
        google_access=lambda _form: authorization,
        readonly_test=lambda _form: "Collegamento riuscito.",
    )
    controller.continue_forward()
    controller.current_view.folder_entry.set(str(tmp_path))
    controller.continue_forward()
    view = controller.current_view
    view.email_entry.set("person@example.invalid")

    assert controller.test_account_connection().is_valid
    deadline = time.monotonic() + 1
    while controller.poll_account_connection() is None and time.monotonic() < deadline:
        time.sleep(0.005)
    assert controller.add_account().is_valid

    account = accounts.configuration.load().accounts[0]
    protected = store.read(account.password_env)
    disk_text = config_path.read_text(encoding="utf-8")
    visible_message = view.message.config["text"]
    assert json.loads(protected)["refresh_token"] == "synthetic-refresh-token"
    assert "synthetic-access-token" not in disk_text
    assert "synthetic-refresh-token" not in disk_text
    assert "synthetic-access-token" not in visible_message
    assert "synthetic-refresh-token" not in visible_message
