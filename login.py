"""RA login for the RA On-Shift Helper.

Students report anonymously. Only the RA Dashboard requires a login.
Accounts are stored in a local SQLite file (users.db). RAs register with an
invite code shared by your team. Run on its own to test: streamlit run login.py
"""

import hashlib
import hmac
import os
import re
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone

import streamlit as st

DB_PATH = os.environ.get("RA_DB_PATH", "users.db")
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
PBKDF2_ROUNDS = 200_000
MIN_PASSWORD_LENGTH = 8
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")


# ---------- password hashing ----------

def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return hmac.compare_digest(candidate.hex(), hash_hex)


# ---------- storage ----------

def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   username TEXT PRIMARY KEY,
                   password_hash TEXT NOT NULL,
                   created_at TEXT NOT NULL
               )"""
        )


def _secrets_users() -> dict[str, str]:
    try:
        return dict(st.secrets["ra_users"])
    except (KeyError, FileNotFoundError):
        return {}


def get_hash(username: str) -> str | None:
    init_db()
    with closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ? COLLATE NOCASE",
            (username,),
        ).fetchone()
    if row:
        return row[0]
    return _secrets_users().get(username)


def user_count() -> int:
    init_db()
    with closing(sqlite3.connect(DB_PATH)) as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def create_user(username: str, password: str) -> str | None:
    """Return an error message, or None when the account is created."""
    if not USERNAME_PATTERN.match(username):
        return "Username must be 3 to 30 characters: letters, numbers, underscore."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if get_hash(username):
        return "That username is taken."
    init_db()
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, hash_password(password), datetime.now(timezone.utc).isoformat()),
        )
    return None


def change_password(username: str, old: str, new: str) -> str | None:
    stored = get_hash(username)
    if not stored or not verify_password(old, stored):
        return "Current password is incorrect."
    if len(new) < MIN_PASSWORD_LENGTH:
        return f"New password must be at least {MIN_PASSWORD_LENGTH} characters."
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        updated = conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ? COLLATE NOCASE",
            (hash_password(new), username),
        ).rowcount
    if not updated:
        return "Accounts defined in secrets.toml must be changed there."
    return None


def _invite_code() -> str | None:
    try:
        return st.secrets["ra_invite_code"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("RA_INVITE_CODE")


# ---------- session state ----------

def _init_state() -> None:
    st.session_state.setdefault("ra_authenticated", False)
    st.session_state.setdefault("ra_user", None)
    st.session_state.setdefault("failed_attempts", 0)
    st.session_state.setdefault("locked_until", 0.0)


def _record_failure() -> None:
    st.session_state["failed_attempts"] += 1
    if st.session_state["failed_attempts"] >= MAX_ATTEMPTS:
        st.session_state["locked_until"] = time.time() + LOCKOUT_SECONDS
        st.session_state["failed_attempts"] = 0


def _locked_message() -> str | None:
    remaining = st.session_state["locked_until"] - time.time()
    if remaining > 0:
        return f"Too many attempts. Try again in {int(remaining) + 1} seconds."
    return None


# ---------- UI ----------

def _sign_in_tab() -> None:
    message = _locked_message()
    if message:
        st.error(message)
        return
    with st.form("ra_login_form"):
        username = st.text_input("Username", autocomplete="username")
        password = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)
    if not submitted:
        return
    stored = get_hash(username.strip())
    # Hash against a dummy value for unknown users so timing stays similar.
    valid = verify_password(password, stored or hash_password("placeholder"))
    if stored and valid:
        st.session_state["ra_authenticated"] = True
        st.session_state["ra_user"] = username.strip()
        st.session_state["failed_attempts"] = 0
        st.rerun()
    _record_failure()
    st.error(_locked_message() or "Incorrect username or password.")


def _register_tab() -> None:
    code = _invite_code()
    if not code:
        st.info("Registration is closed. Ask your team lead to set an invite code.")
        return
    message = _locked_message()
    if message:
        st.error(message)
        return
    with st.form("ra_register_form"):
        invite = st.text_input("Invite code", type="password")
        username = st.text_input("Choose a username")
        password = st.text_input("Choose a password", type="password", autocomplete="new-password")
        confirm = st.text_input("Confirm password", type="password", autocomplete="new-password")
        submitted = st.form_submit_button("Create account", use_container_width=True)
    if not submitted:
        return
    if not hmac.compare_digest(invite.encode(), code.encode()):
        _record_failure()
        st.error(_locked_message() or "Invite code is incorrect.")
        return
    if password != confirm:
        st.error("Passwords do not match.")
        return
    error = create_user(username.strip(), password)
    if error:
        st.error(error)
    else:
        st.success("Account created. Open the Sign in tab to continue.")


def _sidebar() -> None:
    with st.sidebar:
        st.write(f"Signed in as {st.session_state['ra_user']}")
        with st.expander("Change password"):
            with st.form("ra_change_password"):
                old = st.text_input("Current password", type="password")
                new = st.text_input("New password", type="password")
                submitted = st.form_submit_button("Update")
            if submitted:
                error = change_password(st.session_state["ra_user"], old, new)
                st.error(error) if error else st.success("Password updated.")
        if st.button("Sign out", use_container_width=True):
            st.session_state["ra_authenticated"] = False
            st.session_state["ra_user"] = None
            st.rerun()


def require_ra_login() -> str:
    """Call at the top of the RA view. Stops the page until login succeeds."""
    _init_state()
    if not st.session_state["ra_authenticated"]:
        st.title("RA Sign In")
        st.caption("Residence Advisors only. Students do not need an account to report.")
        sign_in, register = st.tabs(["Sign in", "Register"])
        with sign_in:
            _sign_in_tab()
        with register:
            _register_tab()
        st.stop()
    _sidebar()
    return st.session_state["ra_user"]


if __name__ == "__main__":
    st.set_page_config(page_title="RA Sign In", layout="centered")
    user = require_ra_login()
    st.success(f"Welcome, {user}.")