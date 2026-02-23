import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches

# --- 1. INITIALIZATION ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {"rich": {"password": "777", "role": "admin"}, "staff": {"password": "123", "role": "team"}}
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False
if "master_df" not in st.session_state:
    st.session_state["master_df"] = None

st.set_page_config(page_title="Executive BI Hub", layout="wide")

# --- 2. PPT ENGINE ---
def generate_advanced_ppt(fig, title, insight):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = title
    
    slide2 = prs.slides.add_slide(prs.slide_layouts[5])
    slide2.shapes.title.text = "Performance Visualization"
    img_bytes = fig.to_image(format="png")
    slide2.shapes.add_picture(BytesIO(img_bytes), Inches(1), Inches(1.5), width=Inches(8))
    
    slide3 = prs.slides.add_slide(prs.slide_layouts[1])
    slide3.shapes.title.text = "Key Business Insights"
    slide3.placeholders[1].text = insight
    
    ppt_out = BytesIO()
    prs.save(ppt_out)
    return ppt_out.getvalue()

# --- 3. LOGIN SYSTEM ---
def check_password():
    if not st.session_state["password_correct"]:
        st.title("🔒 Business Intelligence Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In"):
            if u in st.session_state["user_db"] and st.session_state["user_db"][u]["password"] == p:
                st.session_state.update({"password_correct": True, "role": st.session_state["user_db"][u]["role"], "user": u})
                st.rerun()
            else: st.error("Invalid credentials")
        return False
    return True

# --- 4. MAIN APP ---
if check_password():
    st.sidebar.title(f"Welcome, {st.session_state['user'].title()}")
    
    # GLOBAL TABS
    tab_dash, tab_pivot, tab_merge, tab_ppt, tab_settings = st.tabs([
        "📊 Dashboard", "🧮 Pivot Table", "🔗 Link & Match", "🎬 PPT Designer", "⚙️ Settings"
    ])

    # FIXED: Added 'accept_multiple_files=True' so you can upload 2+ files for VLOOKUP
    uploaded_files = st.sidebar.file_uploader("Upload Data Files", type=['csv', 'xlsx'], accept_multiple_files=True)

    if uploaded_files:
        # Load all uploaded files into a dictionary
        data_dict = {}
        for f in uploaded_files:
            data_dict[f.name] = pd.read_excel(f) if f.name.endswith('xlsx') else pd.read_csv(f)
        
        # If no merge has happened, default to the first uploaded file
        if st.session_state["master_df"] is None or len(uploaded_files) == 1:
            st.session_state["master_df"] = list(data_dict.values())[0]
            
        working_df = st.session_state["master_df"]

        # --- DASHBOARD TAB ---
        with tab_dash:
            st.header("Visual Performance")
            num_cols = working_df.select_dtypes('number').columns.tolist()
            if num_cols:
                col = st.sidebar.selectbox("Select KPI", num_cols)
                grp = st.sidebar.selectbox("Group By", working_df.columns)
                fig = px.bar(working_df.groupby(grp)[col].sum().reset_index(), x=grp, y=col, color_discrete_sequence=['#4eb8b8'])
                st.plotly_chart(fig, use_container_width=True)

        # --- PIVOT TABLE TAB ---
        with tab_pivot:
            st.header("Data Pivot Summary")
            st.dataframe(working_df.groupby(grp)[col].sum(), use_container_width=True)

        # --- LINK & MATCH (VLOOKUP) TAB ---
        with tab_merge:
            st.header("🔗 Link & Match (VLOOKUP)")
            if len(data_dict) < 2:
                st.info("To use Link & Match, please drag and drop at least TWO files into the sidebar uploader.")
            else:
                st.write("Merge two files together using a common Key column.")
                col1, col2 = st.columns(2)
                with col1:
                    base_file = st.selectbox("1. Main File", list(data_dict.keys()))
                with col2:
                    merge_file = st.selectbox("2. File to Link", [f for f in data_dict.keys() if f != base_file])
                
                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    left_on = st.selectbox(f"Key in {base_file}", data_dict[base_file].columns)
                with m_col2:
                    right_on = st.selectbox(f"Key in {merge_file}", data_dict[merge_file].columns)
                
                if st.button("Run VLOOKUP Match"):
                    new_merged_df = pd.merge(data_dict[base_file], data_dict[merge_file], left_on=left_on, right_on=right_on, how='left')
                    st.session_state["master_df"] = new_merged_df
                    st.success("Successfully linked! Your Dashboard and Pivot Table are now using the combined data.")
                    st.dataframe(new_merged_df.head(10))

        # --- PPT DESIGNER TAB ---
        with tab_ppt:
            st.header("PPT Presentation Designer")
            p_title = st.text_input("Slide Title", "Business Review")
            p_insight = st.text_area("Observations", "Add your meeting notes here.")
            if st.button("Generate Presentation"):
                ppt_data = generate_advanced_ppt(fig, p_title, p_insight)
                st.download_button("📥 Download PowerPoint", ppt_data, "Meeting_Deck.pptx")
    else:
        with tab_dash: st.info("Please upload a file in the sidebar to begin analysis.")
        with tab_ppt: st.warning("Presentation Designer requires an active data chart.")

    # --- SETTINGS TAB ---
    with tab_settings:
        st.header("Settings")
        st.write("Change password or manage your account here.")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
