import streamlit as st

def inject_garland():
    """Enjekte edilen premium çiçek sarmaşığı (Saf CSS sürümü)."""
    # Premium SVG Garland Data URI
    svg_garland = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cg transform='translate(50,50)'%3E%3Cpath fill='%23FF8B71' opacity='0.8' d='M0,-20 Q10,-35 20,-20 Q30,-5 0,0 Q-30,-5 -20,-20 Q-10,-35 0,-20 Z' transform='rotate(0)'/%3E%3Cpath fill='%23FF8B71' opacity='0.8' d='M0,-20 Q10,-35 20,-20 Q30,-5 0,0 Q-30,-5 -20,-20 Q-10,-35 0,-20 Z' transform='rotate(72)'/%3E%3Cpath fill='%23FF8B71' opacity='0.8' d='M0,-20 Q10,-35 20,-20 Q30,-5 0,0 Q-30,-5 -20,-20 Q-10,-35 0,-20 Z' transform='rotate(144)'/%3E%3Cpath fill='%23FF8B71' opacity='0.8' d='M0,-20 Q10,-35 20,-20 Q30,-5 0,0 Q-30,-5 -20,-20 Q-10,-35 0,-20 Z' transform='rotate(216)'/%3E%3Cpath fill='%23FF8B71' opacity='0.8' d='M0,-20 Q10,-35 20,-20 Q30,-5 0,0 Q-30,-5 -20,-20 Q-10,-35 0,-20 Z' transform='rotate(288)'/%3E%3Ccircle fill='%23FFD700' r='5'/%3E%3C/g%3E%3C/svg%3E"
    
    css_content = f"""<style>
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 80px;
        background-image: url("{svg_garland}");
        background-repeat: repeat-x;
        background-size: 80px 80px;
        z-index: 1001;
        pointer-events: none;
        animation: garlandSway 10s infinite ease-in-out;
        filter: drop-shadow(0 5px 15px rgba(0,0,0,0.05));
        opacity: 0.85;
    }}
    @keyframes garlandSway {{
        0%, 100% {{ transform: translateY(0) rotate(0deg); }}
        50% {{ transform: translateY(5px) rotate(0.5deg); }}
    }}
    .main .block-container {{
        padding-top: 100px !important;
    }}
    </style>"""
    st.markdown(css_content, unsafe_allow_html=True)
