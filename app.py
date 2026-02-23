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
    
    tab_dash, tab_pivot, tab_merge, tab_ppt, tab_settings = st.tabs([
        "📊 Dashboard", "🧮 Pivot Table", "🔗 Link & Match", "🎬 PPT Designer", "⚙️ Settings"
    ])

    uploaded_files = st.sidebar.file_uploader("Upload Data Files", type=['csv', 'xlsx'], accept_multiple_files=True)
    
    # Initialize a blank figure to prevent PPT errors
    fig = None 

    if uploaded_files:
        data_dict = {}
        for f in uploaded_files:
            data_dict[f.name] = pd.read_excel(f) if f.name.endswith('xlsx') else pd.read_csv(f)
        
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
                
                # Assign chart to 'fig' variable
                fig = px.bar(working_df.groupby(grp)[col].sum().reset_index(), x=grp, y=col, color_discrete_sequence=['#4eb8b8'])
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        # --- PIVOT TABLE TAB ---
        with tab_pivot:
            st.header("Data Pivot Summary")
            if num_cols:
                st.dataframe(working_df.groupby(grp)[col].sum(), use_container_width=True)

        # --- LINK & MATCH (VLOOKUP) TAB ---
        with tab_merge:
            st.header("🔗 Link & Match (VLOOKUP)")
            
            # 1. Merging Section
            if len(data_dict) < 2:
                st.info("Upload at least TWO files in the sidebar to merge them.")
            else:
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
                    st.success("Files Linked Successfully!")

            # 2. Advanced Instruction & Filter Section
            st.divider()
            st.subheader("🔍 Deep Dive & Filter")
            st.write("Write an instruction to filter your current data. *(e.g., `close > 150` or `ticker == 'AAPL'`)*")
            
            filter_query = st.text_input("Filter Instruction:")
            
            if st.button("Apply Instruction"):
                try:
                    # Apply the user's specific text condition
                    filtered_df = working_df.query(filter_query)
                    st.success(f"Found {len(filtered_df)} matching rows!")
                    st.dataframe(filtered_df, use_container_width=True)
                    
                    # Create a specific download button for these filtered results
                    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Filtered Results",
                        data=csv_data,
                        file_name="Filtered_Data_Results.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error("Could not apply filter. Please check your spelling or formatting. (Hint: Text values need quotes, like `Sector == 'Tech'`)")
            
            # Generic download button for the full merged data
            if st.session_state["master_df"] is not None and not filter_query:
                st.download_button(
                    "📥 Download Full Merged Data", 
                    st.session_state["master_df"].to_csv(index=False).encode('utf-8'), 
                    "Full_Merged_Dataset.csv"
                )

        # --- PPT DESIGNER TAB ---
        with tab_ppt:
            st.header("PPT Presentation Designer")
            if fig is not None:
                p_title = st.text_input("Slide Title", "Business Review")
                p_insight = st.text_area("Observations", "Add your meeting notes here.")
                if st.button("Generate Presentation"):
                    ppt_data = generate_advanced_ppt(fig, p_title, p_insight)
                    st.download_button("📥 Download PowerPoint", ppt_data, "Meeting_Deck.pptx")
            else:
                st.warning("Please configure your chart in the 'Dashboard' tab first.")
    else:
        st.info("Please upload your data in the sidebar to begin.")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
