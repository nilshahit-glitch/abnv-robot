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
# ૨. સાયબર-ગોલ્ડ રોબોટિક UI & Scrolling Ticker
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; }
    [data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #d4af37; }
    
    /* 💡 સ્કોલિંગ ટિકર (ઉપર ફરતી પટ્ટી) ની ડિઝાઇન */
    .ticker-wrap { width: 100%; overflow: hidden; background-color: #111; border-bottom: 2px solid #d4af37; padding: 10px 0; margin-bottom: 20px; }
    .ticker { display: inline-block; white-space: nowrap; padding-right: 100%; animation: ticker 25s linear infinite; }
    @keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
    .ticker-item { display: inline-block; padding: 0 2rem; font-family: 'Orbitron', sans-serif; font-size: 1.2em; font-weight: bold; }
    .t-up { color: #00ff00; } .t-down { color: #ff4b4b; } .t-title { color: #d4af37; }
    
    /* સેક્ટર વાઈઝ ટેબલ */
    .f-o-table { width: 100%; border-collapse: collapse; color: white; font-family: 'Roboto Mono', sans-serif; }
    .f-o-table th { background: #111; color: #d4af37; padding: 12px; text-align: left; border-bottom: 2px solid #d4af37; font-family: 'Orbitron', sans-serif; }
    .f-o-table td { padding: 10px 12px; border-bottom: 1px solid rgba(212, 175, 55, 0.1); }
    
    /* સેક્ટર હેડિંગ માટે ગોલ્ડ પટ્ટી */
    .sector-header { background: #d4af37 !important; color: #000 !important; font-weight: bold; font-family: 'Orbitron', sans-serif; text-align: center !important; font-size: 1.1em; letter-spacing: 2px; }
    
    .stChatMessage { background: #151515 !important; border-left: 3px solid #d4af37 !important; border-radius: 8px; padding: 10px; margin-bottom: 10px; }
    .stChatMessage p { color: #ffffff !important; font-size: 1.1em; font-family: 'Roboto Mono', sans-serif; }
    
    .action-badge { padding: 5px 10px; border-radius: 4px; font-weight: bold; font-family: 'Orbitron', sans-serif; font-size: 0.8em; }
    .buy { background-color: #00ff00; color: #000; box-shadow: 0 0 8px #00ff00; }
    .sell { background-color: #ff0000; color: #fff; box-shadow: 0 0 8px #ff0000; }
    
    h1, h2, h3, h4 { font-family: 'Orbitron', sans-serif; color: #d4af37 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ૩. સુપરફાસ્ટ માર્કેટ એન્જિન (With Cache)
# ==========================================
# 💡 ડેટા દર 60 સેકન્ડે જ નવો આવશે, જેથી એપ હેંગ ના થાય
@st.cache_data(ttl=60)
def get_terminal_data(ticker):
    try:
        ticker = ticker.strip().upper()
        if not ticker.endswith('.NS') and not ticker.startswith('^'): ticker += '.NS'
        t = yf.Ticker(ticker)
        df = t.history(period="2d")
        if df.empty: return None
        
        last = df.iloc[-1]
        prev_close = df.iloc[-2]['Close'] if len(df) > 1 else last['Open']
        
        # BUY/SELL Logic
        ema_data = t.history(period="1mo", interval="1d")
        ema20 = ema_data['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        if last['Close'] > ema20: act, cls = "BUY", "buy"
        else: act, cls = "SELL", "sell"
        
        # ટિકરના કલર માટે ગ્રીન/રેડ નક્કી કરવું
        trend_class = "t-up" if last['Close'] >= prev_close else "t-down"
        arrow = "▲" if last['Close'] >= prev_close else "▼"
        
        return {
            "Symbol": ticker.replace(".NS", ""),
            "Price": round(last['Close'], 2),
            "Open": round(last['Open'], 2),
            "High": round(last['High'], 2),
            "Low": round(last['Low'], 2),
            "Signal": act,
            "Class": cls,
            "Trend_Class": trend_class,
            "Arrow": arrow
        }
    except: return None

# ==========================================
# ૪. ડેશબોર્ડ લેઆઉટ
# ==========================================

with st.sidebar:
    st.title("NILESH SHAH")
    st.write("🤖 v16.2 [Live Radar]")
    st.markdown("---")
    if st.button("RESCAN TERMINAL"): 
        st.cache_data.clear() # Cache સાફ કરવા બટન
        st.rerun()

# --- TOP SCROLLING TICKER (લગાતાર ફરતી પટ્ટી) ---
nifty = get_terminal_data('^NSEI')
banknifty = get_terminal_data('^NSEBANK')
sensex = get_terminal_data('^BSESN')

ticker_html = "<div class='ticker-wrap'><div class='ticker'>"
if nifty: ticker_html += f"<div class='ticker-item'><span class='t-title'>NIFTY 50:</span> <span class='{nifty['Trend_Class']}'>{nifty['Price']} {nifty['Arrow']}</span></div>"
if banknifty: ticker_html += f"<div class='ticker-item'><span class='t-title'>BANK NIFTY:</span> <span class='{banknifty['Trend_Class']}'>{banknifty['Price']} {banknifty['Arrow']}</span></div>"
if sensex: ticker_html += f"<div class='ticker-item'><span class='t-title'>SENSEX:</span> <span class='{sensex['Trend_Class']}'>{sensex['Price']} {sensex['Arrow']}</span></div>"
ticker_html += "</div></div>"

st.markdown(ticker_html, unsafe_allow_html=True)

# ------------------------------------------------

left, right = st.columns([1.6, 1])

# --- ડાબી બાજુ: સેક્ટર વાઈઝ લાઈવ ટેબલ ---
with left:
    st.subheader("📡 F&O SECTOR RADAR")
    
    # 💡 અહીં તમે તમારી રીતે સ્ટોક્સ ઉમેરી શકો છો
    fo_sectors = {
        "IT SECTOR": ['INFY', 'TCS', 'WIPRO', 'HCLTECH'],
        "BANKING & FINANCE": ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK'],
        "AUTO SECTOR": ['TATAMOTORS', 'M&M', 'MARUTI', 'BAJAJ-AUTO'],
        "ENERGY & OIL": ['RELIANCE', 'ONGC', 'NTPC', 'POWERGRID'],
        "FMCG": ['ITC', 'HUL', 'BRITANNIA', 'TATACONSUM']
    }
    
    live_context_data = []

    table_html = "<table class='f-o-table'><thead><tr><th>SYMBOL</th><th>PRICE</th><th>OPEN</th><th>HIGH</th><th>LOW</th><th>SIGNAL</th></tr></thead><tbody>"
    
    for sector, stocks in fo_sectors.items():
        # સેક્ટરનું ગોલ્ડ હેડિંગ
        table_html += f"<tr><td colspan='6' class='sector-header'>{sector}</td></tr>"
        
        for s in stocks:
            d = get_terminal_data(s)
            if d: 
                live_context_data.append(f"{d['Symbol']}: {d['Price']} ({d['Signal']})")
                table_html += f"<tr><td style='color:#ffffff; font-weight:bold;'>{d['Symbol']}</td><td>₹{d['Price']}</td><td style='color:#888;'>{d['Open']}</td><td style='color:#00ff00;'>{d['High']}</td><td style='color:#ff4b4b;'>{d['Low']}</td><td><span class='action-badge {d['Class']}'>{d['Signal']}</span></td></tr>"
                
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)

# --- જમણી બાજુ: દેશી બ્રોકર AI ---
with right:
    st.subheader("🤖 COMMAND CORE")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_box = st.container(height=550)
    for m in st.session_state.messages[-10:]:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if pr := st.chat_input("ટાર્ગેટ કે લેવલ પૂછો..."):
        st.session_state.messages.append({"role": "user", "content": pr})
        with chat_box.chat_message("user"): st.markdown(pr)
        
        with chat_box.chat_message("assistant"):
            try:
                memory_string = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-4:]])
                market_status = " | ".join(live_context_data)
                
                ai_prompt = f"""
                માલિક: નિલેશ શાહ. 
                માર્કેટ ડેટા: {market_status}
                
                તમારે નીચે આપેલા ઉદાહરણ પ્રમાણે જ એકદમ દેશી, ટૂંકો અને સીધો જવાબ આપવાનો છે. માત્ર 1 જ લાઈનમાં જવાબ આપવો.
                
                ઉદાહરણ 1:
                User: infosys target
                Assistant: નિલેશભાઈ, ઇન્ફોસિસ અત્યારે 1292 રૂપિયા છે, માર્કેટમાં તેજી છે, 1310 નો ટાર્ગેટ રાખો.
                
                હવે આ સવાલનો જવાબ આપો:
                વાતચીતનો ઇતિહાસ: {memory_string}
                User: {pr}
                Assistant: 
                """
                
                res = client.models.generate_content(model="gemini-3.1-flash-lite-preview", contents=ai_prompt)
                reply = res.text.replace("Assistant:", "").strip() if (res and res.text) else "સર્વરમાં લોચો છે."
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
            except Exception as e:
                st.error(f"Engine Error: {e}")