from collections import defaultdict
import gc
import io
import json
import os
import tempfile
import uuid
from docx import Document
from docx.shared import Inches, Pt, RGBColor
import ezdxf
from ezdxf import recover
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import pymupdf as fitz
import requests
import streamlit as st

# ---------------------------------------------------------
# Page Configuration & Base Styling
# ---------------------------------------------------------
# ---------------------------------------------------------
# Brand
# ---------------------------------------------------------
# Single place to swap in the real project/company name + logo once decided
# — every header/sidebar/login-screen/page-title reference below reads
# from here instead of a hardcoded string, so that's a one-line change,
# not a find-and-replace across the file. "AECO" was already the working
# name used in the page title/login copy before this redesign, so kept as
# the placeholder.
BRAND_NAME = "AECO"
BRAND_TAGLINE = "Fire & Security AI Engine"
BRAND_ICON = "🔥"  # swap for an <img> logo later — see render_brand() below

st.set_page_config(
    page_title=f"{BRAND_NAME} — Enterprise Fire & Safety AI Engine",
    page_icon=BRAND_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_API_URL = "http://api:8003/api/v1"

# ---------------------------------------------------------
# Translations Dictionary (i18n)
# ---------------------------------------------------------
TRANSLATIONS = {
    "ar": {
        "title": "🔥 AECO - محرك تحليل المخططات واستخراج الكميات",
        "caption": (
            "رفع مخططات السلامة والحريق (PDF / AutoCAD DXF / DWG) واستخراج جدول"
            " الكميات (BOQ) آلياً مع أداة مراجعة تفاعلية."
        ),
        "login_title": "🔐 تسجيل الدخول - نظام AECO AI Engine",
        "login_caption": "منظومة الذكاء الاصطناعي لإدارة المخططات وحصر الكميات الهندسي",
        "username": "اسم المستخدم",
        "password": "كلمة المرور",
        "login_btn": "تسجيل الدخول 🚀",
        "login_success": "تم تسجيل الدخول بنجاح!",
        "login_error": "❌ اسم المستخدم أو كلمة المرور غير صحيحة",
        "login_conn_error": "❌ فشل الاتصال بسيرفر الهوية:",
        "user_role": "الرتبة:",
        "logout": "🚪 تسجيل الخروج",
        "nav_title": "📌 التنقل في النظام",
        "nav_new": "🚀 تحليل مخطط جديد",
        "nav_archive": "📁 أرشيف الجلسات والمخططات السابقة",
        "nav_users": "👥 إدارة المستخدمين",
        "ai_engine": "🤖 محرك الذكاء الاصطناعي",
        "report_type": "📄 نوع النظام والمخطط",
        "unit": "📐 وحدة القياس",
        "security_sys": "تقرير أنظمة الأمن والحماية",
        "fire_sys": "تقرير مكافحة الحريق والسلامة",
        "upload_label": "قم بإسقاط أو اختيار مخطط هندسي (PDF, DXF, DWG)",
        "preview_header": "🖼️ معاينة المخطط الهندسـي والزوم التفاعلي",
        "boq_header": "📊 نتائج حصر الكميات (BOQ)",
        "btn_analyze": "🚀 تحليل وحصر الكميات الآن",
        "analyzing": "⏳ جاري تحليل صفحات المخطط بواسطة الذكاء الاصطناعي...",
        "converting_dwg": "⏳ جاري تحويل ملف DWG إلى DXF للعرض التفاعلي...",
        "conversion_failed": "فشل التحويل برقم الحالة:",
        "conversion_conn_err": "لا يمكن الاتصال بخدمة التحويل:",
        "page_num": "رقم الصفحة:",
        "dpi_label": "دقة الوضوح والزوم (DPI):",
        "success_msg": "تم الانتهاء من المعالجة بنجاح!",
        "no_devices": "لم يتم العثور على أجهزة مسجلة في المخطط.",
        "provider_error_notice": "⚠️ فشل استدعاء مزوّد الذكاء الاصطناعي فعليًا (وليس مجرد مخطط فارغ) — التفاصيل الحقيقية للخطأ موضحة في الملاحظات أدناه.",
        "sys_notes": "📋 التقرير الفني وملاحظات التدقيق الهندسي",
        "download_csv": "📥 تحميل جدول BOQ (CSV)",
        "total_items": "إجمالي الأجهزة المكتشفة",
        "confidence_level": "مستوى الدقة العالية",
        "estimated_api_cost": "التكلفة التقديرية للتحليل (AI)",
        "zoom_hint": (
            "💡 يمكنك استخدام عجلة الماوس للزوم (Zoom) والسحب بالماوس"
            " (Pan) للتحريك داخل المخطط."
        ),
        "page_inspect": "📄 يتم الآن فحص الصفحة",
        "of_page": "من أصل",
        "completed_status": "✅ اكتمل التحليل بنجاح!",
        "save_archive_err": "⚠️ تعذر حفظ الجلسة بالأرشيف:",
        "api_err": "خطأ من الـ API",
        "conn_fail": "فشل الاتصال:",
        "notes_title": "📌 ملاحظات",
        "note_count": "ملاحظة",
        "general_page": "عام / General",
        "download_word": "📄 تحميل التقرير الفني بملف Word (.docx)",
        "archive_title": "📁 أرشيف الجلسات والمخططات السابقة",
        "archive_caption": "استرجاع التحليلات والتقارير المحفوظة السابقة مع المعاينة التفاعلية للمخطط.",
        "no_sessions": "ℹ️ لا توجد جلسات تحليل محفوظة سابقة حتى الآن.",
        "select_session": "اختر الجلسة المحفوظة لعرض نتائجها الكاملة:",
        "session_id": "معرف الجلسة:",
        "created_at": "تاريخ الإنشاء:",
        "fetch_archive_err": "❌ تعذر جلب الأرشيف:",
        "archive_conn_err": "❌ حدث خطأ أثناء الاتصال بسيرفر الأرشيف:",
        "fetching_pdf": "⏳ جاري تحميل المخطط الهندسي الخاص بالجلسة...",
        "pdf_fetch_err": "⚠️ تعذر تحميل الرسم الهندسي الأصلي للجلسة من السيرفر.",
        "archive_rename_label": "اسم الجلسة",
        "archive_rename_btn": "✏️ تعديل الاسم",
        "archive_rename_ok": "✅ اتغيّر اسم الجلسة.",
        "archive_delete_confirm": "متأكد من الحذف؟",
        "archive_delete_btn": "🗑️ احذف الجلسة",
        "archive_delete_ok": "✅ اتحذفت الجلسة.",
        "users_title": "👥 إدارة المستخدمين وصلاحيات النظام",
        "users_admin_only": "⚠️ عفواً، هذه الشاشة مخصصة لمدراء النظام (Admins) فقط.",
        "add_user": "➕ إضافة مهندس / مراجع جديد",
        "email": "البريد الإلكتروني",
        "role": "الصلاحية",
        "role_engineer": "مهندس حصر (Engineer)",
        "role_auditor": "مراجع فني (Auditor)",
        "role_admin": "مدير نظام (Admin)",
        "create_acc_btn": "إنشاء الحساب 🚀",
        "fill_all_fields": "يرجى ملء جميع الحقول المطلوبة!",
        "acc_created": "تم إنشاء الحساب بنجاح!",
        "acc_fail": "❌ فشل إنشاء الحساب:",
        "users_list_title": "👥 المستخدمون الحاليون",
        "users_list_empty": "لا يوجد مستخدمون بعد.",
        "users_list_fetch_err": "❌ تعذر تحميل قائمة المستخدمين:",
        "users_col_username": "اسم المستخدم",
        "users_col_email": "البريد الإلكتروني",
        "users_col_role": "الصلاحية",
        "users_new_role_label": "الصلاحية الجديدة",
        "users_change_role_btn": "💾 حفظ الصلاحية",
        "users_role_updated": "✅ تم تحديث الصلاحية.",
        "users_new_password_label": "كلمة مرور جديدة",
        "users_reset_pw_btn": "🔑 إعادة تعيين كلمة المرور",
        "users_reset_pw_ok": "✅ تم تغيير كلمة المرور.",
        "users_reset_pw_hint": "6 أحرف على الأقل",
        "users_delete_confirm": "متأكد من حذف هذا المستخدم؟",
        "users_delete_btn": "🗑️ حذف المستخدم",
        "users_delete_ok": "✅ تم حذف المستخدم.",
        # Dataframe columns
        "col_name": "اسم الجهاز / المكون",
        "col_count": "الكمية",
        "col_supplier": "نوع المورد",
        "col_unit_cost": "سعر الوحدة (ريال)",
        "col_erp_code": "كود الصنف (ERPNext)",
        "col_erp_name": "اسم الصنف (ERPNext)",
        "col_erp_avg": "المتوسط المتحرك / TCO (ريال)",
        "col_erp_sell": "سعر البيع الحالي (ريال)",
        "col_total_cost": "التكلفة الإجمالية (ريال)",
        "col_confidence": "مستوى الثقة",
        "currency_format": "%'.2f ريال",
        # Interactive chat about the drawing
        "chat_header": "💬 اسأل عن المخطط (محادثة تفاعلية)",
        "chat_caption": (
            "شغالة على نفس ملف الـ PDF اللي رفعته فوق من غير ما تحتاج"
            " ترفعه تاني — اسأل، صحّح، أو اطلب توضيح لحد ما توصل لنتيجة"
            " مرضية."
        ),
        "chat_template_label": "نوع السؤال",
        "chat_template_custom": "✍️ سؤال حر",
        "chat_template_materials": "🧮 احسب كميات المواد بتفاصيل معينة",
        "chat_template_rooms": "📐 احسب قياسات الغرف",
        "chat_template_element": "🔍 هل يوجد عنصر معين؟",
        "chat_template_materials_hint": (
            "اكتب التفاصيل/البنود اللي عايز الحساب يشملها (كل بند في سطر):"
        ),
        "chat_template_materials_placeholder": "1. كاشفات الدخان\n2. طفايات الحريق\n3. الرشاشات",
        "chat_template_materials_fill": (
            "احسبلي كميات المواد/الأجهزة في المخطط بالتفصيل ده:\n{details}"
        ),
        "chat_template_rooms_hint": "هيطلب من الموديل قياسات (الأبعاد والمساحات) كل الغرف الموجودة في المخطط.",
        "chat_template_rooms_fill": (
            "احسبلي قياسات (الأبعاد والمساحات) كل الغرف الموجودة في"
            " المخطط، واذكر رقم الصفحة لكل غرفة لو ينفع."
        ),
        "chat_template_element_hint": "اسم العنصر/الجهاز اللي عايز تتأكد منه:",
        "chat_template_element_placeholder": "مطفأة حريق CO2",
        "chat_template_element_fill": (
            "هل يوجد {element} في المخطط؟ لو موجود، وضّح فين بالظبط"
            " (رقم الصفحة/الموقع) وكام عدده."
        ),
        "chat_template_need_input": "⚠️ اكتب سؤالك أو املأ التفاصيل المطلوبة الأول.",
        "chat_input_label": "اكتب سؤالك أو ملاحظتك",
        "chat_placeholder": "مثلاً: طلعلي كل الديتكتورز في الدور التاني بس",
        "chat_send": "📨 ابعت",
        "chat_thinking": "بيفكر...",
        "chat_err": "خطأ:",
        "chat_conn_fail": "فشل الاتصال:",
        # Reference / RAG library
        "rag_header": "📚 أضف كمرجع لمكتبة التعلم (RAG)",
        "rag_caption": (
            "هيتحفظ المخطط ده كمثال معتمد — التحليلات والمحادثات الجاية"
            " لنفس نوع النظام هتسترشد بيه تلقائيًا."
        ),
        "rag_correction_caveat": (
            "⚠️ ملحوظة: الحفظ هيسجّل نتيجة التحليل الأوتوماتيكي الحالية"
            " كما هي. لو صححت حاجة في المحادثة فوق، التصحيح ده لسه مش"
            " بيترجع تلقائيًا للنتيجة المحفوظة — لو عايز المرجع يعكس"
            " التصحيح، حدّث الأرقام يدويًا الأول."
        ),
        "rag_tag_label": "تصنيف/وصف قصير للمخطط ده",
        "rag_tag_placeholder": "مثلاً: مخطط فيلا سكنية - نظام إنذار حريق",
        "rag_save_btn": "💾 احفظ كمرجع",
        "rag_tag_required": "⚠️ اكتب تصنيف قصير للمخطط الأول.",
        "rag_saved_ok": "✅ اتحفظ في مكتبة المراجع بنجاح.",
    },
    "en": {
        "title": "🔥 AECO - Fire Safety Drawing & CAD AI Engine",
        "caption": (
            "Upload Fire Safety Drawings (PDF / AutoCAD DXF / DWG) to"
            " automatically extract BOQ with interactive engineering review"
            " tools."
        ),
        "login_title": "🔐 Login - AECO AI Engine System",
        "login_caption": "AI System for Engineering Drawing Management & Quantity Surveying",
        "username": "Username",
        "password": "Password",
        "login_btn": "Login 🚀",
        "login_success": "Login successful!",
        "login_error": "❌ Invalid username or password",
        "login_conn_error": "❌ Failed to connect to authentication server:",
        "user_role": "Role:",
        "logout": "🚪 Logout",
        "nav_title": "📌 Navigation",
        "nav_new": "🚀 Analyze New Drawing",
        "nav_archive": "📁 Saved Sessions & Archive",
        "nav_users": "👥 User Management",
        "ai_engine": "🤖 AI Provider Engine",
        "report_type": "📄 Drawing & System Type",
        "unit": "📐 Measurement Unit",
        "security_sys": "Security Systems Report",
        "fire_sys": "Fire Protection Report",
        "upload_label": "Drop or select an engineering drawing (PDF, DXF, DWG)",
        "preview_header": "🖼️ Interactive Drawing Preview & Inspection",
        "boq_header": "📊 BOQ Extraction Results",
        "btn_analyze": "🚀 Analyze & Extract BOQ Now",
        "analyzing": "⏳ Analyzing drawing pages with AI Engine...",
        "converting_dwg": "⏳ Converting DWG to DXF for interactive rendering...",
        "conversion_failed": "Conversion failed with status code:",
        "conversion_conn_err": "Cannot connect to conversion service:",
        "page_num": "Select Page:",
        "dpi_label": "Render Resolution / Zoom (DPI):",
        "success_msg": "Processing completed successfully!",
        "no_devices": "No components detected in this drawing.",
        "provider_error_notice": "⚠️ The AI provider call actually failed (this isn't just an empty drawing) — the real error is in the notes below.",
        "sys_notes": "📋 Technical Observations & Audit Report",
        "download_csv": "📥 Download BOQ (CSV)",
        "total_items": "Total Devices Detected",
        "confidence_level": "High Confidence Rate",
        "estimated_api_cost": "Estimated AI Analysis Cost",
        "zoom_hint": (
            "💡 Use mouse scroll wheel to Zoom in/out and click-drag to Pan"
            " inside the drawing."
        ),
        "page_inspect": "📄 Inspecting Page",
        "of_page": "of",
        "completed_status": "✅ Analysis Completed Successfully!",
        "save_archive_err": "⚠️ Failed to save session to archive:",
        "api_err": "API Error",
        "conn_fail": "Connection Failed:",
        "notes_title": "📌 Notes for",
        "note_count": "note(s)",
        "general_page": "General Notes",
        "download_word": "📄 Download Technical Report (.docx)",
        "archive_title": "📁 Saved Sessions & Archive",
        "archive_caption": "Retrieve and inspect previous saved analyses and reports with interactive drawing viewer.",
        "no_sessions": "ℹ️ No previously saved sessions found.",
        "select_session": "Select a saved session to view full results:",
        "session_id": "Session ID:",
        "created_at": "Created At:",
        "fetch_archive_err": "❌ Failed to fetch archive:",
        "archive_conn_err": "❌ Error connecting to archive server:",
        "fetching_pdf": "⏳ Fetching original drawing PDF for session...",
        "pdf_fetch_err": "⚠️ Unable to load original drawing PDF from server.",
        "archive_rename_label": "Session name",
        "archive_rename_btn": "✏️ Rename",
        "archive_rename_ok": "✅ Session renamed.",
        "archive_delete_confirm": "Confirm delete?",
        "archive_delete_btn": "🗑️ Delete Session",
        "archive_delete_ok": "✅ Session deleted.",
        "users_title": "👥 User Management & Permissions",
        "users_admin_only": "⚠️ Access Restricted. This page is available to System Admins only.",
        "add_user": "➕ Add New Engineer / Auditor",
        "email": "Email Address",
        "role": "Role / Permission",
        "role_engineer": "Quantity Engineer",
        "role_auditor": "Technical Auditor",
        "role_admin": "System Admin",
        "create_acc_btn": "Create Account 🚀",
        "fill_all_fields": "Please fill in all required fields!",
        "users_list_title": "👥 Existing Users",
        "users_list_empty": "No users yet.",
        "users_list_fetch_err": "❌ Could not load the user list:",
        "users_col_username": "Username",
        "users_col_email": "Email",
        "users_col_role": "Role",
        "users_new_role_label": "New role",
        "users_change_role_btn": "💾 Save Role",
        "users_role_updated": "✅ Role updated.",
        "users_new_password_label": "New password",
        "users_reset_pw_btn": "🔑 Reset Password",
        "users_reset_pw_ok": "✅ Password changed.",
        "users_reset_pw_hint": "At least 6 characters",
        "users_delete_confirm": "Are you sure you want to delete this user?",
        "users_delete_btn": "🗑️ Delete User",
        "users_delete_ok": "✅ User deleted.",
        "acc_created": "Account created successfully!",
        "acc_fail": "❌ Failed to create account:",
        # Dataframe columns
        "col_name": "Device / Component Name",
        "col_count": "Quantity",
        "col_supplier": "Supplier Type",
        "col_unit_cost": "Unit Cost (SAR)",
        "col_erp_code": "ERP Item Code",
        "col_erp_name": "ERP Item Name",
        "col_erp_avg": "Moving Avg / TCO (SAR)",
        "col_erp_sell": "Selling Price (SAR)",
        "col_total_cost": "Total Cost (SAR)",
        "col_confidence": "Confidence Level",
        "currency_format": "%'.2f SAR",
        # Interactive chat about the drawing
        "chat_header": "💬 Ask About This Drawing (Interactive Chat)",
        "chat_caption": (
            "Uses the same PDF you already uploaded above — no need to"
            " re-upload it. Ask, correct, or clarify until you're happy"
            " with the answer."
        ),
        "chat_template_label": "Question type",
        "chat_template_custom": "✍️ Free-form question",
        "chat_template_materials": "🧮 Calculate material quantities with details",
        "chat_template_rooms": "📐 Calculate room dimensions",
        "chat_template_element": "🔍 Check if an element exists",
        "chat_template_materials_hint": (
            "List the items/details you want the calculation to cover"
            " (one per line):"
        ),
        "chat_template_materials_placeholder": "1. Smoke detectors\n2. Fire extinguishers\n3. Sprinklers",
        "chat_template_materials_fill": (
            "Calculate the quantities of materials/devices in the drawing"
            " covering these details:\n{details}"
        ),
        "chat_template_rooms_hint": "Asks the model for the dimensions (size and area) of every room in the drawing.",
        "chat_template_rooms_fill": (
            "Calculate the dimensions (size and area) of every room in"
            " the drawing, and note the page number for each room if"
            " possible."
        ),
        "chat_template_element_hint": "Name of the element/device to check for:",
        "chat_template_element_placeholder": "CO2 fire extinguisher",
        "chat_template_element_fill": (
            "Is there a {element} in the drawing? If so, specify exactly"
            " where (page number/location) and how many."
        ),
        "chat_template_need_input": "⚠️ Type your question or fill in the required details first.",
        "chat_input_label": "Type your question or note",
        "chat_placeholder": "e.g. List all the detectors on the second floor only",
        "chat_send": "📨 Send",
        "chat_thinking": "Thinking...",
        "chat_err": "Error:",
        "chat_conn_fail": "Connection failed:",
        # Reference / RAG library
        "rag_header": "📚 Save as a Reference (RAG Library)",
        "rag_caption": (
            "Saves this drawing as an approved example — future analyses"
            " and chats of the same system type will automatically be"
            " grounded in it."
        ),
        "rag_correction_caveat": (
            "⚠️ Note: saving records the current automatic analysis"
            " result as-is. If you corrected something in the chat"
            " above, that correction is not yet reflected back into the"
            " saved result automatically — update the numbers manually"
            " first if you want the reference to reflect the correction."
        ),
        "rag_tag_label": "Short tag/description for this drawing",
        "rag_tag_placeholder": "e.g. Residential villa - fire alarm system",
        "rag_save_btn": "💾 Save as Reference",
        "rag_tag_required": "⚠️ Type a short tag for the drawing first.",
        "rag_saved_ok": "✅ Saved to the reference library successfully.",
    },
}

# ---------------------------------------------------------
# Dynamic CSS Injection (RTL / LTR)
# ---------------------------------------------------------
lang_code = st.sidebar.selectbox(
    "Language / اللغة",
    options=["en", "ar"],
    format_func=lambda x: "العربية 🇸🇦" if x == "ar" else "English 🇺🇸",
)
t = TRANSLATIONS[lang_code]

rtl_direction = "rtl" if lang_code == "ar" else "ltr"
text_align = "right" if lang_code == "ar" else "left"
border_side = "border-right" if lang_code == "ar" else "border-left"

# Light/dark toggle, take two. The first attempt guessed at internal
# Streamlit/baseweb selectors with no way to check them — wrong guesses,
# then pulled back to dark-only. This time the selectors below were
# checked against the actual deployed app (fire-engine.maqaree.com) via
# live browser inspection (getComputedStyle / DOM walk on the real page),
# not guessed. Two concrete things that inspection found:
#   1. This Streamlit build doesn't use baseweb at all for these widgets
#      (it's react-aria-components under the hood) — every earlier
#      [data-baseweb=...] selector was targeting a library that isn't
#      even loaded, which is why it silently did nothing.
#   2. Streamlit bakes config.toml's theme colors as literal computed
#      rgb() values into its own generated CSS classes at server
#      startup — not as CSS variables — so those specific colors can't
#      be swapped at runtime at all; they can only be beaten by a more
#      specific/!important rule of ours targeting the same element,
#      which is what the selectors below do (verified live: overriding
#      [data-testid="stSelectbox"] div[role="group"] does take effect —
#      confirmed via getComputedStyle, not just by eye, since this
#      remote screenshot tool turned out to have its own paint-lag
#      artifacts that made a couple of correct fixes LOOK broken in a
#      screenshot when the DOM said otherwise).
# Persisted the same way the auth token is (see _restore_session_from_url()
# below): st.session_state alone does NOT survive a hard browser refresh —
# a refresh opens a brand-new WebSocket session, so session_state resets
# to its defaults every time — which was exactly the reported bug
# ("لما بغير الوضع نهاري وأعمل رفريش بيرجع ليلي لوحده"). The theme is
# additionally stashed in st.query_params["theme"], which DOES survive a
# refresh (it's part of the URL), and is read back here before the widget
# renders so the last-picked mode wins even on a cold load.
if "theme_mode" not in st.session_state:
  _url_theme = st.query_params.get("theme")
  st.session_state["theme_mode"] = _url_theme if _url_theme in ("dark", "light") else "dark"

theme_mode = st.sidebar.radio(
    "Theme / الوضع",
    options=["dark", "light"],
    index=0 if st.session_state["theme_mode"] == "dark" else 1,
    format_func=lambda x: "🌙 Dark" if x == "dark" else "☀️ Light",
    horizontal=True,
    key="theme_mode_radio",
)
st.session_state["theme_mode"] = theme_mode
if st.query_params.get("theme") != theme_mode:
  st.query_params["theme"] = theme_mode

_PALETTES = {
    "dark": {
        "bg-app": "#0a0d14",
        "bg-elevated": "#11151f",
        "bg-elevated-2": "#171c29",
        "bg-elevated-3": "#1f2532",
        "border": "#242b3a",
        "border-subtle": "#1a2030",
        "text-primary": "#eef1f7",
        "text-secondary": "#9aa3b8",
        "text-muted": "#6b7387",
        "accent": "#f97316",
        "accent-hover": "#fb923c",
        "accent-soft": "rgba(249, 115, 22, 0.14)",
        "accent-text": "#14100a",
        "shadow-card": "0 1px 2px rgba(0,0,0,.35), 0 8px 24px -14px rgba(0,0,0,.6)",
    },
    "light": {
        "bg-app": "#f4f5f7",
        "bg-elevated": "#ffffff",
        "bg-elevated-2": "#f1f2f5",
        "bg-elevated-3": "#e6e8ec",
        "border": "#dfe2e8",
        "border-subtle": "#e9ebef",
        "text-primary": "#181b23",
        "text-secondary": "#5b6270",
        "text-muted": "#868d9a",
        "accent": "#ea580c",
        "accent-hover": "#c2410c",
        "accent-soft": "rgba(234, 88, 12, 0.10)",
        "accent-text": "#ffffff",
        "shadow-card": "0 1px 2px rgba(20,20,30,.06), 0 8px 24px -16px rgba(20,20,30,.18)",
    },
}[theme_mode]

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* -----------------------------------------------------------------
       Design tokens — "Dark SaaS" system (Linear/Vercel-style neutrals +
       one ember-orange accent) with a light-mode variant. Values come
       from the _PALETTES dict above, picked by the sidebar's own
       theme_mode radio — NOT from config.toml (that only sets Streamlit's
       fixed startup default, it has no per-request switch). --border-
       start/-end map to the RTL/LTR side so a single rule set works in
       both directions instead of needing parallel ar/en CSS blocks like
       the old .report-card did.
       ----------------------------------------------------------------- */
    :root {{
        --bg-app: {_PALETTES['bg-app']};
        --bg-elevated: {_PALETTES['bg-elevated']};
        --bg-elevated-2: {_PALETTES['bg-elevated-2']};
        --bg-elevated-3: {_PALETTES['bg-elevated-3']};
        --border: {_PALETTES['border']};
        --border-subtle: {_PALETTES['border-subtle']};
        --text-primary: {_PALETTES['text-primary']};
        --text-secondary: {_PALETTES['text-secondary']};
        --text-muted: {_PALETTES['text-muted']};
        --accent: {_PALETTES['accent']};
        --accent-hover: {_PALETTES['accent-hover']};
        --accent-soft: {_PALETTES['accent-soft']};
        --accent-text: {_PALETTES['accent-text']};
        --success: #22c55e;
        --warning: #f59e0b;
        --danger: #ef4444;
        --info: #38bdf8;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --shadow-card: {_PALETTES['shadow-card']};
        --border-start: {"right" if rtl_direction == "rtl" else "left"};
        --border-end: {"left" if rtl_direction == "rtl" else "right"};
    }}

    /* Base / typography — background-color/color ARE forced here again
       (an in-between version of this file deliberately stopped doing
       that, on the mistaken belief it was blocking a native Streamlit
       theme switcher — see theme_mode's comment above for why that
       turned out to be wrong). Since our own toggle is now the one and
       only thing deciding light vs dark, forcing these from the palette
       is correct again, not a bug: without it the page shell would just
       sit on whatever Streamlit's fixed config.toml default renders,
       ignoring the toggle entirely.

       Known gap, stated plainly rather than glossed over: this repaints
       the page shell and every element this file styles directly, but a
       handful of Streamlit-internal widget innards that this file never
       targets with CSS (parts of the dataframe grid chrome, for one)
       have no rule tying them to the palette, so they stay on whatever
       config.toml's fixed base="dark" renders even after switching to
       light. Say if that remaining surface should be covered too. */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        direction: {rtl_direction};
        text-align: {text_align};
        background-color: var(--bg-app) !important;
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }}
    [data-testid="stHeader"] {{ background-color: transparent !important; }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }}
    p, span, label, div {{ font-family: 'Inter', sans-serif; }}

    /* Global text-color coverage for plain Streamlit widgets/markdown
       (main content area, not just the sidebar rule further down) — most
       of what determines whether the light variant is actually readable
       rather than just "the shell went light while the labels stayed
       dark-mode gray" again. Deliberately does NOT reach into the
       dataframe grid or chat-message internals (see the known-gap note
       above the :root block) — those remain unverified. */
    [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label,
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
    [data-testid="stRadio"] label p, [data-testid="stCheckbox"] label p {{
        color: var(--text-primary) !important;
    }}
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p, .stCaption {{
        color: var(--text-secondary) !important;
    }}
    /* Selectbox closed state + its open dropdown popover. Real selectors,
       checked live against fire-engine.maqaree.com's actual DOM — this
       Streamlit build renders selectboxes as react-aria ComboBoxes, not
       baseweb, so there's no [data-baseweb=...] anywhere in it; the
       group div directly under [data-testid="stSelectbox"] is what
       carries the visible background, and the open popover is a
       position:fixed portal element carrying its own
       data-testid="stSelectboxVirtualDropdown" (confirmed via
       getComputedStyle on the live page, not guessed). */
    [data-testid="stSelectbox"] div[role="group"] {{
        background-color: var(--bg-elevated-2) !important;
        border-color: var(--border) !important;
    }}
    [data-testid="stSelectbox"] input {{ color: var(--text-primary) !important; }}
    [data-testid="stSelectboxVirtualDropdown"] {{
        background-color: var(--bg-elevated-2) !important;
        border: 1px solid var(--border) !important;
    }}
    [data-testid="stSelectboxVirtualDropdown"] [role="option"] {{ color: var(--text-primary) !important; }}
    [data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover,
    [data-testid="stSelectboxVirtualDropdown"] [role="option"][aria-selected="true"] {{
        background-color: var(--bg-elevated-3) !important;
    }}
    /* File-upload dropzone — also unstyled before (not just wrong, simply
       never targeted), confirmed the same way. */
    [data-testid="stFileUploaderDropzone"] {{
        background-color: var(--bg-elevated-2) !important;
        border: 1px dashed var(--border) !important;
    }}
    [data-testid="stFileUploaderDropzone"] * {{ color: var(--text-secondary) !important; }}
    /* The dropzone's own "Upload" <button> (data-testid=stBaseButton-secondary)
       was still unstyled after the two rules above — verified live via
       getComputedStyle on the deployed site: while in LIGHT mode, it was
       rendering with background rgb(14,18,27) / border
       rgba(238,241,247,.2), i.e. Streamlit's stock DARK secondary-button
       colors baked into its own st-emotion-cache class, completely
       disconnected from our palette. The "*{{color:...}}" rule above only
       ever reached its text (that part WAS already correct), because a
       button's background/border aren't inherited the way color is and
       nothing was overriding Streamlit's own button background/border —
       hence a near-black button floating on a light dropzone. */
    [data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] {{
        background-color: var(--bg-elevated-3) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
    }}
    [data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"]:hover {{
        background-color: var(--accent-soft) !important;
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }}
    [data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] * {{
        color: inherit !important;
    }}

    /* Scrollbar — small SaaS-y touch */
    ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    ::-webkit-scrollbar-track {{ background: var(--bg-app); }}
    ::-webkit-scrollbar-thumb {{ background: var(--bg-elevated-3); border-radius: 8px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--border); }}

    /* -------------------- Sidebar -------------------- */
    [data-testid="stSidebar"] {{
        background-color: var(--bg-elevated) !important;
        border-{"left" if rtl_direction == "rtl" else "right"}: 1px solid var(--border-subtle);
    }}
    [data-testid="stSidebar"] > div {{ padding-top: 0.5rem; }}

    .brand-block {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px 4px 18px 4px;
        margin-bottom: 10px;
        border-bottom: 1px solid var(--border-subtle);
    }}
    .brand-icon {{
        width: 40px; height: 40px;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px;
        background: var(--accent-soft);
        border: 1px solid rgba(249, 115, 22, 0.35);
        border-radius: var(--radius-md);
        flex-shrink: 0;
    }}
    .brand-name {{ font-size: 16px; font-weight: 800; color: var(--text-primary); line-height: 1.2; }}
    .brand-tagline {{ font-size: 11px; color: var(--text-muted); line-height: 1.3; }}

    .user-block {{
        background: var(--bg-elevated-2);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 10px 12px;
        margin-bottom: 14px;
    }}
    .user-block .u-name {{ font-size: 13px; font-weight: 600; color: var(--text-primary); }}
    .user-block .u-role {{
        display: inline-block;
        margin-top: 4px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.04em;
        color: var(--accent);
        background: var(--accent-soft);
        padding: 2px 8px;
        border-radius: 999px;
    }}

    /* Sidebar nav rendered via st.sidebar.radio — restyled from radio
       buttons into a vertical pill nav. Scoped to .st-key-nav_radio_wrap
       (see that container's key= above) rather than every sidebar radio
       — the theme_mode toggle is also a st.sidebar.radio() and shares
       the same data-testid, so an unscoped rule here would wrongly force
       its compact horizontal layout into this same full-width pill list.
       :has() is supported in every Chromium-based browser Streamlit apps
       are realistically viewed in. */
    .st-key-nav_radio_wrap [data-testid="stRadio"] > label {{ display: none; }}
    .st-key-nav_radio_wrap [data-testid="stRadio"] [role="radiogroup"] {{
        gap: 4px;
    }}
    .st-key-nav_radio_wrap [data-testid="stRadio"] label {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: var(--radius-sm);
        padding: 9px 12px;
        margin-bottom: 2px;
        width: 100%;
        transition: background .12s ease, border-color .12s ease;
    }}
    .st-key-nav_radio_wrap [data-testid="stRadio"] label:hover {{
        background: var(--bg-elevated-2);
    }}
    .st-key-nav_radio_wrap [data-testid="stRadio"] label:has(input:checked) {{
        background: var(--accent-soft);
        border-color: rgba(249, 115, 22, 0.35);
    }}
    .st-key-nav_radio_wrap [data-testid="stRadio"] label:has(input:checked) p {{
        color: var(--accent) !important;
        font-weight: 600;
    }}
    /* Hides just the decorative radio bullet, not the option text. This
       went through TWO wrong depths before landing here, both caught
       live rather than shipped blind:
         - attempt 1 (`label > div:first-child`) matched nothing — no
           element that shallow exists.
         - attempt 2 (`> div > div:first-child`) matched the CONTENT ROW
           itself (bullet + text together as one flex item), not the
           bullet alone — display:none on it collapsed the whole option
           to 0×0, which is why the nav pills vanished into a stray empty
           blob after shipping that version (caught from the user's own
           screenshot, then reproduced and root-caused live: the row's
           child count dropped from 2 to 1 and the text node's own
           getBoundingClientRect() was 0×0 even though it was still
           `display:block` in the DOM).
       Real structure is one level deeper: [data-testid="stRadioOption"]
       > div (content wrapper) > div (content ROW, flex) > div:first-child
       is the bullet-only branch; [data-testid="stMarkdownContainer"] is
       that row's second child and is untouched. Confirmed via
       getBoundingClientRect() showing real width/height again, not just
       by eye. The native <input type="radio"> is separately already
       screen-reader-only (Streamlit hides it itself via a clip-rect
       span) — it was never the visible bullet, which is also why an
       `accent-color` approach couldn't have worked here either. */
    .st-key-nav_radio_wrap [data-testid="stRadioOption"] > div > div > div:first-child {{ display: none; }}
    /* (The theme_mode/language controls above the nav get their text
       color from the global stWidgetLabel/stRadio rule further up —
       no sidebar-specific duplicate needed here.) */

    /* -------------------- Buttons -------------------- */
    [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button,
    [data-testid="stDownloadButton"] button {{
        background: var(--accent) !important;
        color: var(--accent-text) !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: background .12s ease, transform .08s ease !important;
        box-shadow: none !important;
    }}
    [data-testid="stButton"] button:hover, [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stDownloadButton"] button:hover {{
        background: var(--accent-hover) !important;
        color: var(--accent-text) !important;
    }}
    [data-testid="stButton"] button:active, [data-testid="stFormSubmitButton"] button:active {{
        transform: scale(0.98);
    }}
    [data-testid="stSidebar"] [data-testid="stButton"] button {{
        background: transparent !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border) !important;
        font-weight: 500 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover {{
        background: rgba(239, 68, 68, 0.1) !important;
        color: var(--danger) !important;
        border-color: rgba(239, 68, 68, 0.4) !important;
    }}

    /* -------------------- Inputs -------------------- */
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input {{
        background-color: var(--bg-elevated-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
    }}
    /* The eye icon / show-password button that sits next to a password
       input — same treatment so it doesn't stay on the old fixed dark
       colors while the field itself follows the palette. */
    [data-testid="stTextInput"] button {{
        background-color: var(--bg-elevated-2) !important;
        color: var(--text-secondary) !important;
        border-color: var(--border) !important;
    }}
    [data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
    }}

    /* -------------------- Cards: metric + report -------------------- */
    .metric-card {{
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 16px 18px;
        text-align: {text_align};
        box-shadow: var(--shadow-card);
        position: relative;
        overflow: hidden;
    }}
    .metric-card::before {{
        content: "";
        position: absolute;
        top: 0; {border_side.split("-")[1]}: 0;
        width: 3px; height: 100%;
        background: var(--accent);
        opacity: 0.7;
    }}
    .metric-value {{
        font-size: 22px;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1.2;
    }}
    .metric-label {{
        font-size: 12.5px;
        color: var(--text-secondary);
        margin-top: 4px;
    }}
    .report-card {{
        background-color: var(--bg-elevated);
        {border_side}: 3px solid var(--accent);
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: var(--radius-sm);
        font-size: 14px;
        color: var(--text-primary);
        line-height: 1.6;
        text-align: {text_align};
        direction: {rtl_direction};
        border-top: 1px solid var(--border-subtle);
        border-bottom: 1px solid var(--border-subtle);
        border-{("right" if rtl_direction == "rtl" else "left")}: 1px solid var(--border-subtle);
    }}

    /* -------------------- Page header banner -------------------- */
    .page-header {{
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 18px 20px;
        margin-bottom: 18px;
        background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-elevated-2) 100%);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
    }}
    .page-header .ph-icon {{
        width: 44px; height: 44px;
        display: flex; align-items: center; justify-content: center;
        font-size: 22px;
        background: var(--accent-soft);
        border-radius: var(--radius-md);
        flex-shrink: 0;
    }}
    .page-header .ph-title {{ font-size: 21px; font-weight: 800; color: var(--text-primary); line-height: 1.25; }}
    .page-header .ph-subtitle {{ font-size: 13px; color: var(--text-secondary); margin-top: 2px; }}

    /* -------------------- Auth card -------------------- */
    .st-key-login_card {{
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-lg) !important;
        padding: 20px 24px !important;
        box-shadow: var(--shadow-card);
    }}

    /* -------------------- Expanders -------------------- */
    div[data-testid="stExpander"] {{
        text-align: {text_align};
        direction: {rtl_direction};
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        overflow: hidden;
    }}
    div[data-testid="stExpander"] summary {{
        font-weight: 600 !important;
    }}
    div[data-testid="stExpander"] summary:hover {{
        background: var(--bg-elevated-2);
    }}

    /* -------------------- Alerts -------------------- */
    [data-testid="stAlert"] {{
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-subtle) !important;
    }}

    /* -------------------- DataFrame / chat -------------------- */
    /* overflow:hidden here (added for the rounded-corner card look) was
       the actual cause of the dataframe's hover toolbar (maximize /
       download-as-CSV / search) disappearing — live-verified via DOM
       inspection: Streamlit renders that toolbar
       (data-testid="stElementToolbar") as a child of THIS element,
       absolutely positioned at top:-16px so it floats just above the
       grid's top-right corner. With overflow:hidden, that negative
       offset put it entirely outside the clipped box, so it was never
       paintable — not even on hover (opacity was toggling to 1
       correctly, it just had nowhere visible to render). Dropped
       overflow:hidden to get the toolbar back; border-radius alone still
       rounds the container, it just no longer clips content that
       intentionally pokes above it. */
    [data-testid="stDataFrame"] {{
        border-radius: var(--radius-md);
        border: 1px solid var(--border-subtle);
    }}
    /* Three more dataframe-adjacent pieces live-found the same way as the
       toolbar/canvas issues above — all real DOM (not canvas), so unlike
       the grid cells themselves these CAN be reached, they just never
       had a rule targeting them before: each one was rendering with
       Streamlit's own config.toml-baked dark colors (background
       rgb(10,13,20) / text rgb(238,241,247), i.e. our OWN dark palette's
       exact bg-app/text-primary values, since config.toml's dark theme
       and our dark palette were deliberately kept in sync — so this was
       invisible in dark mode and only showed up as a black patch once
       light mode existed):
       1) stFullScreenFrame — the backdrop behind a dataframe expanded to
          fullscreen (⤢ in the toolbar). This is what showed as a solid
          black page behind an otherwise-correctly-light table.
       2) .gdg-search-bar / [data-testid="search-input"] — the inline
          search box the 🔍 toolbar button opens (glide-data-grid's own
          markup, not a Streamlit data-testid, but a stable library class
          name).
       3) stDataFrameColumnVisibilityMenu — the "Show/hide columns" (☰)
          panel. */
    [data-testid="stFullScreenFrame"] {{
        background-color: var(--bg-app) !important;
    }}
    .gdg-search-bar {{
        background-color: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
    }}
    [data-testid="search-input"] {{
        background-color: var(--bg-elevated-2) !important;
        color: var(--text-primary) !important;
    }}
    [data-testid="stDataFrameColumnVisibilityMenu"] {{
        background-color: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
    }}
    [data-testid="stDataFrameColumnVisibilityMenu"] * {{
        color: var(--text-primary) !important;
    }}
    [data-testid="stChatMessage"] {{
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
    }}

    /* -------------------- Misc -------------------- */
    [data-testid="stDivider"], hr {{ border-color: var(--border-subtle) !important; }}
    </style>
