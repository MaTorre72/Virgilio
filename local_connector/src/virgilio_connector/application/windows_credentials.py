"""Windows Credential Manager adapter for Caronte account credentials."""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from typing import NoReturn, Protocol

from .credentials import (
    AccountCredentialService,
    CredentialAlreadyExistsError,
    CredentialNotFoundError,
    CredentialStoreError,
    _validated_reference,
    _validated_value,
)


ERROR_ACCESS_DENIED = 5
ERROR_NOT_FOUND = 1168
CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2


class CredentialBackendError(CredentialStoreError):
    """Raised when the protected credential backend cannot complete an operation."""


class CredentialBackendUnavailableError(CredentialBackendError):
    """Raised when Windows Credential Manager is unavailable."""


class CredentialAccessDeniedError(CredentialBackendError):
    """Raised when Windows refuses access to the credential backend."""


class WindowsCredentialApiError(OSError):
    """Safe low-level Windows API error without credential data."""

    def __init__(self, operation: str, error_code: int) -> None:
        super().__init__(error_code, f"Windows credential operation failed: {operation}")
        self.operation = operation
        self.error_code = error_code


class WindowsCredentialApi(Protocol):
    """Small mockable surface over the native Windows credential functions."""

    def write(self, target: str, value: str) -> None: ...

    def read(self, target: str) -> str: ...

    def delete(self, target: str) -> None: ...


class _CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class NativeWindowsCredentialApi:
    """Thin ctypes wrapper around the current user's Windows Credential Manager."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise CredentialBackendUnavailableError(
                "Windows protected credentials are unavailable"
            )
        self._advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        self._configure_functions()

    def _configure_functions(self) -> None:
        pointer = ctypes.POINTER(_CREDENTIALW)
        self._advapi32.CredWriteW.argtypes = [pointer, wintypes.DWORD]
        self._advapi32.CredWriteW.restype = wintypes.BOOL
        self._advapi32.CredReadW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(pointer),
        ]
        self._advapi32.CredReadW.restype = wintypes.BOOL
        self._advapi32.CredDeleteW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        self._advapi32.CredDeleteW.restype = wintypes.BOOL
        self._advapi32.CredFree.argtypes = [ctypes.c_void_p]
        self._advapi32.CredFree.restype = None

    def write(self, target: str, value: str) -> None:
        blob = value.encode("utf-16-le")
        buffer = ctypes.create_string_buffer(blob)
        credential = _CREDENTIALW(
            Type=CRED_TYPE_GENERIC,
            TargetName=target,
            CredentialBlobSize=len(blob),
            CredentialBlob=ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)),
            Persist=CRED_PERSIST_LOCAL_MACHINE,
            UserName="Caronte",
        )
        if not self._advapi32.CredWriteW(ctypes.byref(credential), 0):
            self._raise_last_error("write")

    def read(self, target: str) -> str:
        pointer = ctypes.POINTER(_CREDENTIALW)()
        if not self._advapi32.CredReadW(
            target, CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)
        ):
            self._raise_last_error("read")
        try:
            credential = pointer.contents
            blob = ctypes.string_at(
                credential.CredentialBlob, credential.CredentialBlobSize
            )
            return blob.decode("utf-16-le")
        finally:
            self._advapi32.CredFree(pointer)

    def delete(self, target: str) -> None:
        if not self._advapi32.CredDeleteW(target, CRED_TYPE_GENERIC, 0):
            self._raise_last_error("delete")

    @staticmethod
    def _raise_last_error(operation: str) -> NoReturn:
        raise WindowsCredentialApiError(operation, ctypes.get_last_error())


class WindowsCredentialStore:
    """CredentialStore backed by Windows Credential Manager generic credentials."""

    def __init__(self, api: WindowsCredentialApi, *, target_prefix: str = "Caronte/") -> None:
        self._api = api
        self._target_prefix = target_prefix

    def save(self, reference: str, value: str) -> None:
        target = self._target(reference)
        try:
            self._api.read(target)
        except WindowsCredentialApiError as exc:
            if exc.error_code != ERROR_NOT_FOUND:
                _raise_translated(exc)
        else:
            raise CredentialAlreadyExistsError(
                f"credential reference already exists: {_validated_reference(reference)}"
            )
        try:
            self._api.write(target, _validated_value(value))
        except WindowsCredentialApiError as exc:
            _raise_translated(exc)

    def read(self, reference: str) -> str:
        try:
            return self._api.read(self._target(reference))
        except WindowsCredentialApiError as exc:
            _raise_translated(exc)

    def update(self, reference: str, value: str) -> None:
        target = self._target(reference)
        try:
            self._api.read(target)
            self._api.write(target, _validated_value(value))
        except WindowsCredentialApiError as exc:
            _raise_translated(exc)

    def delete(self, reference: str) -> None:
        try:
            self._api.delete(self._target(reference))
        except WindowsCredentialApiError as exc:
            _raise_translated(exc)

    def _target(self, reference: str) -> str:
        return self._target_prefix + _validated_reference(reference)


def create_account_credential_service(
    api: WindowsCredentialApi | None = None,
) -> AccountCredentialService:
    """Build the shared account service with the secure Windows adapter."""

    backend = api if api is not None else NativeWindowsCredentialApi()
    return AccountCredentialService(WindowsCredentialStore(backend))


def credential_error_message(error: CredentialStoreError) -> str:
    """Translate typed backend failures into safe user-facing Italian messages."""

    if isinstance(error, CredentialNotFoundError):
        return "Le credenziali della casella non sono state trovate."
    if isinstance(error, CredentialAlreadyExistsError):
        return "Le credenziali della casella esistono gia`."
    if isinstance(error, CredentialAccessDeniedError):
        return "Windows non consente l'accesso alle credenziali protette."
    if isinstance(error, CredentialBackendUnavailableError):
        return "Le credenziali protette di Windows non sono disponibili."
    return "Non e` stato possibile usare le credenziali protette."


def _raise_translated(error: WindowsCredentialApiError) -> NoReturn:
    if error.error_code == ERROR_NOT_FOUND:
        raise CredentialNotFoundError("credential reference not found") from error
    if error.error_code == ERROR_ACCESS_DENIED:
        raise CredentialAccessDeniedError("credential access denied") from error
    raise CredentialBackendError("credential backend operation failed") from error
