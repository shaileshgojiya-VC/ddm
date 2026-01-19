"""
Database transaction utilities.
"""

from contextlib import contextmanager
from core.db import SessionLocal


@contextmanager
def get_transaction():
    """Get database transaction context."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
