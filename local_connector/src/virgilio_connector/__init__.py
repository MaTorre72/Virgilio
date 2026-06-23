"""Local connector domain skeleton for Virgilio.

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

__all__ = [
    "AckDecision",
    "Attachment",
    "CaronteCommand",
    "CaronteResponse",
    "ContractValidationError",
    "QuarantineStatus",
    "command_from_json",
    "command_to_json",
    "evaluate_ack",
    "response_from_json",
    "response_to_json",
]

__version__ = "0.1.0"
