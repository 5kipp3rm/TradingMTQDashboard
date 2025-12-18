"""
Bot State Management Models

Tracks the state and configuration of the trading bot orchestrator.
Enables API-based start/stop/pause control and status monitoring.
"""
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import String, Integer, DateTime, Boolean, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base


class BotStatus(enum.Enum):
    """Bot operational status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class BotState(Base):
    """
    Bot State Tracking

    Stores the current state of the trading bot orchestrator.
    Only one active bot instance should exist at a time.
    """
    __tablename__ = 'bot_state'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Bot Status
    status: Mapped[BotStatus] = mapped_column(
        SQLEnum(BotStatus),
        default=BotStatus.STOPPED,
        nullable=False,
        index=True
    )

    # State Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Bot Configuration
    config_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_aggressive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Feature Flags
    ml_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    llm_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Runtime Configuration (JSON)
    active_currencies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    config_overrides: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Statistics
    total_cycles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_cycles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_cycles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error Tracking
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Process Information
    process_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thread_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def to_dict(self) -> dict:
        """Convert bot state to dictionary"""
        return {
            'id': self.id,
            'status': self.status.value if isinstance(self.status, enum.Enum) else self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'stopped_at': self.stopped_at.isoformat() if self.stopped_at else None,
            'paused_at': self.paused_at.isoformat() if self.paused_at else None,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'config_file': self.config_file,
            'is_aggressive': self.is_aggressive,
            'is_demo': self.is_demo,
            'ml_enabled': self.ml_enabled,
            'llm_enabled': self.llm_enabled,
            'active_currencies': self.active_currencies,
            'config_overrides': self.config_overrides,
            'total_cycles': self.total_cycles,
            'successful_cycles': self.successful_cycles,
            'failed_cycles': self.failed_cycles,
            'last_error': self.last_error,
            'last_error_at': self.last_error_at.isoformat() if self.last_error_at else None,
            'error_count': self.error_count,
            'process_id': self.process_id,
            'thread_id': self.thread_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<BotState(id={self.id}, status={self.status.value}, started_at={self.started_at})>"
