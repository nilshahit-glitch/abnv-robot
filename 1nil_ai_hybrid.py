import os
import re
import json
import random
import threading
import datetime
import requests
import subprocess
import time
import base64

from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient
import yfinance as yf

import speech_recognition as sr
from gtts import gTTS

# ==========================================
# ૧. API Keys અને એન્જિન સેટઅપ
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(env_path)

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
    timeout=15.0
)

nvidia_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
    timeout=20.0
)

ollama_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama-local", timeout=120.0)

today_date = datetime.date.today().strftime("%d/%m/%Y")

# ==========================================
# ૨. ઓટો-વેક Ollama
# ==========================================
def ensure_ollama_running():
    try:
        requests.get("http://localhost:11434/", timeout=2)
    except:
        print("\n⚠️ લોકલ Ollama બંધ છે. સાચો રસ્તો શોધીને જગાડી રહ્યો છું (8 સેકન્ડ રાહ જુઓ)...")
        try:
            mac_path_magic = "PATH=/usr/local/bin:/opt/homebrew/bin:$PATH "
            subprocess.Popen(mac_path_magic + "ollama serve", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(8) 
        except Exception as e:
            print(f"❌ Ollama ચાલુ કરવામાં એરર: {e}")

# ==========================================
# ૩. સ્માર્ટ મેમરી ફિલ્ટર
# ==========================================
MEMORY_FILE = "nil_memory.json"
IMPORTANT_KEYWORDS = ['trade', 'nifty', 'crude', 'buy', 'sell', 'contact', 'msg', 'મેસેજ', 'સેવ', 'ભાવ', 'નંબર']

def smart_save_memory(history):
    if len(history) <= 1: return
    pruned_history = [history[0]]
    recent_chats = history[-20:]
    for msg in recent_chats:
        content = msg['content'].lower()
        if any(key in content for key in IMPORTANT_KEYWORDS) or msg['role'] == 'assistant' or len(content) > 50:
            pruned_history.append(msg)
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(pruned_history[-15:], f, ensure_ascii=False, indent=4)

# ==========================================
# ૪. વોઇસ, સેન્સર્સ અને વિઝન (આંખો)
# ==========================================
def get_weather(city):
    try:
        search_query = f"current temperature in {city} Ahmedabad today 2026"
        res = tavily_client.search(query=search_query, search_depth="basic", max_results=1)
        if res['results']:
            return res['results'][0]['content']
        return "માહિતી મળી રહી નથી."
    except:
        return "સર્વર એરર."

def speak(text):
    try:
        if re.search(r'[\u0A80-\u0AFF]', text): lang = 'gu'     
        elif re.search(r'[\u0900-\u097F]', text): lang = 'hi'   
        else: lang = 'en'                                       
        
        tts = gTTS(text=text, lang=lang)
        audio_file = "nil_voice.mp3"
        tts.save(audio_file)
        os.system(f"afplay {audio_file}")
        if os.path.exists(audio_file): os.remove(audio_file)
    except Exception as e: print(f"❌ [Voice Error]: {e}")

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 નિલેશ, બોલો...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10) 
            text = recognizer.recognize_google(audio, language="gu-IN")
            print(f"તમે: {text}")
            return text
        except: return ""

def play_filler_sound():
    word = random.choice(["હમ્મ...", "હા...", "ઓકે...", "વિચારવા દો..."])
    os.system(f"say -v Lekha '{word}' &")

def analyze_image(image_path, question):
    print(f"\n[👁️ સિસ્ટમ]: નિલ ફોટો જોઈ રહ્યો છે... મગજ પ્રોસેસ કરી રહ્યું છે...")
    try:
        ext = image_path.split('.')[-1].lower()
        mime_type = "image/jpeg" if ext in ['jpg', 'jpeg'] else "image/png"

        with open(image_path.strip(), "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        headers = {
            "Authorization": f"Bearer {os.getenv('NVIDIA_API_KEY')}",
            "Accept": "application/json"
        }
        
        payload = {
            "model": "meta/llama-3.2-11b-vision-instruct", 
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_string}"}}
                    ]
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.2
        }
        
        response = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"સર્વર એરર: {response.status_code} - કૃપા કરીને સાચો પાથ ચેક કરો."
    except Exception as e:
        return f"ફોટો ખોલવામાં એરર: {e}"

