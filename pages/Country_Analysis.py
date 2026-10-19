
import streamlit as st
import pandas as pd
import plotly.express as px
from auth import require_login

st.set_page_config(
    page_title="Country Analysis | RetailPulse",
    page_icon="🌍",
    layout="wide"
)

require_login()


# --------------------------------------------------
# DARK THEME
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020, #111a30, #17152d);
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
[data-testid="stSidebar"] span {
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

div[data-testid="stDataFrame"] {
    background: #151f35 !important;
    border: 1px solid #303d5a;
    border-radius: 12px;
    overflow: hidden;
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

def style_dark_chart(fig, height=350):
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

# Exclude cancellation invoices from this sales view
sales = df[
    ~df["Invoice"].astype(str).str.startswith("C")
].copy()


# --------------------------------------------------
# PAGE HEADER AND DATE FILTER
# --------------------------------------------------

st.title("🌍 Country Analysis")
st.caption("Compare sales performance across countries.")

min_date = sales["InvoiceDate"].min().date()
max_date = sales["InvoiceDate"].max().date()

date_range = st.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="country_dates"
)

filtered = sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered = filtered[
        filtered["InvoiceDate"].dt.date.between(
            start_date,
            end_date
        )
    ]

if filtered.empty:
    st.warning("No sales data found for the selected dates.")
    st.stop()


# --------------------------------------------------
# COUNTRY SUMMARY AND KPIs
# --------------------------------------------------

country_summary = (
    filtered.groupby("Country")
    .agg(
        Revenue=("Sales", "sum"),
        Orders=("Invoice", "nunique"),
        Units=("Quantity", "sum"),
        Customers=("Customer ID", "nunique")
    )
    .reset_index()
    .sort_values("Revenue", ascending=False)
)

total_revenue = filtered["Sales"].sum()
country_count = filtered["Country"].nunique()
top_country = country_summary.iloc[0]["Country"]
total_orders = filtered["Invoice"].nunique()

c1, c2, c3, c4 = st.columns(4)

c1.metric("💷 Net Revenue", f"£{total_revenue:,.0f}")
c2.metric("🌍 Countries", f"{country_count:,}")
c3.metric("🏆 Top Country", str(top_country))
c4.metric("🧾 Orders", f"{total_orders:,}")

st.divider()


# --------------------------------------------------
# TOP 10 COUNTRIES BY REVENUE AND ORDERS
# --------------------------------------------------

left, right = st.columns(2)

with left:
    st.subheader("🏆 Top 10 Countries by Revenue")

    top_revenue = (
        country_summary
        .nlargest(10, "Revenue")
        .sort_values("Revenue")
    )

    fig_revenue = px.bar(
        top_revenue,
        x="Revenue",
        y="Country",
        orientation="h",
        labels={
            "Revenue": "Revenue (£)",
            "Country": "Country"
        }
    )

    fig_revenue.update_traces(
        marker_color="#818cf8",
        hovertemplate=(
            "Country: %{y}<br>"
            "Revenue: £%{x:,.2f}"
            "<extra></extra>"
        )
    )

    style_dark_chart(fig_revenue, height=400)

    st.plotly_chart(
        fig_revenue,
        use_container_width=True
    )


with right:
    st.subheader("🧾 Top 10 Countries by Orders")

    top_orders = (
        country_summary
        .nlargest(10, "Orders")
        .sort_values("Orders")
    )

    fig_orders = px.bar(
        top_orders,
        x="Orders",
        y="Country",
        orientation="h",
        labels={
            "Orders": "Number of Orders",
            "Country": "Country"
        }
    )

    fig_orders.update_traces(
        marker_color="#34d399",
        hovertemplate=(
            "Country: %{y}<br>"
            "Orders: %{x:,}"
            "<extra></extra>"
        )
    )

    style_dark_chart(fig_orders, height=400)

    st.plotly_chart(
        fig_orders,
        use_container_width=True
    )


# --------------------------------------------------
# UNITS SOLD BY COUNTRY
# --------------------------------------------------

st.divider()
st.subheader("📦 Units Sold by Country")

top_units = (
    country_summary
    .nlargest(10, "Units")
    .sort_values("Units")
)

fig_units = px.bar(
    top_units,
    x="Units",
    y="Country",
    orientation="h",
    labels={
        "Units": "Units Sold",
        "Country": "Country"
    }
)

fig_units.update_traces(
    marker_color="#38bdf8",
    hovertemplate=(
        "Country: %{y}<br>"
        "Units sold: %{x:,}"
        "<extra></extra>"
    )
)

style_dark_chart(fig_units, height=400)

st.plotly_chart(
    fig_units,
    use_container_width=True
)


# --------------------------------------------------
# COUNTRY PERFORMANCE TABLE
# --------------------------------------------------

st.subheader("📋 Country Performance Table")


st.dataframe(
    country_summary.style
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
                ("font-weight", "600")
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
    ]),
    use_container_width=True,
    hide_index=True
)


st.download_button(
    "Download Country Analysis CSV",
    data=country_summary.to_csv(
        index=False
    ).encode("utf-8"),
    file_name="retailpulse_country_analysis.csv",
    mime="text/csv"
)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.caption(
    "Customer counts include only identified customer IDs. "
    "Returns on non-cancellation invoices may affect net totals."
)
