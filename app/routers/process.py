import asyncio
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import functools
import gc
import json
import logging
import os
import shutil
import subprocess
from typing import Optional
import uuid

from app.database import get_db, log_analysis
from app.services.ai_service import GeminiAIService
from app.services.cad_service import analyze_cad_drawing
from app.services.claude_service import ClaudeAIService
from app.services.erpnext_service import ERPNextService
from app.services.groq_service import GroqAIService
from app.services.item_matcher import match_items_with_erp
from app.services.openrouter_service import OpenRouterAIService
from app.services.parser_service import DocumentParserService
from app.services import reference_library_service
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, Depends
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/extract", tags=["Extraction Engine"])

# One shared instance per provider. All four expose the exact same
# interface — analyze_fire_alarm_drawing(image_bytes) / analyze_security_drawing(image_bytes)
# — built on the exact same prompts (app/services/prompts.py), so they can
# be swapped in/out below with no special-casing per provider.
#
# "claude" — briefly changed 2026-08-22 to route through OpenRouter at
# anthropic/claude-sonnet-5 (cheaper model), then reverted the same day
# back to direct ClaudeAIService/claude-fable-5 once it turned out
# OpenRouter charges the exact same list price Anthropic does for
# claude-fable-5 itself ($10/$50 per MTok either way — OpenRouter doesn't
# discount it) — so there was no actual cost saving available for THIS
# model via OpenRouter, only by switching to a cheaper model (Sonnet),
# which carries the real, tested risk documented in claude_service.py
# (Sonnet returned zero components on this project's real dense
# drawings). Direct API it is, one fewer hop, identical price.
PROVIDER_SERVICES = {
    "claude": ClaudeAIService(),
    "gemini": GeminiAIService(),
    "groq": GroqAIService(),
    "openrouter": OpenRouterAIService(),
}

# إعداد الـ Logger
logger = logging.getLogger("dwg_converter")
logger.setLevel(logging.INFO)

# محرك ThreadPool لمنع حصر الـ Async Loop أثناء استدعاء الذكاء الاصطناعي
executor = ThreadPoolExecutor(max_workers=4)


def _resolve_analyzer(provider: str, report_type: str, model: Optional[str] = None):
    """Pick the right provider service + method for this request.

    Previously this branching lived inline in the endpoint and was broken
    for two of the three providers: the "gemini"/default branch called
    `ai_service.analyze_drawing`, a method that never existed on
    GeminiAIService (it only had `analyze_fire_alarm_drawing`) and it
    ignored `report_type` entirely; the "groq" branch called a
    `groq_service` object that was never imported anywhere in this file,
    so selecting Groq from the frontend raised a NameError immediately.
    Both were caught by the broad `except Exception` around the call site
    and silently turned into a per-page "error in model call" flag, so the
    UI looked like it "worked" while actually returning nothing for
    Gemini and Groq. Only "claude" ever produced real results.

    `model` is only meaningful when provider == "openrouter" — it's the
    OpenRouter model id picked in the frontend's model picker (e.g.
    "anthropic/claude-sonnet-4.5"). A fresh OpenRouterAIService is built
    per request in that case rather than reusing the shared instance in
    PROVIDER_SERVICES, since that shared instance is pinned to whatever
    OPENROUTER_MODEL defaults to. Other providers ignore `model` entirely
    — they're each pinned to one model by design (see their own service
    files for why).
    """
    if provider == "openrouter" and model:
        service = OpenRouterAIService(model=model)
    else:
        service = PROVIDER_SERVICES.get(provider, PROVIDER_SERVICES["gemini"])
    if report_type == "security":
        return service.analyze_security_drawing
    return service.analyze_fire_alarm_drawing


