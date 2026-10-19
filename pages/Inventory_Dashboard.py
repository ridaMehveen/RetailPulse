
import streamlit as st
import pandas as pd
import plotly.express as px
from auth import require_login

st.set_page_config(
    page_title="RetailPulse - Inventory",
    page_icon="📦",
    layout="wide"
)

require_login()


# --------------------------------------------------
# DARK THEME
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(
        135deg, #0b1020 0%, #111a30 55%, #17152d 100%
    );
    color: #f1f5f9;
}

.block-container {
    padding-top: 2rem;
    max-width: 1600px;
}

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

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #192742, #151d32);
    border: 1px solid #354363;
    padding: 16px;
    border-radius: 14px;
    min-height: 110px;
}

div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] p {
    color: #e2e8f0 !important;
    -webkit-text-fill-color: #e2e8f0 !important;
}

div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 700 !important;
}

div[data-testid="stPlotlyChart"] {
    background: #151f35 !important;
    border: 1px solid #303d5a;
    border-radius: 14px;
    padding: 8px;
}

.stDownloadButton > button {
    background: #6d5ce8;
    color: #ffffff !important;
    border: 1px solid #8b7cf6;
    border-radius: 10px;
    font-weight: 600;
}

.stDownloadButton > button:hover {
    background: #5746d4;
    color: #ffffff !important;
}

hr {
    border-color: #303d5a;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# DARK CHART HELPER
# --------------------------------------------------

def style_dark_chart(fig, height=400):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", size=12),
        height=height,
        margin=dict(l=25, r=20, t=30, b=65),
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
        title_font=dict(color="#e2e8f0"),
        automargin=True
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False,
        tickfont=dict(color="#cbd5e1"),
        title_font=dict(color="#e2e8f0"),
        automargin=True
    )

    return fig


# --------------------------------------------------
# LOAD CLEANED RETAIL DATA
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


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("📦 Inventory & Demand Dashboard")
st.caption(
    "Product demand analysis and stock planning recommendations"
)


# --------------------------------------------------
# FILTERS
# --------------------------------------------------

sales = df[
    ~df["Invoice"].astype(str).str.startswith("C")
].copy()

st.sidebar.subheader("📅 Inventory Filters")

min_date = sales["InvoiceDate"].min().date()
max_date = sales["InvoiceDate"].max().date()

date_range = st.sidebar.date_input(
    "Analysis period",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="inventory_dates"
)

start_date, end_date = min_date, max_date

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    sales = sales[
        sales["InvoiceDate"].dt.date.between(
            start_date,
            end_date
        )
    ]

if sales.empty:
    st.warning("No sales data found for the selected dates.")
    st.stop()


# --------------------------------------------------
# PRODUCT-LEVEL DEMAND SUMMARY
# --------------------------------------------------

product_summary = (
    sales.groupby("Description")
    .agg(
        Units_Sold=("Quantity", "sum"),
        Revenue=("Sales", "sum"),
        Orders=("Invoice", "nunique")
    )
    .reset_index()
)

period_days = max((end_date - start_date).days + 1, 1)

product_summary["Avg_Daily_Demand"] = (
    product_summary["Units_Sold"] / period_days
)

product_summary["Suggested_7_Day_Demand"] = (
    product_summary["Avg_Daily_Demand"] * 7
).round().astype(int)


# --------------------------------------------------
# INVENTORY KPIs
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "📦 Products Analysed",
    f"{product_summary['Description'].nunique():,}"
)

col2.metric(
    "🛒 Net Units Sold",
    f"{product_summary['Units_Sold'].sum():,.0f}"
)

col3.metric(
    "📈 Products With Positive Demand",
    f"{(product_summary['Avg_Daily_Demand'] > 0).sum():,}"
)

st.divider()


# --------------------------------------------------
# HIGHEST-DEMAND PRODUCTS
# --------------------------------------------------

st.subheader("🔥 Products With Highest Recorded Demand")

top_demand = (
    product_summary
    .nlargest(10, "Avg_Daily_Demand")
    .sort_values("Avg_Daily_Demand")
)

fig_demand = px.bar(
    top_demand,
    x="Avg_Daily_Demand",
    y="Description",
    orientation="h",
    labels={
        "Avg_Daily_Demand": "Average Daily Demand (Units)",
        "Description": "Product"
    }
)

fig_demand.update_traces(
    marker_color="#818cf8",
    hovertemplate=(
        "Product: %{y}<br>"
        "Average daily demand: %{x:,.2f} units"
        "<extra></extra>"
    )
)

style_dark_chart(fig_demand, height=480)

st.plotly_chart(
    fig_demand,
    use_container_width=True
)


# --------------------------------------------------
# DEMAND-BASED PLANNING RECOMMENDATIONS
# --------------------------------------------------

st.subheader("📋 Demand-Based Planning Recommendations")

recommendations = product_summary.sort_values(
    "Avg_Daily_Demand",
    ascending=False
)


styled_recommendations = (
    recommendations[
        [
            "Description",
            "Units_Sold",
            "Avg_Daily_Demand",
            "Suggested_7_Day_Demand",
            "Revenue",
            "Orders"
        ]
    ].head(50).style
    .set_properties(**{
        "background-color": "#E2E8F0",
        "color": "#1E293B",
        "border-color": "#CBD5E1"
    })
    .set_table_styles([
        {
            "selector": "th",
            "props": [
                ("background-color", "#202D47"),
                ("color", "#FFFFFF"),
                ("border", "1px solid #303D5A"),
                ("font-weight", "600"),
                ("padding", "8px")
            ]
        },
        {
            "selector": "td",
            "props": [
                ("border", "1px solid #CBD5E1"),
                ("padding", "8px")
            ]
        },
        {
            "selector": "tbody tr:nth-child(even) td",
            "props": [
                ("background-color", "#F1F5F9")
            ]
        }
    ])
)


st.dataframe(
    styled_recommendations,
    use_container_width=True,
    hide_index=True
)


st.download_button(
    "Download Demand Planning Report",
    data=recommendations.to_csv(index=False).encode("utf-8"),
    file_name="retailpulse_demand_planning.csv",
    mime="text/csv"
)


# --------------------------------------------------
# INTERPRETATION NOTE
# --------------------------------------------------

st.info(
    "The 7-day figures are estimates based on average recorded daily quantity, "
    "not a validated forecast. Actual stock-on-hand, supplier lead time, "
    "safety stock and future forecasts are needed for true reorder recommendations. "
    "Returns and cancellations may also affect recorded quantities."
)
