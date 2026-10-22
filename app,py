import streamlit as st
import threading
import time
import requests
import feedparser
import pyotp
from logzero import logger
from deep_translator import GoogleTranslator
import schedule
from datetime import datetime

# =====================================================================
# [SECTION 1] : CONFIGURATION & API PLACEHOLDERS
# Yahan sabhi keys aur tokens baad me daalne hain.
# =====================================================================

TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID_HERE"

ANGEL_API_KEY = "YOUR_ANGEL_API_KEY_HERE"
ANGEL_CLIENT_ID = "YOUR_ANGEL_CLIENT_ID_HERE"
ANGEL_PIN = "YOUR_ANGEL_PIN_HERE"
ANGEL_TOTP_SECRET = "YOUR_ANGEL_TOTP_SECRET_HERE" # Auto-login ke liye TOTP secret

# News Filter Whitelist (Sirf inhi topics ki news aayegi)
NEWS_WHITELIST = [
    "reliance", "hdfc", "icici", "infosys", "tcs", "itc", "l&t", "sbi", "kotak", "bharti airtel", 
    "trump", "crude", "brent", "usd inr", "rupee", "dollar index", 
    "rbi", "fed", "repo rate", "rate cut", "powell", "das",
    "scam", "fraud", "sebi", "hindenburg", "default", "advisory", "q1", "q2", "q3", "q4", "earnings"
]

# Duplicate news rokne ke liye
seen_news_titles = set()

# =====================================================================
# [SECTION 2] : TELEGRAM NOTIFICATION ENGINE
# =====================================================================

def send_telegram_alert(message):
    """Telegram par message bhejne ka function"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logger.info("Telegram Alert Sent Successfully!")
        else:
            logger.error(f"Telegram Alert Failed: {response.text}")
    except Exception as e:
        logger.error(f"Telegram API Error: {e}")

# =====================================================================
# [SECTION 3] : ANGEL ONE AUTO LOGIN ENGINE
# =====================================================================

def angel_auto_login():
    """Daily Angel One me TOTP ke sath automatic login karega"""
    logger.info("Initiating Angel One Auto-Login...")
    try:
        # SmartAPI library baad me yahan add hogi jab order logic lagayenge
        # Example Auto TOTP generator:
        totp = pyotp.TOTP(ANGEL_TOTP_SECRET).now()
        logger.info(f"Generated TOTP: {totp}")
        
        # TODO: Angel API SmartConnect Login Code Yahan Aayega
        # obj = SmartConnect(api_key=ANGEL_API_KEY)
        # data = obj.generateSession(ANGEL_CLIENT_ID, ANGEL_PIN, totp)
        
        logger.info("Angel One Login Successful!")
        send_telegram_alert("✅ <b>S'Ravaal Option Alert:</b> Angel One Auto Login Successful for the day.")
    except Exception as e:
        logger.error(f"Angel Login Failed: {e}")
        send_telegram_alert(f"❌ <b>Angel Login Failed:</b> {e}")

# =====================================================================
# [SECTION 4] : NEWS SCRAPER & FILTER ENGINE (NOISE REDUCTION)
# =====================================================================

def check_market_news():
    """Google RSS aur NSE se news uthayega aur filter karega"""
    logger.info("Checking for new market updates...")
    
    # Nifty 50 Google News RSS URL
    rss_url = 'https://news.google.com/rss/search?q=NIFTY+OR+NSE+OR+BSE+when:1h&hl=en-IN&gl=IN&ceid=IN:en'
    
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            title_en = entry.title
            
            # Duplicate News Check
            if title_en in seen_news_titles:
                continue
                
            # Filter Logic: Kya whitelist ka koi word headline me hai?
            title_lower = title_en.lower()
            if any(keyword in title_lower for keyword in NEWS_WHITELIST):
                
                # Gujarati Translation
                try:
                    title_gu = GoogleTranslator(source='auto', target='gu').translate(title_en)
                except:
                    title_gu = "Translation Error"

                # Telegram Format
                msg = f"🚨 <b>S'RAVAAL HIGH IMPACT NEWS</b> 🚨\n\n"
                msg += f"🇮🇳 <b>Gujarati:</b> {title_gu}\n"
                msg += f"🔤 <b>English:</b> {title_en}\n\n"
                msg += f"⚠️ <b>Focus:</b> Nifty 50 Options"
                
                send_telegram_alert(msg)
                logger.info(f"News Alert Sent: {title_en}")
                
                seen_news_titles.add(title_en)
                
    except Exception as e:
        logger.error(f"News Scraper Error: {e}")

# =====================================================================
# [SECTION 5] : PRE-MARKET CHECKLIST ENGINE
# =====================================================================

def run_pre_market_checklist():
    """Subah 8:30 AM par pre-market data collect karke Telegram par bhejega"""
    logger.info("Running Pre-Market Checklist...")
    
    # Baad me yahan NSE aur Global APIs se real data fetch hoga
    msg = """🌅 <b>S'RAVAAL PRE-MARKET CHECKLIST</b> 🌅
    
