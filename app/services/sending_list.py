import logging
import re
from enum import StrEnum
from html import escape

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.models.sending_list_recipient import SendingListRecipient

logger = logging.getLogger(__name__)

EMPTY_TWIML = "<Response></Response>"
ADD_RECIPIENT_PATTERN = re.compile(r"^\s*Add:\s*(?P<phone_number>.+?)\s*$", re.IGNORECASE)
PHONE_ALLOWED_CHARS_PATTERN = re.compile(r"^[\d\s().+-]+$")
PHONE_DIGITS_PATTERN = re.compile(r"\D+")
WELCOME_MESSAGE = "You have been added to the BRIDGE SMS service. Reply STOP to opt out."


class AddRecipientResult(StrEnum):
    ADDED = "added"
    ALREADY_ACTIVE = "already_active"
    OPTED_OUT = "opted_out"
    ERROR = "error"


def message_twiml(message: str) -> str:
    return f"<Response><Message>{escape(message)}</Message></Response>"


def is_stop_message(body: str) -> bool:
    return body.strip().casefold() == "stop"


def is_stop_opt_out(payload: dict[str, str]) -> bool:
    return payload.get("OptOutType", "").casefold() == "stop" or is_stop_message(
        payload.get("Body", "")
    )


def empty_twiml() -> str:
    return EMPTY_TWIML


def normalize_us_phone_number(phone_number: str) -> str | None:
    if PHONE_ALLOWED_CHARS_PATTERN.fullmatch(phone_number.strip()) is None:
        return None

    digits = PHONE_DIGITS_PATTERN.sub("", phone_number)
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return None


def parse_add_recipient_command(body: str) -> str | None:
    match = ADD_RECIPIENT_PATTERN.match(body)
    if match is None:
        return None
    return normalize_us_phone_number(match.group("phone_number"))


def is_add_recipient_command(body: str) -> bool:
    return parse_add_recipient_command(body) is not None


def add_recipient(session: Session, phone_number: str) -> AddRecipientResult:
    try:
        recipient = session.exec(
            select(SendingListRecipient).where(SendingListRecipient.phone_number == phone_number)
        ).first()
        if recipient is not None:
            if recipient.active:
                return AddRecipientResult.ALREADY_ACTIVE
            return AddRecipientResult.OPTED_OUT

        recipient = SendingListRecipient(phone_number=phone_number, active=True)
        session.add(recipient)
        session.commit()
        return AddRecipientResult.ADDED
    except SQLAlchemyError as error:
        session.rollback()
        logger.warning("Unable to add SMS recipient %s: %s", phone_number, error)
        return AddRecipientResult.ERROR


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
