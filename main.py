import os
import sys
import logging
import time
from binance.client import Client
from binance.enums import *

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

def main():
    """Función principal del bot."""
    while True:
        for symbol in SYMBOLS:
            price = get_price(symbol)
            logging.info(f"El precio de {symbol} es {price}")
            # Aquí puedes agregar lógica para comprar/vender basado en indicadores técnicos
        time.sleep(60)  # Espera 1 minuto antes de la siguiente iteración

if __name__ == "__main__":
    main()