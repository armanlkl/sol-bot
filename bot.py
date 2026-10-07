import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import time
import threading
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Running 24/7!"

TELEGRAM_TOKEN = "8937330320:AAFW6IwsZbE8yMidb2Eg397JKZytJ-LvT2o"
CHAT_ID = "7312827776"
SYMBOL = "SOL-USD"
LEVERAGE = 15

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def check_market():
    df = yf.download(tickers=SYMBOL, period="30d", interval="1h", progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    df['ema200'] = ta.ema(df['close'], length=200)
    df['dh'] = df['high'].shift(1).rolling(20).max()
    df['dl'] = df['low'].shift(1).rolling(20).min()
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    df['adx'] = ta.adx(df['high'], df['low'], df['close'], length=14)['ADX_14']
    last = df.iloc[-1]
    long_cond = (last['close'] > last['ema200']) and (last['close'] > last['dh']) and (last['adx'] > 25)
    short_cond = (last['close'] < last['ema200']) and (last['close'] < last['dl']) and (last['adx'] > 25)
    return long_cond, short_cond, last['close'], last['atr']

def bot_loop():
    send_telegram("🚀 *ربات روی سرور ابری روشن شد!*")
    alerted = False
    while True:
        now = datetime.now()
        if now.minute == 55 and not alerted:
            lc, sc, price, atr = check_market()
            if lc: send_telegram(f"🟢 BUY SOL @ ${price:.2f}")
            if sc: send_telegram(f"🔴 SELL SOL @ ${price:.2f}")
            alerted = True
        if now.minute == 0: alerted = False
        time.sleep(30)

threading.Thread(target=bot_loop, daemon=True).start()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
