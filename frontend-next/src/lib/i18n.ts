"use client";

import { create } from "zustand";

/**
 * Translation keys are added incrementally as each screen is built (same
 * approach the Streamlit version used with its TRANSLATIONS dict) — this
 * file grows alongside src/app/**. Keeping one flat dict per language
 * (not nested namespaces) matches that original structure so porting
 * strings across is a straight copy.
 */
export const translations = {
  ar: {
    brand_name: "AECO",
    brand_tagline: "محرك الحريق والأمن بالذكاء الاصطناعي",
    login_title: "تسجيل الدخول",
    login_subtitle: "من فضلك سجّل الدخول للمتابعة",
    username: "اسم المستخدم",
    password: "كلمة المرور",
    login_btn: "دخول",
    login_failed: "فشل تسجيل الدخول",
    logging_in: "جاري الدخول...",
    nav_projects: "📋 المشاريع",
    nav_analyze: "🚀 تحليل مخطط جديد",
    nav_archive: "📁 الجلسات المحفوظة والأرشيف",
    nav_users: "👥 إدارة المستخدمين",
    logout: "🚪 تسجيل الخروج",
    theme_dark: "🌙 غامق",
    theme_light: "☀️ فاتح",
    language_label: "اللغة",

    archive_title: "📁 الجلسات المحفوظة والأرشيف",
    archive_subtitle: "استعرض التحليلات المحفوظة سابقًا، أعد تسميتها أو احذفها.",
    archive_loading: "جاري التحميل...",
    archive_empty: "لا توجد جلسات محفوظة بعد.",
    archive_view_btn: "عرض",
    archive_hide_btn: "إخفاء",
    archive_rename_btn: "إعادة تسمية",
    archive_rename_save: "حفظ",
    archive_cancel: "إلغاء",
    archive_delete_btn: "حذف",
    archive_delete_confirm: "متأكد من الحذف؟",
    archive_delete_ok: "تأكيد الحذف",
    archive_no_data: "لا توجد بيانات تحليل محفوظة لهذه الجلسة.",

    users_title: "👥 إدارة المستخدمين",
    users_subtitle: "أضف مستخدمين جدد، غيّر الصلاحيات، أو أعد ضبط كلمات المرور.",
    users_create_title: "إضافة مستخدم جديد",
    users_create_btn: "إنشاء مستخدم",
    users_create_ok: "تم إنشاء المستخدم بنجاح",
    users_list_title: "المستخدمون الحاليون",
    users_list_empty: "لا يوجد مستخدمون.",
    users_col_username: "اسم المستخدم",
    users_col_email: "البريد الإلكتروني",
    users_col_role: "الصلاحية",
    users_new_role_label: "الصلاحية الجديدة",
    users_change_role_btn: "تحديث الصلاحية",
    users_role_updated: "تم تحديث الصلاحية بنجاح",
    users_new_password_label: "كلمة مرور جديدة",
    users_reset_pw_hint: "اتركه فارغًا لعدم التغيير",
    users_reset_pw_btn: "إعادة تعيين",
    users_reset_pw_ok: "تم تحديث كلمة المرور بنجاح",
    users_delete_btn: "حذف المستخدم",
    users_delete_confirm: "متأكد من الحذف؟",
    users_delete_ok: "تأكيد الحذف",

    chat_header: "💬 اسأل عن المخطط (محادثة تفاعلية)",
    chat_caption:
      "شغالة على نفس ملف الـ PDF اللي رفعته فوق من غير ما تحتاج ترفعه تاني — اسأل، صحّح، أو اطلب توضيح لحد ما توصل لنتيجة مرضية.",
    chat_template_label: "نوع السؤال",
    chat_template_custom: "✍️ سؤال حر",
    chat_template_materials: "🧮 احسب كميات المواد بتفاصيل معينة",
    chat_template_rooms: "📐 احسب قياسات الغرف",
    chat_template_element: "🔍 هل يوجد عنصر معين؟",
    chat_template_security: "🛡️ برومبت أمن مخصص (محطات محولات)",
    chat_template_fire: "🔥 برومبت حريق مخصص (TES-P-119.21)",
    chat_fire_hint:
      "هيتبعت للمودل قايمة متطلبات كشف وإطفاء الحريق الكاملة لكل مناطق المحطة حسب المواصفة، ويطلب منه يطلعلك جدول كميات بناءً على اللي موجود في المخطط.",
    chat_table_add_to_main: "➕ أضف للجدول الرئيسي",
    chat_table_added_ok: "✅ اتضاف للجدول الرئيسي",
    chat_template_materials_hint:
      "اكتب المواد/الأجهزة اللي عايز تحسبها بالتفصيل، سطر لكل عنصر.",
    chat_template_materials_placeholder: "1. كاشفات الدخان\n2. طفايات الحريق\n3. الرشاشات",
    chat_template_rooms_hint:
      "هيطلب من الموديل قياسات (الأبعاد والمساحات) كل الغرف الموجودة في المخطط.",
    chat_template_element_hint: "اسم العنصر/الجهاز اللي عايز تتأكد منه:",
    chat_template_element_placeholder: "مطفأة حريق CO2",
    chat_security_class_label: "نوع المحطة (Substation Class)",
    chat_security_prompt_label: "نوع البند المطلوب",
    chat_security_hint:
      "هيتبعت البرومبت التفصيلي الجاهز (زي المتفق عليه مع HCIS) للمودل كما هو، ويطلب منه يستخرج جدول كميات (BOQ) بناءً عليه.",
    chat_template_need_input: "⚠️ اكتب سؤالك أو املأ التفاصيل المطلوبة الأول.",
    chat_input_label: "اكتب سؤالك أو ملاحظتك",
    chat_placeholder: "مثلاً: طلعلي كل الديتكتورز في الدور التاني بس",
    chat_send: "📨 ابعت",
    chat_thinking: "بيفكر...",
    chat_needs_save: "لازم تحفظ التحليل في الأرشيف الأول عشان تقدر تبدأ محادثة.",
    chat_empty: "لسه مفيش أسئلة — ابدأ المحادثة من تحت.",

    rag_header: "📚 أضف كمرجع لمكتبة التعلم (RAG)",
    rag_caption:
      "هيتحفظ المخطط ده كمثال معتمد — التحليلات والمحادثات الجاية لنفس نوع النظام هتسترشد بيه تلقائيًا.",
    rag_correction_caveat:
      "⚠️ ملحوظة: الحفظ هيسجّل نتيجة التحليل الأوتوماتيكي الحالية كما هي. لو صححت حاجة في المحادثة فوق، التصحيح ده لسه مش بيترجع تلقائيًا للنتيجة المحفوظة — لو عايز المرجع يعكس التصحيح، حدّث الأرقام يدويًا الأول.",
    rag_tag_label: "تصنيف/وصف قصير للمخطط ده",
    rag_tag_placeholder: "مثلاً: مخطط فيلا سكنية - نظام إنذار حريق",
    rag_save_btn: "💾 احفظ كمرجع",
    rag_tag_required: "⚠️ اكتب تصنيف قصير للمخطط الأول.",
    rag_saved_ok: "✅ اتحفظ في مكتبة المراجع بنجاح.",

    projects_title: "📋 المشاريع",
    projects_subtitle:
      "ارفع مواصفة المشروع الفنية (PTS) وهيطلعلك نطاق العمل: كل منطقة في المواصفة ونوع النظام المطلوب فيها.",
    projects_upload_label: "ملف مواصفة المشروع (PDF)",
    projects_upload_hint: "ملفات PDF بس. المستندات الطويلة ممكن تاخد دقيقة أو أكتر.",
    projects_extract_btn: "📤 استخرج نطاق العمل",
    projects_extracting: "جاري قراءة المستند...",
    projects_extract_truncated_warning:
      "⚠️ الرد اتقطع لأنه وصل لأقصى طول مسموح — ممكن يكون في مناطق ناقصة في آخر الجدول. راجع الجدول قبل الاعتماد.",
    projects_rag_used: "استُخدم {n} جدول معتمد من مشاريع سابقة كمرجع.",

    projects_scope_title: "نطاق العمل حسب الـ PTS",
    projects_col_sl: "SL #",
    projects_col_area: "Area",
    projects_col_system: "Type of system required as per PTS",
    projects_scope_empty: "مفيش صفوف. لو المستند ده متحفظ بالشكل القديم، ارفعه تاني واستخرج النطاق من جديد.",
    projects_add_row: "➕ إضافة صف",
    projects_delete_row: "حذف الصف",
    projects_download_xlsx: "⬇️ تحميل Excel",

    projects_save_filename_label: "اسم الحفظ",
    projects_save_btn: "💾 حفظ",
    projects_save_changes_btn: "💾 حفظ التعديلات",
    projects_saved_ok: "✅ اتحفظ",

    projects_approve_title: "📚 اعتماد وإضافة لمكتبة المراجع (RAG)",
    projects_approve_hint:
      "بعد ما تراجع الجدول وتعدّله لو محتاج، اعتمده عشان الاستخراجات الجاية تسترشد بيه.",
    projects_approve_need_save: "احفظ الجدول الأول قبل الاعتماد.",
    projects_approve_tag_label: "وصف قصير للمشروع",
    projects_approve_tag_placeholder: "مثلاً: محطة تحويل 380/132 ك.ف - حريق",
    projects_approve_btn: "✅ اعتماد وإضافة للمراجع",
    projects_approved_ok: "✅ معتمد ومضاف لمكتبة المراجع",
    projects_approved_badge: "معتمد",
    projects_unsaved_changes: "في تعديلات لسه متحفظتش.",

    projects_saved_list_title: "المستندات المحفوظة",
    projects_saved_loading: "جاري التحميل...",
    projects_saved_empty: "لا توجد مستندات محفوظة بعد.",
    projects_view_btn: "فتح",
    projects_view_pdf_btn: "عرض PDF الأصلي",
    projects_delete_btn: "حذف",
    projects_delete_confirm: "متأكد من الحذف؟",
    projects_delete_ok: "تأكيد الحذف",
  },
  en: {
    brand_name: "AECO",
    brand_tagline: "Fire & Security AI Engine",
    login_title: "Sign in",
    login_subtitle: "Please sign in to continue",
    username: "Username",
    password: "Password",
    login_btn: "Sign in",
    login_failed: "Sign-in failed",
    logging_in: "Signing in...",
    nav_projects: "📋 Projects",
    nav_analyze: "🚀 Analyze New Drawing",
    nav_archive: "📁 Saved Sessions & Archive",
    nav_users: "👥 User Management",
    logout: "🚪 Logout",
    theme_dark: "🌙 Dark",
    theme_light: "☀️ Light",
    language_label: "Language",

    archive_title: "📁 Saved Sessions & Archive",
    archive_subtitle: "Browse previously saved analyses, rename or delete them.",
    archive_loading: "Loading...",
    archive_empty: "No saved sessions yet.",
    archive_view_btn: "View",
    archive_hide_btn: "Hide",
    archive_rename_btn: "Rename",
    archive_rename_save: "Save",
    archive_cancel: "Cancel",
    archive_delete_btn: "Delete",
    archive_delete_confirm: "Are you sure?",
    archive_delete_ok: "Confirm delete",
    archive_no_data: "No saved analysis data for this session.",

    users_title: "👥 User Management",
    users_subtitle: "Add new users, change roles, or reset passwords.",
    users_create_title: "Add a new user",
    users_create_btn: "Create user",
    users_create_ok: "User created successfully",
    users_list_title: "Existing users",
    users_list_empty: "No users found.",
    users_col_username: "Username",
    users_col_email: "Email",
    users_col_role: "Role",
    users_new_role_label: "New role",
    users_change_role_btn: "Update role",
    users_role_updated: "Role updated successfully",
    users_new_password_label: "New password",
    users_reset_pw_hint: "Leave blank to keep unchanged",
    users_reset_pw_btn: "Reset",
    users_reset_pw_ok: "Password updated successfully",
    users_delete_btn: "Delete user",
    users_delete_confirm: "Are you sure?",
    users_delete_ok: "Confirm delete",

    chat_header: "💬 Ask About This Drawing (Interactive Chat)",
    chat_caption:
      "Uses the same PDF you already uploaded above — no need to re-upload it. Ask, correct, or clarify until you're happy with the answer.",
    chat_template_label: "Question type",
    chat_template_custom: "✍️ Free-form question",
    chat_template_materials: "🧮 Calculate material quantities with details",
    chat_template_rooms: "📐 Calculate room dimensions",
    chat_template_element: "🔍 Check if an element exists",
    chat_template_security: "🛡️ Security BOQ Prompt (Substations)",
    chat_template_fire: "🔥 Fire Protection BOQ Prompt (TES-P-119.21)",
    chat_fire_hint:
      "Sends the model the full fire detection/protection requirements for every substation area per the standard, and asks it to produce a Bill of Quantities based on what's actually in the drawing.",
    chat_table_add_to_main: "➕ Add to main table",
    chat_table_added_ok: "✅ Added to main table",
    chat_template_materials_hint:
      "List the materials/devices you want quantities for, one per line.",
    chat_template_materials_placeholder: "1. Smoke detectors\n2. Fire extinguishers\n3. Sprinklers",
    chat_template_rooms_hint:
      "Asks the model for the dimensions (size and area) of every room in the drawing.",
    chat_template_element_hint: "Name of the element/device to check for:",
    chat_template_element_placeholder: "CO2 fire extinguisher",
    chat_security_class_label: "Substation Class",
    chat_security_prompt_label: "Prompt topic",
    chat_security_hint:
      "Sends the full prepared HCIS-style engineering prompt to the model as-is, and asks it to produce a Bill of Quantities based on it.",
    chat_template_need_input: "⚠️ Type your question or fill in the required details first.",
    chat_input_label: "Type your question or note",
    chat_placeholder: "e.g. List all the detectors on the second floor only",
    chat_send: "📨 Send",
    chat_thinking: "Thinking...",
    chat_needs_save: "Save this analysis to the archive first to start a conversation.",
    chat_empty: "No questions yet — start the conversation below.",

    rag_header: "📚 Save as a Reference (RAG Library)",
    rag_caption:
      "Saves this drawing as an approved example — future analyses and chats of the same system type will automatically be grounded in it.",
    rag_correction_caveat:
      "⚠️ Note: saving records the current automatic analysis result as-is. If you corrected something in the chat above, that correction is not yet reflected back into the saved result automatically — update the numbers manually first if you want the reference to reflect the correction.",
    rag_tag_label: "Short tag/description for this drawing",
    rag_tag_placeholder: "e.g. Residential villa - fire alarm system",
    rag_save_btn: "💾 Save as Reference",
    rag_tag_required: "⚠️ Type a short tag for the drawing first.",
    rag_saved_ok: "✅ Saved to the reference library successfully.",

    projects_title: "📋 Projects",
    projects_subtitle:
      "Upload the project's technical specification (PTS) to get its scope: every area in the PTS and the type of system required there.",
    projects_upload_label: "Project specification file (PDF)",
    projects_upload_hint: "PDF only. Long documents can take a minute or more.",
    projects_extract_btn: "📤 Extract scope",
    projects_extracting: "Reading the document...",
    projects_extract_truncated_warning:
      "⚠️ The reply was cut off at the maximum length — some areas at the end of the table may be missing. Review the table before approving.",
    projects_rag_used: "{n} approved table(s) from past projects were used as reference.",

    projects_scope_title: "Scope as per PTS",
    projects_col_sl: "SL #",
    projects_col_area: "Area",
    projects_col_system: "Type of system required as per PTS",
    projects_scope_empty: "No rows. If this document was saved in the old format, upload it again and re-extract the scope.",
    projects_add_row: "➕ Add row",
    projects_delete_row: "Delete row",
    projects_download_xlsx: "⬇️ Download Excel",

    projects_save_filename_label: "Save as",
    projects_save_btn: "💾 Save",
    projects_save_changes_btn: "💾 Save changes",
    projects_saved_ok: "✅ Saved",

    projects_approve_title: "📚 Approve & add to reference library (RAG)",
    projects_approve_hint:
      "After reviewing and correcting the table, approve it so future extractions are guided by it.",
    projects_approve_need_save: "Save the table before approving it.",
    projects_approve_tag_label: "Short project description",
    projects_approve_tag_placeholder: "e.g. 380/132kV substation - fire",
    projects_approve_btn: "✅ Approve & add to references",
    projects_approved_ok: "✅ Approved and added to the reference library",
    projects_approved_badge: "Approved",
    projects_unsaved_changes: "You have unsaved changes.",

    projects_saved_list_title: "Saved documents",
    projects_saved_loading: "Loading...",
    projects_saved_empty: "No saved documents yet.",
    projects_view_btn: "Open",
    projects_view_pdf_btn: "View original PDF",
    projects_delete_btn: "Delete",
    projects_delete_confirm: "Are you sure?",
    projects_delete_ok: "Confirm delete",
  },
} as const;

