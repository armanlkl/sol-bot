import yfinance as yf
import pandas as pd
import numpy as np
import requests
import sys

# تنظیمات تلگرام
TELEGRAM_TOKEN = "8937330320:AAFW6IwsZbE8yMidb2Eg397JKZytJ-LvT2o"
CHAT_IDS = ["7312827776", "449591109"]
SYMBOL = "SOL-USD"
LEVERAGE = 20

def send_telegram(msg):
    for chat_id in CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=15)
        except: pass

try:
    df = yf.download(tickers=SYMBOL, period="60d", interval="1h", progress=False)
    if df.empty or len(df) < 200:
        print("Data insufficient")
        sys.exit(0)

    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]

    # --- محاسبات دستی ---
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['dh'] = df['high'].shift(1).rolling(20).max()
    df['dl'] = df['low'].shift(1).rolling(20).min()
    
    df['tr'] = np.maximum(df['high'] - df['low'], 
                          np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                     abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(window=14).mean()
    
    up = df['high'].diff(); down = -df['low'].diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0)
    minus_dm = np.where((down > up) & (down > 0), down, 0)
    tr_sum = df['tr'].rolling(window=14).sum()
    plus_di = 100 * (pd.Series(plus_dm).rolling(window=14).sum() / tr_sum)
    minus_di = 100 * (pd.Series(minus_dm).rolling(window=14).sum() / tr_sum)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df['adx'] = dx.rolling(window=14).mean()
    vma = df['volume'].rolling(20).mean()

    last = df.iloc[-1]
    price = float(last['close'])
    
    # --- گزارش فارسی ۱۵ دقیقه‌ای ---
    status_icon = "🟢" if price > last['ema200'] else "🔴"
    status_text = "صعودی (بالای EMA200)" if price > last['ema200'] else "نزولی (زیر EMA200)"
    
    report_msg = (
        f"📊 *گزارش قیمت بازار*\n"
        f"────────────────\n"
        f"💎 ارز: SOL/USDT\n"
        f"💵 قیمت لحظه‌ای: *${price:.2f}*\n"
        f"📈 روند کلی: {status_icon} {status_text}\n"
        f"────────────────"
    )
    send_telegram(report_msg)

    # --- بررسی سیگنال ۶۵۲٪ ---
    vol_ok = last['volume'] > (vma.iloc[-1] * 1.2)
    adx_ok = last['adx'] > 25
    
    if (price > last['ema200']) and (price > last['dh']) and adx_ok and vol_ok:
        side = "🟢 LONG (خرید)"
        sl = price - (last['atr'] * 2)
        tp = price + (last['atr'] * 3)
        signal_msg = (
            f"🚨 *سیگنال معامله جدید (Logic 652%)*\n"
            f"────────────────\n"
            f"⚡️ پوزیشن: {side}\n"
            f"📌 *قیمت ورود:* *${price:.2f}*\n"
            f"🎯 *اهرم:* {LEVERAGE}x\n"
            f"🛑 *حد ضرر:* ${sl:.2f}\n"
            f"🎯 *تارگت:* ${tp:.2f}\n"
            f"────────────────"
        )
        send_telegram(signal_msg)
        
    elif (price < last['ema200']) and (price < last['dl']) and adx_ok and vol_ok:
        side = "🔴 SHORT (فروش)"
        sl = price + (last['atr'] * 2)
        tp = price - (last['atr'] * 3)
        signal_msg = (
            f"🚨 *سیگنال معامله جدید (Logic 652%)*\n"
            f"────────────────\n"
            f"⚡️ پوزیشن: {side}\n"
            f"📌 *قیمت ورود:* *${price:.2f}*\n"
            f"🎯 *اهرم:* {LEVERAGE}x\n"
            f"🛑 *حد ضرر:* ${sl:.2f}\n"
            f"🎯 *تارگت:* ${tp:.2f}\n"
            f"────────────────"
        )
        send_telegram(signal_msg)

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
