import streamlit as st
import pandas as pd
import plotly.express as px
from auth import require_login


st.set_page_config(
    page_title="Executive Dashboard | RetailPulse",
    page_icon="📊",
    layout="wide"
)

require_login()

# --------------------------------------------------
# THEME & STYLING
# --------------------------------------------------

st.markdown("""
<style>
/* Main background */
.stApp {
    background: linear-gradient(
        135deg,
        #0b1020 0%,
        #111a30 55%,
        #17152d 100%
    );
    color: #f1f5f9;
}

.block-container {
    padding: 1.5rem clamp(1rem, 3vw, 2.5rem) 2rem;
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

/* Headings */
h1, h2, h3, h4 {
    color: #f1f5f9 !important;
}

[data-testid="stCaptionContainer"] {
    color: #b8c5df !important;
}

/* Widget labels */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stDateInput"] label,
[data-testid="stMultiSelect"] label {
    color: #dbe5f7 !important;
}

/* Inputs */
[data-baseweb="select"] {
    border-radius: 9px;
}

[data-testid="stDateInput"] input {
    color: #f1f5f9 !important;
}

/* KPI cards */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #192742, #131d32);
    border: 1px solid #354363;
    border-radius: 14px;
    padding: 14px 12px;
    min-height: 118px;
    box-shadow: 0 5px 18px rgba(0, 0, 0, 0.16);
    overflow-wrap: anywhere;
}



div[data-testid="stMetric"] [data-testid="stMetricLabel"],
div[data-testid="stMetric"] [data-testid="stMetricLabel"] p,
div[data-testid="stMetric"] [data-testid="stMetricLabel"] label {
    color: #e2e8f0 !important;
    -webkit-text-fill-color: #e2e8f0 !important;
    opacity: 1 !important;
    font-weight: 600 !important;
}


div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] div {
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: clamp(1rem, 1.35vw, 1.65rem) !important;
    line-height: 1.3 !important;
    overflow-wrap: anywhere;
}

/* Keep KPI column contents inside their columns */
[data-testid="stHorizontalBlock"] {
    gap: 0.8rem;
}

[data-testid="column"] {
    min-width: 0 !important;
}

/* Chart containers */
[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"],
[data-testid="stPlotlyChart"],
[data-testid="stLineChart"],
[data-testid="stBarChart"] {
    background: #151f35;
    border: 1px solid #303d5a;
    border-radius: 14px;
    padding: 8px;
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

/* Data table */
div[data-testid="stDataFrame"] {
    border: 1px solid #303d5a;
    border-radius: 12px;
    overflow: hidden;
}

/* Expander and divider */
[data-testid="stExpander"] {
    border: 1px solid #303d5a;
    border-radius: 12px;
}

hr {
    border-color: #303d5a;
}

/* Small-screen spacing */
@media (max-width: 900px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    div[data-testid="stMetric"] {
        padding: 10px 8px;
        min-height: 105px;
    }
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("retailpulse_cleaned.csv.gz")
    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"],
        dayfirst=True
    )
    df["Sales"] = df["Quantity"] * df["Price"]
    return df


df = load_data()

# Exclude cancellation invoices
sales = df[
    ~df["Invoice"].astype(str).str.startswith("C")
].copy()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("📊 Executive Dashboard")
st.caption(
    "A high-level view of retail business performance."
)


# --------------------------------------------------
# FILTERS
# --------------------------------------------------

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
    countries = sorted(
        sales["Country"].dropna().unique()
    )

    selected_countries = st.multiselect(
        "Countries",
        countries,
        key="exec_countries"
    )


# Apply filters
filtered = sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered = filtered[
        filtered["InvoiceDate"].dt.date.between(
            start_date,
            end_date
        )
    ]

if selected_countries:
    filtered = filtered[
        filtered["Country"].isin(selected_countries)
    ]


# --------------------------------------------------
# KEY PERFORMANCE INDICATORS
# --------------------------------------------------

revenue = filtered["Sales"].sum()
orders = filtered["Invoice"].nunique()
units = filtered["Quantity"].sum()
customers = filtered["Customer ID"].nunique()
products = filtered["Description"].nunique()

st.subheader("📌 Key Performance Indicators")

# Two rows avoid squeezing five cards into narrow columns.
row1 = st.columns(3)
row2 = st.columns(2)

kpi_values = [
    ("💷 Net Revenue", f"£{revenue:,.0f}"),
    ("🧾 Orders", f"{orders:,}"),
    ("📦 Net Units", f"{units:,.0f}"),
    ("👥 Identified Customers", f"{customers:,}"),
    ("🏷️ Products", f"{products:,}")
]

for col, (label, value) in zip(row1, kpi_values[:3]):
    with col:
        st.metric(label, value)

for col, (label, value) in zip(row2, kpi_values[3:]):
    with col:
        st.metric(label, value)


st.divider()


# --------------------------------------------------
# MONTHLY REVENUE & COUNTRY PERFORMANCE
# --------------------------------------------------

def apply_dark_chart(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        margin=dict(l=20, r=20, t=25, b=20),
        legend=dict(
            font=dict(color="#e2e8f0")
        )
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(color="#cbd5e1"),
        title_font=dict(color="#cbd5e1")
    )

    fig.update_yaxes(
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False,
        tickfont=dict(color="#cbd5e1"),
        title_font=dict(color="#cbd5e1")
    )

    return fig


left, right = st.columns([1.5, 1])

with left:
    st.subheader("📈 Monthly Revenue")

    monthly = (
        filtered.groupby(
            filtered["InvoiceDate"].dt.to_period("M")
        )["Sales"]
        .sum()
        .rename_axis("Month")
        .reset_index()
    )

    monthly["Month"] = monthly["Month"].astype(str)

    if not monthly.empty:
        fig_monthly = px.line(
            monthly,
            x="Month",
            y="Sales",
            markers=True,
            labels={
                "Month": "Month",
                "Sales": "Revenue (£)"
            }
        )

        fig_monthly.update_traces(
            line=dict(color="#60a5fa", width=3),
            marker=dict(size=6, color="#a78bfa")
        )

        fig_monthly.update_layout(
            height=350,
            xaxis_tickangle=-45
        )

        apply_dark_chart(fig_monthly)

        st.plotly_chart(
            fig_monthly,
            use_container_width=True
        )
    else:
        st.info("No data available for these filters.")


with right:
    st.subheader("🌍 Top Countries")

    country_sales = (
        filtered.groupby("Country")["Sales"]
        .sum()
        .nlargest(8)
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
                "Country": "Country"
            }
        )

        fig_countries.update_traces(
            marker_color="#818cf8"
        )

        fig_countries.update_layout(height=350)

        apply_dark_chart(fig_countries)

        st.plotly_chart(
            fig_countries,
            use_container_width=True
        )
    else:
        st.info("No country data available for these filters.")


st.divider()




# --------------------------------------------------
# PRODUCT PERFORMANCE
# --------------------------------------------------

st.subheader("🏆 Top 10 Products by Revenue")

top_products = (
    filtered.groupby("Description")["Sales"]
    .sum()
    .nlargest(10)
    .sort_values()
    .reset_index()
)

if not top_products.empty:
    fig_products = px.bar(
        top_products,
        x="Sales",
        y="Description",
        orientation="h",
        labels={
            "Sales": "Revenue (£)",
            "Description": "Product"
        }
    )

    fig_products.update_traces(
        marker_color="#34d399"
    )

    fig_products.update_layout(height=420)

    apply_dark_chart(fig_products)

    st.plotly_chart(
        fig_products,
        use_container_width=True
    )
else:
    st.info("No products found for the selected filters.")


# --------------------------------------------------
# DATA SUMMARY
# --------------------------------------------------

with st.expander("📋 View Executive Data Summary"):
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

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.caption(
    "Historical data. Customer counts include only records "
    "with identified customer IDs. Returns on non-cancellation "
    "invoices may affect net totals."
)
