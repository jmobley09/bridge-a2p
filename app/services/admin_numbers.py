from sqlmodel import Session, select

from app.models.admin_number import AdminNumber


def is_admin_number(session: Session, phone_number: str) -> bool:
    normalized_phone_number = phone_number.strip()
    admin_number = session.exec(
        select(AdminNumber).where(
            AdminNumber.phone_number == normalized_phone_number,
            AdminNumber.is_active.is_(True),
        )
    ).first()
    return admin_number is not None
