import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objects as go
from dotenv import load_dotenv
from google import genai
import joblib
import numpy as np

# ==========================================
# ૧. સિસ્ટમ સેટઅપ
# ==========================================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

st.set_page_config(page_title="ABNV BOT TERMINAL | V7.0", layout="wide")

# ==========================================
# ૨. MASTER AI DICTIONARY (ફક્ત ડેશબોર્ડ માટે)
# ==========================================
FO_MASTER_LIST = {
    "^NSEI": ["NIFTY", "NIFTY 50", "NIFTY50", "નિફ્ટી", "નિફ્ટી 50"],
    "^NSEBANK": ["BANKNIFTY", "BANK NIFTY", "બેંક નિફ્ટી", "બેંકનિફ્ટી"],
    "HCLTECH": ["HCL", "HCL TECH", "HCLTECHNOLOGY", "એચસીએલ", "એચ સી એલ"],
    "INFY": ["INFY", "INFOSYS", "ઇન્ફોસીસ", "ઇન્ફોસિસ"],
    "TCS": ["TCS", "TATA CONSULTANCY", "ટીસીએસ", "ટાટા કન્સલ્ટન્સી"],
    "TECHM": ["TECH MAHINDRA", "TECHM", "ટેક મહિન્દ્રા"],
    "WIPRO": ["WIPRO", "વિપ્રો"],
    "HDFCBANK": ["HDFC", "HDFCBANK", "HDFC BANK", "એચડીએફસી", "એચ ડી એફ સી બેંક"],
    "ICICIBANK": ["ICICI", "ICICIBANK", "ICICI BANK", "આઈસીઆઈસીઆઈ"],
    "SBIN": ["SBI", "SBIN", "STATE BANK", "એસબીઆઈ", "સ્ટેટ બેંક"],
    "BAJFINANCE": ["BAJAJ FINANCE", "BAJFIN", "બજાજ ફાઇનાન્સ"],
    "AXISBANK": ["AXIS", "AXISBANK", "AXIS BANK", "એક્સિસ બેંક", "એક્સીસ"],
    "KOTAKBANK": ["KOTAK", "KOTAKBANK", "કોટક"],
    "EICHERMOT": ["EICHERMOT", "EICHER MOTORS", "આઈશર", "આયશર મોટર્સ"],
    "M&M": ["M&M", "MAHINDRA", "MAHINDRA & MAHINDRA", "MNM", "મહિન્દ્રા"],
    "MARUTI": ["MARUTI", "MARUTI SUZUKI", "મારુતિ", "મારુતી"],
    "BAJAJ-AUTO": ["BAJAJ AUTO", "BAJAJ-AUTO", "BAJAJAUTO", "બજાજ ઓટો"],
    "FORCEMOT": ["FORCE", "FORCEMOTOR", "FORCE MOTORS", "ફોર્સ મોટર્સ"],
    "RELIANCE": ["RELIANCE", "RIL", "RELIANCE INDUSTRIES", "રિલાયન્સ"],
    "LT": ["L&T", "LARSEN", "LNT", "LARSEN & TOUBRO", "એલ એન્ડ ટી", "લાર્સન"], 
    "ONGC": ["ONGC", "ઓએનજીસી"], 
    "NTPC": ["NTPC", "એનટીપીસી"], 
    "POWERGRID": ["POWERGRID", "POWER GRID", "પાવરગ્રીડ"],
    "TATAPOWER": ["TATA POWER", "TATAPOWER", "ટાટા પાવર"],
    "TATASTEEL": ["TATA STEEL", "TATASTEEL", "ટાટા સ્ટીલ"],
    "HINDALCO": ["HINDALCO", "હિન્દાલ્કો"], 
    "JSWSTEEL": ["JSW", "JSWSTEEL", "જેએસડબલ્યુ"], 
    "VEDL": ["VEDANTA", "VEDL", "વેદાન્તા"],
    "NMDC": ["NMDC", "એનએમડીસી"], 
    "ITC": ["ITC", "આઈટીસી"], 
    "BRITANNIA": ["BRITANNIA", "બ્રિટાનિયા"],
    "TATACONSUM": ["TATA CONSUMER", "TATACONSUMER", "TATA TEA", "ટાટા કન્ઝ્યુમર"],
    "DABUR": ["DABUR", "ડાબર"], 
    "HINDUNILVR": ["HUL", "HINDUSTAN UNILEVER", "UNILEVER", "હિન્દુસ્તાન યુનિલિવર", "એચયુએલ"],
    "UNITDSPR": ["UNITED SPIRIT", "UNITED SPIRITS", "USL", "MCDOWELL", "MCDOWELL-N", "યુનાઇટેડ સ્પિરિટ", "મેકડોવેલ"],
    "ZYDUSLIFE": ["ZYDUS", "ZYDUSLIFE", "CADILA", "ઝાયડસ", "કેડિલા"],
    "BTC-USD": ["BTC", "BITCOIN", "BIT COIN", "બિટકોઇન", "બીટકોઈન"],
    "ETH-USD": ["ETH", "ETHEREUM", "ઇથેરિયમ"],
    "SOL-USD": ["SOL", "SOLANA", "સોલાના"],
    "BNB-USD": ["BNB", "BINANCE", "બાઇનાન્સ"],
    "XRP-USD": ["XRP", "RIPPLE", "રિપલ"]
}

