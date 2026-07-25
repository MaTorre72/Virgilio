import json

from virgilio_connector.application.credentials import FakeCredentialStore
from virgilio_connector.application.google_oauth import (
    GOOGLE_SHEETS_SCOPE,
    SHEETS_CREDENTIAL,
    GoogleSheetsOAuthService,
)


class FakeCredentials:
    def __init__(self, *, expired=False):
        self.valid = not expired
        self.expired = expired
        self.refresh_token = "synthetic-refresh"
        self.token = "synthetic-token"
        self.refreshed_with = None

    def refresh(self, request):
        self.refreshed_with = request
        self.expired = False
        self.valid = True
        self.token = "synthetic-refreshed-token"

    def to_json(self):
        return json.dumps(
            {
                "token": self.token,
                "refresh_token": self.refresh_token,
                "client_id": "synthetic-client",
                "client_secret": "synthetic-secret",
            }
        )


class FakeFlow:
    def __init__(self, credentials):
        self.credentials = credentials
        self.calls = []

    def run_local_server(self, **kwargs):
        self.calls.append(kwargs)
        return self.credentials


def _client_config():
    return {"installed": {"client_id": "synthetic-client"}}


def test_sheets_authorization_uses_bundled_client_scope_and_protected_store():
    store = FakeCredentialStore()
    credentials = FakeCredentials()
    flow = FakeFlow(credentials)
    seen = []
    service = GoogleSheetsOAuthService(
        store,
        _client_config,
        flow_factory=lambda config, scopes: seen.append((config, scopes)) or flow,
    )

    service.authorize()

    assert seen == [(_client_config(), (GOOGLE_SHEETS_SCOPE,))]
    assert flow.calls == [{"host": "127.0.0.1", "port": 0, "open_browser": True}]
    assert json.loads(store.read(SHEETS_CREDENTIAL))["refresh_token"] == (
        "synthetic-refresh"
    )


def test_sheets_client_refreshes_and_replaces_only_protected_authorization():
    store = FakeCredentialStore()
    store.save(SHEETS_CREDENTIAL, '{"synthetic":"authorization"}')
    credentials = FakeCredentials(expired=True)
    request = object()
    clients = []
    service = GoogleSheetsOAuthService(
        store,
        _client_config,
        credentials_loader=lambda info, scopes: credentials,
        request_factory=lambda: request,
        client_factory=lambda identifier, auth: clients.append(
            (identifier, auth)
        ) or object(),
    )

    result = service.client("abcDEFGhijklmNOPQRST_uvwx")

    assert result is not None
    assert credentials.refreshed_with is request
    assert clients == [("abcDEFGhijklmNOPQRST_uvwx", credentials)]
    assert json.loads(store.read(SHEETS_CREDENTIAL))["token"] == (
        "synthetic-refreshed-token"
    )
