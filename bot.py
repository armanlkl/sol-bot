import yfinance as yf
import pandas as pd
import numpy as np
import requests
import sys

TELEGRAM_TOKEN = "8937330320:AAFW6IwsZbE8yMidb2Eg397JKZytJ-LvT2o"
CHAT_IDS = ["7312827776", "449591109"]
SYMBOL = "SOL-USD"

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

    # --- محاسبات دستی اندیکاتورها ---
    # EMA 200
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # Donchian Channels
    df['dh'] = df['high'].shift(1).rolling(20).max()
    df['dl'] = df['low'].shift(1).rolling(20).min()
    
    # ATR 14
    high_low = df['high'] - df['low']
    high_cp = np.abs(df['high'] - df['close'].shift())
    low_cp = np.abs(df['low'] - df['close'].shift())
    df['tr'] = np.max([high_low, high_cp, low_cp], axis=0)
    df['atr'] = df['tr'].rolling(14).mean()
    
    # ADX 14 (ساده شده)
    plus_dm = df['high'].diff()
    minus_dm = df['low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    tr14 = df['tr'].rolling(14).sum()
    plus_di = 100 * (plus_dm.rolling(14).sum() / tr14)
    minus_di = 100 * (np.abs(minus_dm.rolling(14).sum()) / tr14)
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    df['adx'] = dx.rolling(14).mean()

    # فیلتر حجم
    vma = df['volume'].rolling(20).mean()
    
    last = df.iloc[-1]
    price = float(last['close'])
    
    # گزارش قیمت
    status = "🟢 Up" if price > last['ema200'] else "🔴 Down"
    send_telegram(f"📊 SOL Report\nPrice: `${price:.2f}`\nTrend: {status}")

    # بررسی سیگنال
    vol_ok = last['volume'] > (vma.iloc[-1] * 1.2)
    adx_ok = last['adx'] > 25
    
    if (price > last['ema200']) and (price > last['dh']) and adx_ok and vol_ok:
        send_telegram(f"🚨 SIGNAL: LONG SOL at `${price:.2f}`")
    elif (price < last['ema200']) and (price < last['dl']) and adx_ok and vol_ok:
        send_telegram(f"🚨 SIGNAL: SHORT SOL at `${price:.2f}`")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
