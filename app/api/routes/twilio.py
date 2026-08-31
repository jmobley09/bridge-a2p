from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.services.allowed_senders import is_allowed_sender
from app.services.inbound_messages import save_inbound_message
from app.services.twilio_security import is_valid_twilio_signature

router = APIRouter(prefix="/webhooks/twilio", tags=["twilio"])


@router.post("/inbound-sms")
async def receive_inbound_sms(
    request: Request,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    form = await request.form()
    payload = {key: str(value) for key, value in form.items()}

    missing_fields = {"MessageSid", "From", "To"} - payload.keys()
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required Twilio field(s): {', '.join(sorted(missing_fields))}",
        )

    public_url = (
        f"{settings.public_webhook_base_url.rstrip('/')}{request.url.path}"
        if settings.public_webhook_base_url
        else str(request.url)
    )
    if not is_valid_twilio_signature(
        url=public_url,
        params=payload,
        signature=request.headers.get("X-Twilio-Signature"),
        auth_token=settings.twilio_auth_token,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Twilio signature")

    if not is_allowed_sender(session, payload["From"]):
        return Response(
            content="Sender is not allowed",
            media_type="text/plain",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    save_inbound_message(session, payload)
    return Response(content="<Response></Response>", media_type="application/xml")
