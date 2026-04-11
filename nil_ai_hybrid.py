import os
import json
import datetime
import re
import requests
from dotenv import load_dotenv
from openai import OpenAI
import httpx
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
from tavily import TavilyClient
import yfinance as yf
import speech_recognition as sr
from gtts import gTTS
import os

# ==========================================
# ૧. API Keys અને OpenRouter / Ollama સેટઅપ
# ==========================================
load_dotenv()
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_MY_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# 💡 ટાઈમઆઉટ સેટ કર્યું છે જેથી ક્યારેય હેંગ ન થાય
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    timeout=60.0  # httpx.Timeout ની જગ્યાએ સીધી 60 સેકન્ડ આપી દો
)

# 💡 લોકલ Ollama ફોલબેક (ઇન્ટરનેટ/સર્વર ડાઉન હોય ત્યારે)
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama-local",
    timeout=120.0  # અહીં પણ સીધી 120 સેકન્ડ આપી દો
)

# ==========================================
# ૨. લાઈવ કેલેન્ડર 
# ==========================================
today_date = datetime.date.today().strftime("%d/%m/%Y")
current_time = datetime.datetime.now().strftime("%I:%M %p")

# ==========================================
# ૩. ડિજિટલ ડાયરી અને સેન્સર્સ
# ==========================================
CONTACTS_FILE = "contacts.json"

