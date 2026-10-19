
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="RetailPulse | Retail Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- CUSTOM DESIGN ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(
        135deg, #0b1020 0%, #111a30 55%, #17152d 100%
    );
    color: #f1f5f9;
}

.block-container {
    padding: 1.8rem clamp(1rem, 2.5vw, 2rem) 2rem;
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

[data-testid="stSidebar"] [data-baseweb="select"] {
    background-color: #151f35;
    border-radius: 8px;
}

[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    background: #151f35;
    color: #f1f5f9 !important;
    border-color: #394866;
}

/* Hero banner */
.hero {
    padding: 30px;
    border-radius: 20px;
    background: linear-gradient(
        115deg, #222c55 0%, #48358b 65%, #176b78 100%
    );
    border: 1px solid #59658e;
    margin-bottom: 26px;
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.16);
}

.hero h1 {
    color: #ffffff !important;
    font-size: clamp(2rem, 3vw, 2.7rem);
    font-weight: 750;
    margin: 0 0 12px 0;
}

.hero p {
    color: #edf0ff !important;
    font-size: 1rem;
    margin: 5px 0 0 0;
}

/* Headings and supporting text */
h1, h2, h3, h4 {
    color: #f1f5f9 !important;
}

[data-testid="stCaptionContainer"] {
    color: #b8c5df !important;
}

[data-testid="stMarkdownContainer"] p {
    color: #e2e8f0;
}

.section-title {
    font-size: 1.4rem;
    font-weight: 700;
    margin-top: 24px;
    margin-bottom: 14px;
    color: #eef2ff;
}

/* KPI cards */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #192742, #151d32);
    border: 1px solid #354363;
    padding: 18px;
    border-radius: 16px;
    min-height: 112px;
    box-shadow: 0 5px 18px rgba(0, 0, 0, 0.12);
}

div[data-testid="stMetric"] [data-testid="stMetricLabel"],
div[data-testid="stMetric"] [data-testid="stMetricLabel"] p,
div[data-testid="stMetric"] [data-testid="stMetricLabel"] label {
    color: #e2e8f0 !important;
    -webkit-text-fill-color: #e2e8f0 !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}

div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 700 !important;
}

/* Chart containers */
div[data-testid="stPlotlyChart"] {
    background: #151f35;
    border: 1px solid #303d5a;
    border-radius: 14px;
    padding: 8px;
}

/* Tables */
div[data-testid="stDataFrame"] {
    border: 1px solid #303d5a;
    border-radius: 12px;
    overflow: hidden;
}

