import logging
import numpy as np
import pandas as pd
import talib
from itertools import product
from bayes_opt import BayesianOptimization
from dydx3 import Client  # Importar la biblioteca de dYdX
from trading_bot.utils import get_technical_indicators, get_atr, get_price
from trading_bot.config import SYMBOLS, BUDGET, DEFAULT_PROFIT_THRESHOLD, DEFAULT_TRAILING_STOP, PROFIT_THRESHOLD_RANGE, TRAILING_STOP_RANGE
from trading_bot.ml_models import train_ml_model, predict_with_ml_model
from ml_models import train_ml_model, predict_with_ml_model

def backtest(client, symbol, profit_threshold, trailing_stop):
    ...
    # Entrenar modelo de ML
    model = train_ml_model(df)
    ...
    for i in range(200, len(df)):
        if df["RSI"].iloc[i] < 30 and df["MACD"].iloc[i] > df["Signal"].iloc[i] and \
                df["close"].iloc[i] > df["SMA50"].iloc[i] and df["close"].iloc[i] > df["EMA200"].iloc[i]:
            if position is None:
                # Predecir con modelo de ML
                prediction = predict_with_ml_model(model, df.iloc[:i])
                if prediction == "buy":
                    position = "long"
                    buy_price = df["close"].iloc[i]
                    quantity = BUDGET * 0.25 / buy_price
                    logging.info(f"Backtest Compra: Precio={buy_price}, Cantidad={quantity}")

def backtest(client, symbol, profit_threshold, trailing_stop):
    logging.info(f"Backtesting para {symbol} con profit_threshold={profit_threshold}, trailing_stop={trailing_stop}")
    klines = client.public.get_candles(market=symbol, resolution="1H", limit=500)  # Obtener datos de velas de dYdX
    close_prices = [float(k['close']) for k in klines['candles']]
    df = pd.DataFrame(close_prices, columns=["close"])
    df["RSI"] = talib.RSI(df["close"].values, timeperiod=14)
    df["EMA12"] = pd.Series(df["close"]).ewm(span=12, adjust=False).mean()
    df["EMA26"] = pd.Series(df["close"]).ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["SMA50"] = talib.SMA(df["close"].values, timeperiod=50)
    df["EMA200"] = talib.EMA(df["close"].values, timeperiod=200)
    
    # Entrenar modelo de ML
    model = train_ml_model(client, symbol)
    total_profit = 0
    position = None
    buy_price = 0
    quantity = 0
    max_drawdown = 0
    peak = -float("inf")
    returns = []

    for i in range(200, len(df)):
        if df["RSI"].iloc[i] < 30 and df["MACD"].iloc[i] > df["Signal"].iloc[i] and \
                df["close"].iloc[i] > df["SMA50"].iloc[i] and df["close"].iloc[i] > df["EMA200"].iloc[i]:
            if position is None:
                # Predecir con modelo de ML
                prediction = predict_with_ml_model(model, df.iloc[:i])
                if prediction == "buy":
                    position = "long"
                    buy_price = df["close"].iloc[i]
                    quantity = BUDGET * 0.25 / buy_price
                    logging.info(f"Backtest Compra: Precio={buy_price}, Cantidad={quantity}")
        elif (df["RSI"].iloc[i] > 70 or df["MACD"].iloc[i] < df["Signal"].iloc[i]) or \
                (position == "long" and df["close"].iloc[i] < buy_price * (1 - trailing_stop)):
            if position == "long":
                sell_price = df["close"].iloc[i]
                profit = (sell_price - buy_price) * quantity
                total_profit += profit
                returns.append(profit / (buy_price * quantity))
                logging.info(f"Backtest Venta: Precio={sell_price}, Ganancia={profit}")
                peak = max(peak, total_profit)
                drawdown = (peak - total_profit) / peak if peak != 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
                position = None

    sharpe_ratio = np.mean(returns) / np.std(returns) if returns else 0
    logging.info(f"Backtesting finalizado para {symbol}: Ganancia total={total_profit}, Max Drawdown={max_drawdown}, Sharpe Ratio={sharpe_ratio}")
    return {"total_profit": total_profit, "max_drawdown": max_drawdown, "sharpe_ratio": sharpe_ratio}

def optimize_parameters(client, symbol):
    def objective(profit_threshold, trailing_stop):
        result = backtest(client, symbol, profit_threshold, trailing_stop)
        return result["total_profit"]

    optimizer = BayesianOptimization(
        f=objective,
        pbounds={
            "profit_threshold": (min(PROFIT_THRESHOLD_RANGE), max(PROFIT_THRESHOLD_RANGE)),
            "trailing_stop": (min(TRAILING_STOP_RANGE), max(TRAILING_STOP_RANGE))
        },
        random_state=42,
    )
    optimizer.maximize(init_points=10, n_iter=30)
    best_params = optimizer.max["params"]
    logging.info(f"Parámetros óptimos para {symbol}: profit_threshold={best_params['profit_threshold']}, trailing_stop={best_params['trailing_stop']}")
    return best_params
