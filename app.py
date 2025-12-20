
import streamlit as st
import traceback

# --- PAGE CONFIG (Sabse upar hona chahiye) ---
st.set_page_config(page_title="Sniper AI (Safe Mode)", layout="wide", page_icon="🛡️")

# --- ERROR CATCHER WRAPPER ---
try:
    # Imports
    import yfinance as yf
    import pandas_ta as ta
    import pandas as pd
    import google.generativeai as genai
    import numpy as np

    # --- PASSWORD CHECK ---
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Agar secrets mein password hai toh check karo
    if "APP_PASSWORD" in st.secrets:
        if not st.session_state.authenticated:
            st.title("🔒 LOCKED")
            pwd = st.text_input("Password:", type="password")
            if st.button("Login"):
                if pwd == st.secrets["APP_PASSWORD"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Wrong Password")
            st.stop()

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🎯 Controls")
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("Connected ✅")
        else:
            api_key = st.text_input("API Key", type="password")
        
        if st.button("Refresh Data"):
            st.rerun()

    # --- MAIN LOGIC ---
    st.title("🎯 Sniper Trade AI")

    # Data Fetching
    symbol = "^NSEI"
    
    # Try block for Data
    try:
        data = yf.download(symbol, period="5d", interval="15m", progress=False)
        
        if data is None or data.empty:
            st.error("⚠️ Market Data nahi mil raha. (Market Closed or API Issue)")
        else:
            # Multi-index fix
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)

            # Indicators
            data['RSI'] = ta.rsi(data['Close'], length=14)
            data['EMA'] = ta.ema(data['Close'], length=200)
            
            # Supertrend (Try/Except taaki crash na ho)
            try:
                st_data = ta.supertrend(data['High'], data['Low'], data['Close'], length=10, multiplier=3)
                # Direction column usually index 1
                data['ST'] = st_data.iloc[:, 1] 
            except:
                data['ST'] = 0

            # Latest Values
            latest = data.iloc[-1]
            price = float(latest['Close'])
            rsi = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50
            ema = float(latest['EMA']) if not pd.isna(latest['EMA']) else price

            # Display
            c1, c2, c3 = st.columns(3)
            c1.metric("Nifty Price", f"{price:.2f}")
            c2.metric("RSI", f"{rsi:.2f}")
            c3.metric("EMA 200", f"{ema:.2f}")

            # AI Logic
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                if st.button("🤖 Ask AI"):
                    with st.spinner("Thinking..."):
                        prompt = f"Analyze Nifty Price {price}, RSI {rsi}. Buy or Sell? Short answer."
                        res = model.generate_content(prompt)
                        st.write(res.text)

    except Exception as e:
        st.error(f"Data Fetching Error: {str(e)}")

# --- CRITICAL ERROR CATCHER ---
except Exception as e:
    st.error("🚨 App Crash Error:")
    st.code(traceback.format_exc())
