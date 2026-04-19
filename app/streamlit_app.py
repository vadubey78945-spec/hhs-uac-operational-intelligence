"""
app/streamlit_app.py
---------------------
Main Streamlit dashboard for the UAC Care Transition Analytics project.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from src.data_loader   import load_data, load_data_from_upload
from src.preprocessing import clean_data, filter_by_date, get_monthly_aggregates
from src.metrics       import compute_kpis, kpi_summary, monthly_kpi_table
from src.bottleneck    import detect_bottlenecks, get_bottleneck_summary, bottleneck_stats
from src.visualization import (
    pipeline_load_chart, intake_discharge_chart, kpi_trends_chart,
    backlog_chart, bottleneck_heatmap, outcome_stability_chart, monthly_summary_chart,
)
from src.utils import generate_insights, generate_recommendations

st.set_page_config(
    page_title="UAC Care Transition Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
html,body,[data-testid="stAppViewContainer"]{background:#0E1117;color:#FAFAFA;font-family:'Inter',Arial,sans-serif}
[data-testid="stSidebar"]{background:#13161F}
.kpi-card{background:linear-gradient(135deg,#1A1D2E 0%,#252842 100%);border:1px solid #2D3150;border-radius:14px;padding:22px 18px;text-align:center;margin-bottom:8px}
.kpi-label{font-size:.75rem;color:#8A8FA8;text-transform:uppercase;letter-spacing:.08em}
.kpi-value{font-size:2rem;font-weight:700;margin:6px 0}
.kpi-sub{font-size:.75rem;color:#8A8FA8}
.section-header{font-size:1.1rem;font-weight:600;color:#00D4FF;border-left:3px solid #00D4FF;padding-left:10px;margin:18px 0 10px}
.insight-card{background:#1A1D2E;border:1px solid #2D3150;border-radius:10px;padding:14px 16px;margin-bottom:8px;font-size:.9rem;line-height:1.55}
.rec-card{background:#13161F;border-left:4px solid #00D4FF;border-radius:8px;padding:12px 16px;margin-bottom:8px;font-size:.88rem}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 UAC Analytics")
    st.markdown("---")
    st.markdown("### 📂 Data Source")
    data_source = st.radio("Select Data Source", [ "Use bundled dataset","Upload CSV"], label_visibility="collapsed")

    raw_df = None
    if data_source == "Upload CSV":
        uploaded = st.file_uploader("Upload HHS UAC CSV", type=["csv"])
        if uploaded:
            try:
                raw_df = load_data_from_upload(uploaded)
                st.success("File loaded successfully")
            except Exception as e:
                st.error(f"{e}")
    else:
        default_path = os.path.join(os.path.dirname(__file__), "..", "data",
                                    "HHS_Unaccompanied_Alien_Children_Program.csv")
        if os.path.exists(default_path):
            try:
                raw_df = load_data(default_path)
                st.success("Bundled dataset loaded")
            except Exception as e:
                st.error(f"{e}")
        else:
            st.warning("Bundled dataset not found. Place the CSV in data/")

    st.markdown("---")

    if raw_df is not None:
        df_clean = clean_data(raw_df)
        st.markdown("### 📅 Date Range")
        min_d = df_clean["Date"].min().date()
        max_d = df_clean["Date"].max().date()
        start_date = st.date_input("Start", value=min_d, min_value=min_d, max_value=max_d)
        end_date   = st.date_input("End",   value=max_d, min_value=min_d, max_value=max_d)
        if start_date > end_date:
            st.error("Start date must be before end date.")
            st.stop()
        df_filtered = filter_by_date(df_clean, str(start_date), str(end_date))

        st.markdown("---")
        st.markdown("### ⚙️ KPI Thresholds")
        thresh_te = st.slider("Min Transfer Efficiency",     0.0, 1.0, 0.80, 0.05)
        thresh_de = st.slider("Min Discharge Effectiveness", 0.0, 0.5, 0.10, 0.01)
        thresh_tp = st.slider("Min Pipeline Throughput",     0.0, 2.0, 0.50, 0.05)

        st.markdown("---")
        st.markdown("### 🔧 Bottleneck Settings")
        sustained_n = st.slider("Sustained Bottleneck Threshold (days)", 1, 14, 3)
        st.markdown("---")
        st.caption(f"Showing: {start_date} to {end_date}")
        st.caption(f"Rows in view: {len(df_filtered):,}")

# ── HEADER ────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding:18px 0 10px'>
  <h1 style='color:#00D4FF;margin:0;font-size:2rem;'>
    UAC Care Transition Efficiency & Placement Outcome Analytics
  </h1>
  <p style='color:#8A8FA8;margin:4px 0 0;font-size:.95rem;'>
    Operational intelligence dashboard · U.S. Dept. of Health & Human Services
  </p>
</div>""", unsafe_allow_html=True)
st.markdown("---")

