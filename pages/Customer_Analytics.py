
import streamlit as st
import pandas as pd
from auth import require_login

st.set_page_config(
    page_title="Customer Analytics | RetailPulse",
    page_icon="👥",
    layout="wide"
)
require_login()

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020, #111a30, #17152d);
    color: #f1f5f9;
}
.block-container {
    padding-top: 2rem;
    max-width: 1500px;
}
[data-testid="stSidebar"] {
    background: #0a1020;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {
    color: #e2e8f0 !important;
}
div[data-testid="stMetric"] {
    background: #151f35;
    border: 1px solid #303d5a;
    padding: 16px;
    border-radius: 14px;
}
div[data-testid="stMetricLabel"] {
    color: #bac6df;
}
div[data-testid="stMetricValue"] {
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    df =pd.read_csv("retailpulse_cleaned.csv.gz")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True)
    df["Sales"] = df["Quantity"] * df["Price"]
    return df


df = load_data()

# Customer analytics only uses identified customers
customer_sales = df.dropna(subset=["Customer ID"]).copy()

# Exclude cancellation invoices from purchase activity
customer_sales = customer_sales[
    ~customer_sales["Invoice"].astype(str).str.startswith("C")
].copy()

st.title("👥 Customer Analytics")
st.caption("Understand customer value, purchasing frequency, and spending behaviour.")

# Date filter
min_date = customer_sales["InvoiceDate"].min().date()
max_date = customer_sales["InvoiceDate"].max().date()

date_range = st.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="customer_analytics_dates"
)

filtered = customer_sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["InvoiceDate"].dt.date.between(start_date, end_date)
    ]

if filtered.empty:
    st.warning("No customer purchases found for this date range.")
    st.stop()

# Customer-level metrics
customer_summary = (
    filtered.groupby("Customer ID")
    .agg(
        Revenue=("Sales", "sum"),
        Orders=("Invoice", "nunique"),
        Units=("Quantity", "sum"),
        LastPurchase=("InvoiceDate", "max")
    )
    .reset_index()
)

total_customers = len(customer_summary)
total_revenue = filtered["Sales"].sum()
avg_spend = customer_summary["Revenue"].mean()
repeat_customers = (customer_summary["Orders"] >= 2).sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Identified Customers", f"{total_customers:,}")
c2.metric("Net Revenue", f"£{total_revenue:,.0f}")
c3.metric("Avg. Revenue per Customer", f"£{avg_spend:,.2f}")
c4.metric("Repeat Buyers", f"{repeat_customers:,}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("🏆 Top 10 Customers by Revenue")
    top_customers = (
        customer_summary.nlargest(10, "Revenue")
        .sort_values("Revenue")
        .copy()
    )
    top_customers["Customer ID"] = top_customers["Customer ID"].astype(str)
    st.bar_chart(top_customers, x="Customer ID", y="Revenue", height=350)

with right:
    st.subheader("🛍️ Purchase Frequency")
    order_distribution = (
        customer_summary["Orders"]
        .value_counts()
        .sort_index()
        .head(10)
        .rename_axis("Orders per Customer")
        .reset_index(name="Number of Customers")
    )
    st.bar_chart(
        order_distribution,
        x="Orders per Customer",
        y="Number of Customers",
        height=350
    )

st.divider()

st.subheader("💰 Customer Spending Distribution")

spending = customer_summary[["Customer ID", "Revenue"]].copy()
spending["Spending Band"] = pd.cut(
    spending["Revenue"],
    bins=[-float("inf"), 0, 100, 500, 1000, 5000, float("inf")],
    labels=[
        "Zero or Negative",
        "£0–£100",
        "£100–£500",
        "£500–£1,000",
        "£1,000–£5,000",
        "Above £5,000"
    ]
)

spending_counts = (
    spending["Spending Band"]
    .value_counts(sort=False)
    .rename_axis("Spending Band")
    .reset_index(name="Customers")
)

st.bar_chart(spending_counts, x="Spending Band", y="Customers", height=300)

with st.expander("View customer summary table"):
    st.dataframe(
        customer_summary.sort_values("Revenue", ascending=False),
        use_container_width=True
    )
    st.download_button(
        "Download customer summary CSV",
        data=customer_summary.to_csv(index=False).encode("utf-8"),
        file_name="retailpulse_customer_analytics.csv",
        mime="text/csv"
    )

st.caption(
    "Customer-level analysis excludes transactions without a Customer ID. "
    "Revenue may include returns recorded on non-cancellation invoices."
)
