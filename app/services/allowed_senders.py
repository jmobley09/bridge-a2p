from sqlmodel import Session, select

from app.models.allowed_sender import AllowedSender


def is_allowed_sender(session: Session, phone_number: str) -> bool:
    normalized_phone_number = phone_number.strip()
    allowed_sender = session.exec(
        select(AllowedSender).where(
            AllowedSender.phone_number == normalized_phone_number,
            AllowedSender.is_active.is_(True),
        )
    ).first()
    return allowed_sender is not None