if raw_df is None:
    st.info("Upload a CSV or select the bundled dataset from the sidebar to begin.")
    st.stop()


# ── COMPUTE & RESCUE MISSION ───────────────────────────────────────────────

# 1. RESCUE THE MISSING COLUMN FROM RAW DATA (Safe Date Mapping)
try:
    raw_care_col = [c for c in raw_df.columns if 'care' in c.lower()][0]
    # Match data perfectly by Date to avoid mixing up months
    date_map = dict(zip(pd.to_datetime(raw_df['Date'], errors='coerce').dt.date, raw_df[raw_care_col]))
    df_filtered['HHS_In_Care'] = pd.to_datetime(df_filtered['Date']).dt.date.map(date_map)
except Exception as e:
    pass

# 2. FORCE RENAME ANY VARIATIONS OF THE KEY COLUMNS (Because sometimes the source data has weird names and we need to standardize them for the rest of the code to work)
rename_map = {}
for col in df_filtered.columns:
    c_low = col.lower()
    if 'care' in c_low: rename_map[col] = 'HHS_In_Care'
    elif 'discharge' in c_low: rename_map[col] = 'HHS_Discharges'
    elif 'apprehension' in c_low: rename_map[col] = 'CBP_Apprehensions'
df_filtered = df_filtered.rename(columns=rename_map)

# 3. DATE SORTING AND CLEANING (Ensures all charts are perfectly chronological and the x-axis flows left-to-right without hiccups)
if 'Date' in df_filtered.columns:
    df_filtered['Date'] = pd.to_datetime(df_filtered['Date'])
    # Sort from oldest to newest so the graph flows perfectly Left-to-Right
    df_filtered = df_filtered.sort_values('Date').reset_index(drop=True)

# 4. NUMBER CLEANING & LINE SMOOTHING (Handles any non-numeric characters and fills in gaps to make the line charts smooth and continuous)
for col in ['HHS_In_Care', 'HHS_Discharges', 'CBP_Apprehensions']:
    if col in df_filtered.columns:
        df_filtered[col] = pd.to_numeric(
            df_filtered[col].astype(str).str.replace(r'[^\d.]', '', regex=True), 
            errors='coerce'
        )
        # Interpolate bridges the gaps between dots, making the graph a smooth, continuous line!
        df_filtered[col] = df_filtered[col].interpolate(method='linear').ffill().bfill()

# Run standard KPIs
df_kpi = compute_kpis(df_filtered)

# 5. MATH RESCUE FOR DISCHARGE EFFECTIVENESS ) 
if 'HHS_In_Care' in df_kpi.columns and 'HHS_Discharges' in df_kpi.columns:
    # Ensure both columns are numeric before calculating to prevent math errors
    hhs_in_care = pd.to_numeric(df_kpi['HHS_In_Care'], errors='coerce')
    hhs_discharges = pd.to_numeric(df_kpi['HHS_Discharges'], errors='coerce')
    
    df_kpi['Discharge_Effectiveness'] = np.where(
        (hhs_in_care > 0) & hhs_in_care.notna() & hhs_discharges.notna(),
        hhs_discharges / hhs_in_care,
        np.nan 
    )

df_full = detect_bottlenecks(df_kpi, sustained_days=sustained_n)
summary = kpi_summary(df_full)

# 5. UI INSIGHTS GENERATION (Translates the raw numbers into plain-language insights for operational teams)
if 'Discharge_Effectiveness' in df_full.columns:
    # Only average the real numbers, ignore zeroes and NaNs
    eff_vals = df_full['Discharge_Effectiveness'].dropna()
    valid_eff = eff_vals[eff_vals > 0]
    summary["avg_discharge_eff"] = valid_eff.mean() if len(valid_eff) > 0 else 0.0

bn_sum  = bottleneck_stats(df_full)
monthly = get_monthly_aggregates(df_full)

# Monthly Table 
if 'Discharge_Effectiveness' in monthly.columns:
    monthly['Discharge_Effectiveness'] = monthly['Discharge_Effectiveness'].fillna(0)

# ───────────────────────────────────────────────────────────────────────────

# ── KPI CARDS ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Key Performance Indicators</div>', unsafe_allow_html=True)
c1,c2,c3,c4,c5 = st.columns(5)

def kpi_card(col, label, value, fmt, sub, color):
    if value is None or pd.isna(value):
        display_value = "N/A"
    else:
        display_value = fmt.format(value)

    col.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value" style="color:{color};">{display_value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

