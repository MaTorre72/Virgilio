"""Google installed-app OAuth flow shared by Caronte presentations."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import sys
from typing import Callable, Mapping

from .credentials import (
    CredentialAlreadyExistsError,
    CredentialNotFoundError,
    CredentialStore,
)


GMAIL_IMAP_SCOPE = "https://mail.google.com/"
GOOGLE_SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
OAUTH_RESOURCE_NAME = "google_oauth_client.json"
OAUTH_CLIENT_PATH_ENV = "CARONTE_GOOGLE_OAUTH_CLIENT_PATH"
SHEETS_CREDENTIAL = "VIRGILIO_BUCOLICHE_GOOGLE_OAUTH"


class GoogleOAuthError(RuntimeError):
    """Base safe error for the Google mailbox authorization flow."""


class GoogleOAuthConfigurationError(GoogleOAuthError):
    """The distribution has no valid Desktop OAuth client configuration."""


@dataclass(frozen=True, slots=True)
class GoogleAuthorization:
    """Opaque authorization material; callers must persist it as a secret."""

    credentials_json: str = field(repr=False)
    access_token: str = field(repr=False)


def load_google_oauth_client_config() -> Mapping[str, object] | None:
    """Load an operator-provided client without asking end users for a file."""

    configured = os.environ.get(OAUTH_CLIENT_PATH_ENV, "").strip()
    candidates = []
    if configured:
        candidates.append(Path(configured))
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
    candidates.append(bundle_root / "resources" / OAUTH_RESOURCE_NAME)
    for path in candidates:
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            raise GoogleOAuthConfigurationError(
                "Google OAuth client configuration is invalid"
            ) from None
        if isinstance(payload, dict):
            return payload
        raise GoogleOAuthConfigurationError(
            "Google OAuth client configuration is invalid"
        )
    return None


class GoogleMailboxOAuthService:
    """Authorize Gmail through Google's supported desktop loopback flow."""

    def __init__(
        self,
        client_config: Callable[[], Mapping[str, object] | None] = load_google_oauth_client_config,
        *,
        flow_factory: Callable[[Mapping[str, object], tuple[str, ...]], object] | None = None,
    ) -> None:
        self._client_config = client_config
        self._flow_factory = flow_factory

    def authorize(self, email: str) -> GoogleAuthorization:
        if "@" not in email or not email.strip():
            raise GoogleOAuthConfigurationError("Google account email is required")
        config = self._client_config()
        if not isinstance(config, Mapping) or not isinstance(config.get("installed"), Mapping):
            raise GoogleOAuthConfigurationError(
                "Google Desktop OAuth client is not configured"
            )
        flow = self._flow(config)
        credentials = flow.run_local_server(
            host="127.0.0.1", port=0, open_browser=True
        )
        token = str(getattr(credentials, "token", "") or "")
        serialized = str(credentials.to_json())
        if not token or not serialized:
            raise GoogleOAuthError("Google authorization did not return credentials")
        return GoogleAuthorization(serialized, token)

    def access_token(self, credentials_json: str) -> GoogleAuthorization:
        """Load and, when needed, refresh previously protected credentials."""

        try:
            info = json.loads(credentials_json)
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials

            credentials = Credentials.from_authorized_user_info(
                info, scopes=(GMAIL_IMAP_SCOPE,)
            )
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            if not credentials.valid or not credentials.token:
                raise ValueError
            return GoogleAuthorization(credentials.to_json(), credentials.token)
        except GoogleOAuthError:
            raise
        except Exception as exc:
            name = type(exc).__name__.casefold()
            if any(word in name for word in ("timeout", "connection", "transport")):
                raise ConnectionError("Google authorization network error") from None
            raise PermissionError("Google authorization rejected") from None

    def _flow(self, config: Mapping[str, object]):
        scopes = (GMAIL_IMAP_SCOPE,)
        if self._flow_factory is not None:
            return self._flow_factory(config, scopes)
        from google_auth_oauthlib.flow import InstalledAppFlow

        return InstalledAppFlow.from_client_config(config, scopes=scopes)


