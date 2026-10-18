
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Sales Analytics | RetailPulse",
    page_icon="📈",
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
    data = pd.read_csv("retailpulse_cleaned.csv")
    data["InvoiceDate"] = pd.to_datetime(
        data["InvoiceDate"], dayfirst=True
    )
    data["Sales"] = data["Quantity"] * data["Price"]
    return data


df = load_data()

# Exclude cancellation invoices from this sales view
sales = df[
    ~df["Invoice"].astype(str).str.startswith("C")
].copy()

st.title("📈 Sales Analytics")
st.caption(
    "Explore revenue trends, order activity, and product performance."
)

# Filters
col1, col2 = st.columns(2)

with col1:
    min_date = sales["InvoiceDate"].min().date()
    max_date = sales["InvoiceDate"].max().date()

    date_range = st.date_input(
        "Select date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="sales_date_range"
    )

with col2:
    countries = sorted(sales["Country"].dropna().unique())
    selected_countries = st.multiselect(
        "Select countries",
        countries,
        key="sales_countries"
    )

filtered = sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["InvoiceDate"].dt.date.between(
            start_date, end_date
        )
    ]

if selected_countries:
    filtered = filtered[
        filtered["Country"].isin(selected_countries)
    ]

# KPIs
revenue = filtered["Sales"].sum()
orders = filtered["Invoice"].nunique()
units = filtered["Quantity"].sum()
avg_order_value = revenue / orders if orders else 0

c1, c2, c3, c4 = st.columns(4)

c1.metric("Net Revenue", f"£{revenue:,.0f}")
c2.metric("Orders", f"{orders:,}")
c3.metric("Net Units Sold", f"{units:,.0f}")
c4.metric("Avg. Order Value", f"£{avg_order_value:,.2f}")

st.divider()

# Monthly sales trend
st.subheader("Monthly Revenue Trend")

monthly = (
    filtered.groupby(filtered["InvoiceDate"].dt.to_period("M"))
    .agg(
        Revenue=("Sales", "sum"),
        Orders=("Invoice", "nunique")
    )
    .reset_index()
)

monthly["Month"] = monthly["InvoiceDate"].astype(str)
monthly = monthly.sort_values("InvoiceDate")

if not monthly.empty:
    st.line_chart(
        monthly,
        x="Month",
        y="Revenue",
        height=350
    )
else:
    st.info("No sales records match the selected filters.")

# Monthly order activity
left, right = st.columns(2)

with left:
    st.subheader("Monthly Orders")
    if not monthly.empty:
        st.bar_chart(
            monthly,
            x="Month",
            y="Orders",
            height=300
        )

with right:
    st.subheader("Top 10 Products by Revenue")
    top_products = (
        filtered.groupby("Description")["Sales"]
        .sum()
        .nlargest(10)
        .sort_values()
    )

    if not top_products.empty:
        st.bar_chart(top_products, height=300)
    else:
        st.info("No product data available.")

# Country contribution
st.subheader("Revenue by Country")

country_revenue = (
    filtered.groupby("Country")["Sales"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

if not country_revenue.empty:
    st.bar_chart(country_revenue, height=320)

st.caption(
    "Historical retail data. Cancellation invoices are excluded, "
    "but returns recorded on other invoices may affect net totals."
)
