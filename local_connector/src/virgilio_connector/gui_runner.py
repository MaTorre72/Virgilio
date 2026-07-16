"""Compatibility imports for the abandoned technical presentation."""

from .application.operation_runner import (
    ManagedOperationRunner as ManagedCliRunner,
    RunnerEvent,
)

__all__ = ["ManagedCliRunner", "RunnerEvent"]
