# config.py
from dydx_v4_client.network import make_testnet

# Configuración de la red Testnet
TESTNET = make_testnet(
    node_url="your-testnet-node-url",
    rest_indexer="your-testnet-rest-url",
    websocket_indexer="your-testnet-websocket-url"
)

SYMBOLS = ["BTC-USD", "ETH-USD"]
BUDGET = 1000.0
DEFAULT_PROFIT_THRESHOLD = 0.03
DEFAULT_TRAILING_STOP = 0.02
PROFIT_THRESHOLD_RANGE = (0.01, 0.1)
TRAILING_STOP_RANGE = (0.01, 0.1)
REAL_MARKET = False

# Credenciales de la API de dYdX v4
DYDX_API_KEY = "your_api_key"
DYDX_API_SECRET = "your_api_secret"
DYDX_API_PASSPHRASE = "your_passphrase"
DYDX_API_HOST = "https://api.stage.dydx.exchange/v4"  # Para operar en Mainnet, agregar a dydx_api_host: "https://api.dydx.exchange/v4

# Configuración adicional para dYdX v4
DYDX_STARK_PRIVATE_KEY = "your_stark_private_key"
DYDX_ETHEREUM_ADDRESS = "your_ethereum_address"
DYDX_NETWORK_ID = 3  # Use 1 for Mainnet (use 3 for Ropsten)

# Asegúrate de instalar la librería de dYdX v4
# pip install dydx-v4-python
