from pathlib import Path
from textwrap import dedent

import streamlit as st

from .themes import DEFAULT_THEME, THEMES


def get_current_theme_name() -> str:
    theme_name = st.session_state.get("theme", DEFAULT_THEME)
    if theme_name not in THEMES:
        theme_name = DEFAULT_THEME
        st.session_state["theme"] = theme_name
    return theme_name


def get_current_theme() -> dict:
    return THEMES[get_current_theme_name()]


def build_theme_css(theme: dict) -> str:
    return dedent(
        f"""
        :root {{
            --background-color: {theme["background"]};
            --secondary-background-color: {theme["surface"]};
            --secondary-background-alt: {theme["surface_alt"]};
            --sidebar-color: {theme["sidebar"]};
            --top-bar-color: {theme["top_bar"]};
            --text-color: {theme["text_color"]};
            --muted-text-color: {theme["muted_text_color"]};
            --title-text-color: {theme["title_text_color"]};
            --caption-color: {theme["caption_color"]};
            --zone-text-color: {theme["zone_text_color"]};
            --border-color: {theme["border_color"]};
            --accent-color: {theme["accent_color"]};
            --accent-soft: {theme["accent_soft"]};
            --success-color: {theme["success_color"]};
            --warning-color: {theme["warning_color"]};
            --danger-color: {theme["danger_color"]};
            --shadow-color: {theme["shadow_color"]};
            --hero-gradient: {theme["hero_gradient"]};
        }}
        """
    ).strip()


def load_css() -> dict:
    theme = get_current_theme()
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "assets" / "style.css",
        here.parent / "style.css",
        here.parent.parent / "assets" / "style.css",
    ]

    stylesheet = ""
    for css_path in candidates:
        if css_path.exists():
            stylesheet = css_path.read_text(encoding="utf-8")
            break

    if not stylesheet:
        st.warning("style.css not found in expected frontend assets paths.")
        return theme

    combined_css = f"<style>{build_theme_css(theme)}\n{stylesheet}</style>"
    if hasattr(st, "html"):
        st.html(combined_css)
    else:
        st.markdown(combined_css, unsafe_allow_html=True)
    return theme
