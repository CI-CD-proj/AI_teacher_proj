from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_teacher
from app.models import Answer, Attempt, Teacher, Test
from app.schemas import AttemptOut, AttemptStart, AttemptSubmit, AnswerResultOut
from app.services.ai_analyzer import analyze_open_answer

router = APIRouter(tags=["attempts"])


def serialize_attempt(attempt: Attempt) -> AttemptOut:
    answers = []
    questions = {q.id: q for q in attempt.test.questions}
    for ans in attempt.answers:
        q = questions.get(ans.question_id) or ans.question
        answers.append(
            AnswerResultOut(
                question_id=ans.question_id,
                qtype=q.qtype if q else "",
                prompt=q.prompt if q else "",
                topic=q.topic if q else "",
                selected_option=ans.selected_option,
                text_answer=ans.text_answer,
                is_correct=ans.is_correct,
                score=ans.score,
                max_score=q.max_score if q else 0,
                feedback=ans.feedback,
            )
        )
    return AttemptOut(
        id=attempt.id,
        test_id=attempt.test_id,
        test_title=attempt.test.title,
        student_name=attempt.student_name,
        class_name=attempt.class_name,
        status=attempt.status,
        closed_score=attempt.closed_score,
        closed_max=attempt.closed_max,
        open_score=attempt.open_score,
        open_max=attempt.open_max,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        answers=answers,
    )


def public_test_payload(test: Test) -> dict:
    questions = []
    for q in sorted(test.questions, key=lambda x: x.position):
        questions.append(
            {
                "id": q.id,
                "qtype": q.qtype,
                "prompt": q.prompt,
                "options": q.options or [],
                "topic": q.topic,
                "max_score": q.max_score,
                "position": q.position,
            }
        )
    return {
        "id": test.id,
        "title": test.title,
        "subject": test.subject,
        "grade": test.grade,
        "description": test.description,
        "public_code": test.public_code,
        "time_limit_minutes": test.time_limit_minutes,
        "questions": questions,
    }


@router.get("/public/tests/{code}")
def get_public_test(code: str, db: Session = Depends(get_db)):
    test = db.query(Test).filter(Test.public_code == code.upper().strip()).first()
    if not test or not test.is_published:
        raise HTTPException(status_code=404, detail="Тест табылмады")
    return public_test_payload(test)


@router.post("/public/tests/{code}/start")
def start_attempt(code: str, payload: AttemptStart, db: Session = Depends(get_db)):
    test = db.query(Test).filter(Test.public_code == code.upper().strip()).first()
    if not test or not test.is_published:
        raise HTTPException(status_code=404, detail="Тест табылмады")
    attempt = Attempt(
        test_id=test.id,
        student_name=payload.student_name.strip(),
        class_name=(payload.class_name or "").strip(),
        status="in_progress",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return {"attempt_id": attempt.id, "test": public_test_payload(test)}


@router.post("/public/attempts/{attempt_id}/submit", response_model=AttemptOut)
def submit_attempt(attempt_id: str, payload: AttemptSubmit, db: Session = Depends(get_db)):
    attempt = db.get(Attempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Әрекет табылмады")
    if attempt.status == "submitted":
        return serialize_attempt(attempt)

    answers_by_q = {a.question_id: a for a in payload.answers}
    closed_score = 0.0
    closed_max = 0.0
    open_score = 0.0
    open_max = 0.0

    attempt.answers.clear()
    db.flush()

    for question in attempt.test.questions:
        submitted = answers_by_q.get(question.id)
        selected = submitted.selected_option if submitted else -1
        text = (submitted.text_answer if submitted else "") or ""
        answer = Answer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option=selected,
            text_answer=text,
        )
        if question.qtype == "closed":
            closed_max += question.max_score
            correct = selected == question.correct_option
            answer.is_correct = correct
            answer.score = question.max_score if correct else 0
            closed_score += answer.score
        else:
            open_max += question.max_score
            feedback = analyze_open_answer(question, text)
            pct = float(feedback.get("score") or 0)
            answer.feedback = feedback
            answer.score = round(question.max_score * (pct / 100.0), 2)
            answer.is_correct = bool(feedback.get("is_correct"))
            open_score += answer.score
        db.add(answer)

    attempt.closed_score = closed_score
    attempt.closed_max = closed_max
    attempt.open_score = round(open_score, 2)
    attempt.open_max = open_max
    attempt.status = "submitted"
    attempt.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(attempt)
    return serialize_attempt(attempt)


@router.get("/public/attempts/{attempt_id}", response_model=AttemptOut)
def get_public_attempt(attempt_id: str, db: Session = Depends(get_db)):
    attempt = db.get(Attempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Әрекет табылмады")
    return serialize_attempt(attempt)


@router.get("/attempts/{attempt_id}", response_model=AttemptOut)
def get_teacher_attempt(
    attempt_id: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    attempt = db.get(Attempt, attempt_id)
    if not attempt or attempt.test.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Әрекет табылмады")
    return serialize_attempt(attempt)