@router.post("/pdf-boq")
async def extract_boq_from_pdf(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None), # خليه Optional لمنع أخطاء 422/404
    provider: str = Query("gemini", description="gemini, claude, groq, or openrouter"),
    report_type: str = Query("fire", description="security or fire"),
    model: Optional[str] = Query(
        None,
        description=(
            "Only used when provider=openrouter. Specific OpenRouter model"
            " id to route to (e.g. 'openai/gpt-4o',"
            " 'anthropic/claude-sonnet-4.5', 'google/gemini-2.5-flash')."
            " Ignored by the other three providers, which are each pinned"
            " to one model."
        ),
    ),
    db: Session = Depends(get_db), # 👈 1. حقن دالة الداتابيز هنا
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    contents = await file.read()

    # Reverted the native-PDF-per-page experiment (media_kind="pdf") for
    # all providers, back to rendering every page to a JPEG — the same
    # path Groq always used. Two concrete, tested findings killed it:
    # 1) Real drawing exports from this project (AutoCAD/Distiller PDFs)
    #    have NO embedded text layer at all — `pdffonts` on the actual
    #    sample file showed zero fonts; every label is vector-outlined
    #    shapes. So native PDF's headline benefit ("the model reads the
    #    real text directly") never applied to these files in the first
    #    place.
    # 2) The fix required to make native PDF reliable — baking a
    #    rotated page's /Rotate flag into its content stream, since
    #    Claude's internal PDF-to-image conversion doesn't reliably honor
    #    /Rotate — took 34 seconds for a single page in direct local
    #    testing (pypdf's transfer_rotation_to_content on a dense CAD
    #    export). That's a non-starter per page, let alone per document.
    # get_pixmap()-based JPEG rendering (below) always honors rotation
    # correctly and renders in a fraction of a second, which is what this
    # pipeline used successfully before the native-PDF detour. See
    # DocumentParserService.split_pdf_to_pages for the still-available
    # (but unused by default) native-PDF path if this is revisited later
    # with a faster rotation-normalization approach.
    page_payloads = DocumentParserService.process_pdf_to_images(contents)
    media_kind = "image"

    if not page_payloads:
        raise HTTPException(status_code=400, detail="Could not read PDF pages")

    analyzer = _resolve_analyzer(provider, report_type, model)

    # Pulled ONCE per document, not per page — every page of this same
    # PDF gets the same reference examples, and there's no reason to hit
    # the DB 40 times for a 40-page drawing set to fetch the exact same 3
    # rows. No tag/hint is available at this automatic stage (the user
    # hasn't typed anything — reference_library_service.retrieve_similar
    # falls back to "most recent N for this report_type" when tag_hint is
    # empty), so this is deliberately a general "house style" reference,
    # not a targeted one. See app/services/reference_library_service.py.
    reference_examples_block = reference_library_service.build_examples_block(
        reference_library_service.retrieve_similar(db, report_type)
    )

    async def generate_progress():
        aggregated_components = defaultdict(
            lambda: {
                "count": 0,
                "confidence": "high",
                "supplier_type": "Local Supplier",
                "unit_cost_sar": 0.0,
                "total_cost_sar": 0.0,
            }
        )
        all_flagged_issues = []
        total_pages = len(page_payloads)

        # تجميع استهلاك التوكن والتكلفة عبر كل صفحات المخطط لهذا المزوّد
        usage_totals = {"total_input_tokens": 0, "total_output_tokens": 0, "total_cost_usd": 0.0}
        usage_model_name = None

        loop = asyncio.get_event_loop()

        for idx, page_bytes in enumerate(page_payloads):
            progress_msg = {
                "status": "progress",
                "current_page": idx + 1,
                "total_pages": total_pages,
            }
            yield json.dumps(progress_msg) + "\n"
            await asyncio.sleep(0)

            try:
                raw_ai_result = await loop.run_in_executor(
                    executor,
                    functools.partial(
                        analyzer,
                        page_bytes,
                        media_kind,
                        reference_examples=reference_examples_block,
                    ),
                )
            except Exception as model_err:
                all_flagged_issues.append(
                    f"الصفحة {idx + 1}: خطأ في استدعاء الموديل - {str(model_err)}"
                )
                continue

            try:
                parsed_analysis = json.loads(raw_ai_result)

                for comp in parsed_analysis.get("components", []):
                    name = comp.get("name")
                    count = comp.get("count", 0)
                    confidence = comp.get("confidence", "high")
                    supplier_type = comp.get("supplier_type", "Local Supplier")
                    unit_cost_sar = float(comp.get("unit_cost_sar", 0.0))

                    if name and count > 0:
                        aggregated_components[name]["count"] += count
                        aggregated_components[name]["confidence"] = confidence
                        aggregated_components[name]["supplier_type"] = supplier_type
                        aggregated_components[name]["unit_cost_sar"] = unit_cost_sar
                        aggregated_components[name]["total_cost_sar"] = (
                            aggregated_components[name]["count"] * unit_cost_sar
                        )

                for flag in parsed_analysis.get("flagged_unclear_areas", []):
                    all_flagged_issues.append(f"الصفحة {idx + 1}: {flag}")

                page_usage = parsed_analysis.get("api_usage")
                if page_usage:
                    usage_totals["total_input_tokens"] += page_usage.get("input_tokens", 0) or 0
                    usage_totals["total_output_tokens"] += page_usage.get("output_tokens", 0) or 0
                    usage_totals["total_cost_usd"] += page_usage.get("total_cost_usd", 0.0) or 0.0
                    usage_model_name = page_usage.get("model", usage_model_name)

            except Exception as e:
                all_flagged_issues.append(
                    f"الصفحة {idx + 1}: خطأ في قراءة النتيجة - {str(e)}"
                )

            if idx % 5 == 0:
                gc.collect()

        final_components_list = [
            {
                "name": name,
                "count": data["count"],
                "confidence": data["confidence"],
                "supplier_type": data["supplier_type"],
                "unit_cost_sar": data["unit_cost_sar"],
                "total_cost_sar": data["total_cost_sar"],
            }
            for name, data in aggregated_components.items()
        ]

        if final_components_list:
            try:
                logger.info("🔄 جاري سحب أحدث الأصناف والأسعار من ERPNext...")
                erp_service = ERPNextService()
                erp_items = erp_service.get_all_items_with_prices()

                if erp_items:
                    final_components_list = match_items_with_erp(
                        final_components_list, erp_items
                    )
            except Exception as erp_err:
                logger.error(f"❌ فشلت عملية المطابقة مع ERPNext: {str(erp_err)}")

        final_analysis_payload = {
            "system_type": (
                "Fire Alarm System"
                if report_type == "fire"
                else "Security System"
            ),
            "components": final_components_list,
            "flagged_unclear_areas": all_flagged_issues,
            "usage_summary": {
                "provider": provider,
                "model": usage_model_name,
                "total_input_tokens": usage_totals["total_input_tokens"],
                "total_output_tokens": usage_totals["total_output_tokens"],
                "total_cost_usd": round(usage_totals["total_cost_usd"], 5),
            },
        }

        # -------------------------------------------------------------
        # 💾 2. إضافة الحفظ في الداتابيز هنا قبل إرجاع النتيجة النهائية
        # -------------------------------------------------------------
        try:
            log_analysis(
                db=db,
                session_id=session_id,
                filename=file.filename,
                provider=provider,
                report_type=report_type,
                results=final_analysis_payload,
            )
            logger.info(f"✅ تم حفظ نتائج التحليل بنجاح في الداتابيز للسيشن: {session_id}")
        except Exception as db_err:
            logger.error(f"❌ فشل حفظ النتائج في الداتابيز: {str(db_err)}")
        # -------------------------------------------------------------

        final_response = {
            "status": "completed",
            "data": {
                "session_id": session_id,
                "filename": file.filename,
                "total_pages": total_pages,
                "analysis": final_analysis_payload,
            },
        }
        yield json.dumps(final_response) + "\n"

    return StreamingResponse(
        generate_progress(), media_type="application/x-ndjson"
    )


