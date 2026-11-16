import re

# Toifalar lug'ati (avtomatik kategoriya aniqlash)
CATEGORIES_EXPENSE = {
    "Oziq-ovqat": [
        r"\bnon\b", r"\bsuv\b", r"\bgo['`]?sht\b", r"\bsut\b", r"\bqatiq\b", r"\btuxum\b",
        r"\bshakar\b", r"\bchoy\b", r"\byog['`]?\b", r"\bun\b", r"\bkartoshka\b", r"\bpiyoz\b",
        r"\bsabzi\b", r"\bmeva\b", r"\bolma\b", r"\bbanan\b", r"\bmuzqaymoq\b", r"\bshirinlik\b",
        r"\bbozor\b", r"\bkorzinka\b", r"\bmakro\b", r"\bhavas\b", r"\bdo['`]?kon\b", r"\bsupermarket\b",
        r"\btushlik\b", r"\bkechki ovqat\b", r"\bnonushta\b", r"\bsomsa\b", r"\bosh\b", r"\blavash\b",
        r"\bfastfood\b", r"\bkafe\b", r"\brestoran\b"
    ],
    "Transport": [
        r"\btaxi\b", r"\btaksi\b", r"\bbenzin\b", r"\bmetan\b", r"\bpropan\b", r"\bgaz\b",
        r"\bavtobus\b", r"\bmetro\b", r"\bmoy\b", r"\bzapchast\b", r"\bmoyka\b", r"\byandex\b",
        r"\byandeks\b", r"\byo['`]?lkira\b", r"\bbilet\b"
    ],
    "Kommunal va Aloqa": [
        r"\bsvet\b", r"\belektr\b", r"\bwifi\b", r"\binternet\b", r"\btelefon\b", r"\bbeeline\b",
        r"\bucell\b", r"\buztelecom\b", r"\bmobiuz\b", r"\bpaynet\b", r"\bkvartplata\b", r"\bmusor\b"
    ],
    "Kiyim va Go'zallik": [
        r"\bkiyim\b", r"\bshim\b", r"\bko['`]?ylak\b", r"\bkurtka\b", r"\boyoq kiyim\b",
        r"\btufli\b", r"\bkrossovka\b", r"\bsartarosh\b", r"\bparfyum\b", r"\bkosmetika\b"
    ],
    "Salomatlik": [
        r"\bdorixona\b", r"\bdori\b", r"\bapteka\b", r"\bdoktor\b", r"\bshifoxona\b", r"\bklinika\b"
    ],
    "Maishiy va Ro'zg'or": [
        r"\bporoshok\b", r"\bsovun\b", r"\bidish\b", r"\bmebel\b", r"\btexnika\b", r"\bremont\b", r"\busta\b"
    ]
}

CATEGORIES_INCOME = {
    "Oylik va Maosh": [r"\boylik\b", r"\bmaosh\b", r"\bzarplata\b", r"\bsalary\b"],
    "Bonus va Mukofot": [r"\bbonus\b", r"\bmukofot\b", r"\bpremiya\b", r"\bavans\b"],
    "Qo['`]?shimcha Daromad": [r"\bdaromad\b", r"\bkirim\b", r"\bfoyda\b", r"\btushum\b", r"\btushdi\b", r"\bqo['`]?shimcha\b", r"\bkarta\b"]
}

def parse_uzbek_amount(text: str) -> float | None:
    text_lower = text.lower().replace(",", ".").strip()
    
    # 1. "10 va uchta nol"
    zero_words = {
        "bitta": 1, "bir": 1, "ikkita": 2, "ikki": 2, "uchta": 3, "uch": 3,
        "to'rtta": 4, "to'rt": 4, "beshta": 5, "besh": 5, "oltita": 6, "olti": 6
    }
    zero_pattern = r'(\d+)\s+va\s+([a-z\'`]+)\s+nol'
    m_zero = re.search(zero_pattern, text_lower)
    if m_zero:
        base_num = int(m_zero.group(1))
        word = m_zero.group(2)
        count = zero_words.get(word, 3)
        return float(base_num * (10 ** count))

    # 2. "2.5 mln", "2 million", "10 mln"
    mln_pattern = r'(\d+(?:\.\d+)?)\s*(?:mln|million)'
    match_mln = re.search(mln_pattern, text_lower)
    if match_mln:
        return float(match_mln.group(1)) * 1_000_000

    # 3. "50k", "50 ming", "15k"
    k_pattern = r'(\d+(?:\.\d+)?)\s*(?:k|ming)\b'
    match_k = re.search(k_pattern, text_lower)
    if match_k:
        return float(match_k.group(1)) * 1_000

    # 4. "10 000 so'm", "10000 som", "25 000"
    tokens = re.finditer(r'(?:^|[^\d])(\d{1,3}(?:\s\d{3})+|\d+)(?:\s*(so[\'`]?m|som))?', text_lower)
    
    found_numbers = []
    for t in tokens:
        raw_val = t.group(1).replace(" ", "")
        has_som = bool(t.group(2))
        try:
            val = float(raw_val)
            found_numbers.append((val, has_som))
        except ValueError:
            continue
            
    if not found_numbers:
        return None
        
    if len(found_numbers) == 1:
        return found_numbers[0][0]
        
    som_tagged = [n for n in found_numbers if n[1]]
    if som_tagged:
        return som_tagged[-1][0]
        
    large_nums = [n for n in found_numbers if n[0] >= 1000]
    if large_nums:
        return max(large_nums, key=lambda x: x[0])[0]
        
    return found_numbers[-1][0]

def detect_transaction_type(text: str) -> str:
    text_lower = text.lower()
    if any(k in text_lower for k in ["oylik", "maosh", "bonus", "mukofot", "avans", "tushdi", "daromad", "kirim", "qo'shimcha ish"]):
        return "kirim"
    return "chiqim"

def detect_category(text: str, trans_type: str = "chiqim") -> str:
    text_lower = text.lower()
    
    if trans_type == "kirim":
        for cat, patterns in CATEGORIES_INCOME.items():
            for p in patterns:
                if re.search(p, text_lower):
                    return cat.replace("['`]", "'")
        return "Qo'shimcha Daromad"
    else:
        for cat, patterns in CATEGORIES_EXPENSE.items():
            for p in patterns:
                if re.search(p, text_lower):
                    return cat
        return "Ro'zg'or / Boshqa"

def extract_description(text: str, amount: float) -> str:
    clean = text
    clean = re.sub(r'\b\d+\s+va\s+[a-z\'`]+\s+nol\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b\d+(?:\.\d+)?\s*(?:so[\'`]?m|som|mln|million|k|ming)\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b\d{1,3}(?:\s\d{3})+\b', '', clean)
    clean = re.sub(r'\b\d+\b', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip(' ,.-:\t\n')
    
    if not clean:
        return "Noma'lum"
    return clean

def parse_full_transaction(text: str):
    amount = parse_uzbek_amount(text)
    if amount is None or amount <= 0:
        return None
        
    trans_type = detect_transaction_type(text)
    category = detect_category(text, trans_type)
    description = extract_description(text, amount)
    
    return {
        "type": trans_type,
        "amount": amount,
        "category": category,
        "description": description,
        "raw_text": text
    }

def format_money(amount: float) -> str:
    return f"{amount:,.0f}".replace(",", " ") + " so'm"
