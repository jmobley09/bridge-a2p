# bridge-a2p

SMS application for Bridge Co-op.

## Stack

- FastAPI for the HTTP app
- SQLModel for database models and sessions
- Postgres for persistence
- Alembic for versioned database migrations

## Local setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Start Postgres:

```bash
docker compose up -d postgres
```

Create your local environment file:

```bash
cp .env.example .env
```

Apply database migrations:

```bash
alembic upgrade head
```

Add a test phone number to the admin numbers table:

```bash
docker compose exec postgres psql -U bridge -d bridge_a2p \
  -c "insert into admin_numbers (id, phone_number, label) values (gen_random_uuid(), '+15551230000', 'Local test admin');"
```

To send welcome messages when an admin adds a recipient, configure Twilio REST credentials:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_KEY_SID=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_KEY_SECRET=your_twilio_api_key_secret
```

Run the API:

```bash
fastapi dev app/main.py
```

The health check is available at:

```text
GET http://localhost:8000/health
```

## Twilio inbound SMS webhook

The inbound SMS webhook is:

```text
POST /webhooks/twilio/inbound-sms
```

Twilio sends inbound SMS webhooks as form-encoded fields. The app currently stores:

- `MessageSid`
- `AccountSid`
- `From`
- `To`
- `Body`
- `NumMedia`
- the full raw Twilio payload

Only senders listed in `admin_numbers` are stored. Unknown senders receive an HTTP `403`
response with `Sender is not an admin number`, which keeps them out of the local database while making
the rejection visible in Twilio's webhook request logs.

Opt-out messages are processed before the admin-number check. If Twilio sends `OptOutType=STOP`,
or if any sender texts only the word `stop` matched case-insensitively, the app looks up their
number in `sending_list_recipients`, sets `active` to `false` when present, returns empty TwiML,
and does not store an inbound message. Twilio should own the user-facing opt-out confirmation
message through its Messaging Service opt-out settings.

Opt-in messages are also processed before the admin-number check. If Twilio sends `OptOutType=START`,
or if any sender texts only the word `start` matched case-insensitively, the app looks up their
number in `sending_list_recipients` and sets `active` to `true` when present. If the sender is not
already in the sending list, the app responds with:

```text
Please see a BRIDGE board member for joining this service
```

Outbound sending should only use recipients where `sending_list_recipients.active = true`.
The sending list service exposes helpers for checking a single number and loading active
recipients so the app avoids sending to locally opted-out numbers before Twilio rejects them.

Admins can add a new sending-list recipient by texting:

```text
Add: +15551230000
```

US numbers may also be sent without a country code, for example `Add: 5551230000`.
The app normalizes them to E.164 format with a `+1` prefix before storing or sending.

The sender must be listed in `admin_numbers`. When a new active recipient is added, the app replies
to that admin with a confirmation and sends this welcome message to the recipient:

```text
You have been added to the BRIDGE SMS service. Reply STOP to opt out.
```

If the number is already active, the admin receives `user already has an active account`. If the
number exists but is inactive, the app does not reactivate it or send a welcome message, and the
admin receives `user exists. please try again with 'activate: <phone number>' to reactivate.`

Admins can broadcast a message to every active sending-list recipient by texting:

```text
broadcast: Your message here
```

Everything after `broadcast:` is sent as the message body, preserving line breaks, emoji, and
attached media. The app appends this footer automatically:

```text
Regards,
BRIDGE Homeschool Community

Reply STOP to opt out.
```

For local Twilio testing, expose the local API with a tunnel such as ngrok and configure your
Twilio phone number's messaging webhook to:

```text
https://your-public-url.example/webhooks/twilio/inbound-sms
```

Set `PUBLIC_WEBHOOK_BASE_URL` in `.env` to the same public base URL Twilio uses, for example:

```env
PUBLIC_WEBHOOK_BASE_URL=https://your-public-url.example
```

For local testing, keep webhook signature validation disabled while still using Twilio credentials
for outbound messages:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_VALIDATE_SIGNATURE=false
```

In production, set `TWILIO_VALIDATE_SIGNATURE=true`. When enabled, requests must include a valid
`X-Twilio-Signature` header and `PUBLIC_WEBHOOK_BASE_URL` must exactly match the public URL Twilio
uses to call the webhook.

## Migrations

Schema changes live in `migrations/versions`.

Create a future migration with:

```bash
alembic revision --autogenerate -m "describe change"
```

Apply migrations with:

```bash
alembic upgrade head
```
