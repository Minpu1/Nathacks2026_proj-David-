"""
auth.py: simple login gate for the RA On-Shift Helper (Streamlit).

Test accounts only. No registration. Passwords are stored as SHA-256 hashes
so plain text passwords never sit in the logic below.

Usage in app.py (place near the top, right after st.set_page_config):

    from auth import require_login, show_user_sidebar

    user = require_login()          # blocks the page until login succeeds
    show_user_sidebar(user)         # shows name, role, and a logout button

    if user["role"] == "student":
        ...  # student report form
    elif user["role"] == "ra":
        ...  # RA dashboard
"""

import hashlib
import hmac

import streamlit as st


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# Test accounts. Swap for a real user store after the hackathon.
SAMPLE_ACCOUNTS = {
    "student1": {"password_hash": _hash("student123"), "role": "student", "name": "Alex Student"},
    "student2": {"password_hash": _hash("student456"), "role": "student", "name": "Sam Student"},
    "ra1": {"password_hash": _hash("ra12345"), "role": "ra", "name": "Jordan (RA)"},
    "ra2": {"password_hash": _hash("ra67890"), "role": "ra", "name": "Taylor (RA)"},
}


def authenticate(username: str, password: str):
    """Return the account dict (with username) on success, otherwise None."""
    account = SAMPLE_ACCOUNTS.get(username.strip().lower())
    if account is None:
        # Hash anyway so response time does not reveal valid usernames.
        _hash(password)
        return None
    if hmac.compare_digest(account["password_hash"], _hash(password)):
        return {
            "username": username.strip().lower(),
            "role": account["role"],
            "name": account["name"],
        }
    return None


def show_login():
    """Render the login form. Sets st.session_state['user'] on success."""
    st.markdown(
        """
        <style>
        .block-container { max-width: 440px; padding-top: 3rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("RA On-Shift Helper")
    st.caption("Sign in to continue.")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="e.g. student1")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if not username or not password:
            st.warning("Enter both a username and a password.")
        else:
            user = authenticate(username, password)
            if user:
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    with st.expander("Test accounts"):
        st.table(
            {
                "Username": ["student1", "student2", "ra1", "ra2"],
                "Password": ["student123", "student456", "ra12345", "ra67890"],
                "Role": ["Student", "Student", "RA", "RA"],
            }
        )


def require_login(allowed_roles=None):
    """
    Gate a page. Returns the logged-in user dict.
    Stops the script and shows the login form if nobody is signed in.
    Pass allowed_roles=["ra"] to restrict a page to certain roles.
    """
    user = st.session_state.get("user")

    if user is None:
        show_login()
        st.stop()

    if allowed_roles and user["role"] not in allowed_roles:
        st.error("Your account does not have access to this page.")
        show_user_sidebar(user)
        st.stop()

    return user


def show_user_sidebar(user):
    """Sidebar block with the signed-in name, role, and a logout button."""
    with st.sidebar:
        st.markdown(f"**{user['name']}**")
        st.caption(f"Role: {user['role'].upper()}")
        if st.button("Log out", use_container_width=True):
            st.session_state.pop("user", None)
            st.rerun()


def ra_dashboard():
    """Placeholder RA page until the dashboard is wired in."""
    st.title("RA Dashboard")
    st.info("RA view: the patrol dashboard goes here.")


def main():
    """
    Entry point: streamlit run auth.py
    Shows the login form first. After sign-in, students are sent to the
    student report page in student_app.py. RAs see the RA dashboard.
    """
    st.set_page_config(page_title="RA On-Shift Helper", page_icon="🏠")
    user = require_login()
    if user is None:
        # Happens when the file is run with plain python instead of streamlit.
        print("Run this with: streamlit run auth.py")
        return
    show_user_sidebar(user)

    if user["role"] == "student":
        pages = [st.Page("student_app.py", title="Report an Incident", icon="📝")]
    else:
        pages = [st.Page(ra_dashboard, title="RA Dashboard", icon="🗺️")]

    st.navigation(pages).run()


if __name__ == "__main__":
    main()
