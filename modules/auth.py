import streamlit as st
from supabase import create_client
import os

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def login_form():
    st.subheader("Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if not email or not password:
            st.warning("Please enter both email and password.")
            return

        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            user = response.user
            if user:
                st.success(f"Welcome {user.email}!")
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("Login failed. Please check your credentials.")

        except Exception as e:
            st.error(f"Login error: {e}")
