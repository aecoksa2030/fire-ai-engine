import os
import requests


class ERPNextService:

  def __init__(self):
    self.base_url = os.environ.get(
        "ERPNEXT_URL", "https://erp.advanced-elements.com"
    ).rstrip("/")
    self.api_key = os.environ.get("ERPNEXT_API_KEY", "f690e70e74f78b0")
    self.api_secret = os.environ.get("ERPNEXT_API_SECRET", "db154916905591b")

    self.headers = {
        "Authorization": f"token {self.api_key}:{self.api_secret}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

  def get_all_items_with_prices(self):
    """جلب الأصناف من ERPNext ودمج الأسعار من جدول Item Price ومن جدول Item"""
    # 1. جلب الأصناف
    items_url = f"{self.base_url}/api/resource/Item"
    items_params = {
        "fields": (
            '["name", "item_code", "item_name", "valuation_rate",'
            ' "standard_rate"]'
        ),
        "limit_page_length": 2000,
    }

    # 2. جلب قوائم الأسعار (Item Price)
    prices_url = f"{self.base_url}/api/resource/Item Price"
    prices_params = {
        "fields": '["item_code", "price_list_rate", "price_list"]',
        "limit_page_length": 5000,
    }

    item_prices_map = {}

    # جلب قائمة الأسعار
    try:
      p_res = requests.get(
          prices_url, headers=self.headers, params=prices_params, timeout=10
      )
      if p_res.status_code == 200:
        for p in p_res.json().get("data", []):
          code = p.get("item_code")
          rate = float(p.get("price_list_rate", 0.0) or 0.0)
          if code and rate > 0:
            item_prices_map[code] = rate
    except Exception as pe:
      print(f"⚠️ لم نتمكن من جلب Item Price: {pe}")

    # جلب الأصناف ودمج الأسعار
    try:
      response = requests.get(
          items_url, headers=self.headers, params=items_params, timeout=15
      )

      if response.status_code == 200:
        raw_items = response.json().get("data", [])
        formatted_items = []

        for item in raw_items:
          code = item.get("item_code") or item.get("name")
          name = item.get("item_name") or item.get("name")

          # سعر الصنف المباشر أو من قائمة الأسعار
          val_rate = float(item.get("valuation_rate", 0.0) or 0.0)
          std_rate = float(item.get("standard_rate", 0.0) or 0.0)

          # إذا كان سعر الصنف 0، نتحقق من قائمة الأسعار Item Price
          price_list_rate = item_prices_map.get(code, 0.0)
          final_selling_price = std_rate if std_rate > 0 else price_list_rate

          formatted_items.append({
              "item_code": code,
              "item_name": name,
              "valuation_rate": val_rate,
              "standard_rate": final_selling_price,
          })

        print(
            f"✅ [ERPNext] Loaded {len(formatted_items)} items with price"
            " integration."
        )
        return formatted_items
      else:
        print(f"❌ [ERPNext Error {response.status_code}]: {response.text}")
        return []

    except Exception as e:
      print(f"❌ [ERPNext Exception]: {str(e)}")
      return []