# ==========================================
# 📈 ૫. ફાઇનાન્શિયલ સેન્સર (AI-Powered Live Market Pulse)
# ==========================================
def get_live_stock_price(user_input):
    print("\n[સિસ્ટમ 🧠]: શેર કે કૉમોડિટીનું સાચું નામ શોધી રહ્યો છું...")
    try:
        prompt = f"""
        Extract the Indian stock, index, or commodity name from the following Gujarati text. 
        Return ONLY its Yahoo Finance ticker symbol.
        Rules:
        [Indices]
        - Nifty 50 = ^NSEI
        - Bank Nifty = ^NSEBANK
        
        [Commodities]
        - Crude Oil / ક્રૂડ = CL=F
        - Gold / સોનું = GC=F
        - Silver / ચાંદી = SI=F
        - Natural Gas / નેચરલ ગેસ = NG=F
        
        [Indian Stocks]
        - For any Indian stock, add '.NS' at the end (e.g., HDFC Bank = HDFCBANK.NS, Reliance = RELIANCE.NS).
        
        - If no financial instrument is found, return exactly 'NONE'.
        Text: '{user_input}'
        """
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=15
        )
        ticker_symbol = response.choices[0].message.content.strip().upper()

        if ticker_symbol == 'NONE' or not ticker_symbol:
            return None

        print(f"[સિસ્ટમ 📈]: {ticker_symbol} નો લાઈવ ભાવ લાવી રહ્યો છું...")
        stock = yf.Ticker(ticker_symbol)
        data = stock.history(period="1d")
        
        if not data.empty:
            current_price = data['Close'].iloc[-1]
            return f"મળેલ માહિતી મુજબ {ticker_symbol} નો લેટેસ્ટ લાઈવ ભાવ {current_price:.2f} છે."
        return None
    except Exception as e:
        return None

# ==========================================
# ૬. માસ્ટર લૂપ: ધ ડિજિટલ અવતાર એન્જિન
# ==========================================
print("\n" + "="*55)
print(f" 🤖 👁️ 📈 NIL AI v8.5 [Financial Avatar]")
print("="*55 + "\n")

system_prompt = f"""
તમારું નામ 'નિલ' (Nil) છે. તમે નિલેશના સાચા ડિજિટલ મિત્ર અને પ્રોફેશનલ ટ્રેડિંગ એક્સપર્ટ છો. 
આજની તારીખ {today_date} છે.

[વ્યક્તિત્વ અને ભાષા]:
૧. હંમેશા ૧૦૦% શુદ્ધ, સાદી અને રોજિંદી ગુજરાતીમાં જ વાત કરવી.
૨. તમારો ટોન એક સમજુ અને વિશ્વાસુ મિત્ર જેવો હોવો જોઈએ.

[લાઈવ ડેટા નિયમ]:
જ્યારે પણ કોઈ નિલેશ તાપમાન, સમાચાર કે લાઈવ ભાવ પૂછે, ત્યારે હંમેશા 'Live Internet Data' કે 'Live Internet Market Data' નો જ ઉપયોગ કરવો. જો ડેટા જૂનો લાગે તો ઇન્ટરનેટ ચેક કરવું તેવું જણાવવુ.

[ચાર્ટ રીડિંગના કડક નિયમો (Must Follow)]:
જ્યારે તમને 'Image Analysis Report' મળે, ત્યારે:
૧. ભાવની ચોકસાઈ (MUST FOLLOW): જો તમને 'Live Price Data' મળ્યો હોય, તો માત્ર તે ભાવનો જ ઉપયોગ કરવો. 
૨. વિશ્લેષણ: ચાર્ટ જોઈને ટ્રેન્ડ (તેજી/મંદી) અને પેટર્ન જણાવવી, પણ ચોક્કસ ભાવ માટે માત્ર 'Live Price Data' પર જ ભરોસો કરવો.
૩. ભાવની ચોકસાઈ (Price Accuracy): ચાર્ટની જમણી બાજુ (Y-axis) પર જે મોટા અક્ષરે વર્તમાન ભાવ (LTP) લખ્યો હોય તે જ જણાવવો.
૪. શેરની વિગત: શેરનું નામ અને ચાર્ટની ટાઈમફ્રેમ ઓળખવી.
૫. ટેકનિકલ એનાલિસિસ: કેન્ડલસ્ટિક પેટર્ન અને ટ્રેન્ડ સ્પષ્ટ જણાવવો.
૬. લેવલ્સ: સપોર્ટ અને રેઝિસ્ટન્સના લેવલ વર્તમાન ભાવની આસપાસના જ આપવા.

[જવાબ]: જવાબ ટૂંકો, સચોટ અને એક અનુભવી ટ્રેડર જેવો આપવો.
"""
chat_history = [{"role": "system", "content": system_prompt.strip()}]

