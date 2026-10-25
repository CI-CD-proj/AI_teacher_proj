import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    school_name: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    materials: Mapped[list["Material"]] = relationship(back_populates="teacher")
    tests: Mapped[list["Test"]] = relationship(back_populates="teacher")


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # study_plan | syllabus
    title: Mapped[str] = mapped_column(String(255))
    original_name: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    teacher: Mapped[Teacher] = relationship(back_populates="materials")


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(128), default="")
    grade: Mapped[str] = mapped_column(String(32), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    public_code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    teacher: Mapped[Teacher] = relationship(back_populates="tests")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="test", cascade="all, delete-orphan", order_by="Question.position"
    )
    attempts: Mapped[list["Attempt"]] = relationship(
        back_populates="test", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    test_id: Mapped[str] = mapped_column(ForeignKey("tests.id"), index=True)
    qtype: Mapped[str] = mapped_column(String(16))  # closed | open
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)
    correct_option: Mapped[int] = mapped_column(Integer, default=-1)
    reference_answer: Mapped[str] = mapped_column(Text, default="")
    topic: Mapped[str] = mapped_column(String(255), default="")
    max_score: Mapped[float] = mapped_column(Float, default=1.0)
    position: Mapped[int] = mapped_column(Integer, default=0)

    test: Mapped[Test] = relationship(back_populates="questions")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    test_id: Mapped[str] = mapped_column(ForeignKey("tests.id"), index=True)
    student_name: Mapped[str] = mapped_column(String(255))
    class_name: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="in_progress")
    closed_score: Mapped[float] = mapped_column(Float, default=0)
    closed_max: Mapped[float] = mapped_column(Float, default=0)
    open_score: Mapped[float] = mapped_column(Float, default=0)
    open_max: Mapped[float] = mapped_column(Float, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    test: Mapped[Test] = relationship(back_populates="attempts")
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    selected_option: Mapped[int] = mapped_column(Integer, default=-1)
    text_answer: Mapped[str] = mapped_column(Text, default="")
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0)
    feedback: Mapped[dict] = mapped_column(JSON, nullable=True)

    attempt: Mapped[Attempt] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship()
