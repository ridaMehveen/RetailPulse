
import streamlit as st
from auth import is_logged_in, require_login, show_login

st.set_page_config(
    page_title="RetailPulse | Retail Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Logged out: show only the login screen.
# Do not register dashboard pages until the user is logged in.
if not is_logged_in():
    show_login()
    st.stop()

# Logged in: register the existing homepage and dashboard pages.
pages = {
    "Workspace": [
        st.Page(
            "home_dashboard.py",
            title="Home",
            icon="🏠",
            default=True,
        ),
    ],
    "Analytics": [
        st.Page("pages/Executive_Dashboard.py", title="Executive Dashboard", icon="📊"),
        st.Page("pages/Business_Insights.py", title="Business Insights", icon="💡"),
        st.Page("pages/Sales_Analytics.py", title="Sales Analytics", icon="📈"),
        st.Page("pages/Product_Analytics.py", title="Product Analytics", icon="🛍️"),
        st.Page("pages/Customer_Analytics.py", title="Customer Analytics", icon="👥"),
        st.Page("pages/Customer_Dashboard.py", title="Customer Dashboard", icon="👤"),
        st.Page("pages/Customer_Segmentation.py", title="Customer Segmentation", icon="🎯"),
        st.Page("pages/Country_Analysis.py", title="Country Analysis", icon="🌍"),
        st.Page("pages/Inventory_Dashboard.py", title="Inventory Dashboard", icon="📦"),
        st.Page("pages/Forecast_Dashboard.py", title="Demand Forecast", icon="📈"),
        st.Page("pages/Model_Monitoring.py", title="Model Monitoring", icon="🩺"),
    ],
}

# Show account details and logout in the sidebar.
st.sidebar.caption(
    f"Signed in: {st.session_state.get('rp_user_email', 'User')}"
)

if st.sidebar.button("Log out", use_container_width=True):
    try:
        client = __import__("auth").get_supabase_client()
        client.auth.set_session(
            st.session_state.get("rp_access_token", ""),
            st.session_state.get("rp_refresh_token", ""),
        )
        client.auth.sign_out()
    except Exception:
        pass

    for key in ("rp_access_token", "rp_refresh_token", "rp_user_email"):
        st.session_state.pop(key, None)

    st.rerun()

navigation = st.navigation(pages)
navigation.run()
