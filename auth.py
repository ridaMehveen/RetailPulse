
import streamlit as st
from supabase import create_client


def get_supabase_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_PUBLISHABLE_KEY"],
    )


def show_login():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        .stApp {
            background:
                radial-gradient(ellipse at 15% 20%, #28205a 0%, transparent 42%),
                radial-gradient(ellipse at 85% 80%, #173c50 0%, transparent 38%),
                linear-gradient(135deg, #080d1b, #11172b 60%, #17122c);
            color: #f8fafc;
        }

        .block-container {
            max-width: 1100px;
            padding-top: 3rem;
        }

        .login-panel {
            background: rgba(20, 27, 50, 0.78);
            border: 1px solid rgba(167, 139, 250, 0.3);
            border-radius: 24px;
            padding: 24px;
            box-shadow: 0 20px 70px rgba(0, 0, 0, 0.3);
        }

        .brand {
            color: #c4b5fd;
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -1px;
        }

        .subtle {
            color: #a5b4cf;
        }

        [data-testid="stTextInput"] label,
        [data-testid="stTextInput"] label p {
            color: #e2e8f0 !important;
        }

        [data-testid="stTextInput"] input {
            color: #111827 !important;
            background: #f8fafc !important;
            border-radius: 10px !important;
        }

        [data-testid="stFormSubmitButton"] button {
            background: linear-gradient(90deg, #8b5cf6, #6d5ce8) !important;
            border: none !important;
            border-radius: 12px !important;
            min-height: 48px;
        }

        [data-testid="stFormSubmitButton"] button,
        [data-testid="stFormSubmitButton"] button p {
            color: #ffffff !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }

        [data-testid="stFormSubmitButton"] button:hover {
            background: linear-gradient(90deg, #7c3aed, #5b4bd5) !important;
        }
        /* Force the sidebar to stay hidden on the login screen */
body:has([data-testid="stForm"]) [data-testid="stSidebar"] {
    display: none !important;
}

/* Improve login button contrast */
[data-testid="stFormSubmitButton"] button {
    background: #7c3aed !important;
    color: #ffffff !important;
    opacity: 1 !important;
}

[data-testid="stFormSubmitButton"] button p {
    color: #ffffff !important;
    opacity: 1 !important;
}

/* Improve labels */
[data-testid="stTextInput"] label,
[data-testid="stTextInput"] label p {
    color: #f1f5f9 !important;
}
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.1, 1], gap="large")

    with left:
        st.markdown(
            '<div class="brand">✦ RetailPulse</div>',
            unsafe_allow_html=True,
        )
        st.markdown("### Intelligence behind every sale.")
        st.markdown(
            '<p class="subtle">Understand customers. Forecast demand. '
            'Make smarter inventory decisions.</p>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown("**CUSTOMER INTELLIGENCE**")
        st.markdown("RFM segmentation and churn insights")
        st.markdown("**DEMAND FORECASTING**")
        st.markdown("Compare forecasting models and historical trends")
        st.markdown("**INVENTORY OPTIMIZATION**")
        st.markdown("Turn sales signals into smarter decisions")

    with right:
        st.markdown(
            '<div class="login-panel">',
            unsafe_allow_html=True,
        )
        st.markdown("### Welcome back")
        st.caption("Sign in to access your retail intelligence workspace.")

        with st.form("retailpulse_login"):
            email = st.text_input("Email address")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Sign in",
                use_container_width=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        if submitted:
            if not email.strip() or not password:
                st.error("Enter your email and password.")
            else:
                try:
                    result = get_supabase_client().auth.sign_in_with_password(
                        {
                            "email": email.strip(),
                            "password": password,
                        }
                    )

                    if result.session and result.user:
                        st.session_state["rp_access_token"] = (
                            result.session.access_token
                        )
                        st.session_state["rp_refresh_token"] = (
                            result.session.refresh_token
                        )
                        st.session_state["rp_user_email"] = (
                            result.user.email or email.strip()
                        )
                        st.rerun()
                    else:
                        st.error("Sign-in was not completed. Try again.")

                except Exception:
                    st.error(
                        "Sign-in failed. Check your email, password, "
                        "and Supabase authentication settings."
                    )

        st.caption(
            "Need an account? Ask the RetailPulse administrator to "
            "create one for you."
        )



def require_login():
    if not st.session_state.get("rp_access_token"):
        show_login()
        st.stop()

def is_logged_in():
    return bool(st.session_state.get("rp_access_token"))