@router.post("/cad-boq")
async def extract_boq_from_cad(file: UploadFile):
  filename_lower = file.filename.lower()
  if not (filename_lower.endswith(".dxf") or filename_lower.endswith(".dwg")):
    raise HTTPException(
        status_code=400, detail="يرجى رفع ملف بصيغة .dxf أو .dwg"
    )

  contents = await file.read()
  raw_cad_result = analyze_cad_drawing(contents, file.filename)
  parsed_result = json.loads(raw_cad_result)

  return {
      "filename": file.filename,
      "total_pages": 1,
      "analysis": parsed_result,
  }


@router.post("/convert-dwg-to-dxf")
async def convert_dwg_to_dxf(file: UploadFile = File(...)):
  if not file.filename.lower().endswith(".dwg"):
    raise HTTPException(status_code=400, detail="الملف ليس DWG")

  contents = await file.read()

  session_id = str(uuid.uuid4())
  work_dir = f"/tmp/preview_{session_id}"
  in_dir = os.path.join(work_dir, "input")
  out_dir = os.path.join(work_dir, "output")

  os.makedirs(in_dir, exist_ok=True)
  os.makedirs(out_dir, exist_ok=True)

  try:
    temp_dwg = os.path.join(in_dir, file.filename)
    with open(temp_dwg, "wb") as f:
      f.write(contents)

    cmd = [
        "ODAFileConverter",
        in_dir,
        out_dir,
        "ACAD2018",
        "DXF",
        "0",
        "1",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)

    if result.returncode != 0:
      raise RuntimeError(
          f"ODA Converter failed with code {result.returncode}: {result.stderr}"
      )

    expected_dxf_name = os.path.splitext(file.filename)[0] + ".dxf"
    output_dxf = os.path.join(out_dir, expected_dxf_name)

    if not os.path.exists(output_dxf):
      dxf_files = [f for f in os.listdir(out_dir) if f.endswith(".dxf")]
      if dxf_files:
        output_dxf = os.path.join(out_dir, dxf_files[0])
      else:
        raise FileNotFoundError(
            "لم يتم العثور على ملف DXF الناتج بعد التحويل"
        )

    with open(output_dxf, "rb") as f:
      dxf_bytes = f.read()

    return Response(content=dxf_bytes, media_type="application/dxf")

  except subprocess.TimeoutExpired:
    raise HTTPException(
        status_code=500, detail="استغرقت عملية التحويل وقتاً أطول من المتوقع"
    )
  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"فشل تحويل الملف للمعاينة: {str(e)}"
    )

  finally:
    if os.path.exists(work_dir):
      shutil.rmtree(work_dir, ignore_errors=True)


