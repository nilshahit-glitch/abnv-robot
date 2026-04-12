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
# ૨. અલ્ટ્રા-સ્માર્ટ ડિક્શનરી (AI Alias Engine)
# ==========================================
FO_MASTER_LIST = {
    # IT & Tech
    "HCLTECH": ["HCL", "HCL TECH", "HCLTECHNOLOGY"],
    "INFY": ["INFY", "INFOSYS"],
    "TCS": ["TCS", "TATA CONSULTANCY"],
    "TECHM": ["TECH MAHINDRA", "TECHM"],
    "WIPRO": ["WIPRO"],
    
    # Banks & Finance
    "HDFCBANK": ["HDFC", "HDFCBANK", "HDFC BANK"],
    "ICICIBANK": ["ICICI", "ICICIBANK", "ICICI BANK"],
    "SBIN": ["SBI", "SBIN", "STATE BANK"],
    "BAJFINANCE": ["BAJAJ FINANCE", "BAJFIN"],
    "BAJAJFINSV": ["BAJAJ FINSERV", "FINSERV"],
    "AXISBANK": ["AXIS", "AXISBANK", "AXIS BANK"],
    "KOTAKBANK": ["KOTAK", "KOTAKBANK"],
    
    # Auto
    "TATAMOTORS": ["TATAMOTORS", "TATA MOTORS", "TAMO"],
    "M&M": ["M&M", "MAHINDRA", "MAHINDRA & MAHINDRA", "MNM"],
    "MARUTI": ["MARUTI", "MARUTI SUZUKI"],
    "BAJAJ-AUTO": ["BAJAJ AUTO", "BAJAJ-AUTO"],
    "FORCEMOT": ["FORCE", "FORCEMOTOR", "FORCE MOTORS"],
    "TVSMOTOR": ["TVS", "TVSMOTOR", "TVS MOTORS"],
    
    # Energy, Infra & Metals
    "RELIANCE": ["RELIANCE", "RIL", "RELIANCE INDUSTRIES"],
    "LT": ["L&T", "LARSEN", "LNT", "LARSEN & TOUBRO"],
    "BHEL": ["BHEL", "BHARAT HEAVY"],
    "SAIL": ["SAIL", "STEEL AUTHORITY"],
    "ONGC": ["ONGC"], "NTPC": ["NTPC"], "POWERGRID": ["POWERGRID", "POWER GRID"],
    "TATAPOWER": ["TATA POWER", "TATAPOWER"],
    "TATASTEEL": ["TATA STEEL", "TATASTEEL"],
    "HINDALCO": ["HINDALCO"], "JSWSTEEL": ["JSW", "JSWSTEEL"], "VEDL": ["VEDANTA", "VEDL"],
    
    # FMCG & Others (અઘરા નામો)
    "MCDOWELL-N": ["UNITED SPIRIT", "UNITED SPIRITS", "USL", "MCDOWELL", "MCDOWELL-N"], 
    "JCHAC": ["HITACHI", "JOHNSON CONTROLS", "HITACHI AC", "JCHAC"], 
    "HITACHIEGY": ["HITACHI ENERGY", "POWERGRID HITACHI"],
    "TATACONSUM": ["TATA CONSUMER", "TATACONSUMER", "TATA TEA"],
    "SUNPHARMA": ["SUN PHARMA", "SUNPHARMA", "SUN"],
    "ITC": ["ITC"], "ZOMATO": ["ZOMATO"], "BRITANNIA": ["BRITANNIA"],
    "DABUR": ["DABUR"], "NMDC": ["NMDC"],
    
    # Crypto
    "BTC-USD": ["BTC", "BITCOIN", "BIT COIN"],
    "ETH-USD": ["ETH", "ETHEREUM"],
    "SOL-USD": ["SOL", "SOLANA"],
    "BNB-USD": ["BNB", "BINANCE"],
    "XRP-USD": ["XRP", "RIPPLE"]
}

def get_smart_symbol(query):
    query = query.strip().upper()
    if query in FO_MASTER_LIST.keys(): return query
    
    clean_query = query.replace(" ", "").replace("-", "").replace("&", "")
    for symbol, aliases in FO_MASTER_LIST.items():
        for alias in aliases:
            clean_alias = alias.replace(" ", "").replace("-", "").replace("&", "")
            if clean_query == clean_alias or clean_query in clean_alias or clean_alias in clean_query:
                return symbol
    return query

