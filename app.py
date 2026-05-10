"""
Botanica AI: Evimizin Güzelleri
Production Entry Point
"""
import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. SET PAGE CONFIG (MUST BE THE VERY FIRST STREAMLIT COMMAND)
st.set_page_config(
    page_title="Nabzı Filiz | Akıllı Bahçem",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

try:
    # Load environment variables
    load_dotenv()

    # Add project root and backend to path
    root_dir = Path(__file__).parent
    if str(root_dir) not in sys.path: sys.path.append(str(root_dir))
    if str(root_dir / "backend") not in sys.path: sys.path.append(str(root_dir / "backend"))

    # Import and run the main frontend application
    from frontend.app import render_app
    render_app()

except Exception as e:
    st.error("🚨 UYGULAMA BAŞLATILAMADI")
    st.markdown(f"""
    **Başlatma Hatası:** `{type(e).__name__}: {str(e)}`
    
    Lütfen projenin tüm dosyalarının doğru yerleştirildiğinden ve `backend/` klasörünün mevcut olduğundan emin olun.
    """)
    st.stop()

if __name__ == "__main__":
    pass
