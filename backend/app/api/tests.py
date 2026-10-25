from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_teacher
from app.models import Attempt, Question, Teacher, Test
from app.schemas import QuestionIn, QuestionOut, TestIn, TestListOut, TestOut

router = APIRouter(prefix="/tests", tags=["tests"])


def make_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def replace_questions(db: Session, test: Test, questions: list[QuestionIn]) -> None:
    test.questions.clear()
    db.flush()
    for i, q in enumerate(questions):
        qtype = q.qtype if q.qtype in {"closed", "open"} else "open"
        options = [str(o).strip() for o in (q.options or []) if str(o).strip()]
        if qtype == "closed" and len(options) < 2:
            raise HTTPException(status_code=400, detail="Жабық сұрақта кемінде 2 нұсқа керек")
        db.add(
            Question(
                test_id=test.id,
                qtype=qtype,
                prompt=q.prompt.strip(),
                options=options,
                correct_option=q.correct_option if qtype == "closed" else -1,
                reference_answer=q.reference_answer or "",
                topic=q.topic or "",
                max_score=q.max_score or 1,
                position=q.position if q.position else i,
            )
        )


def test_out(test: Test, include_key: bool) -> TestOut:
    questions = []
    for q in sorted(test.questions, key=lambda x: x.position):
        item = QuestionOut(
            id=q.id,
            qtype=q.qtype,
            prompt=q.prompt,
            options=q.options or [],
            correct_option=q.correct_option if include_key else None,
            reference_answer=q.reference_answer if include_key else None,
            topic=q.topic,
            max_score=q.max_score,
            position=q.position,
        )
        questions.append(item)
    return TestOut(
        id=test.id,
        title=test.title,
        subject=test.subject,
        grade=test.grade,
        description=test.description,
        public_code=test.public_code,
        time_limit_minutes=test.time_limit_minutes,
        is_published=test.is_published,
        created_at=test.created_at,
        questions=questions,
    )


@router.get("", response_model=list[TestListOut])
def list_tests(
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    tests = (
        db.query(Test)
        .filter(Test.teacher_id == teacher.id)
        .order_by(Test.created_at.desc())
        .all()
    )
    result = []
    for t in tests:
        result.append(
            TestListOut(
                id=t.id,
                title=t.title,
                subject=t.subject,
                grade=t.grade,
                public_code=t.public_code,
                question_count=len(t.questions),
                attempt_count=len(t.attempts),
                created_at=t.created_at,
            )
        )
    return result


@router.post("", response_model=TestOut)
def create_test(
    payload: TestIn,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    code = make_code()
    while db.query(Test).filter(Test.public_code == code).first():
        code = make_code()
    test = Test(
        teacher_id=teacher.id,
        title=payload.title.strip(),
        subject=payload.subject.strip(),
        grade=payload.grade.strip(),
        description=payload.description.strip(),
        public_code=code,
        time_limit_minutes=payload.time_limit_minutes or 0,
        is_published=payload.is_published,
    )
    db.add(test)
    db.flush()
    replace_questions(db, test, payload.questions)
    db.commit()
    db.refresh(test)
    return test_out(test, include_key=True)


@router.get("/{test_id}", response_model=TestOut)
def get_test(
    test_id: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    test = db.get(Test, test_id)
    if not test or test.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Тест табылмады")
    return test_out(test, include_key=True)


@router.put("/{test_id}", response_model=TestOut)
def update_test(
    test_id: str,
    payload: TestIn,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    test = db.get(Test, test_id)
    if not test or test.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Тест табылмады")
    test.title = payload.title.strip()
    test.subject = payload.subject.strip()
    test.grade = payload.grade.strip()
    test.description = payload.description.strip()
    test.time_limit_minutes = payload.time_limit_minutes or 0
    test.is_published = payload.is_published
    replace_questions(db, test, payload.questions)
    db.commit()
    db.refresh(test)
    return test_out(test, include_key=True)


@router.delete("/{test_id}")
def delete_test(
    test_id: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    test = db.get(Test, test_id)
    if not test or test.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Тест табылмады")
    db.delete(test)
    db.commit()
    return {"ok": True}


@router.get("/{test_id}/attempts")
def list_attempts(
    test_id: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    test = db.get(Test, test_id)
    if not test or test.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Тест табылмады")
    rows = (
        db.query(Attempt)
        .filter(Attempt.test_id == test.id)
        .order_by(Attempt.started_at.desc())
        .all()
    )
    return [
        {
            "id": a.id,
            "student_name": a.student_name,
            "class_name": a.class_name,
            "status": a.status,
            "closed_score": a.closed_score,
            "closed_max": a.closed_max,
            "open_score": a.open_score,
            "open_max": a.open_max,
            "started_at": a.started_at,
            "submitted_at": a.submitted_at,
        }
        for a in rows
    ]
