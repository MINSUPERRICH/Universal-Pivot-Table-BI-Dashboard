import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(page_title="Universal Pivot & BI App", layout="wide")

st.title("📊 Universal Pivot & BI Dashboard")
st.markdown("Upload your data, pivot it, and visualize results instantly.")

# 1. File Upload Section
uploaded_file = st.sidebar.file_uploader("Upload Excel or CSV", type=['csv', 'xlsx'])

if uploaded_file:
    # Load Data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.sidebar.success("File Loaded Successfully!")

    # 2. Pivot Table Settings
    st.sidebar.header("Pivot Table Configuration")
    
    all_columns = df.columns.tolist()
    
    rows = st.sidebar.multiselect("Select Rows (Index)", options=all_columns, default=all_columns[1] if len(all_columns)>1 else None)
    cols = st.sidebar.selectbox("Select Columns", options=[None] + all_columns)
    vals = st.sidebar.multiselect("Select Values (Metrics)", options=all_columns, default=all_columns[-1] if len(all_columns)>0 else None)
    agg_func = st.sidebar.selectbox("Aggregation Method", ["sum", "mean", "count", "min", "max"], index=0)

    # 3. Logic: Generate Pivot Table
    if rows and vals:
        try:
            pivot_df = df.pivot_table(
                index=rows,
                columns=cols if cols else None,
                values=vals,
                aggfunc=agg_func
            ).fillna(0)

            # Display Pivot Table
            st.subheader("🧮 Pivot Table Result")
            st.dataframe(pivot_df, use_container_width=True)

            # 4. BI Visualization
            st.divider()
            st.subheader("📈 Visual Analysis")
            
            chart_type = st.selectbox("Choose Chart Type", ["Bar Chart", "Line Chart", "Scatter Plot", "Area Chart"])
            
            # Reset index for plotting
            plot_df = pivot_df.reset_index()
            
            # Simple Logic to handle Multi-Index for plotting
            x_axis = rows[0]
            y_axis = vals[0]

            if chart_type == "Bar Chart":
                fig = px.bar(plot_df, x=x_axis, y=y_axis, color=cols if cols else None, barmode="group", template="plotly_white")
            elif chart_type == "Line Chart":
                fig = px.line(plot_df, x=x_axis, y=y_axis, color=cols if cols else None, template="plotly_white")
            elif chart_type == "Area Chart":
                fig = px.area(plot_df, x=x_axis, y=y_axis, color=cols if cols else None, template="plotly_white")
            else:
                fig = px.scatter(plot_df, x=x_axis, y=y_axis, color=cols if cols else None, template="plotly_white")

            st.plotly_chart(fig, use_container_width=True)

            # 5. Export Data
            csv = pivot_df.to_csv().encode('utf-8')
            st.download_button("📥 Download Pivot Results (CSV)", data=csv, file_name="pivot_analysis.csv", mime="text/csv")

        except Exception as e:
            st.error(f"Analysis Error: {e}")
    else:
        st.info("Please select Rows and Values in the sidebar to start.")

else:
    st.info("👋 Welcome! Please upload a CSV or Excel file in the sidebar to begin your analysis.")
    # Show a sample preview if no file is uploaded
    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=200)