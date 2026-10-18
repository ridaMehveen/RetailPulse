
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="RetailPulse - Inventory",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Inventory & Demand Dashboard")
st.caption("Product demand analysis and stock planning recommendations")

# Load cleaned retail data
@st.cache_data
def load_data():
    data = pd.read_csv("retailpulse_cleaned.csv")
    data["InvoiceDate"] = pd.to_datetime(
        data["InvoiceDate"], dayfirst=True
    )
    return data

df = load_data()

# Exclude cancellation invoices
sales = df[
    ~df["Invoice"].astype(str).str.startswith("C")
].copy()

# Select date range
st.sidebar.subheader("📅 Inventory Filters")

min_date = sales["InvoiceDate"].min().date()
max_date = sales["InvoiceDate"].max().date()

date_range = st.sidebar.date_input(
    "Analysis period",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    sales = sales[
        sales["InvoiceDate"].dt.date.between(start_date, end_date)
    ]

# Product-level demand summary
product_summary = (
    sales.groupby("Description")
    .agg(
        Units_Sold=("Quantity", "sum"),
        Revenue=("Sales", "sum"),
        Orders=("Invoice", "nunique")
    )
    .reset_index()
)

# Average units per day in the selected period
period_days = max((end_date - start_date).days + 1, 1)

product_summary["Avg_Daily_Demand"] = (
    product_summary["Units_Sold"] / period_days
)

# Illustrative 7-day demand estimate
product_summary["Suggested_7_Day_Demand"] = (
    product_summary["Avg_Daily_Demand"] * 7
).round().astype(int)

# Inventory KPIs
col1, col2, col3 = st.columns(3)

col1.metric(
    "Products Analysed",
    f"{product_summary['Description'].nunique():,}"
)

col2.metric(
    "Net Units Sold",
    f"{product_summary['Units_Sold'].sum():,.0f}"
)

col3.metric(
    "Products With Positive Demand",
    f"{(product_summary['Avg_Daily_Demand'] > 0).sum():,}"
)

st.divider()

# Highest-demand products
st.subheader("🔥 Products With Highest Recorded Demand")

top_demand = (
    product_summary.nlargest(10, "Avg_Daily_Demand")
    .sort_values("Avg_Daily_Demand", ascending=True)
)

st.bar_chart(
    top_demand.set_index("Description")["Avg_Daily_Demand"]
)

# Recommendations table
st.subheader("📋 Demand-Based Planning Recommendations")

recommendations = product_summary.sort_values(
    "Avg_Daily_Demand", ascending=False
)

st.dataframe(
    recommendations[
        [
            "Description",
            "Units_Sold",
            "Avg_Daily_Demand",
            "Suggested_7_Day_Demand",
            "Revenue",
            "Orders"
        ]
    ].head(50),
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download Demand Planning Report",
    data=recommendations.to_csv(index=False).encode("utf-8"),
    file_name="retailpulse_demand_planning.csv",
    mime="text/csv"
)

st.info(
    "The 7-day figures are estimates based on average recorded daily quantity, "
    "not a validated forecast. Actual stock-on-hand, supplier lead time, "
    "safety stock and future forecasts are needed for true reorder recommendations. "
    "Returns and cancellations may also affect recorded quantities."
)
