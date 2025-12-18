import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import google.generativeai as genai
import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SNIPER TRADE AI 🎯",
    page_icon="🎯",
    layout="wide"
)

# --- CUSTOM CSS (Trading Terminal Look) ---
st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: #e1e1e1; font-family: 'Roboto Mono', monospace; }
    .metric-box { border: 1px solid #333; padding: 10px; border-radius: 5px; background-color: #161b22; text-align: center; }
    .buy-signal { 
        background-color: rgba(0, 255, 0, 0.1); 
        color: #00ff00; 
        font-weight: bold; 
        font-size: 24px; 
        border: 2px solid #00ff00; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center;
    }
    .sell-signal { 
        background-color: rgba(255, 0, 0, 0.1); 
        color: #ff0000; 
        font-weight: bold; 
        font-size: 24px; 
        border: 2px solid #ff0000; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center;
    }
    .wait-signal { 
        background-color: rgba(255, 255, 0, 0.1); 
        color: #ffff00; 
        font-weight: bold; 
        font-size: 24px; 
        border: 2px solid #ffff00; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎯 SNIPER CONTROLS")
    
    # API Key Handling (Secrets First)
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("🤖 AI Brain Connected")
    else:
        api_key = st.text_input("Enter Gemini API Key", type="password")
    
    st.divider()
    timeframe = st.selectbox("Timeframe", ["5m", "15m", "1h", "1d"], index=1)
    st.info("Intraday ke liye 15m best hai.")
    
    if st.button("🔄 SCAN MARKET"):
        st.rerun()

# --- DATA ENGINE ---
def get_sniper_data(interval):
    try:
        # Fetch Data (Nifty 50)
        symbol = "^NSEI"
        # yfinance data fetch
        data = yf.download(symbol, period="5d", interval=interval, progress=False)
        
        if data.empty: return None, "No Data Found"

        # Handle Multi-index columns if present (yfinance update)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        # --- CALCULATE INDICATORS (The Math) ---
        
        # 1. RSI (Momentum)
        data['RSI'] = ta.rsi(data['Close'], length=14)
        
        # 2. VWAP (Volume Weighted Average Price) - Institutional Level
        # Note: yfinance often misses volume on index, using approximation or HL3
        # If Volume is 0, VWAP might fail, so we wrap it
        try:
            data['VWAP'] = ta.vwap(data['High'], data['Low'], data['Close'], data['Volume'])
        except:
            data['VWAP'] = data['Close'] # Fallback
        
        # 3. Supertrend (Direction)
        st_data = ta.supertrend(data['High'], data['Low'], data['Close'], length=10, multiplier=3)
        # Supertrend returns multiple columns, usually 'SUPERT_10_3.0' is the line
        # We need to determine direction based on Close vs Supertrend line
        data['SUPERTREND'] = st_data['SUPERT_10_3.0']
        
        # 4. EMA 200 (Long Term Trend)
        data['EMA_200'] = ta.ema(data['Close'], length=200)

        # Get Latest Candle Values
        latest = data.iloc[-1]
        
        close_price = float(latest['Close'])
        rsi_val = float(latest['RSI'])
        supertrend_val = float(latest['SUPERTREND'])
        ema_200 = float(latest['EMA_200']) if not pd.isna(latest['EMA_200']) else 0
        
        # Determine Trend Direction
        # If Close > Supertrend Line -> Bullish (Green)
        # If Close < Supertrend Line -> Bearish (Red)
        supertrend_dir = 1 if close_price > supertrend_val else -1

        # --- SIGNAL LOGIC (The Sniper Rule) ---
        signal = "WAIT"
        reason = "Market Undecided"
        
        # BUY Condition: Supertrend Green + Price > EMA 200 + RSI Healthy
        if supertrend_dir == 1 and close_price > ema_200 and rsi_val > 50:
            signal = "BUY CALL (CE) 🚀"
            reason = "Trend is UP (Supertrend Green) & Price above 200 EMA."
            
        # SELL Condition: Supertrend Red + Price < EMA 200 + RSI Weak
        elif supertrend_dir == -1 and close_price < ema_200 and rsi_val < 50:
            signal = "BUY PUT (PE) 🔻"
            reason = "Trend is DOWN (Supertrend Red) & Price below 200 EMA."
            
        return {
            "price": close_price,
            "rsi": rsi_val,
            "supertrend": "🟢 BULLISH" if supertrend_dir == 1 else "🔴 BEARISH",
            "ema_200": ema_200,
            "signal": signal,
            "reason": reason,
            "interval": interval
        }

    except Exception as e:
        return None, str(e)

# --- UI LAYOUT ---
st.title("🎯 NIFTY SNIPER AI")
st.caption("Powered by Maths + Gemini AI")

data, error = get_sniper_data(timeframe)

if data:
    # Top Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Price", f"{data['price']:.2f}")
    c2.metric("Trend (Supertrend)", data['supertrend'])
    c3.metric("RSI (Strength)", f"{data['rsi']:.2f}")
    c4.metric("200 EMA", f"{data['ema_200']:.2f}")

    st.divider()

    # --- SIGNAL BOX ---
    st.subheader("📡 AI SIGNAL GENERATOR")
    
    if "BUY CALL" in data['signal']:
        st.markdown(f'<div class="buy-signal">{data["signal"]}</div>', unsafe_allow_html=True)
    elif "BUY PUT" in data['signal']:
        st.markdown(f'<div class="sell-signal">{data["signal"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="wait-signal">✋ {data["signal"]}</div>', unsafe_allow_html=True)
        
    st.info(f"**Reason:** {data['reason']}")

    # --- GEMINI VALIDATION ---
    if api_key:
        genai.configure(api_key=api_key)
        # Using Flash for speed
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        if st.button("🤖 Ask Gemini to Confirm"):
            with st.spinner("Sniper AI analyzing chart data..."):
                prompt = (
                    f"Analyze this Nifty 50 Data on {data['interval']} timeframe:\n"
                    f"Price: {data['price']}, RSI: {data['rsi']}, Supertrend: {data['supertrend']}, Signal: {data['signal']}.\n"
                    "You are a Strict Trading Coach. If the signal is BUY, give a logical Stop Loss and Target.\n"
                    "If Signal is WAIT, tell a joke to calm the trader down.\n"
                    "Keep it strictly Hinglish and short."
                )
                try:
                    response = model.generate_content(prompt)
                    st.success("AI Analysis:")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"AI Error: {str(e)}")

else:
    st.error(f"Error fetching data: {error}")
