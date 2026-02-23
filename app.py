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

# --- 2. PPT ENGINE (Fixes the ValueError with Kaleido) ---
def generate_advanced_ppt(fig, title, insight):
    prs = Presentation()
    # Title Slide
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = title
    # Chart Slide (Requires kaleido in requirements.txt)
    slide2 = prs.slides.add_slide(prs.slide_layouts[5])
    slide2.shapes.title.text = "Performance Visualization"
    img_bytes = fig.to_image(format="png")
    slide2.shapes.add_picture(BytesIO(img_bytes), Inches(1), Inches(1.5), width=Inches(8))
    # Insights Slide
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
    
    # TABS (Defined globally so they never disappear)
    tab_dash, tab_pivot, tab_merge, tab_ppt, tab_settings = st.tabs([
        "📊 Dashboard", "🧮 Pivot Table", "🔗 Link & Match", "🎬 PPT Designer", "⚙️ Settings"
    ])

    uploaded_file = st.sidebar.file_uploader("Upload Master Data", type=['csv', 'xlsx'])

    if uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
        st.session_state["master_df"] = df
        
        with tab_dash:
            st.header("Visual Performance")
            num_cols = df.select_dtypes('number').columns.tolist()
            if num_cols:
                col = st.sidebar.selectbox("Select KPI", num_cols)
                grp = st.sidebar.selectbox("Group By", df.columns)
                fig = px.bar(df.groupby(grp)[col].sum().reset_index(), x=grp, y=col, color_discrete_sequence=['#4eb8b8'])
                st.plotly_chart(fig, use_container_width=True)

        with tab_pivot:
            st.header("Data Pivot Summary")
            st.dataframe(df.groupby(grp)[col].sum(), use_container_width=True)

        with tab_ppt:
            st.header("PPT Presentation Designer")
            p_title = st.text_input("Slide Title", "Business Review")
            p_insight = st.text_area("Observations", "Positive growth in major segments.")
            if st.button("Generate Presentation"):
                ppt_data = generate_advanced_ppt(fig, p_title, p_insight)
                st.download_button("📥 Download PowerPoint", ppt_data, "Meeting_Deck.pptx")
    else:
        with tab_dash: st.info("Please upload a file in the sidebar to begin analysis.")
        with tab_ppt: st.warning("Presentation Designer requires an active data chart.")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
