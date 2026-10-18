
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Product Analytics | RetailPulse",
    page_icon="🛍️",
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
    df = pd.read_csv("retailpulse_cleaned.csv.gz")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True)
    df["Sales"] = df["Quantity"] * df["Price"]
    return df


df = load_data()
sales = df[~df["Invoice"].astype(str).str.startswith("C")].copy()

st.title("🛍️ Product Analytics")
st.caption("Discover top products, sales patterns, and product performance.")

# Filters
c1, c2 = st.columns(2)

with c1:
    min_date = sales["InvoiceDate"].min().date()
    max_date = sales["InvoiceDate"].max().date()

    date_range = st.date_input(
        "Select date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="product_dates"
    )

with c2:
    products = sorted(sales["Description"].dropna().unique())
    selected_products = st.multiselect(
        "Choose products (optional)",
        products,
        key="selected_products"
    )

filtered = sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["InvoiceDate"].dt.date.between(start_date, end_date)
    ]

if selected_products:
    filtered = filtered[filtered["Description"].isin(selected_products)]

if filtered.empty:
    st.warning("No product sales found for these filters.")
    st.stop()

# Product summary
product_summary = (
    filtered.groupby("Description")
    .agg(
        Revenue=("Sales", "sum"),
        Units=("Quantity", "sum"),
        Orders=("Invoice", "nunique")
    )
    .reset_index()
)

total_revenue = filtered["Sales"].sum()
total_units = filtered["Quantity"].sum()
unique_products = filtered["Description"].nunique()
total_orders = filtered["Invoice"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Net Revenue", f"£{total_revenue:,.0f}")
k2.metric("Net Units", f"{total_units:,.0f}")
k3.metric("Products", f"{unique_products:,}")
k4.metric("Orders", f"{total_orders:,}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("🏆 Top 10 Products by Revenue")
    top_revenue = (
        product_summary.nlargest(10, "Revenue")
        .sort_values("Revenue")
    )
    st.bar_chart(top_revenue, x="Description", y="Revenue", height=400)

with right:
    st.subheader("📦 Top 10 Products by Units")
    top_units = (
        product_summary.nlargest(10, "Units")
        .sort_values("Units")
    )
    st.bar_chart(top_units, x="Description", y="Units", height=400)

st.divider()

st.subheader("📈 Monthly Revenue for Top Products")

top_product_names = (
    product_summary.nlargest(5, "Revenue")["Description"].tolist()
)

monthly = filtered[filtered["Description"].isin(top_product_names)].copy()
monthly["Month"] = monthly["InvoiceDate"].dt.to_period("M").astype(str)

monthly = (
    monthly.groupby(["Month", "Description"])["Sales"]
    .sum()
    .reset_index()
)

if not monthly.empty:
    chart = monthly.pivot(
        index="Month",
        columns="Description",
        values="Sales"
    ).fillna(0)
    st.line_chart(chart, height=350)

st.subheader("📋 Product Performance Table")

product_summary = product_summary.sort_values("Revenue", ascending=False)

st.dataframe(
    product_summary,
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download product analysis CSV",
    data=product_summary.to_csv(index=False).encode("utf-8"),
    file_name="retailpulse_product_analysis.csv",
    mime="text/csv"
)

st.caption(
    "Cancellation invoices are excluded. Returns on other invoices may "
    "affect net revenue and units."
)