# ==========================================
# ૩. TRUE HYBRID SEARCH LOGIC (Old Logic + AI)
# ==========================================
def get_smart_symbol(query):
    query = query.strip().upper()
    if not query: return ""
    
    if query in FO_MASTER_LIST: return query
    for symbol, aliases in FO_MASTER_LIST.items():
        if query in [a.upper() for a in aliases]: return symbol
            
    clean_query = query.replace(" ", "").replace("-", "").replace("&", "")
    for symbol, aliases in FO_MASTER_LIST.items():
        if clean_query == symbol.replace("-", ""): return symbol
        for alias in aliases:
            if clean_query == alias.replace(" ", "").replace("-", "").replace("&", ""):
                return symbol
                
    if len(clean_query) >= 3:
        for symbol, aliases in FO_MASTER_LIST.items():
            if symbol.replace("-", "").startswith(clean_query): return symbol
            for alias in aliases:
                if alias.replace(" ", "").replace("-", "").replace("&", "").startswith(clean_query):
                    return symbol

    for symbol, aliases in FO_MASTER_LIST.items():
        for alias in aliases:
            if query in alias.split(): return symbol

    try:
        ai_prompt = f"Find the official Yahoo Finance NSE ticker symbol for the Indian stock query: '{query}'. Return ONLY the ticker symbol without '.NS'. For example, if query is 'ટાટા મોટર્સ', return TATAMOTORS. If 'hul', return HINDUNILVR. Return only the exact word."
        res = client.models.generate_content(model="gemini-3.1-flash-lite-preview", contents=ai_prompt)
        if res and res.text:
            return res.text.strip().upper().replace(".NS", "")
    except:
        pass

    return query

# ==========================================
# ૩.૧ SMART CHARTING & ML ENGINE (NEW ✨)
# ==========================================
def create_interactive_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"
    )])
    # EMA 20 Indicator
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'].ewm(span=20, adjust=False).mean(), 
                             line=dict(color='#d4af37', width=1.5), name='EMA 20'))
    fig.update_layout(
        template="plotly_dark", title=f"📊 LIVE CHART: {symbol}", yaxis_title="Price",
        xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Orbitron", size=10, color="#d4af37"), height=350, margin=dict(l=0, r=0, t=30, b=0)
    )
    return fig

