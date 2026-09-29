import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, LargeBinary
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from passlib.context import CryptContext

# قراءة رابط الاتصال بـ PostgreSQL الممرر من الـ docker-compose
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://ai_user:ChangeMe123!@db_fire_ai:5432/fire_engine_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ----------------- Database Models -----------------
# This is the ONLY place the ORM models live. They used to also be
# redefined in app/routers/auth.py on a second, separate declarative_base()
# with a slightly different (incompatible) set of columns mapped to the
# SAME table names. Only this module's Base.metadata is ever passed to
# create_all() (via init_db() / reset_db.py), so the auth.py copy's extra
# `pdf_bytes` column never actually existed in Postgres — every attempt to
# save a session's PDF for archive preview was silently failing at the DB
# level. auth.py now imports User/AnalysisSession from here. Do not
# redefine these models anywhere else.


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="engineer") # admin, engineer, auditor
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("AnalysisSession", back_populates="owner")
    logs = relationship("AnalysisLog", back_populates="user")

class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    analysis_result = Column(JSON, nullable=True)  # جدول الكميات BOQ + الملاحظات كاملة
    pdf_bytes = Column(LargeBinary, nullable=True)  # الملف الأصلي (PDF) لعرضه في شاشة الأرشيف

    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="sessions")

class ChatMessage(Base):
    """One turn of the interactive "chat about this drawing" feature
    (app/services/claude_chat_service.py, app/routers/chat.py). Keyed by
    the same session_id AnalysisSession already uses — a chat can only
    exist for a session that's been saved (i.e. already has pdf_bytes),
    which is exactly what the feature relies on: the PDF gets uploaded
    ONCE as part of the normal analyze flow, and every chat turn reuses
    that same stored copy instead of asking the user to re-upload it.

    Only role + plain text content are stored — the PDF itself lives on
    AnalysisSession.pdf_bytes and is re-attached to the Claude request on
    every turn (see claude_chat_service.py for why re-sending it every
    turn is required even though it's the "same" conversation, and how
    prompt caching keeps that cheap).
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        # ondelete="CASCADE" so deleting an AnalysisSession (see
        # DELETE /api/v1/auth/sessions/{session_id} in auth.py) cleans up
        # its chat thread automatically instead of the delete failing on
        # an FK violation, or orphaned messages being left behind.
        String,
        ForeignKey("analysis_sessions.session_id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReferenceExample(Base):
    """One approved past project the "reference library" can draw on to
    ground future extractions and chat answers — "here's how a similar
    drawing was correctly handled before" — instead of relying purely on
    the model's general knowledge. See
    app/services/reference_library_service.py for the retrieval logic
    that reads this table.

    Deliberately NOT a vector-search/embeddings setup. Retrieval filters
    on report_type (always available — the frontend already requires
    picking fire/security before analyzing) and ranks by plain string
    similarity on `tag`, the short classification the user types in when
    saving an example (e.g. "مخطط فيلا سكنية - نظام إنذار حريق"). No new
    infrastructure (no pgvector extension, no embedding API calls/cost)
    — good enough at the tens-to-low-hundreds-of-examples scale this
    starts at. A real embeddings-based upgrade is a valid later step if
    the library outgrows this, not something to build ahead of need.
    """
    __tablename__ = "reference_examples"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Informational only — which AnalysisSession this was approved from,
    # if any. Not a hard ForeignKey: a reference example should be able
    # to outlive (or exist independently of) the session it came from.
    session_id = Column(String, nullable=True)
    report_type = Column(String, nullable=False)  # "fire" or "security" — the hard filter at retrieval time
    tag = Column(String, nullable=False)  # short user-written classification/description
    pdf_bytes = Column(LargeBinary, nullable=True)
    approved_result = Column(JSON, nullable=False)  # the ground-truth {system_type, components[], ...}
    created_at = Column(DateTime, default=datetime.utcnow)


class ProjectSpec(Base):
    """One uploaded project technical-specification document (a PTS
    appendix like "Fire Detection, Alarm, Safety & Fire Fighting
    Requirements", or an equivalent security appendix) and the structured
    technical digest extracted from it — see
    app/services/project_spec_service.py.

    Deliberately a standalone table, NOT linked to AnalysisSession: this
    powers the separate "Projects" page, a read-the-spec-first tool for
    the estimation engineer that runs independently of the drawing
    Analyze/Archive flow (per the user's explicit request that this not
    be wired into Analyze for now). extracted_data is the full structured
    digest (JSON) the engineer reviews on-screen; pdf_bytes is kept only
    so the original document can be re-downloaded later, the same
    pattern AnalysisSession uses for its drawing PDF.
    """
    __tablename__ = "project_specs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String, nullable=False)
    pdf_bytes = Column(LargeBinary, nullable=True)
    extracted_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String, index=True, nullable=True)
    filename = Column(String, nullable=False)
    provider = Column(String, nullable=True)  # claude / gemini / groq
    report_type = Column(String, nullable=True)  # fire / security
    system_type = Column(String)
    model_used = Column(String)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    result_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logs")

# إنشاء الجداول تلقائياً عند بدء التشغيل
def init_db():
    Base.metadata.create_all(bind=engine)

# ----------------- FastAPI Dependency -----------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------- Helper Functions -----------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_user(db: Session, username: str, email: str, password: str, role: str = "engineer") -> User:
    hashed_pwd = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_pwd,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def log_analysis(
    db: Session,
    session_id: str,
    filename: str,
    provider: str,
    report_type: str,
    results: dict,
    user_id: int = None,
) -> AnalysisLog:
    """Persist one completed drawing analysis for auditing / cost tracking.

    `results` is the same `final_analysis_payload` dict process.py builds
    for the frontend — this pulls the aggregated `usage_summary` out of it
    (see process.py) instead of requiring the caller to pass token/cost
    numbers separately.
    """
    usage = results.get("usage_summary", {}) or {}

    log = AnalysisLog(
        user_id=user_id,
        session_id=session_id,
        filename=filename,
        provider=provider,
        report_type=report_type,
        system_type=results.get("system_type"),
        model_used=usage.get("model") or provider,
        input_tokens=usage.get("total_input_tokens", 0),
        output_tokens=usage.get("total_output_tokens", 0),
        cost_usd=usage.get("total_cost_usd", 0.0),
        result_json=json_dumps_safe(results),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def json_dumps_safe(data) -> str:
    import json
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception:
        return "{}"