class GoogleSheetsOAuthService:
    """Authorize the shared Register with the bundled client and protected storage."""

    def __init__(
        self,
        credentials: CredentialStore,
        client_config: Callable[[], Mapping[str, object] | None] = load_google_oauth_client_config,
        *,
        flow_factory: Callable[[Mapping[str, object], tuple[str, ...]], object] | None = None,
        credentials_loader: Callable[[Mapping[str, object], tuple[str, ...]], object] | None = None,
        request_factory: Callable[[], object] | None = None,
        client_factory: Callable[[str, object], object] | None = None,
    ) -> None:
        self.credentials = credentials
        self._client_config = client_config
        self._flow_factory = flow_factory
        self._credentials_loader = credentials_loader
        self._request_factory = request_factory
        self._client_factory = client_factory

    def authorize(self) -> None:
        config = self._desktop_config()
        flow = (
            self._flow_factory(config, (GOOGLE_SHEETS_SCOPE,))
            if self._flow_factory is not None
            else self._flow(config)
        )
        credentials = flow.run_local_server(
            host="127.0.0.1", port=0, open_browser=True
        )
        serialized = str(credentials.to_json())
        if not serialized:
            raise GoogleOAuthError("Google authorization did not return credentials")
        self._put(serialized)

    def client(self, spreadsheet_id: str):
        identifier = spreadsheet_id.strip()
        if not identifier:
            raise GoogleOAuthConfigurationError("Google Register is not configured")
        try:
            serialized = self.credentials.read(SHEETS_CREDENTIAL)
        except CredentialNotFoundError:
            raise GoogleOAuthConfigurationError(
                "Google Sheets authorization is not configured"
            ) from None
        try:
            info = json.loads(serialized)
            credentials = self._load_credentials(info)
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(self._request())
                self.credentials.update(SHEETS_CREDENTIAL, credentials.to_json())
            if not credentials.valid:
                raise ValueError
        except (ConnectionError, TimeoutError):
            raise
        except Exception:
            raise PermissionError("Google Sheets authorization rejected") from None
        if self._client_factory is not None:
            return self._client_factory(identifier, credentials)
        from ..bucoliche import GoogleSheetsAppendClient

        return GoogleSheetsAppendClient(identifier, credentials=credentials)

    def _desktop_config(self) -> Mapping[str, object]:
        config = self._client_config()
        if not isinstance(config, Mapping) or not isinstance(
            config.get("installed"), Mapping
        ):
            raise GoogleOAuthConfigurationError(
                "Google Desktop OAuth client is not configured"
            )
        return config

    def _flow(self, config: Mapping[str, object]):
        from google_auth_oauthlib.flow import InstalledAppFlow

        return InstalledAppFlow.from_client_config(
            config, scopes=(GOOGLE_SHEETS_SCOPE,)
        )

    def _load_credentials(self, info: Mapping[str, object]):
        if self._credentials_loader is not None:
            return self._credentials_loader(info, (GOOGLE_SHEETS_SCOPE,))
        from google.oauth2.credentials import Credentials

        return Credentials.from_authorized_user_info(
            info, scopes=(GOOGLE_SHEETS_SCOPE,)
        )

    def _request(self):
        if self._request_factory is not None:
            return self._request_factory()
        from google.auth.transport.requests import Request

        return Request()

    def _put(self, serialized: str) -> None:
        try:
            self.credentials.save(SHEETS_CREDENTIAL, serialized)
        except CredentialAlreadyExistsError:
            self.credentials.update(SHEETS_CREDENTIAL, serialized)


def create_google_sheets_oauth_service() -> GoogleSheetsOAuthService:
    from .windows_credentials import NativeWindowsCredentialApi, WindowsCredentialStore

    return GoogleSheetsOAuthService(
        WindowsCredentialStore(NativeWindowsCredentialApi())
    )
