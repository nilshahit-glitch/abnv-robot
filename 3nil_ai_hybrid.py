import os
import re
import json
import random
import threading
import datetime
import requests
import subprocess
import time
import queue
import logging
import warnings

# 💡 સાયલન્સર: yfinance નો કચરો રોકવા
warnings.filterwarnings("ignore")
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

import numpy as np
import pandas as pd
from dotenv import load_dotenv
import yfinance as yf
import speech_recognition as sr
from gtts import gTTS
import google.generativeai as genai

# ==========================================
# ૧. API Keys અને લેટેસ્ટ Gemini 3.1 એન્જિન
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(env_path)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
chat_model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

# ==========================================
# ૨. ઓડિયો ક્યુ અને માસ્ટર Echo Lock 
# ==========================================
audio_queue = queue.Queue()
is_speaking = False  

def speak_worker():
    global is_speaking
    while True:
        text = audio_queue.get()
        if text is None: break
        
        clean_text = text.replace(".NS", "").replace("^NSEI", "નિફ્ટી").replace("^NSEBANK", "બેંક નિફ્ટી").replace("^CNXFIN", "ફિન નિફ્ટી")
        clean_text = re.sub(r'[*_#@\[\]()~`"“”-]', '', clean_text)
        
        if len(clean_text.strip()) > 1:
            try:
                audio_file = os.path.join(current_dir, f"nil_voice_{random.randint(1,1000)}.mp3")
                tts = gTTS(text=clean_text, lang='gu')
                tts.save(audio_file)
                
                is_speaking = True 
                subprocess.run(["afplay", audio_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(0.3) 
                
                if os.path.exists(audio_file): os.remove(audio_file)
            except: pass
            
        if audio_queue.empty(): is_speaking = False 
        audio_queue.task_done()

threading.Thread(target=speak_worker, daemon=True).start()

def speak_instant(text):
    global is_speaking
    is_speaking = True 
    audio_queue.put(text)

def listen():
    global is_speaking
    audio_queue.join() 
    time.sleep(0.5) 
    
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 માઈક ચાલુ છે... નિલેશ, બોલો...")
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        try:
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=25) 
            text = recognizer.recognize_google(audio, language="gu-IN")
            text = text.replace("નીપટી", "નિફ્ટી").replace("પિક્ચર", "ફિફ્ટી").replace("સેન્ટર", "સેક્ટર")
            print(f"તમે બોલ્યા: {text}")
            return text
        except: 
            print("માફ કરજો, અવાજ સંભળાયો નહિ.")
            return ""

# ==========================================
# 📡 ૩. ધ પ્યોર F&O રાડાર 
# ==========================================
scanned_stocks = {"buy": [], "sell": []}

MASTER_FNO_LIST = [
    '^NSEI', '^NSEBANK', '^CNXFIN', 
    'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS', 'INDUSINDBK.NS', 'PNB.NS', 'BANKBARODA.NS', 'FEDERALBNK.NS', 'IDFCFIRSTB.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'CHOLAFIN.NS', 'MUTHOOTFIN.NS', 'PFC.NS', 'RECLTD.NS', 'HDFCAMC.NS', 'ICICIGI.NS', 'SBILIFE.NS', 'HDFCLIFE.NS',
    'INFY.NS', 'TCS.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS', 'LTIM.NS', 'COFORGE.NS', 'PERSISTENT.NS', 'MPHASIS.NS',
    'TATAMOTORS.NS', 'MARUTI.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'HEROMOTOCO.NS', 'TVSMOTOR.NS', 'EICHERMOT.NS', 'ASHOKLEY.NS', 'BOSCHLTD.NS', 'MRF.NS', 'APOLLOTYRE.NS',
    'RELIANCE.NS', 'ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'COALINDIA.NS', 'GAIL.NS', 'BPCL.NS', 'IOC.NS', 'HINDPETRO.NS', 'TATAPOWER.NS',
    'ADANIENT.NS', 'ADANIPORTS.NS', 'AMBUJACEM.NS',
    'TATASTEEL.NS', 'JSWSTEEL.NS', 'HINDALCO.NS', 'VEDL.NS', 'JINDALSTEL.NS', 'NMDC.NS', 'SAIL.NS', 'NATIONALUM.NS',
    'ITC.NS', 'HINDUNILVR.NS', 'BRITANNIA.NS', 'TATACONSUM.NS', 'NESTLEIND.NS', 'DABUR.NS', 'GODREJCP.NS', 'MARICO.NS', 'COLPAL.NS',
    'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS', 'APOLLOHOSP.NS', 'TORNTPHARM.NS', 'LUPIN.NS', 'AUROPHARMA.NS', 'BIOCON.NS', 'GLENMARK.NS',
    'ULTRACEMCO.NS', 'GRASIM.NS', 'SHREECEM.NS', 'LT.NS', 'DLF.NS', 'GODREJPROP.NS',
    'ZOMATO.NS', 'INDIGO.NS', 'TITAN.NS', 'TRENT.NS', 'ASIANPAINT.NS', 'HAVELLS.NS', 'PIDILITIND.NS', 'SIEMENS.NS', 'BHEL.NS', 'HAL.NS', 'BEL.NS', 'IRCTC.NS', 'DIXON.NS'
]

def background_market_radar():
    print("\n[સિસ્ટમ 📡]: અપડેટેડ F&O સ્કેનર ઓનલાઈન છે (સ્કેનિંગ ચાલુ...)")
    while True:
        try:
            buy_list, sell_list = [], []
            data = yf.download(MASTER_FNO_LIST, period="5d", interval="15m", group_by='ticker', progress=False, show_errors=False)
            
            for ticker in MASTER_FNO_LIST:
                if ticker in data and not data[ticker].empty:
                    df = data[ticker].ffill().dropna()
                    if len(df) < 20: continue
                    current_price = df['Close'].iloc[-1]
                    ema_20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
                    ema_9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
                    
                    clean_name = ticker.replace(".NS", "").replace("^NSEI", "નિફ્ટી").replace("^NSEBANK", "બેંક નિફ્ટી").replace("^CNXFIN", "ફિન નિફ્ટી")
                    
                    if current_price > ema_20 and current_price > ema_9: buy_list.append(clean_name)
                    elif current_price < ema_20 and current_price < ema_9: sell_list.append(clean_name)
            
            scanned_stocks["buy"] = buy_list
            scanned_stocks["sell"] = sell_list
            time.sleep(900) 
        except Exception as e: 
            time.sleep(60) 

threading.Thread(target=background_market_radar, daemon=True).start()

# ==========================================
# 📊 ૪. સેક્ટર એનાલિસિસ 
# ==========================================
def run_sector_analysis():
    print("\n[સિસ્ટમ 📊]: સેક્ટરનો ડેટા ચેક કરી રહ્યો છું...")
    try:
        sectors = {'બેંકિંગ': '^NSEBANK', 'આઈટી': '^CNXIT', 'ઓટો': '^CNXAUTO', 'ફાર્મા': '^CNXPHARMA', 'એફએમસીજી': '^CNXFMCG', 'મેટલ': '^CNXMETAL', 'ફાઇનાન્સ': '^CNXFIN'}
        tickers = list(sectors.values())
        data = yf.download(tickers, period="5d", group_by='ticker', progress=False, show_errors=False)
        results = []
        for name, ticker in sectors.items():
            if ticker in data and not data[ticker].empty:
                df = data[ticker].ffill().dropna()
                if len(df) >= 2:
                    pct_change = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                    results.append((name, pct_change))
        if not results: return "[ERROR] સેક્ટરનો ડેટા મળી રહ્યો નથી."
        results.sort(key=lambda x: x[1]) 
        return f"\nસૌથી નબળું **{results[0][0]}** સેક્ટર છે ({results[0][1]:.2f}% ઘટાડો).\nઅને સૌથી મજબૂત **{results[-1][0]}** સેક્ટર છે ({results[-1][1]:.2f}% ઉછાળો).\n"
    except: return "[ERROR] સેક્ટર ડેટા લાવવામાં ટેકનિકલ એરર આવી."

# ==========================================
# 📈 ૫. ઇન્ટ્રાડે એનાલિસિસ ટૂલ
# ==========================================
def run_intraday_analysis(ticker_symbol):
    try:
        ticker_symbol = ticker_symbol.upper()
        if not ticker_symbol.endswith('.NS') and not ticker_symbol.startswith('^'): 
            ticker_symbol += '.NS' 
        
        ticker_symbol = ticker_symbol.replace(".NS.NS", ".NS").replace("^NSEI.NS", "^NSEI").replace("^NSEBANK.NS", "^NSEBANK").replace("^CNXFIN.NS", "^CNXFIN")
            
        ticker = yf.Ticker(ticker_symbol)
        df_30m = yf.download(ticker_symbol, period="10d", interval="30m", progress=False, show_errors=False).ffill().dropna()
        df_15m = yf.download(ticker_symbol, period="5d", interval="15m", progress=False, show_errors=False).ffill().dropna()
        df_5m = yf.download(ticker_symbol, period="5d", interval="5m", progress=False, show_errors=False).ffill().dropna()
        
        if df_5m.empty or df_15m.empty: return f"[ERROR] {ticker_symbol} નો લાઈવ ડેટા અત્યારે ઉપલબ્ધ નથી."
        
        current_price = df_5m['Close'].iloc[-1]
        ema_20_30m = df_30m['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        ema_9_15m = df_15m['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        
        if current_price > ema_20_30m and current_price > ema_9_15m: trend = "મજબૂત તેજી"
        elif current_price < ema_20_30m and current_price < ema_9_15m: trend = "મજબૂત મંદી"
        else: trend = "સાઇડવેઝ"
            
        demand_zone = min(df_15m['Low'].tail(20).min(), df_30m['Low'].tail(15).min())
        supply_zone = max(df_15m['High'].tail(20).max(), df_30m['High'].tail(15).max())
        
        if trend == "મજબૂત તેજી":
            entry = current_price
            stoploss = demand_zone * 0.998 
            risk = entry - stoploss
            t1 = entry + (risk * 1.5)
            t2 = entry + (risk * 2.5)
        elif trend == "મજબૂત મંદી":
            entry = current_price
            stoploss = supply_zone * 1.002
            risk = stoploss - entry
            t1 = entry - (risk * 1.5)
            t2 = entry - (risk * 2.5)
        else:
            entry = current_price
            stoploss = demand_zone
            t1 = current_price + (supply_zone - current_price)*0.5
            t2 = supply_zone

        reward = abs(t1 - entry)
        rr_ratio = reward / risk if risk > 0 else 0
        
        if trend == "સાઇડવેઝ" or rr_ratio < 1.2: trade_action = "તટસ્થ (ટ્રેડ ટાળવો)"
        elif trend == "મજબૂત તેજી": trade_action = "ખરીદી કરો (Buy)"
        elif trend == "મજબૂત મંદી": trade_action = "વેચવાલી કરો (Sell)"

        return f"\n> {ticker_symbol} માટે ગણતરી:\nટ્રેન્ડ: {trend}. નિર્ણય: {trade_action}.\nચોક્કસ લેવલ્સ -> એન્ટ્રી: ₹{entry:.2f}, ટાર્ગેટ 1: ₹{t1:.2f}, ટાર્ગેટ 2: ₹{t2:.2f}, સ્ટોપલોસ: ₹{stoploss:.2f}.\n"
    except: return f"[ERROR] {ticker_symbol} ની ગણતરીમાં ટેકનિકલ ખામી છે."

# ==========================================
# 🧠 ૬. The AI Agent Router (Strict Truth Engine)
# ==========================================
print("\n" + "="*55)
print(f" 🤖 👁️ 📈 NIL AI v13.3 [Strict Anti-Hallucination Edition]")
print("="*55)
print(" ⌨️ સીધો પ્રશ્ન ટાઈપ કરો (લખીને જવાબ માટે)")
print(" 🎤 અથવા માત્ર 'v' લખીને Enter દબાવો (બોલીને જવાબ માટે)")
print("="*55 + "\n")

chat_history = [] 

def determine_intent(user_text, history_text):
    router_prompt = f"""
    Analyze the user's input: "{user_text}"
    Recent context: {history_text}
    
    TICKER EXTRACTION RULES (STRICTLY NSE F&O):
    1. INDICES: 'nifty' MUST be "^NSEI", 'bank nifty' MUST be "^NSEBANK", 'fin nifty' MUST be "^CNXFIN".
    2. NSE STOCKS: Identify the EXACT NSE ticker and append ".NS" (e.g., 'dixon' -> 'DIXON.NS', 'infosys' -> 'INFY.NS').
    
    Return EXACTLY a JSON:
    {{
      "intent": "INTRADAY" or "SCAN" or "SECTOR" or "CHAT",
      "tickers": ["TICKER"] 
    }}
    """
    try:
        model = genai.GenerativeModel('gemini-3.1-flash-lite-preview', generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(router_prompt)
        return json.loads(response.text)
    except: return {"intent": "CHAT", "tickers": []}

while True:
    mode_input = input("\n[તમે]: ").strip()
    
    if mode_input.lower() in ['બંધ કર', 'exit', 'quit', 'આવજો', 'બાય']: 
        print("Nil: આવજો નિલેશ! ટ્રેડિંગ માટે ઓલ ધ બેસ્ટ.")
        speak_instant("આવજો નિલેશ! ટ્રેડિંગ માટે ઓલ ધ બેસ્ટ.")
        time.sleep(2)
        audio_queue.join() 
        break
    
    is_voice_mode = False
    if mode_input.lower() == 'v':
        user_input = listen()
        is_voice_mode = True 
    else: user_input = mode_input

    if not user_input: continue

    history_text = "\n".join([f"You: {m['parts'][0]}" if m['role']=='user' else f"Nil: {m['parts'][0]}" for m in chat_history[-2:]])
    
    agent_decision = determine_intent(user_input, history_text)
    intent = agent_decision.get("intent", "CHAT")
    tickers = agent_decision.get("tickers", [])
    
    context = ""
    if intent == "SECTOR": context = f"[SECTOR DATA]: {run_sector_analysis()}"
    elif intent == "SCAN":
        buy_str = ", ".join(scanned_stocks["buy"][:10]) if scanned_stocks["buy"] else "કોઈ નહિ"
        sell_str = ", ".join(scanned_stocks["sell"][:10]) if scanned_stocks["sell"] else "કોઈ નહિ"
        context = f"[RADAR DATA]: ખરીદવા લાયક શેર (ટોપ 10 F&O): {buy_str}. વેચવા લાયક શેર (ટોપ 10 F&O): {sell_str}."
    elif intent == "INTRADAY" and len(tickers) > 0:
        combined_analysis = ""
        for t in tickers: combined_analysis += run_intraday_analysis(t) + "\n"
        context = f"[INTRADAY DATA]: \n{combined_analysis}"

    final_prompt = f"યુઝરનો પ્રશ્ન: {user_input}\n"
    if context:
        final_prompt += f"\n[માર્કેટ ડેટા]: {context}\n"
        
    # 💡 બગ ફિક્સ: ગપ્પા મારવા પર કડક પ્રતિબંધ
    final_prompt += """
    અત્યંત કડક નિયમો (CRITICAL):
    1. જો તમને આપેલા [માર્કેટ ડેટા] માં '[ERROR]' લખેલું હોય, તો તમારે ક્યારેય કોઈ અંદાજિત, જૂના કે ખોટા આંકડા (એન્ટ્રી, ટાર્ગેટ) જાતે બનાવવા નહિ. તમારે સ્પષ્ટ કહેવું: "માફ કરજો, આ શેરનો ડેટા અત્યારે મળી રહ્યો નથી."
    2. ક્યારેય 'નમસ્તે, હું નિલ છું' એવું બોલવું નહિ. સીધો જ જવાબ આપવો.
    3. જો ડેટામાં ERROR ન હોય અને આંકડા આપ્યા હોય, તો જ તે આંકડા યુઝરને આપવા. જો ટ્રેન્ડ સાઇડવેઝ હોય તો આંકડા આપીને પછી ના પાડવી કે "આ ટ્રેડ ના લો તો સારું".
    4. શુદ્ધ ગુજરાતીમાં પ્રોફેશનલ ફંડ મેનેજરની જેમ ટુ-ધ-પોઇન્ટ વાત કરવી.
    """
        
    chat_history.append({"role": "user", "parts": [final_prompt]})
    
    ai_response = ""
    sentence_buffer = ""
    
    try:
        print(f"Nil [Gemini 3.1 Flash-Lite ⚡]: \n", end="", flush=True) 
        
        response = chat_model.generate_content(chat_history, stream=True)
        
        for chunk in response:
            if chunk.text:
                text = chunk.text
                print(text, end="", flush=True)
                ai_response += text
                sentence_buffer += text
                
                if any(p in text for p in ['.', '!', '?', '\n']):
                    if len(sentence_buffer.strip()) > 2 and is_voice_mode:
                        speak_instant(sentence_buffer.strip())
                    sentence_buffer = ""
                    
        if sentence_buffer.strip() and is_voice_mode:
            speak_instant(sentence_buffer.strip())
            
    except Exception as e: print(f"\n❌ [Error]: {e}")

    if ai_response:
        print("\n")
        chat_history.append({"role": "model", "parts": [ai_response]})
        if is_voice_mode: audio_queue.join()