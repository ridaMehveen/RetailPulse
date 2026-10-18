
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import pandas as pd
import numpy as np
import tensorflow as tf
from prophet import Prophet
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping

np.random.seed(42)
tf.random.set_seed(42)

# 1. Load and prepare data
df = pd.read_csv("retailpulse_cleaned.csv")
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True)

product = "WHITE HANGING HEART T-LIGHT HOLDER"

df = df[~df["Invoice"].astype(str).str.startswith("C")].copy()
df = df[df["Description"] == product].copy()
df["Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()

monthly = df.groupby("Month")["Quantity"].sum().reset_index()
monthly.columns = ["ds", "y"]
monthly = monthly[monthly["ds"] < "2011-12-01"].reset_index(drop=True)

lookback = 6
test_size = 3
results = []

# 2. Rolling-window evaluation
for start in range(12, len(monthly) - test_size + 1, test_size):
    train = monthly.iloc[:start].copy()
    test = monthly.iloc[start:start + test_size].copy()

    actual = test["y"].to_numpy(dtype=float)

    # 3. Prophet predictions
    prophet = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False
    )
    prophet.fit(train)
    prophet_forecast = prophet.predict(test[["ds"]])
    prophet_pred = np.maximum(prophet_forecast["yhat"].to_numpy(), 0)

    # 4. Prepare LSTM using training data only
    train_values = train["y"].to_numpy(dtype=float)

    scaler = MinMaxScaler()
    scaled_train = scaler.fit_transform(
        train_values.reshape(-1, 1)
    ).flatten()

    X, y = [], []
    for i in range(lookback, len(scaled_train)):
        X.append(scaled_train[i-lookback:i])
        y.append(scaled_train[i])

    X = np.array(X).reshape(-1, lookback, 1)
    y = np.array(y)

    tf.keras.backend.clear_session()
    tf.random.set_seed(42)

    lstm = Sequential([
        Input(shape=(lookback, 1)),
        LSTM(16),
        Dense(1)
    ])
    lstm.compile(optimizer="adam", loss="mse")
    lstm.fit(
        X, y,
        epochs=100,
        batch_size=4,
        shuffle=False,
        callbacks=[
            EarlyStopping(
                monitor="loss",
                patience=10,
                restore_best_weights=True
            )
        ],
        verbose=0
    )

    # 5. Recursive LSTM predictions
    history = list(scaled_train[-lookback:])
    lstm_pred = []

    for _ in range(test_size):
        x_input = np.array(
            history[-lookback:]
        ).reshape(1, lookback, 1)

        pred_scaled = lstm.predict(x_input, verbose=0)[0, 0]
        pred = scaler.inverse_transform([[pred_scaled]])[0, 0]

        lstm_pred.append(max(0, pred))
        history.append(pred_scaled)

    lstm_pred = np.array(lstm_pred)

    # 6. Hybrid: equal-weight average of Prophet and LSTM
    hybrid_pred = (prophet_pred + lstm_pred) / 2

    # 7. Baseline: average demand in previous three months
    baseline_pred = np.full(test_size, train_values[-3:].mean())

    results.append({
        "Test_Start": test["ds"].iloc[0].strftime("%Y-%m"),
        "Test_End": test["ds"].iloc[-1].strftime("%Y-%m"),
        "Prophet_MAE": mean_absolute_error(actual, prophet_pred),
        "LSTM_MAE": mean_absolute_error(actual, lstm_pred),
        "Hybrid_MAE": mean_absolute_error(actual, hybrid_pred),
        "Baseline_MAE": mean_absolute_error(actual, baseline_pred),
        "Prophet_RMSE": np.sqrt(mean_squared_error(actual, prophet_pred)),
        "LSTM_RMSE": np.sqrt(mean_squared_error(actual, lstm_pred)),
        "Hybrid_RMSE": np.sqrt(mean_squared_error(actual, hybrid_pred)),
        "Baseline_RMSE": np.sqrt(mean_squared_error(actual, baseline_pred))
    })

# 8. Display and save results
results_df = pd.DataFrame(results)

print("\nHYBRID ROLLING-WINDOW RESULTS")
print(results_df.round(2).to_string(index=False))

metric_cols = [
    "Prophet_MAE", "LSTM_MAE", "Hybrid_MAE", "Baseline_MAE",
    "Prophet_RMSE", "LSTM_RMSE", "Hybrid_RMSE", "Baseline_RMSE"
]

summary = results_df[metric_cols].mean().to_frame(
    name="Average_Error"
)

print("\nAVERAGE PERFORMANCE")
print(summary.round(2).to_string())

results_df.to_csv("retailpulse_hybrid_rolling_details.csv", index=False)
summary.to_csv("retailpulse_hybrid_rolling_summary.csv")

print("\nSaved:")
print("retailpulse_hybrid_rolling_details.csv")
print("retailpulse_hybrid_rolling_summary.csv")
