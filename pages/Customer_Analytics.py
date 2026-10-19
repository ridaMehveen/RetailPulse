
import streamlit as st
import pandas as pd
import plotly.express as px
from auth import require_login

st.set_page_config(
    page_title="Customer Analytics | RetailPulse",
    page_icon="👥",
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

/* Plotly charts */
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
# DARK CHART THEME
# --------------------------------------------------

def style_dark_chart(fig, height=350):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", size=12),
        height=height,
        margin=dict(l=20, r=20, t=25, b=40),
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

# Customer analytics only uses identified customers
customer_sales = df.dropna(
    subset=["Customer ID"]
).copy()

# Exclude cancellation invoices from purchase activity
customer_sales = customer_sales[
    ~customer_sales["Invoice"].astype(str).str.startswith("C")
].copy()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("👥 Customer Analytics")
st.caption(
    "Understand customer value, purchasing frequency, "
    "and spending behaviour."
)


# --------------------------------------------------
# DATE FILTER
# --------------------------------------------------

min_date = customer_sales["InvoiceDate"].min().date()
max_date = customer_sales["InvoiceDate"].max().date()

date_range = st.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="customer_analytics_dates"
)

filtered = customer_sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered = filtered[
        filtered["InvoiceDate"].dt.date.between(
            start_date, end_date
        )
    ]

if filtered.empty:
    st.warning("No customer purchases found for this date range.")
    st.stop()


# --------------------------------------------------
# CUSTOMER SUMMARY & KPIs
# --------------------------------------------------

customer_summary = (
    filtered.groupby("Customer ID")
    .agg(
        Revenue=("Sales", "sum"),
        Orders=("Invoice", "nunique"),
        Units=("Quantity", "sum"),
        LastPurchase=("InvoiceDate", "max")
    )
    .reset_index()
)

total_customers = len(customer_summary)
total_revenue = filtered["Sales"].sum()
avg_spend = customer_summary["Revenue"].mean()
repeat_customers = (
    customer_summary["Orders"] >= 2
).sum()

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "👥 Identified Customers",
    f"{total_customers:,}"
)
c2.metric(
    "💷 Net Revenue",
    f"£{total_revenue:,.0f}"
)
c3.metric(
    "🛍️ Avg. Revenue per Customer",
    f"£{avg_spend:,.2f}"
)
c4.metric(
    "🔁 Repeat Buyers",
    f"{repeat_customers:,}"
)

st.divider()


# --------------------------------------------------
# TOP CUSTOMERS & PURCHASE FREQUENCY
# --------------------------------------------------

left, right = st.columns(2)

with left:
    st.subheader("🏆 Top 10 Customers by Revenue")

    top_customers = (
        customer_summary.nlargest(10, "Revenue")
        .sort_values("Revenue")
        .copy()
    )

    top_customers["Customer ID"] = (
        top_customers["Customer ID"].astype(str)
    )

    fig_customers = px.bar(
        top_customers,
        x="Revenue",
        y="Customer ID",
        orientation="h",
        labels={
            "Customer ID": "Customer ID",
            "Revenue": "Revenue (£)"
        }
    )

    fig_customers.update_traces(
        marker_color="#818cf8",
        hovertemplate=(
            "Customer: %{y}<br>"
            "Revenue: £%{x:,.2f}"
            "<extra></extra>"
        )
    )

    style_dark_chart(fig_customers, height=380)

    st.plotly_chart(
        fig_customers,
        use_container_width=True
    )


with right:
    st.subheader("🛍️ Purchase Frequency")

    order_distribution = (
        customer_summary["Orders"]
        .value_counts()
        .sort_index()
        .head(10)
        .rename_axis("Orders per Customer")
        .reset_index(name="Number of Customers")
    )

    fig_frequency = px.bar(
        order_distribution,
        x="Orders per Customer",
        y="Number of Customers",
        labels={
            "Orders per Customer": "Orders per Customer",
            "Number of Customers": "Number of Customers"
        }
    )

    fig_frequency.update_traces(
        marker_color="#34d399",
        hovertemplate=(
            "Orders per customer: %{x}<br>"
            "Customers: %{y:,}"
            "<extra></extra>"
        )
    )

    style_dark_chart(fig_frequency, height=380)

    st.plotly_chart(
        fig_frequency,
        use_container_width=True
    )


st.divider()


# --------------------------------------------------
# CUSTOMER SPENDING DISTRIBUTION
# --------------------------------------------------

st.subheader("💰 Customer Spending Distribution")

spending = customer_summary[
    ["Customer ID", "Revenue"]
].copy()

spending["Spending Band"] = pd.cut(
    spending["Revenue"],
    bins=[
        -float("inf"),
        0,
        100,
        500,
        1000,
        5000,
        float("inf")
    ],
    labels=[
        "Zero or Negative",
        "£0–£100",
        "£100–£500",
        "£500–£1,000",
        "£1,000–£5,000",
        "Above £5,000"
    ]
)

spending_counts = (
    spending["Spending Band"]
    .value_counts(sort=False)
    .rename_axis("Spending Band")
    .reset_index(name="Customers")
)

fig_spending = px.bar(
    spending_counts,
    x="Spending Band",
    y="Customers",
    labels={
        "Spending Band": "Spending Band",
        "Customers": "Number of Customers"
    }
)

fig_spending.update_traces(
    marker_color="#22d3ee",
    hovertemplate=(
        "Spending band: %{x}<br>"
        "Customers: %{y:,}"
        "<extra></extra>"
    )
)

style_dark_chart(fig_spending, height=350)

fig_spending.update_layout(
    xaxis_tickangle=-25
)

st.plotly_chart(
    fig_spending,
    use_container_width=True
)


# --------------------------------------------------
# CUSTOMER SUMMARY TABLE & DOWNLOAD
# --------------------------------------------------


with st.expander("View customer summary table"):
    sorted_customer_summary = customer_summary.sort_values(
        "Revenue",
        ascending=False
    )

    styled_customer_summary = (
        sorted_customer_summary.style
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
        styled_customer_summary,
        use_container_width=True,
        hide_index=True
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.caption(
    "Customer-level analysis excludes transactions without a Customer ID. "
    "Revenue may include returns recorded on non-cancellation invoices."
)
