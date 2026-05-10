"""
Nabzı Filiz: Akıllı Bitki Yönetim Sistemi
Streamlit Cloud Entry Point
"""
import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime

# 1. SET PAGE CONFIG (MUST BE THE VERY FIRST COMMAND)
st.set_page_config(
    page_title="Nabzı Filiz | Akıllı Bahçem",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. PATH SETUP
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path: sys.path.append(str(ROOT_DIR))
if str(ROOT_DIR / "backend") not in sys.path: sys.path.append(str(ROOT_DIR / "backend"))

# 3. DEFENSIVE IMPORT & RUN
try:
    from frontend.app import render_app
    render_app()
except Exception as e:
    st.error("🚨 UYGULAMA BAŞLATILAMADI")
    st.markdown(f"**Detaylar:** `{type(e).__name__}: {str(e)}`")
    st.info("İpucu: Streamlit Cloud'da 'requirements.txt' dosyasının doğru olduğundan emin olun.")
    
    # Show traceback for debugging
    import traceback
    st.code(traceback.format_exc())
