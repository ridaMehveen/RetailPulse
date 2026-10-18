
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 1. Load cleaned retail data
df = pd.read_csv("retailpulse_cleaned.csv")
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True)

# 2. Select one product for the first experiment
product_name = "WHITE HANGING HEART T-LIGHT HOLDER"

product_data = df[
    (df["Description"] == product_name)
    & (~df["Invoice"].astype(str).str.startswith("C"))
].copy()

# 3. Aggregate sales quantity by month
product_data["Month"] = (
    product_data["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
)

monthly = (
    product_data.groupby("Month")["Quantity"]
    .sum()
    .rename_axis("ds")
    .reset_index(name="y")
    .sort_values("ds")
)

# Exclude December 2011 because the dataset ends mid-month
monthly = monthly[monthly["ds"] < "2011-12-01"].copy()

if len(monthly) < 12:
    raise ValueError("Not enough monthly observations to forecast.")

# 4. Reserve the final three complete months for testing
train = monthly.iloc[:-3].copy()
test = monthly.iloc[-3:].copy()

# 5. Train Prophet on training data only
model = Prophet(
    yearly_seasonality=False,
    weekly_seasonality=False,
    daily_seasonality=False
)
model.fit(train)

# 6. Predict the held-out test months
forecast = model.predict(test[["ds"]])

results = test.merge(
    forecast[["ds", "yhat"]],
    on="ds",
    how="left"
)
results = results.rename(columns={"y": "Actual", "yhat": "Prophet_Prediction"})

# 7. Compare with a trailing 3-month average baseline
baseline = []

for date in results["ds"]:
    history = monthly.loc[monthly["ds"] < date, "y"].tail(3)
    baseline.append(history.mean())

results["Baseline_Prediction"] = baseline

# 8. Evaluate both models
prophet_mae = mean_absolute_error(
    results["Actual"], results["Prophet_Prediction"]
)
baseline_mae = mean_absolute_error(
    results["Actual"], results["Baseline_Prediction"]
)

prophet_rmse = np.sqrt(mean_squared_error(
    results["Actual"], results["Prophet_Prediction"]
))
baseline_rmse = np.sqrt(mean_squared_error(
    results["Actual"], results["Baseline_Prediction"]
))

print("\nPRODUCT:", product_name)
print("\nTEST RESULTS:")
print(results.round(2).to_string(index=False))

print("\nMODEL COMPARISON")
print(f"Prophet MAE:  {prophet_mae:.2f}")
print(f"Baseline MAE: {baseline_mae:.2f}")
print(f"Prophet RMSE: {prophet_rmse:.2f}")
print(f"Baseline RMSE: {baseline_rmse:.2f}")

# 9. Save test results
results.to_csv("retailpulse_prophet_test_results.csv", index=False)
print("\nSaved: retailpulse_prophet_test_results.csv")
