from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.models.sending_list_recipient import SendingListRecipient
from app.services.sending_list import (
    EMPTY_TWIML,
    empty_twiml,
    get_active_recipients,
    is_active_recipient,
    is_stop_message,
    is_stop_opt_out,
    opt_out_sender,
)


class FailingSession:
    def __init__(self) -> None:
        self.rollback_called = False

    def exec(self, statement):  # noqa: ANN001
        raise SQLAlchemyError("missing active column")

    def rollback(self) -> None:
        self.rollback_called = True


def build_test_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine, tables=[SendingListRecipient.__table__])
    return Session(engine)


def test_stop_messages_are_opt_out_commands() -> None:
    assert is_stop_message("STOP")
    assert is_stop_message("stop")
    assert is_stop_message("Stop")
    assert is_stop_message("sToP")
    assert is_stop_message(" STOP ")


def test_non_stop_messages_are_not_opt_out_commands() -> None:
    assert not is_stop_message("hello")
    assert not is_stop_message("stop please")
    assert not is_stop_message("")


def test_twilio_opt_out_type_is_an_opt_out_command() -> None:
    assert is_stop_opt_out({"OptOutType": "STOP", "Body": "anything"})
    assert is_stop_opt_out({"OptOutType": "stop", "Body": "anything"})


def test_body_stop_is_an_opt_out_command_without_twilio_opt_out_type() -> None:
    assert is_stop_opt_out({"Body": "Stop"})


def test_empty_twiml_does_not_send_a_duplicate_confirmation() -> None:
    assert empty_twiml() == EMPTY_TWIML
    assert "<Message>" not in empty_twiml()


def test_opt_out_sender_rolls_back_and_returns_false_on_database_error() -> None:
    session = FailingSession()

    assert not opt_out_sender(session, "+15551230000")  # type: ignore[arg-type]
    assert session.rollback_called


def test_is_active_recipient_only_allows_active_numbers() -> None:
    with build_test_session() as session:
        session.add(SendingListRecipient(phone_number="+15551230000", active=True))
        session.add(SendingListRecipient(phone_number="+15551230001", active=False))
        session.commit()

        assert is_active_recipient(session, "+15551230000")
        assert not is_active_recipient(session, "+15551230001")
        assert not is_active_recipient(session, "+15551230002")


def test_get_active_recipients_excludes_inactive_numbers() -> None:
    with build_test_session() as session:
        session.add(SendingListRecipient(phone_number="+15551230000", active=True))
        session.add(SendingListRecipient(phone_number="+15551230001", active=False))
        session.commit()

        recipients = get_active_recipients(session)

        assert [recipient.phone_number for recipient in recipients] == ["+15551230000"]
