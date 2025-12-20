import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sniper AI (Lite)", layout="wide", page_icon="🎯")

# --- MANUAL INDICATOR FUNCTIONS (Taaki Library ki zaroorat na pade) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(series, period=200):
    return series.ewm(span=period, adjust=False).mean()

def calculate_supertrend(df, period=10, multiplier=3):
    # Basic ATR Calculation
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    
    # Supertrend Bands
    hl2 = (high + low) / 2
    final_upperband = hl2 + (multiplier * atr)
    final_lowerband = hl2 - (multiplier * atr)
    
    supertrend = [True] * len(df) # True = Green, False = Red
    
    for i in range(1, len(df)):
        curr, prev = i, i-1
        # Upper Band Logic
        if final_upperband[curr] < final_upperband[prev] or close[prev] > final_upperband[prev]:
            final_upperband[curr] = min(final_upperband[curr], final_upperband[prev])
        else:
            final_upperband[curr] = final_upperband[curr]
        # Lower Band Logic
        if final_lowerband[curr] > final_lowerband[prev] or close[prev] < final_lowerband[prev]:
            final_lowerband[curr] = max(final_lowerband[curr], final_lowerband[prev])
        else:
            final_lowerband[curr] = final_lowerband[curr]
        # Trend Logic
        if supertrend[prev] == True and close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        elif supertrend[prev] == False and close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        else:
            supertrend[curr] = supertrend[prev]
            
    return supertrend

# --- MAIN APP LOGIC ---
try:
    st.title("🎯 Sniper Trade AI (Lite Mode)")

    # 1. Sidebar & Password
    if "APP_PASSWORD" in st.secrets:
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if not st.session_state.authenticated:
            pwd = st.text_input("Password:", type="password")
            if st.button("Login"):
                if pwd == st.secrets["APP_PASSWORD"]:
                    st.session_state.authenticated = True
                    st.rerun()
            st.stop()

    with st.sidebar:
        st.header("Controls")
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("API Connected ✅")
        else:
            api_key = st.text_input("Enter API Key", type="password")
        
        timeframe = st.selectbox("Timeframe", ["15m", "5m", "1h", "1d"])
        if st.button("Refresh"):
            st.rerun()

    # 2. Data Fetching
    symbol = "^NSEI"
    period = "1y" if timeframe == "1d" else "5d"
    
    # Download data
    data = yf.download(symbol, period=period, interval=timeframe, progress=False)

    if data is None or data.empty:
        st.error("⚠️ Market Data nahi mil raha.")
    else:
        # 3. Clean & Calculate
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        df = data.copy()
        df['RSI'] = calculate_rsi(df['Close'])
        df['EMA_200'] = calculate_ema(df['Close'], 200)
        st_trend = calculate_supertrend(df)

        # 4. Latest Values
        latest_idx = -1
        price = float(df['Close'].iloc[latest_idx])
        rsi = float(df['RSI'].iloc[latest_idx])
        ema = float(df['EMA_200'].iloc[latest_idx])
        is_bullish = st_trend[latest_idx]

        # 5. Logic
        signal = "WAIT"
        color = "orange"
        
        if is_bullish and price > ema and rsi > 50:
            signal = "BUY CALL 🚀"
            color = "green"
        elif not is_bullish and price < ema and rsi < 50:
            signal = "BUY PUT 🔻"
            color = "red"

        # 6. UI Display
        c1, c2, c3 = st.columns(3)
        c1.metric("Nifty", f"{price:.2f}")
        c2.metric("RSI", f"{rsi:.2f}")
        c3.metric("Trend", "UP 🟢" if is_bullish else "DOWN 🔴")

        st.markdown(f"""
            <div style="background-color:{color}; padding:15px; border-radius:10px; text-align:center;">
                <h2 style="color:white; margin:0;">SIGNAL: {signal}</h2>
            </div>
        """, unsafe_allow_html=True)

        # 7. AI Advice
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            if st.button("🤖 Ask Gemini"):
                with st.spinner("Analysing..."):
                    prompt = f"Nifty Price {price}, RSI {rsi}, Trend {'Bullish' if is_bullish else 'Bearish'}. Signal is {signal}. Short trading advice?"
                    res = model.generate_content(prompt)
                    st.info(res.text)

except Exception as e:
    st.error(f"Error: {str(e)}")