""",
    unsafe_allow_html=True,
)


def render_brand():
  """Sidebar brand block — icon + name + tagline, read from the BRAND_*
  constants near the top of this file so swapping in a real logo/name
  later is a one-line change instead of hunting through markup."""
  st.sidebar.markdown(
      f"""<div class="brand-block">
          <div class="brand-icon">{BRAND_ICON}</div>
          <div>
              <div class="brand-name">{BRAND_NAME}</div>
              <div class="brand-tagline">{BRAND_TAGLINE}</div>
          </div>
      </div>""",
      unsafe_allow_html=True,
  )


def _themed_df(dataframe):
  """st.dataframe() renders through glide-data-grid onto an HTML5
  <canvas> — confirmed live via getComputedStyle/pixel-sampling on the
  deployed site: it stayed dark (rgb ~10,13,20 header / ~33,37,43 body)
  even in "light" mode, and even after forcing Streamlit's OWN native
  theme (its real internal theme, independent of our CSS toggle, tracked
  client-side under the localStorage key "stActiveTheme-/-v2") to
  "Light" and reloading — because none of our injected <style> CSS can
  reach canvas pixels at all, and this app's config.toml pins a single
  fixed base="dark" Streamlit theme at server startup, so the canvas
  never got repainted regardless of which theme was requested.
  The one thing that DOES reach it: pandas Styler's background-color /
  color, which Streamlit's dataframe renderer honors per cell (confirmed
  against streamlit/streamlit#10768 — "background-color" works, only the
  "background" shorthand doesn't). This paints the BODY cells to match
  our active palette. It can NOT reach the header row — st.dataframe's
  header color has no Styler hook at all (streamlit/streamlit#6958 is
  the open issue tracking that as a real product gap in Streamlit
  itself, not something we can style around from here) — the header
  stays a fixed dark strip. The only way to also theme the header is
  dropping st.dataframe for st.table()/a raw HTML table, which loses the
  built-in search / CSV-export / fullscreen toolbar entirely — not done
  here since that trade-off wasn't asked for."""
  return dataframe.style.set_properties(**{
      "background-color": _PALETTES["bg-elevated"],
      "color": _PALETTES["text-primary"],
  })


