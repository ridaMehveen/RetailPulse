
import streamlit as st
import pandas as pd
import plotly.express as px
from auth import require_login

st.set_page_config(
    page_title="Sales Analytics | RetailPulse",
    page_icon="📈",
    layout="wide"
)
require_login()

# --------------------------------------------------
# THEME & STYLING
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(
        135deg, #0b1020, #111a30, #17152d
    );
    color: #f1f5f9;
}

.block-container {
    padding: 2rem clamp(1rem, 2.5vw, 2rem);
    max-width: 1800px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0a1020;
    border-right: 1px solid #29334d;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #e2e8f0 !important;
}

/* Headings and text */
h1, h2, h3, h4 {
    color: #f1f5f9 !important;
}

[data-testid="stCaptionContainer"] {
    color: #b8c5df !important;
}

[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p {
    color: #dbe5f7 !important;
}

/* KPI cards */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #192742, #151d32);
    border: 1px solid #354363;
    padding: 16px;
    border-radius: 14px;
    min-height: 112px;
    box-shadow: 0 5px 18px rgba(0, 0, 0, 0.12);
}

div[data-testid="stMetric"] [data-testid="stMetricLabel"],
div[data-testid="stMetric"] [data-testid="stMetricLabel"] p,
div[data-testid="stMetric"] [data-testid="stMetricLabel"] label {
    color: #e2e8f0 !important;
    -webkit-text-fill-color: #e2e8f0 !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}

div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 700 !important;
}

/* Plotly chart containers */
div[data-testid="stPlotlyChart"] {
    background: #151f35 !important;
    border: 1px solid #303d5a;
    border-radius: 14px;
    padding: 8px;
}

/* Data table */
div[data-testid="stDataFrame"] {
    background: #151f35 !important;
    border: 1px solid #303d5a;
    border-radius: 12px;
    overflow: hidden;
}

/* Buttons */
.stButton > button,
.stDownloadButton > button {
    background: #6d5ce8;
    color: #ffffff !important;
    border: 1px solid #8b7cf6;
    border-radius: 10px;
    font-weight: 600;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background: #5746d4;
    color: #ffffff !important;
    border-color: #a99fff;
}

hr {
    border-color: #303d5a;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    data = pd.read_csv("retailpulse_cleaned.csv.gz")

    data["InvoiceDate"] = pd.to_datetime(
        data["InvoiceDate"],
        dayfirst=True
    )

    data["Sales"] = data["Quantity"] * data["Price"]

    return data


df = load_data()

# Exclude cancellation invoices from this sales view
sales = df[
    ~df["Invoice"].astype(str).str.startswith("C")
].copy()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("📈 Sales Analytics")
st.caption(
    "Explore revenue trends, order activity, and product performance."
)


# --------------------------------------------------
# FILTERS
# --------------------------------------------------

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


# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------

revenue = filtered["Sales"].sum()
orders = filtered["Invoice"].nunique()
units = filtered["Quantity"].sum()
avg_order_value = revenue / orders if orders else 0

c1, c2, c3, c4 = st.columns(4)

c1.metric("💷 Net Revenue", f"£{revenue:,.0f}")
c2.metric("🧾 Orders", f"{orders:,}")
c3.metric("📦 Net Units Sold", f"{units:,.0f}")
c4.metric("🛒 Avg. Order Value", f"£{avg_order_value:,.2f}")

st.divider()


# --------------------------------------------------
# MONTHLY SALES CALCULATIONS
# --------------------------------------------------

monthly = (
    filtered.groupby(
        filtered["InvoiceDate"].dt.to_period("M")
    )
    .agg(
        Revenue=("Sales", "sum"),
        Orders=("Invoice", "nunique")
    )
    .reset_index()
)

monthly["Month"] = monthly["InvoiceDate"].astype(str)
monthly = monthly.sort_values("InvoiceDate")


# --------------------------------------------------
# DARK CHART STYLE
# --------------------------------------------------

def style_dark_chart(fig, height=320):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", size=12),
        height=height,
        margin=dict(l=25, r=20, t=25, b=45),
        hoverlabel=dict(
            bgcolor="#202d47",
            font_color="#ffffff",
            bordercolor="#526586"
        )
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(color="#cbd5e1"),
        title_font=dict(color="#e2e8f0")
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False,
        tickfont=dict(color="#cbd5e1"),
        title_font=dict(color="#e2e8f0")
    )

    return fig


