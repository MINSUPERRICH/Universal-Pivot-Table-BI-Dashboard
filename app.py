import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
import easyocr
from PIL import Image
import fitz  # PyMuPDF
from pptx import Presentation
from pptx.util import Inches

# --- 1. INITIALIZATION & SECURITY ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "rich": {"password": "777", "role": "admin"},
        "staff": {"password": "123", "role": "team"}
    }

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

st.set_page_config(page_title="Universal AI-BI Hub", layout="wide")

# --- 2. DEFINE ALL FUNCTIONS FIRST ---

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
    for col in df.columns:
        if any(kw in col.lower() for kw in ['date', 'trans', 'posted']):
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(['en'])

def process_image_to_df(uploaded_file):
    reader = get_ocr_reader()
    image = Image.open(uploaded_file)
    result = reader.readtext(np.array(image), detail=0)
    # Convert list of strings to a simple one-column DataFrame for analysis
    return pd.DataFrame(result, columns=["Extracted Text"])

# --- 3. MAIN APP INTERFACE ---

if check_password():
    role = st.session_state["user_role"]
    user = st.session_state["logged_in_user"]
    
    st.sidebar.title(f"Welcome, {user.title()}")
    tab_dash, tab_settings = st.tabs(["📊 BI Dashboard", "⚙️ Account Settings"])

    with tab_dash:
        st.header("Unified Data Analysis")
        
        # UPLOADER supporting all types
        uploaded_file = st.sidebar.file_uploader(
            "Upload File (Excel, CSV, JPG, PDF)", 
            type=['csv', 'xlsx', 'jpg', 'jpeg', 'png', 'pdf']
        )

        if uploaded_file:
            # Handle different file types
            file_ext = uploaded_file.name.split('.')[-1].lower()
            
            if file_ext in ['csv', 'xlsx']:
                df = pd.read_csv(uploaded_file) if file_ext == 'csv' else pd.read_excel(uploaded_file)
            elif file_ext in ['jpg', 'jpeg', 'png']:
                with st.spinner("Reading Image..."):
                    df = process_image_to_df(uploaded_file)
            elif file_ext == 'pdf':
                with st.spinner("Extracting PDF Text..."):
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    text = "".join([page.get_text() for page in doc])
                    df = pd.DataFrame([line for line in text.split('\n') if line.strip()], columns=["PDF Content"])

            # Cleaning Logic
            if role == "admin" and st.sidebar.button("🧼 Run One-Click Clean"):
                df = clean_data(df)
                st.sidebar.success("Standardized!")

            # BI Engine
            num_cols = df.select_dtypes(include='number').columns.tolist()
            if num_cols:
                st.sidebar.divider()
                selected_kpis = st.sidebar.multiselect("Select KPIs", options=num_cols, default=num_cols[:1])
                
                # KPI Display
                k_cols = st.columns(len(selected_kpis))
                for i, kpi in enumerate(selected_kpis):
                    val = df[kpi].sum()
                    k_cols[i].metric(kpi, f"{val:,.2f}")

                # Charting
                group_col = st.sidebar.selectbox("Group By", df.columns)
                fig = px.bar(df.groupby(group_col)[selected_kpis[0]].sum().reset_index(), 
                             x=group_col, y=selected_kpis[0], color_discrete_sequence=['#4eb8b8'], template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("Current view: Text/Image Data")
                st.dataframe(df, use_container_width=True)

    with tab_settings:
        st.header("Security & Account")
        with st.form("reset_pwd"):
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Update Password"):
                st.session_state["user_db"][user]["password"] = new_p
                st.success("Password Updated!")

    if st.sidebar.button("Logout"):
        st.session_state["password_correct"] = False
        st.rerun()