def load_contacts():
    try:
        with open(CONTACTS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError:
        default_contacts = {"નિલેશ": TELEGRAM_MY_CHAT_ID} if TELEGRAM_MY_CHAT_ID else {}
        with open(CONTACTS_FILE, 'w', encoding='utf-8') as f: json.dump(default_contacts, f, ensure_ascii=False, indent=4)
        return default_contacts

def save_new_contact(name, chat_id):
    contacts = load_contacts()
    contacts[name] = str(chat_id)
    with open(CONTACTS_FILE, 'w', encoding='utf-8') as f: json.dump(contacts, f, ensure_ascii=False, indent=4)
    return f"✅ '{name}' નો નંબર સેવ થઈ ગયો છે."

def send_telegram_message(name, message):
    contacts = load_contacts()
    if name in contacts:
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": contacts[name], "text": message}, timeout=5)
            return f"✅ {name} ને મેસેજ મોકલી દીધો છે."
        except Exception as e: return f"❌ મેસેજ એરર: {e}"
    else: return f"માફ કરજો, '{name}' નો નંબર ડાયરીમાં નથી."

def get_weather(city):
    try:
        res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric", timeout=5).json()
        return f"{city} નું તાપમાન {res['main']['temp']}°C છે ({res['weather']['description']})."
    except: return "હવામાનની માહિતી મળી શકી નથી."
    # ==========================================
# 🎙️ ધ વોઇસ એન્જિન (સાંભળવાની અને બોલવાની શક્તિ)
# ==========================================
def speak(text):
    """આ ફંક્શન શુદ્ધ ગુજરાતીમાં બોલશે"""
    try:
        # ટર્મિનલમાં મેસેજ પ્રિન્ટ કરો
        print(f"🔊 Nil: {text}")
        
        # લખાણને અવાજમાં ફેરવીને mp3 ફાઈલ બનાવો
        tts = gTTS(text=text, lang='gu')
        audio_file = "nil_voice.mp3"
        tts.save(audio_file)
        
        # Mac ની ઇનબિલ્ટ સિસ્ટમ (afplay) થી અવાજ પ્લે કરો 
        os.system(f"afplay {audio_file}")
        
        # ફાઈલ પ્લે થયા પછી કચરો (mp3) ડિલીટ કરો
        if os.path.exists(audio_file):
            os.remove(audio_file)
    except Exception as e:
        print(f"❌ [Voice Error]: {e}")

def listen():
    """આ ફંક્શન તમારા માઈક્રોફોનમાંથી તમારો અવાજ સાંભળશે"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 નિલેશ, હું સાંભળી રહ્યો છું... (બોલો)")
        # પાછળનો ઘોંઘાટ (પંખાનો અવાજ વગેરે) ઓછો કરવા
        recognizer.adjust_for_ambient_noise(source, duration=1) 
        try:
            # 5 સેકન્ડ સુધી અવાજની રાહ જોશે
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10) 
            print("[સિસ્ટમ]: પ્રોસેસ થઈ રહ્યું છે...")
            
            # ગૂગલને કહો કે આ અવાજ ગુજરાતી (gu-IN) માં છે
            text = recognizer.recognize_google(audio, language="gu-IN")
            print(f"તમે કહ્યું: {text}")
            return text
        except sr.WaitTimeoutError:
            return "" # જો તમે કંઈ ન બોલો તો ખાલી પાછું જશે
        except sr.UnknownValueError:
            speak("માફ કરજો નિલેશ, હું બરાબર સમજી ન શક્યો. ફરીથી બોલશો?")
            return ""
        except Exception as e:
            print(f"❌ [Mic Error]: {e}")
            return ""

# ==========================================
# ૪. સ્માર્ટ મેમરી અને ઓળખ
# ==========================================
system_prompt = f"""
તમારું નામ 'Nil' છે. તમે નિલેશના અત્યંત ચતુર ડીજીટલ અવતાર છો.
તમારી મુખ્ય ભાષા શુદ્ધ ગુજરાતી છે.

[ખાસ સૂચના]: આજની તારીખ {today_date} છે અને સમય {current_time} છે. 

એક્શન કમાન્ડ:
૧. કોઈનો નંબર સેવ કરવા:
૨. કોઈને ટેલિગ્રામ મેસેજ કરવા:
"""

MEMORY_FILE = "nil_memory.json"
def load_memory():
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return [{"role": "system", "content": system_prompt}]

def save_memory(history):
    # સિસ્ટમ પ્રોમ્પ્ટ (પહેલો મેસેજ) અને છેલ્લા ૪ મેસેજ જાળવી રાખવા માટે સુધારો
    data_to_save = [history[0]] + history[-4:] if len(history) > 5 else history
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f: json.dump(data_to_save, f, ensure_ascii=False, indent=4)

chat_history = load_memory()
market_symbols = {'nifty': '^NSEI', 'નિફ્ટી': '^NSEI', 'crude': 'CL=F', 'ક્રૂડ': 'CL=F'}

# ==========================================
# ૫. સ્માર્ટ રીટ્રાય અને ફોલબેક સિસ્ટમ (Tenacity)
# ==========================================
@retry(
    wait=wait_random_exponential(min=1, max=10), # સ્માર્ટ વેઇટ ટાઈમ 
    stop=stop_after_attempt(3), # 3 વખત ટ્રાય કરશે
    retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError, openai.InternalServerError))
)
def call_openrouter_with_fallback(messages):
    return client.chat.completions.create(
        extra_headers={"HTTP-Referer": "https://nil-ai.com", "X-Title": "Nil AI"},
        model="qwen/qwen3.6-plus:free", # 1M કોન્ટેક્સ્ટવાળું બેસ્ટ મોડલ
        messages=messages,
        temperature=0.3,
        extra_body={
            # જો Qwen સર્વર બીઝી હોય, તો જાતે જ આ બે પાવરફુલ મોડલ પર ટ્રાય કરશે
            "models": ["meta-llama/llama-3.3-70b-instruct:free", "google/gemma-3-27b-it:free"]
        }
    )

# ==========================================
# ૬. માસ્ટર લૂપ (Clean, Fast & Bulletproof)
# ==========================================
print("=======================================================")
print(f" 🤖 🌐 Nil AI")
print(f" 📅 ડેટ: {today_date} | ⚡ એન્જિન: Hybrid (Cloud + Ollama)")
print("=======================================================")

while True:
    user_input = input("તમે: ")
    if user_input.lower() in ['exit', 'quit', 'bye']: break
    
    context = ""
    if "તાપમાન" in user_input or "વાતાવરણ" in user_input:
        city = "Ahmedabad" if "અમદાવાદ" in user_input else "Surat" if "સુરત" in user_input else "Ahmedabad"
        context += f"\n: {get_weather(city)}"

    found_symbols = [s for k, s in market_symbols.items() if k in user_input.lower()]
    if found_symbols:
        try:
            # 💡 બ્રેકેટ્સ અને f-string ની એરર અહીં સોલ્વ કરી દીધી છે
            finance_str = " ".join([f"[{sym}: {round(yf.Ticker(sym).history(period='1d')['Close'].iloc[-1], 2)}]" for sym in set(found_symbols) if not yf.Ticker(sym).history(period='1d').empty])
            context += f"\n[Live Finance]: {finance_str}"
        except: pass

    if any(w in user_input.lower() for w in ['સમાચાર', 'ન્યૂઝ', 'news', 'તાજા']):
        print("[સિસ્ટમ 🌐]: લાઇવ સમાચાર શોધાઈ રહ્યા છે...")
        try:
            res = tavily_client.search(query=f"{user_input} {today_date} latest news", search_depth="basic", max_results=2)
            context += f"\n[Live News]: " + "\n".join([r['content'] for r in res['results']])
        except: pass
            
    final_input = user_input + context
    chat_history.append({"role": "user", "content": final_input})
    
    ai_response = None
    engine = ""

    # 💡 સ્ટેપ 1: Cloud APIs (Qwen, Llama, Gemma) ટ્રાય કરશે
    try:
        completion = call_openrouter_with_fallback(chat_history)
        # 💡 API નો રિસ્પોન્સ ફેચ કરવા માટે choices[0] એડ કર્યું
        ai_response = completion.choices[0].message.content
        used_model = getattr(completion, 'model', 'Cloud Model').split('/')[-1]
        engine = f"☁️ OpenRouter [{used_model}]"
        
    except Exception as e:
        # 💡 સ્ટેપ 2: જો બધા ક્લાઉડ સર્વર ફૂલ હોય તો Local મશીન પર જશે!
        print(f"⚠️ ક્લાઉડ સર્વર્સ બીઝી છે. 💻 લોકલ Ollama પર સ્વિચ થઈ રહ્યું છે...")
        try:
            completion = ollama_client.chat.completions.create(
                model="llama3.2:latest", # તમારા Mac પર ઇન્સ્ટોલ કરેલ મોડલ
                messages=chat_history,
                temperature=0.3
            )
            # 💡 લોકલમાં પણ choices[0] એડ કર્યું
            ai_response = completion.choices[0].message.content
            engine = "💻 Local [Ollama]"
        except Exception as local_e:
            print("❌ ઇન્ટરનેટ અને લોકલ Ollama બંને બંધ છે. કૃપા કરીને Ollama ચાલુ કરો.")
            chat_history.pop()
            continue

    if not ai_response:
        continue

    # 💡 બુલેટપ્રૂફ એક્શન સેન્સર
    clean_response = ai_response.replace("[", "").replace("]", "")
    if "SAVE_CONTACT:" in clean_response:
        match = re.search(r"SAVE_CONTACT:\s*(.*?),\s*(.*)", clean_response)
        if match: print(f"\n[સિસ્ટમ 📱]: {save_new_contact(match.group(1).strip(), match.group(2).strip())}")
    
    if "SEND_MSG:" in clean_response:
        match = re.search(r"SEND_MSG:\s*(.*?),\s*(.*)", clean_response)
        if match: print(f"\n[સિસ્ટમ 📨]: {send_telegram_message(match.group(1).strip(), match.group(2).strip())}")

    ai_response = re.sub(r"\?", "", ai_response).strip()
    ai_response = re.sub(r"\?", "", ai_response).strip()
    if not ai_response: ai_response = "મેસેજ મોકલી દીધો છે!"

    print(f"\nNil [{engine}]: {ai_response}\n")
    save_memory(chat_history)