# ==========================================
# ૩.૨ PRO ML PREDICTION ENGINE (Smart Money + Non-Linear)
# ==========================================
# ==========================================
# ૩.૨ PRO ML PREDICTION ENGINE (Dynamic ML Targets)
# ==========================================
def get_ml_prediction(df):
    try:
        scaler = joblib.load('abnv_pro_scaler.pkl')
        knn_model = joblib.load('abnv_pro_knn.pkl')
        xgb_model = joblib.load('abnv_pro_xgb.pkl')
        
        df = df.copy()
        df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
        df['VPT'] = df['Volume'] * df['Log_Return']
        df['VPT_EMA'] = df['VPT'].ewm(span=21, adjust=False).mean()
        
        df['Vol_Short'] = df['Close'].rolling(window=5).std()
        df['Vol_Long'] = df['Close'].rolling(window=21).std()
        df['Volatility_Ratio'] = df['Vol_Short'] / df['Vol_Long']
        
        df['Momentum_10'] = df['Close'] - df['Close'].shift(10)
        df['Acceleration'] = df['Momentum_10'] - df['Momentum_10'].shift(10)
        
        # 🧠 નવું: ATR (વોલેટિલિટી માપવા માટે)
        df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
        
        latest_row = df.iloc[-1]
        latest_data = latest_row[['Log_Return', 'VPT_EMA', 'Volatility_Ratio', 'Momentum_10', 'Acceleration']].values.reshape(1, -1)
        
        if np.isnan(latest_data).any():
            return "PRO AI: WAITING ⏳", "Processing Deep Market Data...", "#888888", 0, 0
            
        latest_scaled = scaler.transform(latest_data)
        knn_pred = knn_model.predict(latest_scaled)[0]
        xgb_pred = xgb_model.predict(latest_scaled)[0]
        
        # 🎯 મશીન લર્નિંગ ડાયનેમિક ટાર્ગેટ અને SL ની ગણતરી
        xgb_proba = xgb_model.predict_proba(latest_scaled)[0]
        confidence = max(xgb_proba) # મોડેલ કેટલું સ્યોર છે? (દા.ત. 0.85 એટલે 85%)
        
        current_price = latest_row['Close']
        atr = latest_row['ATR'] if not pd.isna(latest_row['ATR']) else (current_price * 0.015)
        
        # લોજિક: મોડેલ વધુ સ્યોર હોય અને માર્કેટ ફાસ્ટ હોય, તો ટાર્ગેટ મોટો મળશે
        ml_target_dist = atr * (confidence * 3.5) * latest_row['Volatility_Ratio']
        ml_sl_dist = atr * 1.5
        
        if knn_pred == 1 and xgb_pred == 1:
            sig, msg, col = "PRO AI: STRONG BUY 🚀", f"ML Conf: {int(confidence*100)}% (Vol+Mom)", "#00ff00"
            tg, sl = current_price + ml_target_dist, current_price - ml_sl_dist
        elif knn_pred == 0 and xgb_pred == 0:
            sig, msg, col = "PRO AI: STRONG SELL 🔻", f"ML Conf: {int(confidence*100)}% (Dist)", "#ff0000"
            tg, sl = current_price - ml_target_dist, current_price + ml_sl_dist
        elif knn_pred == 1 and xgb_pred == 0:
            sig, msg, col = "PRO AI: ACCUMULATION 🔼", "KNN Bullish Base", "#d4af37"
            tg, sl = current_price + (ml_target_dist*0.5), current_price - ml_sl_dist
        else:
            sig, msg, col = "PRO AI: WEAK SELL 🔽", "XGB Bearish Pressure", "#ff8800"
            tg, sl = current_price - (ml_target_dist*0.5), current_price + ml_sl_dist
            
        return sig, msg, col, round(tg, 2), round(sl, 2) # હવે 5 વસ્તુઓ રિટર્ન કરશે
        
    except Exception as e:
        return "PRO AI SYSTEM OFFLINE", f"Error: {str(e)[:20]}", "#888888", 0, 0
    
