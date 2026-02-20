import streamlit as st
import pandas as pd
import plotly.express as px

# --- (Password & Cleaning functions remain the same) ---

if check_password():
    role = st.session_state["user_role"]
    st.title("💎 Unified BI Analysis")
    
    uploaded_file = st.sidebar.file_uploader("Upload File", type=['csv', 'xlsx', 'jpg', 'pdf'])

    if uploaded_file:
        # Load Data Logic
        df = pd.read_excel(uploaded_file) # Standardized from your last session

        # --- SIDEBAR: VISUALIZATION SETTINGS ---
        st.sidebar.header("📊 Visualization Settings")
        chart_style = st.sidebar.radio("Select Chart Type", ["Bar Chart", "Line Graph", "Pie Chart (Round)"])
        
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        selected_kpis = st.sidebar.multiselect("Select KPIs", options=numeric_cols, default=numeric_cols[:1])
        group_by = st.sidebar.selectbox("Group By (Rows)", df.columns)

        # --- NEW: TOP N / BOTTOM N RANKING ---
        st.sidebar.divider()
        st.sidebar.header("🏆 Ranking Filter")
        use_ranking = st.sidebar.toggle("Enable Ranking (Top/Bottom)")
        
        if use_ranking:
            rank_type = st.sidebar.selectbox("Rank By", ["Top", "Bottom"])
            rank_limit = st.sidebar.slider("Show how many?", 1, 20, 5)
        
        # --- TABS ---
        tab_dash, tab_pivot, tab_settings = st.tabs(["📈 Dashboard", "🧮 Pivot Table", "⚙️ Settings"])

        with tab_dash:
            if selected_kpis and group_by:
                # Calculate aggregated data
                chart_df = df.groupby(group_by)[selected_kpis[0]].sum().reset_index()
                
                # Apply Ranking Logic
                if use_ranking:
                    is_ascending = (rank_type == "Bottom")
                    chart_df = chart_df.sort_values(by=selected_kpis[0], ascending=is_ascending).head(rank_limit)
                    st.subheader(f"Dashboard: {rank_type} {rank_limit} {group_by}")
                else:
                    st.subheader("Unified Data Analysis")

                # Metrics
                k_cols = st.columns(len(selected_kpis))
                for i, kpi in enumerate(selected_kpis):
                    val = chart_df[kpi].sum() if use_ranking else df[kpi].sum()
                    k_cols[i].metric(kpi, f"{val:,.2f}")

                # Charts (Bar, Line, Round/Pie)
                if chart_style == "Bar Chart":
                    fig = px.bar(chart_df, x=group_by, y=selected_kpis[0], color_discrete_sequence=['#4eb8b8'])
                elif chart_style == "Line Graph":
                    fig = px.line(chart_df, x=group_by, y=selected_kpis[0], markers=True, color_discrete_sequence=['#4eb8b8'])
                else: # Pie Chart
                    fig = px.pie(chart_df, names=group_by, values=selected_kpis[0], hole=0.4)
                
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        with tab_pivot:
            st.subheader("Data Pivot Summary")
            # Pivot table reflects the ranking if enabled
            pivot_data = chart_df.set_index(group_by) if use_ranking else df.groupby(group_by)[selected_kpis].sum()
            st.dataframe(pivot_data, use_container_width=True)

    else:
        st.info("Please upload your master file to begin analysis.")
