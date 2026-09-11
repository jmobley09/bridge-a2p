import base64
import hashlib
import hmac


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

    signed_data = url + "".join(f"{key}{value}" for key, value in sorted(params.items()))
    digest = hmac.new(auth_token.encode(), signed_data.encode(), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)