# ==========================================
# ૩.૨ ગ્લાસ UI સ્ટાઈલ
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
    
    .scan-card { background: rgba(0, 255, 0, 0.05); border: 1px solid #00ff00; border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 0 15px rgba(0,255,0,0.1); }
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
    
    div[data-baseweb="input"] {
        background-color: rgba(20,20,20,0.8) !important;
        border: 1px solid rgba(212,175,55,0.5) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] input {
        color: #d4af37 !important; 
        font-family: 'Roboto Mono', sans-serif !important;
    }
    div[data-baseweb="input"] input::placeholder {
        color: #888888 !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.html(
    """
    <script>
    const inputs = window.parent.document.querySelectorAll('input[type=text]');
    for (let i = 0; i < inputs.length; i++) {
        inputs[i].setAttribute('spellcheck', 'false');
        inputs[i].setAttribute('autocorrect', 'off');
        inputs[i].setAttribute('autocapitalize', 'off');
        inputs[i].setAttribute('autocomplete', 'off');
    }
    </script>
    """
)

# ==========================================
# ૪. એડવાન્સ માર્કેટ એન્જિન
# ==========================================
def get_terminal_data(original_query):
    try:
        ticker = get_smart_symbol(original_query)
        raw_symbol = ticker 
        
        if not ticker.endswith('.NS') and not ticker.startswith('^') and not ticker.endswith('-USD'): 
            ticker += '.NS'
            
        t = yf.Ticker(ticker)
        df = t.history(period="3mo", interval="1d")
        
        # 🛠️ YAHOO BUG FIX: જો યાહૂ છેલ્લો ભાવ ખાલી (NaN) મોકલે, તો એ લાઈન કાઢી નાખો
        df = df.dropna(subset=['Close'])
        
        if df.empty or len(df) < 20: return None
        
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
            "Query": original_query, 
            "Price": round(last['Close'], 2),
            "Signal": act, "Class": cls, "Trend_Class": trend_class, "Arrow": arrow, "Currency": currency,
            "RSI": current_rsi, "MACD": "Bullish" if macd_bullish else "Bearish",
            "Data": df 
        }
    except: return None

# ==========================================
# ૫. ડેશબોર્ડ લેઆઉટ
# ==========================================

