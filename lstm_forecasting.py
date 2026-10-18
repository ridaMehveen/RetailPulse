
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

# Reproducible results
np.random.seed(42)
tf.random.set_seed(42)

# 1. Load cleaned retail data
df = pd.read_csv("retailpulse_cleaned.csv")
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True)

product_name = "WHITE HANGING HEART T-LIGHT HOLDER"

# Exclude cancellation invoices
df = df[~df["Invoice"].astype(str).str.startswith("C")].copy()
df = df[df["Description"] == product_name].copy()

# 2. Aggregate quantity by month
df["Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()

monthly = (
    df.groupby("Month")["Quantity"]
    .sum()
    .reset_index()
)
monthly.columns = ["ds", "y"]

# December 2011 is incomplete
monthly = monthly[monthly["ds"] < "2011-12-01"].reset_index(drop=True)

if len(monthly) < 18:
    raise ValueError("Not enough monthly observations for this LSTM experiment.")

# 3. Reserve the final 3 months for testing
test_size = 3
train_values = monthly["y"].iloc[:-test_size].to_numpy(dtype=float)
test_values = monthly["y"].iloc[-test_size:].to_numpy(dtype=float)
test_dates = monthly["ds"].iloc[-test_size:]

# 4. Scale using training data only
scaler = MinMaxScaler()
train_scaled = scaler.fit_transform(train_values.reshape(-1, 1)).flatten()

# Use the previous 6 months to predict the next month
lookback = 6

X_train = []
y_train = []

for i in range(lookback, len(train_scaled)):
    X_train.append(train_scaled[i - lookback:i])
    y_train.append(train_scaled[i])

X_train = np.array(X_train).reshape(-1, lookback, 1)
y_train = np.array(y_train)

# 5. Build the LSTM model
model = Sequential([
    Input(shape=(lookback, 1)),
    LSTM(32),
    Dense(16, activation="relu"),
    Dense(1)
])

model.compile(optimizer="adam", loss="mse")

early_stop = EarlyStopping(
    monitor="loss",
    patience=15,
    restore_best_weights=True
)

# 6. Train the model
model.fit(
    X_train,
    y_train,
    epochs=150,
    batch_size=4,
    shuffle=False,
    callbacks=[early_stop],
    verbose=0
)

# 7. Forecast the final 3 months recursively
history = list(train_scaled[-lookback:])
lstm_predictions = []

for _ in range(test_size):
    input_array = np.array(history[-lookback:]).reshape(1, lookback, 1)
    prediction_scaled = model.predict(input_array, verbose=0)[0, 0]
    prediction = scaler.inverse_transform([[prediction_scaled]])[0, 0]

    lstm_predictions.append(max(0, prediction))
    history.append(prediction_scaled)

# 8. Baseline: average of the last 3 training months
baseline_value = np.mean(train_values[-3:])
baseline_predictions = np.full(test_size, baseline_value)

# 9. Evaluate both models
lstm_mae = mean_absolute_error(test_values, lstm_predictions)
baseline_mae = mean_absolute_error(test_values, baseline_predictions)

lstm_rmse = np.sqrt(mean_squared_error(test_values, lstm_predictions))
baseline_rmse = np.sqrt(mean_squared_error(test_values, baseline_predictions))

results = pd.DataFrame({
    "Month": test_dates.dt.strftime("%Y-%m").to_numpy(),
    "Actual": test_values,
    "LSTM_Prediction": lstm_predictions,
    "Baseline_Prediction": baseline_predictions
})

print("\nPRODUCT:", product_name)
print("\nLSTM TEST RESULTS")
print(results.round(2).to_string(index=False))

print("\nMODEL COMPARISON")
print(f"LSTM MAE:      {lstm_mae:.2f}")
print(f"Baseline MAE:  {baseline_mae:.2f}")
print(f"LSTM RMSE:     {lstm_rmse:.2f}")
print(f"Baseline RMSE: {baseline_rmse:.2f}")

results.to_csv("retailpulse_lstm_test_results.csv", index=False)
model.save("retailpulse_lstm_model.keras")

print("\nSaved:")
print("retailpulse_lstm_test_results.csv")
print("retailpulse_lstm_model.keras")
