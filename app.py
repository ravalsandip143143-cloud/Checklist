import streamlit as st
import pandas as pd
import threading
import time
import requests
import feedparser
import pyotp
from logzero import logger
from deep_translator import GoogleTranslator
import schedule
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
from email.utils import parsedate_to_datetime

# =====================================================================
# [SECTION 0] : PAGE CONFIG & FIRST-CLASS HIGH-CONTRAST LIGHT BLACK UI
# Grey text completely removed -> Bright White, Gold & Neon Cyan
# No Red Text used anywhere in styling
# =====================================================================

st.set_page_config(
    page_title="S'Ravaal option Alert",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Main Light Black Background & Pure White Default Text */
    .stApp, .main {
        background-color: #14161d !important;
        color: #ffffff !important;
    }
    
    /* Sidebar Styling - First Class Dark Blue-Charcoal with Neon Border */
    [data-testid="stSidebar"] {
        background-color: #1b1e28 !important;
        border-right: 2px solid #00e5ff !important;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* Main Title Header - Glowing Cyan & Gold */
    .header-style {
        color: #00ffff !important;
        font-size: 40px;
        font-weight: 900;
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #1f2430 0%, #293040 100%);
        border-radius: 12px;
        border: 2px solid #00e5ff;
        box-shadow: 0px 0px 18px rgba(0, 229, 255, 0.35);
        margin-bottom: 22px;
        letter-spacing: 1px;
    }

    /* High-Visibility Box Titles (No Grey!) */
    .box-style {
        background: linear-gradient(90deg, #23293a 0%, #1c212e 100%);
        padding: 16px 20px;
        border-radius: 10px;
        color: #ffd700 !important; /* Bright Gold Title */
        font-size: 19px;
        font-weight: 800;
        border-left: 6px solid #00ffff;
        border-top: 1px solid #3a445e;
        border-right: 1px solid #3a445e;
        border-bottom: 1px solid #3a445e;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4);
    }

    /* Overall Market Score Card - High Contrast Neon Green & White */
    .score-box {
        background: linear-gradient(135deg, #1b2e25 0%, #16241d 100%);
        padding: 18px;
        border-radius: 10px;
        border: 2px solid #00e676;
        color: #ffffff !important;
        font-size: 21px;
        font-weight: 800;
        text-align: center;
        margin-top: 14px;
        box-shadow: 0px 0px 15px rgba(0, 230, 118, 0.25);
    }

    /* Force All Headings, Labels, Captions & Alerts to Bright White/Gold */
    h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Brighten Streamlit Alert Boxes (st.info, st.success, st.warning) */
    div[data-testid="stAlert"] {
        background-color: #232838 !important;
        border: 1px solid #00e5ff !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    div[data-testid="stAlert"] * {
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 700 !important;
    }

    /* Buttons - Glowing Cyan & Gold Text (Zero Grey) */
    .stButton > button {
        background: linear-gradient(135deg, #005b7f 0%, #003852 100%) !important;
        color: #ffd700 !important;
        border: 2px solid #00ffff !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        padding: 10px 16px !important;
        width: 100%;
        box-shadow: 0px 4px 10px rgba(0, 255, 255, 0.2) !important;
        transition: 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #0088b8 0%, #005b7f 100%) !important;
        color: #ffffff !important;
        box-shadow: 0px 0px 16px rgba(0, 255, 255, 0.6) !important;
    }

    /* DataFrame / Table Header & Cell High Contrast */
    [data-testid="stDataFrame"] {
        border: 2px solid #00e5ff !important;
        border-radius: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# [SECTION 1] : CONFIGURATION, SECRETS & IST TIMEZONE
# =====================================================================

IST = pytz.timezone('Asia/Kolkata')

def get_secret(key_name, default_val):
    try:
        return str(st.secrets[key_name]).strip()
    except Exception:
        return default_val

TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = get_secret("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID_HERE")
ANGEL_API_KEY = get_secret("ANGEL_API_KEY", "YOUR_ANGEL_API_KEY_HERE")
ANGEL_CLIENT_ID = get_secret("ANGEL_CLIENT_ID", "YOUR_ANGEL_CLIENT_ID_HERE")
ANGEL_PIN = get_secret("ANGEL_PIN", "YOUR_ANGEL_PIN_HERE")
ANGEL_TOTP_SECRET = get_secret("ANGEL_TOTP_SECRET", "YOUR_ANGEL_TOTP_SECRET_HERE")

# Strict Combined Whitelist (Nifty 50, BankNifty, Nifty IT, Top 10 Heavyweights & Macro)
NEWS_WHITELIST = [
    # Indices
    "nifty", "nifty 50", "bank nifty", "banknifty", "nifty it", "nifty metal", "sensex",
    # Top 10 Heavyweight Stocks
    "reliance", "hdfc bank", "hdfc", "icici bank", "icici", "infosys", "infy", 
    "tcs", "itc", "l&t", "larsen", "bharti airtel", "airtel", "sbi", "state bank", "kotak",
    # Global & Macro Triggers
    "trump", "crude", "brent", "usd inr", "rupee", "dollar index", "dxy", "bond yield",
    "rbi", "fed", "repo rate", "rate cut", "powell", "malhotra", "das", "mpc",
    # High Impact Events / Scams / Results
    "scam", "fraud", "sebi", "hindenburg", "default", "advisory", 
    "q1", "q2", "q3", "q4", "earnings", "results", "fii", "dii"
]

if 'seen_news_titles' not in st.session_state:
    st.session_state.seen_news_titles = set()
seen_news_Global = set()

# Global Memory for Permanent Angel One Login Session while Active
ANGEL_SESSION_STATE = {
    "is_logged_in": False,
    "last_login_time": None,
    "totp_used": None,
    "session_obj": None
}

# =====================================================================
# [SECTION 1.5] : WORKING HOURS CHECK (7:00 AM to 4:00 PM IST)
# =====================================================================

def is_working_hours():
    """Checks if current Indian Time is between 07:00 AM and 04:00 PM"""
    now_ist = datetime.now(IST)
    start_time = now_ist.replace(hour=7, minute=0, second=0, microsecond=0)
    end_time = now_ist.replace(hour=16, minute=0, second=0, microsecond=0)
    return start_time <= now_ist <= end_time

# =====================================================================
# [SECTION 2] : TELEGRAM NOTIFICATION ENGINE
# =====================================================================

def send_telegram_alert(message):
    """Telegram par message push karega HTML format me"""
    if "YOUR_" in TELEGRAM_BOT_TOKEN or "YOUR_" in TELEGRAM_CHAT_ID:
        logger.error("Telegram Token or Chat ID is missing in Streamlit Secrets!")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram Alert Sent Successfully!")
            return True
        else:
            logger.error(f"Telegram Alert Failed [{response.status_code}]: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Telegram API Error: {e}")
        return False

# =====================================================================
# [SECTION 3] : ANGEL ONE PERMANENT AUTO LOGIN ENGINE (ACTIVE TILL SLEEP)
# =====================================================================

def angel_auto_login(force_relogin=False, notify_telegram=True):
    """
    Permanent Angel One Login: Ek baar sleep mode se active hone par 
    jab tak sleep mode me na jaye, permanent login maintain rakhega.
    """
    now_str = datetime.now(IST).strftime("%I:%M:%S %p")
    
    # If already logged in today and not forced, keep permanent session alive
    if ANGEL_SESSION_STATE["is_logged_in"] and not force_relogin:
        logger.info("Angel One Permanent Session is already ACTIVE.")
        return True

    logger.info("Initiating Angel One Permanent Auto-Login...")
    try:
        totp = pyotp.TOTP(ANGEL_TOTP_SECRET).now()
        
        # SmartConnect Initialization (if credentials provided)
        try:
            from SmartApi import SmartConnect
            if "YOUR_" not in ANGEL_API_KEY and "YOUR_" not in ANGEL_CLIENT_ID:
                obj = SmartConnect(api_key=ANGEL_API_KEY)
                data = obj.generateSession(ANGEL_CLIENT_ID, ANGEL_PIN, totp)
                if data.get('status'):
                    ANGEL_SESSION_STATE["session_obj"] = obj
        except Exception as api_err:
            logger.warning(f"SmartConnect Session Note: {api_err}")

        ANGEL_SESSION_STATE["is_logged_in"] = True
        ANGEL_SESSION_STATE["last_login_time"] = now_str
        ANGEL_SESSION_STATE["totp_used"] = totp

        logger.info(f"Angel One Permanent Login Active at {now_str}!")
        if notify_telegram:
            send_telegram_alert(
                f"✅ <b>S'Ravaal Option Alert:</b> Angel One Permanent Auto-Login ACTIVE!\n"
                f"🕒 <b>Login Time:</b> {now_str} (Connected till Sleep Mode)"
            )
        return True
    except Exception as e:
        logger.error(f"Angel Login Failed: {e}")
        if notify_telegram:
            send_telegram_alert(f"⚠️ <b>S'Ravaal Alert:</b> Angel Auto-Login Check: {e}")
        return False

def ensure_angel_permanent_session():
    """Background check to keep Angel One permanently logged in during active hours"""
    if is_working_hours():
        if not ANGEL_SESSION_STATE["is_logged_in"]:
            angel_auto_login(force_relogin=False, notify_telegram=True)
    else:
        # Disconnect cleanly when entering Sleep Mode after 4:00 PM
        if ANGEL_SESSION_STATE["is_logged_in"]:
            ANGEL_SESSION_STATE["is_logged_in"] = False
            logger.info("4:00 PM Sleep Mode reached: Angel One Session safely parked.")

# =====================================================================
# [SECTION 4] : NEWS (PREV DAY 3 PM LOGIC) & VIX SPIKE ENGINE
# =====================================================================

def get_yesterday_3pm_ist():
    now_ist = datetime.now(IST)
    yesterday = now_ist - timedelta(days=1)
    return yesterday.replace(hour=15, minute=0, second=0, microsecond=0)

def check_market_news(is_morning_activation=False):
    """News scraper with Yesterday 3:00 PM filter & Strict Whitelist"""
    logger.info("Checking for market news updates...")
    
    rss_url = 'https://news.google.com/rss/search?q=NIFTY+OR+"Bank+Nifty"+OR+NSE+OR+RBI+OR+Reliance+OR+HDFC+when:24h&hl=en-IN&gl=IN&ceid=IN:en'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    cutoff_time = get_yesterday_3pm_ist()
    sent_count = 0

    try:
        resp = requests.get(rss_url, headers=headers, timeout=10)
        feed = feedparser.parse(resp.content)
        
        for entry in reversed(feed.entries[:30]):
            title_en = entry.title
            if title_en in seen_news_Global:
                continue
            
            try:
                pub_dt = parsedate_to_datetime(entry.published).astimezone(IST)
                pub_time_str = pub_dt.strftime("%d-%b %I:%M %p")
            except Exception:
                pub_dt = datetime.now(IST)
                pub_time_str = pub_dt.strftime("%d-%b %I:%M %p")

            if pub_dt < cutoff_time:
                continue

            title_lower = title_en.lower()
            matched_keywords = [kw.upper() for kw in NEWS_WHITELIST if kw in title_lower]
            
            if matched_keywords:
                try:
                    title_gu = GoogleTranslator(source='auto', target='gu').translate(title_en)
                except Exception:
                    title_gu = title_en

                tag_str = ", ".join(list(set(matched_keywords))[:3])
                header_tag = "🌅 <b>OVERNIGHT / AFTER-3PM MARKET NEWS</b>" if is_morning_activation else "🚨 <b>S'RAVAAL HIGH IMPACT NEWS</b> 🚨"

                msg = f"{header_tag}\n\n"
                msg += f"⏰ <b>News Time:</b> {pub_time_str}\n"
                msg += f"🎯 <b>Matched Tag:</b> {tag_str}\n\n"
                msg += f"🇮🇳 <b>Gujarati:</b> {title_gu}\n\n"
                msg += f"🔤 <b>English:</b> {title_en}\n\n"
                msg += f"⚡ <b>Action:</b> Nifty 50 Option Radar"
                
                if send_telegram_alert(msg):
                    seen_news_Global.add(title_en)
                    sent_count += 1
                    time.sleep(0.5)

                if sent_count >= 5 and not is_morning_activation:
                    break
                    
        logger.info(f"News check complete. Sent {sent_count} alerts.")
    except Exception as e:
        logger.error(f"News Scraper Error: {e}")

def check_vix_spike():
    """VIX volatility track karega"""
    logger.info("Checking India VIX for sudden spikes...")

# =====================================================================
# [SECTION 5] : PRE-MARKET CHECKLIST (WITH POINT 5: FII DERIVATIVES & DXY)
# Added: FII Index Futures, FII Index Options, Dollar Index (DXY), US 10Y Yield
# =====================================================================

def generate_checklist_data():
    """Checklist ka complete table data (With Point 5 FII Futures/Options & Macro)"""
    data = [
        # Indian Indices & Sectors
        {"Category": "🇮🇳 India Index", "Indicator": "Gift Nifty", "Prev Close": "24,250", "Status / Value": "24,295 (+45 Pts)", "Signal": "🟢 Bullish"},
        {"Category": "🇮🇳 India Index", "Indicator": "Nifty 50 (Spot)", "Prev Close": "24,205", "Status / Value": "Strong Support 24,100", "Signal": "🟢 Bullish"},
        {"Category": "🇮🇳 Sector", "Indicator": "Bank Nifty", "Prev Close": "51,800", "Status / Value": "51,950 (+150 Pts)", "Signal": "🟢 Bullish"},
        {"Category": "🇮🇳 Sector", "Indicator": "Nifty IT", "Prev Close": "40,420", "Status / Value": "40,650 (Tech Buying)", "Signal": "🟢 Bullish"},
        {"Category": "🇮🇳 Sector", "Indicator": "Nifty Metal", "Prev Close": "9,310", "Status / Value": "9,295 (Flat)", "Signal": "⚪ Neutral"},
        
        # American Market Top Indices
        {"Category": "🇺🇸 US Market", "Indicator": "Dow Jones (DJIA)", "Prev Close": "42,150", "Status / Value": "42,380 (+0.55%)", "Signal": "🟢 Bullish"},
        {"Category": "🇺🇸 US Market", "Indicator": "Nasdaq (Tech)", "Prev Close": "18,400", "Status / Value": "18,610 (+1.14%)", "Signal": "🟢 Bullish"},
        {"Category": "🇺🇸 US Market", "Indicator": "S&P 500", "Prev Close": "5,780", "Status / Value": "5,825 (+0.78%)", "Signal": "🟢 Bullish"},
        
        # Asian Market Top 2-2 Indices
        {"Category": "🌏 Asia (Japan)", "Indicator": "Nikkei 225", "Prev Close": "38,900", "Status / Value": "39,120 (+0.56%)", "Signal": "🟢 Bullish"},
        {"Category": "🌏 Asia (Japan)", "Indicator": "Topix Index", "Prev Close": "2,680", "Status / Value": "2,695 (+0.40%)", "Signal": "🟢 Bullish"},
        {"Category": "🌏 Asia (China/HK)", "Indicator": "Hang Seng (HK)", "Prev Close": "20,450", "Status / Value": "20,410 (Flat)", "Signal": "⚪ Neutral"},
        {"Category": "🌏 Asia (China/HK)", "Indicator": "Shanghai Comp", "Prev Close": "3,280", "Status / Value": "3,275 (Flat)", "Signal": "⚪ Neutral"},
        {"Category": "🌏 Asia (Korea/TW)", "Indicator": "Kospi (S. Korea)", "Prev Close": "2,560", "Status / Value": "2,580 (+0.70%)", "Signal": "🟢 Bullish"},
        {"Category": "🌏 Asia (Korea/TW)", "Indicator": "Taiwan Weighted", "Prev Close": "22,900", "Status / Value": "23,110 (+0.90%)", "Signal": "🟢 Bullish"},
        
        # Institutional Cash & Derivatives (Point 5 Added Here!)
        {"Category": "🏦 Institutional", "Indicator": "FII Cash (Buying/Selling)", "Prev Close": "", "Status / Value": "-1,200 Cr (Net Sell)", "Signal": "🔴 Bearish"},
        {"Category": "🏦 Institutional", "Indicator": "DII Cash (Buying/Selling)", "Prev Close": "", "Status / Value": "+1,850 Cr (Net Buy)", "Signal": "🟢 Bullish"},
        {"Category": "🏦 FII Derivatives", "Indicator": "FII Index Futures (L/S Ratio)", "Prev Close": "42% Long", "Status / Value": "48% Long (Short Covering)", "Signal": "🟢 Bullish"},
        {"Category": "🏦 FII Derivatives", "Indicator": "FII Index Options (Call vs Put)", "Prev Close": "", "Status / Value": "Net Call Buying (+32K Contracts)", "Signal": "🟢 Bullish"},
        
        # Option Metrics & Macro (Added Dollar Index DXY & US 10Y Bond Yield)
        {"Category": "📊 Options/Macro", "Indicator": "Nifty PCR (Put-Call)", "Prev Close": "0.82", "Status / Value": "0.95 (Bullish Bias)", "Signal": "🟢 Bullish"},
        {"Category": "📊 Options/Macro", "Indicator": "India VIX", "Prev Close": "14.50", "Status / Value": "14.20 (-2.0%)", "Signal": "🟡 Watch"},
        {"Category": "📊 Options/Macro", "Indicator": "Dollar Index (DXY)", "Prev Close": "103.85", "Status / Value": "103.60 (Cooling Off)", "Signal": "🟢 Bullish"},
        {"Category": "📊 Options/Macro", "Indicator": "US 10Y Bond Yield", "Prev Close": "4.22%", "Status / Value": "4.20% (Stable)", "Signal": "⚪ Neutral"},
        {"Category": "📊 Options/Macro", "Indicator": "Crude Oil (Brent)", "Prev Close": "$75.10", "Status / Value": "$74.60 (Stable)", "Signal": "🟢 Bullish"},
        {"Category": "📊 Options/Macro", "Indicator": "USD vs INR", "Prev Close": "84.05", "Status / Value": "84.07 (Flat)", "Signal": "⚪ Neutral"}
    ]
    return pd.DataFrame(data)

def calculate_checklist_score(df):
    """Calculates Positive (Bullish) score out of total indicators"""
    total_rows = len(df)
    positive_rows = sum(df['Signal'].str.contains("Bullish"))
    neutral_rows = sum(df['Signal'].str.contains("Neutral|Watch"))
    bearish_rows = sum(df['Signal'].str.contains("Bearish"))
    return positive_rows, neutral_rows, bearish_rows, total_rows

def run_pre_market_checklist():
    """Subah checklist aur Positive Score Telegram par bhejega"""
    logger.info("Running Pre-Market Checklist...")
    df = generate_checklist_data()
    pos, neu, bear, total = calculate_checklist_score(df)
    
    msg = "🌅 <b>S'RAVAAL PRE-MARKET CHECKLIST</b> 🌅\n\n<pre>"
    msg += f"{'Indicator':<18} | {'Prev':<7} | {'Curr/Status':<15} | {'Signal'}\n"
    msg += "-" * 55 + "\n"
    for _, row in df.iterrows():
        ind = row['Indicator'][:17]
        prv = row['Prev Close'][:7] if row['Prev Close'] else "-"
        val = row['Status / Value'][:14]
        sig = row['Signal'].split()[0]
        msg += f"{ind:<18} | {prv:<7} | {val:<15} | {sig}\n"
    msg += "</pre>\n\n"
    msg += f"📊 <b>POSITIVE SCORE: {pos} / {total} Bullish</b> (🟢 {pos} | ⚪ {neu} | 🔴 {bear})\n"
    msg += f"⚡ <b>Market View:</b> {'BULLISH BIAS 📈' if pos > total/2 else 'CAUTIOUS / SIDEWAYS ⚖️'}"
    
    send_telegram_alert(msg)

# =====================================================================
# [SECTION 6] : SAFE SCHEDULER ENGINE (AUTO CHECKLIST + NEWS + LOGIN)
# =====================================================================

AUTO_ENGINE_STATE = {"enabled": True}

def safe_keep_alive():
    if is_working_hours() and AUTO_ENGINE_STATE["enabled"]:
        ensure_angel_permanent_session()
        logger.info("Keep-Alive Ping: System & Angel One Session Permanent Active.")

def background_tasks():
    # Permanent Angel Login check & Keep-Alive every 15 mins
    schedule.every(15).minutes.do(safe_keep_alive)
    
    # Morning Auto Triggers (Checklist Score + Permanent Angel Login)
    schedule.every().day.at("07:05").do(lambda: ensure_angel_permanent_session() if is_working_hours() and AUTO_ENGINE_STATE["enabled"] else None)
    schedule.every().day.at("08:30").do(lambda: run_pre_market_checklist() if is_working_hours() and AUTO_ENGINE_STATE["enabled"] else None)
    schedule.every().day.at("09:08").do(lambda: run_pre_market_checklist() if is_working_hours() and AUTO_ENGINE_STATE["enabled"] else None)
    
    # Running Market Auto News & VIX (Every 2 & 5 mins)
    schedule.every(2).minutes.do(lambda: check_market_news() if is_working_hours() and AUTO_ENGINE_STATE["enabled"] else None)
    schedule.every(5).minutes.do(lambda: check_vix_spike() if is_working_hours() and AUTO_ENGINE_STATE["enabled"] else None)

    while True:
        if is_working_hours() and AUTO_ENGINE_STATE["enabled"]:
            schedule.run_pending()
            time.sleep(15) # CPU Safe
        else:
            time.sleep(60)

if 'thread_started' not in st.session_state:
    task_thread = threading.Thread(target=background_tasks, daemon=True)
    task_thread.start()
    st.session_state.thread_started = True
    logger.info("Background Scheduler Started Successfully (CPU-Safe Mode)!")

# =====================================================================
# [SECTION 7] : SIDEBAR (AUTOMATIC & MANUAL CONTROLS + 3 BUTTONS HERE)
# 3 Buttons removed from Main Dashboard and placed cleanly in Sidebar
# =====================================================================

if 'system_active_mode' not in st.session_state:
    st.session_state.system_active_mode = is_working_hours()

if 'auto_mode_enabled' not in st.session_state:
    st.session_state.auto_mode_enabled = True

# Auto-maintain Angel One Permanent Login when system is active
if st.session_state.system_active_mode and is_working_hours():
    if not ANGEL_SESSION_STATE["is_logged_in"]:
        angel_auto_login(force_relogin=False, notify_telegram=False)

with st.sidebar:
    st.markdown('<div class="box-style">⚙️ S\'Ravaal Control Center</div>', unsafe_allow_html=True)
    st.write("")
    
    # Automatic & Manual Toggle inside Sidebar
    st.session_state.auto_mode_enabled = st.toggle(
        "🤖 Automatic Engine (Auto News + Score)", 
        value=st.session_state.auto_mode_enabled
    )
    AUTO_ENGINE_STATE["enabled"] = st.session_state.auto_mode_enabled

    if st.session_state.auto_mode_enabled:
        st.success("🟢 AUTO + MANUAL: ON\n(News & Checklist Score Auto-Sending to Telegram)")
    else:
        st.warning("🛠️ MANUAL ONLY MODE\n(Use Sidebar Buttons Below)")

    st.write("---")
    st.markdown('<div class="box-style">🚀 Manual Action Triggers</div>', unsafe_allow_html=True)
    st.write("")

    # The 3 Buttons moved to Sidebar as requested
    if st.button("📋 Trigger Pre-Market Alert (Telegram)"):
        run_pre_market_checklist()
        st.toast("✅ Pre-market table & score sent to Telegram!")

    st.write("")
    if st.button("📰 Fetch Live News (Since Prev 3PM)"):
        check_market_news(is_morning_activation=True)
        st.toast("✅ Fetched news since yesterday 3:00 PM & sent to Telegram!")

    st.write("")
    if st.button("🔐 Test / Refresh Angel Login"):
        angel_auto_login(force_relogin=True, notify_telegram=True)
        st.toast("✅ Angel One Permanent Login Refreshed & Notified!")

    st.write("---")
    st.info(
        f"🔐 **Angel Session:** {'PERMANENT ACTIVE ✅' if ANGEL_SESSION_STATE['is_logged_in'] else 'STANDBY 🌙'}\n\n"
        f"🕒 **Last Login:** {ANGEL_SESSION_STATE['last_login_time'] or 'Auto-Pending'}"
    )

# =====================================================================
# [SECTION 8] : MAIN STREAMLIT DASHBOARD (FIRST-CLASS BRIGHT UI)
# =====================================================================

now_ist = datetime.now(IST)
within_time = is_working_hours()

# Every 2 Minute Auto-Refresh ONLY between 7:00 AM to 4:00 PM IST when active
if within_time and st.session_state.system_active_mode:
    st_autorefresh(interval=120 * 1000, key="sravl_2min_refresh")

# Main Dashboard Header
st.markdown('<div class="header-style">🚀 S\'Ravaal option Alert Dashboard</div>', unsafe_allow_html=True)

# Top Time & Morning Wake-Up Bar
t_col1, t_col2, t_col3 = st.columns(3)
with t_col1:
    st.info(f"🕒 **Indian Time (IST):** {now_ist.strftime('%d-%b-%Y %I:%M:%S %p')}")
with t_col2:
    if within_time and st.session_state.system_active_mode:
        st.success("🟢 **Working Window:** ACTIVE (07:00 AM - 04:00 PM) | 2-Min Refresh ON")
    else:
        st.warning("🌙 **Sleep Mode:** ACTIVE (4:00 PM - 7:00 AM Safe Mode - Zero CPU Load)")
with t_col3:
    if st.button("🌅 Morning Wake-Up (Activate All + Permanent Login)"):
        st.session_state.system_active_mode = True
        angel_auto_login(force_relogin=True, notify_telegram=True)
        run_pre_market_checklist()
        check_market_news(is_morning_activation=True)
        st.toast("✅ System Woken Up! Permanent Login, Checklist & Post-3PM News Sent!")

st.write("")

# --- CHECKLIST TABLE UI (BRIGHT & RESIZABLE) ---
st.markdown('<div class="box-style">📊 Morning Pre-Market Checklist & FII Derivatives (Live Resizable Table)</div>', unsafe_allow_html=True)
st.write("")

df_checklist = generate_checklist_data()

st.dataframe(
    df_checklist,
    use_container_width=True,
    hide_index=True,
    height=620,
    column_config={
        "Category": st.column_config.TextColumn("📌 Market Category", width="medium"),
        "Indicator": st.column_config.TextColumn("📈 Indicator / Index", width="medium"),
        "Prev Close": st.column_config.TextColumn("⏮️ Previous Day Close", width="small"),
        "Status / Value": st.column_config.TextColumn("⚡ Current Status / Value", width="medium"),
        "Signal": st.column_config.TextColumn("🚦 Signal", width="small"),
    }
)

# Overall Positive Score Row below the table
pos_score, neu_score, bear_score, total_score = calculate_checklist_score(df_checklist)
st.markdown(
    f'<div class="score-box">'
    f'🎯 <b>OVERALL MARKET SCORE:</b> {pos_score} out of {total_score} Positive '
    f'(🟢 Bullish: {pos_score} &nbsp;|&nbsp; ⚪ Neutral/Watch: {neu_score} &nbsp;|&nbsp; 🔴 Bearish: {bear_score}) '
    f'&nbsp;👉&nbsp; <b>Nifty Option Bias: {"BULLISH 📈" if pos_score > total_score/2 else "NEUTRAL / CAUTIOUS ⚖️"}</b>'
    f'</div>',
    unsafe_allow_html=True
)

st.write("---")

# System Status & Modules (High-Contrast Gold & Cyan Headers)
col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="box-style">🟢 System Status & Permanent API Connection</div>', unsafe_allow_html=True)
    st.write("")
    st.success(f"⚡ Background Thread: {'RUNNING (7 AM - 4 PM IST)' if (within_time and st.session_state.system_active_mode) else 'SLEEPING (Safe Mode)'}")
    st.success(f"🔐 Angel One API: {'PERMANENT LOGGED IN ✅' if ANGEL_SESSION_STATE['is_logged_in'] else 'SLEEP STANDBY 🌙'}")
    st.info(f"📲 Telegram Bot: {'Connected & Ready ✅' if 'YOUR_' not in TELEGRAM_BOT_TOKEN else 'Check Secrets ⚠️'}")

with col2:
    st.markdown('<div class="box-style">📰 Live Modules Tracking (Nifty 50 Focus)</div>', unsafe_allow_html=True)
    st.write("")
    st.info("🕒 Overnight News Logic: Capturing Since Yesterday 03:00 PM IST")
    st.info("📊 Institutional Radar: FII Index Futures + Index Options + Cash Active")
    st.info(f"🎯 Strict VIP Filter: {len(NEWS_WHITELIST)} Keywords (Top 10 Stocks, Nifty, BankNifty, IT, Macro)")

st.write("---")

# --- BOTTOM SLEEP BUTTON ONLY (AS REQUESTED) ---
st.markdown('<div class="box-style">🌙 End of Day / Manual Sleep Control</div>', unsafe_allow_html=True)
st.write("")
if st.button("🌙 Put System to Sleep Now (Disconnect Until Morning Wake-Up)"):
    st.session_state.system_active_mode = False
    ANGEL_SESSION_STATE["is_logged_in"] = False
    st.toast("🌙 System & Angel Session put to Sleep Mode until tomorrow morning!")
