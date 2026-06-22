"""班级管理接口：创建、列表"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.class_ import Class
from app.models.user import User
from app.schemas.class_ import ClassCreate, ClassResponse

router = APIRouter(prefix="/api/v1/classes", tags=["班级管理"])


@router.post("", response_model=ClassResponse, status_code=201)
def create_class(
    body: ClassCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建班级"""
    cls = Class(teacher_id=current_user.id, class_name=body.class_name)
    db.add(cls)
    db.flush()
    db.refresh(cls)
    return cls


@router.get("", response_model=list[ClassResponse])
def list_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前老师的班级列表"""
    return (
        db.query(Class)
        .filter(Class.teacher_id == current_user.id)
        .order_by(Class.created_at.desc())
        .all()
    )
