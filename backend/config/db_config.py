"""
Database configuration with support for both sync and async sessions.
"""

import ssl
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.env_config import settings
import logging

logger = logging.getLogger(__name__)

# Synchronous database configuration
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Asynchronous database configuration
# Convert DATABASE_URL from mysql+pymysql to mysql+aiomysql for async
async_database_url = settings.DATABASE_URL.replace("mysql+pymysql", "mysql+aiomysql")

# Create SSL context if DATABASE_SSL_CA is provided
connect_args = {}
if settings.DATABASE_SSL_VERIFY:
    if settings.DATABASE_SSL_CA:
        ssl_context = ssl.create_default_context(cafile=settings.DATABASE_SSL_CA)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        connect_args = {"ssl": ssl_context}

    async_engine = create_async_engine(
        async_database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
        connect_args=connect_args,
    )
else:
    async_engine = create_async_engine(
        async_database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )

AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


def get_db():
    """
    Get synchronous database session.

    Yields:
        Session: Synchronous database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """
    Get asynchronous database session.

    Yields:
        AsyncSession: Asynchronous database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
