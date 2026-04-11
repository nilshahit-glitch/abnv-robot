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
    
    .f-o-table { width: 100%; border-collapse: collapse; color: white; font-family: 'Roboto Mono', sans-serif; }
    .f-o-table th { background: #111; color: #d4af37; padding: 12px; text-align: left; border-bottom: 2px solid #d4af37; font-family: 'Orbitron', sans-serif; }
    .f-o-table td { padding: 12px; border-bottom: 1px solid rgba(212, 175, 55, 0.1); }
    
    .stChatMessage { background: #151515 !important; border-left: 3px solid #d4af37 !important; border-radius: 8px; padding: 10px; margin-bottom: 10px; }
    .stChatMessage p { color: #ffffff !important; font-size: 1.1em; font-family: 'Roboto Mono', sans-serif; line-height: 1.6; }
    
    .action-badge { padding: 5px 10px; border-radius: 4px; font-weight: bold; font-family: 'Orbitron', sans-serif; font-size: 0.8em; }
    .buy { background-color: #00ff00; color: #000; box-shadow: 0 0 10px #00ff00; }
    .sell { background-color: #ff0000; color: #fff; box-shadow: 0 0 10px #ff0000; }
    .neutral { background-color: #555; color: #fff; }
    
    h1, h2, h3, h4 { font-family: 'Orbitron', sans-serif; color: #d4af37 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ૩. પાવરફુલ માર્કેટ એન્જિન
# ==========================================

def get_terminal_data(ticker):
    try:
        ticker = ticker.strip().upper()
        if not ticker.endswith('.NS') and not ticker.startswith('^'): ticker += '.NS'
        t = yf.Ticker(ticker)
        df = t.history(period="2d")
        if df.empty: return None
        
        last = df.iloc[-1]
        
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
    st.write("🤖 v16.1 [UI Fixed]")
    st.markdown("---")
    if st.button("RESCAN TERMINAL"): st.rerun()

st.title("🔱 ABNV MASTER TERMINAL")

nifty = get_terminal_data('^NSEI')
banknifty = get_terminal_data('^NSEBANK')
c1, c2 = st.columns(2)
if nifty: c1.metric("NIFTY 50", f"₹{nifty['Price']}", nifty['Signal'])
if banknifty: c2.metric("BANK NIFTY", f"₹{banknifty['Price']}", banknifty['Signal'])

st.markdown("---")

left, right = st.columns([1.5, 1])

# --- ડાબી બાજુ: લાઈવ ટેબલ ---
with left:
    st.subheader("📡 F&O LIVE RADAR")
    watchlist = ['RELIANCE', 'INFY', 'TCS', 'HDFCBANK', 'ZOMATO', 'DIXON', 'TATAMOTORS', 'ICICIBANK']
    all_data = []
    live_context_data = []

    for s in watchlist:
        data = get_terminal_data(s)
        if data: 
            all_data.append(data)
            live_context_data.append(f"{data['Symbol']}: {data['Price']} ({data['Signal']})")

    # 💡 ફિક્સ: સળંગ લાઈનમાં HTML જેથી Streamlit ગોથા ના ખાય
    table_html = "<table class='f-o-table'><thead><tr><th>SYMBOL</th><th>PRICE</th><th>OPEN</th><th>HIGH</th><th>LOW</th><th>SIGNAL</th></tr></thead><tbody>"
    for d in all_data:
        table_html += f"<tr><td style='color:#d4af37; font-weight:bold;'>{d['Symbol']}</td><td>₹{d['Price']}</td><td style='color:#888;'>{d['Open']}</td><td style='color:#00ff00;'>{d['High']}</td><td style='color:#ff4b4b;'>{d['Low']}</td><td><span class='action-badge {d['Class']}'>{d['Signal']}</span></td></tr>"
    table_html += "</tbody></table>"

    st.markdown(table_html, unsafe_allow_html=True)

# --- જમણી બાજુ: દેશી બ્રોકર AI ---
with right:
    st.subheader("🤖 COMMAND CORE")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_box = st.container(height=500)
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
                
                તમારે નીચે આપેલા ઉદાહરણ પ્રમાણે જ એકદમ દેશી, ટૂંકો અને સીધો જવાબ આપવાનો છે. 
                'આશરે', 'વિશ્લેષણ', 'સંભાવના', 'રિપોર્ટ' જેવા ચોપડીના શબ્દો બિલકુલ ન વાપરતા. માત્ર 1 જ લાઈનમાં જવાબ આપવો.
                
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