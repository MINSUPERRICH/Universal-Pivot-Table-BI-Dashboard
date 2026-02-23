import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- 1. INITIALIZATION & SECURITY ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "rich": {"password": "777", "role": "admin"},
        "staff": {"password": "123", "role": "team"}
    }

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

st.set_page_config(page_title="Corporate BI Hub", layout="wide")

# --- 2. FUNCTION DEFINITIONS ---

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

# --- 3. MAIN APP LOGIC ---

if check_password():
    role = st.session_state["user_role"]
    user = st.session_state["logged_in_user"]
    
    st.sidebar.title(f"Welcome, {user.title()}")
    
    # TWO UPLOADERS FOR VLOOKUP
    st.sidebar.header("📁 Data Sources")
    main_file = st.sidebar.file_uploader("1. Main Sales File", type=['csv', 'xlsx'])
    lookup_file = st.sidebar.file_uploader("2. Lookup/Price List (Optional)", type=['csv', 'xlsx'])

    if main_file:
        df_main = pd.read_csv(main_file) if main_file.name.endswith('.csv') else pd.read_excel(main_file)
        
        # TAB SETUP
        tab_dash, tab_pivot, tab_vlookup, tab_settings = st.tabs([
            "📈 Dashboard", "🧮 Pivot Table", "🔗 Link & Match (VLOOKUP)", "⚙️ Settings"
        ])

        # --- NEW TAB: VLOOKUP / LINKING ---
        with tab_vlookup:
            st.header("VLOOKUP Engine")
            if lookup_file:
                df_lookup = pd.read_csv(lookup_file) if lookup_file.name.endswith('.csv') else pd.read_excel(lookup_file)
                
                st.subheader("Match Directions")
                col1, col2 = st.columns(2)
                
                with col1:
                    main_key = st.selectbox("Key Column in Main File", df_main.columns)
                with col2:
                    lookup_key = st.selectbox("Key Column in Lookup File", df_lookup.columns)
                
                if st.button("🔗 Execute Match (VLOOKUP)"):
                    # This performs a 'Left Join' - finding all matches from the lookup file
                    df_merged = pd.merge(df_main, df_lookup, left_on=main_key, right_on=lookup_key, how='left')
                    st.session_state['df_main'] = df_merged
                    st.success("Matching Complete! Your Dashboard and Pivot Table are now updated with the new data.")
                    st.dataframe(df_merged.head(10))
            else:
                st.info("To use VLOOKUP, please upload a second 'Lookup' file in the sidebar.")

        # --- REST OF APP LOGIC ---
        # (Use st.session_state['df_main'] for calculations)
        working_df = st.session_state.get('df_main', df_main)

        with tab_dash:
            # (Insert your Dashboard/Chart logic here using working_df)
            st.header("Unified Data Analysis")
            num_cols = working_df.select_dtypes(include='number').columns.tolist()
            if num_cols:
                selected_kpi = st.sidebar.multiselect("Select KPIs", num_cols, default=num_cols[:1])
                group_by = st.sidebar.selectbox("Group By", working_df.columns)
                
                # Dynamic Bar Chart
                fig = px.bar(working_df.groupby(group_by)[selected_kpi[0]].sum().reset_index(), 
                             x=group_by, y=selected_kpi[0], color_discrete_sequence=['#4eb8b8'], template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        with tab_pivot:
            st.subheader("Data Pivot Summary")
            st.dataframe(working_df.pivot_table(index=group_by, values=selected_kpi, aggfunc='sum'))

    if st.sidebar.button("Logout"):
        st.session_state["password_correct"] = False
        st.rerun()
