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

Add a test phone number to the inbound allowlist:

```bash
docker compose exec postgres psql -U bridge -d bridge_a2p \
  -c "insert into allowed_senders (id, phone_number, label) values (gen_random_uuid(), '+15551230000', 'Local test sender');"
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

Only senders listed in `allowed_senders` are stored. Unknown senders receive an HTTP `403`
response with `Sender is not allowed`, which keeps them out of the local database while making
the rejection visible in Twilio's webhook request logs.

For local Twilio testing, expose the local API with a tunnel such as ngrok and configure your
Twilio phone number's messaging webhook to:

```text
https://your-public-url.example/webhooks/twilio/inbound-sms
```

Set `PUBLIC_WEBHOOK_BASE_URL` in `.env` to the same public base URL Twilio uses, for example:

```env
PUBLIC_WEBHOOK_BASE_URL=https://your-public-url.example
```

If `TWILIO_AUTH_TOKEN` is set, requests must include a valid `X-Twilio-Signature` header.
Leaving it blank is convenient for early local testing but should not be used in production.

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
