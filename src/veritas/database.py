"""Database models and utilities for Veritas."""

from datetime import datetime
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    DateTime,
    JSON,
    ForeignKey,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.pool import NullPool

from veritas.config import settings

Base = declarative_base()


class AgentModel(Base):
    """Database model for persistent agent storage."""

    __tablename__ = "agents"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    network = Column(String(50), default="base-sepolia")
    brain_provider = Column(String(50), default="minimax")
    address = Column(String(42), nullable=False)
    private_key = Column(Text, nullable=False)
    status = Column(String(50), default="active")
    capabilities = Column(JSON, default=list)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = relationship("SessionModel", back_populates="agent", cascade="all, delete-orphan")


class SessionModel(Base):
    """Database model for agent session persistence."""

    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    objective = Column(Text, nullable=False)
    status = Column(String(50), default="running")
    current_step = Column(Integer, default=0)
    max_steps = Column(Integer, default=20)
    session_root = Column(String(66), nullable=True)
    attestation_tx = Column(String(66), nullable=True)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("AgentModel", back_populates="sessions")
    logs = relationship("LogModel", back_populates="session", cascade="all, delete-orphan")


class LogModel(Base):
    """Database model for action logs with Merkle chaining."""

    __tablename__ = "logs"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    basis_id = Column(String(36), nullable=True)
    event_type = Column(String(50), nullable=False)
    tool_name = Column(String(100), nullable=True)
    input_params = Column(JSON, default=dict)
    output_result = Column(Text, nullable=True)
    timestamp = Column(Float, nullable=False)
    merkle_leaf = Column(String(66), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionModel", back_populates="logs")


# Database engine configuration
DATABASE_URL = (
    settings.DATABASE_URL
    if hasattr(settings, "DATABASE_URL")
    else "sqlite+aiosqlite:///./veritas.db"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG if hasattr(settings, "DEBUG") else False,
    poolclass=NullPool if "sqlite" in DATABASE_URL else None,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await engine.dispose()
