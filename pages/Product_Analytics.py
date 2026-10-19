
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from auth import require_login

st.set_page_config(
    page_title="Product Analytics | RetailPulse",
    page_icon="🛍️",
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

/* Chart containers */
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

/* Download button */
.stDownloadButton button {
    background: linear-gradient(90deg, #8b5cf6, #6d5ce8) !important;
    color: #ffffff !important;
    border: 1px solid #a78bfa !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    min-height: 44px;
}

.stDownloadButton button:hover {
    background: linear-gradient(90deg, #7c3aed, #5b4bd5) !important;
}

hr {
    border-color: #303d5a;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# DARK PLOTLY STYLE
# --------------------------------------------------

def style_dark_chart(fig, height=350):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", size=11),
        height=height,
        margin=dict(l=20, r=20, t=25, b=45),
        hoverlabel=dict(
            bgcolor="#202d47",
            font_color="#ffffff",
            bordercolor="#526586"
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0")
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

# Exclude cancellation invoices
sales = df[
    ~df["Invoice"].astype(str).str.startswith("C")
].copy()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("🛍️ Product Analytics")
st.caption(
    "Discover top products, sales patterns, and product performance."
)


# --------------------------------------------------
# FILTERS
# --------------------------------------------------

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
    products = sorted(
        sales["Description"].dropna().unique()
    )

    selected_products = st.multiselect(
        "Choose products (optional)",
        products,
        key="selected_products"
    )

filtered = sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered = filtered[
        filtered["InvoiceDate"].dt.date.between(
            start_date, end_date
        )
    ]

if selected_products:
    filtered = filtered[
        filtered["Description"].isin(selected_products)
    ]

if filtered.empty:
    st.warning("No product sales found for these filters.")
    st.stop()


# --------------------------------------------------
# PRODUCT SUMMARY & KPIs
# --------------------------------------------------

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

k1.metric("💷 Net Revenue", f"£{total_revenue:,.0f}")
k2.metric("📦 Net Units", f"{total_units:,.0f}")
k3.metric("🏷️ Products", f"{unique_products:,}")
k4.metric("🧾 Orders", f"{total_orders:,}")

st.divider()


# --------------------------------------------------
# TOP PRODUCTS BY REVENUE & UNITS
# --------------------------------------------------

left, right = st.columns(2)

with left:
    st.subheader("🏆 Top 10 Products by Revenue")

    top_revenue = (
        product_summary.nlargest(10, "Revenue")
        .sort_values("Revenue")
    )

    if not top_revenue.empty:
        fig_revenue = px.bar(
            top_revenue,
            x="Revenue",
            y="Description",
            orientation="h",
            labels={
                "Description": "Product",
                "Revenue": "Revenue (£)"
            }
        )

        fig_revenue.update_traces(
            marker_color="#818cf8",
            hovertemplate=(
                "Product: %{y}<br>"
                "Revenue: £%{x:,.2f}"
                "<extra></extra>"
            )
        )

        style_dark_chart(fig_revenue, height=400)

        st.plotly_chart(
            fig_revenue,
            use_container_width=True
        )
    else:
        st.info("No revenue data available.")

with right:
    st.subheader("📦 Top 10 Products by Units")

    top_units = (
        product_summary.nlargest(10, "Units")
        .sort_values("Units")
    )

    if not top_units.empty:
        fig_units = px.bar(
            top_units,
            x="Units",
            y="Description",
            orientation="h",
            labels={
                "Description": "Product",
                "Units": "Units sold"
            }
        )

        fig_units.update_traces(
            marker_color="#34d399",
            hovertemplate=(
                "Product: %{y}<br>"
                "Units: %{x:,.0f}"
                "<extra></extra>"
            )
        )

        style_dark_chart(fig_units, height=400)

        st.plotly_chart(
            fig_units,
            use_container_width=True
        )
    else:
        st.info("No unit data available.")

st.divider()


# --------------------------------------------------
# MONTHLY REVENUE FOR TOP PRODUCTS
# --------------------------------------------------

st.subheader("📈 Monthly Revenue for Top Products")

top_product_names = (
    product_summary.nlargest(5, "Revenue")["Description"].tolist()
)

monthly_data = filtered[
    filtered["Description"].isin(top_product_names)
].copy()

monthly_data["Month"] = (
    monthly_data["InvoiceDate"].dt.to_period("M").astype(str)
)

monthly_data = (
    monthly_data.groupby(["Month", "Description"])["Sales"]
    .sum()
    .reset_index()
)

if not monthly_data.empty:
    fig_monthly = px.line(
        monthly_data,
        x="Month",
        y="Sales",
        color="Description",
        markers=True,
        labels={
            "Month": "Month",
            "Sales": "Revenue (£)",
            "Description": "Product"
        }
    )

    fig_monthly.update_traces(
        line=dict(width=2.5),
        hovertemplate=(
            "Month: %{x}<br>"
            "Product: %{fullData.name}<br>"
            "Revenue: £%{y:,.2f}"
            "<extra></extra>"
        )
    )

    fig_monthly.update_layout(xaxis_tickangle=-35)
    style_dark_chart(fig_monthly, height=380)

    st.plotly_chart(
        fig_monthly,
        use_container_width=True
    )
else:
    st.info("No monthly revenue data available.")


# --------------------------------------------------
# PRODUCT PERFORMANCE TABLE
# --------------------------------------------------

styled_products = (
    product_summary.style
    .format({
        "Revenue": "£{:,.2f}",
        "Units": "{:,.0f}",
        "Orders": "{:,.0f}"
    })
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



# --------------------------------------------------
# CSV DOWNLOAD
# --------------------------------------------------

csv_data = product_summary.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download product analysis CSV",
    data=csv_data,
    file_name="retailpulse_product_analysis.csv",
    mime="text/csv",
    key="download_product_analysis",
    use_container_width=True
)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.caption(
    "Cancellation invoices are excluded. Returns on other invoices may "
    "affect net revenue and units."
)
