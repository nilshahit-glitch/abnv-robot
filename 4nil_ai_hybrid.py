import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import os
import re
import json
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
# ૨. એડવાન્સ UI 
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
# ૩. પાવરફુલ ફંક્શન્સ 
# ==========================================

def get_trading_signal(ticker):
    try:
        ticker = ticker.strip().upper()
        if not ticker.endswith('.NS') and not ticker.startswith('^'): ticker += '.NS'
        t = yf.Ticker(ticker)
        df = t.history(period="5d", interval="1h")
        if df.empty: return None
        last_p = df['Close'].iloc[-1]
        ema20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        ema9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        if last_p > ema20 and last_p > ema9: act, cls = "BUY", "buy"
        elif last_p < ema20 and last_p < ema9: act, cls = "SELL", "sell"
        else: act, cls = "NEUTRAL", "neutral"
        return {"symbol": ticker.replace(".NS", ""), "price": round(last_p, 2), "action": act, "class": cls}
    except: return None

def speak_premium(text):
    """
    પ્રીમિયમ બ્રાઉઝર બેઝ્ડ વૉઇસ એન્જિન (No gTTS)
    આ સીધો જ તમારા MacBook/Mobile નો નેચરલ અવાજ વાપરશે.
    """
    clean_text = re.sub(r'[^\w\s\.]', '', text).replace('\n', ' ')
    if not clean_text: return
    
    # JavaScript Speech Synthesis API
    js_code = f"""
    <script>
        const textToSpeak = "{clean_text}";
        const msg = new SpeechSynthesisUtterance(textToSpeak);
        msg.lang = 'gu-IN'; // ગુજરાતી ભાષા
        msg.rate = 0.95; // બોલવાની સ્પીડ થોડી નોર્મલ
        msg.pitch = 1.0; 
        window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0, width=0)

# ==========================================
# ૪. ડેશબોર્ડ લેઆઉટ
# ==========================================

with st.sidebar:
    st.title("NILESH SHAH")
    st.write("🤖 v15.3 [Premium Voice]")
    st.markdown("---")
    if st.button("RESCAN SYSTEM"): st.rerun()

st.markdown('<h2 style="text-align:center;">📊 TRADING TERMINAL</h2>', unsafe_allow_html=True)
nifty = get_trading_signal('^NSEI')
banknifty = get_trading_signal('^NSEBANK')

c1, c2 = st.columns(2)
with c1:
    if nifty: st.markdown(f'<div class="index-card">NIFTY 50<h3>₹{nifty["price"]}</h3><span class="action-badge {nifty["class"]}">{nifty["action"]}</span></div>', unsafe_allow_html=True)
with c2:
    if banknifty: st.markdown(f'<div class="index-card">BANK NIFTY<h3>₹{banknifty["price"]}</h3><span class="action-badge {banknifty["class"]}">{banknifty["action"]}</span></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

left, right = st.columns([1.2, 1])

with left:
    st.markdown("<h4>📡 F&O RADAR</h4>", unsafe_allow_html=True)
    for s in ['RELIANCE', 'INFY', 'TCS', 'DIXON', 'ZOMATO']:
        d = get_trading_signal(s)
        if d:
            st.markdown(f'<div class="stock-row"><b style="color:#d4af37;">{d["symbol"]}</b><span style="color:#fff;">₹{d["price"]}</span><span class="action-badge {d["class"]}">{d["action"]}</span></div>', unsafe_allow_html=True)

with right:
    st.markdown("<h4>🤖 COMMAND CORE</h4>", unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_box = st.container(height=400)
    for m in st.session_state.messages:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if pr := st.chat_input("સવાલ પૂછો..."):
        st.session_state.messages.append({"role": "user", "content": pr})
        with chat_box.chat_message("user"): st.markdown(pr)
        
        with chat_box.chat_message("assistant"):
            try:
                ai_prompt = f"""
                User: {pr}. 
                સૂચના: એકદમ સાદી ગુજરાતી ભાષા વાપરો. જાણે કોઈ અમદાવાદી મિત્ર વાત કરતો હોય.
                જવાબ માત્ર ૧ કે ૨ લાઈનનો જ હોવો જોઈએ. માલિક: નિલેશ શાહ.
                """
                
                res = client.models.generate_content(
                    model="gemini-3.1-flash-lite-preview",
                    contents=ai_prompt
                )
                
                reply = res.text if (res and res.text) else "સર્વર બીઝી છે."
                st.markdown(reply)
                
                # અવાજને સ્મૂથ કરવા ચિહ્નો કાઢી નાખ્યા
                voice_text = reply.replace("₹", "રૂપિયા ").replace("%", "ટકા ").replace("-", " માઇનસ ")
                speak_premium(voice_text)
                
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
            except Exception as e:
                st.error(f"Engine Error: {e}")