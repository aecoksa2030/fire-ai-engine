import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.routers.auth import User, get_password_hash

def reset_and_init():
    print("⏳ جاري مسح الجداول القديمة...")
    # مسح كل الجداول المرتبطة بالـ Base
    Base.metadata.drop_all(bind=engine)
    print("🗑️ تم مسح الجداول القديمة بنجاح.")

    print("⏳ جاري إنشاء الجداول الجديدة (New Schema)...")
    Base.metadata.create_all(bind=engine)
    print("✅ تم إنشاء الجداول الجديدة بنجاح!")

    # إضافة حساب الـ Admin الأول
    db = SessionLocal()
    try:
        admin_user = User(
            username="admin",
            email="admin@aeco.com",
            hashed_password=get_password_hash("adminpassword123"),
            role="admin"
        )
        db.add(admin_user)
        db.commit()
        print("=" * 40)
        print("🚀 تم إنشاء حساب Admin بنجاح!")
        print("👤 Username: admin")
        print("🔑 Password: adminpassword123")
        print("=" * 40)
    except Exception as e:
        db.rollback()
        print(f"❌ حدث خطأ: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_and_init()