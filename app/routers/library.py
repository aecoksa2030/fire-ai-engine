from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import AnalysisSession, ReferenceExample, User, get_db
from app.routers.auth import get_current_user
from app.services import reference_library_service

router = APIRouter(prefix="/api/v1/library", tags=["Reference Library"])


class SaveExampleRequest(BaseModel):
    session_id: str
    report_type: str
    tag: str


@router.post("/save")
async def save_reference_example(
    payload: SaveExampleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Promotes an already-saved analysis session into the reference
    library so future analyses/chats can be grounded in it.

    Known limitation, on purpose rather than by accident: this saves
    whatever is currently on session_rec.analysis_result — the ORIGINAL
    automatic extraction. If the engineer corrected something through the
    chat feature (app/routers/chat.py) afterward, that correction lives
    as free-text chat messages, not as a structured result, and there's
    no mechanism yet to fold it back into analysis_result. Until that
    exists, saving a chat-corrected drawing as a reference means manually
    re-typing the corrected numbers isn't possible from this endpoint —
    flagged to the user in the frontend rather than silently saving the
    stale pre-correction version as if it were the approved one.
    """
    if not payload.tag.strip():
        raise HTTPException(
            status_code=400,
            detail="لازم تكتب تصنيف/وصف قصير للمثال ده (مثلاً: مخطط فيلا سكنية - نظام إنذار حريق).",
        )

    session_rec = (
        db.query(AnalysisSession)
        .filter(
            AnalysisSession.session_id == payload.session_id,
            AnalysisSession.user_id == current_user.id,
        )
        .first()
    )
    if not session_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{payload.session_id}' not found.",
        )
    if not session_rec.analysis_result:
        raise HTTPException(
            status_code=400,
            detail="الجلسة دي لسه ما فيهاش نتيجة تحليل تتحفظ كمرجع.",
        )

    example = reference_library_service.save_example(
        db=db,
        user_id=current_user.id,
        report_type=payload.report_type,
        tag=payload.tag,
        approved_result=session_rec.analysis_result,
        pdf_bytes=session_rec.pdf_bytes,
        session_id=payload.session_id,
    )
    return {"status": "success", "id": example.id, "tag": example.tag}


@router.get("/examples")
async def list_reference_examples(
    report_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ReferenceExample).filter(
        ReferenceExample.user_id == current_user.id
    )
    if report_type:
        query = query.filter(ReferenceExample.report_type == report_type)

    examples = query.order_by(ReferenceExample.created_at.desc()).all()
    return [
        {
            "id": e.id,
            "report_type": e.report_type,
            "tag": e.tag,
            "session_id": e.session_id,
            "created_at": e.created_at.isoformat(),
            # Drawing examples store "components"; PTS scope examples
            # (report_type "pts_scope", see routers/projects.py) store
            # "scope" rows.
            "component_count": len(
                (e.approved_result or {}).get("components")
                or (e.approved_result or {}).get("scope")
                or []
            ),
        }
        for e in examples
    ]


@router.delete("/examples/{example_id}")
async def delete_reference_example(
    example_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    example = (
        db.query(ReferenceExample)
        .filter(
            ReferenceExample.id == example_id,
            ReferenceExample.user_id == current_user.id,
        )
        .first()
    )
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference example {example_id} not found.",
        )
    db.delete(example)
    db.commit()
    return {"status": "success"}