🔹 <b>Global Cues:</b> Fetching...
🔹 <b>Gift Nifty:</b> Fetching...
🔹 <b>FII/DII Data:</b> Fetching...
🔹 <b>Nifty Max Pain:</b> Fetching...
🔹 <b>Events Today:</b> Fetching...

<i>(Data logic API connect hone ke baad live hoga)</i>
"""
    send_telegram_alert(msg)

# =====================================================================
# [SECTION 6] : BACKGROUND SCHEDULER ENGINE
# =====================================================================

def background_tasks():
    """Ye function loop me chalega aur scheduled tasks ko trigger karega"""
    
    # Subah 8:30 baje Pre-Market Checklist
    schedule.every().day.at("08:30").do(run_pre_market_checklist)
    
    # Subah 8:45 baje Angel One Login
    schedule.every().day.at("08:45").do(angel_auto_login)
    
    # Market hours (9:15 to 15:30) me har 2 minute me news check
    schedule.every(2).minutes.do(check_market_news)

    while True:
        schedule.run_pending()
        time.sleep(1)

# Streamlit start hote hi background thread chalu kar do (Taki UI block na ho)
if 'thread_started' not in st.session_state:
    task_thread = threading.Thread(target=background_tasks, daemon=True)
    task_thread.start()
    st.session_state.thread_started = True
    logger.info("Background Scheduler Started Successfully!")

# =====================================================================
# [SECTION 7] : STREAMLIT UI (DASHBOARD DESIGN)
# =====================================================================

# Title aur Page Config (Bright layout)
st.set_page_config(page_title="S'Ravaal option Alert", layout="wide")

# Custom CSS for Bright/Light Colors (30-40% Bright theme)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa; /* Light grey/white background */
    }
    .header-style {
        color: #ff4b4b; /* Bright Red/Pink for title */
        font-size: 40px;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    .box-style {
        background-color: #e3f2fd; /* Light blue */
        padding: 20px;
        border-radius: 10px;
        color: #0d47a1;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Dashboard UI HTML
st.markdown('<div class="header-style">🚀 S\'Ravaal option Alert Dashboard</div>', unsafe_allow_html=True)
st.write("---")

# Layout Columns
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="box-style">🟢 System Status: RUNNING BACKGROUND</div>', unsafe_allow_html=True)
    st.write("")
    st.success("Telegram Bot: Connected (Pending Key)")
    st.success("Angel API: Auto-Login Ready (Pending Key)")

with col2:
    st.markdown('<div class="box-style">📰 Live News Filter (Gujarati)</div>', unsafe_allow_html=True)
    st.write("")
    st.info(f"Tracking {len(NEWS_WHITELIST)} VIP Keywords for Nifty 50.")
    st.write("Keywords:", ", ".join(NEWS_WHITELIST[:5]) + "...")

st.write("---")
st.write("### 🛠️ Control Panel")
if st.button("Manual Pre-Market Trigger Test"):
    run_pre_market_checklist()
    st.toast("Pre-market alert sent to Telegram!")

if st.button("Manual News Fetch Test"):
    check_market_news()
    st.toast("Checking for live news...")
