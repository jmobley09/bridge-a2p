import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TwilioCredentials:
    account_sid: str | None
    api_key_sid: str | None
    api_key_secret: str | None

    @property
    def is_complete(self) -> bool:
        return bool(self.account_sid and self.api_key_sid and self.api_key_secret)


def build_client(credentials: TwilioCredentials) -> Any | None:
    if not credentials.is_complete:
        return None

    from twilio.rest import Client

    return Client(credentials.api_key_sid, credentials.api_key_secret, credentials.account_sid)


def send_sms(
    *,
    account_sid: str | None,
    api_key_sid: str | None,
    api_key_secret: str | None,
    from_number: str,
    to_number: str,
    body: str,
    media_urls: list[str] | None = None,
    client: Any | None = None,
) -> bool:
    if client is None:
        credentials = TwilioCredentials(account_sid, api_key_sid, api_key_secret)
        if not credentials.is_complete:
            logger.warning("Unable to send SMS to %s: missing Twilio credentials", to_number)
            return False

    try:
        if client is None:
            client = build_client(credentials)
        kwargs = {"from_": from_number, "to": to_number, "body": body}
        if media_urls:
            kwargs["media_url"] = media_urls
        client.messages.create(**kwargs)
        return True
    except Exception as error:
        logger.warning("Unable to send SMS to %s: %s", to_number, error)
        return False


def send_broadcast(
    *,
    credentials: TwilioCredentials,
    from_number: str,
    recipient_numbers: list[str],
    body: str,
    media_urls: list[str] | None,
    admin_number: str,
) -> tuple[int, int]:
    """Send a broadcast to every recipient, then text the admin a summary.

    Runs outside the webhook request so a large list can't exceed Twilio's 15s
    webhook timeout or the gunicorn worker timeout and get cut off mid-loop.
    """
    if not credentials.is_complete:
        logger.warning(
            "Unable to send broadcast to %d recipient(s): missing Twilio credentials",
            len(recipient_numbers),
        )
        return 0, len(recipient_numbers)

    client = build_client(credentials)
    sent_count = 0
    failed_numbers: list[str] = []

    for to_number in recipient_numbers:
        if send_sms(
            account_sid=credentials.account_sid,
            api_key_sid=credentials.api_key_sid,
            api_key_secret=credentials.api_key_secret,
            from_number=from_number,
            to_number=to_number,
            body=body,
            media_urls=media_urls,
            client=client,
        ):
            sent_count += 1
        else:
            failed_numbers.append(to_number)

    logger.info(
        "Broadcast finished: %d sent, %d failed %s",
        sent_count,
        len(failed_numbers),
        failed_numbers,
    )

    summary = f"Broadcast sent to {sent_count} active recipient(s). {len(failed_numbers)} send(s) failed."
    if failed_numbers:
        summary = f"{summary} Failed: {', '.join(failed_numbers)}"
    send_sms(
        account_sid=credentials.account_sid,
        api_key_sid=credentials.api_key_sid,
        api_key_secret=credentials.api_key_secret,
        from_number=from_number,
        to_number=admin_number,
        body=summary,
        client=client,
    )
    return sent_count, len(failed_numbers)
