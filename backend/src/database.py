from sqlmodel import create_engine, Session
from typing import Generator
import os

# Get database URL from environment, with a default for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todo_chatbot.db")

# Create the engine
engine = create_engine(DATABASE_URL, echo=True)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session