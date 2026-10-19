
import streamlit as st
import pandas as pd
import plotly.express as px
from auth import require_login

st.set_page_config(
    page_title="RetailPulse - Customer Analytics",
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
    background: linear-gradient(135deg, #0b1020, #111a30, #17152d);
    color: #f1f5f9;
}

.block-container {
    padding: 2rem clamp(1rem, 2.5vw, 2rem);
    max-width: 1800px;
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

/* KPI cards */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #192742, #151d32);
    border: 1px solid #354363;
    padding: 16px;
    border-radius: 14px;
    min-height: 112px;
    box-shadow: 0 5px 18px rgba(0, 0, 0, 0.12);
}

div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] p,
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

div[data-testid="stMetricLabel"] p {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
}

div[data-testid="stMetricValue"] {
    font-weight: 700 !important;
}

/* Plotly charts */
div[data-testid="stPlotlyChart"] {
    background: #151f35 !important;
    border: 1px solid #303d5a;
    border-radius: 14px;
    padding: 8px;
}

/* Table containers */
div[data-testid="stDataFrame"],
div[data-testid="stTable"] {
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
# REUSABLE DARK CHART HELPER
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
# REUSABLE SOFT SLATE TABLE STYLING
# --------------------------------------------------

def style_customer_table(df):
    return (
        df.style
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
# LOAD CUSTOMER DATA
# --------------------------------------------------

@st.cache_data
def load_customers():
    return pd.read_csv("retailpulse_customer_churn.csv")


customers = load_customers()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("👥 Customer Analytics Dashboard")
st.caption("Customer behaviour and predicted churn risk")


# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------

total_customers = customers["Customer ID"].nunique()
high_risk = (customers["Churn_Probability"] >= 0.70).sum()
average_recency = customers["Recency"].mean()
average_spending = customers["Monetary"].mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric("👥 Identified Customers", f"{total_customers:,}")
col2.metric("⚠️ High-Risk Customers", f"{high_risk:,}")
col3.metric("📅 Average Recency", f"{average_recency:.0f} days")
col4.metric("💷 Average Customer Spending", f"£{average_spending:,.0f}")

st.divider()


# --------------------------------------------------
# CHURN RISK DISTRIBUTION
# --------------------------------------------------

st.subheader("📊 Customer Churn Risk Distribution")

risk_customers = customers.copy()

risk_customers["Risk Level"] = pd.cut(
    risk_customers["Churn_Probability"],
    bins=[-0.01, 0.30, 0.70, 1.00],
    labels=["Low Risk", "Medium Risk", "High Risk"]
)

risk_counts = (
    risk_customers["Risk Level"]
    .value_counts()
    .reindex(
        ["Low Risk", "Medium Risk", "High Risk"],
        fill_value=0
    )
    .rename_axis("Risk Level")
    .reset_index(name="Customers")
)

fig_risk = px.bar(
    risk_counts,
    x="Risk Level",
    y="Customers",
    color="Risk Level",
    color_discrete_map={
        "Low Risk": "#34d399",
        "Medium Risk": "#fbbf24",
        "High Risk": "#f87171"
    },
    category_orders={
        "Risk Level": ["Low Risk", "Medium Risk", "High Risk"]
    },
    labels={
        "Risk Level": "Churn Risk",
        "Customers": "Number of Customers"
    }
)

fig_risk.update_traces(
    hovertemplate=(
        "Risk level: %{x}<br>"
        "Customers: %{y:,}"
        "<extra></extra>"
    )
)

fig_risk.update_layout(showlegend=False)
style_dark_chart(fig_risk, height=350)

st.plotly_chart(fig_risk, use_container_width=True)


# --------------------------------------------------
# RFM CUSTOMER SEGMENTATION
# --------------------------------------------------

st.divider()
st.subheader("👥 RFM Customer Segmentation")


@st.cache_data
def load_segments():
    return pd.read_csv("retailpulse_customer_segments.csv")


segments_df = load_segments()

segment_counts = (
    segments_df["Customer_Segment"]
    .value_counts()
    .rename_axis("Customer Segment")
    .reset_index(name="Number of Customers")
)

col1, col2 = st.columns(2)

with col1:
    st.write("**Customers by Segment**")

    fig_segments = px.bar(
        segment_counts.sort_values("Number of Customers"),
        x="Number of Customers",
        y="Customer Segment",
        orientation="h",
        labels={
            "Number of Customers": "Number of Customers",
            "Customer Segment": "Customer Segment"
        }
    )

    fig_segments.update_traces(
        marker_color="#818cf8",
        hovertemplate=(
            "Segment: %{y}<br>"
            "Customers: %{x:,}"
            "<extra></extra>"
        )
    )

    style_dark_chart(fig_segments, height=380)

    st.plotly_chart(
        fig_segments,
        use_container_width=True
    )

with col2:
    st.write("**Segment Summary**")

    st.table(style_customer_table(segment_counts))


# --------------------------------------------------
# EXPLORE CUSTOMER SEGMENTS
# --------------------------------------------------

st.subheader("🔎 Explore Customer Segments")

segment_options = sorted(
    segments_df["Customer_Segment"].dropna().unique()
)

selected_segment = st.selectbox(
    "Choose a customer segment",
    ["All Segments"] + segment_options
)

if selected_segment == "All Segments":
    displayed_customers = segments_df
else:
    displayed_customers = segments_df[
        segments_df["Customer_Segment"] == selected_segment
    ]

st.write(f"Customers found: {len(displayed_customers):,}")

customer_columns = [
    "Customer ID",
    "Recency",
    "Frequency",
    "Monetary",
    "RFM_Score",
    "Customer_Segment"
]

styled_customers = style_customer_table(
    displayed_customers[customer_columns]
)

st.dataframe(
    styled_customers,
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download Selected Customer Segment",
    data=displayed_customers.to_csv(
        index=False
    ).encode("utf-8"),
    file_name="retailpulse_selected_customers.csv",
    mime="text/csv"
)


# --------------------------------------------------
# HIGHEST-RISK CUSTOMERS
# --------------------------------------------------

st.subheader("⚠️ Customers with Highest Predicted Churn Risk")

top_risk = customers.sort_values(
    "Churn_Probability",
    ascending=False
).head(20)

styled_top_risk = style_customer_table(top_risk)

st.dataframe(
    styled_top_risk,
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download Customer Risk Report",
    data=customers.to_csv(index=False).encode("utf-8"),
    file_name="retailpulse_customer_risk_report.csv",
    mime="text/csv"
)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.caption(
    "These are historical model predictions, not live customer churn estimates. "
    "High risk means predicted probability of 70% or more."
)
