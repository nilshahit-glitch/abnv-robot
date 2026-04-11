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

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = st.secrets.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

st.set_page_config(page_title="ABNV TERMINAL | NILESH SHAH", layout="wide")

# ==========================================
# ૨. એડવાન્સ UI (Clear Text & Dark Mode)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; }
    [data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #d4af37; }
    .index-card { flex: 1; background: #111; border: 1px solid #d4af37; padding: 15px; border-radius: 10px; text-align: center; }
    .stock-row { background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 12px; margin-bottom: 8px; border-left: 5px solid #d4af37; display: flex; justify-content: space-between; align-items: center; }
    .stChatMessage { background: #151515 !important; border-left: 3px solid #d4af37 !important; border-radius: 8px; padding: 10px; margin-bottom: 10px; }
    .stChatMessage p { color: #ffffff !important; font-size: 1.1em; font-family: 'Roboto Mono', sans-serif; line-height: 1.6; }
    .action-badge { padding: 4px 12px; border-radius: 4px; font-weight: bold; font-family: 'Orbitron', sans-serif; font-size: 0.8em; }
    .buy { background-color: #00ff00; color: #000; }
    .sell { background-color: #ff0000; color: #fff; }
    .neutral { background-color: #555; color: #fff; }
    h1, h2, h3, h4 { font-family: 'Orbitron', sans-serif; color: #d4af37 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ૩. પાવરફુલ માર્કેટ એન્જિન
# ==========================================

def get_trading_signal(ticker):
    try:
        ticker = ticker.strip().upper()
        if not ticker.endswith('.NS') and not ticker.startswith('^'): ticker += '.NS'
        t = yf.Ticker(ticker)
        df = t.history(period="1mo", interval="1d") 
        if df.empty: return None
        
        last_p = df['Close'].iloc[-1]
        ema20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        ema9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        
        if last_p > ema20 and last_p > ema9: act, cls = "BUY", "buy"
        elif last_p < ema20 and last_p < ema9: act, cls = "SELL", "sell"
        else: act, cls = "NEUTRAL", "neutral"
        
        return {"symbol": ticker.replace(".NS", ""), "price": round(last_p, 2), "action": act, "class": cls}
    except: return None

# ==========================================
# ૪. ડેશબોર્ડ લેઆઉટ
# ==========================================

with st.sidebar:
    st.title("NILESH SHAH")
    st.write("🤖 v15.8 [Silent Broker]")
    st.markdown("---")
    if st.button("RESCAN SYSTEM"): st.rerun()

st.markdown('<h2 style="text-align:center;">📊 TRADING TERMINAL</h2>', unsafe_allow_html=True)

nifty = get_trading_signal('^NSEI')
banknifty = get_trading_signal('^NSEBANK')
live_context_data = []

c1, c2 = st.columns(2)
if nifty: 
    st.markdown(f'<div class="index-card">NIFTY 50<h3>₹{nifty["price"]}</h3><span class="action-badge {nifty["class"]}">{nifty["action"]}</span></div>', unsafe_allow_html=True)
    live_context_data.append(f"NIFTY: ₹{nifty['price']} ({nifty['action']})")
if banknifty: 
    st.markdown(f'<div class="index-card">BANK NIFTY<h3>₹{banknifty["price"]}</h3><span class="action-badge {banknifty["class"]}">{banknifty["action"]}</span></div>', unsafe_allow_html=True)
    live_context_data.append(f"BANKNIFTY: ₹{banknifty['price']} ({banknifty['action']})")

st.markdown("<br>", unsafe_allow_html=True)

left, right = st.columns([1.2, 1])

with left:
    st.markdown("<h4>📡 F&O RADAR</h4>", unsafe_allow_html=True)
    for s in ['RELIANCE', 'INFY', 'TCS', 'DIXON', 'ZOMATO']:
        d = get_trading_signal(s)
        if d:
            st.markdown(f'<div class="stock-row"><b style="color:#d4af37;">{d["symbol"]}</b><span style="color:#fff;">₹{d["price"]}</span><span class="action-badge {d["class"]}">{d["action"]}</span></div>', unsafe_allow_html=True)
            live_context_data.append(f"{d['symbol']}: ભાવ ₹{d['price']} સિગ્નલ {d['action']}")

with right:
    st.markdown("<h4>🤖 COMMAND CORE</h4>", unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_box = st.container(height=400)
    for m in st.session_state.messages[-10:]: # છેલ્લી 10 ચેટ જ બતાવશે
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if pr := st.chat_input("ટાર્ગેટ કે લેવલ પૂછો..."):
        st.session_state.messages.append({"role": "user", "content": pr})
        with chat_box.chat_message("user"): st.markdown(pr)
        
        with chat_box.chat_message("assistant"):
            try:
                # મેમરી સેટઅપ
                memory_string = ""
                for msg in st.session_state.messages[-4:]:
                    memory_string += f"{msg['role']}: {msg['content']}\n"
                
                market_status = " | ".join(live_context_data)
                
                # દેશી બ્રોકર સ્ક્રિપ્ટ
                ai_prompt = f"""
                માલિક: નિલેશ શાહ. 
                માર્કેટ ડેટા: {market_status}
                
                તમારે નીચે આપેલા ઉદાહરણ પ્રમાણે જ એકદમ દેશી, ટૂંકો અને સીધો જવાબ આપવાનો છે. 
                'આશરે', 'વિશ્લેષણ', 'સંભાવના', 'રિપોર્ટ' જેવા ચોપડીના શબ્દો બિલકુલ ન વાપરતા. માત્ર 1 જ લાઈનમાં જવાબ આપવો.
                
                ઉદાહરણ 1:
                User: infosys target
                Assistant: નિલેશભાઈ, ઇન્ફોસિસ અત્યારે 1292 રૂપિયા છે, માર્કેટમાં તેજી છે, 1310 નો ટાર્ગેટ રાખો.
                
                ઉદાહરણ 2:
                User: tcs levay?
                Assistant: ના નિલેશભાઈ, ટીસીએસ માં અત્યારે મંદી દેખાય છે, 2524 રૂપિયા ભાવ છે, અત્યારે રહેવા દો.
                
                ઉદાહરણ 3:
                User: reliance no bhav
                Assistant: રિલાયન્સ અત્યારે 1350 રૂપિયા છે નિલેશભાઈ, કોઈ મુવમેન્ટ નથી.
                
                હવે આ સવાલનો જવાબ આપો:
                વાતચીતનો ઇતિહાસ: {memory_string}
                User: {pr}
                Assistant: 
                """
                
                res = client.models.generate_content(
                    model="gemini-3.1-flash-lite-preview",
                    contents=ai_prompt
                )
                
                reply = res.text.replace("Assistant:", "").strip() if (res and res.text) else "સર્વરમાં લોચો છે."
                st.markdown(reply)
                
                # 💡 વૉઇસ કાઢી નાખ્યો છે, સીધો જ રિપ્લે સેવ થશે
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
            except Exception as e:
                st.error(f"Engine Error: {e}")