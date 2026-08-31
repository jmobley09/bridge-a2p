import logging

logger = logging.getLogger(__name__)


def send_sms(
    *,
    account_sid: str | None,
    api_key_sid: str | None,
    api_key_secret: str | None,
    from_number: str,
    to_number: str,
    body: str,
) -> bool:
    if not account_sid or not api_key_sid or not api_key_secret:
        logger.warning("Unable to send SMS to %s: missing Twilio credentials", to_number)
        return False

    try:
        from twilio.rest import Client

        client = Client(api_key_sid, api_key_secret, account_sid)
        client.messages.create(from_=from_number, to=to_number, body=body)
        return True
    except Exception as error:
        logger.warning("Unable to send SMS to %s: %s", to_number, error)
        return False
