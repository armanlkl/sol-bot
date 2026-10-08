import yfinance as yf
import pandas as pd
import pandas_ta as ta
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
    print("Downloading data...")
    df = yf.download(tickers=SYMBOL, period="30d", interval="1h", progress=False)
    
    if df.empty:
        print("Error: Data is empty")
        sys.exit(1)

    if isinstance(df.columns, pd.MultiIndex): 
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    
    df['ema200'] = ta.ema(df['close'], length=200)
    df['dh'] = df['high'].shift(1).rolling(20).max()
    df['dl'] = df['low'].shift(1).rolling(20).min()
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    df['vma'] = ta.sma(df['volume'], length=20)
    df['adx'] = ta.adx(df['high'], df['low'], df['close'], length=14)['ADX_14']
    
    last = df.iloc[-1]
    price = last['close']
    
    # گزارش قیمت
    status = "🟢 Up" if price > last['ema200'] else "🔴 Down"
    send_telegram(f"📊 SOL Report\nPrice: ${price:.2f}\nTrend: {status}")
    print("Report sent.")

    # بررسی سیگنال
    vol_ok = last['volume'] > (last['vma'] * 1.2)
    adx_ok = last['adx'] > 25
    if (price > last['ema200']) and (price > last['dh']) and adx_ok and vol_ok:
        send_telegram(f"🚨 SIGNAL: LONG SOL at ${price:.2f}")
    elif (price < last['ema200']) and (price < last['dl']) and adx_ok and vol_ok:
        send_telegram(f"🚨 SIGNAL: SHORT SOL at ${price:.2f}")

except Exception as e:
    print(f"Final Error: {e}")
    sys.exit(1)
