from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db import get_db
from app.deps import get_current_teacher
from app.models import Teacher
from app.schemas import TeacherLogin, TeacherOut, TeacherRegister, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(payload: TeacherRegister, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    exists = db.query(Teacher).filter(Teacher.email == email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Бұл email тіркелген")
    teacher = Teacher(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        school_name=(payload.school_name or "").strip(),
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    token = create_access_token(teacher.id)
    return TokenOut(access_token=token, teacher=TeacherOut.model_validate(teacher))


@router.post("/login", response_model=TokenOut)
def login(payload: TeacherLogin, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.email == payload.email.lower().strip()).first()
    if not teacher or not verify_password(payload.password, teacher.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email немесе құпиясөз қате",
        )
    token = create_access_token(teacher.id)
    return TokenOut(access_token=token, teacher=TeacherOut.model_validate(teacher))


@router.get("/me", response_model=TeacherOut)
def me(teacher: Teacher = Depends(get_current_teacher)):
    return teacher
