# ai_engine.py — Gemini + BERTürk motor entegrasyonu

import streamlit as st
import google.generativeai as genai
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from config import (
    GEMINI_SYSTEM_PROMPT,
    BERT_MODEL_NAME,
    ANXIETY_HIGH_THRESHOLD,
    ANXIETY_MEDIUM_THRESHOLD,
)
from safety_filter import check_crisis, check_forbidden_content, get_crisis_response


# ─── Gemini Kurulumu ──────────────────────────────────────────────────────────

def init_gemini():
    """Gemini API'yi başlatır."""
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        st.error("⚠️ Gemini API anahtarı bulunamadı.")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # Hata alma ihtimaline karşı model ismini 'gemini-1.5-flash' olarak sadeleştiriyoruz
    # ve safety_settings formatını güncelliyoruz
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash"
    )
    return model

# ─── BERTürk Duygu/Kaygı Analizi ─────────────────────────────────────────────

@st.cache_resource(show_spinner="BERTürk modeli yükleniyor...")
def load_bert_model():
    """
    BERTürk tabanlı duygu/kaygı sınıflandırıcısını yükler.
    Hugging Face'den Türkçe duygu analizi modeli kullanılır.
    Not: Gerçek bir kaygı modeli mevcut değilse, genel duygu
    analizi modeli kullanılır ve skorlar normalize edilir.
    """
    try:
        # Türkçe duygu analizi için alternatif model
        classifier = pipeline(
            "text-classification",
            model="savasy/bert-base-turkish-sentiment-cased",
            tokenizer="savasy/bert-base-turkish-sentiment-cased",
            return_all_scores=True,
        )
        return classifier
    except Exception as e:
        st.warning(f"BERTürk modeli yüklenemedi: {e}. Kural tabanlı analiz kullanılacak.")
        return None


def analyze_emotional_state(text: str, bert_classifier) -> dict:
    """
    Kullanıcının yazdığı metni analiz eder.
    Döndürülen dict:
      - anxiety_score: 0.0–1.0 (yüksek = yüksek kaygı)
      - confidence_score: 0.0–1.0
      - problem_solving_score: 0.0–1.0
      - dominant_emotion: str
      - alert_level: "green" | "yellow" | "red"
    """
    if not text or len(text.strip()) < 10:
        return _neutral_state()

    # Kural tabanlı kaygı göstergeleri (BERTürk fallback için de kullanılır)
    anxiety_keywords = [
        "korkuyorum", "endişe", "kaygı", "başaramam", "berbat", "yalnız",
        "kimse", "nefret", "ağlamak", "sıkıldım", "bunaldım", "yoruldum",
        "yapamıyorum", "zor", "üzgün", "mutsuz", "sinirli",
    ]
    confidence_keywords = [
        "yapabilirim", "deneyeceğim", "güveniyorum", "başaracağım",
        "mutlu", "umut", "güzel", "iyi", "çözüm", "yardım", "teşekkür",
        "sevinç", "harika", "mümkün",
    ]
    problem_solving_keywords = [
        "çözüm", "deneyeceğim", "konuşacağım", "planım", "adım atacağım",
        "anlatacağım", "değiştireceğim", "öğreneceğim", "yardım isteyeceğim",
    ]

    text_lower = text.lower()

    # Kural tabanlı skorlar
    anxiety_count = sum(1 for kw in anxiety_keywords if kw in text_lower)
    confidence_count = sum(1 for kw in confidence_keywords if kw in text_lower)
    ps_count = sum(1 for kw in problem_solving_keywords if kw in text_lower)

    total = max(anxiety_count + confidence_count + ps_count, 1)
    rule_anxiety = min(anxiety_count / total, 1.0)
    rule_confidence = min(confidence_count / total, 1.0)
    rule_ps = min(ps_count / total, 1.0)

    # BERTürk varsa birleştir
    final_anxiety = rule_anxiety
    if bert_classifier:
        try:
            results = bert_classifier(text[:512])[0]
            # Modele göre etiketler değişebilir; negatif = kaygı proxy
            for r in results:
                label = r["label"].lower()
                if "negative" in label or "negatif" in label:
                    # BERTürk ve kural tabanlı ortalaması
                    final_anxiety = (rule_anxiety + r["score"]) / 2
                    break
        except Exception:
            pass  # Fallback: sadece kural tabanlı kullan

    # Alert seviyesi
    if final_anxiety >= ANXIETY_HIGH_THRESHOLD:
        alert = "red"
    elif final_anxiety >= ANXIETY_MEDIUM_THRESHOLD:
        alert = "yellow"
    else:
        alert = "green"

    # Baskın duygu
    scores = {
        "kaygı/stres": final_anxiety,
        "özgüven": rule_confidence,
        "problem çözme": rule_ps,
    }
    dominant = max(scores, key=scores.get)

    return {
        "anxiety_score": round(final_anxiety, 2),
        "confidence_score": round(rule_confidence, 2),
        "problem_solving_score": round(rule_ps, 2),
        "dominant_emotion": dominant,
        "alert_level": alert,
    }


