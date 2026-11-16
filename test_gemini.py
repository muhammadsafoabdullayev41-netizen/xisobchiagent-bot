import requests
import json
from config import GEMINI_API_KEY

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

tests = [
    "do'kondan ikkita non oldim 10 000 so'm",
    "beshta suv 15k",
    "firma tomonidan 2 million so'm bonus tushdi",
    "oylik oldim 4.5 mln"
]

for t in tests:
    prompt = f"""
Siz professional shaxsiy hisobchisiz. Foydalanuvchi quyidagi matnni yozdi:
"{t}"

Quyidagi qat'iy JSON formatda qaytaring:
{{
  "is_financial": true,
  "type": "kirim" yoki "chiqim",
  "amount": faqat son raqamda so'm birligida (masalan 10000 yoki 15000 yoki 2000000 yoki 4500000. Miqdor soni (2 ta, 5 ta) emas, aynan pul summasi bo'lishi shart!),
  "category": "Oziq-ovqat" yoki "Transport" yoki "Oylik" yoki "Bonus" yoki "Maishiy" yoki "Kommunal" yoki "Boshqa",
  "description": "mahsulot yoki tushum manbai qisqacha nomi"
}}
Faqat JSON qaytaring.
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    r = requests.post(url, json=payload, timeout=20)
    print(f"INPUT: {t}")
    print(f"OUTPUT: {r.json()['candidates'][0]['content']['parts'][0]['text']}\n")
