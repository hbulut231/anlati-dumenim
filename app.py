# app.py — Streamlit ana arayüz

import streamlit as st
from config import (
    APP_TITLE, APP_SUBTITLE, EMOTIONAL_THEMES,
    METAPHOR_CHOICES_FALLBACK, MIN_AGE, MAX_AGE,
)
from ai_engine import (
    init_gemini, load_bert_model,
    analyze_emotional_state,
    generate_initial_story, generate_story_continuation,
)
from safety_filter import sanitize_user_input

# ─── Sayfa Ayarları ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Anlatı Dümenim",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─── CSS Özelleştirme ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Ana renk paleti */
    :root {
        --primary: #5B8DEF;
        --secondary: #A78BFA;
        --accent: #34D399;
        --warm: #FCD34D;
        --danger: #F87171;
        --bg-card: #1E293B;
    }

    /* Genel arka plan */
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%);
    }

    /* Hikâye kutusu */
    .story-box {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(91, 141, 239, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        font-family: 'Georgia', serif;
        font-size: 1.05rem;
        line-height: 1.8;
        color: #E2E8F0;
        box-shadow: 0 4px 24px rgba(91, 141, 239, 0.1);
    }

    /* Duygu göstergesi */
    .emotion-card {
        background: rgba(15, 23, 42, 0.7);
        border-radius: 12px;
        padding: 16px;
        border-left: 4px solid var(--accent);
        margin: 8px 0;
    }

    /* Seçenek butonları */
    .stButton > button {
        background: linear-gradient(135deg, #5B8DEF, #A78BFA);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 20px;
        font-size: 0.95rem;
        width: 100%;
        transition: all 0.3s ease;
        text-align: left;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(91, 141, 239, 0.4);
    }

    /* Başlık */
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #5B8DEF, #A78BFA, #34D399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    /* Tur sayacı */
    .turn-badge {
        display: inline-block;
        background: rgba(91, 141, 239, 0.2);
        border: 1px solid rgba(91, 141, 239, 0.4);
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.85rem;
        color: #93C5FD;
    }

    /* Yazar rozeti */
    .author-badge {
        background: linear-gradient(135deg, #FCD34D, #F97316);
        color: #1E293B;
        border-radius: 20px;
        padding: 6px 16px;
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-block;
        margin: 8px 0;
    }

    /* Uyarı kutuları */
    .alert-green { border-left-color: #34D399; }
    .alert-yellow { border-left-color: #FCD34D; }
    .alert-red { border-left-color: #F87171; }
</style>
""", unsafe_allow_html=True)


# ─── Oturum Durumu Başlatma ───────────────────────────────────────────────────
def init_session():
    defaults = {
        "phase": "welcome",          # welcome | theme_select | story | complete
        "selected_theme": None,
        "story_history": [],          # [{"role": "ai"|"user", "text": str}]
        "full_story_text": "",        # Birleşik hikâye metni
        "turn_count": 0,
        "emotion_log": [],            # Her tur duygu analizi kaydı
        "gemini_model": None,
        "bert_classifier": None,
        "user_name": "",
        "author_name": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────

def render_emotion_dashboard():
    """Sidebar'da duygu analizi göstergesi."""
    if not st.session_state.emotion_log:
        return

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Duygu Yolculuğun")

    latest = st.session_state.emotion_log[-1]
    alert = latest["alert_level"]
    color_map = {"green": "🟢", "yellow": "🟡", "red": "🔴"}

    st.sidebar.markdown(f"**Baskın duygu:** {latest['dominant_emotion'].capitalize()}")

    # Kaygı çubuğu
    st.sidebar.markdown("**Kaygı düzeyi:**")
    st.sidebar.progress(latest["anxiety_score"])

    # Özgüven çubuğu
    st.sidebar.markdown("**Özgüven:**")
    st.sidebar.progress(latest["confidence_score"])

    # Problem çözme
    st.sidebar.markdown("**Problem çözme odağı:**")
    st.sidebar.progress(latest["problem_solving_score"])

    # Durum ikonu
    status_text = {
        "green": "✅ Dengeli bir anlatı akışı",
        "yellow": "💛 Duygular yoğunlaşıyor, hikâye seni destekliyor",
        "red": "💙 Zorlu duygular — devam etmeden önce bir mola ver",
    }
    st.sidebar.info(f"{color_map[alert]} {status_text[alert]}")

    # Tarihçe grafiği
    if len(st.session_state.emotion_log) > 1:
        import pandas as pd
        df = pd.DataFrame(st.session_state.emotion_log)
        df.index = [f"Tur {i+1}" for i in range(len(df))]
        st.sidebar.line_chart(
            df[["anxiety_score", "confidence_score", "problem_solving_score"]],
            use_container_width=True,
        )


def render_story_box(text: str):
    """Hikâye metnini stil kutusu içinde göster."""
    st.markdown(f'<div class="story-box">{text}</div>', unsafe_allow_html=True)


def render_author_badge():
    st.markdown(
        f'<div class="author-badge">✍️ Yazar: {st.session_state.author_name or "Sen"}</div>',
        unsafe_allow_html=True,
    )


# ─── Aşama: Karşılama ─────────────────────────────────────────────────────────
def phase_welcome():
    st.markdown(f'<h1 class="main-title">{APP_TITLE}</h1>', unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#94A3B8; font-size:1.1rem'>{APP_SUBTITLE}</p>",
                unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    ### Merhaba! 👋

    **Anlatı Dümenim**, *senin* hikâyeni yazmana yardımcı olan güvenli bir alan.

    Burada:
    - 🖊️ Kendi karakterini yaratır ve hikâyeni yönetirsin
    - 💬 Duygularını güvenli bir şekilde keşfedersin
    - 🌱 Her tur seni biraz daha güçlü kılar

    > *"En iyi hikâye, senin anlattığın hikâyedir."*
    """)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("📝 Adın ne? (İstersen takma ad kullanabilirsin)",
                             placeholder="örn. Deniz, Yıldız, Kahraman...")
    with col2:
        author = st.text_input("✍️ Yazar adın ne olsun?",
                               placeholder="örn. Gece Yazarı, Söz Ustası...")

    age_ok = st.checkbox(
        f"✅ {MIN_AGE}-{MAX_AGE} yaş aralığındayım ve bu uygulamayı kullanmak istiyorum."
    )

    if age_ok and name:
        st.session_state.user_name = name
        st.session_state.author_name = author or name

        if st.button("🚀 Hikâyemi Başlat!", use_container_width=True):
            # Modelleri yükle
            with st.spinner("Anlatı motoru hazırlanıyor..."):
                st.session_state.gemini_model = init_gemini()
                st.session_state.bert_classifier = load_bert_model()
            st.session_state.phase = "theme_select"
            st.rerun()
    elif not age_ok and name:
        st.info("Devam etmek için yaş onayı kutucuğunu işaretle.")


# ─── Aşama: Tema Seçimi ───────────────────────────────────────────────────────
def phase_theme_select():
    st.markdown(f'<h1 class="main-title">🎭 Hikâyeni Seç</h1>', unsafe_allow_html=True)
    st.markdown(
        f"Merhaba **{st.session_state.user_name}**! "
        "Bugün hangi duyguyu keşfetmek istiyorsun?",
        unsafe_allow_html=False,
    )
    st.markdown("---")

    for key, theme in EMOTIONAL_THEMES.items():
        if st.button(theme["label"], key=f"theme_{key}", use_container_width=True):
            st.session_state.selected_theme = key

            # İlk hikâyeyi oluştur
            with st.spinner("Hikâyen şekilleniyor..."):
                starter = theme["starter"]
                initial = generate_initial_story(
                    st.session_state.gemini_model,
                    starter,
                    theme["label"],
                )
            st.session_state.story_history.append({"role": "ai", "text": initial})
            st.session_state.full_story_text = starter + "\n\n" + initial
            st.session_state.phase = "story"
            st.rerun()

    st.markdown("---")
    if st.button("← Geri", use_container_width=False):
        st.session_state.phase = "welcome"
        st.rerun()


# ─── Aşama: Hikâye ───────────────────────────────────────────────────────────
def phase_story():
    theme_key = st.session_state.selected_theme
    theme = EMOTIONAL_THEMES[theme_key]

    # Sidebar
    st.sidebar.markdown(f"### 🧭 {APP_TITLE}")
    render_author_badge()
    st.sidebar.markdown(f"**Tema:** {theme['label']}")
    st.sidebar.markdown(
        f'<span class="turn-badge">Tur {st.session_state.turn_count + 1} / 6</span>',
        unsafe_allow_html=True,
    )
    render_emotion_dashboard()

    # Ana başlık
    st.markdown(f'<h2 class="main-title" style="font-size:1.8rem">✍️ Hikâyen</h2>',
                unsafe_allow_html=True)

    # Hikâye geçmişi
    for entry in st.session_state.story_history:
        if entry["role"] == "ai":
            render_story_box(entry["text"].replace("\n", "<br>"))
        else:
            st.markdown(
                f'<div style="background:rgba(167,139,250,0.1);border-left:3px solid #A78BFA;'
                f'border-radius:8px;padding:12px;margin:8px 0;color:#C4B5FD;">'
                f'💬 <em>{entry["text"]}</em></div>',
                unsafe_allow_html=True,
            )

    # Tamamlandı kontrolü
    if st.session_state.turn_count >= 6:
        st.session_state.phase = "complete"
        st.rerun()
        return

    st.markdown("---")
    st.markdown("### 🖊️ Sıra Sende!")

    # Seçenek veya serbest yazım sekmesi
    tab1, tab2 = st.tabs(["📌 Metaforik Seçenekler", "✏️ Kendi Kelimelerinle Yaz"])

    with tab1:
        st.markdown("*Aşağıdaki seçeneklerden birini tıkla:*")
        choices = METAPHOR_CHOICES_FALLBACK  # Gemini çıktısından parse edilebilir
        for i, choice in enumerate(choices):
            if st.button(choice, key=f"choice_{i}_{st.session_state.turn_count}",
                         use_container_width=True):
                _process_user_input(choice, theme)

    with tab2:
        user_text = st.text_area(
            "Karakterin ne yapmasını, ne hissetmesini ya da ne söylemesini istersin?",
            placeholder="Kendi kelimelerinle yaz... (en az 10 karakter)",
            max_chars=500,
            height=120,
            key=f"free_input_{st.session_state.turn_count}",
        )
        if st.button("📨 Hikâyeme Ekle", use_container_width=True,
                     key=f"submit_{st.session_state.turn_count}"):
            if len(user_text.strip()) >= 10:
                _process_user_input(user_text, theme)
            else:
                st.warning("Lütfen en az 10 karakter yaz.")

    # Güvenlik notu
    st.markdown(
        '<p style="color:#475569;font-size:0.8rem;text-align:center;margin-top:16px">'
        '🔒 Bu alan pedagojik güvenlik filtreleriyle korunmaktadır.</p>',
        unsafe_allow_html=True,
    )


def _process_user_input(user_input: str, theme: dict):
    """Kullanıcı girdisini işle: temizle → analiz et → Gemini'ye gönder → kaydet."""
    clean_input = sanitize_user_input(user_input)

    # Duygu analizi
    emotion_data = analyze_emotional_state(
        clean_input, st.session_state.bert_classifier
    )
    st.session_state.emotion_log.append(emotion_data)

    # Kırmızı uyarı: hikâyeyi durdur
    if emotion_data["alert_level"] == "red":
        st.error(
            "💙 **Dikkat:** Yazdıklarında çok yoğun duygular fark ettim. "
            "Bir mola vermeni ve güvendiğin bir yetişkinle konuşmanı öneririm.\n\n"
            "**Türkiye Çocuk Destek Hattı: 183**"
        )
        return

    # Hikâye devamını üret
    with st.spinner("Hikâyen şekilleniyor..."):
        st.session_state.turn_count += 1
        continuation = generate_story_continuation(
            st.session_state.gemini_model,
            st.session_state.full_story_text,
            clean_input,
            theme["label"],
            st.session_state.turn_count,
        )

    # Kaydet
    st.session_state.story_history.append({"role": "user", "text": clean_input})
    st.session_state.story_history.append({"role": "ai", "text": continuation})
    st.session_state.full_story_text += f"\n\n[{clean_input}]\n\n{continuation}"

    st.rerun()


# ─── Aşama: Tamamlandı ───────────────────────────────────────────────────────
def phase_complete():
    st.balloons()
    st.markdown(f'<h1 class="main-title">🏆 Hikâyen Tamamlandı!</h1>',
                unsafe_allow_html=True)

    render_author_badge()

    st.markdown(f"""
    ### Tebrikler, **{st.session_state.user_name}**! 🌟

    Bu hikâyeyi **sen** yazdın. Her kelime, her seçim, **seninindi**.

    > *"Kendi hikâyesini yazan kişi, hayatının da yazarı olmayı öğrenir."*
    """)

    # Yolculuk özeti
    if st.session_state.emotion_log:
        first = st.session_state.emotion_log[0]
        last = st.session_state.emotion_log[-1]
        delta_anxiety = first["anxiety_score"] - last["anxiety_score"]
        delta_ps = last["problem_solving_score"] - first["problem_solving_score"]

        st.markdown("---")
        st.markdown("### 📊 Duygusal Yolculuğun")

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Kaygı Değişimi",
            f"{last['anxiety_score']:.0%}",
            f"{delta_anxiety:+.0%}" if delta_anxiety else "—",
            delta_color="inverse",
        )
        col2.metric(
            "Problem Çözme",
            f"{last['problem_solving_score']:.0%}",
            f"{delta_ps:+.0%}" if delta_ps else "—",
        )
        col3.metric(
            "Özgüven",
            f"{last['confidence_score']:.0%}",
        )

    # Hikâyeyi indir
    st.markdown("---")
    st.markdown("### 📖 Senin Hikâyen")
    with st.expander("Tüm hikâyeyi gör ve indir"):
        st.text_area("Hikâyen:", st.session_state.full_story_text, height=400)
        st.download_button(
            "📥 Hikâyemi İndir (.txt)",
            data=st.session_state.full_story_text,
            file_name=f"anlati_dumenim_{st.session_state.author_name}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Yeni Hikâye Yaz", use_container_width=True):
            # Oturumu sıfırla (modelleri koru)
            gemini = st.session_state.gemini_model
            bert = st.session_state.bert_classifier
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_session()
            st.session_state.gemini_model = gemini
            st.session_state.bert_classifier = bert
            st.session_state.phase = "theme_select"
            st.rerun()
    with col2:
        st.markdown(
            '<p style="color:#64748B;font-size:0.85rem;padding-top:8px">'
            '💙 Zorluklar yaşıyorsan rehber öğretmenine danışmayı unutma.</p>',
            unsafe_allow_html=True,
        )


# ─── Ana Yönlendirici ─────────────────────────────────────────────────────────
def main():
    init_session()

    phase = st.session_state.phase
    if phase == "welcome":
        phase_welcome()
    elif phase == "theme_select":
        phase_theme_select()
    elif phase == "story":
        phase_story()
    elif phase == "complete":
        phase_complete()


if __name__ == "__main__":
    main()
