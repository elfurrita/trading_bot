import os
import sys
import logging
import time
import pandas as pd
from binance.client import Client
from binance.enums import *
import ta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sklearn.ensemble import RandomForestRegressor
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Configuración del log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración
SYMBOLS = ['BTCUSDT', 'ETHUSDT']
BUDGET = 1000
DEFAULT_PROFIT_THRESHOLD = 0.05
DEFAULT_TRAILING_STOP = 0.02
REAL_MARKET = False  # Cambiar a True para operar en el mercado real
ALERT_EMAIL = os.getenv('ALERT_EMAIL')
ALERT_PASSWORD = os.getenv('ALERT_PASSWORD')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Claves de la API de Binance
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# Inicialización del cliente de Binance
client = Client(API_KEY, API_SECRET)

# Inicialización del bot de Telegram
bot = Bot(token=TELEGRAM_TOKEN)
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher

def send_email(subject, body, max_retries=3, retry_delay=5):
    """Envía un correo electrónico con una alerta, con lógica de reintentos."""
    msg = MIMEMultipart()
    msg['From'] = ALERT_EMAIL
    msg['To'] = ALERT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    for attempt in range(max_retries):
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(ALERT_EMAIL, ALERT_PASSWORD)
            text = msg.as_string()
            server.sendmail(ALERT_EMAIL, ALERT_EMAIL, text)
            server.quit()
            logging.info(f"Correo enviado: {subject}")
            break
        except Exception as e:
            logging.error(f"Error al enviar correo: {e}")
            if attempt < max_retries - 1:
                logging.info(f"Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                logging.error("Fallo al enviar correo después de varios intentos.")

def send_telegram_message(message):
    """Envía un mensaje a través del bot de Telegram."""
    try:
        bot.send_message(chat_id='YOUR_CHAT_ID', text=message)
        logging.info(f"Mensaje de Telegram enviado: {message}")
    except Exception as e:
        logging.error(f"Error al enviar mensaje de Telegram: {e}")

def get_historical_data(symbol, interval='1h', limit=100):
    """Obtiene datos históricos de una criptomoneda."""
    try:
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
    except Exception as e:
        logging.error(f"Error al obtener datos históricos: {e}")
        return None

def calculate_indicators(data):
    """Calcula indicadores técnicos."""
    try:
        data['rsi'] = ta.momentum.RSIIndicator(data['close']).rsi()
        data['macd'] = ta.trend.MACD(data['close']).macd()
        data['macd_signal'] = ta.trend.MACD(data['close']).macd_signal()
        data['bollinger_hband'] = ta.volatility.BollingerBands(data['close']).bollinger_hband()
        data['bollinger_lband'] = ta.volatility.BollingerBands(data['close']).bollinger_lband()
        return data
    except Exception as e:
        logging.error(f"Error al calcular indicadores técnicos: {e}")
        return None

def train_model(data):
    """Entrena un modelo de machine learning para predecir precios."""
    try:
        X = data[['rsi', 'macd', 'macd_signal', 'bollinger_hband', 'bollinger_lband']].dropna()
        y = data['close'].shift(-1).dropna()
        X = X[:-1]
        model = RandomForestRegressor()
        model.fit(X, y)
        return model
    except Exception as e:
        logging.error(f"Error al entrenar el modelo: {e}")
        return None

def predict_price(model, latest_data):
    """Predice el precio futuro usando el modelo entrenado."""
    try:
        X_latest = latest_data[['rsi', 'macd', 'macd_signal', 'bollinger_hband', 'bollinger_lband']].values.reshape(1, -1)
        predicted_price = model.predict(X_latest)[0]
        return predicted_price
    except Exception as e:
        logging.error(f"Error al predecir el precio: {e}")
        return None

def get_price(symbol):
    """Obtiene el precio actual de una criptomoneda."""
    try:
        ticker = client.get_ticker(symbol=symbol)
        return float(ticker['lastPrice'])
    except Exception as e:
        logging.error(f"Error al obtener el precio actual: {e}")
        return None

def place_order(symbol, quantity, order_type=ORDER_TYPE_MARKET, side=SIDE_BUY):
    """Realiza una orden en Binance."""
    try:
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
    except Exception as e:
        logging.error(f"Error al realizar la orden: {e}")
        return None

def trading_strategy(data, symbol):
    """Estrategia de trading basada en indicadores técnicos y machine learning."""
    try:
        latest_data = data.iloc[-1]
        model = train_model(data)
        if model is None:
            return

        predicted_price = predict_price(model, latest_data)
        if predicted_price is None:
            return

        if latest_data['rsi'] < 30 and latest_data['close'] < latest_data['bollinger_lband']:
            logging.info(f"Señal de compra para {symbol}")
            place_order(symbol, BUDGET / latest_data['close'], side=SIDE_BUY)
            send_email(f"Señal de compra para {symbol}", f"Precio: {latest_data['close']}, RSI: {latest_data['rsi']}")
            send_telegram_message(f"Señal de compra para {symbol}\nPrecio: {latest_data['close']}, RSI: {latest_data['rsi']}")
        elif latest_data['rsi'] > 70 and latest_data['close'] > latest_data['bollinger_hband']:
            logging.info(f"Señal de venta para {symbol}")
            place_order(symbol, BUDGET / latest_data['close'], side=SIDE_SELL)
            send_email(f"Señal de venta para {symbol}", f"Precio: {latest_data['close']}, RSI: {latest_data['rsi']}")
            send_telegram_message(f"Señal de venta para {symbol}\nPrecio: {latest_data['close']}, RSI: {latest_data['rsi']}")
    except Exception as e:
        logging.error(f"Error en la estrategia de trading: {e}")

def backtesting(symbol, data):
    """Realiza backtesting de la estrategia de trading."""
    try:
        balance = 1000  # Balance inicial
        positions = []
        for i in range(len(data)):
            latest_data = data.iloc[i]
            if latest_data['rsi'] < 30 and latest_data['close'] < latest_data['bollinger_lband']:
                positions.append(('buy', latest_data['close']))
                logging.info(f"Backtesting compra para {symbol} a {latest_data['close']}")
            elif latest_data['rsi'] > 70 and latest_data['close'] > latest_data['bollinger_hband'] and positions:
                buy_price = positions.pop()[1]
                profit = (latest_data['close'] - buy_price) * (balance / buy_price)
                balance += profit
                logging.info(f"Backtesting venta para {symbol} a {latest_data['close']}, ganancia: {profit}")
        logging.info(f"Balance final de backtesting para {symbol}: {balance}")
    except Exception as e:
        logging.error(f"Error en el backtesting: {e}")

def start(update: Update, context: CallbackContext):
    """Comando /start para el bot de Telegram."""
    context.bot.send_message(chat_id=update.effective_chat.id, text="¡Hola! Soy tu bot de trading.")

def main():
    """Función principal del bot."""
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    
    updater.start_polling()
    
    while True:
        for symbol in SYMBOLS:
            data = get_historical_data(symbol)
            if data is not None:
                data = calculate_indicators(data)
                if data is not None:
                    trading_strategy(data, symbol)
                    backtesting(symbol, data)  # Realiza backtesting con los datos históricos
        time.sleep(60)  # Espera 1 minuto antes de la siguiente iteración

if __name__ == "__main__":
    main()
