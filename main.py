import os
import sys
import logging
import time
import pandas as pd
from dydx4 import Client
from dydx4.constants import MARKET_BTC_USD, ORDER_SIDE_BUY, ORDER_SIDE_SELL
from dydx4.helpers.request_helpers import generate_now_iso
from dydx_v4_client import NodeClient, QueryNodeClient, IndexerClient, FaucetClient
from dydx_v4_client.network import secure_channel, TESTNET, TESTNET_FAUCET
from dotenv import load_dotenv
import asyncio

# Cargar variables de entorno
load_dotenv()

# Configuración del log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración
SYMBOLS = ['BTC-USD']  # dYdX utiliza diferentes símbolos
BUDGET = 1000
DEFAULT_PROFIT_THRESHOLD = 0.05
DEFAULT_TRAILING_STOP = 0.02
REAL_MARKET = False  # Cambiar a True para operar en el mercado real
DYDX_API_KEY = os.getenv('DYDX_API_KEY')
DYDX_API_SECRET = os.getenv('DYDX_API_SECRET')
DYDX_API_PASSPHRASE = os.getenv('DYDX_API_PASSPHRASE')
DYDX_API_HOST = 'https://api.dydx.exchange'

# Inicialización del cliente de dYdX
client = Client(
    host=DYDX_API_HOST,
    api_key=DYDX_API_KEY,
    api_secret=DYDX_API_SECRET,
    passphrase=DYDX_API_PASSPHRASE
)

async def initialize_clients():
    try:
        node = await NodeClient(secure_channel("test-dydx-grpc.kingnodes.com"))
        indexer = IndexerClient(TESTNET.rest_indexer)
        faucet = FaucetClient(TESTNET_FAUCET)
        logging.info("Clientes de dYdX inicializados correctamente")
        return node, indexer, faucet
    except Exception as e:
        logging.error(f"Error al inicializar los clientes de dYdX: {e}")
        return None, None, None

async def get_historical_data(symbol, interval='1h', limit=100):
    """Obtiene datos históricos de una criptomoneda."""
    candles = await client.public.get_candles(
        market=symbol,
        resolution=interval,
        from_iso=generate_now_iso(),
        limit=limit
    )
    data = pd.DataFrame(candles['candles'])
    return data

async def place_order(market, side, size, price):
    """Coloca una orden en dYdX."""
    if REAL_MARKET:
        await client.private.create_order(
            market=market,
            side=side,
            size=size,
            price=price,
            type='limit',
            post_only=True
        )
        logging.info(f"Orden {side} colocada: {size} {market} a {price}")
    else:
        logging.info(f"Simulación de orden {side}: {size} {market} a {price}")

async def main():
    node, indexer, faucet = await initialize_clients()
    if node and indexer and faucet:
        # Ejemplo de obtención de datos históricos
        data = await get_historical_data(SYMBOLS[0])
        print(data.head())

        # Ejemplo de colocación de una orden de compra
        await place_order(SYMBOLS[0], ORDER_SIDE_BUY, 0.01, 30000)

if __name__ == "__main__":
    asyncio.run(main())
