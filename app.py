import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt

# --- 1. INITIALIZATION & SECURITY ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {"rich": {"password": "777", "role": "admin"}, "staff": {"password": "123", "role": "team"}}
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False
if "master_df" not in st.session_state:
    st.session_state["master_df"] = None

st.set_page_config(page_title="Executive BI & Presentation Hub", layout="wide")

# --- 2. PPT GENERATION ENGINE ---
def generate_advanced_ppt(df_summary, fig, title_text, subtitle_text, insight_text):
    prs = Presentation()
    
    # Slide 1: Professional Title Slide
    slide1 = prs.slides.add_slide(prs.slide_layouts[0])
    slide1.shapes.title.text = title_text
    slide1.placeholders[1].text = subtitle_text

    # Slide 2: Visual & Insight Slide
    slide2 = prs.slides.add_slide(prs.slide_layouts[5]) # Title Only layout
    slide2.shapes.title.text = "Visual Performance Overview"
    
    # Export Plotly fig to image
    img_bytes = fig.to_image(format="png", width=1000, height=600)
    img_stream = BytesIO(img_bytes)
    slide2.shapes.add_picture(img_stream, Inches(0.5), Inches(1.5), width=Inches(9))
    
    # Slide 3: Executive Key Insights (Revisable Text)
    slide3 = prs.slides.add_slide(prs.slide_layouts[1]) # Title and Content
    slide3.shapes.title.text = "Executive Summary & Insights"
    body_shape = slide3.shapes.placeholders[1]
    tf = body_shape.text_frame
    tf.text = "Key Observations:"
    p = tf.add_paragraph()
    p.text = insight_text
    p.level = 1

    ppt_output = BytesIO()
    prs.save(ppt_output)
    return ppt_output.getvalue()

# --- 3. MAIN APP LOGIC ---
def check_password():
    def password_entered():
        user, pwd = st.session_state["u"], st.session_state["p"]
        if user in st.session_state["user_db"] and st.session_state["user_db"][user]["password"] == pwd:
            st.session_state.update({"password_correct": True, "user_role": st.session_state["user_db"][user]["role"], "logged_in_user": user})
    if not st.session_state["password_correct"]:
        st.text_input("Username", key="u")
        st.text_input("Password", type="password", key="p", on_change=password_entered)
        return False
    return True

if check_password():
    st.sidebar.title(f"Welcome, {st.session_state['logged_in_user'].title()}")
    uploaded_files = st.sidebar.file_uploader("Upload Data", type=['csv', 'xlsx'], accept_multiple_files=True)

    if uploaded_files:
        # Load and Merge Logic (Simplified for brevity)
        df = pd.read_excel(uploaded_files[0]) if uploaded_files[0].name.endswith('.xlsx') else pd.read_csv(uploaded_files[0])
        st.session_state["master_df"] = df
        
        tab_dash, tab_ppt, tab_settings = st.tabs(["📊 Dashboard", "🎬 PPT Designer", "⚙️ Settings"])

        with tab_dash:
            st.header("Unified Data Analysis")
            num_cols = df.select_dtypes(include='number').columns.tolist()
            selected_kpi = st.sidebar.selectbox("KPI for Visuals", num_cols)
            group_by = st.sidebar.selectbox("Group By", df.columns)
            
            fig = px.bar(df.groupby(group_by)[selected_kpi].sum().reset_index(), 
                         x=group_by, y=selected_kpi, color_discrete_sequence=['#4eb8b8'], template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with tab_ppt:
            st.header("🎬 Business Presentation Builder")
            st.write("Customize your meeting slides below.")
            
            col1, col2 = st.columns(2)
            with col1:
                ppt_title = st.text_input("Presentation Title", value="Monthly Business Review")
                ppt_sub = st.text_input("Subtitle", value=f"Analysis prepared by {st.session_state['logged_in_user'].title()}")
            with col2:
                ppt_insight = st.text_area("Key Insight / Action Item", value="Sales are up 15% in the North Region. Suggest increasing inventory for Q2.")
            
            if st.button("🚀 Finalize & Download PPTX"):
                ppt_data = generate_advanced_ppt(df, fig, ppt_title, ppt_sub, ppt_insight)
                st.download_button(label="📥 Download Ready-to-Present Deck", data=ppt_data, file_name="Meeting_Presentation.pptx")
                st.success("Slide deck generated with your custom insights!")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
