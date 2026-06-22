import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubmissionCreate(BaseModel):
    """学生提交请求"""
    paper_id: uuid.UUID
    student_name: str = Field(..., min_length=1, max_length=100)
    student_class: str = Field(..., min_length=1, max_length=100)
    student_number: str | None = None
    scores: dict = Field(default_factory=dict)
    answers: dict = Field(default_factory=dict)


class SubmissionCreateResponse(BaseModel):
    """提交成功响应"""
    submission_id: uuid.UUID
    message: str = "提交成功，报告生成中..."
    is_new: bool


class SubmissionStatusResponse(BaseModel):
    """查询分析状态响应"""
    submission_id: uuid.UUID
    analyze_status: str

    model_config = ConfigDict(from_attributes=True)