export type Lang = keyof typeof translations;
export type TranslationKey = keyof (typeof translations)["en"];

type I18nState = {
  lang: Lang;
  setLang: (lang: Lang) => void;
};

const STORAGE_KEY = "aeco_lang";

// Always "ar" for this store's very first value — on BOTH the server
// render and the client's initial render before hydration. This file has
// no true SSR/CSR split (it's a "use client" module instantiated fresh in
// each environment), so the old version — returning `window ? stored :
// "ar"` — made the server always produce "ar"-language HTML while a
// returning client with lang="en" saved would instantiate this same
// store with "en" *before* React had hydrated against the server HTML.
// That's a text-content mismatch on every single translated string on
// the page at once, which is exactly what was surfacing as React's
// minified hydration error #418 and taking the whole app down to a
// blank screen with no other clue. The actual persisted language is
// applied a tick later instead, via hydrateLangFromStorage() below,
// called from a client-only useEffect (see providers.tsx) — a normal
// post-hydration state update, not part of the hydration diff, so it
// can safely differ from the first render.
function readInitialLang(): Lang {
  return "ar";
}

export const useI18nStore = create<I18nState>((set) => ({
  lang: readInitialLang(),
  setLang: (lang) => {
    if (typeof window !== "undefined") window.localStorage.setItem(STORAGE_KEY, lang);
    set({ lang });
  },
}));

/** Applies whatever language was actually persisted from a previous
 * visit. Must only ever run client-side, after the first paint — see the
 * comment on readInitialLang() above for why. */
export function hydrateLangFromStorage() {
  if (typeof window === "undefined") return;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "en" || stored === "ar") {
    useI18nStore.setState({ lang: stored });
  }
}

export function dirFor(lang: Lang) {
  return lang === "ar" ? "rtl" : "ltr";
}

/** `const t = useT()` then `t.login_title` — mirrors the Streamlit code's
 * `t = TRANSLATIONS[lang_code]; t["login_title"]` usage closely enough
 * that porting a screen's strings over is mostly mechanical. */
export function useT() {
  const lang = useI18nStore((s) => s.lang);
  return translations[lang];
}
