
import streamlit as st
import pandas as pd
import plotly.express as px
from auth import require_login

st.set_page_config(
    page_title="Business Insights | RetailPulse",
    page_icon="💡",
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

/* Headings and supporting text */
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

/* Dark chart containers */
div[data-testid="stPlotlyChart"] {
    background: #151f35 !important;
    border: 1px solid #303d5a;
    border-radius: 14px;
    padding: 8px;
}

/* Data table container */
div[data-testid="stDataFrame"] {
    background: #151f35 !important;
    border: 1px solid #303d5a;
    border-radius: 12px;
    overflow: hidden;
}

/* Expander */
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
    df = pd.read_csv("retailpulse_cleaned.csv.gz")

    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"],
        dayfirst=True
    )

    df["Sales"] = df["Quantity"] * df["Price"]

    return df


df = load_data()

sales = df[
    ~df["Invoice"].astype(str).str.startswith("C")
].copy()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("💡 Business Insights")
st.caption(
    "Discover useful patterns in historical retail performance."
)


# --------------------------------------------------
# DATE FILTER
# --------------------------------------------------

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
        filtered["InvoiceDate"].dt.date.between(
            start_date, end_date
        )
    ]

if filtered.empty:
    st.warning("No data found for this date range.")
    st.stop()


# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------

revenue = filtered["Sales"].sum()
orders = filtered["Invoice"].nunique()
products = filtered["Description"].nunique()
countries = filtered["Country"].nunique()

c1, c2, c3, c4 = st.columns(4)

c1.metric("💷 Net Revenue", f"£{revenue:,.0f}")
c2.metric("🧾 Orders", f"{orders:,}")
c3.metric("🏷️ Products", f"{products:,}")
c4.metric("🌍 Countries", f"{countries:,}")

st.divider()


# --------------------------------------------------
# CALCULATE INSIGHTS
# --------------------------------------------------

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
    filtered.groupby(
        filtered["InvoiceDate"].dt.to_period("M")
    )["Sales"]
    .sum()
    .rename_axis("Month")
    .reset_index()
)

monthly["Month"] = monthly["Month"].astype(str)


# --------------------------------------------------
# KEY FINDINGS
# --------------------------------------------------

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


# --------------------------------------------------
# DARK CHART THEME
# --------------------------------------------------

def style_dark_chart(fig, height=340):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", size=12),
        height=height,
        margin=dict(l=20, r=20, t=25, b=35),
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
# MONTHLY REVENUE & TOP COUNTRIES
# --------------------------------------------------

left, right = st.columns(2)

with left:
    st.subheader("📈 Monthly Revenue")

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
            marker=dict(color="#a78bfa", size=6),
            hovertemplate=(
                "Month: %{x}<br>"
                "Revenue: £%{y:,.0f}"
                "<extra></extra>"
            )
        )

        fig_monthly.update_layout(xaxis_tickangle=-35)
        style_dark_chart(fig_monthly)

        st.plotly_chart(
            fig_monthly,
            use_container_width=True
        )
    else:
        st.info("No monthly revenue data available.")

with right:
    st.subheader("🌍 Top Countries")

    top_countries = (
        country_summary.head(10)
        .sort_values()
        .rename_axis("Country")
        .reset_index(name="Sales")
    )

    if not top_countries.empty:
        fig_countries = px.bar(
            top_countries,
            x="Sales",
            y="Country",
            orientation="h",
            labels={
                "Sales": "Revenue (£)",
                "Country": "Country"
            }
        )

        fig_countries.update_traces(
            marker_color="#818cf8",
            hovertemplate=(
                "Country: %{y}<br>"
                "Revenue: £%{x:,.0f}"
                "<extra></extra>"
            )
        )

        style_dark_chart(fig_countries)

        st.plotly_chart(
            fig_countries,
            use_container_width=True
        )
    else:
        st.info("No country revenue data available.")


# --------------------------------------------------
# PRODUCTS NEEDING ATTENTION
# --------------------------------------------------

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



styled_table = (
    bottom_products.style
    .set_properties(**{
        "background-color": "#E2E8F0",
        "color": "#1E293B",
        "border-color": "#303D5A"
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

st.table(styled_table)


# --------------------------------------------------
# DOWNLOAD DATA
# --------------------------------------------------

st.download_button(
    "Download business insights data",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="retailpulse_business_insights.csv",
    mime="text/csv"
)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.caption(
    "Insights describe historical data; they are not causal conclusions "
    "or future predictions. Returns on non-cancellation invoices may "
    "affect net totals."
)
