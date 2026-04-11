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

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
import yfinance as yf
import speech_recognition as sr
from gtts import gTTS

# ==========================================
# ૧. API Keys અને એન્જિન સેટઅપ
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(env_path)

groq_client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"), timeout=20.0)

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
        
        clean_text = text.replace(".NS", "").replace("^NSEI", "નિફ્ટી").replace("^NSEBANK", "બેંક નિફ્ટી")
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
            except Exception as e: 
                pass 
            
        if audio_queue.empty():
            is_speaking = False 
            
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
# 📡 ૩. બેકગ્રાઉન્ડ સ્કેનર
# ==========================================
NIFTY_WATCHLIST = ['RELIANCE.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'TCS.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'LT.NS', 'BAJFINANCE.NS', 'TATAMOTORS.NS', 'MARUTI.NS']
scanned_stocks = {"buy": [], "sell": []}

def background_market_radar():
    print("\n[સિસ્ટમ 📡]: બેકગ્રાઉન્ડ રાડાર ઓનલાઈન છે...")
    while True:
        try:
            buy_list, sell_list = [], []
            data = yf.download(NIFTY_WATCHLIST, period="5d", interval="15m", group_by='ticker', progress=False)
            
            for ticker in NIFTY_WATCHLIST:
                if ticker in data and not data[ticker].empty:
                    df = data[ticker].ffill().dropna()
                    if len(df) < 20: continue
                    current_price = df['Close'].iloc[-1]
                    ema_20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
                    ema_9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
                    clean_name = ticker.replace(".NS", "")
                    if current_price > ema_20 and current_price > ema_9: buy_list.append(clean_name)
                    elif current_price < ema_20 and current_price < ema_9: sell_list.append(clean_name)
            
            scanned_stocks["buy"] = buy_list
            scanned_stocks["sell"] = sell_list
            time.sleep(900) 
        except: time.sleep(60) 

threading.Thread(target=background_market_radar, daemon=True).start()

# ==========================================
# 📊 ૪. સેક્ટર એનાલિસિસ
# ==========================================
def run_sector_analysis():
    print("\n[સિસ્ટમ 📊]: તમામ સેક્ટરનો ડેટા ચેક કરી રહ્યો છું...")
    try:
        sectors = {
            'બેંકિંગ (Bank)': '^NSEBANK', 
            'આઈટી (IT)': '^CNXIT', 
            'ઓટો (Auto)': '^CNXAUTO', 
            'ફાર્મા (Pharma)': '^CNXPHARMA', 
            'એફએમસીજી (FMCG)': '^CNXFMCG', 
            'મેટલ (Metal)': '^CNXMETAL'
        }
        tickers = list(sectors.values())
        data = yf.download(tickers, period="5d", group_by='ticker', progress=False)
        
        results = []
        for name, ticker in sectors.items():
            if ticker in data and not data[ticker].empty:
                df = data[ticker].ffill().dropna()
                if len(df) >= 2:
                    close_today = df['Close'].iloc[-1]
                    close_yest = df['Close'].iloc[-2]
                    pct_change = ((close_today - close_yest) / close_yest) * 100
                    results.append((name, pct_change))
        
        if not results: return "[ERROR] સેક્ટરનો લાઈવ ડેટા મળી રહ્યો નથી."
        results.sort(key=lambda x: x[1]) 
        
        worst_sector = results[0]
        best_sector = results[-1]
        
        return f"\nઆજના માર્કેટમાં સૌથી નબળું (ડાઉન) **{worst_sector[0]}** સેક્ટર છે ({worst_sector[1]:.2f}% ઘટાડો).\nઅને સૌથી મજબૂત (તેજીવાળું) **{best_sector[0]}** સેક્ટર છે ({best_sector[1]:.2f}% ઉછાળો).\n"
    except Exception as e:
        return f"[ERROR] સેક્ટર ડેટા લાવવામાં ટેકનિકલ એરર આવી."

# ==========================================
# 📈 ૫. ઇન્ટ્રાડે એનાલિસિસ ટૂલ
# ==========================================
def run_intraday_analysis(ticker_symbol):
    try:
        if not ticker_symbol.endswith('.NS') and not ticker_symbol.startswith('^') and ticker_symbol != 'CL=F': ticker_symbol += '.NS'
            
        ticker = yf.Ticker(ticker_symbol)
        df_30m = ticker.history(period="10d", interval="30m").ffill().dropna()
        df_15m = ticker.history(period="5d", interval="15m").ffill().dropna()
        df_5m = ticker.history(period="2d", interval="5m").ffill().dropna()
        
        if df_5m.empty or df_15m.empty: return f"[ERROR] {ticker_symbol} નો ડેટા મળતો નથી. કદાચ સ્પેલિંગ ખોટો છે અથવા સર્વર એરર છે."
        
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

        return f"\n> {ticker_symbol} માટે:\nટ્રેન્ડ: {trend}. નિર્ણય: {trade_action}.\nએન્ટ્રી: ₹{entry:.2f}, ટાર્ગેટ 1: ₹{t1:.2f}, ટાર્ગેટ 2: ₹{t2:.2f}, સ્ટોપલોસ: ₹{stoploss:.2f}.\n"
    except Exception as e: return f"[ERROR] {ticker_symbol} ની ગણતરીમાં ખામી."