def render_page_header(icon: str, title: str, subtitle: str = ""):
  """Replaces the old bare st.title()/st.caption() pair with a bannered
  header card, consistent across all three views.

  Live-root-caused bug fix: the User Management page (the one call site
  that passes no `subtitle`) was rendering a literal "</div></div>" text
  artifact instead of a header. Confirmed via direct DOM inspection on the
  deployed site — the escaped text sat inside a stCode/stMarkdownPre
  element (a Markdown "indented code block"), nested INSIDE .page-header.
  Root cause: the old version built the HTML as a multi-line f-string
  with each line indented to match the surrounding Python source, and put
  the conditional subtitle fragment on its own line —
  `{f'<div class="ph-subtitle">...' if subtitle else ''}`. When subtitle
  is "" (only the Users page call), that line evaluates to an empty
  string, leaving a bare blank line in the middle of the template.
  CommonMark's HTML-block rule passes an HTML block through verbatim only
  until the first blank line; that blank line ended the block early, so
  the final two "</div>" lines — both indented 4+ spaces to match the
  Python source — were re-parsed as a new block and, being indented 4+
  spaces, treated as a plain Markdown indented code block instead of raw
  HTML. The other two call sites (which do pass a subtitle) never hit
  this because they never produce a blank line. Fix: build the whole
  fragment as a single unbroken line with no interior newlines at all, so
  there is no line for CommonMark to treat as blank or indented,
  regardless of which branch subtitle takes."""
  subtitle_html = f'<div class="ph-subtitle">{subtitle}</div>' if subtitle else ''
  st.markdown(
      f'<div class="page-header"><div class="ph-icon">{icon}</div>'
      f'<div><div class="ph-title">{title}</div>{subtitle_html}</div></div>',
      unsafe_allow_html=True,
  )

