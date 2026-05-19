"""
Utility to create all tables directly (useful for tests and local dev).
For production, always use: alembic upgrade head
"""
from app.db.session import engine
from app.db.base import Base
import app.models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("All tables created.")


if __name__ == "__main__":
    init_db()
