
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="RetailPulse | Retail Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- CUSTOM DESIGN ----------
st.markdown("""
<style>

/* Improve sidebar text visibility */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #e2e8f0 !important;
}

/* Make navigation labels readable */
[data-testid="stSidebarNav"] span {
    color: #e2e8f0 !important;
}

/* Improve chart readability */
[data-testid="stSidebar"] [data-baseweb="select"] {
    color: #172033;
}

    .stApp {
        background: linear-gradient(135deg, #0b1020 0%, #111a30 55%, #17152d 100%);
        color: #f1f5f9;
    }
    [data-testid="stSidebar"] {
        background: #0a1020;
        border-right: 1px solid #29334d;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }
    .hero {
        padding: 28px;
        border-radius: 20px;
        background: linear-gradient(115deg, #222c55, #48358b 65%, #176b78);
        border: 1px solid #59658e;
        margin-bottom: 24px;
    }
    .hero h1 {
        color: white;
        font-size: 2.35rem;
        margin-bottom: 8px;
    }
    .hero p {
        color: #e0e7ff;
        font-size: 1rem;
        margin-bottom: 0;
    }
    .metric-card {
        background: #151f35;
        border: 1px solid #303d5a;
        padding: 20px;
        border-radius: 16px;
        min-height: 125px;
    }
    .metric-label {
        color: #a8b5d1;
        font-size: 0.9rem;
    }
    .metric-value {
        color: #ffffff;
        font-size: 1.65rem;
        font-weight: 700;
        margin-top: 10px;
    }
    .section-title {
        font-size: 1.35rem;
        font-weight: 650;
        margin-top: 24px;
        margin-bottom: 12px;
        color: #eef2ff;
    }
    div[data-testid="stMetric"] {
        background: #151f35;
        border: 1px solid #303d5a;
        padding: 15px;
        border-radius: 14px;
    }
    div[data-testid="stMetricLabel"] {
        color: #bac6df;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff;
    }
    .stCaption {
        color: #a8b5d1;
    }
</style>
""", unsafe_allow_html=True)

# ---------- DATA ----------
@st.cache_data
def load_data():
    data = pd.read_csv("retailpulse_cleaned.csv.gz")
    data["InvoiceDate"] = pd.to_datetime(
        data["InvoiceDate"], dayfirst=True
    )
    return data

df = load_data()

# Exclude cancellation invoices for the main sales view
sales = df[
    ~df["Invoice"].astype(str).str.startswith("C")
].copy()

# ---------- SIDEBAR ----------
st.sidebar.markdown("# 📊 RetailPulse")
st.sidebar.caption("AI-powered retail intelligence")
st.sidebar.divider()

st.sidebar.markdown("### Dashboard Filters")

min_date = sales["InvoiceDate"].min().date()
max_date = sales["InvoiceDate"].max().date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

countries = sorted(sales["Country"].dropna().unique())
selected_countries = st.sidebar.multiselect(
    "Countries",
    options=countries,
    default=[]
)

filtered_sales = sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_sales = filtered_sales[
        filtered_sales["InvoiceDate"].dt.date.between(
            start_date, end_date
        )
    ]

if selected_countries:
    filtered_sales = filtered_sales[
        filtered_sales["Country"].isin(selected_countries)
    ]

st.sidebar.divider()
st.sidebar.caption("RetailPulse • Analytics Workspace")

# ---------- HEADER ----------
st.markdown("""
<div class="hero">
    <h1>RetailPulse</h1>
    <p>Turn retail data into smarter business decisions.</p>
    <p>Sales intelligence · Customer analytics · Demand forecasting</p>
</div>
""", unsafe_allow_html=True)

st.markdown("## Executive Overview")
st.caption(
    "Explore business performance using the filters in the sidebar."
)

# ---------- KPI METRICS ----------
total_revenue = filtered_sales["Sales"].sum()
total_orders = filtered_sales["Invoice"].nunique()
units_sold = filtered_sales["Quantity"].sum()
unique_products = filtered_sales["Description"].nunique()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("💷 Net Revenue", f"£{total_revenue:,.0f}")

with c2:
    st.metric("🧾 Orders", f"{total_orders:,.0f}")

with c3:
    st.metric("📦 Net Units", f"{units_sold:,.0f}")

with c4:
    st.metric("🏷️ Products", f"{unique_products:,.0f}")

# ---------- CHARTS ----------
st.markdown(
    '<div class="section-title">Sales Performance</div>',
    unsafe_allow_html=True
)

left, right = st.columns([1.6, 1])

with left:
    monthly_sales = (
        filtered_sales
        .groupby(filtered_sales["InvoiceDate"].dt.to_period("M"))["Sales"]
        .sum()
        .rename_axis("Month")
        .reset_index()
    )
    monthly_sales["Month"] = monthly_sales["Month"].dt.to_timestamp()

    st.markdown("#### Monthly Revenue Trend")
    if not monthly_sales.empty:
        st.line_chart(
            monthly_sales,
            x="Month",
            y="Sales",
            height=340
        )
    else:
        st.info("No sales data for the selected filters.")

with right:
    top_products = (
        filtered_sales.groupby("Description")["Sales"]
        .sum()
        .nlargest(8)
        .sort_values()
    )

    st.markdown("#### Top Products by Revenue")
    if not top_products.empty:
        st.bar_chart(top_products, height=340)
    else:
        st.info("No product data available.")

# ---------- COUNTRY INSIGHTS ----------
st.markdown(
    '<div class="section-title">Geographic Performance</div>',
    unsafe_allow_html=True
)

country_sales = (
    filtered_sales.groupby("Country")["Sales"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

if not country_sales.empty:
    st.bar_chart(
        country_sales.set_index("Country"),
        height=300
    )

# ---------- DATA PREVIEW ----------
with st.expander("Explore filtered sales data"):
    st.dataframe(
        filtered_sales.head(500),
        use_container_width=True
    )
    st.caption(
        "Showing up to 500 rows. Figures reflect the selected filters."
    )

st.caption(
    "RetailPulse | Historical retail analytics. "
    "Revenue and unit totals may include returns recorded on "
    "non-cancellation invoices."
)
