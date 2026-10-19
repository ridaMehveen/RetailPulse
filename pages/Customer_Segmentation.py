
import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from auth import require_login


st.set_page_config(
    page_title="Customer Segmentation | RetailPulse",
    page_icon="🎯",
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
}

hr {
    border-color: #303d5a;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# CHART STYLING
# --------------------------------------------------

def style_dark_chart(fig, height=350):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", size=12),
        height=height,
        margin=dict(l=25, r=20, t=30, b=45),
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
def load_segments():
    return pd.read_csv("retailpulse_customer_segments.csv")


@st.cache_data
def run_kmeans(data, n_clusters):
    features = ["Recency", "Frequency", "Monetary"]
    X = data[features].copy()

    # Reduce the effect of unusually large monetary values
    X["Monetary"] = X["Monetary"].clip(
        lower=X["Monetary"].quantile(0.01),
        upper=X["Monetary"].quantile(0.99)
    )

    X = X.fillna(X.median())

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )

    labels = model.fit_predict(X_scaled)

    result = data.copy()
    result["ML_Cluster"] = labels.astype(str)

    return result


df = load_segments()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("🎯 Customer Segmentation")
st.caption(
    "Understand customer groups using RFM analysis and machine learning."
)


# --------------------------------------------------
# EXISTING RFM SEGMENTS
# --------------------------------------------------

st.subheader("📊 Existing RFM Segments")

if "Customer_Segment" in df.columns:

    segment_counts = (
        df["Customer_Segment"]
        .value_counts()
        .rename_axis("Segment")
        .reset_index(name="Customers")
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("👥 Identified Customers", f"{len(df):,}")

    c2.metric(
        "🎯 RFM Segments",
        f"{df['Customer_Segment'].nunique()}"
    )

    c3.metric(
        "🏆 Largest Segment",
        str(segment_counts.iloc[0]["Segment"])
        if not segment_counts.empty else "N/A"
    )

    fig_rfm = px.bar(
        segment_counts.sort_values("Customers"),
        x="Customers",
        y="Segment",
        orientation="h",
        labels={
            "Customers": "Number of Customers",
            "Segment": "Customer Segment"
        },
        color="Customers",
        color_continuous_scale=[
            "#3730a3",
            "#6366f1",
            "#a5b4fc"
        ]
    )

    fig_rfm.update_traces(
        hovertemplate=(
            "Segment: %{y}<br>"
            "Customers: %{x:,}"
            "<extra></extra>"
        )
    )

    fig_rfm.update_layout(
        coloraxis_showscale=False
    )

    style_dark_chart(fig_rfm, height=380)

    st.plotly_chart(
        fig_rfm,
        use_container_width=True
    )

    with st.expander("View existing RFM customer data"):
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

else:
    st.warning(
        "The dataset does not contain a Customer_Segment column."
    )


st.divider()


# --------------------------------------------------
# MACHINE LEARNING: K-MEANS
# --------------------------------------------------

st.subheader("🤖 Machine Learning: K-Means Clustering")

st.write(
    "K-Means groups customers with similar recency, purchase frequency, "
    "and monetary value. Cluster numbers are labels, not rankings."
)

required_columns = [
    "Recency",
    "Frequency",
    "Monetary",
    "Customer ID"
]

if all(col in df.columns for col in required_columns):

    n_clusters = st.slider(
        "Number of clusters",
        min_value=2,
        max_value=6,
        value=4
    )

    if st.button("Run Customer Clustering", type="primary"):

        with st.spinner("Grouping customers..."):
            clustered = run_kmeans(df, n_clusters)

        st.session_state["retailpulse_clustered"] = clustered
        st.session_state["retailpulse_cluster_count"] = n_clusters

    if "retailpulse_clustered" in st.session_state:

        clustered = st.session_state["retailpulse_clustered"]

        if (
            st.session_state.get("retailpulse_cluster_count")
            != n_clusters
        ):

            st.info(
                "Click **Run Customer Clustering** to apply "
                "the newly selected cluster count."
            )

        else:

            # Cluster distribution
            cluster_counts = (
                clustered["ML_Cluster"]
                .value_counts()
                .sort_index()
                .rename_axis("ML Cluster")
                .reset_index(name="Customers")
            )

            st.markdown("#### ML Cluster Distribution")

            fig_clusters = px.bar(
                cluster_counts,
                x="ML Cluster",
                y="Customers",
                color="ML Cluster",
                labels={
                    "ML Cluster": "Cluster",
                    "Customers": "Number of Customers"
                },
                color_discrete_sequence=[
                    "#818cf8",
                    "#34d399",
                    "#fbbf24",
                    "#f87171",
                    "#38bdf8",
                    "#c084fc"
                ]
            )

            fig_clusters.update_traces(
                hovertemplate=(
                    "Cluster: %{x}<br>"
                    "Customers: %{y:,}"
                    "<extra></extra>"
                )
            )

            fig_clusters.update_layout(
                showlegend=False
            )

            style_dark_chart(fig_clusters, height=350)

            st.plotly_chart(
                fig_clusters,
                use_container_width=True
            )

            # Cluster characteristics
            st.markdown("#### Cluster Characteristics")

            profile = (
                clustered.groupby("ML_Cluster")
                .agg(
                    Customers=("Customer ID", "count"),
                    Avg_Recency=("Recency", "mean"),
                    Avg_Frequency=("Frequency", "mean"),
                    Avg_Monetary=("Monetary", "mean")
                )
                .round(2)
                .reset_index()
            )

            st.dataframe(
                profile,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "Download ML Cluster Results",
                data=clustered.to_csv(index=False).encode("utf-8"),
                file_name="retailpulse_ml_clusters.csv",
                mime="text/csv"
            )

else:

    st.error(
        "The dataset needs Customer ID, Recency, Frequency, "
        "and Monetary columns before clustering can run."
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.caption(
    "RFM segments above are rule-based. K-Means clusters are generated "
    "separately when you click Run Customer Clustering."
)
