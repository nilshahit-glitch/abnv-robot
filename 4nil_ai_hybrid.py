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
# ૨. અલ્ટ્રા-કોમ્પેક્ટ CSS Grid & Styling
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@400;700&display=swap');
    
    .stApp { background-color: #030303; }
    [data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #d4af37; }
    
    .ticker-wrap { width: 100%; overflow: hidden; background-color: #0a0a0a; border-bottom: 1px solid #d4af37; padding: 2px 0; margin-bottom: 5px; }
    .ticker { display: inline-block; white-space: nowrap; padding-right: 100%; animation: ticker 35s linear infinite; }
    @keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
    .ticker-item { display: inline-block; padding: 0 1.5rem; font-family: 'Orbitron', sans-serif; font-size: 0.9em; font-weight: bold; }
    .t-up { color: #00ff00; } .t-down { color: #ff4b4b; } .t-title { color: #d4af37; } .t-crypto { color: #f7931a; }
    
    .radar-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    
    .f-o-table { width: 100%; border-collapse: collapse; color: white; font-family: 'Roboto Mono', sans-serif; font-size: 0.8em; background: #0a0a0a; border: 1px solid #222; }
    .f-o-table th { background: #111; color: #d4af37; padding: 4px; text-align: left; border-bottom: 1px solid #d4af37; font-family: 'Orbitron', sans-serif; font-size: 0.85em; }
    .f-o-table td { padding: 2px 4px; border-bottom: 1px solid #1a1a1a; transition: background-color 0.3s; } /* 💡 સ્મૂથ ટ્રાન્ઝિશન માટે */
    
    .sector-header { background: #1a1a1a !important; color: #d4af37 !important; font-weight: bold; font-family: 'Orbitron', sans-serif; text-align: left !important; font-size: 0.85em; border-left: 2px solid #d4af37; padding: 4px 8px !important; }
    .crypto-header { background: #1a1a1a !important; color: #f7931a !important; font-weight: bold; font-family: 'Orbitron', sans-serif; text-align: left !important; font-size: 0.85em; border-left: 2px solid #f7931a; padding: 4px 8px !important; }
    
    .sector-summary { font-family: 'Roboto Mono', sans-serif; font-size: 0.9em; font-weight: normal; float: right; color: #aaa; }
    .s-buy { color: #00ff00; font-weight: bold; }
    .s-sell { color: #ff0000; font-weight: bold; }
    
    .stChatMessage { background: #111 !important; border-left: 2px solid #d4af37 !important; border-radius: 5px; padding: 5px 8px; margin-bottom: 5px; }
    .stChatMessage p { color: #ddd !important; font-size: 0.9em; font-family: 'Roboto Mono', sans-serif; margin: 0; }
    
    .action-badge { padding: 1px 4px; border-radius: 2px; font-weight: bold; font-family: 'Orbitron', sans-serif; font-size: 0.7em; }
    .buy { background-color: #00ff00; color: #000; }
    .sell { background-color: #ff0000; color: #fff; }
    .neutral { background-color: #555; color: #fff; }
    
    h1, h2, h3, h4 { font-family: 'Orbitron', sans-serif; color: #d4af37 !important; margin-bottom: 5px; padding: 0; }
    .live-badge { text-align: center; padding: 10px; background-color: rgba(0, 255, 0, 0.1); border: 1px solid #00ff00; border-radius: 5px; color: #00ff00; font-weight: bold; font-family: 'Orbitron', sans-serif; margin-top: 20px; box-shadow: 0 0 10px rgba(0, 255, 0, 0.2); animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ૩. માર્કેટ એન્જિન (ફાસ્ટ કેશલેસ)
# ==========================================
# 💡 કેશ કાઢી નાખ્યો જેથી દર 3 સેકન્ડે પ્યોર લાઈવ ડેટા આવે
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
            "Signal": act,
            "Class": cls,
            "Trend_Class": trend_class,
            "Arrow": arrow,
            "Currency": currency
        }
    except: return None

# ==========================================
# ૪. ડેશબોર્ડ લેઆઉટ
# ==========================================

with st.sidebar:
    st.title("NILESH SHAH")
    st.write("🤖 v16.9 [Smooth Live]")
    st.markdown("---")
    st.markdown("<div class='live-badge'>🟢 TICK ENGINE <br><small>3 SEC SYNC</small></div>", unsafe_allow_html=True)

left, right = st.columns([1.8, 1])

# 💡 ધ મેજિક: આ આખું સેક્શન દર 3 સેકન્ડે ચૂપચાપ રિફ્રેશ થશે (પેજ હલ્યા વગર)
@st.fragment(run_every=3)
def live_market_board():
    global live_context_data # AI માટે ગ્લોબલ ડેટા
    live_context_data = []
    
    # --- SCROLLING TICKER ---
    nifty = get_terminal_data('^NSEI')
    banknifty = get_terminal_data('^NSEBANK')
    btc = get_terminal_data('BTC-USD')

    ticker_html = "<div class='ticker-wrap'><div class='ticker'>"
    if nifty: ticker_html += f"<div class='ticker-item'><span class='t-title'>NIFTY:</span> <span class='{nifty['Trend_Class']}'>₹{nifty['Price']} {nifty['Arrow']}</span></div>"
    if banknifty: ticker_html += f"<div class='ticker-item'><span class='t-title'>BANK NIFTY:</span> <span class='{banknifty['Trend_Class']}'>₹{banknifty['Price']} {banknifty['Arrow']}</span></div>"
    if btc: ticker_html += f"<div class='ticker-item'><span class='t-crypto'>BITCOIN (TEST):</span> <span class='{btc['Trend_Class']}'>${btc['Price']} {btc['Arrow']}</span></div>"
    ticker_html += "</div></div>"
    st.markdown(ticker_html, unsafe_allow_html=True)

    # --- રડાર ટેબલ ---
    fo_sectors = {
        "IT": ['INFY', 'TCS', 'WIPRO', 'HCLTECH', 'TECHM'],
        "BANKING": ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK'],
        "AUTO": ['TATAMOTORS', 'M&M', 'MARUTI', 'BAJAJ-AUTO', 'TVSMOTOR'],
        "ENERGY": ['RELIANCE', 'ONGC', 'NTPC', 'POWERGRID', 'TATAPOWER'],
        "FMCG": ['ITC', 'HUL', 'BRITANNIA', 'TATACONSUM', 'DABUR'],
        "METALS": ['TATASTEEL', 'HINDALCO', 'JSWSTEEL', 'VEDL', 'NMDC']
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
        
        summary_html = f"<span class='sector-summary'>(કુલ: {total}) | <span class='s-buy'>BUY: {buy_count}</span> | <span class='s-sell'>SELL: {sell_count}</span></span>"
        header_class = "crypto-header" if is_crypto else "sector-header"
        header_html = f"<tr><td colspan='3' class='{header_class}'>{sector_name} {summary_html}</td></tr>"
        
        html = "<table class='f-o-table'><thead><tr><th>SYMBOL</th><th>PRICE</th><th>SIGNAL</th></tr></thead><tbody>"
        html += header_html + rows_html + "</tbody></table>"
        return html

    sectors = list(fo_sectors.items())
    half = len(sectors) // 2
    grid_html = "<div class='radar-grid'><div>"
    for name, stocks in sectors[:half]:
        grid_html += build_table(name, stocks) + "<br>"
    grid_html += "</div><div>"
    for name, stocks in sectors[half:]:
        grid_html += build_table(name, stocks) + "<br>"
    grid_html += "</div></div>"
    st.markdown(grid_html, unsafe_allow_html=True)
    
    # ક્રિપ્ટો ટેસ્ટ બેડ
    crypto_list = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
    st.markdown(build_table("HIGH VOLUME CRYPTO (24x7)", crypto_list, is_crypto=True), unsafe_allow_html=True)

with left:
    # ફંક્શન કોલ કરીશું એટલે તે દર 3 સેકન્ડે જાતે જ ચાલ્યા કરશે
    live_market_board()

# --- જમણી બાજુ: કમાન્ડ બોટ ---
with right:
    st.markdown("<h4>🤖 COMMAND CORE</h4>", unsafe_allow_html=True)
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