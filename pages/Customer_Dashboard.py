
import streamlit as st
import pandas as pd
from auth import require_login


st.set_page_config(
    page_title="RetailPulse - Customer Analytics",
    page_icon="👥",
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

[data-testid="stDataFrame"] {
    border: 1px solid #303d5a;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# Load saved customer predictions
@st.cache_data
def load_customers():
    return pd.read_csv("retailpulse_customer_churn.csv")

customers = load_customers()

# Dashboard title
st.title("👥 Customer Analytics Dashboard")
st.caption("Customer behaviour and predicted churn risk")

# KPI calculations
total_customers = customers["Customer ID"].nunique()
high_risk = (customers["Churn_Probability"] >= 0.70).sum()
average_recency = customers["Recency"].mean()
average_spending = customers["Monetary"].mean()

# KPI cards
col1, col2, col3, col4 = st.columns(4)

col1.metric("Identified Customers", f"{total_customers:,}")
col2.metric("High-Risk Customers", f"{high_risk:,}")
col3.metric("Average Recency", f"{average_recency:.0f} days")
col4.metric("Average Customer Spending", f"£{average_spending:,.0f}")

st.divider()

# Churn risk distribution
st.subheader("📊 Customer Churn Risk Distribution")

risk_customers = customers.copy()

risk_customers["Risk Level"] = pd.cut(
    risk_customers["Churn_Probability"],
    bins=[-0.01, 0.30, 0.70, 1.00],
    labels=["Low Risk", "Medium Risk", "High Risk"]
)

risk_counts = (
    risk_customers["Risk Level"]
    .value_counts()
    .reindex(["Low Risk", "Medium Risk", "High Risk"], fill_value=0)
)

st.bar_chart(risk_counts)

# Highest-risk customers


# ---------------- RFM CUSTOMER SEGMENTATION ----------------
st.divider()
st.subheader("👥 RFM Customer Segmentation")

@st.cache_data
def load_segments():
    return pd.read_csv("retailpulse_customer_segments.csv")

segments_df = load_segments()

# Customer count by segment
segment_counts = (
    segments_df["Customer_Segment"]
    .value_counts()
    .rename_axis("Customer Segment")
    .reset_index(name="Number of Customers")
)

col1, col2 = st.columns(2)

with col1:
    st.write("**Customers by Segment**")
    st.bar_chart(
        segment_counts.set_index("Customer Segment")
    )

with col2:
    st.write("**Segment Summary**")
    st.dataframe(
        segment_counts,
        use_container_width=True,
        hide_index=True
    )


# Filter customers by segment
st.subheader("🔎 Explore Customer Segments")

segment_options = sorted(
    segments_df["Customer_Segment"].dropna().unique()
)

selected_segment = st.selectbox(
    "Choose a customer segment",
    ["All Segments"] + segment_options
)

if selected_segment == "All Segments":
    displayed_customers = segments_df
else:
    displayed_customers = segments_df[
        segments_df["Customer_Segment"] == selected_segment
    ]

st.write(f"Customers found: {len(displayed_customers):,}")

st.dataframe(
    displayed_customers[
        [
            "Customer ID",
            "Recency",
            "Frequency",
            "Monetary",
            "RFM_Score",
            "Customer_Segment"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download Selected Customer Segment",
    data=displayed_customers.to_csv(index=False).encode("utf-8"),
    file_name="retailpulse_selected_customers.csv",
    mime="text/csv"
)


st.subheader("⚠️ Customers with Highest Predicted Churn Risk")

top_risk = customers.sort_values(
    "Churn_Probability",
    ascending=False
).head(20)

st.dataframe(
    top_risk,
    use_container_width=True,
    hide_index=True
)

# Download results
st.download_button(
    "Download Customer Risk Report",
    data=customers.to_csv(index=False).encode("utf-8"),
    file_name="retailpulse_customer_risk_report.csv",
    mime="text/csv"
)

st.caption(
    "These are historical model predictions, not live customer churn estimates. "
    "High risk means predicted probability of 70% or more."
)
