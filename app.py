import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# --- 1. CONFIGURATION & PERMISSIONS ---
st.set_page_config(page_title="AI-BI Command Center", layout="wide")

# User Database
USERS = {
    "rich": {"password": "777", "role": "admin"},
    "staff": {"password": "123", "role": "team"}
}

# --- 2. DEFINE FUNCTIONS FIRST (To avoid NameError) ---

def check_password():
    """Returns True if the user has a correct username and password."""
    def password_entered():
        user = st.session_state["username"]
        pwd = st.session_state["password_input"]
        if user in USERS and USERS[user]["password"] == pwd:
            st.session_state["password_correct"] = True
            st.session_state["user_role"] = USERS[user]["role"]
            del st.session_state["password_input"] 
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

def clean_my_data(df):
    """Basic data cleaning engine."""
    df = df.drop_duplicates()
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['date', 'trans', 'posted']):
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

# --- 3. MAIN APP LOGIC ---

if check_password():
    role = st.session_state["user_role"]
    st.sidebar.success(f"Logged in as: {role.upper()}")
    st.title("💎 Dynamic BI Command Center")
    
    # File Upload (Admin Only)
    if role == "admin":
        uploaded_file = st.sidebar.file_uploader("Upload Data File", type=['csv', 'xlsx'])
    else:
        st.sidebar.info("Standard View: Data is managed by Admin.")
        uploaded_file = None

    if uploaded_file:
        # Load Data
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        # Cleaning Toggle
        if role == "admin" and st.sidebar.button("🧼 Run One-Click Clean"):
            df = clean_my_data(df)
            st.sidebar.success("Data Cleaned!")

        # Dynamic KPI Logic
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols:
            st.sidebar.divider()
            selected_kpis = st.sidebar.multiselect("Select KPIs", options=numeric_cols, default=numeric_cols[:1])
            agg_method = st.sidebar.selectbox("Calculation Method", ["sum", "mean", "count"])

            # Render KPI Cards
            st.subheader("📌 Current Performance")
            kpi_cols = st.columns(len(selected_kpis) if selected_kpis else 1)
            for i, kpi in enumerate(selected_kpis):
                val = df[kpi].agg(agg_method)
                label = f"{agg_method.title()} {kpi}"
                if any(word in kpi.lower() for word in ['price', 'sale', 'cost']):
                    kpi_cols[i].metric(label, f"${val:,.2f}")
                else:
                    kpi_cols[i].metric(label, f"{val:,.0f}")

            # Dynamic Charting
            st.divider()
            group_col = st.sidebar.selectbox("Breakdown By", df.columns)
            fig = px.bar(df.groupby(group_col)[selected_kpis[0]].agg(agg_method).reset_index(), 
                         x=group_col, y=selected_kpis[0], color_discrete_sequence=['#4eb8b8'], template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("🔍 Preview Data"):
            st.write(df.head(20))
            
    else:
        st.info("👋 Admin, please upload a file to begin.")

    if st.sidebar.button("Log Out"):
        st.session_state.clear()
        st.rerun()
