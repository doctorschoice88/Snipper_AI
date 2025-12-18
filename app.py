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
    
    # --- FIX: YAHAN ERROR THA ---
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("🤖 AI Brain: Connected")
    else:
        api_key = st.text_input("Enter Gemini API Key", type="password")
    
    st.divider()
    timeframe = st.selectbox("Timeframe", ["5m", "15m", "1h", "1d"], index=1)
    if st.button("🔄 SCAN MARKET"):
        st.rerun()

# --- SMART DATA ENGINE (Crash Proof) ---
def get_sniper_data(interval):
    try:
        symbol = "^NSEI"
        
        # FIX: Timeframe ke hisab se Data Period decide karo
        if interval == "1d":
            period_len = "6mo" # Daily ke liye 6 mahine chahiye
        else:
            period_len = "5d"  # Intraday ke liye 5 din kaafi hain
            
        # Data Download
        data = yf.download(symbol, period=period_len, interval=interval, progress=False)
        
        if data.empty: return None, "Market Data Empty / Closed"

        # Multi-index Columns Fix (Yahoo Issue)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        # Calculation ke liye kam se kam 20 candles honi chahiye
        if len(data) < 20:
            return None, f"Insufficient Data ({len(data)} candles only). Try smaller timeframe."

        # --- INDICATORS ---
        data['RSI'] = ta.rsi(data['Close'], length=14)
        data['EMA_200'] = ta.ema(data['Close'], length=200)
        
        # Supertrend (Robust Logic)
        try:
            st = ta.supertrend(data['High'], data['Low'], data['Close'], length=10, multiplier=3)
            # 2nd Column usually holds the direction (1 or -1)
            data['SUPERTREND_DIR'] = st.iloc[:, 1] 
        except:
            return None, "Supertrend Calculation Failed"

        # Get Latest Values
        latest = data.iloc[-1]
        
        close_price = float(latest['Close'])
        # Handle NaN values safely
        rsi_val = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50
        st_dir = int(latest['SUPERTREND_DIR']) if not pd.isna(latest['SUPERTREND_DIR']) else 0
        ema_200 = float(latest['EMA_200']) if not pd.isna(latest['EMA_200']) else close_price

        # --- SIGNAL LOGIC ---
        signal = "WAIT"
        reason = "No Clear Setup"
        
        # BUY Condition
        if st_dir == 1 and close_price > ema_200 and rsi_val > 50:
            signal = "BUY CALL (CE) 🚀"
            reason = "Trend UP + Price > 200 EMA + Momentum Strong"
            
        # SELL Condition
        elif st_dir == -1 and close_price < ema_200 and rsi_val < 50:
            signal = "BUY PUT (PE) 🔻"
            reason = "Trend DOWN + Price < 200 EMA + Momentum Weak"
            
        return {
            "price": close_price,
            "rsi": rsi_val,
            "supertrend": "🟢 BULLISH" if st_dir == 1 else "🔴 BEARISH",
            "ema_200": ema_200,
            "signal": signal,
            "reason": reason,
            "interval": interval
        }, None # <--- Error return fix

    except Exception as e:
        return None, f"Error: {str(e)}"

# --- UI LAYOUT ---
st.title("🎯 NIFTY SNIPER AI")
st.caption("Auto-Detecting Trends & Signals")

# Fetch Data
data, error = get_sniper_data(timeframe)

if data:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NIFTY Price", f"{data['price']:.2f}")
    c2.metric("Trend", data['supertrend'])
    c3.metric("RSI", f"{data['rsi']:.2f}")
    c4.metric("200 EMA", f"{data['ema_200']:.2f}")

    st.divider()
    st.subheader("📡 SIGNAL STATUS")
    
    # Display Colored Signal Box
    if "BUY CALL" in data['signal']:
        st.markdown(f'<div class="buy-signal">{data["signal"]}</div>', unsafe_allow_html=True)
    elif "BUY PUT" in data['signal']:
        st.markdown(f'<div class="sell-signal">{data["signal"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="wait-signal">✋ {data["signal"]}</div>', unsafe_allow_html=True)
        
    st.info(f"**LOGIC:** {data['reason']}")

    # --- GEMINI ANALYSIS BUTTON ---
    if api_key:
        genai.configure(api_key=api_key)
        # Using Flash for speed & reliability
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        if st.button("🤖 Ask Gemini to Validate Trade"):
            with st.spinner("Sniper AI analyzing risk..."):
                prompt = (
                    f"Analyze Nifty 50 Chart Data ({data['interval']}): "
                    f"Price: {data['price']}, RSI: {data['rsi']}, Trend: {data['supertrend']}, Signal: {data['signal']}. "
                    "You are a Senior Trader. "
                    "1. Confirm if this is a safe entry or risky. "
                    "2. Suggest a logical Stop Loss & Target. "
                    "3. Keep it short and Hinglish."
                )
                try:
                    res = model.generate_content(prompt)
                    st.success("AI TRADING COACH:")
                    st.write(res.text)
                except Exception as e:
                    st.error(f"AI Error: {e}")
else:
    st.error(f"Data Fetch Error: {error}")
        
