import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PaperUploadResponse(BaseModel):
    """上传试卷响应"""
    paper_id: uuid.UUID
    paper_name: str
    status: str


class StructureUpdateRequest(BaseModel):
    """更新试卷结构请求"""
    question_structure: list
    subject: str | None = None
    grade: str | None = None
    total_score: int | None = None
    class_ids: list[str] | None = None


class PaperPublishResponse(BaseModel):
    """发布试卷响应"""
    qr_code_url: str
    status: str = "published"


class ClassSubmissionStats(BaseModel):
    """班级提交统计"""
    class_name: str
    total_count: int = 0
    submitted_count: int = 0


class PaperListItem(BaseModel):
    """试卷列表项"""
    id: uuid.UUID
    paper_name: str
    subject: str | None
    grade: str | None
    total_score: int | None
    status: str
    qr_code_url: str | None
    created_at: datetime
    published_at: datetime | None
    class_stats: list[ClassSubmissionStats] = []

    model_config = ConfigDict(from_attributes=True)


class SubmissionBrief(BaseModel):
    """提交记录简要"""
    id: uuid.UUID
    student_name: str
    student_class: str
    student_number: str | None
    analyze_status: str
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)
