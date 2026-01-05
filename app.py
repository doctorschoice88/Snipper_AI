import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import google.generativeai as genai

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Sniper AI (Aggressive)",
    page_icon="🔥",
    layout="wide"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: #e1e1e1; font-family: 'Roboto Mono', monospace; }
    .buy-signal { background-color: rgba(0, 255, 0, 0.1); color: #00ff00; font-weight: bold; padding: 15px; border: 2px solid #00ff00; border-radius: 10px; text-align: center; }
    .sell-signal { background-color: rgba(255, 0, 0, 0.1); color: #ff0000; font-weight: bold; padding: 15px; border: 2px solid #ff0000; border-radius: 10px; text-align: center; }
    .wait-signal { background-color: rgba(255, 255, 0, 0.1); color: #ffff00; font-weight: bold; padding: 15px; border: 2px solid #ffff00; border-radius: 10px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🔥 SCALPER CONTROLS")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("Brain: Active")
    else:
        api_key = st.text_input("API Key", type="password")
    
    st.divider()
    # Scalping ke liye chota timeframe default kar diya
    timeframe = st.selectbox("Timeframe", ["5m", "15m", "1h"], index=0) 
    if st.button("🔄 REFRESH"):
        st.rerun()

# --- DATA ENGINE ---
def get_scalper_data(interval):
    try:
        symbol = "^NSEI"
        # Sirf 5 din ka data chahiye speed ke liye
        data = yf.download(symbol, period="5d", interval=interval, progress=False)
        
        if data is None or data.empty:
            return None, "Data Unavailable"

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        # --- INDICATORS ---
        data['RSI'] = ta.rsi(data['Close'], length=14)
        
        # Supertrend (Standard 10, 3)
        try:
            st = ta.supertrend(data['High'], data['Low'], data['Close'], length=10, multiplier=3)
            data['SUPERTREND_DIR'] = st.iloc[:, 1] # 1 = Green, -1 = Red
        except:
            data['SUPERTREND_DIR'] = 0

        # Latest Values
        latest = data.iloc[-1]
        close_price = float(latest['Close'])
        rsi_val = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50
        st_dir = int(latest['SUPERTREND_DIR']) if not pd.isna(latest['SUPERTREND_DIR']) else 0

        # --- AGGRESSIVE LOGIC (No EMA Filter) ---
        signal = "WAIT"
        reason = "Choppy Market"
        
        # BUY CALL Logic
        if st_dir == 1 and rsi_val > 55:
            signal = "BUY CALL (CE) 🚀"
            reason = "Supertrend GREEN + RSI Strong (>55)"
            
        # BUY PUT Logic (Ab yeh chalega!)
        # Pehle yahan 'Price < 200 EMA' ki shart thi, wo hata di maine.
        elif st_dir == -1 and rsi_val < 45:
            signal = "BUY PUT (PE) 🔻"
            reason = "Supertrend RED + RSI Weak (<45)"
            
        return {
            "price": close_price,
            "rsi": rsi_val,
            "supertrend": "🟢 UP" if st_dir == 1 else "🔴 DOWN",
            "signal": signal,
            "reason": reason,
            "interval": interval
        }, None

    except Exception as e:
        return None, str(e)

# --- UI LAYOUT ---
st.title("🔥 NIFTY SCALPER AI")
st.caption("Aggressive Mode: Put Side Unlocked")

data, error = get_scalper_data(timeframe)

if data:
    c1, c2, c3 = st.columns(3)
    c1.metric("NIFTY Spot", f"{data['price']:.2f}")
    c2.metric("Trend", data['supertrend'])
    c3.metric("RSI", f"{data['rsi']:.2f}")

    st.divider()
    
    # Signal Box
    if "BUY CALL" in data['signal']:
        st.markdown(f'<div class="buy-signal">{data["signal"]}</div>', unsafe_allow_html=True)
    elif "BUY PUT" in data['signal']:
        st.markdown(f'<div class="sell-signal">{data["signal"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="wait-signal">✋ {data["signal"]}</div>', unsafe_allow_html=True)
        
    st.info(f"**LOGIC:** {data['reason']}")

    # Gemini Analysis
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        if st.button("🤖 Quick Analysis"):
            prompt = (
                f"Nifty {data['interval']} Chart: Price {data['price']}, RSI {data['rsi']}, Trend {data['supertrend']}. "
                f"Signal is {data['signal']}. "
                "Give me a quick SCALPING view. Should I short? Keep it very short."
            )
            with st.spinner("Checking..."):
                try:
                    res = model.generate_content(prompt)
                    st.write(res.text)
                except:
                    st.error("AI Busy")

else:
    st.error(f"Error: {error}")
