from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.core.settings import settings

# ── Engine ────────────────────────────────────────────────────────────────────
# SQLite needs check_same_thread=False for FastAPI's async workers.
# PostgreSQL ignores connect_args entirely, so this is safe for both.
connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    # Pool tuning — SQLite uses StaticPool in tests; Postgres uses QueuePool.
    # echo=True logs every SQL statement; useful during dev, noisy in prod.
    echo=settings.app_debug,
)

# Enable WAL mode for SQLite — dramatically better concurrent read performance.
if settings.is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # prevents lazy-load errors after commit
)


# ── Dependency ────────────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency. Yields a database session and guarantees
    it is closed even if the request raises an exception.

    Usage in a route:
        @router.get("/")
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
