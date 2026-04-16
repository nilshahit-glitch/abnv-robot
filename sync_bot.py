import subprocess
import time

print("="*50)
print("🚀 ABNV PRO: GITHUB AUTO-SYNC ENGINE")
print("="*50)

def run_command(cmd, step_name):
    print(f"⏳ {step_name}...")
    # ટર્મિનલનો કમાન્ડ બેકગ્રાઉન્ડમાં ચલાવો
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # જો કોઈ એરર આવે તો બતાવો
    if result.returncode != 0 and "nothing to commit" not in result.stdout:
        print(f"❌ એરર આવી:\n{result.stderr}")
        return False
    return True

time.sleep(1)

# ૧. નવી ફાઈલો સ્કેન કરવી (git add)
if run_command("git add .", "૧. ફોલ્ડરની બધી નવી ફાઈલો સ્કેન કરી રહ્યા છીએ"):
    
    # ૨. ફાઈલો પેક કરવી (git commit)
    if run_command('git commit -m "ABNV Pro AI Core Update"', "૨. બધી ફાઈલોને પેક કરી રહ્યા છીએ"):
        
        # ૩. ગિટહબ પર મોકલવી (git push)
        if run_command("git push origin main --force", "૩. ઓનલાઇન સર્વર (GitHub) પર અપલોડ કરી રહ્યા છીએ"):
            print("="*50)
            print("✅ 100% SUCCESS: તમારી બધી ફાઈલો GitHub પર લાઈવ અપડેટ થઈ ગઈ છે!")
            print("🌐 Streamlit સર્વર હવે જાતે જ નવું AI મગજ ડાઉનલોડ કરી લેશે (૨ મિનિટ રાહ જુઓ).")
            print("="*50)
        else:
            print("⚠️ અપલોડ ફેલ થયું. (કૃપા કરીને તમારું ઇન્ટરનેટ અને GitHub લિંક ચેક કરો)")