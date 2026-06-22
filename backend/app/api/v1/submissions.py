"""学生提交接口：提交答案、查询分析状态"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.paper import Paper
from app.models.submission import Submission
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionCreateResponse,
    SubmissionStatusResponse,
)

router = APIRouter(prefix="/api/v1/submissions", tags=["学生提交"])


def _compute_correct_result(
    question_structure: list[dict],
    scores: dict[str, int | float],
    answers: dict[str, dict],
) -> dict:
    """根据题目结构和学生提交的得分/答案，计算每道题的对错结果"""
    result: dict[str, dict] = {}
    for q in question_structure:
        qid: str = q["id"]
        full_score: int | float = q.get("score", 0)
        q_type: str = q.get("type", "subjective")
        student_answer_data = answers.get(qid, {})
        student_answer = student_answer_data.get("answer", "")

        if q_type in ("choice", "multiple_choice"):
            correct = q.get("correctAnswer", "")
            is_correct = student_answer == correct
            score_obtained = full_score if is_correct else 0
        else:
            obtained = scores.get(qid, full_score)
            score_obtained = obtained
            is_correct = obtained == full_score

        result[qid] = {
            "is_correct": is_correct,
            "score_obtained": score_obtained,
            "full_score": full_score,
        }

    return result


@router.post("", response_model=SubmissionCreateResponse, status_code=201)
def submit_answers(
    body: SubmissionCreate,
    db: Session = Depends(get_db),
):
    """提交答案

    同一试卷下 (paper_id + student_class + student_name) 已存在则覆盖更新。
    无需 JWT 认证。
    """
    paper = db.get(Paper, body.paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="试卷不存在")
    if paper.status not in ("published",):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="试卷不在可提交状态")

    existing = db.execute(
        select(Submission).where(
            Submission.paper_id == body.paper_id,
            Submission.student_class == body.student_class,
            Submission.student_name == body.student_name,
        )
    ).scalar_one_or_none()

    question_structure = paper.question_structure or []
    correct_result = _compute_correct_result(
        question_structure, body.scores, body.answers
    )

    is_new = existing is None

    if existing:
        existing.scores = body.scores
        existing.answers = body.answers
        existing.correct_result = correct_result
        existing.analyze_status = "pending"
        submission = existing
    else:
        submission = Submission(
            paper_id=body.paper_id,
            student_name=body.student_name,
            student_class=body.student_class,
            student_number=body.student_number,
            scores=body.scores,
            answers=body.answers,
            correct_result=correct_result,
            analyze_status="pending",
        )
        db.add(submission)

    db.flush()
    db.refresh(submission)

    return SubmissionCreateResponse(
        submission_id=submission.id,
        is_new=is_new,
    )


@router.get("/{submission_id}/status", response_model=SubmissionStatusResponse)
def get_submission_status(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """查询提交记录的分析状态"""
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提交记录不存在")

    return SubmissionStatusResponse(
        submission_id=submission.id,
        analyze_status=submission.analyze_status,
    )