/* Expanders */
[data-testid="stExpander"] {
    background: #121c30;
    border: 1px solid #303d5a;
    border-radius: 12px;
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

/* Sidebar logout button */
[data-testid="stSidebar"] .stButton > button {
    background: #6d5ce8 !important;
    color: #ffffff !important;
    border: 1px solid #8b7cf6 !important;
}

hr {
    border-color: #303d5a;
}
</style>
""", unsafe_allow_html=True)


# ---------- DATA ----------
@st.cache_data
def load_data():
    data = pd.read_csv("retailpulse_cleaned.csv.gz")

    data["InvoiceDate"] = pd.to_datetime(
        data["InvoiceDate"],
        dayfirst=True,
        errors="coerce",
    )

    data["Sales"] = pd.to_numeric(
        data["Sales"], errors="coerce"
    )
    data["Quantity"] = pd.to_numeric(
        data["Quantity"], errors="coerce"
    )

    data = data.dropna(
        subset=["InvoiceDate", "Sales", "Quantity"]
    )

    return data


df = load_data()

# Exclude cancellation invoices from the main sales view.
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
    max_value=max_date,
)

countries = sorted(sales["Country"].dropna().unique())

selected_countries = st.sidebar.multiselect(
    "Countries",
    options=countries,
    default=[],
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


# ---------- DARK CHART THEME ----------
def style_dark_chart(fig, height=340):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Arial, sans-serif",
            color="#e2e8f0",
            size=12,
        ),
        height=height,
        margin=dict(l=20, r=20, t=25, b=35),
        hoverlabel=dict(
            bgcolor="#202d47",
            font_color="#ffffff",
            bordercolor="#526586",
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(color="#cbd5e1"),
        title_font=dict(color="#e2e8f0"),
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False,
        tickfont=dict(color="#cbd5e1"),
        title_font=dict(color="#e2e8f0"),
    )

    return fig


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


# ---------- SALES CHARTS ----------
st.markdown(
    '<div class="section-title">Sales Performance</div>',
    unsafe_allow_html=True,
)

left, right = st.columns([1.6, 1])

with left:
    monthly_sales = (
        filtered_sales
        .groupby(
            filtered_sales["InvoiceDate"].dt.to_period("M")
        )["Sales"]
        .sum()
        .rename_axis("Month")
        .reset_index()
    )

    monthly_sales["Month"] = (
        monthly_sales["Month"].astype(str)
    )

    st.markdown("#### Monthly Revenue Trend")

    if not monthly_sales.empty:
        fig_monthly = px.line(
            monthly_sales,
            x="Month",
            y="Sales",
            markers=True,
            labels={
                "Month": "Month",
                "Sales": "Revenue (£)",
            },
        )

        fig_monthly.update_traces(
            line=dict(color="#60a5fa", width=3),
            marker=dict(color="#a78bfa", size=6),
            hovertemplate=(
                "Month: %{x}<br>"
                "Revenue: £%{y:,.0f}"
                "<extra></extra>"
            ),
        )

        fig_monthly.update_layout(
            xaxis_tickangle=-35,
        )

        style_dark_chart(fig_monthly, height=360)

        st.plotly_chart(
            fig_monthly,
            use_container_width=True,
        )
    else:
        st.info("No sales data for the selected filters.")


with right:
    top_products = (
        filtered_sales.groupby("Description")["Sales"]
        .sum()
        .nlargest(8)
        .sort_values()
        .reset_index()
    )

    st.markdown("#### Top Products by Revenue")

    if not top_products.empty:
        fig_products = px.bar(
            top_products,
            x="Sales",
            y="Description",
            orientation="h",
            labels={
                "Sales": "Revenue (£)",
                "Description": "Product",
            },
        )

        fig_products.update_traces(
            marker_color="#818cf8",
            hovertemplate=(
                "%{y}<br>"
                "Revenue: £%{x:,.0f}"
                "<extra></extra>"
            ),
        )

        style_dark_chart(fig_products, height=360)

        st.plotly_chart(
            fig_products,
            use_container_width=True,
        )
    else:
        st.info("No product data available.")


# ---------- COUNTRY INSIGHTS ----------
st.markdown(
    '<div class="section-title">Geographic Performance</div>',
    unsafe_allow_html=True,
)

country_sales = (
    filtered_sales.groupby("Country")["Sales"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .sort_values()
    .reset_index()
)

if not country_sales.empty:
    fig_countries = px.bar(
        country_sales,
        x="Sales",
        y="Country",
        orientation="h",
        labels={
            "Sales": "Revenue (£)",
            "Country": "Country",
        },
    )

    fig_countries.update_traces(
        marker_color="#34d399",
        hovertemplate=(
            "%{y}<br>"
            "Revenue: £%{x:,.0f}"
            "<extra></extra>"
        ),
    )

    style_dark_chart(fig_countries, height=380)

    st.plotly_chart(
        fig_countries,
        use_container_width=True,
    )
else:
    st.info("No country data available for the selected filters.")


# ---------- DATA PREVIEW ----------
with st.expander("Explore filtered sales data"):
    st.dataframe(
        filtered_sales.head(500),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Showing up to 500 rows. Figures reflect the selected filters."
    )


# ---------- FOOTER ----------
st.caption(
    "RetailPulse | Historical retail analytics. "
    "Revenue and unit totals may include returns recorded on "
    "non-cancellation invoices."
)
