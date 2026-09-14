from twilio.request_validator import RequestValidator


def is_valid_twilio_signature(
    *,
    url: str,
    params: dict[str, str],
    signature: str | None,
    auth_token: str | None,
) -> bool:
    if not auth_token:
        return True
    if not signature:
        return False

    validator = RequestValidator(auth_token)
    return validator.validate(url, params, signature)
