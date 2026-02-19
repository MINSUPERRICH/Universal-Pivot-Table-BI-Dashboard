import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# --- 1. SESSION INITIALIZATION ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "rich": {"password": "777", "role": "admin"},
        "staff": {"password": "123", "role": "team"}
    }

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

# --- 2. THEME & STYLING ---
st.set_page_config(page_title="Executive BI Hub", layout="wide")
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-bottom: 4px solid #4eb8b8; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .dictionary-card { background-color: #f1f3f4; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #4eb8b8; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def check_password():
    def password_entered():
        user = st.session_state["username_input"]
        pwd = st.session_state["password_input"]
        db = st.session_state["user_db"]
        if user in db and db[user]["password"] == pwd:
            st.session_state["password_correct"] = True
            st.session_state["user_role"] = db[user]["role"]
            st.session_state["logged_in_user"] = user
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 Business Intelligence Login")
        st.text_input("Username", key="username_input")
        st.text_input("Password", type="password", on_change=password_entered, key="password_input")
        return False
    return True

def clean_my_data(df):
    df = df.drop_duplicates()
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if any(kw in col.lower() for kw in ['date', 'trans', 'posted']):
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

def generate_dictionary(df):
    dict_data = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        desc = "General Information"
        if "id" in col.lower(): desc = "Unique Identifier"
        elif any(w in col.lower() for w in ["sale", "price", "debit", "credit"]): desc = "Currency Value"
        elif "date" in col.lower(): desc = "Time Stamp"
        dict_data.append({"Column": col, "Type": dtype, "Description": desc})
    return pd.DataFrame(dict_data)

# --- 4. MAIN APP LOGIC ---

if check_password():
    role = st.session_state["user_role"]
    user = st.session_state["logged_in_user"]
    
    # Sidebar
    st.sidebar.title(f"Welcome, {user.title()}")
    st.sidebar.info(f"Access Level: {role.upper()}")
    
    # Tabs
    tab_dash, tab_dict, tab_settings = st.tabs(["📊 BI Dashboard", "📖 Data Dictionary", "⚙️ Account Settings"])

    # --- TAB 1: DASHBOARD ---
    with tab_dash:
        st.header("Your Data Insights")
        
        # Only Admins can upload
        uploaded_file = None
        if role == "admin":
            uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel", type=['csv', 'xlsx'])
        else:
            st.info("Standard Team View: Please wait for Admin to upload master data.")

        if uploaded_file:
            # Load Data
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            
            # Cleaning Button
            if role == "admin" and st.sidebar.button("🧼 Run One-Click Clean"):
                df = clean_my_data(df)
                st.sidebar.success("Data Cleaned!")

            # KPI Engine
            num_cols = df.select_dtypes(include='number').columns.tolist()
            if num_cols:
                st.sidebar.divider()
                selected_kpis = st.sidebar.multiselect("Select KPIs to Display", options=num_cols, default=num_cols[:1])
                agg = st.sidebar.selectbox("Calculation", ["sum", "mean", "count"])
                
                # Render Metrics
                cols = st.columns(len(selected_kpis) if selected_kpis else 1)
                for i, kpi in enumerate(selected_kpis):
                    val = df[kpi].agg(agg)
                    label = f"{agg.title()} of {kpi}"
                    if any(w in kpi.lower() for w in ['price', 'sale', 'debit', 'credit']):
                        cols[i].metric(label, f"${val:,.2f}")
                    else:
                        cols[i].metric(label, f"{val:,.0f}")

                # Charting
                st.divider()
                group_col = st.sidebar.selectbox("Group By (e.g., Category or Date)", df.columns)
                fig = px.bar(df.groupby(group_col)[selected_kpis[0]].agg(agg).reset_index(), 
                             x=group_col, y=selected_kpis[0], color_discrete_sequence=['#4eb8b8'], template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("🔍 View Raw Data Table"):
                st.dataframe(df, use_container_width=True)
        else:
            st.info("👋 Admin: Please upload a file in the sidebar to begin analysis.")

    # --- TAB 2: DICTIONARY ---
    with tab_dict:
        if role == "admin" and 'df' in locals():
            st.header("Admin: Auto Data Dictionary")
            data_dict = generate_dictionary(df)
            for _, row in data_dict.iterrows():
                st.markdown(f'<div class="dictionary-card"><strong>{row["Column"]}</strong> ({row["Type"]})<br><small>{row["Description"]}</small></div>', unsafe_allow_html=True)
        else:
            st.warning("Dictionary is available to Admin only after a file is uploaded.")

    # --- TAB 3: SETTINGS (Password Reset) ---
    with tab_settings:
        st.header("Account Security")
        st.subheader("Change Password")
        with st.form("pwd_form"):
            new_p = st.text_input("New Password", type="password")
            con_p = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Password"):
                if new_p == con_p and len(new_p) > 0:
                    st.session_state["user_db"][user]["password"] = new_p
                    st.success("✅ Password updated for this session!")
                else:
                    st.error("Passwords do not match or are empty.")

    if st.sidebar.button("Logout"):
        st.session_state["password_correct"] = False
        st.rerun()
