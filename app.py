import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches

# --- SETUP & THEME ---
st.set_page_config(page_title="Professional BI Dashboard", layout="wide")

# Custom CSS for a clean, colorful (but not overwhelming) look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #4eb8b8; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 1. Password Protection
def check_password():
    def password_entered():
        if st.session_state["password"] == "rich":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    return True

# --- POWERPOINT ENGINE ---
def create_ppt(df_pivot, fig):
    prs = Presentation()
    # Title Slide
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Business Intelligence Report"
    slide.placeholders[1].text = "Summary of Analysis and Visuals"
    # Chart Slide
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Key Performance Visualization"
    img_bytes = fig.to_image(format="png")
    image_stream = BytesIO(img_bytes)
    slide.shapes.add_picture(image_stream, Inches(0.5), Inches(1.5), width=Inches(9))
    ppt_output = BytesIO()
    prs.save(ppt_output)
    return ppt_output.getvalue()

# --- APP START ---
if check_password():
    st.title("💎 Jewelry & Sales BI Hub")
    
    # Sidebar: Data Management
    st.sidebar.header("📁 Data Sources")
    main_file = st.sidebar.file_uploader("Upload Main File", type=['csv', 'xlsx'], key="main")
    lookup_file = st.sidebar.file_uploader("Upload Lookup/Price List", type=['csv', 'xlsx'], key="lookup")

    if main_file:
        df = pd.read_csv(main_file) if main_file.name.endswith('.csv') else pd.read_excel(main_file)
        
        # VLOOKUP Feature
        if lookup_file:
            df_lookup = pd.read_csv(lookup_file) if lookup_file.name.endswith('.csv') else pd.read_excel(lookup_file)
            common = list(set(df.columns) & set(df_lookup.columns))
            if common:
                col = st.sidebar.selectbox("Match Column (VLOOKUP)", common)
                if st.sidebar.button("Run Merge"):
                    df = pd.merge(df, df_lookup, on=col, how='left')
                    st.sidebar.success("Linked!")

        all_cols = df.columns.tolist()

        # Step 2: Calculations
        st.sidebar.divider()
        st.sidebar.header("➕ Custom Measures")
        m_name = st.sidebar.text_input("Measure Name (e.g., Margin)")
        m_form = st.sidebar.text_input("Formula (e.g., [Sales] - [Cost])")
        if st.sidebar.button("Add Measure"):
            try:
                clean_f = m_form
                for c in all_cols: clean_f = clean_f.replace(f"[{c}]", f"df['{c}']")
                df[m_name] = eval(clean_f)
                st.sidebar.success(f"{m_name} Added!")
                all_cols = df.columns.tolist()
            except: st.sidebar.error("Check Formula Syntax")

        # Step 3: KPIs (Top Row)
        st.subheader("📌 Team KPIs")
        kpi_cols = st.columns(3)
        # Assuming we have numeric columns to show
        nums = df.select_dtypes(include=['number']).columns.tolist()
        if nums:
            kpi_cols[0].metric("Total Sales", f"${df[nums[0]].sum():,.0f}")
            if len(nums) > 1:
                kpi_cols[1].metric("Avg Performance", f"{df[nums[1]].mean():,.1f}")
            kpi_cols[2].metric("Total Items", f"{len(df):,}")

        # Step 4: Pivot & Visuals
        st.divider()
        st.sidebar.header("📊 Reporting")
        p_row = st.sidebar.multiselect("Rows", all_cols)
        p_val = st.sidebar.selectbox("Value to Chart", nums if nums else all_cols)
        
        if p_row and p_val:
            pivot_df = df.pivot_table(index=p_row, values=p_val, aggfunc='sum').reset_index()
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader("🧮 Summary Table")
                st.dataframe(pivot_df, use_container_width=True)
            
            with col2:
                st.subheader("📈 Visual Insight")
                # Using a professional, muted color palette (Teal/Blue)
                fig = px.bar(pivot_df, x=p_row[0], y=p_val, color_discrete_sequence=['#4eb8b8'], template="plotly_white")
                fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

            # Step 5: Export Buttons
            st.divider()
            ex_col1, ex_col2 = st.columns(2)
            
            with ex_col1:
                excel_bytes = BytesIO()
                with pd.ExcelWriter(excel_bytes, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                st.download_button("📥 Download Excel (Full Data)", excel_bytes.getvalue(), "BI_Report.xlsx")
            
            with ex_col2:
                try:
                    ppt_data = create_ppt(pivot_df, fig)
                    st.download_button("🎬 Download PowerPoint Slide", ppt_data, "Meeting_Deck.pptx")
                except:
                    st.info("PowerPoint generator requires 'kaleido' to save charts.")

        with st.expander("🔍 Raw Data Preview"):
            st.write(df.head(10))
    else:
        st.info("Please upload a file to view the BI Dashboard.")
