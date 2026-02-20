import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- 1. INITIALIZATION & SECURITY ---
# We define the users and functions FIRST to prevent NameError
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "rich": {"password": "777", "role": "admin"},
        "staff": {"password": "123", "role": "team"}
    }

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

st.set_page_config(page_title="Corporate BI Hub", layout="wide")

# --- 2. FUNCTION DEFINITIONS (Must be before main logic) ---

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

# --- 3. MAIN APP LOGIC ---

if check_password():
    role = st.session_state["user_role"]
    user = st.session_state["logged_in_user"]
    
    st.sidebar.title(f"Welcome, {user.title()}")
    
    # UPLOADER
    uploaded_file = st.sidebar.file_uploader("Upload File (Excel or CSV)", type=['csv', 'xlsx'])

    if uploaded_file:
        # Load Data
        file_ext = uploaded_file.name.split('.')[-1].lower()
        df = pd.read_csv(uploaded_file) if file_ext == 'csv' else pd.read_excel(uploaded_file)

        if not df.empty:
            # Admin Cleaning Tool
            if role == "admin" and st.sidebar.button("🧼 Run One-Click Clean"):
                df = clean_data(df)
                st.sidebar.success("Data Standardized!")

            # --- DYNAMIC CONTROLS ---
            st.sidebar.divider()
            st.sidebar.header("📊 Visualization Settings")
            chart_style = st.sidebar.radio("Select Chart Type", ["Bar Chart", "Line Graph", "Pie Chart (Round)"])
            
            num_cols = df.select_dtypes(include='number').columns.tolist()
            selected_kpis = st.sidebar.multiselect("Select KPIs", options=num_cols, default=num_cols[:1] if num_cols else None)
            group_by = st.sidebar.selectbox("Group By (Rows)", df.columns)

            # --- POWER BI FEATURE: RANKING ---
            st.sidebar.divider()
            st.sidebar.header("🏆 Ranking Filter")
            use_ranking = st.sidebar.toggle("Enable Top/Bottom Filter")
            
            if use_ranking:
                rank_type = st.sidebar.selectbox("Show", ["Top", "Bottom"])
                rank_limit = st.sidebar.slider("How many items?", 1, 20, 5)

            # --- TABS ---
            tab_dash, tab_pivot, tab_settings = st.tabs(["📈 Dashboard", "🧮 Pivot Table", "⚙️ Account Settings"])

            with tab_dash:
                st.header("Unified Data Analysis")
                
                # Prepare filtered/ranked data
                if selected_kpi := (selected_kpis[0] if selected_kpis else None):
                    chart_df = df.groupby(group_by)[selected_kpi].sum().reset_index()
                    
                    if use_ranking:
                        chart_df = chart_df.sort_values(by=selected_kpi, ascending=(rank_type == "Bottom")).head(rank_limit)
                    
                    # Metric Cards
                    k_cols = st.columns(len(selected_kpis))
                    for i, kpi in enumerate(selected_kpis):
                        total = chart_df[kpi].sum() if use_ranking else df[kpi].sum()
                        k_cols[i].metric(kpi, f"{total:,.2f}")

                    # Render Visuals
                    if chart_style == "Bar Chart":
                        fig = px.bar(chart_df, x=group_by, y=selected_kpi, color_discrete_sequence=['#4eb8b8'])
                    elif chart_style == "Line Graph":
                        fig = px.line(chart_df, x=group_by, y=selected_kpi, markers=True, color_discrete_sequence=['#4eb8b8'])
                    else:
                        fig = px.pie(chart_df, names=group_by, values=selected_kpi, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    
                    fig.update_layout(template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)

            with tab_pivot:
                st.subheader("Data Pivot Summary")
                if selected_kpis and group_by:
                    # Show ranked data if active, else full summary
                    pivot_data = chart_df.set_index(group_by) if use_ranking else df.groupby(group_by)[selected_kpis].sum()
                    st.dataframe(pivot_data, use_container_width=True)
                    st.download_button("📥 Download Pivot CSV", pivot_data.to_csv().encode('utf-8'), "pivot.csv")

            with tab_settings:
                st.subheader("Change Password")
                with st.form("pwd_form"):
                    new_p = st.text_input("New Password", type="password")
                    if st.form_submit_button("Update"):
                        st.session_state["user_db"][user]["password"] = new_p
                        st.success("Updated!")

    if st.sidebar.button("Logout"):
        st.session_state["password_correct"] = False
        st.rerun()
