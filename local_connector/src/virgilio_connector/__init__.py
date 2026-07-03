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
from .orchestrator import ConnectorConfig, ConnectorOrchestrator, ProcessingResult
from .imap_readonly import (
    DetectedAttachment,
    ImapReadonlyConfig,
    ImapReadonlyError,
    ImapReadonlyMailbox,
)
from .local_paths import LocalDataPaths
from .readonly_quarantine import QuarantinePlanItem, ReadonlyQuarantineRunner
from .readonly_state import ReadonlyStateStore
from .scanner import (
    LocalScanResult,
    LocalScanner,
    ScanVerdict,
    UnconfiguredScanner,
    WindowsDefenderScanner,
    select_scanner,
)
from .caronte_dry_run import (
    CaronteDryRunConfig,
    NoReadyAttachmentsError,
    generate_caronte_dry_run_files,
)
from .caronte_http import (
    CaronteBridgeResponse,
    CaronteDryRunClientError,
    CaronteDryRunHttpClient,
    CaronteDryRunUrlNotConfigured,
)
from .classification import (AttachmentClassificationProposer,
                             ClassificationFeedback,
                             ClassificationProposal,
                             ClassificationProposalError,
                             ClassificationReview,
                             classification_feedback_human_summary,
                             classification_human_summary,
                             classification_review_human_summary,
                             record_classification_feedback,
                             review_classification_proposal)
from .staging_transport import (
    LocalDriveStagingConfig,
    LocalDriveStagingTransport,
    NoReadyFilesError,
    StagingDirectoryError,
    StagingDisabledError,
    StagingResult,
    StagingTransportError,
)
from .drive_staging_verify import (
    DriveStagingVerifyClient,
    DriveStagingVerifyError,
    DriveStagingVerifyResponse,
    DriveStagingVerifyUrlNotConfigured,
)
from .drive_staging_intake_test import (
    DriveStagingIntakeTestClient,
    DriveStagingIntakeTestError,
    DriveStagingIntakeTestResponse,
    DriveStagingIntakeTestUrlNotConfigured,
)
from .da_archiviare_intake import (
    DA_ARCHIVIARE_INTAKE_ACTION,
    DaArchiviareIntakeError,
    build_da_archiviare_intake_payload,
)
from .multi_account import (
    LocalImapAccount,
    LocalStorageConfig,
    MultiAccountAttachmentResult,
    MultiAccountConfigError,
    MultiAccountImapProcessor,
    MultiAccountReadonlyScanner,
    MultiAccountScanResult,
    load_storage_config,
    load_multi_account_config,
)
from .storage_adapter import (
    LocalFilesystemStorageAdapter,
    StorageAdapterError,
    StorageStageResult,
)
from .pipeline import LocalPipelineRunner, PipelineResult
from .doctor import DoctorResult, LocalDoctor
from .litellm_gateway import (LiteLLMBudgetError, LiteLLMGateway,
                              LiteLLMGatewayConfig, LiteLLMGatewayError,
                              LiteLLMRequest, LiteLLMResponse,
                              MockLiteLLMProvider)

__all__ = [
    "AckDecision",
    "Attachment",
    "AttachmentRecord",
    "CaronteCommand",
    "CaronteDryRunConfig",
    "CaronteBridgeResponse",
    "CaronteDryRunClientError",
    "CaronteDryRunHttpClient",
    "CaronteDryRunUrlNotConfigured",
    "CaronteResponse",
    "ClassificationProposal",
    "ClassificationProposalError",
    "ClassificationReview",
    "ClassificationFeedback",
    "CommandAttemptRecord",
    "CommandAttemptStatus",
    "ContractValidationError",
    "ConnectorConfig",
    "ConnectorOrchestrator",
    "DATABASE_SCHEMA_VERSION",
    "MessageRecord",
    "ImapReadonlyConfig",
    "DetectedAttachment",
    "ImapReadonlyError",
    "ImapReadonlyMailbox",
    "LocalDataPaths",
    "LocalDriveStagingConfig",
    "LocalDriveStagingTransport",
    "DriveStagingVerifyClient",
    "DriveStagingVerifyError",
    "DriveStagingVerifyResponse",
    "DriveStagingVerifyUrlNotConfigured",
    "DriveStagingIntakeTestClient",
    "DriveStagingIntakeTestError",
    "DriveStagingIntakeTestResponse",
    "DriveStagingIntakeTestUrlNotConfigured",
    "DA_ARCHIVIARE_INTAKE_ACTION",
    "DaArchiviareIntakeError",
    "build_da_archiviare_intake_payload",
    "AttachmentClassificationProposer",
    "LocalImapAccount",
    "LocalStorageConfig",
    "MultiAccountAttachmentResult",
    "MultiAccountConfigError",
    "MultiAccountImapProcessor",
    "MultiAccountReadonlyScanner",
    "MultiAccountScanResult",
    "load_storage_config",
    "load_multi_account_config",
    "CompletionError",
    "CompletionResult",
    "AckCompletedMessagesResult",
    "ControlledAckRunner",
    "LocalCompletionRunner",
    "LocalFilesystemStorageAdapter",
    "StorageAdapterError",
    "StorageStageResult",
    "LocalPipelineRunner",
    "PipelineResult",
    "DoctorResult",
    "LocalDoctor",
    "LiteLLMBudgetError",
    "LiteLLMGateway",
    "LiteLLMGatewayConfig",
    "LiteLLMGatewayError",
    "LiteLLMRequest",
    "LiteLLMResponse",
    "MockLiteLLMProvider",
    "LocalScanResult",
    "LocalScanner",
    "MessageStatus",
    "NewAttachment",
    "NewMessage",
    "NoReadyAttachmentsError",
    "NoReadyFilesError",
    "QuarantineStatus",
    "ProcessingResult",
    "QuarantinePlanItem",
    "ReadonlyQuarantineRunner",
    "ReadonlyStateStore",
    "ScanVerdict",
    "UnconfiguredScanner",
    "WindowsDefenderScanner",
    "select_scanner",
    "generate_caronte_dry_run_files",
    "StateConflictError",
    "StateDatabaseError",
    "StateEvent",
    "StateNotFoundError",
    "StateStore",
    "StagingDirectoryError",
    "StagingDisabledError",
    "StagingResult",
    "StagingTransportError",
    "UnsupportedSchemaError",
    "command_from_json",
    "classification_human_summary",
    "classification_feedback_human_summary",
    "classification_review_human_summary",
    "command_to_json",
    "evaluate_ack",
    "review_classification_proposal",
    "record_classification_feedback",
    "response_from_json",
    "response_to_json",
]

__version__ = "0.11.0"
from .completion import (
    AckCompletedMessagesResult,
    CompletionError,
    CompletionResult,
    ControlledAckRunner,
    LocalCompletionRunner,
)
