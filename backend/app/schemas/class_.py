import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClassCreate(BaseModel):
    """创建班级请求"""
    class_name: str


class ClassResponse(BaseModel):
    """班级响应"""
    id: uuid.UUID
    class_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
