import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import ProjectSpec, ReferenceExample, User, get_db
from app.routers.auth import get_current_user
from app.services import reference_library_service
from app.services.project_spec_service import (
    REFERENCE_EXAMPLE_LIMIT,
    REFERENCE_REPORT_TYPE,
    ProjectSpecService,
    build_reference_block,
    build_scope_xlsx,
    normalize_scope_data,
    normalize_scope_rows,
)

router = APIRouter(prefix="/api/v1/projects", tags=["Project Specs"])

# Own small pool: the Anthropic call blocks for a long time, and uvicorn
# runs single-process — without offloading, one extraction would freeze
# the whole server for every other user.
executor = ThreadPoolExecutor(max_workers=2)
spec_service = ProjectSpecService()


def _reference_session_id(spec_id: int) -> str:
  """Links a ReferenceExample back to the ProjectSpec it was approved
  from (session_id is a plain string column, not a foreign key)."""
  return f"project_spec:{spec_id}"


def _get_own_spec(db: Session, spec_id: int, user: User) -> ProjectSpec:
  spec = (
      db.query(ProjectSpec)
      .filter(ProjectSpec.id == spec_id, ProjectSpec.user_id == user.id)
      .first()
  )
  if not spec:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المستند غير موجود.")
  return spec


@router.post("/extract")
async def extract_project_spec(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  """Runs the uploaded PTS through the model and returns the scope table.
  Not auto-saved — the engineer reviews/edits it, then saves."""
  if not file.filename or not file.filename.lower().endswith(".pdf"):
    raise HTTPException(status_code=400, detail="لازم ترفع ملف PDF.")

  contents = await file.read()
  if not contents:
    raise HTTPException(status_code=400, detail="الملف فاضي أو مش قادر أقرأه.")

  # RAG: approved scope tables from past projects guide naming/granularity.
  examples = reference_library_service.retrieve_similar(
      db, REFERENCE_REPORT_TYPE, limit=REFERENCE_EXAMPLE_LIMIT
  )
  reference_block = build_reference_block(examples)

  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(
      executor, spec_service.extract, contents, reference_block
  )
  result["reference_examples_used"] = len(examples)

  if result.get("error"):
    raise HTTPException(status_code=502, detail=f"فشل تحليل المستند: {result['error']}")

  return {"filename": file.filename, "data": result}


@router.post("/save")
async def save_project_spec(
    filename: str = Form(...),
    data: str = Form(...),  # JSON string: {"scope": [...], ...}
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  try:
    parsed_data = normalize_scope_data(json.loads(data))
  except json.JSONDecodeError:
    raise HTTPException(status_code=400, detail="بيانات الاستخراج غير صالحة.")

  pdf_content = await file.read() if file else None

  spec = ProjectSpec(
      user_id=current_user.id,
      filename=filename,
      pdf_bytes=pdf_content,
      extracted_data=parsed_data,
  )
  db.add(spec)
  db.commit()
  db.refresh(spec)
  return {"status": "success", "id": spec.id}


class ScopeRow(BaseModel):
  area: str
  system: str


class UpdateSpecRequest(BaseModel):
  scope: List[ScopeRow]
  filename: Optional[str] = None


@router.patch("/{spec_id}")
async def update_project_spec(
    spec_id: int,
    payload: UpdateSpecRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  """Saves the engineer's edits to an already-saved scope table. If this
  table was already approved into the reference library, the library copy
  is updated too, so the RAG never keeps a stale version."""
  spec = _get_own_spec(db, spec_id, current_user)

  data = normalize_scope_data(dict(spec.extracted_data or {}))
  data["scope"] = normalize_scope_rows([r.model_dump() for r in payload.scope])
  spec.extracted_data = data
  if payload.filename and payload.filename.strip():
    spec.filename = payload.filename.strip()

  example = (
      db.query(ReferenceExample)
      .filter(
          ReferenceExample.report_type == REFERENCE_REPORT_TYPE,
          ReferenceExample.session_id == _reference_session_id(spec.id),
      )
      .first()
  )
  if example:
    example.approved_result = {"scope": data["scope"]}

  db.commit()
  return {"status": "success", "id": spec.id}


class ApproveRequest(BaseModel):
  tag: str


@router.post("/{spec_id}/approve")
async def approve_project_spec(
    spec_id: int,
    payload: ApproveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  """Adds a saved, engineer-accepted scope table to the reference library
  (RAG) so future extractions are guided by it. Approving the same table
  again updates its library entry instead of creating a duplicate."""
  if not payload.tag.strip():
    raise HTTPException(
        status_code=400,
        detail="لازم تكتب وصف قصير للمشروع (مثلاً: محطة تحويل 380/132 كيلو فولت - حريق).",
    )

  spec = _get_own_spec(db, spec_id, current_user)
  rows = normalize_scope_rows((spec.extracted_data or {}).get("scope"))
  if not rows:
    raise HTTPException(status_code=400, detail="الجدول فاضي — مفيش حاجة تتحفظ كمرجع.")

  example = (
      db.query(ReferenceExample)
      .filter(
          ReferenceExample.report_type == REFERENCE_REPORT_TYPE,
          ReferenceExample.session_id == _reference_session_id(spec.id),
      )
      .first()
  )
  if example:
    example.tag = payload.tag.strip()
    example.approved_result = {"scope": rows}
    db.commit()
  else:
    example = reference_library_service.save_example(
        db=db,
        user_id=current_user.id,
        report_type=REFERENCE_REPORT_TYPE,
        tag=payload.tag,
        approved_result={"scope": rows},
        pdf_bytes=spec.pdf_bytes,
        session_id=_reference_session_id(spec.id),
    )
  return {"status": "success", "id": example.id, "tag": example.tag}


@router.get("/my-specs")
async def list_project_specs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  specs = (
      db.query(ProjectSpec)
      .filter(ProjectSpec.user_id == current_user.id)
      .order_by(ProjectSpec.created_at.desc())
      .all()
  )
  approved = {
      e.session_id: e.tag
      for e in db.query(ReferenceExample)
      .filter(ReferenceExample.report_type == REFERENCE_REPORT_TYPE)
      .all()
  }
  return [
      {
          "id": s.id,
          "filename": s.filename,
          "created_at": s.created_at.isoformat(),
          "data": normalize_scope_data(dict(s.extracted_data or {})),
          "has_pdf": s.pdf_bytes is not None,
          "approved_tag": approved.get(_reference_session_id(s.id)),
      }
      for s in specs
  ]


class ExportRequest(BaseModel):
  filename: str
  scope: List[ScopeRow]


@router.post("/export-xlsx", response_class=Response)
async def export_scope_xlsx(
    payload: ExportRequest,
    current_user: User = Depends(get_current_user),
):
  """Returns the (possibly edited) scope table as an Excel file in the
  engineer's reference-sheet layout."""
  rows = normalize_scope_rows([r.model_dump() for r in payload.scope])
  content = build_scope_xlsx(rows)
  base = payload.filename.rsplit(".", 1)[0] if payload.filename else "PTS"
  name = f"{base} - Scope.xlsx"
  return Response(
      content=content,
      media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"},
  )


@router.delete("/{spec_id}")
async def delete_project_spec(
    spec_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  """Deletes the saved table only. If it was approved into the reference
  library, that library entry is kept on purpose — it's an approved
  reference in its own right, managed from the library."""
  spec = _get_own_spec(db, spec_id, current_user)
  db.delete(spec)
  db.commit()
  return {"status": "success"}


@router.get("/{spec_id}/pdf", response_class=Response)
async def get_project_spec_pdf(
    spec_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
  spec = _get_own_spec(db, spec_id, current_user)
  if not spec.pdf_bytes:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="مفيش PDF محفوظ للمستند ده.")

  return Response(
      content=spec.pdf_bytes,
      media_type="application/pdf",
      headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(spec.filename or 'spec.pdf')}"},
  )
