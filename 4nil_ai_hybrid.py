import streamlit as st
import yfinance as yf
import pandas as pd
import os
from dotenv import load_dotenv
from google import genai

# ==========================================
# ૧. સિસ્ટમ સેટઅપ
# ==========================================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

st.set_page_config(page_title="ABNV TERMINAL | NILESH SHAH", layout="wide")

# ==========================================
# ૨. સાયબર-ગોલ્ડ રોબોટિક UI
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; }
    [data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #d4af37; }
    
    /* ટેબલ સ્ટાઇલિંગ */
    .f-o-table {
        width: 100%;
        border-collapse: collapse;
        color: white;
        font-family: 'Roboto Mono', sans-serif;
    }
    .f-o-table th {
        background: #111;
        color: #d4af37;
        padding: 12px;
        text-align: left;
        border-bottom: 2px solid #d4af37;
        font-family: 'Orbitron', sans-serif;
    }
    .f-o-table td {
        padding: 12px;
        border-bottom: 1px solid rgba(212, 175, 55, 0.1);
    }
    
    .action-badge { padding: 5px 10px; border-radius: 4px; font-weight: bold; font-family: 'Orbitron', sans-serif; font-size: 0.8em; }
    .buy { background-color: #00ff00; color: #000; box-shadow: 0 0 10px #00ff00; }
    .sell { background-color: #ff0000; color: #fff; box-shadow: 0 0 10px #ff0000; }
    .neutral { background-color: #555; color: #fff; }
    
    h1, h2, h3, h4 { font-family: 'Orbitron', sans-serif; color: #d4af37 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ૩. પાવરફુલ માર્કેટ એન્જિન (OHL Support)
# ==========================================

def get_terminal_data(ticker):
    try:
        ticker = ticker.strip().upper()
        if not ticker.endswith('.NS') and not ticker.startswith('^'): ticker += '.NS'
        t = yf.Ticker(ticker)
        df = t.history(period="2d") # છેલ્લો ૨ દિવસનો ડેટા
        if df.empty: return None
        
        last = df.iloc[-1]
        
        # BUY/SELL Logic
        ema_data = t.history(period="1mo", interval="1d")
        ema20 = ema_data['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        if last['Close'] > ema20: act, cls = "BUY", "buy"
        else: act, cls = "SELL", "sell"
        
        return {
            "Symbol": ticker.replace(".NS", ""),
            "Price": round(last['Close'], 2),
            "Open": round(last['Open'], 2),
            "High": round(last['High'], 2),
            "Low": round(last['Low'], 2),
            "Signal": act,
            "Class": cls
        }
    except: return None

# ==========================================
# ૪. ડેશબોર્ડ લેઆઉટ
# ==========================================

with st.sidebar:
    st.title("NILESH SHAH")
    st.write("👤 Admin: Verified")
    st.markdown("---")
    if st.button("RESCAN TERMINAL"): st.rerun()

st.title("🔱 ABNV MASTER TERMINAL")

# ટોપ ઇન્ડેક્સ લાઈન
nifty = get_terminal_data('^NSEI')
banknifty = get_terminal_data('^NSEBANK')
c1, c2 = st.columns(2)
if nifty: c1.metric("NIFTY 50", f"₹{nifty['Price']}", nifty['Signal'])
if banknifty: c2.metric("BANK NIFTY", f"₹{banknifty['Price']}", banknifty['Signal'])

st.markdown("---")

# F&O Table Section
st.subheader("📡 F&O LIVE RADAR")

watchlist = ['RELIANCE', 'INFY', 'TCS', 'HDFCBANK', 'ZOMATO', 'DIXON', 'TATAMOTORS', 'ICICIBANK']
all_data = []

# ડેટા ભેગો કરવો
for s in watchlist:
    data = get_terminal_data(s)
    if data: all_data.append(data)

# HTML ટેબલ બનાવવું
table_html = """
<table class="f-o-table">
    <thead>
        <tr>
            <th>SYMBOL</th>
            <th>PRICE</th>
            <th>OPEN</th>
            <th>HIGH</th>
            <th>LOW</th>
            <th>SIGNAL</th>
        </tr>
    </thead>
    <tbody>
"""

for d in all_data:
    table_html += f"""
        <tr>
            <td style="color:#d4af37; font-weight:bold;">{d['Symbol']}</td>
            <td>₹{d['Price']}</td>
            <td style="color:#888;">{d['Open']}</td>
            <td style="color:#00ff00;">{d['High']}</td>
            <td style="color:#ff4b4b;">{d['Low']}</td>
            <td><span class="action-badge {d['Class']}">{d['Signal']}</span></td>
        </tr>
    """

table_html += "</tbody></table>"
st.markdown(table_html, unsafe_allow_html=True)

st.markdown("---")

# Command Core
if pr := st.chat_input("ટાર્ગેટ પૂછો..."):
    # જૂનું AI લોજિક અહીં ચાલુ રહેશે...
    st.chat_message("user").markdown(pr)
    st.chat_message("assistant").markdown("નિલેશભાઈ, ટર્મિનલ અપડેટ થઈ ગયું છે. હવે ડેટા ચેક કરો.")