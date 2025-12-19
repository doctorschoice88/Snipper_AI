import streamlit as st
import traceback
import time

st.set_page_config(page_title="System Check", layout="wide")

st.title("🛠️ Repair Mode: System Check")

# 1. Library Check
st.write("Checking Libraries...")
try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    import google.generativeai as genai
    st.success("✅ All Libraries Installed Successfully!")
except Exception as e:
    st.error(f"❌ Library Error: {e}")
    st.stop()

# 2. Data Connection Check
st.write("Testing Market Data Connection...")
symbol = "^NSEI"
try:
    # Attempt download
    data = yf.download(symbol, period="5d", interval="1d", progress=False)
    
    if data is None or data.empty:
        st.warning("⚠️ Real Data Failed (Market/Network Block). Switching to Mock Data for UI Testing.")
        # Create Mock Data just to show UI works
        dates = pd.date_range(end=pd.Timestamp.now(), periods=5)
        data = pd.DataFrame({
            'Close': [24000, 24100, 24050, 24200, 24150],
            'High': [24100, 24200, 24100, 24300, 24200],
            'Low': [23900, 24000, 24000, 24100, 24100]
        }, index=dates)
        is_mock = True
    else:
        st.success("✅ Real Nifty Data Received!")
        is_mock = False

    # Fix Columns if needed
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)

    latest = data.iloc[-1]
    price = latest['Close']
    
    st.metric("Nifty Check", f"{price:.2f}", "Mock Data" if is_mock else "Live Data")
    
    st.write("### Data Preview:")
    st.dataframe(data.tail())

except Exception as e:
    st.error(f"❌ Data Error: {e}")
    st.code(traceback.format_exc())

# 3. AI Check
st.divider()
st.write("Checking AI Brain...")
api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Say 'System is Operational'")
        st.success(f"✅ AI Response: {response.text}")
    except Exception as e:
        st.error(f"❌ AI Error: {e}")
else:
    st.warning("⚠️ API Key Not Found in Secrets")

st.info("Agar yeh screen dikh rahi hai, iska matlab App sahi hai, bas connection check ho raha hai.")
