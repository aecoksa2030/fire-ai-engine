from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import AnalysisSession, ChatMessage, User, get_db
from app.routers.auth import get_current_user
from app.services.claude_chat_service import ClaudeChatService

router = APIRouter(prefix="/api/v1/chat", tags=["Drawing Chat"])

# One shared instance — ClaudeChatService only holds an API client and a
# model name, no per-request state (all conversation state lives in the DB
# via ChatMessage, keyed by session_id), so there's nothing request-scoped
# to build fresh each time, unlike OpenRouterAIService in process.py.
chat_service = ClaudeChatService()


class AskRequest(BaseModel):
    question: str
    # Set by the frontend for the fixed "generate a BOQ" prompts (the
    # HCIS security prompts and the TES-P-119.21 fire prompt — see
    # frontend src/lib/security-prompts.ts / fire-prompts.ts) so the
    # model is additionally asked to end its reply with a machine-
    # parsable ```json block. Defaults False for normal free-form
    # questions, which get a plain-text answer exactly as before.
    expect_table: bool = False


def _get_owned_session(session_id: str, current_user: User, db: Session) -> AnalysisSession:
    """Shared lookup for both endpoints below — same ownership check
    get_session_pdf() in auth.py already uses (session_id + user_id),
    so a user can only chat about their own saved sessions."""
    session_rec = (
        db.query(AnalysisSession)
        .filter(
            AnalysisSession.session_id == session_id,
            AnalysisSession.user_id == current_user.id,
        )
        .first()
    )
    if not session_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Session '{session_id}' not found — حلّلت المخطط ده الأول؟"
                " المحادثة محتاجة جلسة محفوظة (فيها الـ PDF) عشان تشتغل."
            ),
        )
    return session_rec


@router.post("/{session_id}/ask")
async def ask_about_drawing(
    session_id: str,
    payload: AskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ask (or correct, or clarify) something about a previously-analyzed
    drawing. Reuses the PDF already stored on AnalysisSession — the
    frontend does NOT re-upload the file here, only sends the question
    text. See claude_chat_service.py for why this is safe/cheap to do on
    every turn (Claude prompt caching on the document block)."""
    session_rec = _get_owned_session(session_id, current_user, db)
    if not session_rec.pdf_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "مفيش PDF محفوظ لهذه الجلسة — المحادثة بتحتاج نسخة الملف"
                " اللي اتحفظت وقت التحليل الأول."
            ),
        )

    prior_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in prior_messages]

    try:
        result = chat_service.ask(
            session_rec.pdf_bytes,
            history,
            payload.question,
            expect_table=payload.expect_table,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claude Chat Error: {str(e)}")

    # Persist both turns together — a failed persist here would otherwise
    # leave a reply the user saw on-screen missing from history on the
    # next turn (Claude would then be re-asked without ever having "said"
    # it), so both inserts share one commit.
    db.add(ChatMessage(session_id=session_id, role="user", content=payload.question))
    db.add(
        ChatMessage(session_id=session_id, role="assistant", content=result["answer"])
    )
    db.commit()

    return {"answer": result["answer"], "usage": result["usage"]}


@router.get("/{session_id}/history")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Full prior thread for this session, oldest first — lets the
    frontend redraw the conversation after a Streamlit rerun/reconnect
    instead of losing it (Streamlit's own session_state does not survive
    a hard reload — see auth.py's /me endpoint docstring for the same
    issue on the login side)."""
    _get_owned_session(session_id, current_user, db)  # ownership check only

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
