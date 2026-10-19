
import streamlit as st
import pandas as pd
from pathlib import Path
from auth import require_login

st.set_page_config(
    page_title="RetailPulse - Forecast",
    page_icon="📈",
    layout="wide"
)

require_login()

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020 0%, #111a30 55%, #17152d 100%);
    color: #f1f5f9;
}

[data-testid="stSidebar"] {
    background: #0a1020;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    color: #f1f5f9;
}

div[data-testid="stMetric"] {
    background: #151f35;
    border: 1px solid #303d5a;
    padding: 15px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 Demand Forecast Dashboard")
st.caption("Historical demand forecasting and model evaluation")

BASE = Path(__file__).resolve().parent.parent


@st.cache_data
def load_csv(filename):
    path = BASE / filename
    if path.exists():
        return pd.read_csv(path)
    return None


# 1. Existing baseline results
forecast = load_csv("retailpulse_forecast_results.csv")

if forecast is not None:
    st.subheader("📊 Historical Forecast Results")

    if {"Month", "Quantity", "Predicted_MA"}.issubset(forecast.columns):
        forecast["Month"] = pd.to_datetime(
            forecast["Month"], format="%b %Y", errors="coerce"
        )

        mae = (forecast["Quantity"] - forecast["Predicted_MA"]).abs().mean()

        col1, col2, col3 = st.columns(3)
        col1.metric("Actual Quantity", f"{forecast['Quantity'].sum():,.0f}")
        col2.metric("Predicted Quantity", f"{forecast['Predicted_MA'].sum():,.0f}")
        col3.metric("Baseline MAE", f"{mae:,.2f}")

        chart_data = forecast.set_index("Month")[
            ["Quantity", "Predicted_MA"]
        ]
        st.line_chart(chart_data)

        st.dataframe(forecast, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Baseline Results",
            forecast.to_csv(index=False).encode("utf-8"),
            "retailpulse_forecast_results.csv",
            "text/csv"
        )
    else:
        st.warning("The baseline CSV does not contain the expected columns.")
else:
    st.warning("Baseline results file was not found.")

st.divider()

# 2. Rolling-window comparison
st.subheader("🏆 Model Comparison — Rolling-Window Validation")
st.caption(
    "Historical evaluation for WHITE HANGING HEART T-LIGHT HOLDER. "
    "Lower MAE and RMSE indicate smaller prediction errors."
)

comparison_files = {
    "Baseline + Prophet": "retailpulse_rolling_validation.csv",
    "LSTM": "retailpulse_lstm_rolling_validation.csv",
    "Hybrid": "retailpulse_hybrid_rolling_details.csv",
}

rows = []

# Prophet and baseline results
prophet_df = load_csv(comparison_files["Baseline + Prophet"])
if prophet_df is not None:
    for model_name, source_col in [
        ("Prophet", "Prophet_MAE"),
        ("Baseline", "Baseline_MAE"),
    ]:
        rmse_col = source_col.replace("_MAE", "_RMSE")
        if source_col in prophet_df.columns and rmse_col in prophet_df.columns:
            rows.append({
                "Model": model_name,
                "MAE": prophet_df[source_col].mean(),
                "RMSE": prophet_df[rmse_col].mean(),
                "Evaluation Windows": len(prophet_df)
            })

# LSTM results
lstm_df = load_csv(comparison_files["LSTM"])
if lstm_df is not None and {
    "LSTM_MAE", "LSTM_RMSE"
}.issubset(lstm_df.columns):
    rows.append({
        "Model": "LSTM",
        "MAE": lstm_df["LSTM_MAE"].mean(),
        "RMSE": lstm_df["LSTM_RMSE"].mean(),
        "Evaluation Windows": len(lstm_df)
    })

# Hybrid results
hybrid_df = load_csv(comparison_files["Hybrid"])
if hybrid_df is not None and {
    "Hybrid_MAE", "Hybrid_RMSE"
}.issubset(hybrid_df.columns):
    rows.append({
        "Model": "Hybrid",
        "MAE": hybrid_df["Hybrid_MAE"].mean(),
        "RMSE": hybrid_df["Hybrid_RMSE"].mean(),
        "Evaluation Windows": len(hybrid_df)
    })

if rows:
    comparison = pd.DataFrame(rows).sort_values("MAE").reset_index(drop=True)

    best_mae = comparison.iloc[0]
    best_rmse = comparison.loc[comparison["RMSE"].idxmin()]

    col1, col2 = st.columns(2)
    col1.metric("Lowest Average MAE", best_mae["Model"])
    col2.metric("Lowest Average RMSE", best_rmse["Model"])

    st.dataframe(
        comparison.round(2),
        use_container_width=True,
        hide_index=True
    )

    st.bar_chart(comparison.set_index("Model")[["MAE", "RMSE"]])

    st.download_button(
        "Download Model Comparison",
        comparison.to_csv(index=False).encode("utf-8"),
        "retailpulse_model_comparison.csv",
        "text/csv"
    )
else:
    st.warning(
        "No rolling-validation results found. Check that the evaluation CSV "
        "files are saved in the main Retail project folder."
    )

st.info(
    "These are historical test results, not future demand forecasts. "
    "The comparison covers one product and four test windows, so performance "
    "may differ for other products. The LSTM and hybrid models were trained "
    "in the separate .venv_lstm environment."
)
