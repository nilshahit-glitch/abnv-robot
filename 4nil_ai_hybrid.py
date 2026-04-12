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

st.set_page_config(page_title="ABNV TERMINAL | NILESH & VASVI", layout="wide")

# ==========================================
# ૨. નેક્સ્ટ-લેવલ ગ્લાસ UI & ZERO FLICKER
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Roboto+Mono:wght@400;700&display=swap');
    
    /* 💡 ઝીરો-ફ્લિકર એન્જિન */
    div[data-stale="true"] { opacity: 1 !important; filter: none !important; transition: none !important; }
    [data-testid="stSkeleton"], .stSpinner { display: none !important; }
    * { transition: none !important; }
    
    /* મેઈન બેકગ્રાઉન્ડ (Dark Premium) */
    .stApp { background: radial-gradient(circle at 50% 0%, #1a1a1a 0%, #000000 70%); }
    [data-testid="stSidebar"] { background-color: rgba(10, 10, 10, 0.9) !important; border-right: 1px solid #d4af37; backdrop-filter: blur(10px); }
    
    /* 🌟 ABNV 3D ગ્લોઈંગ લોગો */
    .abnv-logo {
        font-family: 'Orbitron', sans-serif; font-size: 3em; font-weight: 900; text-align: center;
        background: linear-gradient(135deg, #d4af37, #fff4cc, #d4af37);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0px 0px 20px rgba(212, 175, 55, 0.4); letter-spacing: 5px; margin-bottom: 0px; line-height: 1.2;
    }
    .abnv-sub { color: #888; font-family: 'Orbitron', sans-serif; font-size: 0.8em; text-align: center; letter-spacing: 8px; margin-bottom: 20px; text-transform: uppercase; }
    
    /* 👑 ફાઉન્ડર્સ હાઈલાઈટ બેજ */
    .founders-badge {
        background: linear-gradient(90deg, rgba(212,175,55,0.1) 0%, rgba(212,175,55,0.2) 50%, rgba(212,175,55,0.1) 100%);
        border-top: 1px solid rgba(212,175,55,0.5); border-bottom: 1px solid rgba(212,175,55,0.5);
        padding: 15px 5px; text-align: center; margin-bottom: 20px;
    }
    .founders-badge p { margin: 0; color: #aaa; font-size: 0.8em; text-transform: uppercase; letter-spacing: 2px; }
    .founders-badge h3 { font-family: 'Orbitron', sans-serif; color: #d4af37 !important; margin: 5px 0 0 0; font-size: 1.1em; font-weight: bold; text-shadow: 0 0 10px rgba(212,175,55,0.3); }
    
    /* 💎 ગ્લાસ મોર્ફિઝમ કાર્ડ્સ (ટેબલ માટે) */
    .glass-card {
        background: rgba(20, 20, 20, 0.6); backdrop-filter: blur(8px);
        border: 1px solid rgba(212, 175, 55, 0.2); border-radius: 12px; padding: 10px; margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
    }
    
    /* ટેબલ ડિઝાઇન અપગ્રેડ */
    .f-o-table { width: 100%; border-collapse: collapse; color: white; font-family: 'Roboto Mono', sans-serif; font-size: 0.85em; }
    .f-o-table th { color: #d4af37; padding: 6px; text-align: left; border-bottom: 1px solid #d4af37; font-family: 'Orbitron', sans-serif; font-size: 0.85em; text-transform: uppercase; }
    .f-o-table td { padding: 4px 6px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    
    .sector-header { background: transparent !important; color: #d4af37 !important; font-weight: bold; font-family: 'Orbitron', sans-serif; text-align: left !important; font-size: 1em; border-left: 3px solid #d4af37; padding: 4px 10px !important; }
    .crypto-header { background: transparent !important; color: #f7931a !important; font-weight: bold; font-family: 'Orbitron', sans-serif; text-align: left !important; font-size: 1em; border-left: 3px solid #f7931a; padding: 4px 10px !important; }
    
    .sector-summary { font-family: 'Roboto Mono', sans-serif; font-size: 0.85em; font-weight: normal; float: right; color: #888; }
    .s-buy { color: #00ff00; } .s-sell { color: #ff0000; }
    
    .action-badge { padding: 3px 8px; border-radius: 4px; font-weight: bold; font-family: 'Orbitron', sans-serif; font-size: 0.75em; }
    .buy { background: rgba(0, 255, 0, 0.1); border: 1px solid #00ff00; color: #00ff00; }
    .sell { background: rgba(255, 0, 0, 0.1); border: 1px solid #ff0000; color: #ff4b4b; }
    .neutral { background: rgba(100, 100, 100, 0.1); border: 1px solid #888; color: #aaa; }
    
    /* ચેટ બોક્સ અને ટિકર */
    .ticker-wrap { width: 100%; overflow: hidden; background: rgba(10,10,10,0.8); border-bottom: 1px solid #d4af37; padding: 5px 0; margin-bottom: 15px; }
    .ticker { display: inline-block; white-space: nowrap; padding-right: 100%; animation: ticker 35s linear infinite; }
    @keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
    .ticker-item { display: inline-block; padding: 0 1.5rem; font-family: 'Orbitron', sans-serif; font-size: 0.9em; font-weight: bold; }
    .t-up { color: #00ff00; } .t-down { color: #ff4b4b; } .t-title { color: #d4af37; } .t-crypto { color: #f7931a; }
    
    .radar-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
    .stChatMessage { background: rgba(20,20,20,0.5) !important; border-left: 2px solid #d4af37 !important; border-radius: 8px; padding: 10px; margin-bottom: 8px; }
    .stChatMessage p { color: #eee !important; font-size: 0.95em; font-family: 'Roboto Mono', sans-serif; margin: 0; }
    .live-badge { text-align: center; padding: 8px; background: rgba(0, 255, 0, 0.05); border: 1px solid rgba(0,255,0,0.5); border-radius: 5px; color: #00ff00; font-family: 'Orbitron', sans-serif; font-size: 0.8em; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ૩. માર્કેટ એન્જિન 
# ==========================================
def get_terminal_data(ticker):
    try:
        ticker = ticker.strip().upper()
        if not ticker.endswith('.NS') and not ticker.startswith('^') and not ticker.endswith('-USD'): 
            ticker += '.NS'
            
        t = yf.Ticker(ticker)
        df = t.history(period="2d")
        if df.empty: return None
        
        last = df.iloc[-1]
        prev_close = df.iloc[-2]['Close'] if len(df) > 1 else last['Open']
        ema_data = t.history(period="1mo", interval="1d")
        ema20 = ema_data['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        if last['Close'] > ema20: act, cls = "BUY", "buy"
        elif last['Close'] < ema20: act, cls = "SELL", "sell"
        else: act, cls = "NEUTRAL", "neutral"
        
        trend_class = "t-up" if last['Close'] >= prev_close else "t-down"
        arrow = "▲" if last['Close'] >= prev_close else "▼"
        currency = "$" if "-USD" in ticker else "₹"
        
        return {
            "Symbol": ticker.replace(".NS", "").replace("-USD", ""),
            "Price": round(last['Close'], 2),
            "Signal": act, "Class": cls, "Trend_Class": trend_class, "Arrow": arrow, "Currency": currency
        }
    except: return None

# ==========================================
# ૪. ડેશબોર્ડ અને બ્રાન્ડિંગ લેઆઉટ
# ==========================================

with st.sidebar:
    # 🌟 ABNV LOGO SECTION
    # જો તમારે તમારી ઈમેજ (logo.png) વાપરવી હોય તો નીચેની 1 લીટીમાંથી # હટાવી દો અને તેની નીચેનો html કોડ કાઢી નાખો.
    # st.image("logo.png", use_container_width=True) 
    
    st.markdown("""
        <div class="abnv-logo">ABNV</div>
        <div class="abnv-sub">Trading Terminal</div>
    """, unsafe_allow_html=True)
    
    # 👑 FOUNDERS HIGHLIGHT
    st.markdown("""
        <div class="founders-badge">
            <p>Developed & Managed By</p>
            <h3>NILESH SHAH</h3>
            <h3>VASVI SENGUPTA</h3>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='live-badge'>🟢 TICK ENGINE <br><small>10 SEC SYNC | ZERO-FLICKER</small></div>", unsafe_allow_html=True)

left, right = st.columns([2, 1])

# 💡 10 સેકન્ડ લાઈવ રિફ્રેશ એન્જિન
@st.fragment(run_every=10)
def live_market_board():
    global live_context_data 
    live_context_data = []
    
    # --- SCROLLING TICKER ---
    nifty = get_terminal_data('^NSEI')
    banknifty = get_terminal_data('^NSEBANK')
    btc = get_terminal_data('BTC-USD')

    ticker_html = "<div class='ticker-wrap'><div class='ticker'>"
    if nifty: ticker_html += f"<div class='ticker-item'><span class='t-title'>NIFTY:</span> <span class='{nifty['Trend_Class']}'>₹{nifty['Price']} {nifty['Arrow']}</span></div>"
    if banknifty: ticker_html += f"<div class='ticker-item'><span class='t-title'>BANK NIFTY:</span> <span class='{banknifty['Trend_Class']}'>₹{banknifty['Price']} {banknifty['Arrow']}</span></div>"
    if btc: ticker_html += f"<div class='ticker-item'><span class='t-crypto'>BITCOIN:</span> <span class='{btc['Trend_Class']}'>${btc['Price']} {btc['Arrow']}</span></div>"
    ticker_html += "</div></div>"
    st.markdown(ticker_html, unsafe_allow_html=True)

    # --- રડાર ટેબલ ---
    fo_sectors = {
        "IT": ['INFY', 'TCS', 'WIPRO', 'HCLTECH', 'TECHM'],
        "BANKING": ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK'],
        "AUTO": ['TATAMOTORS', 'M&M', 'MARUTI', 'BAJAJ-AUTO', 'TVSMOTOR'],
        "ENERGY": ['RELIANCE', 'ONGC', 'NTPC', 'POWERGRID', 'TATAPOWER']
    }
    
    def build_table(sector_name, stocks, is_crypto=False):
        rows_html = ""
        buy_count, sell_count, total = 0, 0, 0
        for s in stocks:
            d = get_terminal_data(s)
            if d: 
                total += 1
                if d['Signal'] == 'BUY': buy_count += 1
                elif d['Signal'] == 'SELL': sell_count += 1
                live_context_data.append(f"{d['Symbol']}: {d['Price']} ({d['Signal']})")
                rows_html += f"<tr><td style='color:#ffffff; font-weight:bold;'>{d['Symbol']}</td><td>{d['Currency']}{d['Price']}</td><td><span class='action-badge {d['Class']}'>{d['Signal']}</span></td></tr>"
        
        summary_html = f"<span class='sector-summary'>(કુલ: {total}) | <span class='s-buy'>B: {buy_count}</span> | <span class='s-sell'>S: {sell_count}</span></span>"
        header_class = "crypto-header" if is_crypto else "sector-header"
        
        # 💎 અહીં ટેબલને Glass Card માં પેક કર્યું છે
        html = f"<div class='glass-card'><table class='f-o-table'><thead><tr><th colspan='3' class='{header_class}'>{sector_name} {summary_html}</th></tr></thead><tbody>"
        html += rows_html + "</tbody></table></div>"
        return html

    sectors = list(fo_sectors.items())
    half = len(sectors) // 2
    grid_html = "<div class='radar-grid'><div>"
    for name, stocks in sectors[:half]:
        grid_html += build_table(name, stocks)
    grid_html += "</div><div>"
    for name, stocks in sectors[half:]:
        grid_html += build_table(name, stocks)
    grid_html += "</div></div>"
    st.markdown(grid_html, unsafe_allow_html=True)
    
    # ક્રિપ્ટો ટેસ્ટ બેડ
    crypto_list = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
    st.markdown(build_table("HIGH VOLUME CRYPTO (24x7)", crypto_list, is_crypto=True), unsafe_allow_html=True)

with left:
    live_market_board()

# --- જમણી બાજુ: કમાન્ડ બોટ ---
with right:
    st.markdown("<h4 style='font-family: Orbitron; color: #d4af37; margin-bottom: 10px;'>🤖 ABNV COMMAND CORE</h4>", unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_box = st.container(height=650) 
    for m in st.session_state.messages[-10:]:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if pr := st.chat_input("ટાર્ગેટ પૂછો..."):
        st.session_state.messages.append({"role": "user", "content": pr})
        with chat_box.chat_message("user"): st.markdown(pr)
        
        with chat_box.chat_message("assistant"):
            try:
                memory_string = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-4:]])
                market_status = " | ".join(live_context_data) if 'live_context_data' in globals() else "માર્કેટ લોડ થઈ રહ્યું છે..."
                
                ai_prompt = f"""
                માલિક: નિલેશ શાહ અને વાસવી સેનગુપ્તા. 
                કંપની: ABNV. 
                માર્કેટ ડેટા: {market_status}
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