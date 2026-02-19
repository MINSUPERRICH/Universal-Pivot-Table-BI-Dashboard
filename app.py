import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(page_title="AI-Powered BI Dashboard", layout="wide")

st.title("🚀 Advanced BI & Pivot Engine")
st.markdown("Upload data, create **Calculated Measures (DAX-style)**, and pivot instantly.")

# 1. File Upload Section
uploaded_file = st.sidebar.file_uploader("📂 Step 1: Upload Data", type=['csv', 'xlsx'])

if uploaded_file:
    # Load Data
    @st.cache_data # Speed up the app by caching the file
    def load_data(file):
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        return pd.read_excel(file)
    
    df = load_data(uploaded_file)
    all_columns = df.columns.tolist()

    # 2. CALCULATED MEASURES (The "DAX" Section)
    st.sidebar.divider()
    st.sidebar.header("➕ Step 2: Create Measures")
    st.sidebar.info("Example: [Sales] * 0.10 or [Profit] / [Sales]")
    
    measure_name = st.sidebar.text_input("Measure Name", placeholder="e.g. Tax_Amount")
    measure_formula = st.sidebar.text_input("Formula (Use [ColumnName])", placeholder="[Sales] * 0.1")
    
    if st.sidebar.button("Add Measure"):
        try:
            # Simple parser to turn [Column] into df['Column']
            clean_formula = measure_formula
            for col in all_columns:
                clean_formula = clean_formula.replace(f"[{col}]", f"df['{col}']")
            
            # Execute the calculation
            df[measure_name] = eval(clean_formula)
            st.sidebar.success(f"Created: {measure_name}")
            all_columns = df.columns.tolist() # Refresh column list
        except Exception as e:
            st.sidebar.error(f"Formula Error: {e}")

    # 3. PIVOT TABLE SETTINGS
    st.sidebar.divider()
    st.sidebar.header("📊 Step 3: Pivot Setup")
    
    rows = st.sidebar.multiselect("Rows (Index)", options=all_columns)
    cols = st.sidebar.selectbox("Columns", options=[None] + all_columns)
    vals = st.sidebar.multiselect("Values (Metrics)", options=all_columns)
    agg_func = st.sidebar.selectbox("Aggregation", ["sum", "mean", "count", "min", "max"], index=0)

    # 4. LOGIC: RENDER RESULTS
    if rows and vals:
        try:
            # Create the Pivot
            pivot_df = df.pivot_table(
                index=rows,
                columns=cols if cols else None,
                values=vals,
                aggfunc=agg_func
            ).fillna(0)

            # Dashboard Layout
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("🧮 Pivot Table")
                st.dataframe(pivot_df, use_container_width=True)
                
                # Export Button
                csv = pivot_df.to_csv().encode('utf-8')
                st.download_button("📥 Export CSV", data=csv, file_name="analysis.csv")

            with col2:
                st.subheader("📈 Visualization")
                plot_df = pivot_df.reset_index()
                
                # Handle multi-index column names for plotting
                if isinstance(plot_df.columns, pd.MultiIndex):
                    plot_df.columns = ['_'.join(map(str, col)).strip() for col in plot_df.columns.values]
                
                y_val = plot_df.columns[-1] # Pick the last value column for Y axis
                fig = px.bar(plot_df, x=rows[0], y=y_val, color=cols if cols else None, 
                             template="plotly_dark", barmode="group")
                st.plotly_chart(fig, use_container_width=True)

            # Show Data Preview
            with st.expander("🔍 View Raw Data with New Measures"):
                st.write(df.head(10))

        except Exception as e:
            st.error(f"Pivot Error: {e}")
    else:
        st.info("👈 Use the sidebar to select your Rows and Values.")

else:
    st.info("👋 Upload a file to start building your BI App.")
