"""Credential persistence contracts independent from system backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..multi_account import LocalImapAccount


class CredentialStoreError(ValueError):
    """Base error for credential persistence operations."""


class CredentialNotFoundError(CredentialStoreError):
    """Raised when a credential reference is unknown."""


class CredentialAlreadyExistsError(CredentialStoreError):
    """Raised when saving an existing credential reference."""


class CredentialStore(Protocol):
    """Persistence port for secrets addressed only by structural references."""

    def save(self, reference: str, value: str) -> None: ...

    def read(self, reference: str) -> str: ...

    def update(self, reference: str, value: str) -> None: ...

    def delete(self, reference: str) -> None: ...


class FakeCredentialStore:
    """In-memory credential adapter for application services and synthetic tests."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def save(self, reference: str, value: str) -> None:
        reference = _validated_reference(reference)
        if reference in self._values:
            raise CredentialAlreadyExistsError(
                f"credential reference already exists: {reference}"
            )
        self._values[reference] = _validated_value(value)

    def read(self, reference: str) -> str:
        reference = _validated_reference(reference)
        try:
            return self._values[reference]
        except KeyError as exc:
            raise CredentialNotFoundError(
                f"credential reference not found: {reference}"
            ) from exc

    def update(self, reference: str, value: str) -> None:
        reference = _validated_reference(reference)
        if reference not in self._values:
            raise CredentialNotFoundError(
                f"credential reference not found: {reference}"
            )
        self._values[reference] = _validated_value(value)

    def delete(self, reference: str) -> None:
        reference = _validated_reference(reference)
        if reference not in self._values:
            raise CredentialNotFoundError(
                f"credential reference not found: {reference}"
            )
        del self._values[reference]


@dataclass(frozen=True, slots=True)
class AccountCredentials:
    """Credential values returned only to an authorized application use case."""

    username: str = field(repr=False)
    password: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class _CredentialState:
    exists: bool
    value: str = field(default="", repr=False)


@dataclass(frozen=True, slots=True)
class _AccountCredentialState:
    username: _CredentialState
    password: _CredentialState


class AccountCredentialService:
    """Coordinates account credential references without changing configuration."""

    def __init__(self, store: CredentialStore) -> None:
        self.store = store

    def save(self, account: LocalImapAccount, credentials: AccountCredentials) -> None:
        self.store.save(account.username_env, credentials.username)
        try:
            self.store.save(account.password_env, credentials.password)
        except Exception:
            self.store.delete(account.username_env)
            raise

    def replace_or_save(
        self, account: LocalImapAccount, credentials: AccountCredentials
    ) -> _AccountCredentialState:
        """Replace orphaned references and return a rollback-safe snapshot."""

        previous = _AccountCredentialState(
            username=self._state(account.username_env),
            password=self._state(account.password_env),
        )
        try:
            self._put(account.username_env, credentials.username, previous.username)
            self._put(account.password_env, credentials.password, previous.password)
        except Exception:
            self.restore(account, previous)
            raise
        return previous

    def restore(
        self, account: LocalImapAccount, state: _AccountCredentialState
    ) -> None:
        """Restore references captured by replace_or_save after a later failure."""

        self._restore_one(account.username_env, state.username)
        self._restore_one(account.password_env, state.password)

    def read(self, account: LocalImapAccount) -> AccountCredentials:
        return AccountCredentials(
            username=self.store.read(account.username_env),
            password=self.store.read(account.password_env),
        )

    def update(self, account: LocalImapAccount, credentials: AccountCredentials) -> None:
        self.store.update(account.username_env, credentials.username)
        self.store.update(account.password_env, credentials.password)

    def delete(self, account: LocalImapAccount) -> None:
        self.store.delete(account.username_env)
        self.store.delete(account.password_env)

    def _state(self, reference: str) -> _CredentialState:
        try:
            return _CredentialState(True, self.store.read(reference))
        except CredentialNotFoundError:
            return _CredentialState(False)

    def _put(
        self, reference: str, value: str, previous: _CredentialState
    ) -> None:
        if previous.exists:
            self.store.update(reference, value)
        else:
            self.store.save(reference, value)

    def _restore_one(self, reference: str, state: _CredentialState) -> None:
        if state.exists:
            try:
                self.store.update(reference, state.value)
            except CredentialNotFoundError:
                self.store.save(reference, state.value)
            return
        try:
            self.store.delete(reference)
        except CredentialNotFoundError:
            pass


def _validated_reference(reference: str) -> str:
    if not reference or not reference.strip():
        raise CredentialStoreError("credential reference is required")
    return reference.strip()


def _validated_value(value: str) -> str:
    if not value:
        raise CredentialStoreError("credential value is required")
    return value
