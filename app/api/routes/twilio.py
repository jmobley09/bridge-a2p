from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.services.admin_numbers import is_admin_number
from app.services.inbound_messages import save_inbound_message
from app.services.sending_list import (
    AddRecipientResult,
    JOIN_INSTRUCTIONS_MESSAGE,
    WELCOME_MESSAGE,
    add_recipient,
    empty_twiml,
    is_start_opt_in,
    is_stop_opt_out,
    message_twiml,
    opt_in_sender,
    opt_out_sender,
    parse_add_recipient_command,
)
from app.services.twilio_messages import send_sms
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
        auth_token=settings.twilio_auth_token if settings.twilio_validate_signature else None,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Twilio signature")

    if is_stop_opt_out(payload):
        opt_out_sender(session, payload["From"])
        return Response(content=empty_twiml(), media_type="application/xml")

    if is_start_opt_in(payload):
        if opt_in_sender(session, payload["From"]):
            return Response(content=empty_twiml(), media_type="application/xml")
        return Response(
            content=message_twiml(JOIN_INSTRUCTIONS_MESSAGE),
            media_type="application/xml",
        )

    if not is_admin_number(session, payload["From"]):
        return Response(
            content="Sender is not an admin number",
            media_type="text/plain",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    recipient_phone_number = parse_add_recipient_command(payload.get("Body", ""))
    if recipient_phone_number is not None:
        result = add_recipient(session, recipient_phone_number)
        if result == AddRecipientResult.ALREADY_ACTIVE:
            admin_message = "user already has an active account"
        elif result == AddRecipientResult.OPTED_OUT:
            admin_message = "user exists. have user reply START to re-enable."
        elif result == AddRecipientResult.ERROR:
            admin_message = f"{recipient_phone_number} could not be added. Check application logs."
        else:
            welcome_sent = send_sms(
                account_sid=settings.twilio_account_sid,
                api_key_sid=settings.twilio_api_key_sid,
                api_key_secret=settings.twilio_api_key_secret,
                from_number=payload["To"],
                to_number=recipient_phone_number,
                body=WELCOME_MESSAGE,
            )
            admin_message = (
                f"Added {recipient_phone_number} and sent the welcome message."
                if welcome_sent
                else f"Added {recipient_phone_number}, but the welcome message could not be sent."
            )

        return Response(content=message_twiml(admin_message), media_type="application/xml")

    save_inbound_message(session, payload)
    return Response(content=empty_twiml(), media_type="application/xml")
