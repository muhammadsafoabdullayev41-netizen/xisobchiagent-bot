# 🤖 Xisobchi Agent Bot (Shaxsiy Aqlli Hisobchi)

Telegram uchun sun'iy intellekt (Google Gemini) bilan qurollangan aqlli shaxsiy moliya va hisobchi bot.

## 🌟 Imkoniyatlari:
- **Kirim va Chiqim hisobi:** Boshlang'ich oylik maosh, oy o'rtasida tushgan bonuslar va qo'shimcha daromadlarni to'g'ri hisoblaydi (bonuslarni balansdan ayirib yubormaydi, balki qo'shadi).
- **Aqlli miqdor va summa tahlili:** "Do'kondan 2 ta non oldim 10 000 so'm" deyilganda miqdor (2 ta) emas, balki aynan 10 000 so'm xarajat qilib olinadi.
- **Barcha formatlar:** "so'm", "ming", "k", "mln", "10 va uchta nol" kabi barcha ifodalarni tushunadi.
- **Cheklarni skanerlash (AI):** Chek fotosuratini yuborsangiz, Google Gemini multimodal AI umumiy summani va do'kon nomini o'qib xarajatga yozadi.
- **Yangi oy boshlash:** "Yangi oy boshlash" tugmasi bilan eski oylik hisobot arxivlanadi va yangi oy hisobi ochiladi.
- **Maxsus Yashirin Admin Panel:** Faqat belgilangan Admin ID uchun ishlaydi, bot foydalanuvchilari ro'yxatini va ular yozgan barcha xabarlar jurnalini ko'rsatadi.

---

## 🚀 Render.com da 24/7 Bepul Ishga Tushirish Qo'llanmasi:

1. **GitHub repozitoriyaga yuklash:**
   ```bash
   git init
   git add .
   git commit -m "Hisobchi bot 24/7 versiyasi"
   git branch -M main
   git remote add origin https://github.com/muhammadsafoabdullayev41-netizen/xisobchiagent-bot.git
   git push -u origin main
   ```

2. **Render.com da yangi Web Service ochish:**
   - [Render.com](https://render.com) ga kiring va GitHub profilingiz bilan kiring.
   - **New +** tugmasini bosing -> **Web Service** ni tanlang.
   - GitHub repozitoriyangizni (`xisobchiagent-bot`) ulang.
   - Sozlamalarni quyidagicha to'ldiring:
     - **Name:** `xisobchiagent-bot`
     - **Language:** `Python 3`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python bot.py`
     - **Instance Type:** `Free`

3. **Environment Variables (Maxfiy Kalitlar) bo'limiga kiriting:**
   - `BOT_TOKEN`: Sizning bot tokeningiz
   - `GEMINI_API_KEY`: Sizning Google AI Studio kalitingiz
   - `ADMIN_ID`: Sizning Telegram ID raqamingiz (`5017047967`)

4. **24/7 Uyg'oq (Awake) qilib qo'yish (Cron-Job orqali):**
   - Render bepul xizmati 15 daqiqada uxlab qolmasligi uchun loyihaga `keep_alive.py` mini-serveri o'rnatilgan.
   - [cron-job.org](https://cron-job.org) yoki [uptimerobot.com](https://uptimerobot.com) saytiga bepul kiring.
   - Yangi monitor / cron job yarating:
     - **URL:** `https://xisobchiagent-bot.onrender.com` (Render bergan URL)
     - **Interval:** Har 10 daqiqada (Every 10 minutes)
   - Shunda server har 10 daqiqada uyg'onib turadi va bot 24 soat uzluksiz, bir umr o'chmasdan ishlaydi!
