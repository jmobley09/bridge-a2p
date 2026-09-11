import base64
import hashlib
import hmac

from app.services.twilio_security import is_valid_twilio_signature


def test_valid_twilio_signature() -> None:
    url = "https://example.ngrok.app/webhooks/twilio/inbound-sms"
    params = {"Body": "hello", "From": "+15551230000", "MessageSid": "SM123", "To": "+15559870000"}
    token = "secret"
    signed_data = url + "".join(f"{key}{value}" for key, value in sorted(params.items()))
    signature = base64.b64encode(
        hmac.new(token.encode(), signed_data.encode(), hashlib.sha1).digest()
    ).decode()

    assert is_valid_twilio_signature(
        url=url,
        params=params,
        signature=signature,
        auth_token=token,
    )


def test_signature_is_optional_without_auth_token() -> None:
    assert is_valid_twilio_signature(
        url="https://example.com",
        params={},
        signature=None,
        auth_token=None,
    )
