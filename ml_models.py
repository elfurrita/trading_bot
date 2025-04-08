import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split

def train_ml_model(data):
    # Preparar los datos
    X = data.drop(columns=["target"])
    y = data["target"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Definir el modelo
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    # Compilar el modelo
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    
    # Entrenar el modelo
    model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_test, y_test))
    
    return model

def predict_with_ml_model(model, data):
    X = data.drop(columns=["target"])
    predictions = model.predict(X)
    return ["buy" if pred > 0.5 else "sell" for pred in predictions]