# --------------------------------------------------
# MONTHLY REVENUE TREND
# --------------------------------------------------

st.subheader("📈 Monthly Revenue Trend")

if not monthly.empty:
    fig_revenue = px.line(
        monthly,
        x="Month",
        y="Revenue",
        markers=True,
        labels={
            "Month": "Month",
            "Revenue": "Revenue (£)"
        }
    )

    fig_revenue.update_traces(
        line=dict(color="#60a5fa", width=3),
        marker=dict(color="#a78bfa", size=6),
        hovertemplate=(
            "Month: %{x}<br>"
            "Revenue: £%{y:,.0f}"
            "<extra></extra>"
        )
    )

    fig_revenue.update_layout(xaxis_tickangle=-35)
    style_dark_chart(fig_revenue, height=350)

    st.plotly_chart(
        fig_revenue,
        use_container_width=True
    )
else:
    st.info("No sales records match the selected filters.")


# --------------------------------------------------
# MONTHLY ORDERS & TOP PRODUCTS
# --------------------------------------------------

left, right = st.columns(2)

with left:
    st.subheader("🧾 Monthly Orders")

    if not monthly.empty:
        fig_orders = px.bar(
            monthly,
            x="Month",
            y="Orders",
            labels={
                "Month": "Month",
                "Orders": "Number of Orders"
            }
        )

        fig_orders.update_traces(
            marker_color="#818cf8",
            hovertemplate=(
                "Month: %{x}<br>"
                "Orders: %{y:,}"
                "<extra></extra>"
            )
        )

        fig_orders.update_layout(xaxis_tickangle=-35)
        style_dark_chart(fig_orders, height=320)

        st.plotly_chart(
            fig_orders,
            use_container_width=True
        )
    else:
        st.info("No monthly order data available.")

with right:
    st.subheader("🏆 Top 10 Products by Revenue")

    top_products = (
        filtered.groupby("Description")["Sales"]
        .sum()
        .nlargest(10)
        .sort_values()
    )

    if not top_products.empty:
        product_data = (
            top_products
            .rename_axis("Product")
            .reset_index(name="Revenue")
        )

        fig_products = px.bar(
            product_data,
            x="Revenue",
            y="Product",
            orientation="h",
            labels={
                "Revenue": "Revenue (£)",
                "Product": "Product"
            }
        )

        fig_products.update_traces(
            marker_color="#34d399",
            hovertemplate=(
                "Product: %{y}<br>"
                "Revenue: £%{x:,.2f}"
                "<extra></extra>"
            )
        )

        style_dark_chart(fig_products, height=320)

        st.plotly_chart(
            fig_products,
            use_container_width=True
        )
    else:
        st.info("No product data available.")


# --------------------------------------------------
# REVENUE BY COUNTRY
# --------------------------------------------------

st.subheader("🌍 Revenue by Country")

country_revenue = (
    filtered.groupby("Country")["Sales"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

if not country_revenue.empty:
    country_data = (
        country_revenue
        .rename_axis("Country")
        .reset_index(name="Revenue")
        .sort_values("Revenue")
    )

    fig_country = px.bar(
        country_data,
        x="Revenue",
        y="Country",
        orientation="h",
        labels={
            "Revenue": "Revenue (£)",
            "Country": "Country"
        }
    )

    fig_country.update_traces(
        marker_color="#22d3ee",
        hovertemplate=(
            "Country: %{y}<br>"
            "Revenue: £%{x:,.2f}"
            "<extra></extra>"
        )
    )

    style_dark_chart(fig_country, height=360)

    st.plotly_chart(
        fig_country,
        use_container_width=True
    )
else:
    st.info("No country revenue data available.")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.caption(
    "Historical retail data. Cancellation invoices are excluded, "
    "but returns recorded on other invoices may affect net totals."
)
