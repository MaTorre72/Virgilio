"""Application services shared by Caronte presentations and the CLI."""

from .configuration import (
    ConfigurationModel,
    ConfigurationService,
    ConfigurationStore,
    YamlConfigurationStore,
)
from .credentials import (
    AccountCredentials,
    AccountCredentialService,
    CredentialAlreadyExistsError,
    CredentialNotFoundError,
    CredentialStore,
    CredentialStoreError,
    FakeCredentialStore,
)
from .windows_credentials import (
    CredentialAccessDeniedError,
    CredentialBackendError,
    CredentialBackendUnavailableError,
    NativeWindowsCredentialApi,
    WindowsCredentialApi,
    WindowsCredentialApiError,
    WindowsCredentialStore,
    create_account_credential_service,
    credential_error_message,
)

__all__ = [
    "ConfigurationModel",
    "ConfigurationService",
    "ConfigurationStore",
    "YamlConfigurationStore",
    "AccountCredentials",
    "AccountCredentialService",
    "CredentialAlreadyExistsError",
    "CredentialNotFoundError",
    "CredentialStore",
    "CredentialStoreError",
    "FakeCredentialStore",
    "CredentialAccessDeniedError",
    "CredentialBackendError",
    "CredentialBackendUnavailableError",
    "NativeWindowsCredentialApi",
    "WindowsCredentialApi",
    "WindowsCredentialApiError",
    "WindowsCredentialStore",
    "create_account_credential_service",
    "credential_error_message",
]
