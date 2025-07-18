import streamlit as st
from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def login_form():
    with st.sidebar:
        st.markdown("### Optional Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            try:
                user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state["user"] = user
                st.success("Logged in successfully!")
            except Exception as e:
                st.error("Login failed. Check your credentials.")

        if st.button("Logout"):
            st.session_state["user"] = None
            st.success("Logged out.")

def is_authenticated():
    return st.session_state.get("user", None) is not None
