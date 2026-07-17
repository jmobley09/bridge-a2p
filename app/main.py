from fastapi import FastAPI

from app.api.routes import health, twilio


def create_app() -> FastAPI:
    app = FastAPI(title="Bridge A2P", version="0.1.0")
    app.include_router(health.router)
    app.include_router(twilio.router)
    return app


app = create_app()
