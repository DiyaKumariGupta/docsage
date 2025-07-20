import streamlit as st
from supabase import create_client
import os

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def login_form():
    st.subheader("🔐 Login or Sign Up")

    # Toggle between login and signup
    mode = st.radio("Select mode", ["Login", "Sign Up"], horizontal=True)

    with st.form("auth_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button(mode)

    if submit:
        if not email or not password:
            st.warning("Please enter both email and password.")
            return

        try:
            if mode == "Login":
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                user = response.user
                if user:
                    st.success(f"Welcome {user.email}!")
                    st.session_state["user"] = {
                        "id": user.id,
                        "email": user.email
                    }
                    st.rerun()
                else:
                    st.error("Invalid login credentials.")

            elif mode == "Sign Up":
                response = supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                user = response.user
                if user:
                    st.success("Account created! Please check your email to confirm it.")
                else:
                    st.error("Signup failed.")

        except Exception as e:
            st.error(f"Auth error: {e}")
            print("DEBUG:", e)

def logout():
    if st.button("Logout"):
        session_keys_to_clear = ["user", "pdf_data", "chat_history", "vectors", "index"]
        for key in session_keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
