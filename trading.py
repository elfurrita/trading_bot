import logging
import time
import numpy as np
import pandas as pd
from multiprocessing import Pool
from binance.client import Client
from binance.exceptions import BinanceAPIException
from trading_bot.utils import get_precision, get_price, get_volume, adjust_sleep_time, execute_with_retry, get_balance, validate_balance, get_atr, get_technical_indicators
from trading_bot.config import SYMBOLS, BUDGET, DEFAULT_PROFIT_THRESHOLD, DEFAULT_TRAILING_STOP, REAL_MARKET
from trading_bot.backtesting import optimize_parameters

# Archivo de registro
log_file = "transacciones.csv"
with open(log_file, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Acción", "Símbolo", "Precio", "Cambio %", "Cantidad", "Saldo Restante"])

def log_transaction(action, price, change, quantity, remaining_balance):
    """
    Registra una transacción en el archivo de registro.

    Args:
        action (str): Acción realizada ("Compra" o "Venta").
        price (float): Precio de la transacción.
        change (float): Cambio porcentual.
        quantity (float): Cantidad comprada o vendida.
        remaining_balance (float): Saldo restante.
    """
    with open(log_file, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([action, symbol, price, change, quantity, remaining_balance])

def get_avg_volume(client, symbol, period=30):
    """
    Obtiene el volumen promedio de trading para un símbolo dado en un periodo específico.

    Args:
        client (Client): Cliente de Binance.
        symbol (str): Símbolo de la criptomoneda.
        period (int): Periodo en horas para calcular el volumen promedio.

    Returns:
        float: Volumen promedio.
    """
    klines = client.get_klines(symbol=symbol, interval="1h", limit=period)
    volumes = [float(k[5]) for k in klines]
    return np.mean(volumes)

def calculate_position_size(client, symbol, buy_price):
    """
    Calcula el tamaño de la posición basado en el riesgo y el ATR.

    Args:
        client (Client): Cliente de Binance.
        symbol (str): Símbolo de la criptomoneda.
        buy_price (float): Precio de compra.

    Returns:
        float: Tamaño de la posición.
    """
    atr = get_atr(client, symbol)
    risk_amount = BUDGET * RISK_PERCENTAGE
    stop_distance = atr  # Utilizando ATR como medida de riesgo
    if stop_distance == 0:
        return BUDGET * 0.25 / buy_price
    return risk_amount / stop_distance

def macd_confirmation(client, symbol):
    """
    Confirma una señal de compra utilizando el indicador MACD.

    Args:
        client (Client): Cliente de Binance.
        symbol (str): Símbolo de la criptomoneda.

    Returns:
        bool: Verdadero si la señal de MACD es de compra, falso en caso contrario.
    """
    klines = client.get_klines(symbol=symbol, interval="1h", limit=200)
    close_prices = [float(k[4]) for k in klines]
    df = pd.DataFrame(close_prices, columns=["close"])
    df["EMA12"] = pd.Series(df["close"]).ewm(span=12, adjust=False).mean()
    df["EMA26"] = pd.Series(df["close"]).ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df["MACD"].iloc[-1] > df["Signal"].iloc[-1]

def buy_crypto(client, symbol, budget):
    """
    Ejecuta una orden de compra de criptomoneda.

    Args:
        client (Client): Cliente de Binance.
        symbol (str): Símbolo de la criptomoneda.
        budget (float): Presupuesto para la compra.

    Returns:
        tuple: Precio de compra y cantidad comprada.
    """
    if not validate_balance(client, budget):
        logging.error(f"{symbol}: Saldo insuficiente, no se ejecuta la compra.")
        return None, None
    initial_price = get_price(client, symbol)
    if not initial_price:
        return None, None
    volume = get_volume(client, symbol)
    avg_vol = get_avg_volume(client, symbol)
    if volume < 1.2 * avg_vol or not macd_confirmation(client, symbol):
        logging.info(f"{symbol}: Condiciones no favorables (volumen/MACD). Compra evitada.")
        return None, None

    q_prec, p_prec = get_precision(client, symbol)
    # Calcular tamaño de posición basado en riesgo
    pos_size = calculate_position_size(client, symbol, initial_price)
    # Tomar el mínimo entre el tamaño calculado por riesgo y 25% del presupuesto
    quantity = round(min(budget * 0.25 / initial_price, pos_size), q_prec)
    try:
        if REAL_MARKET:
            execute_with_retry(client, client.order_limit_buy,
                               symbol=symbol,
                               quantity=quantity,
                               price=round(initial_price * 0.98, p_prec))
        log_transaction("Compra", initial_price, 0, quantity, budget - (quantity * initial_price))
        return initial_price, quantity
    except BinanceAPIException as e:
        logging.error(f"{symbol}: Orden de compra fallida: {e}")
        time.sleep(5)
        return None, None

def sell_crypto(client, symbol, buy_price, quantity, profit_threshold, trailing_stop):
    """
    Ejecuta una orden de venta de criptomoneda.

    Args:
        client (Client): Cliente de Binance.
        symbol (str): Símbolo de la criptomoneda.
        buy_price (float): Precio de compra.
        quantity (float): Cantidad comprada.
        profit_threshold (float): Umbral de ganancia.
        trailing_stop (float): Traling stop inicial.

    Returns:
        None
    """
    q_prec, p_prec = get_precision(client, symbol)
    while True:
        current_price = get_price(client, symbol)
        if not current_price:
            time.sleep(adjust_sleep_time(client, symbol))
            continue
        price_change = (current_price - buy_price) / buy_price
        logging.info(f"{symbol}: Precio actual: ${current_price:.2f} | Cambio: {price_change * 100:.2f}%")

        # Ajuste dinámico del trailing stop usando ATR
        atr = get_atr(client, symbol)
        dynamic_trailing_stop = max(trailing_stop, atr / buy_price)

        if price_change >= profit_threshold or current_price < buy_price * (1 - dynamic_trailing_stop):
            try:
                if REAL_MARKET:
                    execute_with_retry(client, client.order_limit_sell,
                                       symbol=symbol,
                                       quantity=round(quantity, q_prec),
                                       price=round(current_price * 0.98, p_prec))
                log_transaction("Venta", current_price, price_change * 100, quantity, buy_price * quantity)
            except BinanceAPIException as e:
                logging.error(f"{symbol}: Orden de venta fallida: {e}")
                time.sleep(5)
            break
        time.sleep(adjust_sleep_time(client, symbol))