with st.sidebar:
    st.markdown("""<div class="abnv-logo">ABNV</div><div class="abnv-sub">Trading Terminal</div>""", unsafe_allow_html=True)
    st.markdown("""<div class="founders-badge"><p>Developed & Managed By</p><h3>NILESH SHAH</h3><h3>VASVI SENGUPTA</h3></div>""", unsafe_allow_html=True)
    st.markdown("<div class='live-badge'>🟢 TRUE AI SMART ENGINE <br><small>10 SEC SYNC | V7.0</small></div>", unsafe_allow_html=True)

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
        "IT": ["INFY", "TCS", "WIPRO", "HCLTECH", "TECHM"],
        "ENERGY": ["RELIANCE", "ONGC", "NTPC", "POWERGRID", "TATAPOWER"],
        "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
        "FMCG": ["ITC", "BRITANNIA", "TATACONSUM", "DABUR"],
        "AUTO": ["EICHERMOT", "M&M", "MARUTI", "BAJAJ-AUTO", "FORCEMOT"],
        "METALS": ["TATASTEEL", "HINDALCO", "JSWSTEEL", "VEDL", "NMDC"]
    }
    
    hot_buys = []
    hot_sells = []
    
    def build_table(sector_name, stocks, is_crypto=False):
        rows_html = ""
        buy_count, sell_count, total = 0, 0, 0
        for s in stocks:
            d = get_terminal_data(s)
            if d: 
                df = d['Data']
                sym = d['Symbol']
                cp = d['Price']
                ml_sig, ml_conf, ml_col, ml_tg, ml_sl = get_ml_prediction(df)
                
                # 🧠 DYNAMIC TARGET & SMART EXIT LOGIC 🧠
                if sym in st.session_state.active_trades:
                    trade = st.session_state.active_trades[sym]
                    ttype = trade['type']
                    
                    # ૧. ટાર્ગેટ અને કોન્ફિડન્સ લાઈવ અપડેટ કરો (SL ફિક્સ રહેશે)
                    trade['target'] = ml_tg
                    trade['conf'] = ml_conf
                    
                    # ૨. એક્ઝિટ ચેકિંગ (લક્ષ્ય, નુકસાન અથવા AI ની સલાહ)
                    if ttype == 'BUY':
                        if cp >= trade['target']:
                            st.session_state.trade_history.append({'symbol': sym, 'type': 'BUY', 'entry': trade['entry'], 'exit': cp, 'result': 'DYNAMIC TARGET 🎯', 'color': '#00ff00'})
                            del st.session_state.active_trades[sym]
                        elif cp <= trade['sl']:
                            st.session_state.trade_history.append({'symbol': sym, 'type': 'BUY', 'entry': trade['entry'], 'exit': cp, 'result': 'SL HIT 🔻', 'color': '#ff4b4b'})
                            del st.session_state.active_trades[sym]
                        elif "SELL" in ml_sig: # અચાનક માર્કેટ પડે તો AI જાતે કાપી નાખશે
                            st.session_state.trade_history.append({'symbol': sym, 'type': 'BUY', 'entry': trade['entry'], 'exit': cp, 'result': 'AI SMART EXIT 🧠', 'color': '#d4af37'})
                            del st.session_state.active_trades[sym]

                    elif ttype == 'SELL':
                        if cp <= trade['target']:
                            st.session_state.trade_history.append({'symbol': sym, 'type': 'SELL', 'entry': trade['entry'], 'exit': cp, 'result': 'DYNAMIC TARGET 🎯', 'color': '#00ff00'})
                            del st.session_state.active_trades[sym]
                        elif cp >= trade['sl']:
                            st.session_state.trade_history.append({'symbol': sym, 'type': 'SELL', 'entry': trade['entry'], 'exit': cp, 'result': 'SL HIT 🔻', 'color': '#ff4b4b'})
                            del st.session_state.active_trades[sym]
                        elif "BUY" in ml_sig: # અચાનક માર્કેટ વધે તો AI જાતે કાપી નાખશે
                            st.session_state.trade_history.append({'symbol': sym, 'type': 'SELL', 'entry': trade['entry'], 'exit': cp, 'result': 'AI SMART EXIT 🧠', 'color': '#d4af37'})
                            del st.session_state.active_trades[sym]

                is_active = sym in st.session_state.active_trades
                
                # ૩. નવી એન્ટ્રી
                if not is_active:
                    if "STRONG BUY" in ml_sig:
                        st.session_state.active_trades[sym] = {'type': 'BUY', 'entry': cp, 'target': ml_tg, 'sl': ml_sl, 'conf': ml_conf}
                        is_active = True
                    elif "STRONG SELL" in ml_sig:
                        st.session_state.active_trades[sym] = {'type': 'SELL', 'entry': cp, 'target': ml_tg, 'sl': ml_sl, 'conf': ml_conf}
                        is_active = True

                # ૪. ગ્રાફિક્સ માટે ડેટા સેટ કરો
                if is_active:
                    trade = st.session_state.active_trades[sym]
                    d['Entry'], d['SL'], d['Target'] = trade['entry'], trade['sl'], trade['target']
                    d['ML_Conf'] = trade['conf']
                    d['ML_Signal'] = f"🔴 LIVE {trade['type']}"
                    d['ML_Color'] = "#00ff00" if trade['type'] == 'BUY' else "#ff0000"
                    
                    if trade['type'] == 'BUY': hot_buys.append(d)
                    else: hot_sells.append(d)
                else:
                    d['Entry'], d['SL'], d['Target'] = cp, ml_sl, ml_tg
                    d['ML_Conf'] = ml_conf
                    d['ML_Signal'] = ml_sig.replace("PRO AI: ", "")
                    d['ML_Color'] = ml_col

                total += 1
                if "BUY" in ml_sig or (is_active and trade['type'] == 'BUY'): buy_count += 1
                elif "SELL" in ml_sig or (is_active and trade['type'] == 'SELL'): sell_count += 1
                    
                live_context_data.append(f"{sym}: {cp} ({d['ML_Signal']})")
                rows_html += f"<tr><td style='color:#ffffff; font-weight:bold;'>{sym}</td><td>{d['Currency']}{cp}</td><td><span style='color:{d['ML_Color']}; font-weight:bold; font-family: Orbitron; font-size:0.75em;'>{d['ML_Signal']}</span></td></tr>"
        
        summary_html = f"<span class='sector-summary'>(કુલ: {total}) | <span class='s-buy'>B: {buy_count}</span> | <span class='s-sell'>S: {sell_count}</span></span>"
        header_class = "crypto-header" if is_crypto else "sector-header"
        
        html = f"<div class='glass-card'><table class='f-o-table'><thead><tr><th colspan='3' class='{header_class}'>{sector_name} {summary_html}</th></tr></thead><tbody>{rows_html}</tbody></table></div>"
        return html

    sectors = list(fo_sectors.items())
    half = len(sectors) // 2
    
    grid_html_1, grid_html_2 = "", ""
    for name, stocks in sectors[:half]: grid_html_1 += build_table(name, stocks)
    for name, stocks in sectors[half:]: grid_html_2 += build_table(name, stocks)
    
    # 🎯 Action Radar (Update UI for Fixed SL and Dynamic Target)
    st.markdown("<h4 style='font-family: Orbitron; color: #fff; margin-bottom: 10px; border-bottom: 1px solid #444; padding-bottom: 5px;'>⚡ PRO AI ACTION RADAR</h4>", unsafe_allow_html=True)
    radar_html = "<div style='display: flex; gap: 10px; overflow-x: auto; padding-bottom: 15px; margin-bottom: 15px;'>"
    
    for b in hot_buys[:5]: 
        radar_html += f"<div style='min-width: 170px; background: linear-gradient(145deg, rgba(0,255,0,0.1), rgba(0,0,0,0.8)); border: 1px solid #00ff00; border-radius: 10px; padding: 10px; text-align: center; box-shadow: 0 4px 10px rgba(0,255,0,0.2);'><div style='font-family: Orbitron; font-weight: bold; color: #fff; font-size: 1.1em;'>{b['Symbol']}</div><div style='color: #00ff00; font-family: Roboto Mono; font-size: 1.2em; margin: 5px 0;'>₹{b['Price']}</div><div style='display:flex; justify-content:space-between; background:rgba(255,255,255,0.05); padding:5px; border-radius:5px; font-size:0.7em; margin-bottom:8px; font-family:Roboto Mono; border: 1px solid rgba(0,255,0,0.2);'><div style='color:#ccc;'><b>En:</b><br>{b['Entry']}</div><div style='color:#ff4b4b;'><b>SL🔒:</b><br>{b['SL']}</div><div style='color:#00ff00;'><b>Tg🔄:</b><br>{b['Target']}</div></div><div style='font-size: 0.7em; color: #888; margin-bottom: 5px;'>{b['ML_Conf']}</div><div style='background: {b['ML_Color']}; color: #000; font-family: Orbitron; font-weight: bold; font-size: 0.75em; padding: 4px; border-radius: 4px;'>{b['ML_Signal']}</div></div>"
        
    for s in hot_sells[:5]: 
        radar_html += f"<div style='min-width: 170px; background: linear-gradient(145deg, rgba(255,0,0,0.1), rgba(0,0,0,0.8)); border: 1px solid #ff0000; border-radius: 10px; padding: 10px; text-align: center; box-shadow: 0 4px 10px rgba(255,0,0,0.2);'><div style='font-family: Orbitron; font-weight: bold; color: #fff; font-size: 1.1em;'>{s['Symbol']}</div><div style='color: #ff4b4b; font-family: Roboto Mono; font-size: 1.2em; margin: 5px 0;'>₹{s['Price']}</div><div style='display:flex; justify-content:space-between; background:rgba(255,255,255,0.05); padding:5px; border-radius:5px; font-size:0.7em; margin-bottom:8px; font-family:Roboto Mono; border: 1px solid rgba(255,0,0,0.2);'><div style='color:#ccc;'><b>En:</b><br>{s['Entry']}</div><div style='color:#ff4b4b;'><b>SL🔒:</b><br>{s['SL']}</div><div style='color:#00ff00;'><b>Tg🔄:</b><br>{s['Target']}</div></div><div style='font-size: 0.7em; color: #888; margin-bottom: 5px;'>{s['ML_Conf']}</div><div style='background: {s['ML_Color']}; color: #fff; font-family: Orbitron; font-weight: bold; font-size: 0.75em; padding: 4px; border-radius: 4px;'>{s['ML_Signal']}</div></div>"
        
    if not hot_buys and not hot_sells: radar_html += "<div style='color: #888; padding: 10px;'>અત્યારે કોઈ લાઈવ ટ્રેડ એક્ટિવ નથી...</div>"
    radar_html += "</div>"
    st.markdown(radar_html, unsafe_allow_html=True)
    
    # 📊 Tables
    st.markdown(f"<div class='radar-grid'><div>{grid_html_1}</div><div>{grid_html_2}</div></div>", unsafe_allow_html=True)
    
    crypto_list = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
    st.markdown(build_table("HIGH VOLUME CRYPTO (24x7)", crypto_list, is_crypto=True), unsafe_allow_html=True)

    # 📜 TODAY'S TRADE BOOK
    if st.session_state.trade_history:
        st.markdown("<h4 style='font-family: Orbitron; color: #d4af37; margin-top: 25px; border-bottom: 1px solid #444; padding-bottom: 5px;'>📜 TODAY'S TRADE BOOK</h4>", unsafe_allow_html=True)
        tb_html = "<div class='glass-card'><table class='f-o-table' style='text-align: center; width: 100%;'><thead><tr><th style='text-align:center;'>STOCK</th><th style='text-align:center;'>TYPE</th><th style='text-align:center;'>ENTRY</th><th style='text-align:center;'>EXIT</th><th style='text-align:center;'>RESULT</th></tr></thead><tbody>"
        for th in reversed(st.session_state.trade_history): 
            tb_html += f"<tr><td style='font-weight:bold; color:#fff;'>{th['symbol']}</td><td>{th['type']}</td><td>₹{th['entry']}</td><td>₹{th['exit']}</td><td><span style='color:{th['color']}; font-weight:bold; font-family:Orbitron;'>{th['result']}</span></td></tr>"
        tb_html += "</tbody></table></div>"
        st.markdown(tb_html, unsafe_allow_html=True)

