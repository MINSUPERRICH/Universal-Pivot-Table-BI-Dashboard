import streamlit as st
import pandas as pd
import plotly.express as px

# --- (Password & Cleaning functions remain the same as previous versions) ---

if check_password():
    role = st.session_state["user_role"]
    st.title("💎 Dynamic BI Command Center")
    
    main_file = st.sidebar.file_uploader("Upload Data File", type=['csv', 'xlsx'])

    if main_file:
        df = pd.read_csv(main_file) if main_file.name.endswith('.csv') else pd.read_excel(main_file)
        
        # 1. DYNAMIC KPI SETUP
        st.sidebar.divider()
        st.sidebar.header("🎯 Step 2: Select Your KPIs")
        
        # Automatically find all columns with numbers
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols:
            # Let the user pick which columns are the "KPIs" for THIS file
            selected_kpis = st.sidebar.multiselect(
                "Which columns are KPIs?", 
                options=numeric_cols,
                default=numeric_cols[:2] if len(numeric_cols) > 1 else numeric_cols
            )
            
            # Choose how to calculate them (Sum for Sales, Mean for Rating, etc.)
            agg_method = st.sidebar.selectbox("Calculation Method", ["sum", "mean", "max", "min"])

            # 2. RENDER KPI CARDS DYNAMICALLY
            st.subheader("📌 Performance Overview")
            if selected_kpis:
                # Create a column for each selected KPI
                kpi_layout = st.columns(len(selected_kpis))
                
                for i, kpi in enumerate(selected_kpis):
                    total_val = df[kpi].agg(agg_method)
                    
                    # Formatting: Use $ for sales/price, otherwise standard numbers
                    if any(word in kpi.lower() for word in ['price', 'sale', 'cost', 'revenue']):
                        kpi_layout[i].metric(label=kpi, value=f"${total_val:,.2f}")
                    else:
                        kpi_layout[i].metric(label=kpi, value=f"{total_val:,.0f}")
            
            # 3. DYNAMIC CHARTING
            st.divider()
            st.subheader("📈 Visual Breakdown")
            
            chart_group = st.sidebar.selectbox("Breakdown by (e.g., Category or Date)", df.columns)
            chart_kpi = st.sidebar.selectbox("Chart Metric", selected_kpis)
            
            chart_data = df.groupby(chart_group)[chart_kpi].agg(agg_method).reset_index()
            
            fig = px.bar(
                chart_data, 
                x=chart_group, 
                y=chart_kpi, 
                color_discrete_sequence=['#4eb8b8'],
                template="plotly_white",
                title=f"{agg_method.title()} of {chart_kpi} by {chart_group}"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("No numeric columns found in this file to create KPIs.")

    else:
        st.info("👋 Upload any file to see the Dynamic KPI Engine in action.")
