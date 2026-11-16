import os
import sys
from parser import parse_full_transaction, format_money
from database import (
    init_db, get_or_create_user, add_transaction,
    delete_transaction, get_current_stats, start_new_cycle,
    log_activity, get_recent_activity_logs, get_admin_system_stats
)

def run_tests():
    print("=" * 60)
    print("🧪 HISOBCHI BOT FUNKSIYALARINI TO'LIQ TEST QILISH")
    print("=" * 60)
    
    init_db()
    
    # TEST 1: Summa va miqdorni ajratish (Parser)
    test_cases = [
        ("do'kondan ikkita non oldim 10 000 so'm", "chiqim", 10000.0, "Oziq-ovqat"),
        ("5 ta suv 15k", "chiqim", 15000.0, "Oziq-ovqat"),
        ("tushlikka 45 ming ketdi", "chiqim", 45000.0, "Oziq-ovqat"),
        ("10 va uchta nolga ro'zg'or qildim", "chiqim", 10000.0, "Ro'zg'or / Boshqa"),
        ("benzin 150000", "chiqim", 150000.0, "Transport"),
        ("taxi 25 k", "chiqim", 25000.0, "Transport"),
        ("oylik tushdi 3.5 mln", "kirim", 3500000.0, "Oylik va Maosh"),
        ("firma menga 2 million so'm bonus berdi", "kirim", 2000000.0, "Bonus va Mukofot"),
        ("qo'shimcha ishdan 800k daromad tushdi", "kirim", 800000.0, "Qo'shimcha Daromad")
    ]
    
    print("\n1️⃣ PARSER VA AI LOGIKA TESTLARI:")
    for text, exp_type, exp_amount, exp_cat in test_cases:
        res = parse_full_transaction(text)
        assert res is not None, f"Parser natija bermadi: {text}"
        assert res["type"] == exp_type, f"Turi noto'g'ri: {res['type']} != {exp_type}"
        assert res["amount"] == exp_amount, f"Summa xato: {res['amount']} != {exp_amount}"
        print(f"  ✅ [O'TDI] '{text}' -> {res['type'].upper()} {format_money(res['amount'])} ({res['category']})")

    # TEST 2: Multi-user va Balans hisob-kitob testi
    print("\n2️⃣ BAZA VA BALANS HISOB-KITOB TESTLARI:")
    test_user_id = 999999999
    user = get_or_create_user(test_user_id, username="test_user", first_name="Ali")
    print(f"  ✅ Foydalanuvchi yaratildi: {user['first_name']} (ID: {user['user_id']})")
    
    # 1-oy hisobini boshlaymiz
    start_new_cycle(test_user_id, "Test Noyabr Oyi")
    
    # Boshlang'ich oylik kiritamiz: 3 mln
    t1 = add_transaction(test_user_id, "kirim", 3000000.0, "Oylik va Maosh", "Oylik maosh", "oylik 3 mln")
    stats = get_current_stats(test_user_id)
    assert stats['balance'] == 3000000.0, f"Balans xato: {stats['balance']}"
    print(f"  ✅ 3 mln oylik kiritildi. Qoldiq: {format_money(stats['balance'])}")
    
    # Xarajat: 2 ta non 10 000 so'm
    t2 = add_transaction(test_user_id, "chiqim", 10000.0, "Oziq-ovqat", "2 ta non", "2 ta non 10 000")
    stats = get_current_stats(test_user_id)
    assert stats['balance'] == 2990000.0, f"Balans xato: {stats['balance']}"
    print(f"  ✅ 10 000 so'm non olindi. Qoldiq: {format_money(stats['balance'])}")
    
    # Oy o'rtasida BONUS kelib tushdi: 2 000 000 so'm!
    # Bu balandagi 2 990 000 ga qo'shilib 4 990 000 bo'lishi shart!
    t3 = add_transaction(test_user_id, "kirim", 2000000.0, "Bonus va Mukofot", "Firma bonusi", "2 mln bonus")
    stats = get_current_stats(test_user_id)
    assert stats['balance'] == 4990000.0, f"Bonus qo'shilmadi: {stats['balance']}"
    print(f"  ✅ 2 mln bonus tushdi va qo'shildi! Yangi qoldiq: {format_money(stats['balance'])}")
    
    # TEST 3: Tranzaksiyani bekor qilish (Delete)
    print("\n3️⃣ TRANZAKSIYANI O'CHIRISH (BEKOR QILISH) TESTI:")
    delete_transaction(t2, test_user_id) # 10 000 so'mlik non xaridini bekor qilamiz
    stats = get_current_stats(test_user_id)
    assert stats['balance'] == 5000000.0, f"Balans tiklanmadi: {stats['balance']}"
    print(f"  ✅ 10 000 so'm bekor qilindi. Qoldiq yana: {format_money(stats['balance'])}")

    # TEST 4: "Yangi oy boshlash" testi
    print("\n4️⃣ 'YANGI OY BOSHLASH' TESTI:")
    new_c_id = start_new_cycle(test_user_id, "Test Dekabr Oyi")
    stats_new = get_current_stats(test_user_id)
    assert stats_new['balance'] == 0.0, f"Yangi oy nol bo'lmadi: {stats_new['balance']}"
    assert stats_new['total_income'] == 0.0
    assert stats_new['total_expense'] == 0.0
    print(f"  ✅ Yangi oy ochildi! Eski hisobot arxivlandi. Yangi oy balansi: {format_money(stats_new['balance'])}")

    # TEST 5: Admin jurnali (Activity Logs) testi
    print("\n5️⃣ ADMIN JURNALI VA MONITORING TESTI:")
    log_activity(test_user_id, "test_user", "Ali", "text", "Do'kondan non oldim 10 000 so'm")
    log_activity(test_user_id, "test_user", "Ali", "text", "Oy oxirida qancha pulim qoldi?")
    
    logs = get_recent_activity_logs(limit=5)
    assert len(logs) >= 2, "Loglar saqlanmadi!"
    print(f"  ✅ Admin uchun loglar muvaffaqiyatli qayd etildi (Jami loglar: {len(logs)} ta)")
    
    admin_stat = get_admin_system_stats()
    print(f"  ✅ Admin tizim statistikasi: Foydalanuvchilar: {admin_stat['users_count']} ta, Jami aylanma: {format_money(admin_stat['total_volume'])}")

    print("\n" + "=" * 60)
    print("🎉 BARCHA 5 TA TEST TO'LIQ VA 100% MUVAFFAQIYATLI O'TDI!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