kpi_card(
    c1,
    "Avg Transfer Efficiency",
    summary.get("avg_transfer_eff", 0),
    "{:.1%}",
    f"Target >= {thresh_te:.0%}",
    (
        "#6BCB77"
        if summary.get("avg_transfer_eff") is not None
        and not pd.isna(summary.get("avg_transfer_eff"))
        and summary.get("avg_transfer_eff") >= thresh_te
        else "#FF6B6B"
    )
)

kpi_card(
    c2,
    "Avg Discharge Effectiveness",
    summary.get("avg_discharge_eff", 0),
    "{:.2%}",
    f"Target >= {thresh_de:.0%}",
    (
        "#6BCB77"
        if summary.get("avg_discharge_eff") is not None
        and not pd.isna(summary.get("avg_discharge_eff"))
        and summary.get("avg_discharge_eff") >= thresh_de
        else "#FF6B6B"
    )
)

kpi_card(
    c3,
    "Avg Pipeline Throughput",
    summary.get("avg_throughput", 0),
    "{:.1%}",
    f"Target >= {thresh_tp:.0%}",
    (
        "#6BCB77"
        if summary.get("avg_throughput") is not None
        and not pd.isna(summary.get("avg_throughput"))
        and summary.get("avg_throughput") >= thresh_tp
        else "#FF6B6B"
    )
)

kpi_card(
    c4,
    "Current Backlog",
    summary.get("current_backlog", 0),
    "{:,}",
    "Most recent observation",
    "#FF6B6B" if summary.get("current_backlog", 0) > 0 else "#6BCB77"
)

kpi_card(
    c5,
    "Avg Stability Score",
    summary.get("avg_stability", 0),
    "{:.1f}",
    "7-day sigma of discharges",
    "#B197FC"
)

m1,m2,m3,m4 = st.columns(4)
m1.metric("Total Apprehensions", f"{summary.get('total_apprehensions', 0):,}")
m2.metric("Total Discharges",    f"{summary.get('total_discharges', 0):,}")
m3.metric("Total CBP Transfers", f"{summary.get('total_transfers', 0):,}")
m4.metric("Peak Backlog",        f"{summary.get('peak_backlog', 0):,}",
          delta=f"on {summary.get('peak_backlog_date', 'N/A')}", delta_color="inverse")
st.markdown("---")


def safe_pct(val, decimals=1):
    if val is None or pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}%}"

# ── TABS ──────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4 = st.tabs(["Overview","KPI Trends","Bottleneck Analysis","Insights & Recommendations"])

with tab1:
    st.markdown('<div class="section-header">Pipeline Load Overview</div>', unsafe_allow_html=True)
    
    # This is a bit hacky but it allows us to keep the HHS_In_Care line in the data for accurate KPI calculations, 
    # while hiding it from the chart so the smaller lines can be seen clearly without being dwarfed by the large scale 
    # of the care population. Interpolation ensures the line is smooth and continuous even if there are gaps in the data.
    df_chart = df_full.copy()
    if 'HHS_In_Care' in df_chart.columns:
        # Hides the giant 12k line so smaller lines zoom in perfectly, without deleting the column!
        df_chart['HHS_In_Care'] = np.nan 
        
    # Plotting without the deprecated use_container_width to clear your warnings
    st.plotly_chart(pipeline_load_chart(df_chart))
    # ----------------------
    
    ca,cb_ = st.columns(2)
    with ca:
        st.markdown('<div class="section-header">Intake vs Discharge Trends</div>', unsafe_allow_html=True)
        st.plotly_chart(intake_discharge_chart(df_full))
    with cb_:
        st.markdown('<div class="section-header">Backlog Accumulation Rate</div>', unsafe_allow_html=True)
        st.plotly_chart(backlog_chart(df_full))
    st.markdown('<div class="section-header">Monthly Summary</div>', unsafe_allow_html=True)
    st.plotly_chart(monthly_summary_chart(monthly))
    st.markdown('<div class="section-header">Outcome Stability Score</div>', unsafe_allow_html=True)
    st.plotly_chart(outcome_stability_chart(df_full))
