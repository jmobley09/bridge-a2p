from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.models.sending_list_recipient import SendingListRecipient
from app.services.sending_list import (
    AddRecipientResult,
    EMPTY_TWIML,
    add_recipient,
    empty_twiml,
    get_active_recipients,
    is_active_recipient,
    is_start_message,
    is_start_opt_in,
    is_stop_message,
    is_stop_opt_out,
    message_twiml,
    normalize_us_phone_number,
    opt_in_sender,
    opt_out_sender,
    parse_add_recipient_command,
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


def test_start_messages_are_opt_in_commands() -> None:
    assert is_start_message("START")
    assert is_start_message("start")
    assert is_start_message("Start")
    assert is_start_message("sTaRt")
    assert is_start_message(" START ")


def test_non_start_messages_are_not_opt_in_commands() -> None:
    assert not is_start_message("hello")
    assert not is_start_message("start please")
    assert not is_start_message("")


def test_twilio_opt_out_type_is_an_opt_out_command() -> None:
    assert is_stop_opt_out({"OptOutType": "STOP", "Body": "anything"})
    assert is_stop_opt_out({"OptOutType": "stop", "Body": "anything"})


def test_body_stop_is_an_opt_out_command_without_twilio_opt_out_type() -> None:
    assert is_stop_opt_out({"Body": "Stop"})


def test_twilio_opt_out_type_start_is_an_opt_in_command() -> None:
    assert is_start_opt_in({"OptOutType": "START", "Body": "anything"})
    assert is_start_opt_in({"OptOutType": "start", "Body": "anything"})


def test_body_start_is_an_opt_in_command_without_twilio_opt_out_type() -> None:
    assert is_start_opt_in({"Body": "Start"})


def test_empty_twiml_does_not_send_a_duplicate_confirmation() -> None:
    assert empty_twiml() == EMPTY_TWIML
    assert "<Message>" not in empty_twiml()


def test_message_twiml_escapes_content() -> None:
    assert message_twiml("Added +15551230000 & sent welcome") == (
        "<Response><Message>Added +15551230000 &amp; sent welcome</Message></Response>"
    )


def test_parse_add_recipient_command() -> None:
    assert parse_add_recipient_command("Add: +15551230000") == "+15551230000"
    assert parse_add_recipient_command("Add: 15551230000") == "+15551230000"
    assert parse_add_recipient_command("Add: 5551230000") == "+15551230000"
    assert parse_add_recipient_command("Add: (555) 123-0000") == "+15551230000"
    assert parse_add_recipient_command(" add: +15551230000 ") == "+15551230000"


def test_parse_add_recipient_command_rejects_invalid_body() -> None:
    assert parse_add_recipient_command("Add:+15551230000") == "+15551230000"
    assert parse_add_recipient_command("Add: +15551230000 now") is None
    assert parse_add_recipient_command("hello") is None


def test_normalize_us_phone_number() -> None:
    assert normalize_us_phone_number("+15551230000") == "+15551230000"
    assert normalize_us_phone_number("15551230000") == "+15551230000"
    assert normalize_us_phone_number("5551230000") == "+15551230000"
    assert normalize_us_phone_number("(555) 123-0000") == "+15551230000"


def test_normalize_us_phone_number_rejects_invalid_values() -> None:
    assert normalize_us_phone_number("+25551230000") is None
    assert normalize_us_phone_number("555123000") is None
    assert normalize_us_phone_number("55512300000") is None
    assert normalize_us_phone_number("not a number") is None


def test_opt_out_sender_rolls_back_and_returns_false_on_database_error() -> None:
    session = FailingSession()

    assert not opt_out_sender(session, "+15551230000")  # type: ignore[arg-type]
    assert session.rollback_called


def test_opt_in_sender_reactivates_existing_recipient() -> None:
    with build_test_session() as session:
        session.add(SendingListRecipient(phone_number="+15551230000", active=False))
        session.commit()

        assert opt_in_sender(session, "+15551230000")
        assert is_active_recipient(session, "+15551230000")


def test_opt_in_sender_returns_false_for_missing_recipient() -> None:
    with build_test_session() as session:
        assert not opt_in_sender(session, "+15551230000")


def test_opt_in_sender_rolls_back_and_returns_false_on_database_error() -> None:
    session = FailingSession()

    assert not opt_in_sender(session, "+15551230000")  # type: ignore[arg-type]
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


def test_add_recipient_creates_active_recipient() -> None:
    with build_test_session() as session:
        result = add_recipient(session, "+15551230000")

        assert result == AddRecipientResult.ADDED
        assert is_active_recipient(session, "+15551230000")


def test_add_recipient_does_not_duplicate_active_recipient() -> None:
    with build_test_session() as session:
        session.add(SendingListRecipient(phone_number="+15551230000", active=True))
        session.commit()

        result = add_recipient(session, "+15551230000")

        assert result == AddRecipientResult.ALREADY_ACTIVE


def test_add_recipient_does_not_reactivate_opted_out_recipient() -> None:
    with build_test_session() as session:
        session.add(SendingListRecipient(phone_number="+15551230000", active=False))
        session.commit()

        result = add_recipient(session, "+15551230000")

        assert result == AddRecipientResult.OPTED_OUT
        assert not is_active_recipient(session, "+15551230000")


def test_add_recipient_rolls_back_and_returns_error_on_database_error() -> None:
    session = FailingSession()

    assert add_recipient(session, "+15551230000") == AddRecipientResult.ERROR  # type: ignore[arg-type]
    assert session.rollback_called
