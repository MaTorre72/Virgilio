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


def test_connection_check_uses_standard_inbox_not_operational_default(tmp_path: Path):
    selected_mailboxes = []

    class InboxOnlyMailbox:
        def __init__(self, config, _root):
            selected_mailboxes.append(config.mailbox)
            if config.mailbox != "INBOX":
                raise RuntimeError("operational mailbox is absent")

        def list_pending(self):
            return ()

    service = ReadonlyAccountConnectionService(
        tmp_path, mailbox_factory=InboxOnlyMailbox
    )

    message = service.check(AccountConnectionRequest(
        email="account@example.invalid",
        password="synthetic-password",
        host="imap.gmail.com",
        port=993,
        auth_mode="oauth2",
    ))

    assert message == "Collegamento riuscito: 0 messaggi visibili."
    assert selected_mailboxes == ["INBOX"]
