import streamlit as st
import yfinance as yf
import pandas as pd
import os
import re
import json
import random
import threading
import subprocess
import time
from gtts import gTTS
from dotenv import load_dotenv
from google import genai

# ==========================================
# ૧. સિસ્ટમ સેટઅપ
# ==========================================
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="ABNV TERMINAL | NILESH SHAH", layout="wide")

# ==========================================
# ૨. એડવાન્સ ટર્મિનલ UI (Focus Mode)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@400;700&display=swap');
    
    .stApp { background-color: #050505; }
    
    /* સાઈડબારમાં એડમિન વિગતો */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #d4af37;
    }

    /* ઇન્ડેક્સ કાર્ડ્સ (Top bar) */
    .index-container {
        display: flex;
        justify-content: space-around;
        gap: 20px;
        margin-bottom: 25px;
    }
    
    .index-card {
        flex: 1;
        background: linear-gradient(145deg, #111, #050505);
        border: 1px solid #d4af37;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.1);
    }

    /* સ્ટોક ટેબલ/ગ્રીડ */
    .stock-row {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #d4af37;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* એક્શન બેજ (BUY/SELL) */
    .action-badge {
        padding: 5px 15px;
        border-radius: 5px;
        font-weight: bold;
        text-transform: uppercase;
        font-family: 'Orbitron', sans-serif;
    }
    
    .buy { background-color: #00ff00; color: #000; box-shadow: 0 0 10px #00ff00; }
    .sell { background-color: #ff0000; color: #fff; box-shadow: 0 0 10px #ff0000; }
    .neutral { background-color: #555; color: #fff; }

    h1, h2, h3, h4 { font-family: 'Orbitron', sans-serif; color: #d4af37 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ૩. એનાલિસિસ એન્જિન (Buy/Sell Logic)
# ==========================================

def get_trading_signal(ticker):
    try:
        ticker = ticker.strip().upper()
        if not ticker.endswith('.NS') and not ticker.startswith('^'): ticker += '.NS'
        t = yf.Ticker(ticker)
        df = t.history(period="5d", interval="1h") # કલાકનો ડેટા ચોકસાઈ માટે
        
        if df.empty: return None
        
        last_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        ema20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        ema9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        
        # BUY/SELL LOGIC
        if last_price > ema20 and last_price > ema9:
            action = "BUY"
            color_class = "buy"
        elif last_price < ema20 and last_price < ema9:
            action = "SELL"
            color_class = "sell"
        else:
            action = "NEUTRAL"
            color_class = "neutral"
            
        return {
            "symbol": ticker.replace(".NS", ""),
            "price": round(last_price, 2),
            "change": round(last_price - prev_price, 2),
            "action": action,
            "class": color_class
        }
    except: return None

def speak_robot(text):
    def run():
        try:
            clean_text = re.sub(r'[^\w\s\.]', '', text)
            tts = gTTS(text=clean_text, lang='gu')
            path = "voice.mp3"
            tts.save(path)
            subprocess.run(["afplay", "-q", path])
            os.remove(path)
        except: pass
    threading.Thread(target=run, daemon=True).start()

# ==========================================
# ૪. Nilesh Shah Dashboard UI
# ==========================================

# --- SIDEBAR (Version & Owner Info) ---
with st.sidebar:
    st.image("https://img.icons8.com/nolan/64/robot-2.1.png")
    st.title("Admin")
    st.info(f"👤 **Nilesh Shah**")
    st.info(f"🤖 **v14.5 Stable**")
    st.markdown("---")
    if st.button("RESCAN ALL"): st.rerun()

# --- TOP BAR (Market Indices Focus) ---
st.markdown('<h2 style="text-align:center;">📊 MARKET INDEX OVERVIEW</h2>', unsafe_allow_html=True)
nifty = get_trading_signal('^NSEI')
banknifty = get_trading_signal('^NSEBANK')
finnifty = get_trading_signal('^CNXFIN')

col1, col2, col3 = st.columns(3)
with col1:
    if nifty:
        st.markdown(f"""<div class="index-card">
            <small>NIFTY 50</small><h3>₹{nifty['price']}</h3>
            <span class="action-badge {nifty['class']}">{nifty['action']}</span>
        </div>""", unsafe_allow_html=True)
with col2:
    if banknifty:
        st.markdown(f"""<div class="index-card">
            <small>BANK NIFTY</small><h3>₹{banknifty['price']}</h3>
            <span class="action-badge {banknifty['class']}">{banknifty['action']}</span>
        </div>""", unsafe_allow_html=True)
with col3:
    if finnifty:
        st.markdown(f"""<div class="index-card">
            <small>FIN NIFTY</small><h3>₹{finnifty['price']}</h3>
            <span class="action-badge {finnifty['class']}">{finnifty['action']}</span>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- MAIN SECTION (F&O Stock Focus) ---
left, right = st.columns([1.5, 1])

with left:
    st.markdown("<h4>📡 F&O RADAR SCAN</h4>", unsafe_allow_html=True)
    watchlist = ['RELIANCE', 'INFY', 'TCS', 'DIXON', 'ZOMATO', 'TATAMOTORS', 'HDFCBANK', 'ICICIBANK']
    
    for s in watchlist:
        data = get_trading_signal(s)
        if data:
            st.markdown(f"""
                <div class="stock-row">
                    <div style="flex:2;">
                        <b style="color:#d4af37; font-size:1.2em;">{data['symbol']}</b><br>
                        <span style="color:#888; font-size:0.8em;">F&O Segment</span>
                    </div>
                    <div style="flex:2; text-align:center;">
                        <span style="color:#fff; font-size:1.4em; font-family:'Roboto Mono';">₹{data['price']}</span>
                    </div>
                    <div style="flex:1; text-align:right;">
                        <span class="action-badge {data['class']}">{data['action']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

with right:
    st.markdown("<h4>🤖 COMMAND CORE</h4>", unsafe_allow_html=True)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ચેટ બોક્સ
    chat_container = st.container(height=500)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Ask about any Stock/Index..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)

        # AI Response
        with chat_container:
            with st.chat_message("assistant"):
                try:
                    response = client.models.generate_content(
                        model="gemini-1.5-flash", 
                        contents=f"User: {prompt}. Answer in Gujarati. Context: Current Market Indices Nifty:{nifty['price']}, BankNifty:{banknifty['price']}. Focus on levels. Owner is Nilesh Shah."
                    )
                    reply = response.text
                    st.markdown(reply)
                    speak_robot(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"Core Offline: {e}")