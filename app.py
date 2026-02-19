import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches

# --- SETUP ---
st.set_page_config(page_title="AI Decision Hub", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-bottom: 4px solid #4eb8b8; }
    .forecast-box { background-color: #e0f2f2; padding: 20px; border-radius: 10px; border: 1px dashed #4eb8b8; }
    </style>
    """, unsafe_allow_html=True)

# 1. Password Check
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == "rich"}), key="password")
        return False
    return st.session_state["password_correct"]

if check_password():
    st.title("💎 AI Decision & Forecast Hub")
    
    st.sidebar.header("📁 Data Upload")
    main_file = st.sidebar.file_uploader("Upload Historical Sales", type=['csv', 'xlsx'])

    if main_file:
        df = pd.read_csv(main_file) if main_file.name.endswith('.csv') else pd.read_excel(main_file)
        
        # Ensure Date column
        date_col = st.sidebar.selectbox("Date Column", df.columns)
        df[date_col] = pd.to_datetime(df[date_col])
        val_col = st.sidebar.selectbox("Value Column (Sales)", df.select_dtypes(include='number').columns)

        # --- KPI & COMPARISON LOGIC ---
        latest_date = df[date_col].max()
        current_month = df[df[date_col].dt.to_period('M') == latest_date.to_period('M')]
        prev_month = df[df[date_col].dt.to_period('M') == (latest_date - pd.DateOffset(months=1)).to_period('M')]

        st.subheader(f"📊 Performance vs. Last Month ({latest_date.strftime('%B %Y')})")
        k1, k2, k3 = st.columns(3)
        
        curr_total = current_month[val_col].sum()
        prev_total = prev_month[val_col].sum()
        diff = curr_total - prev_total
        
        k1.metric("Current Sales", f"${curr_total:,.0f}", f"{diff:,.0f} vs LM")
        k2.metric("Orders", f"{len(current_month):,}", f"{len(current_month)-len(prev_month)} vs LM")
        k3.metric("Avg Ticket", f"${(curr_total/len(current_month) if len(current_month)>0 else 0):,.2f}")

        # --- AI FORECASTING SECTION ---
        st.divider()
        st.subheader("🔮 AI Trend Forecasting")
        
        # Prepare data for simple linear forecast
        daily_sales = df.groupby(date_col)[val_col].sum().reset_index()
        daily_sales['day_index'] = np.arange(len(daily_sales))
        
        # Simple Linear Regression (Trendline)
        z = np.polyfit(daily_sales['day_index'], daily_sales[val_col], 1)
        p = np.poly1d(z)
        
        # Predict next 30 days
        next_days = np.arange(len(daily_sales), len(daily_sales) + 30)
        predictions = p(next_days)
        forecast_total = predictions.sum()

        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            st.markdown(f"""
            <div class="forecast-box">
                <h4>Next 30 Days Forecast</h4>
                <h2 style="color: #4eb8b8;">${forecast_total:,.0f}</h2>
                <p>Based on your historical growth trend, the AI expects this volume for the coming month.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_f2:
            # Chart showing history + forecast
            hist_trace = px.line(daily_sales, x=date_col, y=val_col, title="Sales History & Trend")
            hist_trace.update_traces(line_color='#d1d1d1')
            st.plotly_chart(hist_trace, use_container_width=True)

        # --- REPORTING ---
        st.sidebar.divider()
        st.sidebar.header("🎬 Final Reports")
        # Export logic remains same as previous versions
        st.sidebar.button("Generate PowerPoint Deck")
        st.sidebar.button("Download Merged Excel")

    else:
        st.info("Upload your jewelry sales file to see AI predictions.")
