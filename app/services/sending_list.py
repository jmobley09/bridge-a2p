import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.models.sending_list_recipient import SendingListRecipient

logger = logging.getLogger(__name__)

OPT_OUT_CONFIRMATION = "You have been removed from the BRIDGE SMS service. You will not recieve further notifications from this service."


def is_stop_message(body: str) -> bool:
    return body.strip().casefold() == "stop"


def opt_out_confirmation_twiml() -> str:
    return f"<Response><Message>{OPT_OUT_CONFIRMATION}</Message></Response>"


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