with tab2:
    st.markdown('<div class="section-header">KPI Time Series (14-Day Rolling Avg)</div>', unsafe_allow_html=True)
    st.plotly_chart(kpi_trends_chart(df_full), use_container_width=True)
    st.markdown('<div class="section-header">Monthly KPI Table</div>', unsafe_allow_html=True)
    mkpi = monthly_kpi_table(df_full)
    st.dataframe(
        mkpi[["YearMonth","Transfer_Efficiency","Discharge_Effectiveness",
              "Pipeline_Throughput","Backlog_Rate","Outcome_Stability"]]
        .rename(columns={"YearMonth":"Month","Transfer_Efficiency":"Transfer Eff.",
                         "Discharge_Effectiveness":"Discharge Eff.","Pipeline_Throughput":"Throughput",
                         "Backlog_Rate":"Backlog Rate","Outcome_Stability":"Stability"})
        .set_index("Month"),
        use_container_width=True, height=420)

with tab3:
    b1,b2,b3,b4 = st.columns(4)
    b1.metric("CBP Bottleneck Days",  f"{bn_sum.get('pct_cbp_bottleneck', 0):.1f}%")
    b2.metric("HHS Bottleneck Days",  f"{bn_sum.get('pct_hhs_bottleneck', 0):.1f}%")
    b3.metric("Sustained Periods",    f"{bn_sum.get('n_sustained_periods', 0):,} days")
    b4.metric("Critical Alerts",      f"{bn_sum.get('n_critical_alerts', 0):,} days")
    ch,cs = st.columns([3,2])
    with ch:
        st.markdown('<div class="section-header">Bottleneck Severity Heatmap</div>', unsafe_allow_html=True)
        st.plotly_chart(bottleneck_heatmap(df_full), use_container_width=True)
    with cs:
        st.markdown('<div class="section-header">Severity Distribution</div>', unsafe_allow_html=True)
        if "Severity_Score" in df_full.columns:
            fig_h = px.histogram(df_full["Severity_Score"].dropna(), nbins=20,
                                 color_discrete_sequence=["#FF922B"], template="plotly_dark")
            fig_h.update_layout(paper_bgcolor="#0E1117",plot_bgcolor="#1A1D2E",showlegend=False,
                                height=300,margin=dict(l=10,r=10,t=30,b=10))
            st.plotly_chart(fig_h, use_container_width=True)
    st.markdown('<div class="section-header">Flagged Bottleneck Periods (Top 200)</div>', unsafe_allow_html=True)
    bn_table = get_bottleneck_summary(df_full).head(200)
    if len(bn_table):
        bn_display = bn_table.copy()
        bn_display["Date"] = bn_display["Date"].dt.strftime("%Y-%m-%d")
        st.dataframe(bn_display, use_container_width=True, height=420)
    else:
        st.info("No bottleneck periods detected in the selected date range.")

with tab4:
    ci,cr = st.columns(2)
    with ci:
        st.markdown('<div class="section-header">Auto-Generated Operational Insights</div>', unsafe_allow_html=True)
        for ins in generate_insights(summary, bn_sum):
            st.markdown(f'<div class="insight-card">{ins}</div>', unsafe_allow_html=True)
    with cr:
        st.markdown('<div class="section-header">Strategic Recommendations</div>', unsafe_allow_html=True)
        for rec in generate_recommendations(summary, bn_sum):
            st.markdown(f"""<div class="rec-card">
              <b>{rec['priority']}</b> | <b>{rec['area']}</b><br>
              <span style='color:#C0C0D0'>{rec['action']}</span></div>""", unsafe_allow_html=True)
    st.markdown("---")
    exec_text = f"""**Period:** {start_date} to {end_date}

**KPIs:** Transfer Efficiency: {safe_pct(summary.get('avg_transfer_eff'))} | Discharge Effectiveness: {safe_pct(summary.get('avg_discharge_eff'), 2)} | Throughput: {safe_pct(summary.get('avg_throughput'))}
**Backlog:** Current: {summary.get('current_backlog', 0):,} | Peak: {summary.get('peak_backlog', 0):,} on {summary.get('peak_backlog_date', 'N/A')}
**Bottlenecks:** CBP: {bn_sum.get('pct_cbp_bottleneck', 0):.1f}% | HHS: {bn_sum.get('pct_hhs_bottleneck', 0):.1f}% | Sustained: {bn_sum.get('n_sustained_periods', 0):,} days | Critical Alerts: {bn_sum.get('n_critical_alerts', 0):,}"""
    st.markdown('<div class="section-header">Executive Summary Snapshot</div>', unsafe_allow_html=True)
    st.markdown(exec_text)
    st.download_button("Download Executive Summary", data=exec_text,
                       file_name="executive_summary_snapshot.md", mime="text/markdown")
    with st.expander("View Raw Processed Data"):
        st.dataframe(df_full.head(500), use_container_width=True)
        st.download_button("Download Full Processed CSV",
                           data=df_full.to_csv(index=False).encode("utf-8"),
                           file_name="uac_processed.csv", mime="text/csv")