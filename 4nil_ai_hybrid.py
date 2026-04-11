import streamlit as st
import yfinance as yf
import pandas as pd
import os
from dotenv import load_dotenv
from google import genai

# ==========================================
# ૧. સિસ્ટમ સેટઅપ (Wide Layout)
# ==========================================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

st.set_page_config(page_title="ABNV TERMINAL | NILESH SHAH", layout="wide")

# ==========================================
# ૨. અલ્ટ્રા-કોમ્પેક્ટ CSS Grid (No Scroll)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@400;700&display=swap');
    
    /* મેઈન બેકગ્રાઉન્ડ */
    .stApp { background-color: #030303; }
    [data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #d4af37; }
    
    /* સ્કોલિંગ ટિકર (વધુ પાતળું) */
    .ticker-wrap { width: 100%; overflow: hidden; background-color: #0a0a0a; border-bottom: 1px solid #d4af37; padding: 2px 0; margin-bottom: 5px; }
    .ticker { display: inline-block; white-space: nowrap; padding-right: 100%; animation: ticker 30s linear infinite; }
    @keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
    .ticker-item { display: inline-block; padding: 0 1.5rem; font-family: 'Orbitron', sans-serif; font-size: 0.9em; font-weight: bold; }
    .t-up { color: #00ff00; } .t-down { color: #ff4b4b; } .t-title { color: #d4af37; }
    
    /* 💡 ધ બ્રહ્માસ્ત્ર: CSS Grid (આ ક્યારેય ઉપર-નીચે નહિ થાય) */
    .radar-grid {
        display: grid;
        grid-template-columns: 1fr 1fr; /* 2 સરખા ભાગ */
        gap: 10px; /* બે ટેબલ વચ્ચેની જગ્યા */
    }
    
    /* અલ્ટ્રા કોમ્પેક્ટ ટેબલ */
    .f-o-table { width: 100%; border-collapse: collapse; color: white; font-family: 'Roboto Mono', sans-serif; font-size: 0.8em; background: #0a0a0a; border: 1px solid #222; }
    .f-o-table th { background: #111; color: #d4af37; padding: 4px; text-align: left; border-bottom: 1px solid #d4af37; font-family: 'Orbitron', sans-serif; font-size: 0.85em; }
    
    /* 💡 ફિક્સ: પેડિંગ સાવ ઓછું કરી દીધું */
    .f-o-table td { padding: 2px 4px; border-bottom: 1px solid #1a1a1a; }
    
    .sector-header { background: #1a1a1a !important; color: #d4af37 !important; font-weight: bold; font-family: 'Orbitron', sans-serif; text-align: left !important; font-size: 0.9em; border-left: 2px solid #d4af37; padding: 2px 8px !important; }
    
    .stChatMessage { background: #111 !important; border-left: 2px solid #d4af37 !important; border-radius: 5px; padding: 5px 8px; margin-bottom: 5px; }
    .stChatMessage p { color: #ddd !important; font-size: 0.9em; font-family: 'Roboto Mono', sans-serif; margin: 0; }
    
    .action-badge { padding: 1px 4px; border-radius: 2px; font-weight: bold; font-family: 'Orbitron', sans-serif; font-size: 0.7em; }
    .buy { background-color: #00ff00; color: #000; }
    .sell { background-color: #ff0000; color: #fff; }
    
    h1, h2, h3, h4 { font-family: 'Orbitron', sans-serif; color: #d4af37 !important; margin-bottom: 5px; padding: 0; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ૩. ફાસ્ટ માર્કેટ એન્જિન
# ==========================================
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
        
        ema_data = t.history(period="1mo", interval="1d")
        ema20 = ema_data['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        if last['Close'] > ema20: act, cls = "BUY", "buy"
        else: act, cls = "SELL", "sell"
        
        trend_class = "t-up" if last['Close'] >= prev_close else "t-down"
        arrow = "▲" if last['Close'] >= prev_close else "▼"
        
        return {
            "Symbol": ticker.replace(".NS", ""),
            "Price": round(last['Close'], 2),
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
    st.write("🤖 v16.4 [No-Scroll Grid]")
    st.markdown("---")
    if st.button("RESCAN TERMINAL"): 
        st.cache_data.clear() 
        st.rerun()

# --- SCROLLING TICKER ---
nifty = get_terminal_data('^NSEI')
banknifty = get_terminal_data('^NSEBANK')

ticker_html = "<div class='ticker-wrap'><div class='ticker'>"
if nifty: ticker_html += f"<div class='ticker-item'><span class='t-title'>NIFTY 50:</span> <span class='{nifty['Trend_Class']}'>{nifty['Price']} {nifty['Arrow']}</span></div>"
if banknifty: ticker_html += f"<div class='ticker-item'><span class='t-title'>BANK NIFTY:</span> <span class='{banknifty['Trend_Class']}'>{banknifty['Price']} {banknifty['Arrow']}</span></div>"
ticker_html += "</div></div>"
st.markdown(ticker_html, unsafe_allow_html=True)

# 💡 ડેશબોર્ડના 2 મેઈન ભાગ: ડાબે રડાર (મોટો), જમણે ચેટ (નાનો)
left, right = st.columns([1.8, 1])

# --- ડાબી બાજુ: હાર્ડકોડેડ 2-કૉલમ CSS Grid ---
with left:
    st.markdown("<h4>📡 F&O SECTOR RADAR</h4>", unsafe_allow_html=True)
    
    # દરેક સેક્ટરમાં 5 સ્ટોક (કુલ 25 સ્ટોક એક જ સ્ક્રીન પર)
    fo_sectors = {
        "IT": ['INFY', 'TCS', 'WIPRO', 'HCLTECH', 'TECHM'],
        "BANKING": ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK'],
        "AUTO": ['TATAMOTORS', 'M&M', 'MARUTI', 'BAJAJ-AUTO', 'EICHERMOT'],
        "ENERGY": ['RELIANCE', 'ONGC', 'NTPC', 'POWERGRID', 'COALINDIA'],
        "FMCG": ['ITC', 'HUL', 'BRITANNIA', 'TATACONSUM', 'NESTLEIND'],
        "METALS": ['TATASTEEL', 'HINDALCO', 'JSWSTEEL', 'VEDL', 'COALINDIA']
    }
    
    live_context_data = []
    
    def build_table(sector_name, stocks):
        html = "<table class='f-o-table'><thead><tr><th>SYMBOL</th><th>PRICE</th><th>SIGNAL</th></tr></thead><tbody>"
        html += f"<tr><td colspan='3' class='sector-header'>{sector_name}</td></tr>"
        for s in stocks:
            d = get_terminal_data(s)
            if d: 
                live_context_data.append(f"{d['Symbol']}: {d['Price']} ({d['Signal']})")
                html += f"<tr><td style='color:#ffffff; font-weight:bold;'>{d['Symbol']}</td><td>₹{d['Price']}</td><td><span class='action-badge {d['Class']}'>{d['Signal']}</span></td></tr>"
        html += "</tbody></table>"
        return html

    sectors = list(fo_sectors.items())
    half = len(sectors) // 2
    
    # 💡 અહીં CSS Grid નો ઉપયોગ કર્યો છે, જેથી ક્યારેય ઉપર-નીચે ના થાય
    grid_html = "<div class='radar-grid'>"
    
    # કૉલમ 1 નો ડેટા
    grid_html += "<div>"
    for name, stocks in sectors[:half]:
        grid_html += build_table(name, stocks) + "<br>"
    grid_html += "</div>"
    
    # કૉલમ 2 નો ડેટા
    grid_html += "<div>"
    for name, stocks in sectors[half:]:
        grid_html += build_table(name, stocks) + "<br>"
    grid_html += "</div>"
    
    grid_html += "</div>"
    
    st.markdown(grid_html, unsafe_allow_html=True)

# --- જમણી બાજુ: કમાન્ડ બોટ ---
with right:
    st.markdown("<h4>🤖 COMMAND CORE</h4>", unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    
    # ચેટ બોક્સની હાઈટ વધારી જેથી બાજુના ટેબલ સાથે મેચ થાય
    chat_box = st.container(height=650) 
    for m in st.session_state.messages[-10:]:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if pr := st.chat_input("ટાર્ગેટ પૂછો..."):
        st.session_state.messages.append({"role": "user", "content": pr})
        with chat_box.chat_message("user"): st.markdown(pr)
        
        with chat_box.chat_message("assistant"):
            try:
                memory_string = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-4:]])
                market_status = " | ".join(live_context_data)
                
                ai_prompt = f"""
                માલિક: નિલેશ શાહ. માર્કેટ ડેટા: {market_status}
                તમારે એકદમ દેશી, ટૂંકો અને સીધો જવાબ આપવાનો છે. માત્ર 1 જ લાઈનમાં.
                ઉદાહરણ: નિલેશભાઈ, ઇન્ફોસિસ અત્યારે 1292 રૂપિયા છે, માર્કેટમાં તેજી છે, 1310 નો ટાર્ગેટ રાખો.
                વાતચીત: {memory_string}
                User: {pr}
                Assistant: 
                """
                res = client.models.generate_content(model="gemini-3.1-flash-lite-preview", contents=ai_prompt)
                reply = res.text.replace("Assistant:", "").strip() if (res and res.text) else "સર્વરમાં લોચો છે."
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Engine Error: {e}")