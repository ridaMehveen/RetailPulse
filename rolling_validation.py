
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 1. Load the cleaned retail dataset
df = pd.read_csv("retailpulse_cleaned.csv")
df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"],
    dayfirst=True
)

# 2. Select one product for forecasting
product_name = "WHITE HANGING HEART T-LIGHT HOLDER"

product_df = df[
    (df["Description"] == product_name)
    & (~df["Invoice"].astype(str).str.startswith("C"))
].copy()

# 3. Convert daily transactions into monthly demand
product_df["Month"] = (
    product_df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
)

monthly = (
    product_df.groupby("Month")["Quantity"]
    .sum()
    .reset_index()
)

monthly.columns = ["ds", "y"]

# December 2011 is incomplete, so exclude it
monthly = monthly[monthly["ds"] < "2011-12-01"].reset_index(drop=True)

# 4. Evaluate multiple test windows
test_months = 3
minimum_training_months = 12
results = []

for start in range(
    minimum_training_months,
    len(monthly) - test_months + 1,
    test_months
):
    train = monthly.iloc[:start].copy()
    test = monthly.iloc[start:start + test_months].copy()

    # Prophet model
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False
    )
    model.fit(train)

    forecast = model.predict(test[["ds"]])

    actual = test["y"].to_numpy()
    prophet_pred = np.maximum(forecast["yhat"].to_numpy(), 0)

    # Simple baseline: average demand from the previous 3 months
    baseline_value = train["y"].tail(3).mean()
    baseline_pred = np.full(len(test), baseline_value)

    results.append({
        "Test_Start": test["ds"].min().strftime("%Y-%m"),
        "Test_End": test["ds"].max().strftime("%Y-%m"),
        "Prophet_MAE": mean_absolute_error(actual, prophet_pred),
        "Baseline_MAE": mean_absolute_error(actual, baseline_pred),
        "Prophet_RMSE": np.sqrt(mean_squared_error(actual, prophet_pred)),
        "Baseline_RMSE": np.sqrt(mean_squared_error(actual, baseline_pred))
    })

# 5. Display results
results_df = pd.DataFrame(results)

if results_df.empty:
    print("Not enough monthly data for rolling-window validation.")
else:
    print("\nROLLING-WINDOW VALIDATION")
    print(results_df.round(2).to_string(index=False))

    print("\nAVERAGE PERFORMANCE ACROSS TEST WINDOWS")
    print(f"Prophet MAE:  {results_df['Prophet_MAE'].mean():.2f}")
    print(f"Baseline MAE: {results_df['Baseline_MAE'].mean():.2f}")
    print(f"Prophet RMSE: {results_df['Prophet_RMSE'].mean():.2f}")
    print(f"Baseline RMSE: {results_df['Baseline_RMSE'].mean():.2f}")

    results_df.to_csv("retailpulse_rolling_validation.csv", index=False)
    print("\nSaved: retailpulse_rolling_validation.csv")
