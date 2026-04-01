# config.py — Uygulama yapılandırması ve sabit değerler

APP_TITLE = "Anlatı Dümenim 🧭"
APP_SUBTITLE = "Kendi hikâyeni yaz, duygularını keşfet."

# Yaş grubu
MIN_AGE = 10
MAX_AGE = 15

# Duygusal temalar (bibliyoterapötik başlangıç noktaları)
EMOTIONAL_THEMES = {
    "akran_zorbaligi": {
        "label": "😔 Arkadaşlarla yaşanan zorluklarla baş etmek",
        "starter": (
            "Okulun koridorlarında yürüyen Deniz, "
            "bugün de kimsenin kendisine yer açmadığını hissetti. "
            "Sırt çantası omzunda, kalbi ağır..."
        ),
    },
    "sinav_kaygisi": {
        "label": "😰 Sınav stresiyle mücadele etmek",
        "starter": (
            "Yarın büyük sınav vardı. Mira saatlerce çalışmıştı ama "
            "kitapların satırları gözünde dans ediyordu. "
            "Başarısız olursam ne olur? sorusu aklından çıkmıyordu..."
        ),
    },
    "aile_iletisimi": {
        "label": "🏠 Aile içindeki anlaşmazlıklarla başa çıkmak",
        "starter": (
            "Yemek masasında sessizlik hâkimdi. Kaan, annesinin "
            "söylediklerini duymuştu ama kelimeler boğazında düğümlenmişti. "
            "Nasıl anlatacaktı kendini?"
        ),
    },
    "ozguven": {
        "label": "💪 Özgüven ve kendini tanıma yolculuğu",
        "starter": (
            "Ayna karşısında duran Elif, bugün sahneye çıkacaktı. "
            "Sesi titriyordu ama içinde küçük bir ışık yanıyordu: "
            "Belki de yapabilirim..."
        ),
    },
    "yalnizlik": {
        "label": "🌧️ Yalnızlık ve aidiyet arayışı",
        "starter": (
            "Teneffüste herkes kendi grubundaydı. Arda, pencereden "
            "dışarıya bakarak düşündü: Acaba ben nereye aitim?"
        ),
    },
}

# Metaforik seçenek şablonları (her tur için Gemini üretecek, bunlar fallback)
METAPHOR_CHOICES_FALLBACK = [
    "🌱 Karakter, içindeki küçük bir cesaret tohumunu hissetti ve bir adım attı.",
    "🌊 Duygular büyük bir dalga gibi geldi; ama karakter nefes alarak dalgayı geçirdi.",
    "🔦 Karanlıkta bir ışık belirdi — bu bir çıkış yolu olabilirdi.",
]

# BERTürk model adı (Hugging Face)
BERT_MODEL_NAME = "dbmdz/bert-base-turkish-cased"

# Gemini sistem talimatı
GEMINI_SYSTEM_PROMPT = """
Sen "Anlatı Dümenim" adlı güvenli bibliyoterapi uygulamasının yapay zekâ motorusun.
Görevin: 10-15 yaş aralığındaki ergenlerin kendi hikâyelerini yazmasına rehberlik etmek.

TEMEL KURALLAR:
1. Her zaman destekleyici, sıcak ve empatik bir "mentor" tonu kullan.
2. Şiddet, cinsellik, nefret söylemi, zararlı davranış teşviki içeren HİÇBİR içerik üretme.
3. Çocuğun yazdığı metni asla küçümseme; her girişi değerli bul.
4. Hikâyeyi 3 metaforik seçenekle ilerlet; seçenekler umut, cesaret, empati temelli olsun.
5. Karakter isimlerini ve durumlarını çocuğun verdiği bilgilerle uyumlu tut.
6. Türkçe yaz. Dil sade, anlaşılır ve yaş grubuna uygun olsun.
7. Her yanıtta çocuğa kısa bir "Nasıl hissettirdi bu?" sorusu sor.
8. Eğer çocuk kendine zarar verme veya kriz içeren bir şey yazarsa,
   hikâyeyi durdur ve şunu söyle:
   "Seninle ilgili endişelendim. Lütfen bir yetişkine veya
    rehber öğretmenine bu duyguları anlat. Sen önemlisin. 💙"
"""

# Kaygı eşik değerleri (BERTürk skorları için)
ANXIETY_HIGH_THRESHOLD = 0.65
ANXIETY_MEDIUM_THRESHOLD = 0.35

# Kriz anahtar kelimeleri (güvenlik katmanı)
CRISIS_KEYWORDS = [
    "kendimi öldür", "ölmek istiyorum", "intihar", "kendime zarar",
    "yaşamak istemiyorum", "hepsini bitirmek istiyorum",
    "acı çekmek istiyorum", "canımı yakmak",
]
