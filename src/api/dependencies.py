"""Shared FastAPI dependencies for database access."""

from __future__ import annotations

from typing import Iterator

from sqlalchemy.orm import Session

from src.db import SessionLocal


def get_db() -> Iterator[Session]:
    """Yield a database session for dependency injection in API endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
