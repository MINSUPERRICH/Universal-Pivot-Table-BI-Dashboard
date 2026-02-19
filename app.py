import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# --- SETUP ---
st.set_page_config(page_title="AI-BI Command Center", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-bottom: 4px solid #4eb8b8; }
    .dictionary-card { background-color: #f1f3f4; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #4eb8b8; }
    </style>
    """, unsafe_allow_html=True)

# 1. Password Protection
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == "rich"}), key="password")
        return False
    return st.session_state["password_correct"]

# 2. Data Cleaning Function
def clean_my_data(df):
    df = df.drop_duplicates()
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['date', 'trans', 'posted']):
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

# 3. Data Dictionary Logic
def generate_dictionary(df):
    dict_data = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        # Simple AI-style logic to guess description
        desc = "General Information"
        if "id" in col.lower(): desc = "Unique Identifier for the record"
        elif "sale" in col.lower() or "price" in col.lower(): desc = "Financial value in currency"
        elif "date" in col.lower(): desc = "Time-based stamp for the transaction"
        elif "cat" in col.lower(): desc = "Group or Type for classification"
        
        dict_data.append({"Column": col, "Type": dtype, "Description": desc})
    return pd.DataFrame(dict_data)

# --- APP START ---
if check_password():
    st.title("💎 AI-BI Command Center")
    
    st.sidebar.header("📁 Step 1: Upload")
    main_file = st.sidebar.file_uploader("Upload Data", type=['csv', 'xlsx'])

    if main_file:
        raw_df = pd.read_csv(main_file) if main_file.name.endswith('.csv') else pd.read_excel(main_file)
        
        # Sidebar Controls
        st.sidebar.divider()
        if st.sidebar.button("🧼 Run One-Click Clean"):
            df = clean_my_data(raw_df)
            st.sidebar.success("Data Cleaned!")
        else:
            df = raw_df

        # TABS FOR ORGANIZATION
        tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📖 Data Dictionary", "🔍 Raw Data"])

        with tab1:
            st.subheader("Live Performance Overview")
            num_cols = df.select_dtypes(include='number').columns.tolist()
            if num_cols:
                kpi_val = st.sidebar.selectbox("KPI Metric", num_cols)
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Sum", f"${df[kpi_val].sum():,.2f}")
                c2.metric("Avg Value", f"${df[kpi_val].mean():,.2f}")
                c3.metric("Row Count", f"{len(df):,}")

                chart_col = st.sidebar.selectbox("Group By", df.columns)
                fig = px.bar(df.groupby(chart_col)[kpi_val].sum().reset_index(), 
                             x=chart_col, y=kpi_val, color_discrete_sequence=['#4eb8b8'], template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Data Dictionary")
            st.markdown("Use this to understand what each column represents.")
            data_dict = generate_dictionary(df)
            for _, row in data_dict.iterrows():
                st.markdown(f"""
                <div class="dictionary-card">
                    <strong>Column: {row['Column']}</strong><br>
                    <small>Type: {row['Type']} | Purpose: {row['Description']}</small>
                </div>
                """, unsafe_allow_html=True)

        with tab3:
            st.dataframe(df, use_container_width=True)
            
    else:
        st.info("Please upload a file to begin.")
