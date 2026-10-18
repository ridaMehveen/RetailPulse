

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Country Analysis | RetailPulse",
    page_icon="🌍",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020, #111a30, #17152d);
    color: #f1f5f9;
}
.block-container { padding-top: 2rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: #0a1020; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: #e2e8f0 !important; }
div[data-testid="stMetric"] {
    background: #151f35;
    border: 1px solid #303d5a;
    padding: 16px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    df = pd.read_csv("retailpulse_cleaned.csv")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True)
    df["Sales"] = df["Quantity"] * df["Price"]
    return df


df = load_data()

# Exclude cancellation invoices from this sales view
sales = df[~df["Invoice"].astype(str).str.startswith("C")].copy()

st.title("🌍 Country Analysis")
st.caption("Compare sales performance across countries.")

# Filters
min_date = sales["InvoiceDate"].min().date()
max_date = sales["InvoiceDate"].max().date()

date_range = st.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="country_dates"
)

filtered = sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["InvoiceDate"].dt.date.between(start_date, end_date)
    ]

if filtered.empty:
    st.warning("No sales data found for the selected dates.")
    st.stop()

# Country summary
country_summary = (
    filtered.groupby("Country")
    .agg(
        Revenue=("Sales", "sum"),
        Orders=("Invoice", "nunique"),
        Units=("Quantity", "sum"),
        Customers=("Customer ID", "nunique")
    )
    .reset_index()
    .sort_values("Revenue", ascending=False)
)

total_revenue = filtered["Sales"].sum()
country_count = filtered["Country"].nunique()
top_country = country_summary.iloc[0]["Country"]
total_orders = filtered["Invoice"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Net Revenue", f"£{total_revenue:,.0f}")
c2.metric("Countries", f"{country_count:,}")
c3.metric("Top Country", str(top_country))
c4.metric("Orders", f"{total_orders:,}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("🏆 Top 10 Countries by Revenue")
    top_revenue = country_summary.nlargest(10, "Revenue").sort_values("Revenue")
    st.bar_chart(top_revenue, x="Country", y="Revenue", height=380)

with right:
    st.subheader("🧾 Top 10 Countries by Orders")
    top_orders = country_summary.nlargest(10, "Orders").sort_values("Orders")
    st.bar_chart(top_orders, x="Country", y="Orders", height=380)

st.divider()

st.subheader("📦 Units Sold by Country")
top_units = country_summary.nlargest(10, "Units").sort_values("Units")
st.bar_chart(top_units, x="Country", y="Units", height=320)

st.subheader("📋 Country Performance Table")
st.dataframe(
    country_summary,
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download country analysis CSV",
    data=country_summary.to_csv(index=False).encode("utf-8"),
    file_name="retailpulse_country_analysis.csv",
    mime="text/csv"
)

st.caption(
    "Customer counts include only identified customer IDs. "
    "Returns on non-cancellation invoices may affect net totals."
)
