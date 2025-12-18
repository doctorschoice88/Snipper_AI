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
        st.markdown("<h1 style='text-align: center;'>🔒 ACCESS RESTRICTED</h1>", unsafe_allow_html=True)
        password = st.text_input("Enter Password to Unlock Sniper AI:", type="password")
        if st.button("UNLOCK SYSTEM"):
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ GALAT PASSWORD! HAT JAO.")
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
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("🤖 Brain Connected")
    else:
        api_key = st.text_input("API Key", type="password")
    
    st.divider()
    timeframe = st.selectbox("Timeframe", ["5m", "15m", "1h", "1d"], index=1)
    if st.button("🔄 REFRESH DATA"):
        st.rerun()

# --- DATA ENGINE ---
def get_sniper_data(interval):
    try:
        symbol = "^NSEI"
        data = yf.download(symbol, period="5d", interval=interval, progress=False)
        
        if data.empty: return None, "No Data Found"
        
        # Clean Columns (Multi-index fix)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        # Indicators
        data['RSI'] = ta.rsi(data['Close'], length=14)
        data['EMA_200'] = ta.ema(data['Close'], length=200)
        
        # Supertrend Fix
        st = ta.supertrend(data['High'], data['Low'], data['Close'], length=10, multiplier=3)
        # Use column index 1 (usually Direction) to avoid name errors
        data['SUPERTREND_DIR'] = st.iloc[:, 1] 

        latest = data.iloc[-1]
        
        close_price = float(latest['Close'])
        rsi_val = float(latest['RSI'])
        st_dir = int(latest['SUPERTREND_DIR']) # 1 = Green, -1 = Red
        ema_200 = float(latest['EMA_200']) if not pd.isna(latest['EMA_200']) else 0

        # Signal Logic
        signal = "WAIT"
        reason = "Market Undecided"
        
        if st_dir == 1 and close_price > ema_200 and rsi_val > 50:
            signal = "BUY CALL (CE) 🚀"
            reason = "Trend UP (Green) + Price > 200 EMA + RSI Strong"
        elif st_dir == -1 and close_price < ema_200 and rsi_val < 50:
            signal = "BUY PUT (PE) 🔻"
            reason = "Trend DOWN (Red) + Price < 200 EMA + RSI Weak"
            
        return {
            "price": close_price,
            "rsi": rsi_val,
            "supertrend": "🟢 BULLISH" if st_dir == 1 else "🔴 BEARISH",
            "ema_200": ema_200,
            "signal": signal,
            "reason": reason,
            "interval": interval
        }

    except Exception as e:
        return None, str(e)

# --- UI LAYOUT ---
st.title("🎯 NIFTY SNIPER AI")
data, error = get_sniper_data(timeframe)

if data:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", f"{data['price']:.2f}")
    c2.metric("Trend", data['supertrend'])
    c3.metric("RSI", f"{data['rsi']:.2f}")
    c4.metric("200 EMA", f"{data['ema_200']:.2f}")

    st.divider()
    st.subheader("📡 SIGNAL GENERATOR")
    
    if "BUY CALL" in data['signal']:
        st.markdown(f'<div class="buy-signal">{data["signal"]}</div>', unsafe_allow_html=True)
    elif "BUY PUT" in data['signal']:
        st.markdown(f'<div class="sell-signal">{data["signal"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="wait-signal">✋ {data["signal"]}</div>', unsafe_allow_html=True)
        
    st.info(f"**LOGIC:** {data['reason']}")

    # --- GEMINI CONFIRMATION ---
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        if st.button("🤖 Ask Gemini to Confirm Trade"):
            with st.spinner("Analyzing Risk..."):
                prompt = (
                    f"Analyze Nifty Data ({data['interval']}): "
                    f"Price: {data['price']}, RSI: {data['rsi']}, Trend: {data['supertrend']}, Signal: {data['signal']}. "
                    "You are a Strict Trading Coach. If Signal is BUY, suggest Stop Loss & Target. "
                    "If WAIT, tell me to relax in Hinglish."
                )
                try:
                    res = model.generate_content(prompt)
                    st.success("AI ADVICE:")
                    st.write(res.text)
                except Exception as e:
                    st.error(f"AI Error: {e}")
else:
    st.error(f"Data Error: {error}")
