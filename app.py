import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Password Protection Logic
def check_password():
    """Returns True if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "rich":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Enter Password to access the BI Dashboard", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Enter Password to access the BI Dashboard", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

# --- APP START ---
st.set_page_config(page_title="Secure AI-BI Dashboard", layout="wide")

if check_password():
    # Everything inside this 'if' block is only visible after login
    st.title("🚀 Secure BI & Pivot Engine")
    
    # --- Sidebar Configuration ---
    st.sidebar.header("📂 Step 1: Upload Data")
    uploaded_file = st.sidebar.file_uploader("Choose Excel/CSV", type=['csv', 'xlsx'])

    if uploaded_file:
        @st.cache_data
        def load_data(file):
            if file.name.endswith('.csv'):
                return pd.read_csv(file)
            return pd.read_excel(file)
        
        df = load_data(uploaded_file)
        all_columns = df.columns.tolist()

        # --- Calculated Measures (DAX Section) ---
        st.sidebar.divider()
        st.sidebar.header("➕ Step 2: Create Measures")
        measure_name = st.sidebar.text_input("Measure Name", placeholder="e.g. Sales_Tax")
        measure_formula = st.sidebar.text_input("Formula (e.g. [Sales] * 0.1)")
        
        if st.sidebar.button("Add Measure"):
            try:
                clean_formula = measure_formula
                for col in all_columns:
                    clean_formula = clean_formula.replace(f"[{col}]", f"df['{col}']")
                df[measure_name] = eval(clean_formula)
                st.sidebar.success(f"Added {measure_name}!")
                all_columns = df.columns.tolist()
            except Exception as e:
                st.sidebar.error(f"Formula Error: {e}")

        # --- Pivot Table Setup ---
        st.sidebar.divider()
        st.sidebar.header("📊 Step 3: Pivot Setup")
        rows = st.sidebar.multiselect("Rows", options=all_columns)
        cols = st.sidebar.selectbox("Columns", options=[None] + all_columns)
        vals = st.sidebar.multiselect("Values (Metrics)", options=all_columns)
        agg_func = st.sidebar.selectbox("Aggregation", ["sum", "mean", "count", "min", "max"])

        # --- Main Dashboard Rendering ---
        if rows and vals:
            try:
                pivot_df = df.pivot_table(index=rows, columns=cols if cols else None, values=vals, aggfunc=agg_func).fillna(0)
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.subheader("🧮 Results Table")
                    st.dataframe(pivot_df, use_container_width=True)
                
                with c2:
                    st.subheader("📈 Visualization")
                    plot_df = pivot_df.reset_index()
                    if isinstance(plot_df.columns, pd.MultiIndex):
                        plot_df.columns = ['_'.join(map(str, col)).strip() for col in plot_df.columns.values]
                    
                    y_val = plot_df.columns[-1]
                    fig = px.bar(plot_df, x=rows[0], y=y_val, color=cols if cols else None, template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Pivot Error: {e}")
        else:
            st.info("👈 Please select your Rows and Values in the sidebar.")
    else:
        st.info("👋 Welcome! Please upload your data file in the sidebar to begin.")

    # Log out option (clears session)
    if st.sidebar.button("Log Out"):
        st.session_state["password_correct"] = False
        st.rerun()
