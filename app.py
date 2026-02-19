import streamlit as st
import pandas as pd

# --- 1. USER DATABASE INITIALIZATION ---
# We use session_state to store the "live" password list so it can be changed
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "rich": {"password": "777", "role": "admin"},
        "staff": {"password": "123", "role": "team"}
    }

def check_password():
    def password_entered():
        user = st.session_state["username"]
        pwd = st.session_state["password_input"]
        db = st.session_state["user_db"]
        
        if user in db and db[user]["password"] == pwd:
            st.session_state["password_correct"] = True
            st.session_state["user_role"] = db[user]["role"]
            st.session_state["logged_in_user"] = user
            del st.session_state["password_input"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Business Intelligence Login")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password_input")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password_input")
        st.error("😕 Access Denied: Check username or password")
        return False
    return True

# --- 2. MAIN APP ---
if check_password():
    role = st.session_state["user_role"]
    current_user = st.session_state["logged_in_user"]
    
    st.sidebar.title(f"Welcome, {current_user.title()}")
    st.sidebar.info(f"Access Level: {role.upper()}")

    # Add a new tab specifically for Security/Settings
    tab_dash, tab_settings = st.tabs(["📊 BI Dashboard", "⚙️ Account Settings"])

    with tab_dash:
        st.header("Your Data Insights")
        st.write("Upload and analyze your files here as we set up before.")
        # [Insert previous dashboard/cleaning/pivot logic here]

    with tab_settings:
        st.header("Security Center")
        st.subheader("Change Your Password")
        
        with st.form("password_change_form"):
            new_pwd = st.text_input("New Password", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            submit_change = st.form_submit_button("Update Password")
            
            if submit_change:
                if new_pwd == confirm_pwd and len(new_pwd) > 0:
                    # Update the live database in session state
                    st.session_state["user_db"][current_user]["password"] = new_pwd
                    st.success("✅ Password updated successfully! It will be active until the session ends.")
                elif new_pwd != confirm_pwd:
                    st.error("❌ Passwords do not match.")
                else:
                    st.error("❌ Password cannot be empty.")

    # Log out button at the bottom of the sidebar
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
