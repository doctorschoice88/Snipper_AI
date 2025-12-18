import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import google.generativeai as genai

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SNIPER TRADE AI 🎯",
    page_icon="🎯",
    layout="wide"
)

# --- 🔒 PASSWORD PROTECTION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "APP_PASSWORD" in st.secrets:
    if not st.session_state.authenticated:
        st.markdown("<h1 style='text-align: center;'>🔒 SNIPER ACCESS LOCKED</h1>", unsafe_allow_html=True)
        password = st.text_input("Enter Password:", type="password")
        if st.button("UNLOCK SYSTEM"):
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ WRONG PASSWORD!")
        st.stop()

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: #e1e1e1; font-family: 'Roboto Mono', monospace; }
    .buy-signal { 
        background-color: rgba(0, 255, 0, 0.1); color: #00ff00; font-weight: bold; font-size: 24px; 
        border: 2px solid #00ff00; padding: 15px; border-radius: 10px; text-align: center; 
    }
    .sell-signal { 
        background-color: rgba(255, 0, 0, 0.1); color: #ff0000; font-weight: bold; font-size: 24px; 
        border: 2px solid #ff0000; padding: 15px; border-radius: 10px; text-align: center; 
    }
    .wait-signal { 
        background-color: rgba(255, 255, 0, 0.1); color: #ffff00; font-weight: bold; font-size: 24px; 
        border: 2px solid #ffff00; padding: 15px; border-radius: 10px; text-align: center; 
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎯 SNIPER CONTROLS")
    
    # API Key Check
    if "GEMINI_API_KEY"
