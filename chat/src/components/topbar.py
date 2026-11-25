import os
import base64
import streamlit as st


def _logo_base64() -> str:
    """Return the LegalAiLogo as a base64 data-URI so it works inside
    st.markdown() without needing a public URL."""
    logo_path = os.path.join(
        os.path.dirname(__file__), "..", "static", "LegalAiLogo.png"
    )
    logo_path = os.path.normpath(logo_path)
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{data}"
    return ""


def topbar():
    """Render the LatLegal AI top navigation bar with logo and nav links."""
    logo_src = _logo_base64()
    logo_html = (
        f'<img src="{logo_src}" alt="LatLegal AI Logo" '
        f'style="width:44px;height:44px;object-fit:contain;flex-shrink:0;" />'
        if logo_src
        else '<span style="font-size:1.5rem;">⚖️</span>'
    )

    st.markdown(
        f"""
        <style>
        @import url(
            'https://fonts.googleapis.com/css2?family=Rajdhani:'
            'wght@400;500;600;700&family=Inter:'
            'wght@300;400;500;600&display=swap'
        );

        /* ── Navbar shell — mirrors website .navbar ── */
        .latlegal-navbar {{
            background-color: #05070A;
            border-bottom: 2px solid #0033AA;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 2rem;
            height: 68px;
            position: sticky;
            top: 0;
            z-index: 999;
            margin-bottom: 1.5rem;
        }}

        /* Logo + brand name group */
        .latlegal-navbar .nav-logo-group {{
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            flex-shrink: 0;
        }}

        .latlegal-navbar .nav-brand {{
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.35rem;
            font-weight: 700;
            color: #FFD700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin: 0;
            white-space: nowrap;
        }}

        /* Ghost pill nav buttons */
        .latlegal-navbar-buttons .stButton > button {{
            background-color: transparent !important;
            color: #AAAAAA !important;
            border: 1px solid #1E2A5A !important;
            border-radius: 12px !important;
            padding: 7px 20px !important;
            font-family: 'Rajdhani', sans-serif !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.04em !important;
            transition: border-color 0.2s, color 0.2s !important;
            box-shadow: none !important;
        }}

        .latlegal-navbar-buttons .stButton > button:hover {{
            border-color: #FFD700 !important;
            color: #FFD700 !important;
            background-color: transparent !important;
            transform: none !important;
            box-shadow: none !important;
        }}

        /* Remove extra top margin Streamlit adds after the HTML block */
        .latlegal-navbar + div {{
            margin-top: 0 !important;
        }}
        </style>

        <div class="latlegal-navbar">
            <div class="nav-logo-group">
                {logo_html}
                <span class="nav-brand">LatLegal AI</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Nav buttons rendered as Streamlit columns so they remain interactive
    st.markdown('<div class="latlegal-navbar-buttons">', unsafe_allow_html=True)

    DEV_MODE = os.environ.get("DEV_MODE", "").lower() in ("true", "1", "yes")

    if DEV_MODE:
        col1, col2, col_spacer = st.columns([2, 2, 8])
    else:
        col1, col_spacer = st.columns([2, 10])

    with col1:
        if st.button("📄 Summary", use_container_width=True, key="nav_summary"):
            st.switch_page("ui.py")

    if DEV_MODE:
        with col2:
            if st.button("⚙️ Dev Tool", use_container_width=True, key="nav_devtool"):
                st.switch_page("pages/Developer_Tool.py")

    st.markdown("</div>", unsafe_allow_html=True)
