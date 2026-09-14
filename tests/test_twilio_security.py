from app.services.twilio_security import is_valid_twilio_signature
from twilio.request_validator import RequestValidator


def test_valid_twilio_signature() -> None:
    url = "https://example.ngrok.app/webhooks/twilio/inbound-sms"
    params = {"Body": "hello", "From": "+15551230000", "MessageSid": "SM123", "To": "+15559870000"}
    token = "secret"
    signature = RequestValidator(token).compute_signature(url, params)

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
