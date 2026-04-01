# safety_filter.py — Pedagojik güvenlik katmanı

import re
from config import CRISIS_KEYWORDS

# Yasaklı içerik kalıpları (regex tabanlı)
FORBIDDEN_PATTERNS = [
    r"\b(cinsel|müstehcen|pornograf)\w*\b",
    r"\b(uyuşturucu|esrar|eroin|kokain)\w*\b",
    r"\b(silah|bomba|patlayıcı)\w*\b",
    r"\b(küfür|hakaret kalıpları)\w*\b",  # Genişletilebilir
]


def check_crisis(text: str) -> bool:
    """
    Kullanıcı metninde kriz göstergesi olup olmadığını kontrol eder.
    Herhangi bir kriz anahtar kelimesi varsa True döner.
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in CRISIS_KEYWORDS)


def check_forbidden_content(text: str) -> bool:
    """
    Metinde yasak içerik kalıpları var mı kontrol eder.
    True = yasak içerik tespit edildi.
    """
    text_lower = text.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def sanitize_user_input(text: str) -> str:
    """
    Kullanıcı girdisini temizler:
    - Aşırı uzun girdileri kırpar (500 karakter)
    - Baştaki/sondaki boşlukları temizler
    """
    text = text.strip()
    if len(text) > 500:
        text = text[:500] + "..."
    return text


def get_crisis_response() -> str:
    return (
        "💙 **Seninle ilgili endişelendim.**\n\n"
        "Yazdıklarından çok zor duygular yaşadığını anlıyorum. "
        "Bu duygular gerçek ve önemli. Lütfen şu anda güvendiğin "
        "bir yetişkine — anne, baba, öğretmen veya rehber öğretmenine — "
        "nasıl hissettiğini anlat.\n\n"
        "**Türkiye Çocuk İstismarını Önleme Hattı: 183**\n\n"
        "Sen değerlisin. Bu hikâyeye devam etmeden önce birileriyle "
        "konuşman çok önemli. 💙"
    )
