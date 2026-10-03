from sqlalchemy import Integer, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReportMetric(Base):
    __tablename__ = "report_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(80), nullable=False, default="overview")
    period: Mapped[str] = mapped_column(String(50), nullable=False, default="monthly")
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    delta: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unit: Mapped[str] = mapped_column(String(50), nullable=True)
    metadata: Mapped[str] = mapped_column(String, nullable=True)