# ---------------------------------------------------------
# Authentication State Management
# ---------------------------------------------------------
# IMPORTANT: st.session_state lives only in the in-memory Python session
# tied to the current browser WebSocket connection. A hard refresh (F5)
# opens a brand-new connection, so Streamlit always starts a fresh
# session_state on refresh — this is a Streamlit platform behavior, not a
# bug you can fix by changing how session_state is initialized. The fix is
# to keep something that DOES survive a refresh (the URL's query string)
# and use it to silently restore the session instead of showing the login
# screen again.
#
# On successful login we stash the JWT in st.query_params. On every load,
# before deciding whether to show the login screen, we check for that
# token and — if present — verify it against GET /auth/me (so a tampered
# or expired token in the URL still can't grant access; the backend
# re-validates the JWT signature and expiry every time).
if "authenticated" not in st.session_state:
  st.session_state["authenticated"] = False
if "auth_token" not in st.session_state:
  st.session_state["auth_token"] = None
if "user_info" not in st.session_state:
  st.session_state["user_info"] = {}


def _restore_session_from_url():
  """Try to re-authenticate using the token carried in the page URL, so a
  browser refresh doesn't bounce the user back to the login screen."""
  if st.session_state["authenticated"]:
    return

  url_token = st.query_params.get("token")
  if not url_token:
    return

  try:
    res = requests.get(
        f"{BASE_API_URL}/auth/me",
        headers={"Authorization": f"Bearer {url_token}"},
        timeout=10,
    )
    if res.status_code == 200:
      data = res.json()
      st.session_state["authenticated"] = True
      st.session_state["auth_token"] = url_token
      st.session_state["user_info"] = {
          "username": data["username"],
          "role": data["role"],
      }
    else:
      # Token expired/invalid — drop it from the URL and fall through to
      # login, but keep the "theme" param (added alongside "token" above)
      # so an expired session doesn't also silently reset the user's
      # light/dark choice back to dark.
      _kept_theme = st.query_params.get("theme")
      st.query_params.clear()
      if _kept_theme:
        st.query_params["theme"] = _kept_theme
  except Exception:
    # Backend unreachable right now — leave the token in the URL and let
    # the user retry; don't force a fresh login just because of a blip.
    pass


_restore_session_from_url()


