from fastapi import FastAPI
from .api.chat_endpoint import router as chat_router
from .database import engine
from .models import task, user, conversation, message  # Import models to register them
from sqlmodel import SQLModel


def create_app():
    app = FastAPI(title="Todo AI Chatbot", version="0.1.0")

    # Include routers
    app.include_router(chat_router, prefix="/v1", tags=["chat"])

    @app.on_event("startup")
    def on_startup():
        # Create database tables
        SQLModel.metadata.create_all(engine)

    return app


app = create_app()


@app.get("/")
def read_root():
    return {"message": "Welcome to the Todo AI Chatbot API"}