# ⚠️ ખાસ ધ્યાન: આ નીચેની લાઈનોમાં આગળ બિલકુલ જગ્યા (Space) નથી છોડવાની, તેને છેક ડાબી બાજુ અડાડીને જ રાખવાની છે.
with left:
    live_market_board()

# --- જમણી બાજુ: સ્માર્ટ સ્કેનર ---
with right:
    st.markdown("<h4 style='font-family: Orbitron; color: #00ff00; margin-bottom: 0px;'>🔍 F&O SMART SCAN</h4>", unsafe_allow_html=True)

# --- જમણી બાજુ: સ્માર્ટ સ્કેનર ---
with right:
    st.markdown("<h4 style='font-family: Orbitron; color: #00ff00; margin-bottom: 0px;'>🔍 F&O SMART SCAN</h4>", unsafe_allow_html=True)
with right:
    st.markdown("<h4 style='font-family: Orbitron; color: #00ff00; margin-bottom: 0px;'>🔍 F&O SMART SCAN</h4>", unsafe_allow_html=True)
    st.markdown("<p style='color: #d4af37; font-family: \"Roboto Mono\", sans-serif; font-size: 0.9em; margin-top: 5px; margin-bottom: 5px;'>શેર/સ્ટોકનું નામ લખો (દા.ત. રિલાયન્સ, zydus, sbi)</p>", unsafe_allow_html=True)
    
    scan_target = st.text_input("Hidden Label", placeholder="અંગ્રેજી કે ગુજરાતીમાં સ્ટોકનું નામ લખો...", label_visibility="collapsed")
    
    if scan_target:
        with st.spinner(f"AI is hunting for '{scan_target}'..."):
            scan_data = get_terminal_data(scan_target)
            if scan_data:
                # ૧. જૂનું સ્કેન કાર્ડ
                card_color = "rgba(0,255,0,0.1)" if scan_data['Signal'] == 'BUY' else "rgba(255,0,0,0.1)" if scan_data['Signal'] == 'SELL' else "rgba(100,100,100,0.1)"
                border_color = "#00ff00" if scan_data['Signal'] == 'BUY' else "#ff0000" if scan_data['Signal'] == 'SELL' else "#888"
                alias_text = f"Verified Target 🎯: {scan_data['Symbol']}" if scan_data['Symbol'] != scan_data['Query'].upper() else ""
                
                st.markdown(f"""
                <div class='scan-card' style='background: {card_color}; border-color: {border_color};'>
                    <div class='scan-title'>{scan_data['Symbol']} <span style='float:right;'>{scan_data['Currency']}{scan_data['Price']}</span></div>
                    <div class='scan-alias'>{alias_text}</div>
                    <div class='scan-data'><span>RSI (14 Days):</span> <b style='color:{"#ff4b4b" if scan_data["RSI"]>70 else "#00ff00" if scan_data["RSI"]<30 else "#fff"}'>{scan_data["RSI"]}</b></div>
                    <div class='scan-data'><span>MACD Trend:</span> <b>{scan_data["MACD"]}</b></div>
                    <div class='scan-data'><span>System Signal:</span> <span class='action-badge {scan_data["Class"]}'>{scan_data["Signal"]}</span></div>
                </div>
                """, unsafe_allow_html=True)
                
                # ૨. નવું ML પ્રેડિક્શન બેજ
                df = scan_data["Data"]
                ml_sig, ml_conf, ml_col = get_ml_prediction(df)
                st.markdown(f"""
                <div style='background:rgba(0,0,0,0.5); border: 1px solid {ml_col}; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px;'>
                    <span style='font-family: Orbitron; font-size: 1.1em; font-weight: bold; color: {ml_col};'>{ml_sig}</span><br>
                    <span style='font-family: Roboto Mono; font-size: 0.8em; color: #888;'>{ml_conf}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # ૩. ઇન્ટરેક્ટિવ ચાર્ટ
                st.plotly_chart(create_interactive_chart(df, scan_data['Symbol']), width='stretch')
                
            else:
                st.error(f"માફ કરજો, '{scan_target}' નો ડેટા મળ્યો નહિ. (કદાચ ABNV Finance સર્વર ડાઉન છે અથવા સ્પેલિંગ ખોટો છે).")
    
    st.markdown("<br><h4 style='font-family: Orbitron; color: #d4af37; margin-bottom: 10px;'>🤖 ABNV BOT CORE</h4>", unsafe_allow_html=True)
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
                કંપની: ABNV BOT. 
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