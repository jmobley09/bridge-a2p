import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.models.sending_list_recipient import SendingListRecipient

logger = logging.getLogger(__name__)

EMPTY_TWIML = "<Response></Response>"


def is_stop_message(body: str) -> bool:
    return body.strip().casefold() == "stop"


def is_stop_opt_out(payload: dict[str, str]) -> bool:
    return payload.get("OptOutType", "").casefold() == "stop" or is_stop_message(
        payload.get("Body", "")
    )


def empty_twiml() -> str:
    return EMPTY_TWIML


def is_active_recipient(session: Session, phone_number: str) -> bool:
    normalized_phone_number = phone_number.strip()
    recipient = session.exec(
        select(SendingListRecipient).where(
            SendingListRecipient.phone_number == normalized_phone_number,
            SendingListRecipient.active.is_(True),
        )
    ).first()
    return recipient is not None


def get_active_recipients(session: Session) -> list[SendingListRecipient]:
    return list(
        session.exec(
            select(SendingListRecipient)
            .where(SendingListRecipient.active.is_(True))
            .order_by(SendingListRecipient.created_at)
        ).all()
    )


def opt_out_sender(session: Session, phone_number: str) -> bool:
    normalized_phone_number = phone_number.strip()
    try:
        recipient = session.exec(
            select(SendingListRecipient).where(
                SendingListRecipient.phone_number == normalized_phone_number
            )
        ).first()
        if recipient is None:
            return False

        recipient.active = False
        session.add(recipient)
        session.commit()
        return True
    except SQLAlchemyError as error:
        session.rollback()
        logger.warning("Unable to update SMS opt-out for %s: %s", normalized_phone_number, error)
        return False
