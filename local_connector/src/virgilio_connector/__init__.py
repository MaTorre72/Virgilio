"""Local connector domain and persistence skeleton for Virgilio.

The package performs no network access, mailbox access, file download, or
antivirus invocation. Concrete adapters are intentionally absent.
"""

from .ack import AckDecision, evaluate_ack
from .contract import (
    command_from_json,
    command_to_json,
    response_from_json,
    response_to_json,
)
from .models import (
    Attachment,
    CaronteCommand,
    CaronteResponse,
    ContractValidationError,
    QuarantineStatus,
)
from .state_db import (
    DATABASE_SCHEMA_VERSION,
    StateConflictError,
    StateDatabaseError,
    StateNotFoundError,
    StateStore,
    UnsupportedSchemaError,
)
from .state_models import (
    AttachmentRecord,
    CommandAttemptRecord,
    CommandAttemptStatus,
    MessageRecord,
    MessageStatus,
    NewAttachment,
    NewMessage,
    StateEvent,
)

__all__ = [
    "AckDecision",
    "Attachment",
    "AttachmentRecord",
    "CaronteCommand",
    "CaronteResponse",
    "CommandAttemptRecord",
    "CommandAttemptStatus",
    "ContractValidationError",
    "DATABASE_SCHEMA_VERSION",
    "MessageRecord",
    "MessageStatus",
    "NewAttachment",
    "NewMessage",
    "QuarantineStatus",
    "StateConflictError",
    "StateDatabaseError",
    "StateEvent",
    "StateNotFoundError",
    "StateStore",
    "UnsupportedSchemaError",
    "command_from_json",
    "command_to_json",
    "evaluate_ack",
    "response_from_json",
    "response_to_json",
]

__version__ = "0.2.0"
