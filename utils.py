import logging
import time
from dydx3 import Client
import numpy as np
import pandas as pd
import talib
from textblob import TextBlob
import requests

def get_precision(client, symbol):
    market = client.public.get_markets(market=symbol)
    precision = market['markets'][symbol]['tickSize']
    quantity_precision = market['markets'][symbol]['stepSize']
    return quantity_precision, precision

def get_price(client, symbol):
    ticker = client.public.get_ticker(market=symbol)
    return float(ticker['ticker']['price'])

def get_volume(client, symbol):
    volume = client.public.get_24_hr_stats(market=symbol)
    return float(volume['markets'][symbol]['volume'])

def adjust_sleep_time(client, symbol):
    return 5

def execute_with_retry(client, func, *args, **kwargs):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error al ejecutar la orden: {e}")
            time.sleep(2 ** attempt)
    return None

def get_balance(client):
    account = client.private.get_account()
    return float(account['account']['quoteBalance'])

def validate_balance(client, budget):
    balance = get_balance(client)
    return balance >= budget

def get_atr(client, symbol, period=14):
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
    df["RSI"] = talib.RSI(df["close"].values, timeperiod=14)
    df["EMA12"] = pd.Series(df["close"]).ewm(span=12, adjust=False).mean()
    df["EMA26"] = pd.Series(df["close"]).ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["SMA50"] = talib.SMA(df["close"].values, timeperiod=50)
    df["EMA200"] = talib.EMA(df["close"].values, timeperiod=200)
    return df

def sentiment_analysis(text):
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def get_market_sentiment():
    url = "https://api.alternative.me/fng/?limit=1"
    response = requests.get(url).json()
    sentiment_value = response['data'][0]['value']
    sentiment_classification = response['data'][0]['value_classification']
    return sentiment_value, sentiment_classification

def calculate_var(returns, confidence_level=0.95):
    if len(returns) < 2:
        return None
    mean = np.mean(returns)
    std_dev = np.std(returns)
    var = np.percentile(returns, (1 - confidence_level) * 100)
    return var

def optimize_portfolio(returns, risk_free_rate=0.01):
    cov_matrix = np.cov(returns)
    mean_returns = np.mean(returns, axis=1)
    num_assets = len(mean_returns)
    weights = np.random.random(num_assets)
    weights /= np.sum(weights)
    portfolio_return = np.sum(mean_returns * weights)
    portfolio_std_dev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_std_dev
    return weights, portfolio_return, portfolio_std_dev, sharpe_ratio

def backtest_scenario(client, symbol, scenarios):
    results = {}
    for scenario in scenarios:
        result = backtest(client, symbol, scenario['profit_threshold'], scenario['trailing_stop'])
        results[scenario['name']] = result
    return results
