from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db import get_db
from app.models import Teacher

bearer = HTTPBearer(auto_error=False)


def get_current_teacher(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Teacher:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Кіру керек")
    teacher_id = decode_token(creds.credentials)
    if not teacher_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия жарамсыз")
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Мұғалім табылмады")
    return teacher