def _neutral_state() -> dict:
    return {
        "anxiety_score": 0.0,
        "confidence_score": 0.5,
        "problem_solving_score": 0.3,
        "dominant_emotion": "nötr",
        "alert_level": "green",
    }


# ─── Hikâye Üretimi ───────────────────────────────────────────────────────────

def generate_story_continuation(
    gemini_model,
    story_so_far: str,
    user_input: str,
    theme_label: str,
    turn_number: int,
) -> str:
    """
    Mevcut hikâyeye kullanıcının katkısını ekleyip Gemini'den devam üretir.
    Üç metaforik seçenek + kısa empati sorusu döndürür.
    """
    # Güvenlik kontrolü
    if check_crisis(user_input):
        return get_crisis_response()
    if check_forbidden_content(user_input):
        return (
            "⚠️ Yazdığın içerik bu hikâye için uygun değil. "
            "Farklı bir yön deneyelim. Hikâyeni nasıl sürdürmek istersin?"
        )

    prompt = f"""
Mevcut hikâye teması: {theme_label}
Tur numarası: {turn_number}

Şimdiye kadar yazılan hikâye:
---
{story_so_far}
---

Kullanıcının bu tura katkısı:
"{user_input}"

Görevin:
1. Kullanıcının katkısını hikâyeye doğal biçimde entegre et (2-3 cümle).
2. Hikâyeyi ilerlet (3-4 cümle, umut ve güç temelli).
3. Karakterin önünde 3 metaforik seçenek sun (numaralı liste).
   Her seçenek: bir duygu + bir eylem metaforu içersin.
4. Son olarak: "Bu an seni nasıl hissettirdi?" sorusuyla bitir.

Eğer bu 5. tur veya sonrasıysa: Hikâyeyi güçlü ve umut dolu bir kapanışa taşı.
Karakterin "kendi hikâyesinin yazarı" olduğunu hissettiren bir son paragraf yaz.
"""

    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return (
            f"⚠️ Hikâye üretilirken bir sorun oluştu: {e}\n\n"
            "Lütfen tekrar dene veya farklı bir şey yaz."
        )


def generate_initial_story(
    gemini_model, starter_text: str, theme_label: str
) -> str:
    """Seçilen tema için ilk hikâye paragrafını üretir."""
    prompt = f"""
Tema: {theme_label}

Başlangıç metni:
"{starter_text}"

Görevin:
1. Bu başlangıç metnini alarak 4-5 cümlelik etkileyici bir açılış paragrafı yaz.
2. Karakteri 10-15 yaş arası bir ergen olarak canlandır.
3. Duygusal derinlik kat; okuyucuyu karakterle empati kurmaya davet et.
4. Metni şu soruyla bitir:
   "Bu hikâyeyi şimdi SEN yönlendiriyorsun. Karakterin şimdi ne yapmasını istersin?"
5. Ardından 3 metaforik seçenek sun (numaralı liste).
"""
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Hikâye başlatılamadı: {e}"
