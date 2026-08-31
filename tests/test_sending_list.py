from sqlalchemy.exc import SQLAlchemyError

from app.services.sending_list import (
    OPT_OUT_CONFIRMATION,
    is_stop_message,
    opt_out_confirmation_twiml,
    opt_out_sender,
)


class FailingSession:
    def __init__(self) -> None:
        self.rollback_called = False

    def exec(self, statement):  # noqa: ANN001
        raise SQLAlchemyError("missing active column")

    def rollback(self) -> None:
        self.rollback_called = True


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


def test_opt_out_confirmation_twiml_sends_message() -> None:
    assert opt_out_confirmation_twiml() == (
        f"<Response><Message>{OPT_OUT_CONFIRMATION}</Message></Response>"
    )


def test_opt_out_sender_rolls_back_and_returns_false_on_database_error() -> None:
    session = FailingSession()

    assert not opt_out_sender(session, "+15551230000")  # type: ignore[arg-type]
    assert session.rollback_called
