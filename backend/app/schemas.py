from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field


class TeacherRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2)
    school_name: str = ""


class TeacherLogin(BaseModel):
    email: EmailStr
    password: str


class TeacherOut(BaseModel):
    id: str
    email: str
    full_name: str
    school_name: str

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    teacher: TeacherOut


class QuestionIn(BaseModel):
    qtype: str  # closed | open
    prompt: str
    options: List[str] = []
    correct_option: int = -1
    reference_answer: str = ""
    topic: str = ""
    max_score: float = 1.0
    position: int = 0


class TestIn(BaseModel):
    title: str
    subject: str = ""
    grade: str = ""
    description: str = ""
    time_limit_minutes: int = 0
    is_published: bool = True
    questions: List[QuestionIn] = []


class QuestionOut(BaseModel):
    id: str
    qtype: str
    prompt: str
    options: List[str]
    correct_option: Optional[int] = None
    reference_answer: Optional[str] = None
    topic: str
    max_score: float
    position: int

    class Config:
        from_attributes = True


class TestOut(BaseModel):
    id: str
    title: str
    subject: str
    grade: str
    description: str
    public_code: str
    time_limit_minutes: int
    is_published: bool
    created_at: datetime
    questions: List[QuestionOut] = []

    class Config:
        from_attributes = True


class TestListOut(BaseModel):
    id: str
    title: str
    subject: str
    grade: str
    public_code: str
    question_count: int
    attempt_count: int
    created_at: datetime


class MaterialOut(BaseModel):
    id: str
    kind: str
    title: str
    original_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class AttemptStart(BaseModel):
    student_name: str = Field(min_length=2)
    class_name: str = ""


class AnswerIn(BaseModel):
    question_id: str
    selected_option: int = -1
    text_answer: str = ""


class AttemptSubmit(BaseModel):
    answers: List[AnswerIn]


class FeedbackOut(BaseModel):
    is_correct: Optional[bool] = None
    correctness: str = "unknown"
    score: float = 0
    what_is_wrong: str = ""
    why_wrong: str = ""
    where_to_start: str = ""
    what_to_study: List[str] = []
    correct_direction: str = ""


class AnswerResultOut(BaseModel):
    question_id: str
    qtype: str
    prompt: str
    topic: str
    selected_option: int
    text_answer: str
    is_correct: Optional[bool]
    score: float
    max_score: float
    feedback: Optional[Any] = None


class AttemptOut(BaseModel):
    id: str
    test_id: str
    test_title: str
    student_name: str
    class_name: str
    status: str
    closed_score: float
    closed_max: float
    open_score: float
    open_max: float
    started_at: datetime
    submitted_at: Optional[datetime]
    answers: List[AnswerResultOut] = []
