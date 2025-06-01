"""Database module for the web application."""
import os
from collections.abc import AsyncGenerator
from datetime import datetime
from sqlalchemy import ForeignKey, Enum, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.utilities.settings import Settings

settings = Settings()

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

class Base(DeclarativeBase):
  """Base class for all models."""

class DBPrompt(Base):
  """Prompt model."""

  __tablename__ = "prompts"
  id: Mapped[int] = mapped_column(primary_key=True)
  content: Mapped[str] = mapped_column(String(settings.max_prompt_length))
  created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
  schedules: Mapped[list["DBSchedule"]] = relationship(back_populates="prompt")

class DBSchedule(Base):
  """Schedule model."""

  __tablename__ = "schedules"
  id: Mapped[int] = mapped_column(primary_key=True)
  prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"))
  schedule_type: Mapped[str] = mapped_column(
    Enum("one_time", "recurring", name="schedule_type"),
    nullable=False,
  )
  run_at: Mapped[datetime | None]
  cron_expression: Mapped[str | None]
  created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
  prompt: Mapped[DBPrompt] = relationship(back_populates="schedules")
  executions: Mapped[list["DBScheduleExecution"]] = relationship(back_populates="schedule", order_by="desc(DBScheduleExecution.executed_at)")

class DBScheduleExecution(Base):
  """Schedule execution history model."""

  __tablename__ = "executions"
  id: Mapped[int] = mapped_column(primary_key=True)
  schedule_id: Mapped[int | None] = mapped_column(ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True)
  prompt_id: Mapped[int | None] = mapped_column(ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True)
  executed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
  status: Mapped[str] = mapped_column(Enum("pending", "success", "error", name="execution_status"))
  result: Mapped[str | None]
  error: Mapped[str | None]
  schedule: Mapped["DBSchedule | None"] = relationship(back_populates="executions")
  prompt: Mapped["DBPrompt | None"] = relationship(foreign_keys=[prompt_id])

engine = create_async_engine(
  f"postgresql+asyncpg://postgres:postgres@{settings.database_host}:{settings.database_port}/ibkr_mcp",
  echo=False,
  pool_pre_ping=True,
  pool_size=20,
  max_overflow=10,
)

async_session = async_sessionmaker(
  engine,
  class_=AsyncSession,
  expire_on_commit=False,
  autocommit=False,
  autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
  """Get a database session."""
  async with async_session() as session:
    try:
      yield session
    finally:
      await session.close()

async def init_db() -> None:
  """Initialize the database. This is used in the init_db.sh script."""
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