def login_screen():
  st.markdown("<div style='height: 6vh;'></div>", unsafe_allow_html=True)

  col_a, col_b, col_c = st.columns([1, 2, 1])
  with col_b:
    st.markdown(
        f"""<div style="text-align:center; margin-bottom: 22px;">
            <div class="brand-icon" style="width:56px;height:56px;font-size:28px;margin:0 auto 12px auto;">{BRAND_ICON}</div>
            <div style="font-size:22px;font-weight:800;color:var(--text-primary);">{BRAND_NAME}</div>
            <div style="font-size:13px;color:var(--text-secondary);margin-top:2px;">{BRAND_TAGLINE}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    # key="login_card" gives this container the CSS class .st-key-login_card
    # (Streamlit 1.37+), which the injected <style> block above targets to
    # render it as a proper bordered/elevated card instead of a bare form
    # floating on the page background.
    with st.container(key="login_card", border=True):
      # Note: padding here comes from .st-key-login_card in the injected
      # CSS above, not from a hand-nested <div> — st.markdown() calls each
      # render as an independent HTML fragment, so opening a <div> in one
      # call and closing it in a later call does NOT actually wrap the
      # Streamlit widgets rendered in between (a common Streamlit CSS
      # pitfall); the sanitizer just auto-closes/strips the dangling tags.
      st.subheader(t["login_title"])
      st.caption(t["login_caption"])
      with st.form("login_form"):
        username = st.text_input(t["username"])
        password = st.text_input(t["password"], type="password")
        submit = st.form_submit_button(t["login_btn"], width='stretch')

      if submit:
        try:
          res = requests.post(
              f"{BASE_API_URL}/auth/login",
              data={"username": username, "password": password},
              timeout=10,
          )
          if res.status_code == 200:
            data = res.json()
            st.session_state["authenticated"] = True
            st.session_state["auth_token"] = data["access_token"]
            st.session_state["user_info"] = {
                "username": data["username"],
                "role": data["role"],
            }
            # Carry the token in the URL so a refresh can restore the
            # session via _restore_session_from_url() above.
            st.query_params["token"] = data["access_token"]
            st.success(t["login_success"])
            st.rerun()
          else:
            st.error(t["login_error"])
        except Exception as e:
          st.error(f"{t['login_conn_error']} {e}")


if not st.session_state["authenticated"]:
  login_screen()
  st.stop()


# ---------------------------------------------------------
# Helper Functions: Generate Real Word Document (.docx)
# ---------------------------------------------------------
def create_word_report(filename, pages_notes, df_components=None):
  doc = Document()
  title = doc.add_heading("EXECUTIVE ENGINEERING AUDIT REPORT", level=0)
  title.runs[0].font.color.rgb = RGBColor(0x1F, 0x4E, 0x78)

  p_meta = doc.add_paragraph()
  p_meta.add_run("Project File: ").bold = True
  p_meta.add_run(f"{filename}\n")
  p_meta.add_run("Audit Date: ").bold = True
  p_meta.add_run(f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")

  doc.add_heading("1. Technical Observations & Findings", level=1)
  for page_name, notes in pages_notes.items():
    doc.add_heading(f"📍 {page_name}", level=2)
    for idx, note in enumerate(notes, 1):
      doc.add_paragraph(f"{idx}. {note}", style="List Bullet")

  doc.add_heading("2. Action Items & Recommendations", level=1)
  doc.add_paragraph(
      "Field verification required for low-resolution symbol counts.",
      style="List Bullet",
  )
  doc.add_paragraph(
      "Cross-reference IT Server Room scopes with specialized fire suppression"
      " schematics.",
      style="List Bullet",
  )
  doc.add_paragraph(
      "Obtain scaled CAD/DWG drawings for precise conduit routing"
      " measurement.",
      style="List Bullet",
  )

  target_stream = io.BytesIO()
  doc.save(target_stream)
  return target_stream.getvalue()


def render_usage_metric_card(analysis: dict):
  """Show the estimated AI cost/token usage for this analysis, so the
  provider comparison (Claude vs Gemini vs Groq) has a number to compare
  on, not just a gut feeling about how expensive a run "felt"."""
  usage = analysis.get("usage_summary")
  if not usage:
    return
  cost = usage.get("total_cost_usd", 0.0) or 0.0
  in_tok = usage.get("total_input_tokens", 0) or 0
  out_tok = usage.get("total_output_tokens", 0) or 0
  provider_label = (usage.get("model") or usage.get("provider") or "").strip()
  st.markdown(
      f"""<div class="metric-card">
          <div class="metric-value">${cost:.4f}</div>
          <div class="metric-label">{t['estimated_api_cost']}
              ({in_tok:,} in / {out_tok:,} out{' · ' + provider_label if provider_label else ''})</div>
      </div>""",
      unsafe_allow_html=True,
  )


# ---------------------------------------------------------
# Navigation & Sidebar
# ---------------------------------------------------------
render_brand()

st.sidebar.markdown(
    f"""<div class="user-block">
        <div class="u-name">👤 {st.session_state['user_info'].get('username', 'User')}</div>
        <span class="u-role">{st.session_state['user_info'].get('role', 'Engineer').upper()}</span>
    </div>""",
    unsafe_allow_html=True,
)

if st.sidebar.button(t["logout"], width='stretch'):
  st.session_state["authenticated"] = False
  st.session_state["auth_token"] = None
  st.session_state["user_info"] = {}
  # Keep "theme" (see the theme_mode block above) — logging out shouldn't
  # also silently flip the user back to dark mode.
  _kept_theme = st.query_params.get("theme")
  st.query_params.clear()
  if _kept_theme:
    st.query_params["theme"] = _kept_theme
  st.rerun()

st.sidebar.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
# key="nav_radio_wrap" (Streamlit 1.37+) gives this container the CSS
# class .st-key-nav_radio_wrap, which the injected <style> block scopes
# the "hide the circle, render as full-width pills" rules to — WITHOUT
# this wrapper, those rules matched every st.sidebar.radio() by its
# generic data-testid, including the theme_mode toggle above, and would
# have squashed its compact horizontal Dark/Light control into the same
# full-width block-pill layout meant for this nav list.
with st.sidebar.container(key="nav_radio_wrap"):
  navigation = st.radio(
      t["nav_title"],
      [
          t["nav_new"],
          t["nav_archive"],
          t["nav_users"],
      ],
  )

# Session State Initializations
if "boq_data" not in st.session_state:
  st.session_state["boq_data"] = None
if "current_file" not in st.session_state:
  st.session_state["current_file"] = None
if "generated_pdf_bytes" not in st.session_state:
  st.session_state["generated_pdf_bytes"] = None
if "rendered_img_cache" not in st.session_state:
  st.session_state["rendered_img_cache"] = {}
if "session_id" not in st.session_state:
  st.session_state["session_id"] = str(uuid.uuid4())[:8]

# Archive View Dynamic Image Caching
if "archived_pdf_bytes" not in st.session_state:
  st.session_state["archived_pdf_bytes"] = None
if "archived_img_cache" not in st.session_state:
  st.session_state["archived_img_cache"] = {}
if "selected_archived_id" not in st.session_state:
  st.session_state["selected_archived_id"] = None

# ---------------------------------------------------------
# VIEW 1: 🚀 ANALYZE NEW DRAWING
# ---------------------------------------------------------
if navigation == t["nav_new"]:
  render_page_header("🚀", t["title"], t["caption"])

  # AI Engines Selection
  col_s1, col_s2, col_s3 = st.columns(3)
  with col_s1:
    ai_provider = st.selectbox(
        t["ai_engine"],
        options=["gemini", "claude", "groq", "openrouter"],
        index=1,
        format_func=lambda x: {
            "gemini": "Google Gemini 3.7 Flash 🌟",
            # Matches app/services/claude_service.py's CLAUDE_MODEL default
            # (claude-fable-5) — keep these in sync if that default changes.
            # (A same-day experiment routed this through OpenRouter to the
            # cheaper claude-sonnet-5 instead — reverted: OpenRouter charges
            # the identical list price for claude-fable-5 itself, so there
            # was no cost saving to be had here without also taking on
            # Sonnet's documented zero-component failure on this project's
            # real drawings. See process.py's PROVIDER_SERVICES comment.)
            "claude": "Anthropic Claude Fable 5 🧠",
            "groq": "Groq (Qwen3.6 27B - Alibaba) ⚡",
            "openrouter": "OpenRouter (pick any model) 🔀",
        }[x],
    )
    if ai_provider == "groq":
      # Qwen3.6-27B is currently the ONLY vision-capable model on Groq —
      # checked directly against Groq's docs (Aug 2026). The two
      # alternatives that used to exist (Llama 4 Maverick / Scout, both
      # from Meta) were deprecated by Groq in March and July 2026, and
      # Groq's own suggested replacement (gpt-oss-120b) is text-only, so
      # there is currently no non-Qwen vision option on this provider.
      # Surfacing this in the UI rather than hiding it, per team decision.
      st.caption(
          "⚠️ حاليًا هذا هو موديل الرؤية الوحيد المتاح على Groq (لا يوجد"
          " بديل آخر يدعم قراءة الصور على هذه المنصة حاليًا) — راجع النتائج"
          " بعناية أكبر مقارنة بكلود وجيمناي."
      )

    # OpenRouter is a router in front of hundreds of models, not one fixed
    # model like the other three engines — so instead of a single caption
    # it gets its own model picker. Curated list checked directly against
    # OpenRouter's live catalog (openrouter.ai/api/v1/models) on
    # 2026-08-17 — a first draft of this list used remembered ids like
    # "openai/gpt-4o" and "anthropic/claude-sonnet-4.5" that turned out to
    # already be gone from OpenRouter entirely, so don't re-add
    # from-memory ids here without checking the live catalog first.
    #
    # Deliberately NO Google/Gemini or Anthropic/Claude models in this list
    # — this project already has dedicated "gemini" and "claude" providers
    # calling those model families directly, so an OpenRouter route to the
    # same vendors would just be redundant. This list is for trying
    # something actually different. Default (index 0) is
    # thinkingmachines/inkling — see OPENROUTER_MODEL's comment in
    # openrouter_service.py for the full reasoning (native multimodal
    # architecture, worth testing empirically since no independent
    # OCR benchmark exists for it yet) and for why qwen3.7-flash and
    # grok-4.6 were considered and passed over.
    # "Custom" drops to a free-text box for anything not listed, sent
    # as-is to OpenRouter.
    openrouter_model = None
    if ai_provider == "openrouter":
      _OPENROUTER_PRESETS = [
          "thinkingmachines/inkling",
          "moonshotai/kimi-k3",
          "qwen/qwen3.8-27b",
          "meta/muse-glimmer-30b",
          "openai/gpt-5.6-sol",
          "x-ai/grok-4.6",
          "custom",
      ]
      preset_choice = st.selectbox(
          "OpenRouter Model",
          options=_OPENROUTER_PRESETS,
          index=0,
          format_func=lambda x: (
              "Custom model id…" if x == "custom"
              else f"{x} ⭐ (فنانة — تستاهل التجربة)" if x == "thinkingmachines/inkling"
              else x
          ),
      )
      if preset_choice == "custom":
        openrouter_model = st.text_input(
            "Custom OpenRouter model id",
            placeholder="e.g. mistralai/pixtral-large-2411",
            help=(
                "Must be a vision-capable model on OpenRouter — text-only"
                " models will reject the image and this page will come"
                " back empty. Browse openrouter.ai/models and filter by"
                " 'Input Modalities: Image' to confirm before pasting an"
                " id here."
            ),
        ).strip()
      else:
        openrouter_model = preset_choice
      st.caption(
          "⚠️ القائمة أعلاه مجرد نقطة بداية وليست كل الموديلات المتاحة —"
          " تأكد أن الموديل يدعم قراءة الصور (Vision) قبل استخدامه."
          " thinkingmachines/inkling معماريته تقرأ الصور كـ patches جوه"
          " الـ transformer مباشرة، بس مفيش benchmark مستقل لدقة الـ OCR"
          " بتاعه لحد دلوقتي — عشان كده أنسب حاجة إننا نجربه فعليًا على"
          " مخططاتنا ونشوف النتيجة."
      )
  with col_s2:
    ai_report_type = st.selectbox(
        t["report_type"],
        options=["security", "fire"],
        index=1,
        format_func=lambda x: {
            "security": t["security_sys"],
            "fire": t["fire_sys"],
        }[x],
    )
  with col_s3:
    unit = st.selectbox(t["unit"], options=["cm", "inch", "m"], index=0)

  uploaded_file = st.file_uploader(
      t["upload_label"], type=["pdf", "dxf", "dwg"]
  )

  if uploaded_file is not None:
    if st.session_state["current_file"] != uploaded_file.name:
      st.session_state["boq_data"] = None
      st.session_state["generated_pdf_bytes"] = None
      st.session_state["rendered_img_cache"] = {}
      st.session_state["current_file"] = uploaded_file.name
      st.session_state["session_id"] = str(uuid.uuid4())[:8]
      # New file → new session_id → the old chat thread (keyed by the
      # previous session_id, see the "chat about this drawing" section
      # below) no longer applies. Nothing to explicitly clear here since
      # the key itself changes with session_id, but resetting
      # current_file/session_id together keeps that invariant obvious.

    col1, col2 = st.columns([1.2, 1], gap="medium")
    file_ext = uploaded_file.name.split(".")[-1].lower()

    # Left Column: Interactive Drawing View
    with col1:
      st.subheader(t["preview_header"])

      if file_ext in ["dxf", "dwg"]:
        dxf_bytes = None
        if file_ext == "dwg":
          with st.spinner(t["converting_dwg"]):
            try:
              files = {
                  "file": (
                      uploaded_file.name,
                      uploaded_file.getvalue(),
                      "application/octet-stream",
                  )
              }
              res = requests.post(
                  f"{BASE_API_URL}/extract/convert-dwg-to-dxf",
                  files=files,
                  timeout=600,
              )
              if res.status_code == 200:
                dxf_bytes = res.content
              else:
                st.error(f"{t['conversion_failed']} {res.status_code}")
            except Exception as e:
              st.error(f"{t['conversion_conn_err']} {e}")
        else:
          dxf_bytes = uploaded_file.getvalue()

        if dxf_bytes:
          with tempfile.NamedTemporaryFile(
              suffix=".dxf", delete=False
          ) as tmp_file:
            tmp_file.write(dxf_bytes)
            tmp_path = tmp_file.name

          try:
            try:
              doc = ezdxf.readfile(tmp_path)
            except Exception:
              doc, auditor = recover.readfile(tmp_path)

            if doc:
              msp = doc.modelspace()
              # NOTE: deliberately left hardcoded to "#0e1117" here, unlike
              # the plotly letterbox fix right below — this facecolor is
              # the actual background ezdxf draws the CAD entities onto,
              # not just page chrome. Standard AutoCAD/DXF convention
              # draws entities in white/light colors meant for a dark
              # viewport; flipping this to a light color in light mode
              # risks white-on-white invisible linework, which is a real
              # regression risk I haven't verified against an actual DXF
              # file. Only the plotly figure's own blank-margin background
              # (below) was changed — that's just letterboxing around the
              # already-rendered image, safe regardless of the drawing's
              # own stroke colors.
              fig, ax = plt.subplots(
                  figsize=(12, 10), dpi=200, facecolor="#0e1117"
              )
              ax.set_facecolor("#0e1117")

              ctx = RenderContext(doc)
              out = MatplotlibBackend(ax)
              Frontend(ctx, out).draw_layout(msp, finalize=True)

              buf = io.BytesIO()
              fig.savefig(
                  buf,
                  format="png",
                  bbox_inches="tight",
                  facecolor="#0e1117",
                  edgecolor="none",
              )

              pdf_buffer = io.BytesIO()
              fig.savefig(
                  pdf_buffer,
                  format="pdf",
                  bbox_inches="tight",
                  facecolor="#0e1117",
              )
              st.session_state["generated_pdf_bytes"] = pdf_buffer.getvalue()
              plt.close(fig)

              buf.seek(0)
              img_arr = plt.imread(buf)
              if img_arr.max() <= 1.0:
                img_arr = (img_arr * 255).astype(np.uint8)

              plotly_fig = px.imshow(img_arr)
              plotly_fig.update_layout(
                  margin=dict(l=0, r=0, t=0, b=0),
                  # Was hardcoded to "#0e1117" (Streamlit's own stock dark
                  # background) since before the redesign — a Plotly
                  # figure's colors are baked into the chart at creation
                  # time in Python, so unlike a native Streamlit widget
                  # this was never going to pick up our CSS-based
                  # light/dark toggle on its own; it just silently stayed
                  # black in light mode too. Using the active palette's
                  # own elevated-surface color instead of a fixed value
                  # makes this letterboxed area track the toggle like
                  # everything else.
                  paper_bgcolor=_PALETTES["bg-elevated"],
                  plot_bgcolor=_PALETTES["bg-elevated"],
                  xaxis=dict(
                      showgrid=False, zeroline=False, showticklabels=False
                  ),
                  yaxis=dict(
                      showgrid=False, zeroline=False, showticklabels=False
                  ),
                  dragmode="pan",
              )
              st.caption(t["zoom_hint"])
              st.plotly_chart(
                  plotly_fig, width='stretch', config={"scrollZoom": True}
              )
          finally:
            if os.path.exists(tmp_path):
              os.remove(tmp_path)

      elif file_ext == "pdf":
        try:
          if (
              "generated_pdf_bytes" not in st.session_state
              or st.session_state["generated_pdf_bytes"] is None
          ):
            st.session_state["generated_pdf_bytes"] = uploaded_file.getvalue()

          doc = fitz.open(
              stream=st.session_state["generated_pdf_bytes"], filetype="pdf"
          )
          total_pages = len(doc)

          sub_col1, sub_col2 = st.columns([1, 1])
          with sub_col1:
            page_num = st.number_input(
                t["page_num"],
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1,
            )
          with sub_col2:
            dpi_val = st.select_slider(
                t["dpi_label"], options=[100, 150, 200, 300], value=150
            )

          cache_key = f"{page_num}_{dpi_val}"
          if cache_key not in st.session_state["rendered_img_cache"]:
            page = doc.load_page(page_num - 1)
            pix = page.get_pixmap(dpi=dpi_val)
            img_data = pix.tobytes("png")

            img_arr = plt.imread(io.BytesIO(img_data))
            if img_arr.max() <= 1.0:
              img_arr = (img_arr * 255).astype(np.uint8)

            st.session_state["rendered_img_cache"][cache_key] = img_arr

          img_arr = st.session_state["rendered_img_cache"][cache_key]
          plotly_fig = px.imshow(img_arr)
          plotly_fig.update_layout(
              margin=dict(l=0, r=0, t=0, b=0),
              # See the matching comment on the DXF-preview version of this
              # call above — was hardcoded to Streamlit's old dark default,
              # never touched by the theme_mode toggle since a plotly
              # figure's colors are set once in Python, not via CSS.
              paper_bgcolor=_PALETTES["bg-elevated"],
              plot_bgcolor=_PALETTES["bg-elevated"],
              xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
              yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
              dragmode="pan",
          )
          st.caption(t["zoom_hint"])
          st.plotly_chart(
              plotly_fig, width='stretch', config={"scrollZoom": True}
          )
          doc.close()
        except Exception as e:
          st.error(f"Error rendering PDF: {e}")

    # Right Column: BOQ Results
    with col2:
      st.subheader(t["boq_header"])
      pdf_to_send = st.session_state.get("generated_pdf_bytes")

      if pdf_to_send:
        if st.button(t["btn_analyze"], type="primary", width='stretch'):
          status_container = st.status(
              t["analyzing"],
              expanded=True,
          )

          with status_container:
            st_text = st.empty()
            progress_bar = st.progress(0)

            try:
              base_name = uploaded_file.name.rsplit(".", 1)[0]
              files = {
                  "file": (f"{base_name}.pdf", pdf_to_send, "application/pdf")
              }
              data = {"session_id": st.session_state["session_id"]}
              params = {"provider": ai_provider, "report_type": ai_report_type}
              if ai_provider == "openrouter" and openrouter_model:
                params["model"] = openrouter_model

              res = requests.post(
                  f"{BASE_API_URL}/extract/pdf-boq",
                  files=files,
                  data=data,
                  params=params,
                  stream=True,
                  timeout=1800,
              )

              if res.status_code == 200:
                for line in res.iter_lines():
                  if line:
                    decoded_line = line.decode("utf-8")
                    try:
                      msg = json.loads(decoded_line)
                      if msg.get("status") == "progress":
                        current_p = msg.get("current_page", 0)
                        total_p = msg.get("total_pages", 1)
                        percent = int((current_p / total_p) * 100)
                        progress_bar.progress(percent)
                        st_text.write(
                            f"{t['page_inspect']} {current_p} {t['of_page']} {total_p}"
                            f" ({percent}%)..."
                        )

                      elif msg.get("status") == "completed":
                        progress_bar.progress(100)
                        status_container.update(
                            label=t["completed_status"], state="complete"
                        )
                        st.session_state["boq_data"] = msg.get("data")

                        try:
                          headers = {
                              "Authorization": (
                                  f"Bearer {st.session_state['auth_token']}"
                              )
                          }
                          # /auth/sessions/save is declared with FastAPI
                          # Form(...)/File(...) parameters, i.e. it expects
                          # multipart/form-data — NOT a JSON body. Sending
                          # `json=save_payload` (the old code) made FastAPI
                          # unable to find session_id/filename/data at all,
                          # which is exactly the 422 Unprocessable Entity.
                          # We also now attach the PDF itself so the
                          # Archive screen has something to preview —
                          # previously this call never sent the file, so
                          # pdf_bytes stayed empty even when the request
                          # otherwise succeeded.
                          save_form = {
                              "session_id": st.session_state["session_id"],
                              "filename": uploaded_file.name,
                              "data": json.dumps(msg.get("data"), ensure_ascii=False),
                          }
                          save_files = {
                              "file": (
                                  f"{base_name}.pdf",
                                  pdf_to_send,
                                  "application/pdf",
                              )
                          }
                          save_res = requests.post(
                              f"{BASE_API_URL}/auth/sessions/save",
                              data=save_form,
                              files=save_files,
                              headers=headers,
                              timeout=60,
                          )
                          if save_res.status_code != 200:
                            st.warning(
                                f"{t['save_archive_err']}"
                                f" {save_res.status_code}: {save_res.text}"
                            )
                        except Exception as save_err:
                          st.warning(f"{t['save_archive_err']} {save_err}")

                        st.rerun()
                    except Exception:
                      continue
              else:
                status_container.update(
                    label=f"❌ {t['api_err']}", state="error"
                )
                st.error(f"{t['api_err']} {res.status_code}: {res.text}")
            except Exception as e:
              status_container.update(label=f"❌ {t['conn_fail']}", state="error")
              st.error(f"{t['conn_fail']} {str(e)}")

      # Display BOQ DataFrame & Audit Reports
      if st.session_state.get("boq_data") is not None:
        result = st.session_state["boq_data"]
        analysis = result.get("analysis", {})
        components = analysis.get("components", [])

        st.success(t["success_msg"])

        # --- Interactive chat about this drawing ---------------------
        # Deliberately separate from the batch analysis above, not a
        # replacement for it (per project decision): that flow renders
        # every page to a JPEG and extracts a BOQ per page automatically
        # with no memory between calls. This is the opposite shape — the
        # engineer uploads nothing new here (the PDF was already saved to
        # this session_id by the /auth/sessions/save call right after
        # analysis finished, a few lines above), then asks follow-up
        # questions, corrects a miscount, or asks "what's on page 3" and
        # keeps getting answers grounded in that same document — a real
        # back-and-forth instead of one-shot-per-page. See
        # app/services/claude_chat_service.py for how the backend keeps
        # this affordable (Claude prompt caching on the PDF) instead of
        # re-paying full price to reprocess the whole document on every
        # single question.
        st.divider()
        with st.expander(t["chat_header"], expanded=False):
          st.caption(t["chat_caption"])

          chat_key = f"chat_history_{st.session_state['session_id']}"
          chat_headers = {
              "Authorization": f"Bearer {st.session_state['auth_token']}"
          }

          if chat_key not in st.session_state:
            # Fetch once per session_id rather than on every rerun — a
            # rerun happens on every button click in this app (see the
            # st.rerun() calls elsewhere), and hitting the DB for history
            # we already have in memory on every single one would be
            # wasteful. None here specifically means "not fetched yet",
            # distinct from an empty list (a real session with zero
            # messages so far).
            try:
              hist_res = requests.get(
                  f"{BASE_API_URL}/chat/{st.session_state['session_id']}/history",
                  headers=chat_headers,
                  timeout=30,
              )
              st.session_state[chat_key] = (
                  hist_res.json() if hist_res.status_code == 200 else []
              )
            except Exception:
              st.session_state[chat_key] = []

          for chat_msg in st.session_state[chat_key]:
            with st.chat_message(
                "user" if chat_msg["role"] == "user" else "assistant"
            ):
              st.markdown(chat_msg["content"])

          # Quick question templates — the same handful of asks (get a
          # full materials breakdown against a checklist, get room
          # dimensions, check whether a specific element/device exists)
          # kept coming up as free-typed questions, so give them a
          # one-click / fill-in-the-blank shortcut instead of composing
          # the same phrasing by hand every time. "custom" keeps the
          # plain free-text box for anything else.
          template_choice = st.selectbox(
              t["chat_template_label"],
              options=["custom", "materials", "rooms", "element_check"],
              format_func=lambda x: {
                  "custom": t["chat_template_custom"],
                  "materials": t["chat_template_materials"],
                  "rooms": t["chat_template_rooms"],
                  "element_check": t["chat_template_element"],
              }[x],
              key=f"chat_template_{st.session_state['session_id']}",
          )

          chat_question = None
          if template_choice == "custom":
            chat_question = st.text_input(
                t["chat_input_label"],
                key=f"chat_q_{st.session_state['session_id']}",
                placeholder=t["chat_placeholder"],
            )
          elif template_choice == "materials":
            details = st.text_area(
                t["chat_template_materials_hint"],
                key=f"chat_details_{st.session_state['session_id']}",
                placeholder=t["chat_template_materials_placeholder"],
                height=100,
            )
            if details.strip():
              chat_question = t["chat_template_materials_fill"].format(
                  details=details.strip()
              )
          elif template_choice == "rooms":
            st.caption(t["chat_template_rooms_hint"])
            chat_question = t["chat_template_rooms_fill"]
          elif template_choice == "element_check":
            element = st.text_input(
                t["chat_template_element_hint"],
                key=f"chat_element_{st.session_state['session_id']}",
                placeholder=t["chat_template_element_placeholder"],
            )
            if element.strip():
              chat_question = t["chat_template_element_fill"].format(
                  element=element.strip()
              )

          if st.button(t["chat_send"], key=f"chat_send_{st.session_state['session_id']}"):
            if not chat_question or not chat_question.strip():
              st.warning(t["chat_template_need_input"])
            else:
              with st.spinner(t["chat_thinking"]):
                try:
                  ask_res = requests.post(
                      f"{BASE_API_URL}/chat/{st.session_state['session_id']}/ask",
                      json={"question": chat_question.strip()},
                      headers=chat_headers,
                      timeout=180,
                  )
                  if ask_res.status_code == 200:
                    chat_reply = ask_res.json()
                    st.session_state[chat_key].append(
                        {"role": "user", "content": chat_question.strip()}
                    )
                    st.session_state[chat_key].append(
                        {"role": "assistant", "content": chat_reply["answer"]}
                    )
                    st.rerun()
                  else:
                    st.error(f"{t['chat_err']} {ask_res.status_code}: {ask_res.text}")
                except Exception as chat_exc:
                  st.error(f"{t['chat_conn_fail']} {chat_exc}")
        # ---------------------------------------------------------------

        # --- Save to the reference/RAG library --------------------------
        # Promotes this session into app/services/reference_library_service.py's
        # library — future analyses and chats of the same report_type will
        # get this one pulled in as grounding. See that service's module
        # docstring for what "grounding" means in practice here (a text
        # summary of approved component names/counts, not the raw image).
        with st.expander(t["rag_header"], expanded=False):
          st.caption(t["rag_caption"])
          st.warning(t["rag_correction_caveat"])

          rag_tag = st.text_input(
              t["rag_tag_label"],
              key=f"rag_tag_{st.session_state['session_id']}",
              placeholder=t["rag_tag_placeholder"],
          )
          if st.button(t["rag_save_btn"], key=f"rag_save_{st.session_state['session_id']}"):
            if not rag_tag.strip():
              st.warning(t["rag_tag_required"])
            else:
              try:
                rag_res = requests.post(
                    f"{BASE_API_URL}/library/save",
                    json={
                        "session_id": st.session_state["session_id"],
                        "report_type": ai_report_type,
                        "tag": rag_tag.strip(),
                    },
                    headers=chat_headers,
                    timeout=30,
                )
                if rag_res.status_code == 200:
                  st.success(t["rag_saved_ok"])
                else:
                  st.error(f"{t['chat_err']} {rag_res.status_code}: {rag_res.text}")
              except Exception as rag_exc:
                st.error(f"{t['chat_conn_fail']} {rag_exc}")
        # ---------------------------------------------------------------

        if components:
          df = pd.DataFrame(components)

          if "supplier_type" not in df.columns:
            df["supplier_type"] = "Local Supplier"
          if "unit_cost_sar" not in df.columns:
            df["unit_cost_sar"] = 0.0
          if "total_cost_sar" not in df.columns:
            df["total_cost_sar"] = df.get("count", 1) * df["unit_cost_sar"]

          total_count = df["count"].sum() if "count" in df.columns else len(df)
          high_conf_count = len(df[df["confidence"] == "high"]) if "confidence" in df.columns else len(df)

          # Metric cards
          m_col1, m_col2, m_col3 = st.columns(3)
          with m_col1:
            st.markdown(
                f"""<div class="metric-card">
                    <div class="metric-value">{total_count}</div>
                    <div class="metric-label">{t['total_items']}</div>
                </div>""",
                unsafe_allow_html=True,
            )
          with m_col2:
            st.markdown(
                f"""<div class="metric-card">
                    <div class="metric-value">{high_conf_count}/{len(df)}</div>
                    <div class="metric-label">{t['confidence_level']}</div>
                </div>""",
                unsafe_allow_html=True,
            )
          with m_col3:
            render_usage_metric_card(analysis)

          st.markdown("<br>", unsafe_allow_html=True)

          # DataFrame Column Translation Config
          st.dataframe(
              _themed_df(df),
              width='stretch',
              column_config={
                  "name": t["col_name"],
                  "count": st.column_config.NumberColumn(t["col_count"], format="%d"),
                  "supplier_type": st.column_config.TextColumn(t["col_supplier"]),
                  "unit_cost_sar": st.column_config.NumberColumn(t["col_unit_cost"], format=t["currency_format"]),
                  "erp_item_code": st.column_config.TextColumn(t["col_erp_code"]),
                  "erp_item_name": st.column_config.TextColumn(t["col_erp_name"]),
                  "erp_moving_avg_cost": st.column_config.NumberColumn(t["col_erp_avg"], format=t["currency_format"]),
                  "erp_selling_price": st.column_config.NumberColumn(t["col_erp_sell"], format=t["currency_format"]),
                  "total_cost_sar": st.column_config.NumberColumn(t["col_total_cost"], format=t["currency_format"]),
                  "confidence": st.column_config.TextColumn(t["col_confidence"]),
              },
          )

          csv = df.to_csv(index=False).encode("utf-8-sig")
          st.download_button(
              t["download_csv"],
              data=csv,
              file_name=f"boq_{uploaded_file.name}.csv",
              mime="text/csv",
              width='stretch',
          )
        else:
          st.warning(t["no_devices"])

        # Interactive Engineering Notes Display — deliberately OUTSIDE the
        # `if components:` block above. Previously this whole section (and
        # therefore any "Claude Error: ..." / "Gemini Error: ..." entry a
        # service's except-block stuffs into flagged_unclear_areas — see
        # claude_service.py's _analyze) was nested INSIDE `if components:`,
        # so whenever a provider call failed and returned components=[],
        # the real error was silently swallowed and the user only ever saw
        # the generic "No components detected in this drawing." warning
        # above with zero indication anything had actually gone wrong
        # server-side. Moving this out means a failed provider call now
        # surfaces its real reason here instead of looking identical to a
        # drawing that legitimately has nothing on it.
        flagged = analysis.get("flagged_unclear_areas", [])
        if flagged:
          st.markdown("---")
          has_error_note = any(
              str(item).startswith(("Claude Error:", "Gemini Error:", "Groq Error:", "OpenRouter Error:"))
              for item in flagged
          )
          if has_error_note:
            st.error(t["provider_error_notice"])
          st.subheader(t["sys_notes"])

          pages_notes = defaultdict(list)
          for item in flagged:
            if ":" in item:
              p_pref, note_body = item.split(":", 1)
              pages_notes[p_pref.strip()].append(note_body.strip())
            else:
              pages_notes[t["general_page"]].append(item.strip())

          for page_name, notes in pages_notes.items():
            with st.expander(f"{t['notes_title']} {page_name} ({len(notes)} {t['note_count']})", expanded=True):
              for note in notes:
                st.markdown(
                    f"""<div class="report-card">🔹 {note}</div>""",
                    unsafe_allow_html=True,
                )

          docx_bytes = create_word_report(uploaded_file.name, pages_notes)
          st.download_button(
              label=t["download_word"],
              data=docx_bytes,
              file_name=f"Technical_Audit_Report_{uploaded_file.name}.docx",
              mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
              width='stretch',
          )

# ---------------------------------------------------------
# VIEW 2: 📁 ARCHIVE & SAVED SESSIONS (With Drawing Preview)
# ---------------------------------------------------------
elif navigation == t["nav_archive"]:
  render_page_header("📁", t["archive_title"], t["archive_caption"])

  headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
  try:
    res = requests.get(
        f"{BASE_API_URL}/auth/sessions/my-sessions",
        headers=headers,
        timeout=10,
    )
    if res.status_code == 200:
      sessions_list = res.json()
      if not sessions_list:
        st.info(t["no_sessions"])
      else:
        selected_session = st.selectbox(
            t["select_session"],
            options=sessions_list,
            format_func=lambda x: (
                f"📄 {x['filename']} | 🕒 {x['created_at']} | ({t['session_id']}"
                f" {x['session_id']})"
            ),
        )

        if selected_session:
          session_id = selected_session["session_id"]
          
          # إعادة ضبط الكاش عند تغيير الجلسة المحددة
          if st.session_state["selected_archived_id"] != session_id:
            st.session_state["selected_archived_id"] = session_id
            st.session_state["archived_pdf_bytes"] = None
            st.session_state["archived_img_cache"] = {}

            # جلب ملف الـ PDF الأصلي الخاص بالجلسة
            with st.spinner(t["fetching_pdf"]):
              try:
                pdf_res = requests.get(
                    f"{BASE_API_URL}/auth/sessions/{session_id}/pdf",
                    headers=headers,
                    timeout=30,
                )
                if pdf_res.status_code == 200:
                  st.session_state["archived_pdf_bytes"] = pdf_res.content
                else:
                  st.warning(t["pdf_fetch_err"])
              except Exception:
                st.warning(t["pdf_fetch_err"])

          st.markdown("---")

          # --- Session controls: rename / delete -------------------------
          # Previously there was no way to fix a bad title or remove an
          # old/duplicate session other than going into the database
          # directly.
          ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])
          with ctrl_col1:
            new_title = st.text_input(
                t["archive_rename_label"],
                value=selected_session["filename"],
                key=f"rename_input_{session_id}",
            )
          with ctrl_col2:
            st.write("")  # vertical alignment spacer to line the button up with the text_input
            if st.button(t["archive_rename_btn"], key=f"rename_btn_{session_id}"):
              if new_title.strip() and new_title.strip() != selected_session["filename"]:
                try:
                  rename_res = requests.patch(
                      f"{BASE_API_URL}/auth/sessions/{session_id}",
                      json={"filename": new_title.strip()},
                      headers=headers,
                      timeout=15,
                  )
                  if rename_res.status_code == 200:
                    st.success(t["archive_rename_ok"])
                    st.rerun()
                  else:
                    st.error(f"{t['chat_err']} {rename_res.status_code}: {rename_res.text}")
                except Exception as rename_exc:
                  st.error(f"{t['chat_conn_fail']} {rename_exc}")
          with ctrl_col3:
            confirm_delete = st.checkbox(
                t["archive_delete_confirm"], key=f"del_confirm_{session_id}"
            )
            if st.button(
                t["archive_delete_btn"],
                key=f"del_btn_{session_id}",
                disabled=not confirm_delete,
            ):
              try:
                del_res = requests.delete(
                    f"{BASE_API_URL}/auth/sessions/{session_id}",
                    headers=headers,
                    timeout=15,
                )
                if del_res.status_code == 200:
                  st.success(t["archive_delete_ok"])
                  st.session_state["selected_archived_id"] = None
                  st.rerun()
                else:
                  st.error(f"{t['chat_err']} {del_res.status_code}: {del_res.text}")
              except Exception as del_exc:
                st.error(f"{t['chat_conn_fail']} {del_exc}")
          st.markdown("---")
          # -----------------------------------------------------------------
          
          # تقسيم العرض لعمودين (المخطط التفاعلي على الشمال، والنتائج على اليمين)
          arch_col1, arch_col2 = st.columns([1.2, 1], gap="medium")

          # 🖼️ العمود الأيسر: عرض الرسم الهندسي التفاعلي للجلسة المحفوظة
          with arch_col1:
            st.subheader(t["preview_header"])
            arch_pdf_bytes = st.session_state.get("archived_pdf_bytes")

            if arch_pdf_bytes:
              try:
                doc = fitz.open(stream=arch_pdf_bytes, filetype="pdf")
                total_pages = len(doc)

                sub_c1, sub_c2 = st.columns([1, 1])
                with sub_c1:
                  arc_page_num = st.number_input(
                      f"{t['page_num']} (Archive)",
                      min_value=1,
                      max_value=total_pages,
                      value=1,
                      step=1,
                      key="arc_page_input",
                  )
                with sub_c2:
                  arc_dpi_val = st.select_slider(
                      f"{t['dpi_label']} (Archive)",
                      options=[100, 150, 200, 300],
                      value=150,
                      key="arc_dpi_slider",
                  )

                arc_cache_key = f"{session_id}_{arc_page_num}_{arc_dpi_val}"
                if arc_cache_key not in st.session_state["archived_img_cache"]:
                  page = doc.load_page(arc_page_num - 1)
                  pix = page.get_pixmap(dpi=arc_dpi_val)
                  img_data = pix.tobytes("png")

                  img_arr = plt.imread(io.BytesIO(img_data))
                  if img_arr.max() <= 1.0:
                    img_arr = (img_arr * 255).astype(np.uint8)

                  st.session_state["archived_img_cache"][arc_cache_key] = img_arr

                img_arr = st.session_state["archived_img_cache"][arc_cache_key]
                plotly_fig = px.imshow(img_arr)
                plotly_fig.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0),
                    # Same fix as the two other px.imshow() call sites above.
                    paper_bgcolor=_PALETTES["bg-elevated"],
                    plot_bgcolor=_PALETTES["bg-elevated"],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    dragmode="pan",
                )
                st.caption(t["zoom_hint"])
                st.plotly_chart(
                    plotly_fig, width='stretch', config={"scrollZoom": True}
                )
                doc.close()
              except Exception as e:
                st.error(f"Error rendering archived PDF: {e}")
            else:
              st.info("ℹ️ الرسم الهندسي غير متاح للمعاينة المباشرة لهذه الجلسة.")

          # 📊 العمود الأيمن: جدول الكميات والملاحظات الفنية
          with arch_col2:
            session_data = selected_session["data"]
            analysis = session_data.get("analysis", {})
            components = analysis.get("components", [])

            st.subheader(f"{t['boq_header']}: {selected_session['filename']}")

            if components:
              df_archived = pd.DataFrame(components)

              total_count = df_archived["count"].sum() if "count" in df_archived.columns else len(df_archived)
              high_conf_count = len(df_archived[df_archived["confidence"] == "high"]) if "confidence" in df_archived.columns else len(df_archived)

              m_col1, m_col2, m_col3 = st.columns(3)
              with m_col1:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-value">{total_count}</div>
                        <div class="metric-label">{t['total_items']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
              with m_col2:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-value">{high_conf_count}/{len(df_archived)}</div>
                        <div class="metric-label">{t['confidence_level']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
              with m_col3:
                render_usage_metric_card(analysis)

              st.markdown("<br>", unsafe_allow_html=True)

              st.dataframe(
                  _themed_df(df_archived),
                  width='stretch',
                  column_config={
                      "name": t["col_name"],
                      "count": st.column_config.NumberColumn(t["col_count"], format="%d"),
                      "supplier_type": st.column_config.TextColumn(t["col_supplier"]),
                      "unit_cost_sar": st.column_config.NumberColumn(t["col_unit_cost"], format=t["currency_format"]),
                      "erp_item_code": st.column_config.TextColumn(t["col_erp_code"]),
                      "erp_item_name": st.column_config.TextColumn(t["col_erp_name"]),
                      "erp_moving_avg_cost": st.column_config.NumberColumn(t["col_erp_avg"], format=t["currency_format"]),
                      "erp_selling_price": st.column_config.NumberColumn(t["col_erp_sell"], format=t["currency_format"]),
                      "total_cost_sar": st.column_config.NumberColumn(t["col_total_cost"], format=t["currency_format"]),
                      "confidence": st.column_config.TextColumn(t["col_confidence"]),
                  },
              )

            else:
              st.warning(t["no_devices"])

            # Same fix as the live-analysis view above: render flagged
            # notes / provider error messages regardless of whether
            # components came back empty, instead of nesting this inside
            # `if components:` where a failed provider call's real error
            # was silently hidden behind the generic "no devices" warning.
            flagged = analysis.get("flagged_unclear_areas", [])
            if flagged:
              st.markdown("---")
              has_error_note = any(
                  str(item).startswith(("Claude Error:", "Gemini Error:", "Groq Error:", "OpenRouter Error:"))
                  for item in flagged
              )
              if has_error_note:
                st.error(t["provider_error_notice"])
              st.subheader(t["sys_notes"])
              pages_notes = defaultdict(list)
              for item in flagged:
                if ":" in item:
                  p_pref, note_body = item.split(":", 1)
                  pages_notes[p_pref.strip()].append(note_body.strip())
                else:
                  pages_notes[t["general_page"]].append(item.strip())

              for page_name, notes in pages_notes.items():
                with st.expander(f"{t['notes_title']} {page_name} ({len(notes)} {t['note_count']})", expanded=True):
                  for note in notes:
                    st.markdown(
                        f"""<div class="report-card">🔹 {note}</div>""",
                        unsafe_allow_html=True,
                    )

              docx_bytes = create_word_report(
                  selected_session["filename"], pages_notes
              )
              st.download_button(
                  label=t["download_word"],
                  data=docx_bytes,
                  file_name=f"Report_{selected_session['filename']}.docx",
                  mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                  width='stretch',
              )
    else:
      st.error(f"{t['fetch_archive_err']} {res.text}")
  except Exception as e:
    st.error(f"{t['archive_conn_err']} {e}")

# ---------------------------------------------------------
# VIEW 3: 👥 USER MANAGEMENT (Admin Only)
# ---------------------------------------------------------
elif navigation == t["nav_users"]:
  render_page_header("👥", t["users_title"])

  if st.session_state["user_info"].get("role") != "admin":
    st.warning(t["users_admin_only"])
  else:
    headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}

    st.subheader(t["add_user"])
    with st.form("add_user_form"):
      new_username = st.text_input(t["username"])
      new_email = st.text_input(t["email"])
      new_password = st.text_input(t["password"], type="password")
      new_role = st.selectbox(
          t["role"],
          options=["engineer", "auditor", "admin"],
          format_func=lambda x: {
              "engineer": t["role_engineer"],
              "auditor": t["role_auditor"],
              "admin": t["role_admin"],
          }[x],
      )

      btn_create = st.form_submit_button(t["create_acc_btn"], width='stretch')

      if btn_create:
        if not new_username or not new_password or not new_email:
          st.error(t["fill_all_fields"])
        else:
          user_payload = {
              "username": new_username,
              "email": new_email,
              "password": new_password,
              "role": new_role,
          }
          try:
            res = requests.post(
                f"{BASE_API_URL}/auth/users",
                json=user_payload,
                headers=headers,
                timeout=10,
            )
            if res.status_code == 200:
              st.success(f"✅ {t['acc_created']} ({new_username})")
              st.rerun()
            else:
              st.error(f"{t['acc_fail']} {res.json().get('detail')}")
          except Exception as e:
            st.error(f"❌ {t['conn_fail']} {e}")

    st.markdown("---")

    # --- Existing users: change role / reset password / delete -----------
    # Previously the only user-management endpoint was POST /users
    # (create) — there was no way to see who already has an account, fix
    # a wrong role, or recover someone locked out of a forgotten password
    # short of a direct DB query. Backed by the new GET/PATCH/DELETE
    # /auth/users[...] endpoints in app/routers/auth.py.
    st.subheader(t["users_list_title"])
    try:
      list_res = requests.get(
          f"{BASE_API_URL}/auth/users", headers=headers, timeout=10
      )
    except Exception as e:
      list_res = None
      st.error(f"{t['users_list_fetch_err']} {e}")

    if list_res is not None:
      if list_res.status_code != 200:
        st.error(f"{t['users_list_fetch_err']} {list_res.text}")
      else:
        existing_users = list_res.json()
        if not existing_users:
          st.info(t["users_list_empty"])
        for u in existing_users:
          role_label = {
              "engineer": t["role_engineer"],
              "auditor": t["role_auditor"],
              "admin": t["role_admin"],
          }.get(u["role"], u["role"])
          # user_info only ever carries {"username", "role"} (see
          # _restore_session_from_url() / the login handler below) — there
          # is no "id" in session state to compare against, so identify
          # "this is me" by username instead (unique, per the DB schema).
          is_self = u["username"] == st.session_state["user_info"].get("username")
          with st.expander(f"👤 {u['username']} — {role_label}", expanded=False):
            st.caption(u["email"])

            role_col, role_btn_col = st.columns([3, 1])
            with role_col:
              role_options = ["engineer", "auditor", "admin"]
              new_role_val = st.selectbox(
                  t["users_new_role_label"],
                  options=role_options,
                  index=role_options.index(u["role"]) if u["role"] in role_options else 0,
                  format_func=lambda x: {
                      "engineer": t["role_engineer"],
                      "auditor": t["role_auditor"],
                      "admin": t["role_admin"],
                  }[x],
                  key=f"role_select_{u['id']}",
              )
            with role_btn_col:
              st.write("")
              if st.button(
                  t["users_change_role_btn"],
                  key=f"role_btn_{u['id']}",
                  width='stretch',
                  disabled=(new_role_val == u["role"]),
              ):
                try:
                  role_res = requests.patch(
                      f"{BASE_API_URL}/auth/users/{u['id']}",
                      json={"role": new_role_val},
                      headers=headers,
                      timeout=10,
                  )
                  if role_res.status_code == 200:
                    st.success(t["users_role_updated"])
                    st.rerun()
                  else:
                    st.error(f"{t['acc_fail']} {role_res.json().get('detail')}")
                except Exception as e:
                  st.error(f"❌ {t['conn_fail']} {e}")

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            pw_col, pw_btn_col = st.columns([3, 1])
            with pw_col:
              new_pw_val = st.text_input(
                  t["users_new_password_label"],
                  type="password",
                  key=f"pw_input_{u['id']}",
                  help=t["users_reset_pw_hint"],
              )
            with pw_btn_col:
              st.write("")
              if st.button(
                  t["users_reset_pw_btn"],
                  key=f"pw_btn_{u['id']}",
                  width='stretch',
                  disabled=not new_pw_val,
              ):
                try:
                  pw_res = requests.patch(
                      f"{BASE_API_URL}/auth/users/{u['id']}",
                      json={"new_password": new_pw_val},
                      headers=headers,
                      timeout=10,
                  )
                  if pw_res.status_code == 200:
                    st.success(t["users_reset_pw_ok"])
                    st.rerun()
                  else:
                    st.error(f"{t['acc_fail']} {pw_res.json().get('detail')}")
                except Exception as e:
                  st.error(f"❌ {t['conn_fail']} {e}")

            if not is_self:
              st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
              del_col, del_btn_col = st.columns([3, 1])
              with del_col:
                confirm_del_user = st.checkbox(
                    t["users_delete_confirm"], key=f"del_confirm_user_{u['id']}"
                )
              with del_btn_col:
                st.write("")
                if st.button(
                    t["users_delete_btn"],
                    key=f"del_btn_user_{u['id']}",
                    width='stretch',
                    disabled=not confirm_del_user,
                ):
                  try:
                    del_res = requests.delete(
                        f"{BASE_API_URL}/auth/users/{u['id']}",
                        headers=headers,
                        timeout=10,
                    )
                    if del_res.status_code == 200:
                      st.success(t["users_delete_ok"])
                      st.rerun()
                    else:
                      st.error(f"{t['acc_fail']} {del_res.json().get('detail')}")
                  except Exception as e:
                    st.error(f"❌ {t['conn_fail']} {e}")