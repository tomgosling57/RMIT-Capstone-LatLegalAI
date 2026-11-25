import os
import streamlit as st


def _load_css(*relative_paths: str) -> str:
    """Load one or more CSS files relative to this file's directory."""
    current_dir = os.path.dirname(__file__)
    parts = []
    for rel in relative_paths:
        path = os.path.normpath(os.path.join(current_dir, rel))
        with open(path, "r") as f:
            parts.append(f.read())
    return "\n".join(parts)


def apply_theme():
    """Inject the LatLegal AI design-system CSS into the Streamlit app.

    Loads:
      - styles/base.css  — CSS variables, typography, layout, Streamlit overrides
      - styles/components.css — reusable component classes
    """
    css = _load_css(
        "../styles/base.css",
        "../styles/components.css",
    )
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def apply_custom_css(css: str):
    """Inject an arbitrary CSS string into the page.

    Args:
        css: Raw CSS to inject.
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_page_header(
    title: str,
    subtitle: str = None,
    icon: str = None,
    show_back: bool = False,
    back_url: str = None,
):
    """Render a standardised page header with title and optional subtitle.

    Args:
        title:     Main page title (will be uppercased via CSS).
        subtitle:  Optional subtitle / description.
        icon:      Optional emoji/icon prepended to the title.
        show_back: Whether to render a back-navigation button.
        back_url:  Explicit URL for the back button; falls back to
                   ``window.history.back()`` when omitted.
    """
    back_button_html = ""
    if show_back:
        if back_url:
            back_button_html = f"""
            <div style="margin-bottom:1rem;">
                <a href="{back_url}"
                   style="display:inline-flex;align-items:center;
                          color:var(--text-secondary);text-decoration:none;
                          padding:0.4rem 0.9rem;border:1px solid var(--border-subtle);
                          border-radius:var(--radius-md);transition:all 0.2s ease;
                          font-size:var(--font-sm);">
                    ← Back
                </a>
            </div>"""
        else:
            back_button_html = """
            <div style="margin-bottom:1rem;">
                <button onclick="window.history.back()"
                        style="display:inline-flex;align-items:center;
                               background:none;border:1px solid var(--border-subtle);
                               padding:0.4rem 0.9rem;border-radius:var(--radius-md);
                               cursor:pointer;color:var(--text-secondary);
                               transition:all 0.2s ease;font-size:var(--font-sm);">
                    ← Back
                </button>
            </div>"""

    heading = f"{icon} {title}" if icon else title

    st.markdown(
        f"""
        <div class="page-header">
            {back_button_html}
            <h1>{heading}</h1>
            {f'<p>{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_card(
    title: str = None,
    content: str = None,
    icon: str = None,
    actions: list = None,
):
    """Render a surface card with optional title, content, and action HTML.

    Args:
        title:   Optional card heading.
        content: Inner HTML string.
        icon:    Optional emoji/icon prepended to the title.
        actions: List of raw HTML strings rendered at the bottom of the card.
    """
    card_title_html = (
        f"<h3>{icon + ' ' + title if icon else title}</h3>" if title else ""
    )
    actions_html = "".join(actions) if actions else ""

    st.markdown(
        f"""
        <div class="card">
            {card_title_html}
            {content or ''}
            {actions_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(text: str, status: str = "info"):
    """Render a small coloured status badge.

    Args:
        text:   Badge label.
        status: One of ``success``, ``warning``, ``error``, ``info``.
    """
    st.markdown(
        f'<span class="status-badge status-badge--{status}">{text}</span>',
        unsafe_allow_html=True,
    )


def render_alert(message: str, type: str = "info", title: str = None):
    """Render a themed alert box.

    Args:
        message: Alert body text / HTML.
        type:    One of ``success``, ``warning``, ``error``, ``info``.
        title:   Optional bold heading inside the alert.
    """
    icons = {"success": "✅", "warning": "⚠️", "error": "❌", "info": "ℹ️"}
    icon = icons.get(type, "ℹ️")
    title_html = f"<div class='alert-title'>{title}</div>" if title else ""

    st.markdown(
        f"""
        <div class="alert-box alert--{type}">
            <div class="alert-icon">{icon}</div>
            <div class="alert-content">
                {title_html}
                {message}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scanned_indicator() -> str:
    """Return HTML for a scanned-PDF informational indicator.

    The indicator uses the ``warning`` status colour, BEM-named classes,
    Rajdhani for the label and Inter for the body text, the standard
    spacing/radius scale, and the ``fadeIn`` animation defined in
    ``components.css``.

    Returns:
        Raw HTML string suitable for ``st.markdown(..., unsafe_allow_html=True)``.
    """
    return """
    <div class="scanned-indicator fade-in" role="alert" aria-live="polite">
        <span class="scanned-indicator__icon" aria-hidden="true">⚠️</span>
        <div class="scanned-indicator__content">
            <span class="scanned-indicator__label">Scanned Document</span>
            <span class="scanned-indicator__message">
                This document is scanned — OCR processing is being applied
                to extract the text content.
            </span>
        </div>
    </div>
    """


def render_empty_state(
    icon: str = "📦",
    title: str = "No items found",
    description: str = None,
):
    """Render a centred empty-state placeholder.

    Args:
        icon:        Large emoji/icon displayed at the top.
        title:       Heading text.
        description: Optional supporting text.
    """
    desc_html = f"<p class='empty-description'>{description}</p>" if description else ""
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-icon">{icon}</div>
            <h3 class="empty-title">{title}</h3>
            {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
