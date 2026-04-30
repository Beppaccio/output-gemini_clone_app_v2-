import streamlit as st

def render_app():
    st.set_page_config(page_title="Gemini-like Portfolio", layout="wide")
    st.title("🚀 Gemini-like Momentum Portfolio")
    st.markdown("Seleziona titoli e lancia la pipeline completa")

if __name__ == "__main__":
    render_app()
