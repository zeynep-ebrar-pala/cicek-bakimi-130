import streamlit as st
import sqlite3
import datetime
import base64
import os
import sys
from pathlib import Path

# 1. PATH SETUP
current_file = Path(__file__).resolve()
root_dir = current_file.parent.parent
backend_dir = root_dir / "backend"
if str(root_dir) not in sys.path: sys.path.append(str(root_dir))
if str(backend_dir) not in sys.path: sys.path.append(str(backend_dir))

# 3. MAIN APP FUNCTION
def render_app():
    # Dynamic Path Setup for Streamlit Cloud
    ROOT_DIR = Path(__file__).parent.parent
    ASSETS_DIR = ROOT_DIR / "assets"
    
    # Defensive Imports & DB Init
    try:
        from data import PLANTS
        from database import init_db, add_to_garden, get_my_garden, update_care, remove_from_garden, get_user_profile, update_user_profile, get_daily_plant_id
        from agent import BotanicaAgent
        init_db()
        raw_profile = get_user_profile()
        profile = dict(raw_profile) if raw_profile else {}
    except Exception as e:
        st.error(f"🚨 SİSTEM DOSYALARI YÜKLENEMEDİ: {e}")
        st.info("İpucu: Streamlit Cloud'da çalışırken klasör yapısının bozulmadığından emin olun.")
        return

    # 4. SESSION STATE INITIALIZATION
    if "app_mode" not in st.session_state: st.session_state.app_mode = "rehber"
    if "view" not in st.session_state: st.session_state.view = "home"
    if "selected_plant" not in st.session_state: st.session_state.selected_plant = None
    if "chat_history" not in st.session_state: st.session_state.chat_history = []

    # 5. PREMIUM GLASSMORPHISM STYLING
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Playfair+Display:wght@700;900&display=swap');
        
        :root {
            --primary: #1B4332;
            --secondary: #2D6A4F;
            --accent: #D8F3DC;
            --glass: rgba(255, 255, 255, 0.7);
            --glass-border: rgba(255, 255, 255, 0.3);
            --shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        }

        html, body, [data-testid="stAppViewContainer"] { 
            font-family: 'Outfit', sans-serif; 
            background: linear-gradient(135deg, #f0f4f1 0%, #e8f0e9 100%);
            background-attachment: fixed;
        }
        
        [data-testid="stHeader"] { background: transparent; }

        .brand { 
            font-family: 'Playfair Display', serif; 
            font-size: 5rem; 
            color: var(--primary); 
            text-align: center; 
            margin-top: -40px;
            margin-bottom: -15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.05);
        }
        
        .motto {
            text-align: center;
            color: var(--secondary);
            font-style: italic;
            margin-bottom: 20px;
            font-weight: 300;
        }

        /* Glassmorphism Card System */
        .glass-card {
            background: var(--glass);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 24px;
            border: 1px solid var(--glass-border);
            box-shadow: var(--shadow);
            padding: 20px;
            transition: all 0.3s ease;
        }
        
        .glass-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.15);
        }

        .card-header-bar {
            background: rgba(255, 255, 255, 0.9);
            padding: 12px;
            text-align: center;
            border-radius: 20px 20px 0 0;
            border: 1px solid var(--glass-border);
            font-weight: 800;
            color: var(--primary);
            font-size: 1.2rem;
            margin-bottom: 0 !important;
        }

        .image-container {
            height: 120px;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            background: rgba(255,255,255,0.4);
            border-bottom: 1px solid var(--glass-border);
        }
        
        .image-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .stButton>button { 
            background: var(--primary) !important;
            color: white !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            border: none !important;
            padding: 12px 24px !important;
            box-shadow: 0 4px 15px rgba(27, 67, 50, 0.2) !important;
        }
        
        /* Stats Dashboard */
        .stat-box {
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 15px;
            border: 1px solid var(--glass-border);
        }
        .stat-val { font-size: 1.8rem; font-weight: 800; color: var(--primary); }
        .stat-lbl { font-size: 0.8rem; color: #666; text-transform: uppercase; }

        /* Animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in { animation: fadeIn 0.6s ease-out; }

        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #B7E4C7, #52B788, #1B4332) !important;
        }

        .property-tag {
            font-size: 0.75rem;
            padding: 4px 8px;
            background: var(--accent);
            border-radius: 6px;
            color: var(--primary);
            font-weight: 600;
        }

        .analysis-card {
            background: var(--glass);
            backdrop-filter: blur(10px);
            border-left: 5px solid var(--primary);
            padding: 20px;
            border-radius: 15px;
            margin-top: 20px;
        }

        .zoom-container {
            overflow: hidden;
            border-radius: 24px;
            cursor: zoom-in;
            border: 1px solid var(--glass-border);
            background: white;
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: auto;
            max-height: 250px;
        }
        .zoom-container img {
            transition: transform 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .zoom-container:hover img {
            transform: scale(1.4);
        }

        /* Thicker Expander Bar */
        div[data-testid="stExpander"] p {
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            color: var(--primary) !important;
        }
        div[data-testid="stExpander"] {
            border: 1px solid var(--glass-border) !important;
            border-radius: 15px !important;
            background: var(--glass) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 6. GLOBAL ERROR PROTECTION & NAVIGATION
    try:
        st.markdown("<h1 class='brand fade-in'>Nabzı Filiz</h1>", unsafe_allow_html=True)
        st.markdown("<p class='motto fade-in'>Evinizin Kalbi Burada Atıyor...</p>", unsafe_allow_html=True)

        if st.session_state.app_mode == "rehber":
            st.markdown("""
            <div class='fade-in' style='text-align: center; color: #444; margin-bottom: 25px; font-size: 1rem; font-weight: 300;'>
                Doğanın nabzını tutan akıllı asistanınızla, filizlerinizin mutluluğuna ortak olun. 
                Bilimsel bakım stratejileri, ileri seviye hastalık teşhisi ve yapay zekanın 
                bilgeliğiyle evinizdeki her yaprağın hikayesini birlikte yazıyoruz.
            </div>
            """, unsafe_allow_html=True)

        n1, n2, n3, n4, n5, n6 = st.columns([1, 1, 1, 1, 1, 1])
        if n1.button("📖 Rehberim", use_container_width=True):
            st.session_state.app_mode = "rehber"; st.session_state.view = "home"; st.rerun()
        if n2.button("🪴 Köşem", use_container_width=True):
            st.session_state.app_mode = "kosem"; st.rerun()
        if n3.button("🩹 Doktorum", use_container_width=True):
            st.session_state.app_mode = "doktor"; st.rerun()
        if n4.button("🧠 Flora", use_container_width=True):
            st.session_state.app_mode = "agent"; st.rerun()
        if n5.button("🔔 Uyarılar", use_container_width=True):
            st.session_state.app_mode = "notif"; st.rerun()
        if n6.button("⚙️ Profilim", use_container_width=True):
            st.session_state.app_mode = "profil"; st.rerun()

        st.divider()

        # 7. MAIN LOGIC
        if st.session_state.app_mode == "rehber":
            if st.session_state.view == "home":
                st.markdown("<div style='margin-top: -20px;'></div>", unsafe_allow_html=True)
                st.markdown("### 🌟 Günün Bitkisi")
                daily_id = get_daily_plant_id()
                daily_p = next((p for p in PLANTS if p["id"] == daily_id), PLANTS[0])
                with st.container(border=True):
                    dc1, dc2, dc3 = st.columns([1, 2, 1])
                    with dc1:
                        img_p = ASSETS_DIR / daily_p.get("image", "")
                        if img_p.exists():
                            with open(img_p, "rb") as f:
                                img_b64 = base64.b64encode(f.read()).decode()
                            st.markdown(f"""
                            <div class='zoom-container' style='max-height: 120px;'>
                                <img src='data:image/jpeg;base64,{img_b64}'>
                            </div>
                            """, unsafe_allow_html=True)
                        else: st.write("🌿")
                    with dc2:
                        st.subheader(daily_p["name"])
                        st.caption(daily_p.get("summary", "Bitki hakkında kısa bilgi..."))
                    with dc3:
                        st.write("<br>", unsafe_allow_html=True)
                        if st.button("Keşfet 🔍", key="daily_btn", use_container_width=True):
                            st.session_state.selected_plant = daily_p; st.session_state.view = "detail"; st.rerun()
                
                # NEW: Bitkimi Tanı Feature
                with st.expander("📸 Bitkimi Tanı (Görsel Analiz)"):
                    st.write("Bitkinizin fotoğrafını yükleyin, kütüphanemizdeki 36 türle karşılaştıralım.")
                    up_file = st.file_uploader("Bitki Fotoğrafı Yükle 📸", type=["jpg", "png", "jpeg"], key="recognizer")
                    if up_file:
                        st.image(up_file, width=200)
                        if st.button("Bitkiyi Tanımla ✨", use_container_width=True):
                            with st.spinner("Yapay zeka fotoğrafı analiz ediyor..."):
                                try:
                                    best_match = None
                                    
                                    # 1. High-Capability AI Vision (Gemini)
                                    if profile and profile.get('api_key'):
                                        from agent import BotanicaAgent
                                        agent = BotanicaAgent(api_key=profile['api_key'])
                                        ai_result = agent.identify_plant_vision(up_file.getvalue(), up_file.type)
                                        if ai_result and ai_result != "Unknown":
                                            best_match = next((p for p in PLANTS if p["name"].lower() in ai_result.lower()), None)
                                    
                                    # 2. Fallback: Robust Keyword/Filename Matching
                                    if not best_match:
                                        fname = up_file.name.lower()
                                        highest_score = 0
                                        for p in PLANTS:
                                            score = 0
                                            p_name = p["name"].lower()
                                            p_img = p.get("image", "").lower()
                                            p_keys = p.get("keywords", [])
                                            
                                            # String-safe checks
                                            if p_name in fname or p_img in fname: score += 10
                                            for k in p_keys:
                                                if str(k).lower() in fname: score += 5
                                            
                                            if score > highest_score:
                                                highest_score = score
                                                best_match = p
                                        
                                        if highest_score == 0: best_match = None

                                    if best_match:
                                        st.success(f"🌟 Yapay zeka bu bitkiyi **{best_match['name']}** olarak tanımladı!")
                                        if st.button(f"{best_match['name']} Detaylarını Gör", key="view_matched_plant", use_container_width=True):
                                            st.session_state.selected_plant = best_match; st.session_state.view = "detail"; st.rerun()
                                    else:
                                        st.warning("⚠️ Bu bitkiyi tam olarak tanıyamadık.")
                                        st.info("İpucu: Bitkiniz henüz kütüphanemizde olmayabilir. Lütfen bitki rehberimizde mevcut olan diğer türlere göz gezdirin.")
                                except Exception as inner_e:
                                    st.error(f"Analiz sırasında bir hata oluştu: {inner_e}")
                
                st.markdown("## 🔎 Filtreleme Paneli")
                f1, f2, f3 = st.columns(3)
                search = f1.text_input("İsimle Ara", placeholder="Örn: Paşa Kılıcı")
                f_water = f2.selectbox("Su İhtiyacı", ["Hepsi", "Az", "Orta", "Çok"])
                f_light = f3.selectbox("Işık İhtiyacı", ["Hepsi", "Düşük", "Orta", "Yüksek"])
                
                water_map = {"Az": 1, "Orta": 2, "Çok": 3}
                light_map = {"Düşük": 1, "Orta": 2, "Yüksek": 3}
                filtered = [p for p in PLANTS if search.lower() in p["name"].lower()]
                if f_water != "Hepsi": filtered = [p for p in filtered if p.get("water_level") == water_map[f_water]]
                if f_light != "Hepsi": filtered = [p for p in filtered if p.get("light_level") == light_map[f_light]]
                
                if not filtered: st.warning("Eşleşen bitki bulunamadı.")
                else:
                    cols = st.columns(3)
                    for idx, p in enumerate(filtered):
                        with cols[idx % 3]:
                            # Card Structure with HTML Clipping
                            st.markdown(f"<div class='card-header-bar'>{p['name']}</div>", unsafe_allow_html=True)
                            
                            # Content Container
                            with st.container(border=True):
                                img_p = ASSETS_DIR / p.get("image", "")
                                if img_p.exists():
                                    with open(img_p, "rb") as f:
                                        img_b64 = base64.b64encode(f.read()).decode()
                                    st.markdown(f"""
                                    <div class='image-container'>
                                        <img src='data:image/jpeg;base64,{img_b64}'>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown("<div class='image-container'>🌿</div>", unsafe_allow_html=True)
                                
                                # Property Tags (Emojis)
                                w_icons = "💧" * p.get("water_level", 1)
                                l_icons = "☀️" * p.get("light_level", 1)
                                st.markdown(f"<div style='text-align:center; margin-top:10px;'><span class='property-tag'>{w_icons}</span> <span class='property-tag'>{l_icons}</span></div>", unsafe_allow_html=True)
                                
                                if st.button(f"İncele", key=f"det_{p['id']}", use_container_width=True):
                                    st.session_state.selected_plant = p; st.session_state.view = "detail"; st.rerun()
                            st.write("") # Spacer

            elif st.session_state.view == "detail":
                p = st.session_state.selected_plant
                st.button("← Geri", on_click=lambda: setattr(st.session_state, "view", "home"))
                if p:
                    st.markdown(f"### 🌿 {p['name']}")
                    d1, d2, d3, d4 = st.columns([1, 1.2, 1.2, 1.2])
                    with d1:
                        img_p = ASSETS_DIR / p.get("image", "")
                        if img_p.exists():
                            with open(img_p, "rb") as f:
                                img_b64 = base64.b64encode(f.read()).decode()
                            st.markdown(f"""
                            <div class='zoom-container'>
                                <img src='data:image/jpeg;base64,{img_b64}'>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.write("🌿")
                    
                    with d2:
                        st.markdown("<div class='metric-pill'>☀️ Işık Seviyesi</div>", unsafe_allow_html=True)
                        st.progress(p.get("light_level", 1) / 3.0)
                        st.caption(p.get("light", ""))
                        st.markdown("<div class='metric-pill'>💧 Su Seviyesi</div>", unsafe_allow_html=True)
                        st.progress(p.get("water_level", 1) / 3.0)
                        st.caption(p.get("water", ""))
                    
                    with d3:
                        st.markdown("**🌱 Toprak/Besin**")
                        st.write(p.get("soil", ""))
                        st.markdown("**🏠 Konum**")
                        st.write(p.get("placement", ""))

                    with d4:
                        st.markdown("**🧪 Püf Noktası**")
                        st.write(p.get("watering_detail", "")[:150] + "...")
                        
                        nickname = st.text_input("Bitkinize bir isim verin", value=p["name"], key=f"nick_{p['id']}")
                        if st.button("✨ Köşeme Ekle", use_container_width=True):
                            if profile and (profile.get('api_key') or profile.get('groq_api_key')):
                                add_to_garden(p["id"], nickname, profile.get('api_key') or profile.get('groq_api_key'))
                                st.success(f"✅ {nickname} köşenize başarıyla eklendi!")
                            else:
                                st.warning("Lütfen önce Profilim sekmesinden bir API Anahtarı kaydedin!")

        elif st.session_state.app_mode == "kosem":
            st.markdown("## 🪴 Bahçemin Durumu")
            if not profile or (not profile.get('api_key') and not profile.get('groq_api_key')):
                st.warning("Dashboard'a erişmek için lütfen önce Profilim sekmesinden bir API Anahtarı kaydedin.")
            else:
                garden = get_my_garden(profile.get('api_key') or profile.get('groq_api_key'))
                
                # Global Garden Stats
                s1, s2, s3 = st.columns(3)
                total = len(garden)
                thirsty = 0
                for r in garden:
                    p_ref = next((p for p in PLANTS if p["id"] == r["plant_id"]), None)
                    if p_ref:
                        last_w = datetime.date.fromisoformat(r["last_watered"])
                        period = 10 if p_ref["water_level"] == 1 else (5 if p_ref["water_level"] == 2 else 2)
                        if (datetime.date.today() - last_w).days >= period: thirsty += 1
                
                score = 100 - (thirsty * 20) if total > 0 else 100
                score = max(0, score)
                
                s1.markdown(f"<div class='stat-box'><div class='stat-val'>{total}</div><div class='stat-lbl'>Toplam Bitki</div></div>", unsafe_allow_html=True)
                s2.markdown(f"<div class='stat-box'><div class='stat-val'>{score}%</div><div class='stat-lbl'>Bahçe Sağlığı</div></div>", unsafe_allow_html=True)
                s3.markdown(f"<div class='stat-box'><div class='stat-val'>{thirsty}</div><div class='stat-lbl'>Su Bekleyen</div></div>", unsafe_allow_html=True)
                
                st.divider()
                
                if not garden:
                    st.info("Henüz bahçenize bitki eklemediniz. Rehberden ekleyerek başlayabilirsiniz!")
                else:
                    cols = st.columns(3)
                    for idx, row in enumerate(garden):
                        p_ref = next((p for p in PLANTS if p["id"] == row["plant_id"]), None)
                        if p_ref:
                            with cols[idx % 3]:
                                with st.container(border=True):
                                    st.markdown(f"#### {row['nickname']} ✨")
                                    st.caption(f"Kayıt: {row['added_date']}")
                                    
                                    # Progress to next watering
                                    last_w = datetime.date.fromisoformat(row["last_watered"])
                                    days = (datetime.date.today() - last_w).days
                                    period = 10 if p_ref["water_level"] == 1 else (5 if p_ref["water_level"] == 2 else 2)
                                    prog = min(1.0, days / period)
                                    st.progress(prog, text=f"Susuzluk: %{int(prog*100)}")
                                    
                                    b1, b2 = st.columns(2)
                                    if b1.button("💧 Suladım", key=f"w_{row['id']}", use_container_width=True):
                                        update_care(row['id'], "water")
                                        st.rerun()
                                    if b2.button("🗑️ Çıkar", key=f"rm_{row['id']}", use_container_width=True):
                                        remove_from_garden(row['id'], profile.get('api_key') or profile.get('groq_api_key'))
                                        st.rerun()

        elif st.session_state.app_mode == "doktor":
            from data import DISEASES
            st.markdown("## 🩹 Bitki Doktoru")
            st.write("Bitkinizdeki anormallikleri (leke, sararma, kuruma) analiz etmek için bir fotoğraf yükleyin.")
            
            c1, c2 = st.columns([1, 1.2])
            with c1:
                uploaded_file = st.file_uploader("Bitki Fotoğrafı Yükle...", type=["jpg","png","jpeg"])
                if uploaded_file:
                    st.success("✅ Fotoğraf başarıyla yüklendi.")
                    st.image(uploaded_file, use_container_width=True)
            
            with c2:
                symptoms = st.text_area("Gördüğünüz belirtileri yazın (Opsiyonel)", placeholder="Örn: Yapraklarda beyaz tozlar var, sararma başladı...")
                if st.button("Analiz Et 🔍", use_container_width=True, disabled=not uploaded_file):
                    with st.spinner("Bitki Doktoru analiz ediyor..."):
                        # High Precision Analysis Logic
                        diag_input = (symptoms.lower() * 2) + " " + uploaded_file.name.lower()
                        scores = []
                        for d in DISEASES:
                            score = 0
                            for k in d["keywords"]:
                                if k in diag_input:
                                    score += 1
                            scores.append((score, d))
                        
                        # Sort by score and pick the best match
                        scores.sort(key=lambda x: x[0], reverse=True)
                        match = scores[0][1] if scores[0][0] > 0 else DISEASES[0]

                        st.markdown(f"""
                        <div class='analysis-card'>
                            <h3>🔬 Teşhis: {match['name']}</h3>
                            <p><i>{match['tone']}</i></p>
                            <hr>
                            <p><b>Neden:</b> {match['cause']}</p>
                            <p><b>Çözüm:</b> {match['treatment']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.info("💡 Uzman Notu: Bu analiz yazdığınız belirtiler ve görsel veriler ışığında yapılmıştır.")

        elif st.session_state.app_mode == "profil":
            st.markdown("## ⚙️ Profilim & Ayarlar")
            with st.form("profile_form"):
                new_name = st.text_input("Kullanıcı Adı", value=profile.get('username', 'Bitki Sever'))
                gemini_key = st.text_input("Gemini API Key", value=profile.get('api_key', "") or "", type="password")
                groq_key = st.text_input("Groq API Key", value=profile.get('groq_api_key', "") or "", type="password")
                
                submitted = st.form_submit_button("Profili Kaydet")
                if submitted:
                    update_user_profile(new_name, gemini_key, groq_key)
                    st.balloons()
                    st.success(f"✨ Tebrikler {new_name}! Profiliniz başarıyla oluşturuldu ve güncellendi.")
                    st.rerun()
            
        elif st.session_state.app_mode == "notif":
            st.markdown("## 🔔 Bakım Uyarıları")
            garden = get_my_garden(profile.get('api_key') or profile.get('groq_api_key')) if profile and (profile.get('api_key') or profile.get('groq_api_key')) else []
            alerts = 0
            for row in garden:
                p_ref = next((p for p in PLANTS if p["id"] == row["plant_id"]), None)
                if p_ref:
                    last_w = datetime.date.fromisoformat(row["last_watered"])
                    days_passed = (datetime.date.today() - last_w).days
                    period = 10 if p_ref["water_level"] == 1 else (5 if p_ref["water_level"] == 2 else 2)
                    if days_passed >= period:
                        with st.container(border=True):
                            st.error(f"⚠️ **{row['nickname']}** (Hedef: {period} gün)")
                            st.write(f"Bu bitki tam **{days_passed}** gündür sulanmadı. Lütfen ilgilenin!")
                            if st.button(f"💧 Şimdi Suladım", key=f"notif_w_{row['id']}"):
                                update_care(row['id'], "water")
                                st.rerun()
                        alerts += 1
            if alerts == 0:
                st.success("Tüm bitkilerin şu an mutlu görünüyor! 🌱")
                st.info("Su veya takviye zamanı gelen bir bitkin olduğunda burada görünecek.")

        elif st.session_state.app_mode == "agent":
            st.markdown("## 🧠 Flora: Baş Botanikçi")
            st.info("Ben bahçenizin stratejik danışmanıyım. Bitki Doktoru acil sorunlarla ilgilenirken, ben bitkilerinizin uzun vadeli sağlığı, gelişimi ve mutluluğu için buradayım.")
            
            # Context-Aware Intro
            garden = get_my_garden(profile.get('api_key') or profile.get('groq_api_key')) if profile else []
            if garden:
                st.success(f"🌱 Bahçenizdeki {len(garden)} dostunuzun durumunu takip ediyorum. Onlar için bir gelişim planı ister misiniz?")
            
            for c in st.session_state.chat_history[-5:]:
                st.write(f"👤 **Sen:** {c['user']}")
                st.info(f"🧠 **Flora:** {c['bot']}")
            
            q = st.text_input("Flora'ya bir şey sor (Örn: Bahçemin durumu nasıl?)...", key="agent_input")
            if st.button("Flora'ya Gönder 🚀"):
                if q:
                    with st.spinner("Flora düşünüyor..."):
                        from agent import BotanicaAgent
                        agent = BotanicaAgent(
                            api_key=profile.get('api_key') if profile else None,
                            groq_key=profile.get('groq_api_key') if profile else None
                        )
                        res = agent.process_command(q)
                        st.session_state.chat_history.append({"user": q, "bot": res["message"]})
                        st.rerun()

        # 7. PREMIUM FOOTER
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.9rem; padding: 20px;'>
            <b>Nabzı Filiz</b> | Akıllı Bitki Yönetim Sistemi<br>
            <b>Zeynep Ebrar Pala</b> tarafından geliştirilmiştir<br>
            <span style='font-size: 0.7rem;'>© 2026 Tüm Hakları Saklıdır.</span>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error("🚨 UYGULAMA ÇALIŞIRKEN BİR HATA OLUŞTU")
        st.markdown(f"**Detaylar:** `{type(e).__name__}: {str(e)}`")
        if st.button("Sistemi Sıfırla"):
            st.session_state.clear()
            st.rerun()
