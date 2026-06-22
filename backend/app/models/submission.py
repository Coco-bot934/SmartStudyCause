"""学生提交模型"""

import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False
    )
    student_name: Mapped[str] = mapped_column(String(100), nullable=False)
    student_class: Mapped[str] = mapped_column(String(100), nullable=False)
    student_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    answers: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    correct_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    analyze_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    submitted_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    # 联合唯一约束：同一份试卷内，同一班级不能有同名学生
    __table_args__ = (
        UniqueConstraint(
            "paper_id", "student_class", "student_name",
            name="unique_student_per_paper",
        ),
    )

    # 关系
    paper = relationship("Paper", back_populates="submissions")