available_engines = [
    ("Groq 70B ⚡", groq_client, "llama-3.3-70b-versatile"),           
    ("NVIDIA Llama 🟢", nvidia_client, "meta/llama-3.1-70b-instruct"), 
    ("NVIDIA Gemma-3 🧠", nvidia_client, "google/gemma-3n-e4b-it")     
]

while True:
    user_input = listen()
    if not user_input: continue
    if any(word in user_input.lower() for word in ['બંધ કર', 'exit', 'quit', 'આવજો', 'બાય']): 
        speak("આવજો નિલેશ! જરૂર પડે ત્યારે યાદ કરજો.")
        break
    
    context = ""
    
    # 👁️‍🗨️ વિઝન ટ્રીગર (આંખો)
    vision_keywords = ['જો', 'ફોટો', 'ચાર્ટ', 'જુઓ', 'સ્ક્રીનશોટ']
    if any(w in user_input.lower() for w in vision_keywords):
        speak("મને ફોટાનો રસ્તો અથવા પાથ આપો.")
        raw_path = input("\n[📸 ફોટાનો Path ડ્રેગ-ડ્રોપ કરો અને Enter મારો]: ")
        clean_path = raw_path.replace("'", "").replace('"', '').strip() 
        
        if os.path.exists(clean_path):
            vision_result = analyze_image(clean_path, user_input)
            context += f"\n[👁️ Image Analysis Report]: {vision_result}"
        else:
            context += "\n[System]: નિલેશ, તમે આપેલો ફોટાનો પાથ ખોટો છે."

    # 📈 ફાઇનાન્શિયલ સેન્સર (Live Market Pulse)
    market_keywords = ['ભાવ', 'price', 'માર્કેટ', 'શેર', 'નિફ્ટી', 'nifty', 'બેંક નિફ્ટી']
    if any(w in user_input.lower() for w in market_keywords):
        live_price_data = get_live_stock_price(user_input)
        if live_price_data:
            context += f"\n[Live Internet Market Data]: {live_price_data}"

    # 🌡️ સેન્સર્સ (હવામાન)
    if any(w in user_input.lower() for w in ['તાપમાન', 'વાતાવરણ', 'હવામાન']):
        city = "Ahmedabad" if "અમદાવાદ" in user_input else "Surat" if "સુરત" in user_input else "Ahmedabad"
        context += f"\n[Live Weather: {get_weather(city)}]"

    # 📰 સેન્સર્સ (સમાચાર)
    research_keywords = ['સમાચાર', 'ન્યૂઝ', 'news', 'તાજા']
    if any(w in user_input.lower() for w in research_keywords):
        print("\n[સિસ્ટમ 🌐]: ગૂગલ પર લાઈવ સમાચાર શોધી રહ્યો છું...")
        try:
            res = tavily_client.search(query=user_input, search_depth="advanced", max_results=3)
            news_data = "\n".join([f"- {r['title']}: {r['content'][:200]}" for r in res['results']])
            context += f"\n[Live Internet News]: {news_data}"
        except: pass

    final_input = user_input + context
    chat_history.append({"role": "user", "content": final_input})
    
    threading.Thread(target=play_filler_sound).start()
    ai_response = ""
    success = False

    optimized_history = [chat_history[0]] + chat_history[-4:] if len(chat_history) > 4 else chat_history

    for engine_name, client_api, model_name in available_engines:
        try:
            stream = client_api.chat.completions.create(
                model=model_name, 
                messages=optimized_history,
                temperature=0.2, 
                stream=True
            )
            print(f"Nil [{engine_name}]: ", end="", flush=True) 
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    print(text, end="", flush=True)
                    ai_response += text
            
            success = True
            break 

        except Exception as e:
            print(f"\n[⚠️ {engine_name} Failed]: સર્વર બિઝી છે, તરત નેક્સ્ટ મગજ વાપરી રહ્યો છું...")
            continue 

    if not success:
        print(f"\n❌ [Cloud Offline]: લોકલ મગજ ચાલુ કરી રહ્યો છું.")
        ensure_ollama_running()
        try:
            local_history = chat_history.copy()
            local_history[0]["content"] += " [LOCAL RULE]: Speak natural, friendly Gujarati ONLY."
            stream = ollama_client.chat.completions.create(
                model="qwen2.5:7b", 
                messages=local_history, 
                temperature=0.1, 
                stream=True
            )
            print(f"Nil [💻 Local 7B]: ", end="", flush=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    print(text, end="", flush=True)
                    ai_response += text
        except Exception as local_e:
            print(f"\n❌ કોઈ સર્વર ઉપલબ્ધ નથી: {local_e}")

    if ai_response:
        print("\n")
        speak(ai_response)
        chat_history.append({"role": "assistant", "content": ai_response})
        smart_save_memory(chat_history)