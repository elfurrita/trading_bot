import logging
import time
import numpy as np
import pandas as pd
from multiprocessing import Pool
from dydx3 import Client  # Importar la biblioteca de dYdX
from trading_bot.utils import get_precision, get_price, get_volume, adjust_sleep_time, execute_with_retry, get_balance, validate_balance, get_atr, get_technical_indicators
from trading_bot.config import SYMBOLS, BUDGET, DEFAULT_PROFIT_THRESHOLD, DEFAULT_TRAILING_STOP, REAL_MARKET
from trading_bot.backtesting import optimize_parameters

# Configura la salida de logging
logging.basicConfig(level=logging.INFO)

# Obtén un logger
logger = logging.getLogger(__name__)

# Usa el logger
logger.info("Inicializando el bot de trading")

# Ejemplo de inicialización del cliente
try:
    client = Client(
        host='https://api.dydx.exchange',
        api_key='tu_api_key',
        api_secret='tu_api_secret',
        passphrase='tu_passphrase'
    )
    logger.info("Cliente de dYdX inicializado correctamente")
except Exception as e:
    logger.error(f"Error al inicializar el cliente de dYdX: {e}")

# Archivo de registro
log_file = "transacciones.csv"
with open(log_file, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Acción", "Símbolo", "Precio", "Cambio %", "Cantidad", "Saldo Restante"])

def log_transaction(action, price, change, quantity, remaining_balance):
    with open(log_file, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([action, symbol, price, change, quantity, remaining_balance])

def get_avg_volume(client, symbol, period=30):
    klines = client.public.get_candles(market=symbol, resolution="1H", limit=period)
    volumes = [float(k['volume']) for k in klines['candles']]
    return np.mean(volumes)

def calculate_position_size(client, symbol, buy_price):
    atr = get_atr(client, symbol)
    risk_amount = BUDGET * RISK_PERCENTAGE
    stop_distance = atr  # Utilizando ATR como medida de riesgo
    if stop_distance == 0:
        return BUDGET * 0.25 / buy_price
    return risk_amount / stop_distance

def macd_confirmation(client, symbol):
    klines = client.public.get_candles(market=symbol, resolution="1H", limit=200)
    close_prices = [float(k['close']) for k in klines['candles']]
    df = pd.DataFrame(close_prices, columns=["close"])
    df["EMA12"] = pd.Series(df["close"]).ewm(span=12, adjust=False).mean()
    df["EMA26"] = pd.Series(df["close"]).ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df["MACD"].iloc[-1] > df["Signal"].iloc[-1]

def buy_crypto(client, symbol, budget):
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
    pos_size = calculate_position_size(client, symbol, initial_price)
    quantity = round(min(budget * 0.25 / initial_price, pos_size), q_prec)
    try:
        if REAL_MARKET:
            execute_with_retry(client, client.private.create_order,  # Cambiar a función de orden de dYdX
                               market=symbol,
                               side="buy",
                               size=quantity,
                               price=round(initial_price * 0.98, p_prec))
        log_transaction("Compra", initial_price, 0, quantity, budget - (quantity * initial_price))
        return initial_price, quantity
    except Exception as e:  # Manejar excepción genérica
        logging.error(f"{symbol}: Orden de compra fallida: {e}")
        time.sleep(5)
        return None, None

def sell_crypto(client, symbol, buy_price, quantity, profit_threshold, trailing_stop):
    q_prec, p_prec = get_precision(client, symbol)
    while True:
        current_price = get_price(client, symbol)
        if not current_price:
            time.sleep(adjust_sleep_time(client, symbol))
            continue
        price_change = (current_price - buy_price) / buy_price
        logging.info(f"{symbol}: Precio actual: ${current_price:.2f} | Cambio: {price_change * 100:.2f}%")

        atr = get_atr(client, symbol)
        dynamic_trailing_stop = max(trailing_stop, atr / buy_price)

        if price_change >= profit_threshold or current_price < buy_price * (1 - dynamic_trailing_stop):
            try:
                if REAL_MARKET:
                    execute_with_retry(client, client.private.create_order,  # Cambiar a función de orden de dYdX
                                       market=symbol,
                                       side="sell",
                                       size=round(quantity, q_prec),
                                       price=round(current_price * 0.98, p_prec))
                log_transaction("Venta", current_price, price_change * 100, quantity, buy_price * quantity)
            except Exception as e:  # Manejar excepción genérica
                logging.error(f"{symbol}: Orden de venta fallida: {e}")
                time.sleep(5)
            break
        time.sleep(adjust_sleep_time(client, symbol))
