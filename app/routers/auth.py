import datetime
import json
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import AnalysisSession, User, get_db

# ---------------------------------------------------------
# Configuration & Security Constants
# ---------------------------------------------------------
# NOTE: the models (User, AnalysisSession) used to be redefined in this
# file on a second, separate declarative_base() with different columns
# than app/database.py's versions of the same tables. They now live only
# in app/database.py and are imported above — do not redefine them here.

SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY",
    "aeco_super_secret_jwt_key_change_me_in_production",
)
if SECRET_KEY == "aeco_super_secret_jwt_key_change_me_in_production":
    print(
        "⚠️ WARNING: JWT_SECRET_KEY is not set in the environment — using the"
        " insecure default. Set JWT_SECRET_KEY in your .env before deploying"
        " this anywhere other than local development."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 Hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & User Sessions"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "engineer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str


# ---------------------------------------------------------
# Helper Auth Functions
# ---------------------------------------------------------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# ---------------------------------------------------------
# Auth Router Endpoints
# ---------------------------------------------------------


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
    }


@router.get("/me", response_model=Token)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """Validate a previously-issued token and return the same shape as
    /login. Used by the frontend to restore a session after a browser
    refresh (Streamlit's session_state does not survive a hard reload) —
    it keeps the JWT in the page's query params and re-validates it here
    instead of forcing the user back to the login screen every time."""
    return {
        "access_token": "",
        "token_type": "bearer",
        "username": current_user.username,
        "role": current_user.role,
    }


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="عفواً، هذه الصلاحية مخصصة لمدير النظام فقط"
        )

    existing_user = (
        db.query(User).filter(User.username == user_data.username).first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="اسم المستخدم موجود بالفعل")

    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd,
        role=user_data.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin-only. Lists every account. Before this, POST /users (create)
    was the only user-management endpoint that existed — there was no way
    for the frontend to show who already has an account, let alone change
    a role or reset a password, short of a direct DB query. This one, plus
    PATCH/DELETE below, close that gap."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="عفواً، هذه الصلاحية مخصصة لمدير النظام فقط"
        )
    return db.query(User).order_by(User.username).all()


class UserUpdate(BaseModel):
    role: Optional[str] = None
    new_password: Optional[str] = None


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin-only. Either field may be sent alone — the frontend uses this
    for two separate actions: changing a user's role, and resetting their
    password. There is no "forgot password" email flow anywhere in this
    app, so an admin setting a new password directly is the only recovery
    path when someone is locked out."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="عفواً، هذه الصلاحية مخصصة لمدير النظام فقط"
        )
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    if payload.role is not None:
        if payload.role not in ("engineer", "auditor", "admin"):
            raise HTTPException(status_code=400, detail="دور غير صالح")
        if target.role == "admin" and payload.role != "admin":
            # Refuse to demote the last remaining admin — otherwise this
            # exact screen becomes unreachable to everyone with no way
            # back short of a direct DB edit.
            admin_count = db.query(User).filter(User.role == "admin").count()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="لا يمكن تنزيل آخر مدير نظام في التطبيق",
                )
        target.role = payload.role

    if payload.new_password is not None:
        if len(payload.new_password) < 6:
            raise HTTPException(
                status_code=400,
                detail="كلمة المرور الجديدة قصيرة جداً (6 أحرف على الأقل)",
            )
        target.hashed_password = get_password_hash(payload.new_password)

    db.commit()
    db.refresh(target)
    return target


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin-only. Guards against an admin deleting their own account
    (would lock the acting session out mid-action) and against deleting
    the last remaining admin (would lock everyone out of user management,
    same reasoning as the demotion guard above)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="عفواً، هذه الصلاحية مخصصة لمدير النظام فقط"
        )
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="لا يمكنك حذف حسابك الخاص")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    if target.role == "admin":
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400, detail="لا يمكن حذف آخر مدير نظام في التطبيق"
            )

    db.delete(target)
    db.commit()
    return {"status": "success"}


@router.post("/sessions/save")
async def save_session(
    session_id: str = Form(...),
    filename: str = Form(...),
    data: str = Form(...),  # يتم استقبال الـ JSON كـ String
    file: Optional[UploadFile] = File(None),  # استقبال ملف الـ PDF كـ Upload File اختياري
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parsed_data = json.loads(data)
    pdf_content = await file.read() if file else None

    existing_session = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.session_id == session_id)
        .first()
    )

    if existing_session:
        existing_session.analysis_result = parsed_data
        existing_session.filename = filename
        if pdf_content:
            existing_session.pdf_bytes = pdf_content
    else:
        new_session = AnalysisSession(
            session_id=session_id,
            user_id=current_user.id,
            filename=filename,
            analysis_result=parsed_data,
            pdf_bytes=pdf_content,
        )
        db.add(new_session)

    db.commit()
    return {"status": "success", "message": "تم حفظ الجلسة والملف بنجاح في الأرشيف"}


@router.get("/sessions/my-sessions")
async def get_my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.user_id == current_user.id)
        .order_by(AnalysisSession.created_at.desc())
        .all()
    )

    return [
        {
            "session_id": s.session_id,
            "filename": s.filename,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M"),
            "data": s.analysis_result,
        }
        for s in sessions
    ]


class SessionRenameRequest(BaseModel):
    filename: str


@router.patch("/sessions/{session_id}")
async def rename_session(
    session_id: str,
    payload: SessionRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lets a user rename (retitle) a saved archive session — the
    filename was previously fixed to whatever the uploaded file was
    called at analysis time with no way to change it afterward."""
    if not payload.filename.strip():
        raise HTTPException(status_code=400, detail="الاسم مينفعش يكون فاضي")

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
            detail=f"Session with ID '{session_id}' not found.",
        )

    session_rec.filename = payload.filename.strip()
    db.commit()
    return {"status": "success", "filename": session_rec.filename}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes a saved archive session. Does NOT touch any
    ReferenceExample rows that were promoted from this session (see
    app/routers/library.py) — a reference example is intentionally
    independent once saved (session_id there is informational only, not
    a hard foreign key), so deleting the original archived session
    doesn't silently remove something already in the reference library."""
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
            detail=f"Session with ID '{session_id}' not found.",
        )

    db.delete(session_rec)
    db.commit()
    return {"status": "success"}


@router.get("/sessions/{session_id}/pdf", response_class=Response)
def get_session_pdf(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    جلب ملف الـ PDF الأصلي للجلسة المحفوظة للعرض في شاشة الأرشيف
    """
    # 1. البحث عن الجلسة باستخدام AnalysisSession الموديل الصحيح
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
            detail=f"Session with ID '{session_id}' not found.",
        )

    # 2. التأكد من وجود بايتات الـ PDF
    if not session_rec.pdf_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF binary data is missing for this session.",
        )

    # 3. إرجاع الـ PDF بـ fastapi Response
    return Response(
        content=session_rec.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f"inline; filename={session_rec.filename or 'drawing.pdf'}"
            )
        },
    )