@router.post("/convert-dwg-to-pdf")
async def convert_dwg_to_pdf(file: UploadFile = File(...)):
  if not file.filename.lower().endswith((".dwg", ".dxf")):
    raise HTTPException(status_code=400, detail="الملف ليس DWG أو DXF")

  contents = await file.read()

  session_id = str(uuid.uuid4())
  work_dir = f"/tmp/preview_{session_id}"
  in_dir = os.path.join(work_dir, "input")
  out_dir = os.path.join(work_dir, "output")

  os.makedirs(in_dir, exist_ok=True)
  os.makedirs(out_dir, exist_ok=True)

  try:
    temp_file = os.path.join(in_dir, file.filename)
    with open(temp_file, "wb") as f:
      f.write(contents)

    cmd = [
        "ODAFileConverter",
        in_dir,
        out_dir,
        "ACAD2018",
        "PDF",
        "0",
        "1",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      raise RuntimeError(
          f"ODA Converter failed with code {result.returncode}: {result.stderr}"
      )

    expected_pdf_name = os.path.splitext(file.filename)[0] + ".pdf"
    output_pdf = os.path.join(out_dir, expected_pdf_name)

    if not os.path.exists(output_pdf):
      pdf_files = [f for f in os.listdir(out_dir) if f.endswith(".pdf")]
      if pdf_files:
        output_pdf = os.path.join(out_dir, pdf_files[0])
      else:
        raise FileNotFoundError(
            "لم يتم العثور على ملف PDF الناتج بعد التحويل"
        )

    with open(output_pdf, "rb") as f:
      pdf_bytes = f.read()

    return Response(content=pdf_bytes, media_type="application/pdf")

  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"فشل تحويل الملف إلى PDF: {str(e)}"
    )

  finally:
    if os.path.exists(work_dir):
      shutil.rmtree(work_dir, ignore_errors=True)
