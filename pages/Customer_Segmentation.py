
import streamlit as st
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

st.set_page_config(
    page_title="Customer Segmentation | RetailPulse",
    page_icon="🎯",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020, #111a30, #17152d);
    color: #f1f5f9;
}
.block-container { padding-top: 2rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: #0a1020; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: #e2e8f0 !important; }
div[data-testid="stMetric"] {
    background: #151f35;
    border: 1px solid #303d5a;
    padding: 16px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_segments():
    return pd.read_csv("retailpulse_customer_segments.csv")


@st.cache_data
def run_kmeans(data, n_clusters):
    features = ["Recency", "Frequency", "Monetary"]
    X = data[features].copy()

    # Reduce the effect of very large monetary values
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

st.title("🎯 Customer Segmentation")
st.caption(
    "Understand customer groups using RFM analysis and machine learning."
)

# Existing rule-based segments
st.subheader("Existing RFM Segments")

if "Customer_Segment" in df.columns:
    segment_counts = (
        df["Customer_Segment"]
        .value_counts()
        .rename_axis("Segment")
        .reset_index(name="Customers")
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Identified Customers", f"{len(df):,}")
    c2.metric("RFM Segments", f"{df['Customer_Segment'].nunique()}")
    c3.metric(
        "Largest Segment",
        str(segment_counts.iloc[0]["Segment"])
        if not segment_counts.empty else "N/A"
    )

    st.bar_chart(segment_counts, x="Segment", y="Customers", height=320)

    with st.expander("View existing RFM customer data"):
        st.dataframe(df, use_container_width=True)

st.divider()

# Actual unsupervised ML clustering
st.subheader("🤖 Machine Learning: K-Means Clustering")
st.write(
    "K-Means groups customers with similar recency, purchase frequency, "
    "and monetary value. Cluster numbers are labels, not rankings."
)

if all(col in df.columns for col in ["Recency", "Frequency", "Monetary"]):
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

        if st.session_state.get("retailpulse_cluster_count") != n_clusters:
            st.info("Click Run Customer Clustering to apply the new cluster count.")
        else:
            cluster_counts = (
                clustered["ML_Cluster"]
                .value_counts()
                .sort_index()
                .rename_axis("ML Cluster")
                .reset_index(name="Customers")
            )

            st.markdown("#### ML Cluster Distribution")
            st.bar_chart(cluster_counts, x="ML Cluster", y="Customers")

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
            st.dataframe(profile, use_container_width=True)

            st.download_button(
                "Download ML cluster results",
                data=clustered.to_csv(index=False).encode("utf-8"),
                file_name="retailpulse_ml_clusters.csv",
                mime="text/csv"
            )
else:
    st.error(
        "The dataset needs Recency, Frequency, and Monetary columns "
        "before clustering can run."
    )

st.caption(
    "RFM segments above are rule-based. K-Means clusters are generated "
    "separately when you click Run Customer Clustering."
)
