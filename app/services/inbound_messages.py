from sqlmodel import Session, select

from app.models.inbound_message import InboundMessage


def save_inbound_message(session: Session, payload: dict[str, str]) -> InboundMessage:
    message_sid = payload["MessageSid"]

    existing = session.exec(
        select(InboundMessage).where(InboundMessage.message_sid == message_sid)
    ).first()
    if existing is not None:
        return existing

    message = InboundMessage(
        message_sid=message_sid,
        account_sid=payload.get("AccountSid"),
        from_number=payload["From"],
        to_number=payload["To"],
        body=payload.get("Body", ""),
        num_media=int(payload.get("NumMedia", "0") or 0),
        raw_payload=payload,
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message
