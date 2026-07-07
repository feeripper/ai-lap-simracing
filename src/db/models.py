"""SQLAlchemy models for the AI Lap Simracing database."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""


class Simulator(Base):
    """Simulator model (e.g., iRacing, Assetto Corsa)."""

    __tablename__ = "simulators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    reference_laps: Mapped[list["ReferenceLap"]] = relationship(
        "ReferenceLap", back_populates="simulator"
    )

    def __repr__(self) -> str:
        return f"<Simulator(id={self.id}, name='{self.name}')>"


class Car(Base):
    """Car model (e.g., Toyota GR86, Porsche 911 GT3)."""

    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    reference_laps: Mapped[list["ReferenceLap"]] = relationship("ReferenceLap", back_populates="car")

    def __repr__(self) -> str:
        return f"<Car(id={self.id}, name='{self.name}')>"


class Track(Base):
    """Track model (e.g., Spa, Nürburgring)."""

    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    layout: Mapped[str | None] = mapped_column(String(100), nullable=True)
    corners_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    reference_laps: Mapped[list["ReferenceLap"]] = relationship("ReferenceLap", back_populates="track")

    def __repr__(self) -> str:
        return f"<Track(id={self.id}, name='{self.name}', layout='{self.layout}')>"


class ReferenceLap(Base):
    """Reference lap model for comparison against user laps."""

    __tablename__ = "reference_laps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("simulators.id"), nullable=False, index=True
    )
    car_id: Mapped[int] = mapped_column(Integer, ForeignKey("cars.id"), nullable=False, index=True)
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id"), nullable=False, index=True)
    driver_name: Mapped[str] = mapped_column(String(100), nullable=False)
    lap_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    csv_path: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    simulator: Mapped["Simulator"] = relationship("Simulator", back_populates="reference_laps")
    car: Mapped["Car"] = relationship("Car", back_populates="reference_laps")
    track: Mapped["Track"] = relationship("Track", back_populates="reference_laps")

    def __repr__(self) -> str:
        return (
            f"<ReferenceLap(id={self.id}, driver='{self.driver_name}', "
            f"lap_time={self.lap_time_seconds}s, is_active={self.is_active})>"
        )
