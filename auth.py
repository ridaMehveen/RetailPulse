
import streamlit as st
from supabase import create_client
from urllib.parse import parse_qs
from streamlit_javascript import st_javascript


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
            color: #f1f5f9 !important;
        }

        [data-testid="stTextInput"] input {
            color: #111827 !important;
            background: #f8fafc !important;
            border-radius: 10px !important;
        }

        [data-testid="stFormSubmitButton"] button {
            background: #7c3aed !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 12px !important;
            min-height: 48px;
            opacity: 1 !important;
        }

        [data-testid="stFormSubmitButton"] button p {
            color: #ffffff !important;
            opacity: 1 !important;
            font-weight: 700 !important;
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
        st.markdown('<div class="login-panel">', unsafe_allow_html=True)
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

        with st.expander("Forgot your password?"):
            st.write(
                "Enter your account email and we'll send you a reset link."
            )

            with st.form("retailpulse_password_reset"):
                reset_email = st.text_input(
                    "Email address",
                    key="reset_email",
                ).strip()
                reset_submitted = st.form_submit_button(
                    "Send reset link",
                    use_container_width=True,
                )

            if reset_submitted:
                if not reset_email:
                    st.error("Enter your email address.")
                else:
                    try:
                        get_supabase_client().auth.reset_password_for_email(
                            reset_email,
                            {
                                "redirect_to": (
    "https://retailpulse-9xbtiqx3v8pkxfgalruqu8.streamlit.app/"
),
                            },
                        )
                        st.success(
                            "Reset request submitted. Check your inbox "
                            "and spam folder."
                        )
                    except Exception as e:
                        st.error(f"Reset request failed: {e}")

        st.caption(
            "Need an account? Ask the RetailPulse administrator to "
            "create one for you."
        )



def handle_password_recovery():
    if st.session_state.get("rp_recovery_mode"):
        return True

    fragment = st_javascript(
        "window.parent.location.hash",
        key="rp_recovery_fragment",
    )

    if not isinstance(fragment, str):
        return False

    fragment = fragment.strip()

    if not fragment.startswith("#"):
        return False

    params = parse_qs(fragment[1:])
    access_token = params.get("access_token", [None])[0]
    refresh_token = params.get("refresh_token", [None])[0]
    auth_type = params.get("type", [None])[0]

    if not access_token or not refresh_token:
        return False

    if auth_type != "recovery":
        return False

    try:
        client = get_supabase_client()
        client.auth.set_session(access_token, refresh_token)

        st.session_state["rp_recovery_mode"] = True
        st.session_state["rp_recovery_client"] = client
        st.rerun()
        return True

    except Exception:
        st.error(
            "This recovery link is invalid or expired. "
            "Please request a new one."
        )
        return True


def show_new_password_form():
    st.title("Create a new password")
    st.write("Choose a strong password for your RetailPulse account.")

    with st.form("rp_new_password_form"):
        new_password = st.text_input("New password", type="password")
        confirm_password = st.text_input(
            "Confirm new password",
            type="password",
        )
        submitted = st.form_submit_button(
            "Update password",
            use_container_width=True,
        )

    if submitted:
        if len(new_password) < 8:
            st.error("Your password must contain at least 8 characters.")
        elif new_password != confirm_password:
            st.error("The passwords don't match.")
        else:
            try:
                client = st.session_state["rp_recovery_client"]
                client.auth.update_user({"password": new_password})

                for key in (
                    "rp_recovery_mode",
                    "rp_recovery_client",
                    "rp_access_token",
                    "rp_refresh_token",
                    "rp_user_email",
                ):
                    st.session_state.pop(key, None)

                st.success("Password updated! You can now sign in.")
                st.rerun()

            except Exception as e:
                st.error(f"Password update failed: {e}")

 
def require_login():
    if not st.session_state.get("rp_access_token"):
        show_login()
        st.stop()


def is_logged_in():
    return bool(st.session_state.get("rp_access_token"))
