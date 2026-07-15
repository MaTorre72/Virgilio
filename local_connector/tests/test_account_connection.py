from pathlib import Path

from virgilio_connector.application.account_connection import (
    AccountConnectionRequest,
    ReadonlyAccountConnectionService,
)


def test_connection_service_uses_only_readonly_listing(tmp_path: Path):
    operations = []

    class MutationRejectingMailbox:
        def __init__(self, config, root):
            operations.append(("create", config, root))

        def list_pending(self):
            operations.append(("list_pending",))
            return (object(), object())

        def acknowledge(self, message):
            raise AssertionError("mutating operations are forbidden")

    service = ReadonlyAccountConnectionService(
        tmp_path, mailbox_factory=MutationRejectingMailbox
    )

    message = service.check(AccountConnectionRequest(
        email="account@example.invalid",
        password="synthetic-password",
        host="imap.gmail.com",
        port=993,
    ))

    assert message == "Collegamento riuscito: 2 messaggi visibili."
    assert [operation[0] for operation in operations] == ["create", "list_pending"]
    config = operations[0][1]
    assert config.username == "account@example.invalid"
    assert config.password == "synthetic-password"
    assert operations[0][2] == tmp_path
