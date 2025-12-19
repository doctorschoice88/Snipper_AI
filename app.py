import streamlit as st
import traceback
import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai

# ---------------- STREAMLIT SAFE MODE ----------------
st.set_option('client.showErrorDetails', True)
st.set_page_config(
    page_title="Sniper Trade AI 🛡️",
    page_icon="🎯",
    layout="wide"
)

# ---------------- INDICATOR FUNCTIONS ----------------
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ---------------- PASSWORD SYSTEM ----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "APP_PASSWORD" in st.secrets:
    if not st.session_state.authenticated:
        st.title("🔒 Sniper AI Locked")
        pwd = st.text_input("Enter Password", type="password")
        if st.button("Login"):
            if pwd == st.secrets["APP_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Wrong Password")
        st.stop()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("🎯 Controls")

    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("Gemini Connected ✅")
    else:
        api_key = st.text_input("Gemini API Key", type="password")

    interval = st.selectbox("Timeframe", ["5m", "15m", "30m"])
    refresh = st.button("🔄 Refresh Data")

# ---------------- MAIN APP ----------------
try:
    st.title("🎯 Sniper Trade AI (Safe Mode)")

    symbol = "NIFTYBEES.NS"  # Stable NIFTY proxy

    data = yf.download(
        symbol,
        period="5d",
        interval=interval,
        progress=False
    )

    if data is None or data.empty:
        st.error("⚠️ Market data not available (market closed / API issue)")
        st.stop()

    # Fix multi-index
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)

    # Indicators
    data["RSI"] = rsi(data["Close"])
    data["EMA200"] = ema(data["Close"], 200)

    latest = data.iloc[-1]
    price = float(latest["Close"])
    rsi_val = float(latest["RSI"]) if not np.isnan(latest["RSI"]) else 50
    ema_val = float(latest["EMA200"]) if not np.isnan(latest["EMA200"]) else price

    # ---------------- METRICS ----------------
    c1, c2, c3 = st.columns(3)
    c1.metric("NIFTY Price", f"{price:.2f}")
    c2.metric("RSI", f"{rsi_val:.2f}")
    c3.metric("EMA 200", f"{ema_val:.2f}")

    # ---------------- BASIC TRADE BIAS ----------------
    bias = "Neutral"
    if price > ema_val and rsi_val > 55:
        bias = "BUY Bias 📈"
    elif price < ema_val and rsi_val < 45:
        bias = "SELL Bias 📉"

    st.subheader("📊 Market Bias")
    st.info(bias)

    # ---------------- AI SECTION ----------------
    st.divider()
    st.subheader("🤖 Gemini AI Insight")

    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        if st.button("Ask AI"):
            with st.spinner("AI analyzing market..."):
                prompt = f"""
                NIFTY Intraday Snapshot:
                Price: {price}
                RSI: {rsi_val}
                EMA200: {ema_val}
                Bias: {bias}

                Give a short intraday view (BUY / SELL / WAIT) with 1 line reasoning.
                """

                response = model.generate_content(prompt)
                st.success(response.text)
    else:
        st.warning("🔑 Enter Gemini API Key to enable AI analysis")

except Exception:
    st.error("🚨 Critical App Error")
    st.code(traceback.format_exc())
