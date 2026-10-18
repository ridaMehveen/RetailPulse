
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Executive Dashboard | RetailPulse",
    page_icon="📊",
    layout="wide"
)

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
    df = pd.read_csv("retailpulse_cleaned.csv.gz")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True)
    df["Sales"] = df["Quantity"] * df["Price"]
    return df


df = load_data()
sales = df[~df["Invoice"].astype(str).str.startswith("C")].copy()

st.title("📊 Executive Dashboard")
st.caption("A high-level view of retail business performance.")

# Filters
c1, c2 = st.columns(2)

with c1:
    min_date = sales["InvoiceDate"].min().date()
    max_date = sales["InvoiceDate"].max().date()
    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="exec_dates"
    )

with c2:
    countries = sorted(sales["Country"].dropna().unique())
    selected_countries = st.multiselect(
        "Countries",
        countries,
        key="exec_countries"
    )

filtered = sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["InvoiceDate"].dt.date.between(start_date, end_date)
    ]

if selected_countries:
    filtered = filtered[filtered["Country"].isin(selected_countries)]

# KPIs
revenue = filtered["Sales"].sum()
orders = filtered["Invoice"].nunique()
units = filtered["Quantity"].sum()
customers = filtered["Customer ID"].nunique()
products = filtered["Description"].nunique()

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("💷 Net Revenue", f"£{revenue:,.0f}")
k2.metric("🧾 Orders", f"{orders:,}")
k3.metric("📦 Net Units", f"{units:,.0f}")
k4.metric("👥 Identified Customers", f"{customers:,}")
k5.metric("🏷️ Products", f"{products:,}")

st.divider()

# Revenue trend
left, right = st.columns([1.6, 1])

with left:
    st.subheader("📈 Monthly Revenue")

    monthly = (
        filtered.groupby(filtered["InvoiceDate"].dt.to_period("M"))["Sales"]
        .sum()
        .rename_axis("Month")
        .reset_index()
    )
    monthly["Month"] = monthly["Month"].astype(str)

    if not monthly.empty:
        st.line_chart(monthly, x="Month", y="Sales", height=320)
    else:
        st.info("No data for these filters.")

with right:
    st.subheader("🌍 Top Countries")

    country_sales = (
        filtered.groupby("Country")["Sales"]
        .sum()
        .nlargest(8)
        .sort_values()
    )

    if not country_sales.empty:
        st.bar_chart(country_sales, height=320)

st.divider()

# Product performance
st.subheader("🏆 Top 10 Products by Revenue")

top_products = (
    filtered.groupby("Description")["Sales"]
    .sum()
    .nlargest(10)
    .sort_values()
)

if not top_products.empty:
    st.bar_chart(top_products, height=350)
else:
    st.info("No products found for the selected filters.")

with st.expander("View executive data summary"):
    summary = pd.DataFrame({
        "Metric": [
            "Net revenue",
            "Unique orders",
            "Net units",
            "Customers with identified IDs",
            "Unique products"
        ],
        "Value": [
            round(revenue, 2),
            orders,
            units,
            customers,
            products
        ]
    })
    st.dataframe(summary, use_container_width=True)

st.caption(
    "Historical data. Customer counts include only records with "
    "identified customer IDs. Returns on non-cancellation invoices "
    "may affect net totals."
)
