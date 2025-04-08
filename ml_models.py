# ml_models.py

from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import talib

def train_ml_model(client, symbol):
    data = client.public.get_candles(market=symbol, resolution="1H", limit=500)
    df = pd.DataFrame(data['candles'])
    df["RSI"] = talib.RSI(df["close"].values, timeperiod=14)
    features = df[["RSI", "close"]]
    target = (df["close"].shift(-1) > df["close"]).astype(int)
    model = RandomForestClassifier()
    model.fit(features[:-1], target[:-1])
    return model

def predict_with_ml_model(model, data):
    prediction = model.predict(data)
    return prediction[0]
