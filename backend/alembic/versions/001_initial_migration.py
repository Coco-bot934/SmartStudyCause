"""初始数据库迁移：创建所有核心表

Revision ID: 001
Revises:
Create Date: 2026-06-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 用户表（老师）
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # 班级表
    op.create_table(
        "classes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("teacher_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # 试卷表
    op.create_table(
        "papers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("teacher_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("paper_name", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(100), nullable=True),
        sa.Column("grade", sa.String(50), nullable=True),
        sa.Column("total_score", sa.Integer, nullable=True),
        sa.Column("class_ids", JSONB, nullable=True, server_default=sa.text("'[]'::jsonb")),
        sa.Column("question_structure", JSONB, nullable=True, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("qr_code_url", sa.String(512), nullable=True),
        sa.Column("file_path", sa.Text, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # 学生提交表（含联合唯一约束）
    op.create_table(
        "submissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_name", sa.String(100), nullable=False),
        sa.Column("student_class", sa.String(100), nullable=False),
        sa.Column("student_number", sa.String(100), nullable=True),
        sa.Column("scores", JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("answers", JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("correct_result", JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("analyze_status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("paper_id", "student_class", "student_name", name="unique_student_per_paper"),
    )

    # 索引
    op.create_index("idx_papers_teacher_id", "papers", ["teacher_id"])
    op.create_index("idx_submissions_paper_id", "submissions", ["paper_id"])


def downgrade() -> None:
    op.drop_table("submissions")
    op.drop_table("papers")
    op.drop_table("classes")
    op.drop_table("users")
