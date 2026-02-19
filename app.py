import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- 1. USER PERMISSIONS DATABASE ---
# In a real app, this would be a secure database, but for your Streamlit setup,
# we can use a simple dictionary.
USERS = {
    "rich": {"password": "777", "role": "admin"},
    "staff": {"password": "123", "role": "team"}
}

def check_password():
    """Returns True if the user has a correct username and password."""
    def password_entered():
        user = st.session_state["username"]
        pwd = st.session_state["password_input"]
        if user in USERS and USERS[user]["password"] == pwd:
            st.session_state["password_correct"] = True
            st.session_state["user_role"] = USERS[user]["role"]
            del st.session_state["password_input"] # Clean up
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password_input")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password_input")
        st.error("😕 User not found or password incorrect")
        return False
    return True

# --- APP START ---
st.set_page_config(page_title="Corporate BI Hub", layout="wide")

if check_password():
    role = st.session_state["user_role"]
    st.sidebar.success(f"Logged in as: {role.upper()}")

    st.title("💎 Corporate BI & Strategy Hub")
    
    # --- ROLE-BASED SIDEBAR ---
    st.sidebar.header("📁 Data Controls")
    
    # Only Admins can upload new data or clean files
    if role == "admin":
        main_file = st.sidebar.file_uploader("Admin: Upload Master Data", type=['csv', 'xlsx'])
        if st.sidebar.button("🧼 Run Master Clean"):
            st.sidebar.warning("Cleaning system files...")
    else:
        st.sidebar.info("Standard View: Data is managed by Admin.")
        # For the demo, we use a sample if staff hasn't uploaded anything
        main_file = None 

    # --- APP TABS ---
    tab1, tab2 = st.tabs(["📊 Performance Dashboard", "📖 Data Dictionary"])

    with tab1:
        st.subheader("Team Results")
        # Logic for charts goes here...
        if role == "team":
            st.write("Welcome to your daily summary. Your view is optimized for sales tracking.")
            # You can hide sensitive columns like 'Profit Margin' or 'Cost' from the team view here
        
        if role == "admin":
            st.write("Full Executive Access: All financial columns are visible.")

    with tab2:
        # Only show the Data Dictionary to Admins to keep the staff view simple
        if role == "admin":
            st.subheader("Admin: Data Dictionary")
            st.write("Manage how your team interprets columns here.")
        else:
            st.warning("Access Denied: The Data Dictionary is for Admin eyes only.")

    if st.sidebar.button("Log Out"):
        st.session_state.clear()
        st.rerun()
