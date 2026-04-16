import yfinance as yf
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
import joblib

print("🚀 ABNV PRO ENGINE: Institutional Level ટ્રેનિંગ શરૂ થઈ રહી છે...")

# ૧. ડેટા ડાઉનલોડ (નવી અને ક્લીન મેથડ)
print("📊 હાઈ-ડેફિનેશન માર્કેટ ડેટા ફેચ થઈ રહ્યો છે...")
nifty = yf.Ticker("^NSEI")
df = nifty.history(period="10y") # ૧૦ વર્ષનો ક્લીન ડેટા

# ==========================================
# ૨. ADVANCED FEATURE ENGINEERING (The Secret Sauce)
# ==========================================
# અ. Log Returns (નોર્મલ ટકાવારી કરતા વધુ સચોટ ગણિત)
df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))

# બ. Volume Footprint Proxy (Smart Money Flow)
df['VPT'] = df['Volume'] * df['Log_Return']
df['VPT_EMA'] = df['VPT'].ewm(span=21, adjust=False).mean()

# ક. Volatility Regime (માર્કેટમાં શાંતિ છે કે તોફાન?)
df['Vol_Short'] = df['Close'].rolling(window=5).std()
df['Vol_Long'] = df['Close'].rolling(window=21).std()
df['Volatility_Ratio'] = df['Vol_Short'] / df['Vol_Long']

# ડ. Momentum & Acceleration
df['Momentum_10'] = df['Close'] - df['Close'].shift(10)
df['Acceleration'] = df['Momentum_10'] - df['Momentum_10'].shift(10)

# ટાર્ગેટ: પ્રોફેશનલ ફંડ મેનેજર માત્ર મોટો ટ્રેન્ડ પકડે છે
# જો આવતા 3 દિવસમાં ભાવ 0.5% થી વધુ વધે તો જ 1 (BUY)
future_return = (df['Close'].shift(-3) - df['Close']) / df['Close'] * 100
df['Target'] = np.where(future_return > 0.5, 1, 0)
df.dropna(inplace=True)

# ૩. ડેટા પ્રોસેસિંગ (Outliers હટાવવા માટે RobustScaler)
features = ['Log_Return', 'VPT_EMA', 'Volatility_Ratio', 'Momentum_10', 'Acceleration']
X = df[features].values
y = df['Target'].values

# પ્રોફેશનલ સ્કેલિંગ 
scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)
joblib.dump(scaler, 'abnv_pro_scaler.pkl')

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, shuffle=False)

# ==========================================
# ૪. મોડેલ 1: Advanced KNN (Lorentzian Distance Approximation)
# ==========================================
print("🧠 મોડેલ 1: Lorentzian-Style KNN ટ્રેન થઈ રહ્યું છે...")
knn_model = KNeighborsClassifier(n_neighbors=8, metric='minkowski', p=1.5, weights='distance')
knn_model.fit(X_train, y_train)

joblib.dump(knn_model, 'abnv_pro_knn.pkl')
print("✅ Advanced KNN મોડેલ સેવ થઈ ગયું! (abnv_pro_knn.pkl)")

# ==========================================
# ૫. મોડેલ 2: XGBoost Pro (Complex Non-linear Patterns)
# ==========================================
print("🧠 મોડેલ 2: Institutional XGBoost ટ્રેન થઈ રહ્યું છે...")
xgb_model = xgb.XGBClassifier(
    n_estimators=300, 
    learning_rate=0.01, 
    max_depth=7, 
    subsample=0.8, 
    colsample_bytree=0.8, 
    random_state=42
)
xgb_model.fit(X_train, y_train)

joblib.dump(xgb_model, 'abnv_pro_xgb.pkl')
print("✅ Pro XGBoost મોડેલ સેવ થઈ ગયું! (abnv_pro_xgb.pkl)")

print("\n🏆 મિશન કમ્પ્લીટ! ક્લાયન્ટ લેવલના પાવરફુલ AI મોડેલ્સ તૈયાર છે.")
