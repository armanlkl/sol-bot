import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests

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

def check_market():
    df = yf.download(tickers=SYMBOL, period="30d", interval="1h", progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    
    df['ema200'] = ta.ema(df['close'], length=200)
    df['dh'] = df['high'].shift(1).rolling(20).max()
    df['dl'] = df['low'].shift(1).rolling(20).min()
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    df['vma'] = ta.sma(df['volume'], length=20)
    df['adx'] = ta.adx(df['high'], df['low'], df['close'], length=14)['ADX_14']
    
    last = df.iloc[-1]
    price = last['close']
    ema = last['ema200']
    status = "🟢 صعودی (بالای EMA200)" if price > ema else "🔴 نزولی (زیر EMA200)"
    
    # ۱. همیشه قیمت رو گزارش کن
    report_msg = (
        f"📊 *گزارش قیمت بازار*\n"
        f"────────────────\n"
        f"💎 ارز: SOL/USDT\n"
        f"💵 قیمت لحظه‌ای: *${price:.2f}*\n"
        f"📈 روند کلی: {status}\n"
        f"────────────────"
    )
    send_telegram(report_msg)
    
    # ۲. بررسی سیگنال ۶۵۲٪
    vol_ok = last['volume'] > (last['vma'] * 1.2)
    adx_ok = last['adx'] > 25
    l_cond = (price > ema) and (price > last['dh']) and adx_ok and vol_ok
    s_cond = (price < ema) and (price < last['dl']) and adx_ok and vol_ok
    
    if l_cond or s_cond:
        side = "🟢 LONG (خرید)" if l_cond else "🔴 SHORT (فروش)"
        atr = last['atr']
        sl = (price - (atr * 2)) if l_cond else (price + (atr * 2))
        tp1 = (price + (atr * 3)) if l_cond else (price - (atr * 3))
        
        signal_msg = (
            f"🚨 *سیگنال معامله جدید (منطق ۶۵۲٪)*\n"
            f"────────────────\n"
            f"⚡️ پوزیشن: {side}\n"
            f"📌 *قیمت دقیق ورود:* *${price:.2f}*\n"
            f"🎯 *اهرم:* {LEVERAGE}x\n"
            f"🛑 *استاپ (SL):* ${sl:.2f}\n"
            f"🎯 *هدف (TP):* ${tp1:.2f}\n"
            f"────────────────"
        )
        send_telegram(signal_msg)

check_market()
