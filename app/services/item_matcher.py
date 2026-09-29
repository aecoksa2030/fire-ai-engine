import json
import os
import anthropic

def match_items_with_erp(extracted_components, erp_items):
    """استخدام الذكاء الاصطناعي (Claude) لمطابقة الأصناف المكتشفة من المخطط مع أصناف ERPNext"""
    if not erp_items or not extracted_components:
        return extracted_components

    # تجهيز قائمة خفيفة من أصناف ERPNext للنموذج
    erp_catalog = [
        {
            "code": item.get("item_code"),
            "name": item.get("item_name"),
            "moving_avg_cost": item.get("valuation_rate", 0.0),
            "standard_selling_price": item.get("standard_rate", 0.0),
        }
        for item in erp_items
    ]

    prompt = f"""
    You are an expert procurement and ERP matching engine for MEP and Fire Safety construction items.
    
    Tasks:
    1. For each extracted item from the CAD drawing, find the BEST matching item from the ERPCatalog list based on semantic meaning, component type, and engineering function.
    2. Map the exact fields from ERPCatalog to the response keys.
    
    Extracted Items from Drawing:
    {json.dumps(extracted_components, ensure_ascii=False)}
    
    ERP Catalog Items:
    {json.dumps(erp_catalog, ensure_ascii=False)}
    
    Return ONLY a raw JSON array of objects with these exact keys:
    - name: (original name from drawing)
    - count: (original count)
    - confidence: (original confidence)
    - supplier_type: (original supplier_type)
    - unit_cost_sar: (original unit_cost_sar)
    - total_cost_sar: (original total_cost_sar)
    - erp_item_code: (Matched ERP item_code or "NOT_FOUND")
    - erp_item_name: (Matched ERP item_name or "N/A")
    - erp_moving_avg_cost: (Matched ERP valuation_rate float)
    - erp_selling_price: (Matched ERP standard_rate float)
    """

    try:
        # تهيئة عميل Anthropic (يجب التأكد من وجود مفتاح ANTHROPIC_API_KEY في البيئة)
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        response = client.messages.create(
            model="claude-sonnet-4-6",  # يمكنك استخدام claude-3-haiku-20240307 إذا أردت سرعة وتكلفة أقل
            max_tokens=4096,
            system="You are an API that only returns raw, valid JSON arrays. Do not include markdown formatting like ```json or any conversational text.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # قراءة النص الصادر من كلود
        result_text = response.content[0].text.strip()
        
        # تنظيف إضافي تحسباً لو كلود أضاف علامات الماركدوان بالخطأ
        if result_text.startswith("```"):
            result_text = result_text.strip("`").removeprefix("json").strip()

        matched_data = json.loads(result_text)
        return matched_data
        
    except Exception as e:
        print(f"Error in Claude AI Item Matching: {e}")
        # في حال الفشل، نمرر الأصناف كما هي بدون تعطيل السيرفر
        return extracted_components