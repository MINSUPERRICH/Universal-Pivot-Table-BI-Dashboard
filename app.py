import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# --- 1. INITIALIZATION & SECURITY ---
# We must define the user database and functions BEFORE calling them
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "rich": {"password": "777", "role": "admin"},
        "staff": {"password": "123", "role": "team"}
    }

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

st.set_page_config(page_title="Corporate BI Hub", layout="wide")

# Custom Styling for KPI Cards
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-bottom: 4px solid #4eb8b8; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DEFINE FUNCTIONS FIRST (Prevents NameError) ---

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

def clean_data(df):
    df = df.drop_duplicates()
    df.columns = df.columns.str.strip()
    return df

# --- 3. MAIN APP INTERFACE ---

if check_password(): # Now this will work because the function is defined above
    role = st.session_state["user_role"]
    user = st.session_state["logged_in_user"]
    
    st.sidebar.title(f"Welcome, {user.title()}")
    
    # UPLOADER (Supporting your JPG and Excel files)
    uploaded_file = st.sidebar.file_uploader("Upload File (Excel, CSV, JPG, PDF)", type=['csv', 'xlsx', 'jpg', 'jpeg', 'png', 'pdf'])

    if uploaded_file:
        # Load Data Logic
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext in ['csv', 'xlsx']:
            df = pd.read_csv(uploaded_file) if file_ext == 'csv' else pd.read_excel(uploaded_file)
        else:
            st.info("For Image/PDF files, please use the 'One-Click Clean' or OCR extraction setup.")
            df = pd.DataFrame() # Placeholder

        if not df.empty:
            # Cleaning
            if role == "admin" and st.sidebar.button("🧼 Run One-Click Clean"):
                df = clean_data(df)
                st.sidebar.success("Standardized!")

            # --- DYNAMIC CONTROLS ---
            st.sidebar.divider()
            st.sidebar.header("📊 Visualization Settings")
            
            # 1. Chart Type Selection (Requested: Round, Graph, Bar)
            chart_style = st.sidebar.radio("Select Chart Type", ["Bar Chart", "Line Graph", "Pie Chart (Round)"])
            
            # 2. KPI and Grouping Selection
            num_cols = df.select_dtypes(include='number').columns.tolist()
            selected_kpis = st.sidebar.multiselect("Select KPIs", options=num_cols, default=num_cols[:1])
            group_by = st.sidebar.selectbox("Group By (Rows)", df.columns)

            # --- TABS (Requested: Dedicated Pivot Tab) ---
            tab_visual, tab_pivot, tab_settings = st.tabs(["📈 Dashboard", "🧮 Pivot Table", "⚙️ Account Settings"])

            with tab_visual:
                st.subheader("Unified Data Analysis")
                
                # Render Metric Cards (Dynamic based on selected KPIs)
                k_cols = st.columns(len(selected_kpis) if selected_kpis else 1)
                for i, kpi in enumerate(selected_kpis):
                    total_val = df[kpi].sum()
                    k_cols[i].metric(kpi, f"{total_val:,.2f}")

                # Render Chart
                if selected_kpis and group_by:
                    chart_df = df.groupby(group_by)[selected_kpis[0]].sum().reset_index()
                    
                    if chart_style == "Bar Chart":
                        fig = px.bar(chart_df, x=group_by, y=selected_kpis[0], color_discrete_sequence=['#4eb8b8'])
                    elif chart_style == "Line Graph":
                        fig = px.line(chart_df, x=group_by, y=selected_kpis[0], markers=True, color_discrete_sequence=['#4eb8b8'])
                    else: # Pie Chart
                        fig = px.pie(chart_df, names=group_by, values=selected_kpis[0], hole=0.4, color_discrete_sequence=px.colors.qualitative.T10)
                    
                    fig.update_layout(template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)

            with tab_pivot:
                st.subheader("Data Pivot Summary")
                if selected_kpis and group_by:
                    # Create the Pivot View
                    pivot_view = df.groupby(group_by)[selected_kpis].sum()
                    st.dataframe(pivot_view, use_container_width=True)
                    
                    # Download button for just the pivot results
                    csv_pivot = pivot_view.to_csv().encode('utf-8')
                    st.download_button("📥 Download Pivot Results", data=csv_pivot, file_name="pivot_summary.csv")

            with tab_settings:
                st.header("Security")
                with st.form("reset_pwd"):
                    new_p = st.text_input("New Password", type="password")
                    if st.form_submit_button("Update Password"):
                        st.session_state["user_db"][user]["password"] = new_p
                        st.success("Password Updated!")

    else:
        st.info("👋 Admin, please upload a master file in the sidebar to begin.")

    if st.sidebar.button("Logout"):
        st.session_state["password_correct"] = False
        st.rerun()
