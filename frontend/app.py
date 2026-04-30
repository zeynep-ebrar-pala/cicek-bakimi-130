import streamlit as st
import pandas as pd
import datetime
import random
import os
import json
import re
import base64
import unicodedata
import io
import google.generativeai as genai
import sys
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

# Sayfa yapılandırması (MUTLAK EN ÜSTTE OLMALI)
st.set_page_config(
    page_title="Ev Güzeli AI | Akıllı Bitki Bakımı",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# .env dosyasını yükle
load_dotenv()

# Proje kök dizinini ve backend klasörünü yola ekle
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "backend"))

from data import PLANTS, DISEASES
from utils import get_image_base64
from database import init_db, add_to_garden, get_my_garden, update_care, add_log, get_logs, get_learned_knowledge
from agent import BotanicaAgent
from dev_layer import DevLayer

# Hem `streamlit run frontend/app.py` hem de `streamlit run app.py` için uyumlu import
try:
    from frontend.decorations import inject_garland
except Exception:
    from decorations import inject_garland

# Veritabanını başlat
init_db()

# Çiçek Sarmaşığını Enjekte Et
inject_garland()

# CSS Yükleme
css_path = Path(__file__).parent / "style.css"
with open(css_path, encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- AI AYARLARI ---
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = os.getenv("GROQ_API_KEY") or ""

def configure_ai():
    if st.session_state.api_key:
        try:
            genai.configure(api_key=st.session_state.api_key)
            return True
        except:
            return False
    return False

def parse_ai_json_response(raw_text):
    """Gemini cevabından JSON benzeri içeriği güvenli şekilde ayrıştırır."""
    if not raw_text:
        return {}

    cleaned = raw_text.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start:end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    parsed = {}
    patterns = {
        "plant_name": r'"plant_name"\s*:\s*"([^"]+)"|plant_name\s*:\s*([^,\n]+)',
        "latin_name": r'"latin_name"\s*:\s*"([^"]+)"|latin_name\s*:\s*([^,\n]+)',
        "visual_description": r'"visual_description"\s*:\s*"([^"]+)"|visual_description\s*:\s*([^,\n]+)',
        "diagnosis": r'"diagnosis"\s*:\s*"([^"]+)"|diagnosis\s*:\s*([^,\n]+)',
        "treatment": r'"treatment"\s*:\s*"([^"]+)"|treatment\s*:\s*([^,\n]+)',
        "cause": r'"cause"\s*:\s*"([^"]+)"|cause\s*:\s*([^,\n]+)',
    }
    lowered = cleaned.lower()
    for key, pattern in patterns.items():
        match = re.search(pattern, lowered)
        if match:
            parsed[key] = (match.group(1) or match.group(2) or "").strip()
    return parsed

def normalize_text(value):
    if not value:
        return ""
    txt = str(value).lower().strip()
    txt = "".join(ch for ch in unicodedata.normalize("NFKD", txt) if not unicodedata.combining(ch))
    txt = re.sub(r"[^a-z0-9\s]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def _to_data_uri(uploaded_file):
    if not uploaded_file:
        return ""
    uploaded_file.seek(0)
    img_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    mime_type = uploaded_file.type or "image/jpeg"
    encoded = base64.b64encode(img_bytes).decode()
    return f"data:{mime_type};base64,{encoded}"

def optimize_data_uri_for_zoom(image_src, max_size=1400, jpeg_quality=82):
    """
    Zoom bileşeni için görseli küçültüp sıkıştırır.
    Efekti korurken Cloud'da beyaz ekran/freeze riskini azaltır.
    """
    if not image_src or not str(image_src).startswith("data:image/"):
        return image_src
    try:
        header, b64_data = image_src.split(",", 1)
        raw = base64.b64decode(b64_data)
        img = Image.open(io.BytesIO(raw))
        img = img.convert("RGB")
        img.thumbnail((max_size, max_size))

        out = io.BytesIO()
        img.save(out, format="JPEG", quality=jpeg_quality, optimize=True)
        optimized_b64 = base64.b64encode(out.getvalue()).decode()
        return f"data:image/jpeg;base64,{optimized_b64}"
    except Exception:
        return image_src

def build_dynamic_plant_profile(ai_data, image_file=None):
    """Kütüphanede yoksa AI verisinden geçici bitki profili üretir."""
    plant_name = ai_data.get("plant_name") or ai_data.get("name") or "Bilinmeyen Bitki"
    latin_name = ai_data.get("latin_name") or "Tür tespit edilemedi"
    summary = ai_data.get("visual_description") or "Bu bitki kütüphanede bulunmuyor; AI görselden geçici profil oluşturdu."
    diagnosis = ai_data.get("diagnosis") or "Belirgin bir hastalık bulgusu net değil."
    treatment = ai_data.get("treatment") or "Dengeli ışık, kontrollü sulama ve yaprak takibi önerilir."
    cause = ai_data.get("cause") or "Çevresel stres veya tür farklılığı kaynaklı olabilir."

    return {
        "id": "dynamic_unknown",
        "name": str(plant_name).title(),
        "latin_name": latin_name,
        "category": "AI Tespiti",
        "summary": f"{summary} | Olası durum: {diagnosis}",
        "light": "Dolaylı parlak ışık önerilir.",
        "light_level": 2,
        "water": "Toprak yüzeyi kurudukça kontrollü sulayın.",
        "water_level": 2,
        "soil": "Drenajı yüksek, hava alan karışım.",
        "supplements": f"Neden: {cause}. Öneri: {treatment}",
        "image": _to_data_uri(image_file),
        "is_dynamic": True,
    }

def render_hybrid_ai_panel(prefix, title_text):
    """Giriş ve doktor sayfalarında ortak hibrit AI paneli."""
    st.markdown(f"""
        <div style='background: #E8F5E9; padding: 18px; border-radius: 16px; border-left: 6px solid #FF8B71; margin-bottom: 10px;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <b style='color: #1B3022; font-size: 1.0rem;'>🧠 {title_text}</b>
                <span style='background: {"#4CAF50" if st.session_state.api_key else "#FF9800"}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem;'>
                    {"SİSTEM AKTİF" if st.session_state.api_key else "YAPILANDIRMA BEKLENİYOR"}
                </span>
            </div>
            <small style='color: #2D1B1B;'>
                Kütüphanemizi sonsuz bir bilgi kaynağına dönüştürmek için <b>Gemini 1.5 Flash</b> ve <b>Groq</b> hibrit gücünü kullanıyoruz.
            </small>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        new_gemini = st.text_input(
            "Gemini (Görsel Analiz):",
            value=st.session_state.api_key,
            type="password",
            key=f"{prefix}_gemini_key",
        )
    with c2:
        new_groq = st.text_input(
            "Groq (Akıllı Asistan):",
            value=st.session_state.groq_api_key,
            type="password",
            key=f"{prefix}_groq_key",
        )

    if st.button("Sistemleri Senkronize Et 🚀", key=f"{prefix}_sync_btn", use_container_width=True):
        st.session_state.api_key = new_gemini.strip()
        st.session_state.groq_api_key = new_groq.strip()
        configure_ai()
        st.success("✅ Hibrit AI altyapısı güncellendi.")
        st.rerun()

# Başlangıçta konfigüre et
configure_ai()

# Helper: Sayfa Değiştirme
# Session State Başlatma (Hataları önlemek için en üstte)
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "rehber"
if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_plant" not in st.session_state:
    st.session_state.selected_plant = None

def navigate_to(view, plant=None):
    st.session_state.view = view
    st.session_state.selected_plant = plant
    st.rerun()

# Ajan ve Dev Katmanı Başlatma
if "agent" not in st.session_state:
    st.session_state.agent = BotanicaAgent()
if "dev_layer" not in st.session_state:
    st.session_state.dev_layer = DevLayer()
if "terminal_history" not in st.session_state:
    st.session_state.terminal_history = []
if "proactive_dismissed" not in st.session_state:
    st.session_state.proactive_dismissed = False
if "show_ai_insight" not in st.session_state:
    st.session_state.show_ai_insight = False

def toggle_ai_insight():
    st.session_state.show_ai_insight = not st.session_state.show_ai_insight
    st.rerun()

# Ana Başlık - Özelleştirilmiş
st.markdown("<h1 style='text-align: center; color: #4A2C2A; margin-top: 0;'>🌸 Botanica AI: Evimizin Güzelleri</h1>", unsafe_allow_html=True)


# Bildirim Kontrolü (Gelişmiş Blink Sistemi)
has_plant_alert = False
my_plants = get_my_garden()
for p_row in my_plants:
    plant_data = next((p for p in PLANTS if p["id"] == p_row["plant_id"]), None)
    if plant_data:
        last_w = datetime.date.fromisoformat(p_row["last_watered"])
        days_since = (datetime.date.today() - last_w).days
        water_period = 7 if plant_data["water_level"] == 2 else 14 if plant_data["water_level"] == 1 else 3
        if days_since >= water_period or p_row["is_sick"]:
            has_plant_alert = True
            break

# AI Analiz Kontrolü
ai_findings = st.session_state.agent.diagnose_plant_anomalies()
has_ai_insight = len(ai_findings.get("data", [])) > 0

# Dinamik CSS Injection
blink_css = "<style>"
if has_plant_alert:
    # Yeşil Köşem (2. Buton) ve Bildirimler (4. Buton)
    if st.session_state.app_mode != "kosem":
        blink_css += 'div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { animation: blink 1.5s infinite ease-in-out !important; border: 1px solid #FF8B71 !important; }'
    if st.session_state.app_mode != "bildirim":
        blink_css += 'div[data-testid="stHorizontalBlock"] > div:nth-child(4) button { animation: blink 1.5s infinite ease-in-out !important; border: 1px solid #FF8B71 !important; }'

if has_ai_insight and st.session_state.app_mode != "agent":
    # Yönetim Merkezi (5. Buton)
    blink_css += 'div[data-testid="stHorizontalBlock"] > div:nth-child(5) button { animation: blink 1.5s infinite ease-in-out !important; border: 1px solid #FF8B71 !important; }'

blink_css += "</style>"
st.markdown(blink_css, unsafe_allow_html=True)

col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([2, 2, 2, 2, 2])

with col_nav1:
    if st.button("🌱 Bitki Rehberim", use_container_width=True):
        st.session_state.app_mode = "rehber"
        st.session_state.view = "home"
        st.rerun()

with col_nav2:
    if st.button("🪴 Yeşil Köşem", use_container_width=True):
        st.session_state.app_mode = "kosem"
        st.session_state.view = "home"
        st.rerun()

with col_nav3:
    if st.button("🩹 Bitki Doktorum", use_container_width=True):
        st.session_state.app_mode = "doktor"
        st.session_state.view = "home"
        st.rerun()

with col_nav4:
    if st.button("🔔 Bildirimler", use_container_width=True):
        st.session_state.app_mode = "bildirim"
        st.session_state.view = "home"
        st.rerun()

with col_nav5:
    if st.button("🧠 Yönetim Merkezi", use_container_width=True):
        st.session_state.app_mode = "agent"
        st.session_state.view = "home"
        st.rerun()

# Global divider kaldırıldı.
pass

app_mode = st.session_state.app_mode

# --- GERÇEK AI MODÜLÜ (Gemini 1.5 Flash) ---
def identify_plant_with_ai(image_file, user_complaint=""):
    if not configure_ai():
        return {"status": "no_api", "message": "Lütfen ayarlardan API anahtarınızı girin."}
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Resim verisini hazırla
        img_bytes = image_file.read()
        image_parts = [{"mime_type": image_file.type, "data": img_bytes}]
        
        prompt = f"""
        Sen dünyanın en iyi botanikçisisin. Bu bitkiyi görsel olarak en ince ayrıntısına kadar analiz et.
        1. Görsel Taksonomi: Yaprak kenarları (dişli, düz, dalgalı), damar yapısı, yüzey dokusu (tüylü, parlak, mat), gövde yapısı ve renk varyasyonlarını tanımla.
        2. Kimlik: Bu görsel verilere dayanarak bitkinin tam Türkçe adını ve bilimsel (Latince) adını belirle.
        3. Sağlık Analizi: Eğer bir anormallik (leke, renk değişimi, kuruma, böcek izi) varsa profesyonel bir teşhis koy.
        4. Kullanıcı Notu: '{user_complaint}'
        5. Reçete: Acil müdahale ve uzun vadeli bakım önerileri sun.
        
        Lütfen cevabını JSON formatında şu anahtarlarla ver: 
        'visual_description', 'plant_name', 'latin_name', 'synonyms', 'diagnosis', 'cause', 'treatment', 'confidence_score'
        """
        
        response = model.generate_content([prompt, image_parts[0]])
        parsed = parse_ai_json_response(response.text)
        return {"status": "success", "data": response.text, "parsed": parsed}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def identify_from_catalog_with_ai(image_file):
    """
    İlk analiz belirsiz kaldığında, AI'dan sadece katalogdaki bitkiler arasından seçim yapmasını ister.
    Böylece Orkide gibi var olan türlerin kaçırılma oranı düşer.
    """
    if not configure_ai() or not image_file:
        return None

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        image_file.seek(0)
        img_bytes = image_file.read()
        image_file.seek(0)

        catalog = "\n".join([f"- {p['name']} ({p['latin_name']})" for p in PLANTS])
        prompt = f"""
        Aşağıdaki görseldeki bitkiyi SADECE verilen katalogdan seç.
        Cevapta tahmin uydurma. Emin değilsen UNKNOWN yaz.
        SADECE tek satır JSON dön:
        {{"best_match":"...", "latin_name":"...", "confidence":0-100, "reason":"kisa"}}

        Katalog:
        {catalog}
        """

        response = model.generate_content([
            prompt,
            {"mime_type": image_file.type, "data": img_bytes}
        ])
        raw_response = response.text or ""
        parsed = parse_ai_json_response(raw_response)
        best_match = normalize_text(parsed.get("best_match") or parsed.get("plant_name") or "")
        latin_name = normalize_text(parsed.get("latin_name") or "")
        confidence = parsed.get("confidence", 0)
        try:
            confidence = float(confidence)
        except Exception:
            # "87%" gibi cevapları da yakala
            conf_match = re.search(r"(\d+(?:\.\d+)?)", str(confidence))
            confidence = float(conf_match.group(1)) if conf_match else 0.0

        # JSON parse başarısızsa ham metinden plant adı yakalamaya çalış
        if best_match in {"", "unknown", "none", "null"}:
            normalized_raw = normalize_text(raw_response)
            scored = []
            for plant in PLANTS:
                p_name = normalize_text(plant["name"])
                p_latin = normalize_text(plant["latin_name"])
                score = 0
                if p_name and p_name in normalized_raw:
                    score += 3
                if p_latin and p_latin in normalized_raw:
                    score += 4
                for kw in plant.get("keywords", []):
                    nkw = normalize_text(kw)
                    if len(nkw) > 2 and nkw in normalized_raw:
                        score += 1
                if score > 0:
                    scored.append((score, plant))
            scored.sort(key=lambda x: x[0], reverse=True)
            if scored and scored[0][0] >= 3:
                return scored[0][1]
            return None

        for plant in PLANTS:
            p_name = normalize_text(plant["name"])
            p_latin = normalize_text(plant["latin_name"])
            if best_match == p_name or (latin_name and latin_name == p_latin):
                return plant
            if best_match in p_name or p_name in best_match:
                # Düşük confidence olsa bile isim/latin net eşleşiyorsa kabul et
                if confidence >= 35 or latin_name == p_latin:
                    return plant
        return None
    except Exception:
        return None

def identify_catalog_id_with_ai(image_file):
    """
    En güçlü sınıflandırma katmanı:
    Modelden yalnızca katalogdaki bitki ID'sini döndürmesini ister.
    """
    if not configure_ai() or not image_file:
        return None

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        image_file.seek(0)
        img_bytes = image_file.read()
        image_file.seek(0)

        catalog_lines = []
        for p in PLANTS:
            catalog_lines.append(
                f"{p['id']} | {p['name']} | {p['latin_name']} | {', '.join(p.get('keywords', [])[:6])}"
            )
        catalog_text = "\n".join(catalog_lines)

        prompt = f"""
        Gorev: Gorseldeki bitkiyi sadece bu katalogdan sec.
        Cevap kurali: SADECE TEK SATIR ve sadece sayi.
        - Katalogdaki ID'lerden birini yaz.
        - Emin degilsen 0 yaz.

        Katalog:
        {catalog_text}
        """

        response = model.generate_content([
            prompt,
            {"mime_type": image_file.type, "data": img_bytes}
        ])
        raw = (response.text or "").strip()
        id_match = re.search(r"\b(\d+)\b", raw)
        if not id_match:
            return None

        predicted_id = int(id_match.group(1))
        if predicted_id == 0:
            return None

        for plant in PLANTS:
            try:
                if int(plant["id"]) == predicted_id:
                    return plant
            except Exception:
                continue
        return None
    except Exception:
        return None

def match_by_filename_hint(image_file):
    """API başarısızsa dosya adından güvenli ipucu eşleşmesi yapar."""
    if not image_file:
        return None
    filename = normalize_text(getattr(image_file, "name", ""))
    if not filename:
        return None

    scored = []
    for plant in PLANTS:
        score = 0
        p_name = normalize_text(plant["name"])
        p_latin = normalize_text(plant["latin_name"])
        if p_name and p_name in filename:
            score += 4
        if p_latin and p_latin in filename:
            score += 5
        for kw in plant.get("keywords", []):
            nkw = normalize_text(kw)
            if len(nkw) > 2 and nkw in filename:
                score += 2
        if score > 0:
            scored.append((score, plant))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored and scored[0][0] >= 3 else None

def identify_plant(image_file, selected_traits):
    """Gelişmiş bitki tanımlama ve kütüphane eşleştirme mantığı."""
    ai_result_text = ""
    ai_parsed_data = {}

    # 0. Aşama: Katalog içi hızlı sınıflandırma (ayırt etme başarısını artırır)
    if st.session_state.api_key and image_file:
        with st.spinner("🎯 Katalog içi kesin sınıflandırma yapılıyor..."):
            forced_id_match = identify_catalog_id_with_ai(image_file)
        if forced_id_match:
            return forced_id_match

        with st.spinner("🎯 Katalog içi ek sınıflandırma yapılıyor..."):
            forced_match = identify_from_catalog_with_ai(image_file)
        if forced_match:
            return forced_match
    
    # 1. Aşama: Yapay Zeka Analizi
    if not st.session_state.api_key:
        st.warning("⚠️ API Anahtarı eksik! Bitki tanıma performansı düşebilir.")
        
    if st.session_state.api_key and image_file:
        with st.spinner("🚀 Gemini 1.5 Flash ile derin analiz yapılıyor..."):
            image_file.seek(0)
            res = identify_plant_with_ai(image_file, " ".join(selected_traits))
            
        if res["status"] == "success":
            raw_text = res["data"].lower()
            ai_result_text = raw_text
            ai_parsed_data = res.get("parsed", {}) or parse_ai_json_response(raw_text)
            if ai_parsed_data.get("plant_name") and not ai_parsed_data.get("name"):
                ai_parsed_data["name"] = str(ai_parsed_data["plant_name"]).strip().lower()
            if ai_parsed_data.get("latin_name"):
                ai_parsed_data["latin_name"] = str(ai_parsed_data["latin_name"]).strip().lower()

    # 2. Aşama: Kütüphane ile Semantik ve Fuzzy Eşleştirme
    with st.spinner("🧠 Botani-Zeka kütüphane verileriyle karşılaştırılıyor..."):
        filename = image_file.name.lower() if image_file else ""
        scored_matches = []
        from difflib import SequenceMatcher

        for plant in PLANTS:
            score = 0
            p_name = normalize_text(plant["name"])
            p_latin = normalize_text(plant["latin_name"])
            
            # --- SEVİYE 0: KELİME BAZLI PARÇALAMA (Ultra Hassas) ---
            p_words = p_name.split()
            for word in p_words:
                if len(word) > 2 and word in ai_result_text:
                    score += 100 # "Orkide" kelimesi "Beyaz Orkide" içinde geçiyorsa büyük puan
            
            # --- SEVİYE 1: TAM VE BİLİMSEL EŞLEŞME ---
            if p_latin in ai_result_text: score += 200
            if p_name in ai_result_text: score += 150
            
            # --- SEVİYE 2: BULANIK (FUZZY) BENZERLİK ---
            if "name" in ai_parsed_data:
                similarity = SequenceMatcher(None, p_name, normalize_text(ai_parsed_data["name"])).ratio()
                if similarity > 0.6: # Eşik 0.8'den 0.6'ya çekildi (Beyaz Orkide vs Orkide için)
                    score += (similarity * 200)
            
            # --- SEVİYE 3: ANAHTAR KELİMELER ---
            for kw in plant.get("keywords", []):
                if normalize_text(kw) in normalize_text(ai_result_text):
                    score += 80
            
            # --- SEVİYE 4: FALLBACK ---
            if filename and plant["image"].lower() in filename: score += 120
            
            if score > 0:
                scored_matches.append((score, plant))
        
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        
        if scored_matches and scored_matches[0][0] >= 30:
            return scored_matches[0][1]
        # Son güvenlik katmanı: katalogdan zorunlu AI seçimi
        catalog_match = identify_from_catalog_with_ai(image_file)
        if catalog_match:
            return catalog_match
        if ai_parsed_data:
            return build_dynamic_plant_profile(ai_parsed_data, image_file)
        filename_hint = match_by_filename_hint(image_file)
        if filename_hint:
            return filename_hint
        return None

# --- MODÜL: BİTKİ DOKTORUM ---
if app_mode == "doktor":
    st.markdown("# 🩹 Bitki Doktoru: AI Teşhis Merkezi")
    st.markdown("Hibrit AI teknolojisi ile bitkinizdeki sorunları saniyeler içinde analiz edin.")
    
    # Hibrit Yapay Zeka Kontrol Paneli (Giriş ile aynı görünüm/akış)
    with st.expander("⚙️ Hibrit AI Kontrol Paneli", expanded=not st.session_state.api_key):
        render_hybrid_ai_panel("doctor", "Hibrit Yapay Zeka Gücü")

    col_up, col_res = st.columns([1, 1.2])
    with col_up:
        st.markdown("""<div style='background: white; padding: 20px; border-radius: 20px; border: 1px solid #eee;'>
            <h4>📸 Fotoğraf Yükle</h4>
            <p style='color: #666; font-size: 0.85rem;'>Sorunlu bölgenin net bir fotoğrafını çekin.</p>
        </div>""", unsafe_allow_html=True)
        doc_file = st.file_uploader("Doktor fotoğraf yükleme", type=["jpg", "png", "jpeg"], key="doc_up", label_visibility="collapsed")
        
        st.markdown("#### 📝 Belirtileri Seçin")
        symptoms = st.multiselect(
            "Gözlemlediğiniz değişimler:",
            ["Yaprak sararması", "Kahverengi lekeler", "Beyaz pamukçuklar", "Yapışkan sıvı", "İnce ağlar", "Aniden solma", "Gövdede yumuşama", "Toprakta böcek", "Gelişim durması", "Yaprak dökülmesi"],
            placeholder="En az bir belirti seçin..."
        )
        complaint = st.text_area("Eklemek istediğiniz notlar", placeholder="Örn: Yapraklar 3 gündür sarı renkte...")
        
    if doc_file or symptoms or complaint:
        with col_res:
            st.markdown("### 🧬 Teşhis Raporu")
            
            combined_input = " ".join(symptoms) + " " + complaint.lower()
            
            if not st.session_state.api_key:
                st.warning("⚠️ Gerçek zamanlı AI teşhisi için lütfen API anahtarınızı girin. Şu an standart veritabanı üzerinden analiz yapılıyor.")
            
            with st.spinner("Yapay Zeka derinlemesine inceliyor..."):
                if st.session_state.api_key and doc_file:
                    res = identify_plant_with_ai(doc_file, combined_input)
                    if res["status"] == "success":
                        st.markdown(f"""
                            <div style='background: #f0fdf4; padding: 25px; border-radius: 20px; border-left: 10px solid #22c55e;'>
                                <h4 style='margin:0; color:#166534;'>🔬 AI Teşhis Sonucu</h4>
                                <hr style='margin: 10px 0;'>
                                {res['data']}
                            </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                    else:
                        st.error(f"Hata: {res['message']}")
                else:
                    # Gelişmiş kütüphane bazlı teşhis (Multi-factor matching)
                    matches = []
                    for d in DISEASES:
                        score = 0
                        # Anahtar kelime eşleşmesi
                        score += sum(2 for k in d["keywords"] if k in combined_input)
                        # Belirti eşleşmesi (Daha yüksek puan)
                        score += sum(5 for s in d["symptoms"] if any(sym.lower() in s.lower() for sym in symptoms))
                        
                        if score > 0:
                            matches.append((score, d))
                    
                    matches.sort(key=lambda x: x[0], reverse=True)
                    found_disease = matches[0][1] if matches else None
                    
                    if found_disease:
                        st.markdown(f"""
                            <div style='background: #fff1f2; padding: 25px; border-radius: 20px; border-left: 10px solid #e11d48;'>
                                <h4 style='margin:0; color:#9f1239;'>🚨 {found_disease['name']}</h4>
                                <p style='margin: 10px 0;'><b>Neden:</b> {found_disease['cause']}</p>
                                <p style='margin: 0;'><b>Tedavi:</b> {found_disease['treatment']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("🔍 Kütüphanemizde tam bir eşleşme bulunamadı. Lütfen notlarınızı detaylandırın veya AI anahtarınızı kullanarak görsel taramayı aktif edin.")

# --- MODÜL: BİLDİRİMLER ---
elif app_mode == "bildirim":
    st.markdown("# 🔔 Bildirim Merkezi")
    my_plants = get_my_garden()
    if not my_plants:
        st.info("Yeşil köşenizde henüz bitki yok. Kütüphaneden bitki ekleyerek bildirimleri aktif edebilirsiniz.")
    else:
        cols = st.columns(2)
        for idx, p_row in enumerate(my_plants):
            plant_data = next((p for p in PLANTS if p["id"] == p_row["plant_id"]), None)
            if plant_data:
                with cols[idx % 2]:
                    last_w = datetime.date.fromisoformat(p_row["last_watered"])
                    days_since = (datetime.date.today() - last_w).days
                    water_period = 7 if plant_data["water_level"] == 2 else 14 if plant_data["water_level"] == 1 else 3
                    
                    if days_since >= water_period:
                        st.warning(f"💧 **{p_row['nickname']}** ({plant_data['name']}) çok susamış! {days_since} gündür su bekliyor.")
                    
                    if p_row["is_sick"]:
                        st.error(f"🩹 **{p_row['nickname']}** şu an tedavi sürecinde. İlaçlarını aksatmayın.")
                    
                    if days_since < water_period and not p_row["is_sick"]:
                        st.success(f"✨ **{p_row['nickname']}** şu an çok mutlu ve sağlıklı!")

# --- MODÜL: BİTKİ REHBERİM ---
elif app_mode == "rehber":
    if st.session_state.view == "home":
        st.markdown("""
            <div style='text-align: center; margin-top: 20px; margin-bottom: 20px;'>
                <h2 style='color: #4A2C2A; margin-bottom: 0;'>🌿 Evimizin Güzelliğini AI ile Yaşatın</h2>
                <p style='color: #666;'>Bitkilerinizi Tanımlayın, Profesyonel Bakım Alın ve Sağlıklarını Takip Edin</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Daha kompakt üst panel (Tanı ve Günün Bitkisi yan yana)
        col_ai, col_daily = st.columns([1, 1])
        
        with col_ai:
            with st.expander("✨ Fotoğraf ile Tanı & Teşhis", expanded=False):
                uploaded_file = st.file_uploader("Fotoğraf Yükle", type=["jpg", "png"], label_visibility="collapsed")
                
                if st.button("Bitkiyi Tanı", use_container_width=True, type="primary"):
                    if uploaded_file:
                        res = identify_plant(uploaded_file, [])
                        if res:
                            navigate_to("detail", res)
                        else:
                            st.error("🔍 Bitki tanımlanamadı. Lütfen kütüphanemizdeki bitkilerden biri olduğundan emin olun.")
                    else:
                        st.warning("📸 Lütfen önce bir fotoğraf yükleyin.")
                
                # Hibrit Yapay Zeka Kontrol Paneli
                st.markdown("---")
                render_hybrid_ai_panel("home", "Hibrit Yapay Zeka Gücü")
        
        with col_daily:
            today_seed = int(datetime.date.today().strftime("%Y%m%d"))
            random.seed(today_seed)
            dp = random.choice(PLANTS)
            random.seed()
            st.markdown(f"""<div style='background: white; padding: 15px; border-radius: 15px; border-left: 5px solid var(--primary-color); box-shadow: 0 4px 15px rgba(0,0,0,0.05);'>
                <p style='margin:0; font-size: 0.9rem; color: var(--primary-color); font-weight: bold;'>🌿 Günün Bitkisi</p>
                <p style='margin:0; font-weight: bold;'>{dp['name']}</p>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Hadi Beni İncele 🔍", key="daily_btn_mini", use_container_width=True):
                navigate_to("detail", dp)

        st.divider()

        col_search, col_filter = st.columns([2, 1])
        with col_search: search_query = st.text_input("Bitki arama", placeholder="Bitki ara...", label_visibility="collapsed")
        with col_filter:
            categories = ["Tümü"] + sorted(list(set(p["category"] for p in PLANTS)))
            selected_category = st.selectbox("Kategori filtresi", categories, label_visibility="collapsed")

        filtered_plants = [p for p in PLANTS if (search_query.lower() in p["name"].lower()) and (selected_category == "Tümü" or p["category"] == selected_category)]
        filtered_plants.sort(key=lambda x: x["name"])
        
        if not filtered_plants:
            st.info(f"🔍 **'{search_query}'** isminde bir bitki henüz kütüphanemizde yok. Belki yazımını kontrol edebilir veya diğer güzellere göz atabilirsiniz!")
            st.image("https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&q=80&w=400", caption="Buralarda bir yerde yeni bir bitki bekliyor olabilir...")
        else:
            cols = st.columns(3) # 4 yerine 3 kolon daha ferah ve kullanıcı dostu durur
            for idx, plant in enumerate(filtered_plants):
                with cols[idx % 3]:
                    img_src = get_image_base64(plant['image'])
                    st.markdown(f"""
                        <div class="plant-card">
                            <div class="image-container">
                                <img src="{img_src}" class="plant-image">
                            </div>
                            <div style="padding: 10px 0;">
                                <span class="plant-name">{plant['name']}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"İncele", key=f"btn_{plant['id']}", use_container_width=True):
                        navigate_to("detail", plant)

    elif st.session_state.view == "detail":
        plant = st.session_state.selected_plant
        if not plant:
            st.warning("Bitki detayı yüklenemedi, ana sayfaya dönülüyor.")
            navigate_to("home")
        if st.button("← Geri", key="back_btn"): navigate_to("home")
        
        # 3 Kolonlu Profesyonel Yerleşim
        col_img, col_info, col_action = st.columns([1.2, 1.5, 1])
        with col_img:
            # Detay sayfasında profesyonel büyüteç (magnifier) efekti - KESİN ÇÖZÜM
            img_base64 = optimize_data_uri_for_zoom(get_image_base64(plant["image"]))
            
            magnifier_html = f"""
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ background: transparent; overflow: hidden; }}
                .magnify-container {{
                    position: relative;
                    width: 100%;
                    height: 550px;
                    background: transparent;
                    border-radius: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    overflow: visible; /* Lensin dışarı taşmasına izin ver */
                    cursor: none;
                }}
                .magnify-img {{
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain; /* Kesilmeyi önler */
                    border-radius: 20px;
                    box-shadow: 0 5px 25px rgba(0,0,0,0.1);
                }}
                .magnifier-lens {{
                    position: absolute;
                    width: 180px;
                    height: 180px;
                    border: 4px solid #FF8B71;
                    border-radius: 15px;
                    background-repeat: no-repeat;
                    visibility: hidden;
                    pointer-events: none;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.5);
                    z-index: 999;
                    background-color: #f0f0f0;
                }}
            </style>
            <div class="magnify-container" id="container">
                <img src="{img_base64}" class="magnify-img" id="main-img" onerror="this.src='https://via.placeholder.com/400'">
                <div class="magnifier-lens" id="lens"></div>
            </div>
            <script>
                const container = document.getElementById('container');
                const img = document.getElementById('main-img');
                const lens = document.getElementById('lens');
                const zoom = 2.5;

                function moveLens(e) {{
                    lens.style.visibility = 'visible';
                    const rect = container.getBoundingClientRect();
                    const imgRect = img.getBoundingClientRect();

                    let x = e.clientX - rect.left;
                    let y = e.clientY - rect.top;

                    // Lens Pozisyonu
                    let lensX = x - lens.offsetWidth / 2;
                    let lensY = y - lens.offsetHeight / 2;

                    // Konteynır sınırları
                    if (lensX < 0) lensX = 0;
                    if (lensY < 0) lensY = 0;
                    if (lensX > rect.width - lens.offsetWidth) lensX = rect.width - lens.offsetWidth;
                    if (lensY > rect.height - lens.offsetHeight) lensY = rect.height - lens.offsetHeight;

                    lens.style.left = lensX + 'px';
                    lens.style.top = lensY + 'px';

                    // ZOOM İŞLEMİ - Resmin kendi src'sini kullan
                    lens.style.backgroundImage = "url('" + img.src + "')";
                    
                    // Hesaplama: Resmin görünür boyutlarına göre zoom ayarı
                    lens.style.backgroundSize = (imgRect.width * zoom) + "px " + (imgRect.height * zoom) + "px";
                    
                    // Resmin merkezini lensin altına getir (ofsetleri hesaba katarak)
                    let bgX = (x - imgRect.left + rect.left) * zoom - lens.offsetWidth / 2;
                    let bgY = (y - imgRect.top + rect.top) * zoom - lens.offsetHeight / 2;

                    lens.style.backgroundPosition = "-" + bgX + "px -" + bgY + "px";
                }}

                container.addEventListener('mousemove', moveLens);
                container.addEventListener('touchstart', (e) => {{
                    e.preventDefault();
                    moveLens(e.touches[0]);
                }}, {{passive: false}});
                
                container.addEventListener('mouseleave', () => {{
                    lens.style.visibility = 'hidden';
                }});
            </script>
            """
            # Zoom efekti korunur; render başarısızsa güvenli fallback devreye girer.
            try:
                import streamlit.components.v1 as components
                components.html(magnifier_html, height=560)
            except Exception:
                st.image(img_base64, use_container_width=True)
            st.info(plant["summary"])

        with col_info:
            st.markdown(f"<h1>{plant['name']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-style: italic; color: #666;'>{plant['latin_name']}</p>", unsafe_allow_html=True)
            
            st.markdown("#### 🌡️ Bakım Reçetesi")
            st.write(f"☀️ Işık: {plant['light']}")
            st.progress(plant["light_level"] / 3.0)
            st.write(f"💧 Su: {plant['water']}")
            st.progress(plant["water_level"] / 3.0)
            
            st.markdown(f"**🏠 Konumlandırma:** {plant.get('placement', 'Aydınlık bir köşe.')}")
            st.markdown(f"**🌊 Sulama Detayı:** {plant.get('watering_detail', 'Toprak kurudukça.')}")
            st.markdown(f"**🌱 Toprak:** {plant['soil']}")
            st.markdown(f"**🧪 Gübreleme:** {plant['supplements']}")

        with col_action:
            # Hayalet kutu tamamen kaldırıldı, başlık ve ön yazı birleştirildi
            st.markdown("""
                <div class='action-card'>
                    <h3>🏡 Yeşil Köşeme Ekle</h3>
                    <p class='action-instruction'>İsterseniz bitkinize özel bir isim takabilirsiniz:</p>
                </div>
            """, unsafe_allow_html=True)
            nickname = st.text_input("Bitkinize bir isim verin:", value=plant["name"], key="nick_input", label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            if plant.get("is_dynamic"):
                st.info("Bu bitki AI ile yeni tespit edildiği için doğrudan kütüphane kaydı yok. Önce kütüphaneye eklenmesi gerekir.")
            elif st.button("Yeşil Köşeme Ekle ✨", type="primary", use_container_width=True, key="add_btn_final"):
                add_to_garden(plant["id"], nickname)
                st.success("✅ Eklendi!")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("🔍 Bu bitkiyi kendi bahçenize ekleyerek sulama hatırlatıcılarını aktif edebilirsiniz.")

# --- MODÜL: YEŞİL KÖŞEM ---
elif app_mode == "kosem":
    st.markdown("# 🪴 Yeşil Köşem")
    my_garden = get_my_garden()
    
    if not my_garden:
        st.info("Yeşil köşeniz henüz boş. Kütüphaneden bitki ekleyerek burayı canlandırabilirsiniz!")
    else:
        for p_row in my_garden:
            plant_data = next((p for p in PLANTS if p["id"] == p_row["plant_id"]), None)
            if plant_data:
                with st.expander(f"🌿 {p_row['nickname']} ({plant_data['name']})", expanded=True):
                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c1:
                        img_src = get_image_base64(plant_data["image"])
                        st.image(img_src, use_container_width=True)
                    
                    with c2:
                        st.markdown(f"**Son Sulama:** {p_row['last_watered']}")
                        st.markdown(f"**Son Gübreleme:** {p_row['last_fertilized']}")
                        status = "🔴 Hasta / Tedavide" if p_row["is_sick"] else "🟢 Sağlıklı"
                        st.markdown(f"**Durum:** {status}")
                        
                        # Butonlar - Hizalı ve İşlevsel
                        bc1, bc2, bc3 = st.columns(3)
                        if bc1.button("💧 Suladım", key=f"w_{p_row['id']}", use_container_width=True):
                            update_care(p_row['id'], "water")
                            st.rerun()
                        if bc2.button("🧪 Gübreledim", key=f"f_{p_row['id']}", use_container_width=True):
                            update_care(p_row['id'], "fertilize")
                            st.rerun()
                        if bc3.button("🩺 Doktoruma Sor", key=f"d_{p_row['id']}", use_container_width=True):
                            st.session_state.app_mode = "doktor"
                            st.rerun()
                    
                    with c3:
                        st.markdown("### 📝 Bitki Günlüğü")
                        note = st.text_input("Not ekle...", key=f"note_{p_row['id']}")
                        if st.button("Kaydet", key=f"save_{p_row['id']}"):
                            add_log(p_row['id'], note)
                            st.success("Not kaydedildi!")
                        
                        logs = get_logs(p_row['id'])
                        for l in logs[:3]:
                            st.caption(f"📅 {l['log_date']}: {l['note'] if l['note'] else l['log_type']}")
                        
                        # AI Optimization Check
                        knowledge = get_learned_knowledge(p_row['plant_id'])
                        if knowledge:
                            st.markdown("---")
                            st.markdown("🤖 **AI Bakım Optimizasyonu:**")
                            for k in knowledge:
                                st.caption(f"✨ {k['content']}")

# --- MODÜL: AKILLI YÖNETİM MERKEZİ ---
elif app_mode == "agent":
    st.markdown(f"# 🧠 {st.session_state.agent.name}")
    st.markdown("Bahçenizin iyiliği için her şeyi düşünen, size özel akıllı yönetim asistanı.")
    
    # Bilgilendirme Kartları - Daha Yumuşak Renkler ve İkonlar
    st.markdown("### ✨ Ben Sizin İçin Neler Yapabilirim?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='management-card'><div class='management-icon'>📋</div>
            <b>Durum Analizi</b><br><small>Tüm bahçenizi tarar ve size özel bir özet hazırlarım.</small></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class='management-card'><div class='management-icon'>⛅</div>
            <b>Bakım Planlama</b><br><small>Bitkilerinizin su ve ışık takvimini sizin yerinize optimize ederim.</small></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class='management-card'><div class='management-icon'>🔍</div>
            <b>Hızlı Teşhis</b><br><small>Bir sorun sezdiğimde sizi hemen bilgilendirir ve çözüm sunarım.</small></div>""", unsafe_allow_html=True)

    tab_chat, tab_train = st.tabs(["💬 Asistan ile Konuş", "🎨 Yapay Zeka Eğitimi"])
    
    with tab_chat:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); padding: 30px; border-radius: 20px; margin-bottom: 20px; border: 1px solid #e0e0e0;">
                <h4 style="margin:0; color:#4A2C2A;">🌿 Botanica Asistanı</h4>
                <p style="color:#666; font-size:0.9rem;">Merhaba! Bugün bahçenizle ilgili neyi merak ediyorsunuz? Aşağıdaki butonlara basabilir veya bana yazabilirsiniz.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Hızlı İşlem Butonları
        st.markdown("**Hızlı İşlemler:**")
        qc1, qc2, qc3 = st.columns(3)
        with qc1:
            if st.button("📊 Genel Rapor Çıkar", use_container_width=True):
                res = st.session_state.agent.process_command("rapor")
                st.session_state.terminal_history.append({"user": "Genel Rapor Çıkar", "bot": res["message"]})
                st.rerun()
        with qc2:
            if st.button("💧 Sulamayı Optimize Et", use_container_width=True):
                res = st.session_state.agent.process_command("sula")
                st.session_state.terminal_history.append({"user": "Sulamayı Optimize Et", "bot": res["message"]})
                st.rerun()
        with qc3:
            if st.button("🚑 Sağlık Taraması Yap", use_container_width=True):
                res = st.session_state.agent.process_command("anomali")
                st.session_state.terminal_history.append({"user": "Sağlık Taraması Yap", "bot": res["message"]})
                st.rerun()

        st.divider()

        # Sohbet Geçmişi - Kod gibi durmayan temiz yapı
        for entry in st.session_state.terminal_history[-3:]:
            with st.chat_message("user", avatar="👤"):
                st.write(entry['user'])
            with st.chat_message("assistant", avatar="🧠"):
                st.write(entry['bot'])

        cmd = st.text_input("Asistanınıza mesaj yazın...", placeholder="Örn: Bitkilerimin durumu nasıl? / Sulama planını revize et...", key="terminal_input", label_visibility="collapsed")
        if st.button("Mesaj Gönder ✨", use_container_width=True, type="primary"):
            if cmd:
                with st.spinner("Asistanınız düşünüyor..."):
                    res = st.session_state.agent.process_command(cmd)
                    st.session_state.terminal_history.append({"user": cmd, "bot": res["message"]})
                    st.rerun()

# Footer
st.markdown("<br><hr><center><small>Botanica AI: Evimizin Güzelleri | Zeynep Ebrar PALA tarafından geliştirilmiştir © 2026</small></center>", unsafe_allow_html=True)
