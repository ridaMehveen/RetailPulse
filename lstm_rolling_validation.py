
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping

np.random.seed(42)
tf.random.set_seed(42)

df = pd.read_csv("retailpulse_cleaned.csv")
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True)
df = df[~df["Invoice"].astype(str).str.startswith("C")].copy()

product = "WHITE HANGING HEART T-LIGHT HOLDER"
df = df[df["Description"] == product].copy()
df["Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()

monthly = df.groupby("Month")["Quantity"].sum().reset_index()
monthly.columns = ["ds", "y"]
monthly = monthly[monthly["ds"] < "2011-12-01"].reset_index(drop=True)

lookback = 6
test_size = 3
results = []

# Same chronological test windows as rolling_validation.py
for start in range(12, len(monthly) - test_size + 1, test_size):
    train = monthly.iloc[:start]["y"].to_numpy(dtype=float)
    test = monthly.iloc[start:start + test_size]["y"].to_numpy(dtype=float)
    dates = monthly.iloc[start:start + test_size]["ds"]

    scaler = MinMaxScaler()
    scaled_train = scaler.fit_transform(train.reshape(-1, 1)).flatten()

    X, y = [], []
    for i in range(lookback, len(scaled_train)):
        X.append(scaled_train[i-lookback:i])
        y.append(scaled_train[i])

    X = np.array(X).reshape(-1, lookback, 1)
    y = np.array(y)

    tf.keras.backend.clear_session()
    tf.random.set_seed(42)

    model = Sequential([
        Input(shape=(lookback, 1)),
        LSTM(16),
        Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse")

    model.fit(
        X, y,
        epochs=100,
        batch_size=4,
        shuffle=False,
        callbacks=[EarlyStopping(monitor="loss", patience=10,
                                 restore_best_weights=True)],
        verbose=0
    )

    history = list(scaled_train[-lookback:])
    predictions = []

    for _ in range(test_size):
        x_input = np.array(history[-lookback:]).reshape(1, lookback, 1)
        pred_scaled = model.predict(x_input, verbose=0)[0, 0]
        predictions.append(max(0, scaler.inverse_transform([[pred_scaled]])[0, 0]))
        history.append(pred_scaled)

    actual = test
    baseline = np.full(test_size, np.mean(train[-3:]))

    results.append({
        "Test_Start": dates.iloc[0].strftime("%Y-%m"),
        "Test_End": dates.iloc[-1].strftime("%Y-%m"),
        "LSTM_MAE": mean_absolute_error(actual, predictions),
        "Baseline_MAE": mean_absolute_error(actual, baseline),
        "LSTM_RMSE": np.sqrt(mean_squared_error(actual, predictions)),
        "Baseline_RMSE": np.sqrt(mean_squared_error(actual, baseline))
    })

results_df = pd.DataFrame(results)
print("\nLSTM ROLLING-WINDOW RESULTS")
print(results_df.round(2).to_string(index=False))

print("\nAVERAGE PERFORMANCE")
print(f"LSTM MAE:      {results_df['LSTM_MAE'].mean():.2f}")
print(f"Baseline MAE:  {results_df['Baseline_MAE'].mean():.2f}")
print(f"LSTM RMSE:     {results_df['LSTM_RMSE'].mean():.2f}")
print(f"Baseline RMSE: {results_df['Baseline_RMSE'].mean():.2f}")

results_df.to_csv("retailpulse_lstm_rolling_validation.csv", index=False)
print("\nSaved: retailpulse_lstm_rolling_validation.csv")