# ==========================================
# ૩. ગ્લાસ UI સ્ટાઈલ
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Roboto+Mono:wght@400;700&display=swap');
    
    div[data-stale="true"] { opacity: 1 !important; filter: none !important; transition: none !important; }
    [data-testid="stSkeleton"], .stSpinner { display: none !important; }
    * { transition: none !important; }
    
    .stApp { background: radial-gradient(circle at 50% 0%, #1a1a1a 0%, #000000 70%); }
    [data-testid="stSidebar"] { background-color: rgba(10, 10, 10, 0.9) !important; border-right: 1px solid #d4af37; backdrop-filter: blur(10px); }
    
    .abnv-logo { font-family: 'Orbitron', sans-serif; font-size: 3em; font-weight: 900; text-align: center; background: linear-gradient(135deg, #d4af37, #fff4cc, #d4af37); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0px 0px 20px rgba(212, 175, 55, 0.4); letter-spacing: 5px; margin-bottom: 0px; line-height: 1.2; }
    .abnv-sub { color: #888; font-family: 'Orbitron', sans-serif; font-size: 0.8em; text-align: center; letter-spacing: 8px; margin-bottom: 20px; text-transform: uppercase; }
    
    .founders-badge { background: linear-gradient(90deg, rgba(212,175,55,0.1) 0%, rgba(212,175,55,0.2) 50%, rgba(212,175,55,0.1) 100%); border-top: 1px solid rgba(212,175,55,0.5); border-bottom: 1px solid rgba(212,175,55,0.5); padding: 15px 5px; text-align: center; margin-bottom: 20px; }
    .founders-badge p { margin: 0; color: #aaa; font-size: 0.8em; text-transform: uppercase; letter-spacing: 2px; }
    .founders-badge h3 { font-family: 'Orbitron', sans-serif; color: #d4af37 !important; margin: 5px 0 0 0; font-size: 1.1em; font-weight: bold; text-shadow: 0 0 10px rgba(212,175,55,0.3); }
    
    .glass-card { background: rgba(20, 20, 20, 0.6); backdrop-filter: blur(8px); border: 1px solid rgba(212, 175, 55, 0.2); border-radius: 12px; padding: 10px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5); }
    
    .scan-card { background: rgba(0, 255, 0, 0.05); border: 1px solid #00ff00; border-radius: 10px; padding: 15px; margin-bottom: 20px; box-shadow: 0 0 15px rgba(0,255,0,0.1); }
    .scan-title { font-family: 'Orbitron', sans-serif; color: #00ff00; font-size: 1.5em; font-weight: bold; margin-bottom: 5px; border-bottom: 1px solid rgba(0,255,0,0.3); padding-bottom: 5px; }
    .scan-alias { font-family: 'Roboto Mono', sans-serif; font-size: 0.8em; color: #d4af37; margin-bottom: 15px; }
    .scan-data { font-family: 'Roboto Mono', sans-serif; color: #fff; font-size: 1em; display: flex; justify-content: space-between; margin-bottom: 5px; }
    .scan-data span { color: #888; }
    
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
# ૪. એડવાન્સ માર્કેટ એન્જિન
# ==========================================
def get_terminal_data(original_query):
    try:
        # સ્માર્ટ એન્જિનથી સાચો સિમ્બોલ લાવો
        ticker = get_smart_symbol(original_query)
        raw_symbol = ticker 
        
        if not ticker.endswith('.NS') and not ticker.startswith('^') and not ticker.endswith('-USD'): 
            ticker += '.NS'
            
        t = yf.Ticker(ticker)
        df = t.history(period="3mo", interval="1d")
        if df.empty or len(df) < 30: return None
        
        last = df.iloc[-1]
        prev_close = df.iloc[-2]['Close']
        ema20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        delta = df['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        rsi = 100 - (100 / (1 + rs))
        current_rsi = round(rsi.iloc[-1], 2)
        
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_bullish = macd.iloc[-1] > signal.iloc[-1]
        
        if last['Close'] > ema20 and current_rsi < 70 and macd_bullish: act, cls = "BUY", "buy"
        elif last['Close'] < ema20 and current_rsi > 30 and not macd_bullish: act, cls = "SELL", "sell"
        else: act, cls = "NEUTRAL", "neutral"
        
        trend_class = "t-up" if last['Close'] >= prev_close else "t-down"
        arrow = "▲" if last['Close'] >= prev_close else "▼"
        currency = "$" if "-USD" in ticker else "₹"
        
        return {
            "Symbol": raw_symbol,
            "Query": original_query.upper(), # 💡 યુઝરે શું લખ્યું હતું તે યાદ રાખવા
            "Price": round(last['Close'], 2),
            "Signal": act, "Class": cls, "Trend_Class": trend_class, "Arrow": arrow, "Currency": currency,
            "RSI": current_rsi, "MACD": "Bullish" if macd_bullish else "Bearish"
        }
    except: return None

# ==========================================
# ૫. ડેશબોર્ડ લેઆઉટ
# ==========================================

with st.sidebar:
    st.markdown("""<div class="abnv-logo">ABNV</div><div class="abnv-sub">Trading Terminal</div>""", unsafe_allow_html=True)
    st.markdown("""<div class="founders-badge"><p>Developed & Managed By</p><h3>NILESH SHAH</h3><h3>VASVI SENGUPTA</h3></div>""", unsafe_allow_html=True)
    st.markdown("<div class='live-badge'>🟢 SMART ENGINE <br><small>10 SEC SYNC | AI ALIAS</small></div>", unsafe_allow_html=True)

left, right = st.columns([2, 1])

@st.fragment(run_every=10)
def live_market_board():
    global live_context_data 
    live_context_data = []
    
    nifty = get_terminal_data('^NSEI')
    banknifty = get_terminal_data('^NSEBANK')
    btc = get_terminal_data('BTC-USD')

    ticker_html = "<div class='ticker-wrap'><div class='ticker'>"
    if nifty: ticker_html += f"<div class='ticker-item'><span class='t-title'>NIFTY:</span> <span class='{nifty['Trend_Class']}'>₹{nifty['Price']} {nifty['Arrow']}</span></div>"
    if banknifty: ticker_html += f"<div class='ticker-item'><span class='t-title'>BANK NIFTY:</span> <span class='{banknifty['Trend_Class']}'>₹{banknifty['Price']} {banknifty['Arrow']}</span></div>"
    if btc: ticker_html += f"<div class='ticker-item'><span class='t-crypto'>BITCOIN:</span> <span class='{btc['Trend_Class']}'>${btc['Price']} {btc['Arrow']}</span></div>"
    ticker_html += "</div></div>"
    st.markdown(ticker_html, unsafe_allow_html=True)

    fo_sectors = {
        "IT": ['INFY', 'TCS', 'WIPRO', 'HCLTECH', 'TECHM'],
        "BANKING": ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK'],
        "AUTO": ['TATAMOTORS', 'M&M', 'MARUTI', 'BAJAJ-AUTO', 'FORCEMOT'],
        "ENERGY": ['RELIANCE', 'ONGC', 'NTPC', 'POWERGRID', 'TATAPOWER'],
        "FMCG": ['ITC', 'BRITANNIA', 'TATACONSUM', 'DABUR'],
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
                live_context_data.append(f"{d['Symbol']}: {d['Price']} ({d['Signal']}, RSI:{d['RSI']})")
                rows_html += f"<tr><td style='color:#ffffff; font-weight:bold;'>{d['Symbol']}</td><td>{d['Currency']}{d['Price']}</td><td><span class='action-badge {d['Class']}'>{d['Signal']}</span></td></tr>"
        
        summary_html = f"<span class='sector-summary'>(કુલ: {total}) | <span class='s-buy'>B: {buy_count}</span> | <span class='s-sell'>S: {sell_count}</span></span>"
        header_class = "crypto-header" if is_crypto else "sector-header"
        
        html = f"<div class='glass-card'><table class='f-o-table'><thead><tr><th colspan='3' class='{header_class}'>{sector_name} {summary_html}</th></tr></thead><tbody>"
        html += rows_html + "</tbody></table></div>"
        return html

    sectors = list(fo_sectors.items())
    half = len(sectors) // 2
    grid_html = "<div class='radar-grid'><div>"
    for name, stocks in sectors[:half]: grid_html += build_table(name, stocks)
    grid_html += "</div><div>"
    for name, stocks in sectors[half:]: grid_html += build_table(name, stocks)
    grid_html += "</div></div>"
    st.markdown(grid_html, unsafe_allow_html=True)
    
    crypto_list = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
    st.markdown(build_table("HIGH VOLUME CRYPTO (24x7)", crypto_list, is_crypto=True), unsafe_allow_html=True)

with left:
    live_market_board()

# --- જમણી બાજુ: સ્માર્ટ સ્કેનર અને કમાન્ડ બોટ ---
with right:
    st.markdown("<h4 style='font-family: Orbitron; color: #00ff00; margin-bottom: 5px;'>🔍 F&O SMART SCAN</h4>", unsafe_allow_html=True)
    scan_target = st.text_input("કોઈ પણ નામ લખો (દા.ત. hitachi, united spirit)", placeholder="Type full or partial name...")
    
    if scan_target:
        with st.spinner(f"AI is hunting for '{scan_target}'..."):
            scan_data = get_terminal_data(scan_target)
            if scan_data:
                card_color = "rgba(0,255,0,0.1)" if scan_data['Signal'] == 'BUY' else "rgba(255,0,0,0.1)" if scan_data['Signal'] == 'SELL' else "rgba(100,100,100,0.1)"
                border_color = "#00ff00" if scan_data['Signal'] == 'BUY' else "#ff0000" if scan_data['Signal'] == 'SELL' else "#888"
                
                # 💡 જો યુઝરનું નામ અને ઓરિજિનલ સિમ્બોલ અલગ હોય તો AI બતાવશે કે તેણે શું શોધી કાઢ્યું!
                alias_text = f"AI Auto-Detected: {scan_data['Symbol']}" if scan_data['Symbol'] != scan_data['Query'] else ""
                
                st.markdown(f"""
                <div class='scan-card' style='background: {card_color}; border-color: {border_color};'>
                    <div class='scan-title'>{scan_data['Symbol']} <span style='float:right;'>{scan_data['Currency']}{scan_data['Price']}</span></div>
                    <div class='scan-alias'>{alias_text}</div>
                    <div class='scan-data'><span>RSI (14 Days):</span> <b style='color:{"#ff4b4b" if scan_data["RSI"]>70 else "#00ff00" if scan_data["RSI"]<30 else "#fff"}'>{scan_data["RSI"]}</b></div>
                    <div class='scan-data'><span>MACD Trend:</span> <b>{scan_data["MACD"]}</b></div>
                    <div class='scan-data'><span>System Signal:</span> <span class='action-badge {scan_data["Class"]}'>{scan_data["Signal"]}</span></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"માફ કરજો, '{scan_target}' નામનો કોઈ સ્ટોક મળ્યો નથી. સાચો સ્પેલિંગ લખવા વિનંતી.")
    
    st.markdown("<br><h4 style='font-family: Orbitron; color: #d4af37; margin-bottom: 10px;'>🤖 ABNV COMMAND CORE</h4>", unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_box = st.container(height=450) 
    for m in st.session_state.messages[-10:]:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if pr := st.chat_input("ટાર્ગેટ પૂછો..."):
        st.session_state.messages.append({"role": "user", "content": pr})
        with chat_box.chat_message("user"): st.markdown(pr)
        
        with chat_box.chat_message("assistant"):
            try:
                memory_string = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-4:]])
                market_status = " | ".join(live_context_data) if 'live_context_data' in globals() else "લોડિંગ..."
                
                ai_prompt = f"""
                માલિક: નિલેશ શાહ અને વાસવી સેનગુપ્તા. 
                કંપની: ABNV. 
                માર્કેટ ડેટા: {market_status}
                તમારે એકદમ દેશી, ટૂંકો અને સીધો જવાબ આપવાનો છે. માત્ર 1 જ લાઈનમાં.
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