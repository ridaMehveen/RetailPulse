
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 1. Load cleaned data
df = pd.read_csv("retailpulse_cleaned.csv")
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True)

# 2. Select three products from the dataset
products = [
    "WHITE HANGING HEART T-LIGHT HOLDER",
    "REGENCY CAKESTAND 3 TIER",
    "PARTY BUNTING"
]

# 3. Prepare monthly demand data
df = df[~df["Invoice"].astype(str).str.startswith("C")].copy()
df["Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()

all_results = []

for product in products:
    product_df = df[df["Description"] == product].copy()

    monthly = (
        product_df.groupby("Month")["Quantity"]
        .sum()
        .reset_index()
    )
    monthly.columns = ["ds", "y"]

    # Exclude incomplete December 2011
    monthly = monthly[monthly["ds"] < "2011-12-01"].reset_index(drop=True)

    if len(monthly) < 15:
        print(f"Skipping {product}: not enough monthly data.")
        continue

    # Test multiple three-month windows
    product_results = []

    for start in range(12, len(monthly) - 3 + 1, 3):
        train = monthly.iloc[:start].copy()
        test = monthly.iloc[start:start + 3].copy()

        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False
        )
        model.fit(train)

        forecast = model.predict(test[["ds"]])

        actual = test["y"].to_numpy()
        prophet_pred = np.maximum(forecast["yhat"].to_numpy(), 0)

        # Baseline: average demand in the previous three months
        baseline_value = train["y"].tail(3).mean()
        baseline_pred = np.full(len(test), baseline_value)

        product_results.append({
            "Product": product,
            "Test_Start": test["ds"].min().strftime("%Y-%m"),
            "Test_End": test["ds"].max().strftime("%Y-%m"),
            "Prophet_MAE": mean_absolute_error(actual, prophet_pred),
            "Baseline_MAE": mean_absolute_error(actual, baseline_pred),
            "Prophet_RMSE": np.sqrt(mean_squared_error(actual, prophet_pred)),
            "Baseline_RMSE": np.sqrt(mean_squared_error(actual, baseline_pred))
        })

    if product_results:
        all_results.extend(product_results)

# 4. Display results
if not all_results:
    print("No results produced. Check product names and available data.")
else:
    results_df = pd.DataFrame(all_results)

    print("\nRESULTS FOR EACH TEST WINDOW")
    print(results_df.round(2).to_string(index=False))

    summary = (
        results_df.groupby("Product")[
            ["Prophet_MAE", "Baseline_MAE", "Prophet_RMSE", "Baseline_RMSE"]
        ]
        .mean()
        .reset_index()
    )

    print("\nAVERAGE RESULTS BY PRODUCT")
    print(summary.round(2).to_string(index=False))

    summary.to_csv("retailpulse_multi_product_summary.csv", index=False)
    results_df.to_csv("retailpulse_multi_product_details.csv", index=False)

    print("\nSaved:")
    print("retailpulse_multi_product_summary.csv")
    print("retailpulse_multi_product_details.csv")
