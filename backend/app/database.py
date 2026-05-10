from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

engine_kwargs = {}
if settings.database_url.startswith("sqlite"):
    engine_kwargs.update(
        connect_args={"check_same_thread": False},
        pool_size=2,
        max_overflow=2,
        pool_timeout=30,
    )

engine = create_engine(settings.database_url, **engine_kwargs)

# Enable WAL mode and FTS5 for SQLite
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA cache_size=-2000")
        cursor.execute("PRAGMA mmap_size=0")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
