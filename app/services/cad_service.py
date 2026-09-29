import json
import os
import shutil
import uuid
import ezdxf
from ezdxf.addons import odafc

def analyze_cad_drawing(file_bytes: bytes, filename: str) -> str:
    file_ext = filename.split(".")[-1].lower()
    
    # إنشاء معرف فريد لكل طلب عشان الملفات ما تتدخلش ببعض
    session_id = str(uuid.uuid4())
    work_dir = f"/tmp/cad_work_{session_id}"
    os.makedirs(work_dir, exist_ok=True)

    try:
        if file_ext == "dwg":
            temp_dwg = os.path.join(work_dir, filename)
            with open(temp_dwg, "wb") as f:
                f.write(file_bytes)

            # استخدام odafc مباشرة لقراءة ملف الـ DWG كوثيقة ezdxf
            try:
                doc = odafc.readfile(temp_dwg)
            except Exception as oda_err:
                return json.dumps({
                    "system_type": "AutoCAD DWG",
                    "components": [],
                    "flagged_unclear_areas": [
                        f"فشل قراءة ملف DWG عبر المحول: {str(oda_err)}"
                    ],
                }, ensure_ascii=False)
        else:
            # لو الملف DXF عادي بنقراه من البايتس مباشرة
            doc = ezdxf.readstream(file_bytes)

        msp = doc.modelspace()

        component_counts = {
            "Smoke Detector": 0,
            "Heat Detector": 0,
            "Manual Pull Station": 0,
            "Speaker / Strobe Device": 0,
            "Strobe Device": 0,
            "Fire Alarm Control Panel (FACP)": 0,
            "Monitor / Control Module": 0,
        }

        keywords_map = {
            "smoke": "Smoke Detector",
            "heat": "Heat Detector",
            "pull": "Manual Pull Station",
            "strobe": "Strobe Device",
            "speaker": "Speaker / Strobe Device",
            "facp": "Fire Alarm Control Panel (FACP)",
            "panel": "Fire Alarm Control Panel (FACP)",
            "module": "Monitor / Control Module",
        }

        for insert in msp.query("INSERT"):
            block_name = insert.dxf.name.lower()
            layer_name = insert.dxf.layer.lower()

            for key, category in keywords_map.items():
                if key in block_name or key in layer_name:
                    component_counts[category] += 1
                    break

        components_result = [
            {"name": name, "count": count, "confidence": "high"}
            for name, count in component_counts.items()
            if count > 0
        ]

        return json.dumps(
            {
                "system_type": "Fire Alarm System (CAD Native)",
                "components": components_result,
                "flagged_unclear_areas": [],
            },
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps({
            "system_type": "Fire Alarm System",
            "components": [],
            "flagged_unclear_areas": [f"خطأ في معالجة ملف الأوتوكاد: {str(e)}"],
        }, ensure_ascii=False)

    finally:
        # تنظيف مجلد العمل المؤقت تلقائياً
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)