from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.deps import get_current_teacher
from app.models import Material, Teacher
from app.schemas import MaterialOut

router = APIRouter(prefix="/materials", tags=["materials"])

ALLOWED_KINDS = {"study_plan", "syllabus"}
MAX_BYTES = 15 * 1024 * 1024


def upload_root() -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


@router.get("", response_model=list[MaterialOut])
def list_materials(
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Material)
        .filter(Material.teacher_id == teacher.id)
        .order_by(Material.created_at.desc())
        .all()
    )
    return rows


@router.post("", response_model=MaterialOut)
async def upload_material(
    kind: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    if kind not in ALLOWED_KINDS:
        raise HTTPException(status_code=400, detail="Түрі study_plan немесе syllabus болуы керек")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Файл бос")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Файл 15MB-тан үлкен")
    ext = Path(file.filename or "file").suffix[:12]
    stored_name = f"{uuid4().hex}{ext}"
    dest = upload_root() / stored_name
    dest.write_bytes(data)
    material = Material(
        teacher_id=teacher.id,
        kind=kind,
        title=title.strip(),
        original_name=file.filename or stored_name,
        stored_path=str(dest),
        content_type=file.content_type or "application/octet-stream",
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.get("/{material_id}/download")
def download_material(
    material_id: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    material = db.get(Material, material_id)
    if not material or material.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Файл табылмады")
    path = Path(material.stored_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл дискіде жоқ")
    return FileResponse(
        path,
        filename=material.original_name,
        media_type=material.content_type,
    )


@router.delete("/{material_id}")
def delete_material(
    material_id: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    material = db.get(Material, material_id)
    if not material or material.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Файл табылмады")
    Path(material.stored_path).unlink(missing_ok=True)
    db.delete(material)
    db.commit()
    return {"ok": True}
