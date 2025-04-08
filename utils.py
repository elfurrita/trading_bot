import logging
import time
from dydx3 import Client
import numpy as np
import pandas as pd

def get_precision(client, symbol):
    # Ejemplo de función para obtener la precisión de cantidad y precio
    market = client.public.get_markets(market=symbol)
    precision = market['markets'][symbol]['tickSize']
    quantity_precision = market['markets'][symbol]['stepSize']
    return quantity_precision, precision

def get_price(client, symbol):
    # Ejemplo de función para obtener el precio actual
    ticker = client.public.get_ticker(market=symbol)
    return float(ticker['ticker']['price'])

def get_volume(client, symbol):
    # Ejemplo de función para obtener el volumen
    volume = client.public.get_24_hr_stats(market=symbol)
    return float(volume['markets'][symbol]['volume'])

def adjust_sleep_time(client, symbol):
    # Ejemplo de función para ajustar el tiempo de espera
    return 5

def execute_with_retry(client, func, *args, **kwargs):
    # Ejemplo de función para ejecutar una orden con reintentos
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error al ejecutar la orden: {e}")
            time.sleep(2 ** attempt)
    return None

def get_balance(client):
    # Ejemplo de función para obtener el balance
    account = client.private.get_account()
    return float(account['account']['quoteBalance'])

def validate_balance(client, budget):
    # Ejemplo de función para validar el balance
    balance = get_balance(client)
    return balance >= budget

def get_atr(client, symbol, period=14):
    # Ejemplo de función para calcular el ATR
    klines = client.public.get_candles(market=symbol, resolution="1H", limit=period)
    high_prices = [float(k['high']) for k in klines['candles']]
    low_prices = [float(k['low']) for k in klines['candles']]
    close_prices = [float(k['close']) for k in klines['candles']]
    df = pd.DataFrame({
        'high': high_prices,
        'low': low_prices,
        'close': close_prices
    })
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift())
    df['tr2'] = abs(df['low'] - df['close'].shift())
    tr = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    atr = tr.rolling(window=period).mean().iloc[-1]
    return atr

def get_technical_indicators(df):
    # Ejemplo de función para calcular indicadores técnicos
    df["RSI"] = talib.RSI(df["close"].values, timeperiod=14)
    df["EMA12"] = pd.Series(df["close"]).ewm(span=12, adjust=False).mean()
    df["EMA26"] = pd.Series(df["close"]).ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["SMA50"] = talib.SMA(df["close"].values, timeperiod=50)
    df["EMA200"] = talib.EMA(df["close"].values, timeperiod=200)
    return df
