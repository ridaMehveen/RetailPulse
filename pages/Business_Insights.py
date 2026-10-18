
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Business Insights | RetailPulse",
    page_icon="💡",
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
sales = df[~df["Invoice"].astype(str).str.startswith("C")].copy()

st.title("💡 Business Insights")
st.caption("Discover useful patterns in historical retail performance.")

# Date filter
min_date = sales["InvoiceDate"].min().date()
max_date = sales["InvoiceDate"].max().date()

date_range = st.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="insights_dates"
)

filtered = sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["InvoiceDate"].dt.date.between(start_date, end_date)
    ]

if filtered.empty:
    st.warning("No data found for this date range.")
    st.stop()

# KPIs
revenue = filtered["Sales"].sum()
orders = filtered["Invoice"].nunique()
products = filtered["Description"].nunique()
countries = filtered["Country"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Net Revenue", f"£{revenue:,.0f}")
c2.metric("Orders", f"{orders:,}")
c3.metric("Products", f"{products:,}")
c4.metric("Countries", f"{countries:,}")

st.divider()

# Calculate insights
country_summary = (
    filtered.groupby("Country")["Sales"]
    .sum()
    .sort_values(ascending=False)
)

product_summary = (
    filtered.groupby("Description")
    .agg(
        Revenue=("Sales", "sum"),
        Units=("Quantity", "sum")
    )
    .sort_values("Revenue", ascending=False)
)

monthly = (
    filtered.groupby(filtered["InvoiceDate"].dt.to_period("M"))["Sales"]
    .sum()
    .rename_axis("Month")
    .reset_index()
)
monthly["Month"] = monthly["Month"].astype(str)

# Insight cards
st.subheader("🔍 Key Findings")

left, right = st.columns(2)

with left:
    if not country_summary.empty and revenue != 0:
        leading_country = country_summary.index[0]
        country_share = country_summary.iloc[0] / revenue * 100

        st.info(
            f"🌍 **Leading country:** {leading_country} generated "
            f"£{country_summary.iloc[0]:,.0f} in net sales "
            f"({country_share:.1f}% of the selected period's net revenue)."
        )

    if not product_summary.empty:
        best_product = product_summary.index[0]
        best_revenue = product_summary.iloc[0]["Revenue"]

        st.success(
            f"🏆 **Top product by revenue:** {best_product}, "
            f"with £{best_revenue:,.0f} in net sales."
        )

with right:
    if not monthly.empty:
        best_month = monthly.loc[monthly["Sales"].idxmax()]
        st.info(
            f"📅 **Highest-sales month:** {best_month['Month']}, "
            f"with £{best_month['Sales']:,.0f} in net sales."
        )

    if not product_summary.empty:
        best_units_product = product_summary["Units"].idxmax()
        units = product_summary.loc[best_units_product, "Units"]

        st.success(
            f"📦 **Highest quantity:** {best_units_product}, "
            f"with {units:,.0f} net units."
        )

st.divider()

# Charts
left, right = st.columns(2)

with left:
    st.subheader("Monthly Revenue")
    if not monthly.empty:
        st.line_chart(monthly, x="Month", y="Sales", height=320)

with right:
    st.subheader("Top Countries")
    top_countries = country_summary.head(10).sort_values()
    if not top_countries.empty:
        st.bar_chart(top_countries, height=320)

st.subheader("Products Needing Attention")

st.caption(
    "The following products have the lowest net revenue among products "
    "with recorded sales in the selected period. Low revenue alone does "
    "not prove poor performance; product costs and stock availability "
    "are not included."
)

bottom_products = (
    product_summary.sort_values("Revenue")
    .head(10)
    .reset_index()
)

st.dataframe(bottom_products, use_container_width=True, hide_index=True)

st.download_button(
    "Download business insights data",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="retailpulse_business_insights.csv",
    mime="text/csv"
)

st.caption(
    "Insights describe historical data; they are not causal conclusions "
    "or future predictions. Returns on non-cancellation invoices may "
    "affect net totals."
)
