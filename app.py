import streamlit as st
import pandas as pd
import plotly.express as px

# --- (Password & Cleaning functions remain the same) ---

if check_password():
    role = st.session_state["user_role"]
    st.title("💎 Unified BI Analysis")
    
    uploaded_file = st.sidebar.file_uploader("Upload File", type=['csv', 'xlsx', 'jpg', 'pdf'])

    if uploaded_file:
        # (File loading logic for Excel/CSV/Images as before)
        df = pd.read_excel(uploaded_file) # Simplified for this example

        # --- SIDEBAR CONTROLS ---
        st.sidebar.header("📊 Chart Settings")
        chart_type = st.sidebar.radio("Select Visualization", ["Bar Chart", "Line Graph", "Pie Chart (Round)"])
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        selected_kpis = st.sidebar.multiselect("Select KPIs", options=numeric_cols, default=numeric_cols[:1])
        group_by = st.sidebar.selectbox("Group By", df.columns)

        # --- TABS ---
        tab_visual, tab_pivot, tab_settings = st.tabs(["📈 Dashboard", "🧮 Pivot Table", "⚙️ Settings"])

        with tab_visual:
            # Render KPI Metrics at top
            k_cols = st.columns(len(selected_kpis) if selected_kpis else 1)
            for i, kpi in enumerate(selected_kpis):
                total = df[kpi].sum()
                k_cols[i].metric(kpi, f"{total:,.2f}")

            # Dynamic Charting Logic
            if selected_kpis:
                chart_df = df.groupby(group_by)[selected_kpis[0]].sum().reset_index()
                
                if chart_type == "Bar Chart":
                    fig = px.bar(chart_df, x=group_by, y=selected_kpis[0], color_discrete_sequence=['#4eb8b8'])
                elif chart_type == "Line Graph":
                    fig = px.line(chart_df, x=group_by, y=selected_kpis[0], markers=True, color_discrete_sequence=['#4eb8b8'])
                else: # Pie Chart
                    fig = px.pie(chart_df, names=group_by, values=selected_kpis[0], hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        with tab_pivot:
            st.subheader(f"Summary Table: {group_by} vs Selected KPIs")
            # This creates a clean Pivot Table view with only the data you need
            pivot_view = df.groupby(group_by)[selected_kpis].sum()
            st.dataframe(pivot_view, use_container_width=True)
            
            # Option to download only this pivot data
            csv_pivot = pivot_view.to_csv().encode('utf-8')
            st.download_button("📥 Download Pivot Results", data=csv_pivot, file_name="pivot_summary.csv")

    else:
        st.info("Please upload your master file to begin analysis.")
