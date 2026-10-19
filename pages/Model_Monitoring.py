
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import ks_2samp

from auth import require_login

require_login()

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020 0%, #111a30 55%, #17152d 100%);
    color: #f1f5f9;
}
[data-testid="stSidebar"] { background: #0a1020; }
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

BASE_DIR = Path(__file__).resolve().parent.parent

st.title("🩺 Model Monitoring")
st.caption(
    "Historical model evaluation and retail data drift analysis"
)

st.info(
    "This dashboard analyses saved validation results and historical data. "
    "It does not continuously monitor a deployed model."
)


# --------------------------------------------------
# Load historical forecasting evaluation results
# --------------------------------------------------
@st.cache_data
def load_evaluation_files():
    results = []

    files = [
        ("Baseline vs Prophet", "retailpulse_rolling_validation.csv",
         "Prophet", "Prophet_MAE", "Prophet_RMSE"),
        ("LSTM", "retailpulse_lstm_rolling_validation.csv",
         "LSTM", "LSTM_MAE", "LSTM_RMSE"),
        ("Hybrid", "retailpulse_hybrid_rolling_details.csv",
         "Hybrid", "Hybrid_MAE", "Hybrid_RMSE"),
    ]

    for comparison, filename, model, mae_col, rmse_col in files:
        path = BASE_DIR / filename

        if not path.exists():
            continue

        try:
            df = pd.read_csv(path)

            if {"Test_Start", "Test_End", mae_col, rmse_col}.issubset(df.columns):
                part = df[
                    ["Test_Start", "Test_End", mae_col, rmse_col]
                ].copy()

                part.columns = [
                    "Test_Start", "Test_End", "MAE", "RMSE"
                ]
                part["Model"] = model
                results.append(part)

        except Exception:
            continue

    if not results:
        return pd.DataFrame()

    return pd.concat(results, ignore_index=True)


# --------------------------------------------------
# Load cleaned retail data
# --------------------------------------------------
@st.cache_data(show_spinner="Loading retail data...")
def load_retail_data():
    compressed = BASE_DIR / "retailpulse_cleaned.csv.gz"
    regular = BASE_DIR / "retailpulse_cleaned.csv"

    if compressed.exists():
        path = compressed
    elif regular.exists():
        path = regular
    else:
        raise FileNotFoundError(
            "Neither retailpulse_cleaned.csv.gz nor "
            "retailpulse_cleaned.csv was found."
        )

    df = pd.read_csv(
        path,
        usecols=["InvoiceDate", "Quantity", "Price", "Sales"],
    )

    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"],
        dayfirst=True,
        errors="coerce",
    )

    for column in ["Quantity", "Price", "Sales"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(
        subset=["InvoiceDate", "Quantity", "Price", "Sales"]
    )

    df["Month"] = df["InvoiceDate"].dt.to_period("M").astype(str)

    return df


# --------------------------------------------------
# Section 1: Model performance
# --------------------------------------------------
st.header("1. Forecast Model Performance")

evaluation = load_evaluation_files()

if evaluation.empty:
    st.warning(
        "No compatible rolling-validation files were found. "
        "Check that the evaluation CSV files exist in the project root."
    )
else:
    evaluation["MAE"] = pd.to_numeric(
        evaluation["MAE"], errors="coerce"
    )
    evaluation["RMSE"] = pd.to_numeric(
        evaluation["RMSE"], errors="coerce"
    )
    evaluation = evaluation.dropna(subset=["MAE", "RMSE"])

    if not evaluation.empty:
        summary = (
            evaluation.groupby("Model", as_index=False)
            .agg(
                Average_MAE=("MAE", "mean"),
                Average_RMSE=("RMSE", "mean"),
                Windows=("MAE", "count"),
            )
            .sort_values("Average_MAE")
        )

        best = summary.iloc[0]

        c1, c2, c3 = st.columns(3)
        c1.metric("Lowest Average MAE", f"{best['Average_MAE']:,.2f}")
        c2.metric("Corresponding RMSE", f"{best['Average_RMSE']:,.2f}")
        c3.metric("Validation Windows", int(best["Windows"]))

        st.caption(
            f"Lowest MAE among the loaded results: {best['Model']}. "
            "This is a historical comparison, not a guarantee of future performance."
        )

        st.subheader("Average error by model")
        st.bar_chart(
            summary.set_index("Model")[["Average_MAE", "Average_RMSE"]]
        )

        st.dataframe(
            summary.round(3),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "The model files may cover different validation windows. "
            "Compare results with that limitation in mind."
        )


# --------------------------------------------------
# Section 2: Historical data drift
# --------------------------------------------------
st.divider()
st.header("2. Historical Data Drift")

try:
    retail = load_retail_data()

    st.caption(
        f"Loaded {len(retail):,} valid records from "
        f"{retail['InvoiceDate'].min():%d %b %Y} to "
        f"{retail['InvoiceDate'].max():%d %b %Y}."
    )

    months = sorted(retail["Month"].unique())

    if len(months) < 2:
        st.warning("At least two distinct months are needed for comparison.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            reference_month = st.selectbox(
                "Reference month",
                months,
                index=0,
                key="monitor_reference_month",
            )

        with col2:
            comparison_month = st.selectbox(
                "Comparison month",
                months,
                index=len(months) - 1,
                key="monitor_comparison_month",
            )

        if reference_month == comparison_month:
            st.warning("Choose two different months to compare.")
        else:
            reference = retail.loc[
                retail["Month"] == reference_month
            ]

            comparison = retail.loc[
                retail["Month"] == comparison_month
            ]

            st.write(
                f"Reference: **{reference_month}** "
                f"({len(reference):,} rows)  ·  "
                f"Comparison: **{comparison_month}** "
                f"({len(comparison):,} rows)"
            )

            def calculate_psi(reference_values, comparison_values, bins=10):
                """Population Stability Index using reference quantile bins."""
                ref = np.asarray(reference_values, dtype=float)
                cur = np.asarray(comparison_values, dtype=float)

                ref = ref[np.isfinite(ref)]
                cur = cur[np.isfinite(cur)]

                if len(ref) < 2 or len(cur) < 2:
                    return np.nan

                edges = np.unique(
                    np.quantile(ref, np.linspace(0, 1, bins + 1))
                )

                if len(edges) < 2:
                    return 0.0 if np.allclose(
                        ref, cur, equal_nan=True
                    ) else np.nan

                edges[0] = -np.inf
                edges[-1] = np.inf

                ref_counts = np.histogram(ref, bins=edges)[0]
                cur_counts = np.histogram(cur, bins=edges)[0]

                ref_pct = ref_counts / len(ref)
                cur_pct = cur_counts / len(cur)

                epsilon = 1e-6
                ref_pct = np.clip(ref_pct, epsilon, None)
                cur_pct = np.clip(cur_pct, epsilon, None)

                return float(
                    np.sum(
                        (cur_pct - ref_pct)
                        * np.log(cur_pct / ref_pct)
                    )
                )

            drift_rows = []

            for feature in ["Quantity", "Price", "Sales"]:
                ref_values = reference[feature].to_numpy(dtype=float)
                cur_values = comparison[feature].to_numpy(dtype=float)

                psi = calculate_psi(ref_values, cur_values)
                ks_result = ks_2samp(ref_values, cur_values)

                if pd.isna(psi):
                    status = "Insufficient variation"
                elif psi >= 0.20:
                    status = "Potential drift"
                else:
                    status = "No major PSI signal"

                drift_rows.append({
                    "Feature": feature,
                    "Reference mean": np.mean(ref_values),
                    "Comparison mean": np.mean(cur_values),
                    "PSI": psi,
                    "KS statistic": ks_result.statistic,
                    "KS p-value": ks_result.pvalue,
                    "Status": status,
                })

            drift = pd.DataFrame(drift_rows)

            potential_drift = int(
                (drift["Status"] == "Potential drift").sum()
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Features checked", len(drift))
            c2.metric("Potential drift signals", potential_drift)
            c3.metric(
                "Reference records",
                f"{len(reference):,}",
            )

            st.subheader("Feature drift results")
            st.dataframe(
                drift.round(5),
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Distribution comparison")

            selected_feature = st.selectbox(
                "Choose a feature",
                ["Quantity", "Price", "Sales"],
                key="monitor_feature",
            )

            chart_data = pd.DataFrame({
                reference_month: reference[selected_feature]
                    .replace([np.inf, -np.inf], np.nan)
                    .dropna()
                    .reset_index(drop=True),
                comparison_month: comparison[selected_feature]
                    .replace([np.inf, -np.inf], np.nan)
                    .dropna()
                    .reset_index(drop=True),
            })

            st.line_chart(
                chart_data,
                height=300,
            )

            st.caption(
                "PSI is a distribution-change indicator; values around 0.10 "
                "and 0.20 are sometimes used as rough reference thresholds, "
                "not universal rules. The KS p-value is sample-size sensitive. "
                "Neither metric alone proves model degradation."
            )

            if potential_drift:
                st.warning(
                    f"{potential_drift} feature(s) crossed the configured "
                    "PSI threshold of 0.20. Review the affected distributions."
                )
            else:
                st.success(
                    "No feature crossed the configured PSI threshold "
                    "in this comparison. This does not prove that the data "
                    "or model is unchanged."
                )

except FileNotFoundError as error:
    st.error(str(error))
except Exception as error:
    st.error(f"Could not complete drift analysis: {error}")
    st.caption(
        "Check the dataset path, date parsing, and column names."
    )


# --------------------------------------------------
# Section 3: Interpretation and limitations
# --------------------------------------------------
st.divider()
st.header("3. Monitoring Notes")

st.markdown("""
- **Model performance** uses saved historical validation results.
- **Data drift** compares distributions from two historical months.
- **Potential drift** is a signal for investigation, not proof that a model has failed.
- **Live monitoring is not configured:** this page does not ingest new transactions or automatically retrain models.
- The retail data spans historical periods, so changes may reflect seasonality,
  promotions, product mix, or other business factors.
""")
