import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sniper AI (Locked)", layout="wide", page_icon="🔐")

# --- 🔒 PASSWORD LOCK SYSTEM ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Sirf tabhi lock lagao agar Secrets mein password set hai
if "APP_PASSWORD" in st.secrets:
    if not st.session_state.authenticated:
        # Lock Screen UI
        st.markdown("<h1 style='text-align: center;'>🔒 SNIPER ACCESS DENIED</h1>", unsafe_allow_html=True)
        st.write("---")
        
        # Password Input
        password = st.text_input("Enter Secret Password:", type="password")
        
        if st.button("UNLOCK SYSTEM"):
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun() # Page refresh karke andar le jao
            else:
                st.error("❌ GALAT PASSWORD! TRY AGAIN.")
        
        # Yahin rok do, aage ka code run nahi hone dena
        st.stop()

# --- MAIN APP LOGIC STARTS HERE ---

# --- MANUAL INDICATOR FUNCTIONS ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_supertrend(df, period=10, multiplier=3):
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # ATR Calculation
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    
    # Bands
    hl2 = (high + low) / 2
    final_upperband = hl2 + (multiplier * atr)
    final_lowerband = hl2 - (multiplier * atr)
    
    supertrend = [True] * len(df) # True = Green, False = Red
    
    for i in range(1, len(df)):
        curr, prev = i, i-1
        if final_upperband[curr] < final_upperband[prev] or close[prev] > final_upperband[prev]:
            final_upperband[curr] = min(final_upperband[curr], final_upperband[prev])
        else:
            final_upperband[curr] = final_upperband[curr]
            
        if final_lowerband[curr] > final_lowerband[prev] or close[prev] < final_lowerband[prev]:
            final_lowerband[curr] = max(final_lowerband[curr], final_lowerband[prev])
        else:
            final_lowerband[curr] = final_lowerband[curr]
            
        if supertrend[prev] == True and close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        elif supertrend[prev] == False and close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        else:
            supertrend[curr] = supertrend[prev]
            
    return supertrend

# --- MAIN UI ---
try:
    # Sidebar
    with st.sidebar:
        st.header("🔥 Scalper Controls")
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("Brain: Active")
        else:
            api_key = st.text_input("API Key", type="password")
        
        timeframe = st.selectbox("Timeframe", ["15m", "5m", "1h"])
        if st.button("Refresh"):
            st.rerun()

    st.title("🔥 NIFTY AGGRESSIVE SNIPER")
    
    # Data Fetching
    symbol = "^NSEI"
    data = yf.download(symbol, period="5d", interval=timeframe, progress=False)

    if data is None or data.empty:
        st.error("⚠️ Market Data Not Found (Market Closed?).")
    else:
        # Columns Fix
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        # Calculations
        df = data.copy()
        df['RSI'] = calculate_rsi(df['Close'])
        st_trend = calculate_supertrend(df)

        # Latest Values
        latest = df.iloc[-1]
        price = float(latest['Close'])
        rsi = float(latest['RSI'])
        is_bullish = st_trend[-1] # True = UP, False = DOWN

        # --- AGGRESSIVE LOGIC ---
        signal = "WAIT"
        color = "orange"
        reason = "Choppy"

        # BUY CALL
        if is_bullish and rsi > 55:
            signal = "BUY CALL 🚀"
            color = "green"
            reason = "Trend UP + Momentum Strong"
        
        # BUY PUT
        elif not is_bullish and rsi < 45:
            signal = "BUY PUT 🔻"
            color = "red"
            reason = "Trend DOWN + Momentum Weak"

        # UI Display
        c1, c2, c3 = st.columns(3)
        c1.metric("Nifty", f"{price:.2f}")
        c2.metric("RSI", f"{rsi:.2f}")
        c3.metric("Trend", "UP 🟢" if is_bullish else "DOWN 🔴")

        st.markdown(f"""
            <div style="background-color:{color}; padding:15px; border-radius:10px; text-align:center;">
                <h1 style="color:white; margin:0;">{signal}</h1>
                <p style="color:white;">{reason}</p>
            </div>
        """, unsafe_allow_html=True)

        # AI Check
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            if st.button("🤖 Quick Check"):
                prompt = f"Nifty {price}, RSI {rsi}, Trend {'UP' if is_bullish else 'DOWN'}. Signal: {signal}. Should I scalp? Short answer."
                res = model.generate_content(prompt)
                st.info(res.text)

except Exception as e:
    st.error(f"Error: {str(e)}")
