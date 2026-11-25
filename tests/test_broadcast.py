from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.main import app
from app.models.admin_number import AdminNumber
from app.models.sending_list_recipient import SendingListRecipient
from app.services import twilio_messages
from app.services.twilio_messages import TwilioCredentials, send_broadcast

ADMIN = "+15550000001"
TWILIO_NUMBER = "+15559999999"
CREDENTIALS = TwilioCredentials("AC123", "SK123", "secret")


class FakeMessages:
    def __init__(self, fail_for: set[str] | None = None) -> None:
        self.sent: list[dict] = []
        self.fail_for = fail_for or set()

    def create(self, **kwargs):
        if kwargs["to"] in self.fail_for:
            raise RuntimeError("twilio error")
        self.sent.append(kwargs)
        return SimpleNamespace(sid="SM123")


@pytest.fixture
def fake_twilio(monkeypatch: pytest.MonkeyPatch) -> FakeMessages:
    messages = FakeMessages()
    clients_built: list[object] = []

    def build_client(credentials: TwilioCredentials) -> SimpleNamespace:
        client = SimpleNamespace(messages=messages)
        clients_built.append(client)
        return client

    monkeypatch.setattr(twilio_messages, "build_client", build_client)
    messages.clients_built = clients_built  # type: ignore[attr-defined]
    return messages


def test_send_broadcast_reuses_one_client_and_texts_admin_summary(fake_twilio: FakeMessages) -> None:
    fake_twilio.fail_for = {"+15550000003"}
    recipients = ["+15550000002", "+15550000003", "+15550000004"]

    sent, failed = send_broadcast(
        credentials=CREDENTIALS,
        from_number=TWILIO_NUMBER,
        recipient_numbers=recipients,
        body="hello",
        media_urls=None,
        admin_number=ADMIN,
    )

    assert (sent, failed) == (2, 1)
    assert len(fake_twilio.clients_built) == 1  # type: ignore[attr-defined]
    assert [m["to"] for m in fake_twilio.sent] == ["+15550000002", "+15550000004", ADMIN]
    assert "2 active recipient(s). 1 send(s) failed" in fake_twilio.sent[-1]["body"]
    assert "+15550000003" in fake_twilio.sent[-1]["body"]


def test_broadcast_webhook_replies_immediately_and_sends_to_every_recipient(
    fake_twilio: FakeMessages,
) -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(
        engine, tables=[AdminNumber.__table__, SendingListRecipient.__table__]
    )
    recipients = [f"+1555000{i:04d}" for i in range(10, 60)]
    with Session(engine) as session:
        session.add(AdminNumber(phone_number=ADMIN))
        for number in recipients:
            session.add(SendingListRecipient(phone_number=number, active=True))
        session.add(SendingListRecipient(phone_number="+15551111111", active=False))
        session.commit()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = lambda: Settings(
        twilio_account_sid="AC123",
        twilio_api_key_sid="SK123",
        twilio_api_key_secret="secret",
        twilio_validate_signature=False,
    )
    try:
        response = TestClient(app).post(
            "/webhooks/twilio/inbound-sms",
            data={
                "MessageSid": "SM1",
                "From": ADMIN,
                "To": TWILIO_NUMBER,
                "Body": "broadcast: Co-op is cancelled today",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "Sending broadcast to 50 active recipient(s)" in response.text
    delivered = [m["to"] for m in fake_twilio.sent]
    assert delivered[:-1] == recipients
    assert delivered[-1] == ADMIN
    assert fake_twilio.sent[0]["from_"] == TWILIO_NUMBER
    assert fake_twilio.sent[0]["body"].startswith("Co-op is cancelled today")