# ==========================================
# 🧠 ૬. The AI Agent Router (Hinglish Support)
# ==========================================
print("\n" + "="*55)
print(f" 🤖 👁️ 📈 NIL AI v11.8 [Hinglish & Server Fix Edition]")
print("="*55)
print(" ⌨️ સીધો પ્રશ્ન ટાઈપ કરો (લખીને જવાબ માટે)")
print(" 🎤 અથવા માત્ર 'v' લખીને Enter દબાવો (બોલીને જવાબ માટે)")
print("="*55 + "\n")

chat_history = [{"role": "system", "content": "તમારું નામ નિલ છે. તમે નિલેશના ફંડ મેનેજર છો. ગુજરાતીમાં જ જવાબ આપવા. ટૂંકમાં વાત કરવી."}]

def determine_intent(user_text, history):
    recent_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-3:] if msg['role'] != 'system'])
    
    # 💡 બગ ફિક્સ: હિંગ્લિશ ડિક્શનરી ઉમેરી
    router_prompt = f"""
    Analyze the user's input (it can be in Gujarati OR Hinglish/English letters): "{user_text}"
    Recent context:
    {recent_context}
    
    TICKER DICTIONARY (Supports Hinglish & Gujarati):
    - nifty, નિફ્ટી -> ^NSEI
    - bank nifty, બેંક નિફ્ટી -> ^NSEBANK
    - reliance, રિલાયન્સ -> RELIANCE.NS
    - hdfc, hdfc bank, એચડીએફસી -> HDFCBANK.NS
    - sbi, sbin, સ્ટેટ બેંક -> SBIN.NS
    - tcs, ટીસીએસ -> TCS.NS
    - tata motor, tata motors, ટાટા મોટર્સ -> TATAMOTORS.NS
    - infosys, infy, ઇન્ફોસિસ -> INFY.NS
    
    Return ONLY a raw JSON object:
    {{
      "intent": "INTRADAY" or "SCAN" or "SECTOR" or "CHAT",
      "tickers": ["TICKER.NS"] 
    }}
    
    CRITICAL RULES:
    1. Match the English/Hinglish spelling strictly using the dictionary to avoid wrong .NS symbols.
    2. If user asks for target/analysis, output "INTRADAY".
    """
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": router_prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return json.loads(res.choices[0].message.content)
    except: return {"intent": "CHAT", "tickers": []}

while True:
    mode_input = input("\n[તમે]: ").strip()
    
    if mode_input.lower() in ['બંધ કર', 'exit', 'quit', 'આવજો', 'બાય']: 
        print("Nil: આવજો નિલેશ! લાઈવ માર્કેટ માટે ઓલ ધ બેસ્ટ.")
        speak_instant("આવજો નિલેશ! ટ્રેડિંગ માટે ઓલ ધ બેસ્ટ.")
        audio_queue.join() 
        break
    
    is_voice_mode = False
    
    if mode_input.lower() == 'v':
        user_input = listen()
        is_voice_mode = True 
    else:
        user_input = mode_input

    if not user_input: continue

    agent_decision = determine_intent(user_input, chat_history)
    intent = agent_decision.get("intent", "CHAT")
    tickers = agent_decision.get("tickers", [])
    
    context = ""
    
    if intent == "SECTOR":
        sector_data = run_sector_analysis()
        context = f"[SECTOR DATA]: {sector_data}"
        
    elif intent == "SCAN":
        buy_str = ", ".join(scanned_stocks["buy"][:5]) if scanned_stocks["buy"] else "કોઈ નહિ"
        sell_str = ", ".join(scanned_stocks["sell"][:5]) if scanned_stocks["sell"] else "કોઈ નહિ"
        context = f"[RADAR DATA]: ખરીદવા લાયક શેર: {buy_str}. વેચવા લાયક શેર: {sell_str}."
        
    elif intent == "INTRADAY" and len(tickers) > 0:
        combined_analysis = ""
        for t in tickers:
            combined_analysis += run_intraday_analysis(t) + "\n"
        context = f"[INTRADAY DATA]: \n{combined_analysis}"
        
    elif intent == "INTRADAY" and len(tickers) == 0:
        context = "[System Instruction]: યુઝરને પૂછો કે તેઓ કયા શેરનું એનાલિસિસ ઈચ્છે છે."

    final_prompt = user_input
    if context:
        final_prompt += f"\n\n[માર્કેટ ડેટા/સંદર્ભ]: {context}\n"
        final_prompt += "\nનિયમ: જો ઉપરના ડેટામાં [ERROR] હોય, તો ગપ્પા મારવા નહિ. માત્ર માફી માંગવી."
        
    chat_history.append({"role": "user", "content": final_prompt})
    
    ai_response = ""
    sentence_buffer = ""
    
    try:
        stream = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=chat_history[-5:], temperature=0.3, stream=True)
        print(f"Nil [Agent ⚡]: \n", end="", flush=True) 
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                print(text, end="", flush=True)
                ai_response += text
                sentence_buffer += text
                
                if any(p in text for p in ['.', '!', '?', '\n']):
                    if len(sentence_buffer.strip()) > 2:
                        if is_voice_mode: speak_instant(sentence_buffer.strip())
                    sentence_buffer = ""
                    
        if sentence_buffer.strip():
            if is_voice_mode: speak_instant(sentence_buffer.strip())
            
    except Exception as e: print(f"\n❌ [Error]: {e}")

    if ai_response:
        print("\n")
        chat_history.append({"role": "assistant", "content": ai_response})
        if is_voice_mode: audio_queue.join()