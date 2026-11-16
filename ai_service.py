import base64
import json
import requests
from config import GEMINI_API_KEY
from parser import parse_full_transaction

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

def get_best_model():
    return "gemini-3.8-flash"

def analyze_financial_text(text: str) -> dict:
    """
    Foydalanuvchi xabarini tahlil qiladi.
    Avval Gemini 3.8 Flash orqali urinadi, agar tarmoq sekin bo'lsa
    zudlik bilan mahalliy aqlli parserga o'tadi.
    """
    # Avval lokal parserdan tekshirib ko'ramiz
    local_res = parse_full_transaction(text)

    try:
        model = get_best_model()
        url = f"{GEMINI_API_URL}/{model}:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""
Siz hisobchi AI botsiz. Foydalanuvchi quyidagi xabarni yozdi:
"{text}"

Ushbu xabardan kirim yoki chiqim ekanligini, umumiy pul summasini (so'mda), xarid qilingan narsalar yoki daromad manbaini va kategoriyani aniqlang.
E'tibor bering: "ikkita non oldim 10 000 so'm" deyilganda miqdor 2 ta, ammo summa 10000 so'm! Miqdor sonini summa bilan adashtirmang!
"10 va uchta nol" deyilganda 10 000 so'm deb oling. "2 mln" = 2000000, "15k" = 15000.
Oylik, bonus, maosh, qo'shimcha daromad bo'lsa bu "kirim". Xaridlar, xarajatlar bo'lsa "chiqim".

Quyidagi qat'iy JSON formatida javob qaytaring:
{{
  "is_financial": true,
  "type": "kirim" yoki "chiqim",
  "amount": 10000.0,
  "category": "Oziq-ovqat" / "Transport" / "Kommunal" / "Oylik va Maosh" / "Bonus va Mukofot" / "Boshqa",
  "description": "2 ta non"
}}
Agar bu umuman moliya/hisob-kitobga aloqador bo'lmasa, "is_financial": false qiling.
Faqat valid JSON qaytaring.
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        
        # Qisqa timeout (5 soniya), agar tarmoq sekin bo'lsa lokal parser tez ishlaydi
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                raw_json = candidates[0]["content"]["parts"][0]["text"]
                parsed = json.loads(raw_json)
                if parsed.get("is_financial") and parsed.get("amount"):
                    return {
                        "type": parsed.get("type", "chiqim"),
                        "amount": float(parsed.get("amount")),
                        "category": parsed.get("category", "Ro'zg'or / Boshqa"),
                        "description": parsed.get("description", text),
                        "raw_text": text,
                        "source": "gemini"
                    }
    except Exception as e:
        # Gemini timeout yoki xato bo'lsa, lokal parserga o'tamiz
        pass

    # Agar Geminidan o'tmagan bo'lsa, lokal parser natijasini qaytaramiz
    if local_res:
        local_res["source"] = "local_parser"
        return local_res
        
    return None

def analyze_receipt_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict | None:
    """
    Do'kon yoki to'lov cheki rasmini Gemini AI orqali tahlil qiladi.
    Chekdagi jami summani, do'kon nomini va tovarlar ro'yxatini aniqlaydi.
    """
    try:
        model = get_best_model()
        url = f"{GEMINI_API_URL}/{model}:generateContent?key={GEMINI_API_KEY}"
        
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = """
Ushbu chek (kvitansiya) rasmini diqqat bilan tahlil qiling.
1. Chekdagi yakuniy to'langan jami summani (ИТОГО / JAMI / TOTAL) so'mda aniqlang.
2. Chek bergan do'kon/tashkilot nomi (masalan Korzinka, Makro, Havas, Apteka, Kafe...).
3. Xarid qilingan asosiy mahsulotlar/xizmatlar ro'yxati.
4. Mos toifani tanlang: Oziq-ovqat, Salomatlik (dorixona), Transport, Maishiy va Ro'zg'or, Kiyim, Kafe va Restoran, Boshqa.

Quyidagi qat'iy JSON formatida javob bering:
{
  "is_receipt": true,
  "type": "chiqim",
  "amount": 45000.0,
  "category": "Oziq-ovqat",
  "merchant": "Korzinka supermarket",
  "items": "Non, sut, tuxum",
  "description": "Korzinka: Non, sut, tuxum"
}
Agar rasm chek emas bo'lsa, "is_receipt": false qilib bering. Faqat JSON qaytaring.
"""
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_image
                        }
                    }
                ]
            }],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        
        response = requests.post(url, json=payload, timeout=8)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                raw_json = candidates[0]["content"]["parts"][0]["text"]
                parsed = json.loads(raw_json)
                if parsed.get("is_receipt") and parsed.get("amount"):
                    return {
                        "type": parsed.get("type", "chiqim"),
                        "amount": float(parsed.get("amount")),
                        "category": parsed.get("category", "Oziq-ovqat"),
                        "description": parsed.get("description", parsed.get("merchant", "Do'kon xaridi")),
                        "merchant": parsed.get("merchant", ""),
                        "items": parsed.get("items", "")
                    }
    except Exception as e:
        print(f"Receipt OCR xatosi: {e}")
        
    return None
