import streamlit as st
import base64
import os

def inject_garland():
    # Yerel custom_flower.png dosyasını yükle (Kök assets klasöründen)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    img_path = os.path.join(root_dir, "assets", "custom_flower.png")
    img_url = ""
    
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            img_url = f"data:image/png;base64,{encoded}"
    else:
        # Fallback
        img_url = "https://www.transparentpng.com/download/pink-flowers/pink-flowers-png-8.png"

    css_content = f"""<style>
.garland-container {{position: fixed;top: 0;left: 0;width: 100%;height: 80px;background-image: url('{img_url}');background-repeat: repeat-x;background-size: contain;z-index: 999999;pointer-events: none;animation: garlandSway 6s infinite ease-in-out;filter: drop-shadow(0 5px 15px rgba(0,0,0,0.1));transform-origin: top center;}}
@keyframes garlandSway {{0%, 100% {{ transform: translateY(0) rotate(0deg); }} 25% {{ transform: translateY(5px) rotate(1deg); }} 50% {{ transform: translateY(8px) rotate(0deg); }} 75% {{ transform: translateY(5px) rotate(-1deg); }}}}
.main .block-container {{padding-top: 100px !important;}}
[data-testid="stHeader"] {{background: transparent !important;}}
</style>
<div class="garland-container"></div>"""
    st.markdown(css_content, unsafe_allow_html=True)
