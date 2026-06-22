"""试卷管理接口：上传、更新结构、发布、列表、查看提交"""

import datetime
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.paper import Paper
from app.models.submission import Submission
from app.models.user import User
from app.schemas.paper import (
    ClassSubmissionStats,
    PaperListItem,
    PaperPublishResponse,
    PaperUploadResponse,
    StructureUpdateRequest,
    SubmissionBrief,
)
from app.utils.qrcode import generate_qrcode

router = APIRouter(prefix="/api/v1/papers", tags=["试卷管理"])


@router.post("/upload", response_model=PaperUploadResponse, status_code=201)
def upload_paper(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传试卷 PDF，存入 ./uploads，返回 paper_id（状态为 draft）"""
    content = file.file.read()

    paper_id = uuid.uuid4()
    ext = Path(file.filename or "paper.pdf").suffix or ".pdf"
    file_path = settings.UPLOAD_DIR / f"{paper_id}{ext}"
    file_path.write_bytes(content)

    paper = Paper(
        id=paper_id,
        teacher_id=current_user.id,
        paper_name=file.filename or "未命名试卷",
        file_path=str(file_path),
        status="draft",
        question_structure=[],
    )
    db.add(paper)
    db.flush()
    db.refresh(paper)

    return PaperUploadResponse(
        paper_id=paper.id,
        paper_name=paper.paper_name,
        status=paper.status,
    )


@router.put("/{paper_id}/structure", response_model=PaperUploadResponse)
def update_structure(
    paper_id: uuid.UUID,
    body: StructureUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新试卷的 question_structure（老师人工校对后提交）"""
    paper = db.query(Paper).get(paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="试卷不存在")
    if paper.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    paper.question_structure = body.question_structure
    if body.subject is not None:
        paper.subject = body.subject
    if body.grade is not None:
        paper.grade = body.grade
    if body.total_score is not None:
        paper.total_score = body.total_score
    if body.class_ids is not None:
        paper.class_ids = body.class_ids

    db.flush()
    db.refresh(paper)

    return PaperUploadResponse(
        paper_id=paper.id,
        paper_name=paper.paper_name,
        status=paper.status,
    )


@router.post("/{paper_id}/publish", response_model=PaperPublishResponse)
def publish_paper(
    paper_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发布试卷：状态改为 published，生成二维码"""
    paper = db.query(Paper).get(paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="试卷不存在")
    if paper.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")
    if paper.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿状态的试卷可以发布")

    qr_url = generate_qrcode(paper.id)
    paper.status = "published"
    paper.qr_code_url = qr_url
    paper.published_at = datetime.datetime.now(datetime.timezone.utc)

    db.flush()

    return PaperPublishResponse(qr_code_url=qr_url)


@router.get("", response_model=list[PaperListItem])
def list_papers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前老师的试卷列表（含各班级提交统计）"""
    papers = (
        db.query(Paper)
        .filter(Paper.teacher_id == current_user.id)
        .order_by(Paper.created_at.desc())
        .all()
    )

    items: list[PaperListItem] = []
    for paper in papers:
        # 统计每个班级的提交人数
        stats_rows = (
            db.query(
                Submission.student_class,
                func.count().label("total_count"),
            )
            .filter(Submission.paper_id == paper.id)
            .group_by(Submission.student_class)
            .all()
        )
        class_stats = [
            ClassSubmissionStats(
                class_name=row.student_class,
                submitted_count=row.total_count,
            )
            for row in stats_rows
        ]

        items.append(
            PaperListItem(
                id=paper.id,
                paper_name=paper.paper_name,
                subject=paper.subject,
                grade=paper.grade,
                total_score=paper.total_score,
                status=paper.status,
                qr_code_url=paper.qr_code_url,
                created_at=paper.created_at,
                published_at=paper.published_at,
                class_stats=class_stats,
            )
        )

    return items


@router.get("/{paper_id}/submissions", response_model=list[SubmissionBrief])
def list_submissions(
    paper_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查看某试卷的所有提交记录"""
    paper = db.query(Paper).get(paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="试卷不存在")
    if paper.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    return (
        db.query(Submission)
        .filter(Submission.paper_id == paper_id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )
