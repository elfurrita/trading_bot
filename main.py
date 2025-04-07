import os
import sys
import logging
import time
import pandas as pd
from binance.client import Client
from binance.enums import *
import ta

# Configuración del log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración
SYMBOLS = ['BTCUSDT', 'ETHUSDT']
BUDGET = 1000
DEFAULT_PROFIT_THRESHOLD = 0.05
DEFAULT_TRAILING_STOP = 0.02
REAL_MARKET = False  # Cambiar a True para operar en el mercado real

# Claves de la API de Binance
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# Inicialización del cliente de Binance
client = Client(API_KEY, API_SECRET)

def get_historical_data(symbol, interval='1h', limit=100):
    """Obtiene datos históricos de una criptomoneda."""
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    data = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore'
    ])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    data.set_index('timestamp', inplace=True)
    data['close'] = data['close'].astype(float)
    return data

def calculate_indicators(data):
    """Calcula indicadores técnicos."""
    data['rsi'] = ta.momentum.RSIIndicator(data['close']).rsi()
    data['macd'] = ta.trend.MACD(data['close']).macd()
    data['macd_signal'] = ta.trend.MACD(data['close']).macd_signal()
    data['bollinger_hband'] = ta.volatility.BollingerBands(data['close']).bollinger_hband()
    data['bollinger_lband'] = ta.volatility.BollingerBands(data['close']).bollinger_lband()
    return data

def get_price(symbol):
    """Obtiene el precio actual de una criptomoneda."""
    ticker = client.get_ticker(symbol=symbol)
    return float(ticker['lastPrice'])

def place_order(symbol, quantity, order_type=ORDER_TYPE_MARKET, side=SIDE_BUY):
    """Realiza una orden en Binance."""
    if REAL_MARKET:
        order = client.create_order(
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=quantity
        )
    else:
        logging.info(f"Simulación de orden: {side} {quantity} {symbol}")
        order = {'status': 'FILLED'}
    return order

def trading_strategy(data, symbol):
    """Estrategia de trading basada en indicadores técnicos."""
    latest_data = data.iloc[-1]
    if latest_data['rsi'] < 30 and latest_data['close'] < latest_data['bollinger_lband']:
        logging.info(f"Señal de compra para {symbol}")
        place_order(symbol, BUDGET / latest_data['close'], side=SIDE_BUY)
    elif latest_data['rsi'] > 70 and latest_data['close'] > latest_data['bollinger_hband']:
        logging.info(f"Señal de venta para {symbol}")
        place_order(symbol, BUDGET / latest_data['close'], side=SIDE_SELL)

def main():
    """Función principal del bot."""
    while True:
        for symbol in SYMBOLS:
            data = get_historical_data(symbol)
            data = calculate_indicators(data)
            trading_strategy(data, symbol)
        time.sleep(60)  # Espera 1 minuto antes de la siguiente iteración

if __name__ == "__main__":
    main()
