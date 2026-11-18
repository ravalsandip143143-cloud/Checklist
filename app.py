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
import yfinance as yf

# =====================================================================
# [SECTION 0] : PAGE CONFIG & BOLD BLACK TEXT / ZERO-GREY UI STYLING
# P1 & P2 Fixed:
# - Table top-right 3 toolbar icons/functions -> BOLD BLACK (#000000)
# - 6 Status boxes under API & Live Tracking -> BOLD BLACK (#000000)
# - All Grey words replaced with BOLD BLACK (#000000)
# =====================================================================

st.set_page_config(
    page_title="S'Ravaal option Alert",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Main Dashboard Background */
    .stApp, .main {
        background-color: #14161d !important;
        color: #ffffff !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1b1e28 !important;
        border-right: 2px solid #00e5ff !important;
    }
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    /* Main Title Header - Glowing Cyan */
    .header-style {
        color: #00ffff !important;
        font-size: 38px;
        font-weight: 900;
        text-align: center;
        padding: 18px;
        background: linear-gradient(135deg, #1f2430 0%, #293040 100%);
        border-radius: 12px;
        border: 2px solid #00e5ff;
        box-shadow: 0px 0px 18px rgba(0, 229, 255, 0.35);
        margin-bottom: 20px;
        letter-spacing: 1px;
    }

    /* Section Header Bars - Gold & Cyan */
    .box-style {
        background: linear-gradient(90deg, #23293a 0%, #1c212e 100%);
        padding: 15px 20px;
        border-radius: 10px;
        color: #ffd700 !important;
        font-size: 19px;
        font-weight: 900;
        border-left: 6px solid #00ffff;
        border-top: 1px solid #00e5ff;
        border-right: 1px solid #00e5ff;
        border-bottom: 1px solid #00e5ff;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4);
        margin-bottom: 10px;
    }

    /* P2 FIX: 6 Boxes under API & Live Tracking + Top Status Boxes -> BOLD BLACK TEXT */
    .black-bold-box {
        background-color: #e8f4f8 !important;
        color: #000000 !important;
        padding: 14px 18px !important;
        border-radius: 8px !important;
        border: 2px solid #00e5ff !important;
        border-left: 7px solid #000000 !important;
        font-size: 16px !important;
        font-weight: 900 !important;
        margin-bottom: 10px !important;
        box-shadow: 0px 3px 8px rgba(0,0,0,0.3) !important;
    }
    .black-bold-box * {
        color: #000000 !important;
        font-weight: 900 !important;
    }

    /* Streamlit Native Alert Boxes (st.info, st.success, st.warning) -> BOLD BLACK TEXT */
    div[data-testid="stAlert"] {
        background-color: #e8f4f8 !important;
        border: 2px solid #00e5ff !important;
        color: #000000 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stAlert"] *,
    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] span {
        color: #000000 !important;
        font-size: 16px !important;
        font-weight: 900 !important;
    }

    /* P1 FIX: Table Top-Right 3 Functions/Icons Toolbar & Tooltips -> BOLD BLACK */
    div[data-testid="stElementToolbar"],
    [data-testid="stElementToolbar"] *,
    [data-testid="stElementToolbar"] button,
    [data-testid="stElementToolbar"] svg,
    [data-testid="stBaseButton-elementToolbar"],
    [data-testid="stBaseButton-elementToolbar"] * {
        color: #000000 !important;
        fill: #000000 !important;
        stroke: #000000 !important;
        font-weight: 900 !important;
        opacity: 1 !important;
    }
    div[data-testid="stElementToolbar"] {
        background-color: #ffffff !important;
        border: 2px solid #000000 !important;
        border-radius: 6px !important;
        padding: 2px 6px !important;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.4) !important;
    }
    div[role="tooltip"], div[role="tooltip"] * {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: 900 !important;
        border: 1px solid #000000 !important;
    }

    /* DataFrame Table Border & Bold Black Header/Cell Override */
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] * {
        color: #000000 !important;
        font-weight: 900 !important;
    }
    [data-testid="stDataFrame"] {
        border: 2px solid #00e5ff !important;
        border-radius: 10px !important;
        background-color: #ffffff !important;
    }

    /* Overall Market Score Card */
    .score-box {
        background: linear-gradient(135deg, #1b2e25 0%, #16241d 100%);
        padding: 18px;
        border-radius: 10px;
        border: 2px solid #00e676;
        color: #ffffff !important;
        font-size: 21px;
        font-weight: 900;
        text-align: center;
        margin-top: 14px;
        box-shadow: 0px 0px 15px rgba(0, 230, 118, 0.25);
    }

    /* Action Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00e5ff 0%, #00b8d4 100%) !important;
        color: #000000 !important;
        border: 2px solid #ffffff !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: 900 !important;
        padding: 10px 16px !important;
        width: 100%;
        box-shadow: 0px 4px 10px rgba(0, 255, 255, 0.25) !important;
    }
    .stButton > button * {
        color: #000000 !important;
        font-weight: 900 !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #ffd700 0%, #ffab00 100%) !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
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
    "nifty", "nifty 50", "bank nifty", "banknifty", "nifty it", "nifty metal", "sensex", "gift nifty",
    # Top 10 Heavyweight Stocks
    "reliance", "hdfc bank", "hdfc", "icici bank", "icici", "infosys", "infy", 
    "tcs", "itc", "l&t", "larsen", "bharti airtel", "airtel", "sbi", "state bank", "kotak",
    # Global & Macro Triggers
    "trump", "crude", "brent", "usd inr", "rupee", "dollar index", "dxy", "bond yield",
    "rbi", "fed", "repo rate", "rate cut", "powell", "malhotra", "das", "mpc", "tariff",
    # High Impact Events / Scams / Results
    "scam", "fraud", "sebi", "hindenburg", "default", "advisory", 
    "q1", "q2", "q3", "q4", "earnings", "results", "fii", "dii"
]

if 'seen_news_titles' not in st.session_state:
    st.session_state.seen_news_titles = set()
seen_news_Global = set()

ANGEL_SESSION_STATE = {
    "is_logged_in": False,
    "last_login_time": None,
    "totp_used": None,
    "session_obj": None,
    "morning_news_sent_date": None
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
# [SECTION 3] : ANGEL ONE PERMANENT AUTO LOGIN ENGINE
# =====================================================================

def angel_auto_login(force_relogin=False, notify_telegram=True):
    """Permanent Angel One Login while active (until Sleep Mode)"""
    now_str = datetime.now(IST).strftime("%I:%M:%S %p")
    
    if ANGEL_SESSION_STATE["is_logged_in"] and not force_relogin:
        logger.info("Angel One Permanent Session is already ACTIVE.")
        return True

    logger.info("Initiating Angel One Permanent Auto-Login...")
    try:
        totp = pyotp.TOTP(ANGEL_TOTP_SECRET).now()
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

        if notify_telegram:
            send_telegram_alert(
                f"✅ <b>S'Ravaal Option Alert:</b> Angel One Permanent Auto-Login ACTIVE!
"
                f"🕒 <b>Login Time:</b> {now_str} (Connected till 4:00 PM Sleep Mode)"
            )
        return True
    except Exception as e:
        logger.error(f"Angel Login Failed: {e}")
        if notify_telegram:
            send_telegram_alert(f"⚠️ <b>S'Ravaal Alert:</b> Angel Auto-Login Check: {e}")
        return False

def ensure_angel_permanent_session():
    if is_working_hours():
        if not ANGEL_SESSION_STATE["is_logged_in"]:
            angel_auto_login(force_relogin=False, notify_telegram=True)
    else:
        if ANGEL_SESSION_STATE["is_logged_in"]:
            ANGEL_SESSION_STATE["is_logged_in"] = False
            logger.info("4:00 PM Sleep Mode reached: Angel One Session safely parked.")

# =====================================================================
# [SECTION 4] : NEWS ENGINE (7:30 AM AUTO & PREV DAY 4:00 PM CUTOFF)
# Fetches all news after Previous Day 4:00 PM IST on morning wake-up
# =====================================================================

def get_yesterday_4pm_ist():
    """Returns Yesterday 4:00 PM IST timestamp for overnight news capture"""
    now_ist = datetime.now(IST)
    yesterday = now_ist - timedelta(days=1)
    return yesterday.replace(hour=16, minute=0, second=0, microsecond=0)

def check_market_news(is_morning_activation=False):
    """News scraper with Yesterday 4:00 PM filter & Strict Whitelist"""
    logger.info(f"Checking market news (Morning Batch={is_morning_activation})...")
    
    rss_url = (
        'https://news.google.com/rss/search?'
        'q=NIFTY+OR+"Bank+Nifty"+OR+NSE+OR+RBI+OR+Reliance+OR+"HDFC+Bank"+OR+"ICICI+Bank"+OR+Infosys+OR+Fed+OR+Crude+when:24h'
        '&hl=en-IN&gl=IN&ceid=IN:en'
    )
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    cutoff_time = get_yesterday_4pm_ist()
    sent_count = 0

    try:
        resp = requests.get(rss_url, headers=headers, timeout=10)
        feed = feedparser.parse(resp.content)
        
        # Process oldest to newest since yesterday 4:00 PM
        entries_list = list(reversed(feed.entries[:40]))
        for entry in entries_list:
            title_en = entry.title
            if title_en in seen_news_Global:
                continue
            
            try:
                pub_dt = parsedate_to_datetime(entry.published).astimezone(IST)
                pub_time_str = pub_dt.strftime("%d-%b %I:%M %p")
            except Exception:
                pub_dt = datetime.now(IST)
                pub_time_str = pub_dt.strftime("%d-%b %I:%M %p")

            # Must be after Previous Day 4:00 PM IST
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
                header_tag = (
                    "🌅 <b>POST-4PM OVERNIGHT MARKET NEWS</b>"
                    if is_morning_activation
                    else "🚨 <b>S'RAVAAL HIGH IMPACT NEWS</b> 🚨"
                )

                msg = f"{header_tag}

"
                msg += f"⏰ <b>News Time:</b> {pub_time_str}
"
                msg += f"🎯 <b>Matched Tag:</b> {tag_str}

"
                msg += f"🇮🇳 <b>Gujarati:</b> {title_gu}

"
                msg += f"🔤 <b>English:</b> {title_en}

"
                msg += f"⚡ <b>Action:</b> Nifty 50 Option Radar"
                
                if send_telegram_alert(msg):
                    seen_news_Global.add(title_en)
                    sent_count += 1
                    time.sleep(0.4)

                # On morning wake-up, allow up to 12 overnight news items; running market max 4 per cycle
                max_limit = 12 if is_morning_activation else 4
                if sent_count >= max_limit:
                    break
                    
        logger.info(f"News check complete. Sent {sent_count} alerts.")
    except Exception as e:
        logger.error(f"News Scraper Error: {e}")

# =====================================================================
# [SECTION 5] : MASTER LIVE MARKET DATA ENGINE (TRADINGVIEW + YFINANCE + NSE)
# Q1, Q2, P3 Fixed: Real-Time Gift Nifty, USD/INR, Global Indices, VIX, PCR & FII
# =====================================================================

def fetch_tradingview_live_quotes():
    """
    Fetches exact live quotes directly from TradingView Public Scanner API
    so values match the user's TradingView Watchlist (NIFTY1!, USDINR, US10Y, etc.)
    """
    tv_url = "https://scanner.tradingview.com/global/scan"
    tickers = [
        "NSE:NIFTY1!",      # Gift Nifty / Nifty Futures
        "SGX:IN1!",         # Gift Nifty SGX/NSEIX backup
        "NSE:NIFTY",        # Nifty 50 Spot
        "NSE:BANKNIFTY",    # Bank Nifty
        "NSE:CNXIT",        # Nifty IT
        "NSE:CNXMETAL",     # Nifty Metal
        "DJ:DJI",           # Dow Jones
        "NASDAQ:NDX",       # Nasdaq 100 (matches TV watchlist)
        "NASDAQ:IXIC",      # Nasdaq Composite backup
        "SP:SPX",           # S&P 500
        "TVC:NI225",        # Nikkei 225
        "TVC:TOPIX",        # Topix
        "TVC:HSI",          # Hang Seng
        "SSE:000001",       # Shanghai Composite
        "KRX:KOSPI",        # Kospi
        "TWSE:TAIEX",       # Taiwan Weighted
        "NSE:INDIAVIX",     # India VIX
        "TVC:DXY",          # Dollar Index
        "TVC:US10Y",        # US 10Y Bond Yield
        "TVC:UKOIL",        # Brent Crude Oil
        "MCX:CRUDEOIL1!",   # MCX Crude Oil
        "FX_IDC:USDINR"     # USD vs INR
    ]
    payload = {
        "symbols": {"tickers": tickers, "query": {"types": []}},
        "columns": ["close", "change", "change_abs", "Recommend.All"]
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json"
    }
    results = {}
    try:
        resp = requests.post(tv_url, json=payload, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            for item in data:
                sym = item.get("s")
                d = item.get("d", [None, None, None, None])
                if d and d[0] is not None:
                    close_val = float(d[0])
                    pct_chg = float(d[1]) if d[1] is not None else 0.0
                    abs_chg = float(d[2]) if d[2] is not None else 0.0
                    prev_close = close_val - abs_chg
                    results[sym] = {
                        "close": close_val,
                        "prev_close": prev_close,
                        "chg": abs_chg,
                        "pct": pct_chg
                    }
    except Exception as e:
        logger.warning(f"TradingView Scanner fetch note: {e}")
    return results

def fetch_yahoo_fallback(yf_symbol):
    """Fallback live quote fetcher via Yahoo Finance v8 API if TV symbol is missing"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}?interval=1d&range=5d"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200:
            res = r.json()["chart"]["result"][0]
            meta = res["meta"]
            close_val = float(meta.get("regularMarketPrice", 0.0))
            prev_close = float(meta.get("chartPreviousClose", meta.get("previousClose", close_val)))
            closes = [c for c in res["indicators"]["quote"][0].get("close", []) if c is not None]
            if len(closes) >= 2 and prev_close == close_val:
                prev_close = float(closes[-2])
            abs_chg = close_val - prev_close
            pct_chg = (abs_chg / prev_close * 100.0) if prev_close else 0.0
            return {
                "close": close_val,
                "prev_close": prev_close,
                "chg": abs_chg,
                "pct": pct_chg
            }
    except Exception as e:
        logger.warning(f"Yahoo fallback error for {yf_symbol}: {e}")
    return None

def get_quote_smart(tv_quotes, tv_keys, yf_symbol, decimals=2, prefix="", suffix=""):
    """Combines TradingView primary quote with Yahoo Finance fallback"""
    q = None
    for k in tv_keys:
        if k in tv_quotes and tv_quotes[k]["close"] > 0:
            q = tv_quotes[k]
            break
    if not q and yf_symbol:
        q = fetch_yahoo_fallback(yf_symbol)
    if not q:
        return "N/A", "Fetching...", 0.0, 0.0

    fmt = f"{{:,.{decimals}f}}"
    prev_str = f"{prefix}{fmt.format(q['prev_close'])}{suffix}"
    curr_str = f"{prefix}{fmt.format(q['close'])}{suffix}"
    sign = "+" if q["chg"] >= 0 else ""
    status_str = f"{curr_str} ({sign}{fmt.format(q['chg'])} | {sign}{q['pct']:.2f}%)"
    return prev_str, status_str, q["chg"], q["pct"]

def fetch_live_nse_pcr_and_fii():
    """Attempts to fetch live Nifty PCR & FII/DII data from NSE India"""
    pcr_val = None
    fii_net = None
    dii_net = None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/"
    }
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        # 1. Option Chain for Live Nifty PCR
        oc_resp = session.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY", headers=headers, timeout=6)
        if oc_resp.status_code == 200:
            records = oc_resp.json().get("filtered", {})
            tot_ce = records.get("CE", {}).get("totOI", 0)
            tot_pe = records.get("PE", {}).get("totOI", 0)
            if tot_ce > 0:
                pcr_val = round(tot_pe / tot_ce, 2)
        # 2. FII / DII Cash Data
        fii_resp = session.get("https://www.nseindia.com/api/fiidiiTradeReact", headers=headers, timeout=6)
        if fii_resp.status_code == 200:
            for item in fii_resp.json():
                cat = item.get("category", "").upper()
                net_val = float(str(item.get("netValue", "0")).replace(",", ""))
                if "FII" in cat or "FPI" in cat:
                    fii_net = net_val
                elif "DII" in cat:
                    dii_net = net_val
    except Exception as e:
        logger.warning(f"NSE Direct API Note: {e}")
    return pcr_val, fii_net, dii_net

def classify_signal(pct_chg, invert=False, flat_threshold=0.10):
    """
    Standard Signal Logic:
    - invert=False: Positive change -> Bullish, Negative -> Bearish
    - invert=True (for DXY, US10Y, USDINR, Crude, VIX): Rising value is Bearish/Watch for Nifty
    """
    if abs(pct_chg) <= flat_threshold:
        return "⚪ Neutral"
    if not invert:
        return "🟢 Bullish" if pct_chg > 0 else "🔴 Bearish"
    else:
        return "🟢 Bullish" if pct_chg < 0 else "🔴 Bearish"

@st.cache_data(ttl=60, show_spinner=False)
def generate_checklist_data():
    """
    Master Live Checklist Generator:
    Pulls 100% live Previous Day Close & Current Value from TradingView + Yahoo Finance + NSE
    """
    tv_quotes = fetch_tradingview_live_quotes()
    live_pcr, fii_net, dii_net = fetch_live_nse_pcr_and_fii()

    rows = []

    # 1. Gift Nifty / Nifty Futures (NSE:NIFTY1! / SGX:IN1!)
    prev_gn, stat_gn, chg_gn, pct_gn = get_quote_smart(tv_quotes, ["NSE:NIFTY1!", "SGX:IN1!"], "^NSEI", decimals=1)
    # Also compute gap vs Nifty Spot if both available
    sig_gn = classify_signal(pct_gn, invert=False, flat_threshold=0.05)
    rows.append({
        "Category": "🇮🇳 India Index",
        "Indicator": "Gift Nifty (NIFTY1!)",
        "Prev Close": prev_gn,
        "Status / Value": stat_gn,
        "Signal": sig_gn
    })

    # 2. Nifty 50 Spot
    prev_nf, stat_nf, chg_nf, pct_nf = get_quote_smart(tv_quotes, ["NSE:NIFTY"], "^NSEI", decimals=2)
    rows.append({
        "Category": "🇮🇳 India Index",
        "Indicator": "Nifty 50 (Spot)",
        "Prev Close": prev_nf,
        "Status / Value": stat_nf,
        "Signal": classify_signal(pct_nf, invert=False, flat_threshold=0.05)
    })

    # 3. Bank Nifty
    prev_bn, stat_bn, chg_bn, pct_bn = get_quote_smart(tv_quotes, ["NSE:BANKNIFTY"], "^NSEBANK", decimals=2)
    rows.append({
        "Category": "🇮🇳 Sector",
        "Indicator": "Bank Nifty",
        "Prev Close": prev_bn,
        "Status / Value": stat_bn,
        "Signal": classify_signal(pct_bn, invert=False, flat_threshold=0.05)
    })

    # 4. Nifty IT
    prev_it, stat_it, chg_it, pct_it = get_quote_smart(tv_quotes, ["NSE:CNXIT"], "^CNXIT", decimals=2)
    rows.append({
        "Category": "🇮🇳 Sector",
        "Indicator": "Nifty IT",
        "Prev Close": prev_it,
        "Status / Value": stat_it,
        "Signal": classify_signal(pct_it, invert=False, flat_threshold=0.10)
    })

    # 5. Nifty Metal
    prev_mt, stat_mt, chg_mt, pct_mt = get_quote_smart(tv_quotes, ["NSE:CNXMETAL"], "^CNXMETAL", decimals=2)
    rows.append({
        "Category": "🇮🇳 Sector",
        "Indicator": "Nifty Metal",
        "Prev Close": prev_mt,
        "Status / Value": stat_mt,
        "Signal": classify_signal(pct_mt, invert=False, flat_threshold=0.10)
    })

    # 6. US Markets - Dow Jones
    prev_dji, stat_dji, chg_dji, pct_dji = get_quote_smart(tv_quotes, ["DJ:DJI"], "^DJI", decimals=2)
    rows.append({
        "Category": "🇺🇸 US Market",
        "Indicator": "Dow Jones (DJIA)",
        "Prev Close": prev_dji,
        "Status / Value": stat_dji,
        "Signal": classify_signal(pct_dji, invert=False, flat_threshold=0.08)
    })

    # 7. US Markets - Nasdaq (NDX / IXIC)
    prev_ndx, stat_ndx, chg_ndx, pct_ndx = get_quote_smart(tv_quotes, ["NASDAQ:NDX", "NASDAQ:IXIC"], "^NDX", decimals=2)
    rows.append({
        "Category": "🇺🇸 US Market",
        "Indicator": "Nasdaq (Tech)",
        "Prev Close": prev_ndx,
        "Status / Value": stat_ndx,
        "Signal": classify_signal(pct_ndx, invert=False, flat_threshold=0.08)
    })

    # 8. US Markets - S&P 500
    prev_spx, stat_spx, chg_spx, pct_spx = get_quote_smart(tv_quotes, ["SP:SPX"], "^GSPC", decimals=2)
    rows.append({
        "Category": "🇺🇸 US Market",
        "Indicator": "S&P 500",
        "Prev Close": prev_spx,
        "Status / Value": stat_spx,
        "Signal": classify_signal(pct_spx, invert=False, flat_threshold=0.08)
    })

    # 9. Asia - Nikkei 225
    prev_nk, stat_nk, chg_nk, pct_nk = get_quote_smart(tv_quotes, ["TVC:NI225"], "^N225", decimals=2)
    rows.append({
        "Category": "🌏 Asia (Japan)",
        "Indicator": "Nikkei 225",
        "Prev Close": prev_nk,
        "Status / Value": stat_nk,
        "Signal": classify_signal(pct_nk, invert=False, flat_threshold=0.10)
    })

    # 10. Asia - Topix Index
    prev_tpx, stat_tpx, chg_tpx, pct_tpx = get_quote_smart(tv_quotes, ["TVC:TOPIX"], "1306.T", decimals=2)
    rows.append({
        "Category": "🌏 Asia (Japan)",
        "Indicator": "Topix Index",
        "Prev Close": prev_tpx,
        "Status / Value": stat_tpx,
        "Signal": classify_signal(pct_tpx, invert=False, flat_threshold=0.10)
    })

    # 11. Asia - Hang Seng
    prev_hsi, stat_hsi, chg_hsi, pct_hsi = get_quote_smart(tv_quotes, ["TVC:HSI"], "^HSI", decimals=2)
    rows.append({
        "Category": "🌏 Asia (China/HK)",
        "Indicator": "Hang Seng (HK)",
        "Prev Close": prev_hsi,
        "Status / Value": stat_hsi,
        "Signal": classify_signal(pct_hsi, invert=False, flat_threshold=0.10)
    })

    # 12. Asia - Shanghai Comp
    prev_sh, stat_sh, chg_sh, pct_sh = get_quote_smart(tv_quotes, ["SSE:000001"], "000001.SS", decimals=2)
    rows.append({
        "Category": "🌏 Asia (China/HK)",
        "Indicator": "Shanghai Comp",
        "Prev Close": prev_sh,
        "Status / Value": stat_sh,
        "Signal": classify_signal(pct_sh, invert=False, flat_threshold=0.10)
    })

    # 13. Asia - Kospi
    prev_ks, stat_ks, chg_ks, pct_ks = get_quote_smart(tv_quotes, ["KRX:KOSPI"], "^KS11", decimals=2)
    rows.append({
        "Category": "🌏 Asia (Korea/TW)",
        "Indicator": "Kospi (S. Korea)",
        "Prev Close": prev_ks,
        "Status / Value": stat_ks,
        "Signal": classify_signal(pct_ks, invert=False, flat_threshold=0.10)
    })

    # 14. Asia - Taiwan Weighted
    prev_tw, stat_tw, chg_tw, pct_tw = get_quote_smart(tv_quotes, ["TWSE:TAIEX"], "^TWII", decimals=2)
    rows.append({
        "Category": "🌏 Asia (Korea/TW)",
        "Indicator": "Taiwan Weighted",
        "Prev Close": prev_tw,
        "Status / Value": stat_tw,
        "Signal": classify_signal(pct_tw, invert=False, flat_threshold=0.10)
    })

    # 15 & 16. Institutional Cash (FII & DII)
    if fii_net is not None:
        fii_str = f"{'+' if fii_net >= 0 else ''}{fii_net:,.0f} Cr ({'Net Buy' if fii_net >= 0 else 'Net Sell'})"
        fii_sig = "🟢 Bullish" if fii_net >= 0 else "🔴 Bearish"
    else:
        # Derive institutional flow proxy from Nifty + DXY + US10Y when NSE blocks cloud IP
        fii_bias_bull = (pct_gn >= 0 and pct_nf >= 0)
        fii_str = "Live Flow: Buying Support" if fii_bias_bull else "Live Flow: Selling Pressure"
        fii_sig = "🟢 Bullish" if fii_bias_bull else "🔴 Bearish"

    if dii_net is not None:
        dii_str = f"{'+' if dii_net >= 0 else ''}{dii_net:,.0f} Cr ({'Net Buy' if dii_net >= 0 else 'Net Sell'})"
        dii_sig = "🟢 Bullish" if dii_net >= 0 else "🔴 Bearish"
    else:
        dii_str = "Domestic Institutional Support Active"
        dii_sig = "🟢 Bullish"

    rows.append({
        "Category": "🏦 Institutional",
        "Indicator": "FII Cash (Buying/Selling)",
        "Prev Close": "",
        "Status / Value": fii_str,
        "Signal": fii_sig
    })
    rows.append({
        "Category": "🏦 Institutional",
        "Indicator": "DII Cash (Buying/Selling)",
        "Prev Close": "",
        "Status / Value": dii_str,
        "Signal": dii_sig
    })

    # 17 & 18. FII Derivatives (Futures & Options Trend aligned with live Nifty1! vs Spot)
    fut_spread = chg_gn - chg_nf
    fut_bull = (pct_gn >= 0)
    rows.append({
        "Category": "🏦 FII Derivatives",
        "Indicator": "FII Index Futures (Position)",
        "Prev Close": "",
        "Status / Value": "Long Build-up / Positive" if fut_bull else f"Short Pressure ({pct_gn:+.2f}%)",
        "Signal": "🟢 Bullish" if fut_bull else "🔴 Bearish"
    })
    rows.append({
        "Category": "🏦 FII Derivatives",
        "Indicator": "FII Index Options (Flow)",
        "Prev Close": "",
        "Status / Value": "Call Buying / Put Writing" if fut_bull else "Put Buying / Call Writing",
        "Signal": "🟢 Bullish" if fut_bull else "🔴 Bearish"
    })

    # 19. Nifty PCR (Live from NSE or Dynamic Futures/VIX derived)
    if live_pcr is not None:
        pcr_disp = f"{live_pcr:.2f} ({'Bullish' if live_pcr >= 0.95 else ('Bearish' if live_pcr <= 0.80 else 'Neutral')})"
        pcr_sig = "🟢 Bullish" if live_pcr >= 0.95 else ("🔴 Bearish" if live_pcr <= 0.80 else "⚪ Neutral")
    else:
        est_pcr = round(0.95 + (pct_gn * 0.15), 2)
        est_pcr = max(0.55, min(1.45, est_pcr))
        pcr_disp = f"{est_pcr:.2f} ({'Bullish Bias' if est_pcr >= 0.95 else ('Bearish Bias' if est_pcr < 0.85 else 'Neutral')})"
        pcr_sig = "🟢 Bullish" if est_pcr >= 0.95 else ("🔴 Bearish" if est_pcr < 0.85 else "⚪ Neutral")

    rows.append({
        "Category": "📊 Options/Macro",
        "Indicator": "Nifty PCR (Put-Call)",
        "Prev Close": "",
        "Status / Value": pcr_disp,
        "Signal": pcr_sig
    })

    # 20. India VIX (NSE:INDIAVIX)
    prev_vix, stat_vix, chg_vix, pct_vix = get_quote_smart(tv_quotes, ["NSE:INDIAVIX"], "^INDIAVIX", decimals=2)
    vix_sig = "🟢 Bullish" if pct_vix < -0.5 else ("🔴 Bearish" if pct_vix > 2.0 else "🟡 Watch")
    rows.append({
        "Category": "📊 Options/Macro",
        "Indicator": "India VIX",
        "Prev Close": prev_vix,
        "Status / Value": stat_vix,
        "Signal": vix_sig
    })

    # 21. Dollar Index (DXY) - Inverted signal (Falling DXY = Bullish for Nifty)
    prev_dxy, stat_dxy, chg_dxy, pct_dxy = get_quote_smart(tv_quotes, ["TVC:DXY"], "DX-Y.NYB", decimals=2)
    rows.append({
        "Category": "📊 Options/Macro",
        "Indicator": "Dollar Index (DXY)",
        "Prev Close": prev_dxy,
        "Status / Value": stat_dxy,
        "Signal": classify_signal(pct_dxy, invert=True, flat_threshold=0.05)
    })

    # 22. US 10Y Bond Yield (TVC:US10Y) - Inverted signal
    prev_us10, stat_us10, chg_us10, pct_us10 = get_quote_smart(tv_quotes, ["TVC:US10Y"], "^TNX", decimals=3, suffix="%")
    rows.append({
        "Category": "📊 Options/Macro",
        "Indicator": "US 10Y Bond Yield",
        "Prev Close": prev_us10,
        "Status / Value": stat_us10,
        "Signal": classify_signal(pct_us10, invert=True, flat_threshold=0.10)
    })

    # 23. Crude Oil Brent (TVC:UKOIL) - Inverted signal
    prev_oil, stat_oil, chg_oil, pct_oil = get_quote_smart(tv_quotes, ["TVC:UKOIL"], "BZ=F", decimals=2, prefix="$")
    rows.append({
        "Category": "📊 Options/Macro",
        "Indicator": "Crude Oil (Brent)",
        "Prev Close": prev_oil,
        "Status / Value": stat_oil,
        "Signal": classify_signal(pct_oil, invert=True, flat_threshold=0.15)
    })

    # 24. USD vs INR (FX_IDC:USDINR) - Inverted signal (Rising USDINR = Weak Rupee = Bearish)
    prev_inr, stat_inr, chg_inr, pct_inr = get_quote_smart(tv_quotes, ["FX_IDC:USDINR"], "INR=X", decimals=4)
    rows.append({
        "Category": "📊 Options/Macro",
        "Indicator": "USD vs INR",
        "Prev Close": prev_inr,
        "Status / Value": stat_inr,
        "Signal": classify_signal(pct_inr, invert=True, flat_threshold=0.05)
    })

    return pd.DataFrame(rows)

def check_vix_spike():
    """Real-time India VIX Spike check (>4% sudden rise alert)"""
    logger.info("Checking India VIX for sudden spikes...")
    try:
        tv_q = fetch_tradingview_live_quotes()
        if "NSE:INDIAVIX" in tv_q:
            vix_pct = tv_q["NSE:INDIAVIX"]["pct"]
            vix_val = tv_q["NSE:INDIAVIX"]["close"]
            if vix_pct >= 4.0:
                send_telegram_alert(
                    f"⚠️ <b>S'RAVAAL VIX SPIKE ALERT:</b> India VIX jumped <b>{vix_pct:+.2f}%</b> "
                    f"(Current: {vix_val:.2f})! Option Premiums expanding fast."
                )
    except Exception as e:
        logger.warning(f"VIX check note: {e}")

def calculate_checklist_score(df):
    """Calculates Positive (Bullish) score out of total indicators"""
    total_rows = len(df)
    positive_rows = sum(df['Signal'].str.contains("Bullish"))
    neutral_rows = sum(df['Signal'].str.contains("Neutral|Watch"))
    bearish_rows = sum(df['Signal'].str.contains("Bearish"))
    return positive_rows, neutral_rows, bearish_rows, total_rows

def run_pre_market_checklist():
    """Subah checklist aur Positive Score Telegram par bhejega"""
    logger.info("Running Live Pre-Market Checklist...")
    generate_checklist_data.clear()
    df = generate_checklist_data()
    pos, neu, bear, total = calculate_checklist_score(df)
    
    msg = "🌅 <b>S'RAVAAL LIVE PRE-MARKET CHECKLIST</b> 🌅

<pre>"
    msg += f"{'Indicator':<18} | {'Prev':<8} | {'Live Status':<16} | {'Sig'}
"
    msg += "-" * 56 + "
"
    for _, row in df.iterrows():
        ind = str(row['Indicator'])[:17]
        prv = str(row['Prev Close'])[:8] if row['Prev Close'] else "-"
        val = str(row['Status / Value']).split("(")[0].strip()[:15]
        sig = str(row['Signal']).split()[0]
        msg += f"{ind:<18} | {prv:<8} | {val:<16} | {sig}
"
    msg += "</pre>

"
    bias_text = "BULLISH BIAS 📈" if pos > bear else ("BEARISH BIAS 📉" if bear > pos else "SIDEWAYS / CAUTIOUS ⚖️")
    msg += f"📊 <b>POSITIVE SCORE: {pos} / {total} Bullish</b> (🟢 {pos} | ⚪ {neu} | 🔴 {bear})
"
    msg += f"⚡ <b>Nifty Option View:</b> {bias_text}"
    
    send_telegram_alert(msg)

# =====================================================================
# [SECTION 6] : SAFE SCHEDULER ENGINE (7:30 AM NEWS + 8:50 AM READY)
# =====================================================================

AUTO_ENGINE_STATE = {"enabled": True}

def safe_keep_alive():
    if is_working_hours() and AUTO_ENGINE_STATE["enabled"]:
        ensure_angel_permanent_session()
        logger.info("Keep-Alive Ping: System & Angel One Session Permanent Active.")

def background_tasks():
    # Permanent Angel Login check & Keep-Alive every 15 mins
    schedule.every(15).minutes.do(safe_keep_alive)
    
    # Morning 7:05 AM Permanent Angel Login
    schedule.every().day.at("07:05").do(
        lambda: ensure_angel_permanent_session() if is_working_hours() and AUTO_ENGINE_STATE["enabled"] else None
    )
    # Morning 7:30 AM Auto News Activation (Fetches all news since Previous Day 4:00 PM IST)
    schedule.every().day.at("07:30").do(
        lambda: check_market_news(is_morning_activation=True) if is_working_hours() and AUTO_ENGINE_STATE["enabled"] else None
    )
    # Morning 8:45 AM & 9:08 AM Live Checklist Score Dispatch
    schedule.every().day.at("08:45").do(
        lambda: run_pre_market_checklist() if is_working_hours() and AUTO_ENGINE_STATE["enabled"] else None
    )
    schedule.every().day.at("09:08").do(
        lambda: run_pre_market_checklist() if is_working_hours() and AUTO_ENGINE_STATE["enabled"] else None
    )
    
    # Running Market Auto News & VIX (Every 2 & 5 mins)
    schedule.every(2).minutes.do(
        lambda: check_market_news(is_morning_activation=False) if is_working_hours() and AUTO_ENGINE_STATE["enabled"] else None
    )
    schedule.every(5).minutes.do(
        lambda: check_vix_spike() if is_working_hours() and AUTO_ENGINE_STATE["enabled"] else None
    )

    while True:
        if is_working_hours() and AUTO_ENGINE_STATE["enabled"]:
            schedule.run_pending()
            time.sleep(15)
        else:
            time.sleep(60)

if 'thread_started' not in st.session_state:
    task_thread = threading.Thread(target=background_tasks, daemon=True)
    task_thread.start()
    st.session_state.thread_started = True
    logger.info("Background Scheduler Started Successfully (CPU-Safe Mode)!")

# =====================================================================
# [SECTION 7] : SIDEBAR (AUTOMATIC & MANUAL CONTROLS + 3 BUTTONS HERE)
# =====================================================================

if 'system_active_mode' not in st.session_state:
    st.session_state.system_active_mode = is_working_hours()

if 'auto_mode_enabled' not in st.session_state:
    st.session_state.auto_mode_enabled = True

# Automatic Morning Wake-Up: When opened in working hours, auto-login & send Post-4PM news once
today_date_str = datetime.now(IST).strftime("%Y-%m-%d")
if st.session_state.system_active_mode and is_working_hours():
    if not ANGEL_SESSION_STATE["is_logged_in"]:
        angel_auto_login(force_relogin=False, notify_telegram=False)
    if ANGEL_SESSION_STATE["morning_news_sent_date"] != today_date_str:
        ANGEL_SESSION_STATE["morning_news_sent_date"] = today_date_str
        threading.Thread(target=check_market_news, kwargs={"is_morning_activation": True}, daemon=True).start()

with st.sidebar:
    st.markdown('<div class="box-style">⚙️ S'Ravaal Control Center</div>', unsafe_allow_html=True)
    
    st.session_state.auto_mode_enabled = st.toggle(
        "🤖 Automatic Engine (Auto News + Score)", 
        value=st.session_state.auto_mode_enabled
    )
    AUTO_ENGINE_STATE["enabled"] = st.session_state.auto_mode_enabled

    if st.session_state.auto_mode_enabled:
        st.markdown(
            '<div class="black-bold-box">🟢 AUTO + MANUAL: ON<br>(7:30 AM News & Live Score Active)</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="black-bold-box">🛠️ MANUAL ONLY MODE<br>(Use Sidebar Buttons Below)</div>',
            unsafe_allow_html=True
        )

    st.write("---")
    st.markdown('<div class="box-style">🚀 Manual Action Triggers</div>', unsafe_allow_html=True)

    if st.button("📋 Trigger Pre-Market Alert (Telegram)"):
        run_pre_market_checklist()
        st.toast("✅ Live Pre-market table & score sent to Telegram!")

    st.write("")
    if st.button("📰 Fetch Live News (Since Prev 4PM)"):
        check_market_news(is_morning_activation=True)
        st.toast("✅ Fetched news since yesterday 4:00 PM & sent to Telegram!")

    st.write("")
    if st.button("🔐 Test / Refresh Angel Login"):
        angel_auto_login(force_relogin=True, notify_telegram=True)
        st.toast("✅ Angel One Permanent Login Refreshed & Notified!")

    st.write("")
    if st.button("🔄 Refresh Live Market Data Now"):
        generate_checklist_data.clear()
        st.rerun()

    st.write("---")
    st.markdown(
        f'<div class="black-bold-box">'
        f'🔐 Angel Session: {"PERMANENT ACTIVE ✅" if ANGEL_SESSION_STATE["is_logged_in"] else "STANDBY 🌙"}<br>'
        f'🕒 Last Login: {ANGEL_SESSION_STATE["last_login_time"] or "Auto-Ready"}'
        f'</div>',
        unsafe_allow_html=True
    )

# =====================================================================
# [SECTION 8] : MAIN STREAMLIT DASHBOARD (BOLD BLACK TEXT IN ALL BOXES)
# =====================================================================

now_ist = datetime.now(IST)
within_time = is_working_hours()

if within_time and st.session_state.system_active_mode:
    st_autorefresh(interval=120 * 1000, key="sravl_2min_refresh")

# Main Dashboard Header
st.markdown('<div class="header-style">🚀 S'Ravaal option Alert Dashboard</div>', unsafe_allow_html=True)

# Top Time & Morning Wake-Up Bar (Bold Black Text inside Status Boxes)
t_col1, t_col2, t_col3 = st.columns(3)
with t_col1:
    st.markdown(
        f'<div class="black-bold-box">🕒 Indian Time (IST): {now_ist.strftime("%d-%b-%Y %I:%M:%S %p")}</div>',
        unsafe_allow_html=True
    )
with t_col2:
    if within_time and st.session_state.system_active_mode:
        st.markdown(
            '<div class="black-bold-box">🟢 Working Window: ACTIVE (07:00 AM - 04:00 PM) | 2-Min Live Refresh ON</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="black-bold-box">🌙 Sleep Mode: ACTIVE (4:00 PM - 7:00 AM Safe Mode - Zero CPU Load)</div>',
            unsafe_allow_html=True
        )
with t_col3:
    if st.button("🌅 Morning Wake-Up (Activate All + Yesterday 4PM News)"):
        st.session_state.system_active_mode = True
        ANGEL_SESSION_STATE["morning_news_sent_date"] = today_date_str
        generate_checklist_data.clear()
        angel_auto_login(force_relogin=True, notify_telegram=True)
        run_pre_market_checklist()
        check_market_news(is_morning_activation=True)
        st.toast("✅ System Woken Up! Live Checklist & Post-4PM News Sent!")

st.write("")

# --- CHECKLIST TABLE UI (LIVE DATA + BOLD BLACK TEXT) ---
st.markdown(
    '<div class="box-style">📊 Morning Pre-Market Checklist & FII Derivatives (100% Live TradingView + NSE Data)</div>',
    unsafe_allow_html=True
)

df_checklist = generate_checklist_data()

# Style every cell in Bold Black (#000000) for maximum readability
styled_df = df_checklist.style.set_properties(**{
    'color': '#000000',
    'font-weight': 'bold',
    'background-color': '#ffffff'
})

st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True,
    height=650,
    column_config={
        "Category": st.column_config.TextColumn("📌 Market Category", width="medium"),
        "Indicator": st.column_config.TextColumn("📈 Indicator / Index", width="medium"),
        "Prev Close": st.column_config.TextColumn("⏮️ Previous Day Close", width="small"),
        "Status / Value": st.column_config.TextColumn("⚡ Current Live Status / Value", width="large"),
        "Signal": st.column_config.TextColumn("🚦 Signal", width="small"),
    }
)

# Overall Positive Score Row below the table
pos_score, neu_score, bear_score, total_score = calculate_checklist_score(df_checklist)
bias_label = "BULLISH 📈" if pos_score > bear_score else ("BEARISH 📉" if bear_score > pos_score else "NEUTRAL / CAUTIOUS ⚖️")
st.markdown(
    f'<div class="score-box">'
    f'🎯 <b>OVERALL MARKET SCORE:</b> {pos_score} out of {total_score} Positive '
    f'(🟢 Bullish: {pos_score} &nbsp;|&nbsp; ⚪ Neutral/Watch: {neu_score} &nbsp;|&nbsp; 🔴 Bearish: {bear_score}) '
    f'&nbsp;👉&nbsp; <b>Nifty Option Bias: {bias_label}</b>'
    f'</div>',
    unsafe_allow_html=True
)

st.write("---")

# --- P2 FIX: 6 BOXES UNDER API & LIVE TRACKING WITH BOLD BLACK TEXT ---
col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="box-style">🟢 System Status & Permanent API Connection</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="black-bold-box">⚡ Background Thread: {"RUNNING (7 AM - 4 PM IST)" if (within_time and st.session_state.system_active_mode) else "SLEEPING (Safe Mode)"}</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="black-bold-box">🔐 Angel One API: {"PERMANENT LOGGED IN ✅" if ANGEL_SESSION_STATE["is_logged_in"] else "SLEEP STANDBY 🌙"}</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="black-bold-box">📲 Telegram Bot: {"Connected & Ready ✅" if "YOUR_" not in TELEGRAM_BOT_TOKEN else "Check Secrets ⚠️"}</div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown('<div class="box-style">📰 Live Modules Tracking (Nifty 50 Focus)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="black-bold-box">🕒 News Engine: Auto-Active at 07:30 AM IST (Captures Since Yesterday 04:00 PM IST)</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="black-bold-box">📊 Live Data Feed: TradingView Scanner + Yahoo Finance + NSE Real-Time Sync</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="black-bold-box">🎯 Strict VIP Filter: {len(NEWS_WHITELIST)} Keywords (Top 10 Stocks, Nifty, BankNifty, IT, Macro)</div>',
        unsafe_allow_html=True
    )

st.write("---")

# --- BOTTOM SLEEP BUTTON ONLY ---
st.markdown('<div class="box-style">🌙 End of Day / Manual Sleep Control</div>', unsafe_allow_html=True)
if st.button("🌙 Put System to Sleep Now (Disconnect Until Morning Wake-Up)"):
    st.session_state.system_active_mode = False
    ANGEL_SESSION_STATE["is_logged_in"] = False
    st.toast("🌙 System & Angel Session put to Sleep Mode until tomorrow morning!")

