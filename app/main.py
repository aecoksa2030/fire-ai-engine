from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import process, auth, chat, library, projects


# إعداد دالة تشغيل وإغلاق السيرفر (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
  # 1. إنشاء الجداول في PostgreSQL عند بدء التطبيق
  print("⚡ Initializing PostgreSQL Database Tables...")
  init_db()

  # 2. التأكد من وجود مجلد حفظ الملفات المربوط بالـ Volume
  storage_dir = os.environ.get("UPLOAD_DIR", "/app/storage/drawings")
  os.makedirs(storage_dir, exist_ok=True)

  yield
  print("🛑 Shutting down Fire AI Engine...")


app = FastAPI(
    title="Fire Safety AI Engine",
    description="MEP Quantity Takeoff & Physical Security AI Analysis API",
    version="1.0.0",
    lifespan=lifespan,
)

# تفعيل الـ CORS لتوفير الاتصال السلس مع الـ Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ربط مجلد الملفات المرفوعة لتتمكن من استدعائها برابط مباشر
# مثال: http://localhost:8003/storage/drawings/KDS-297.pdf
storage_path = os.environ.get("UPLOAD_DIR", "/app/storage/drawings")
if os.path.exists(storage_path):
  app.mount(
      "/storage/drawings",
      StaticFiles(directory=storage_path),
      name="drawings_storage",
  )

# تسجيل الـ Routers
# تعديل السطر ده:
app.include_router(process.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(library.router)
app.include_router(projects.router)

@app.get("/")
def read_root():
  return {
      "status": "Fire AI Engine is Running!",
      "database": "Connected to PostgreSQL",
      "version": "1.0.0",
  }