"""
src/visualization.py
---------------------
All Plotly chart factory functions for the Streamlit dashboard.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

C = {
    "cyan":    "#00D4FF",
    "coral":   "#FF6B6B",
    "gold":    "#FFD93D",
    "green":   "#6BCB77",
    "orange":  "#FF922B",
    "purple":  "#B197FC",
    "bg":      "#0E1117",
    "surface": "#1A1D2E",
    "grid":    "#2D3150",
    "text":    "#FAFAFA",
    "subtext": "#8A8FA8",
}

_LAYOUT_BASE = dict(
    template="plotly_dark",
    paper_bgcolor=C["bg"],
    plot_bgcolor=C["surface"],
    font=dict(family="Inter, Arial, sans-serif", color=C["text"]),
    margin=dict(l=20, r=20, t=50, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=C["grid"], borderwidth=1),
    xaxis=dict(gridcolor=C["grid"], linecolor=C["grid"]),
    yaxis=dict(gridcolor=C["grid"], linecolor=C["grid"]),
)


def _apply_base(fig, title=""):
    fig.update_layout(title=dict(text=title, font=dict(size=16)), **_LAYOUT_BASE)
    return fig


def pipeline_load_chart(df):
    fig = go.Figure()
    for col, name, color, dash in [
        ("CBP_Apprehensions","CBP Apprehensions",C["cyan"],"solid"),
        ("CBP_In_Custody","In CBP Custody",C["orange"],"dot"),
        ("HHS_In_Care","In HHS Care",C["gold"],"solid"),
        ("HHS_Discharges","HHS Discharges",C["green"],"solid"),
    ]:
        fig.add_trace(go.Scatter(x=df["Date"], y=df[col], name=name, mode="lines",
            line=dict(color=color, width=2, dash=dash),
            hovertemplate=f"<b>{name}</b><br>Date: %{{x|%b %d, %Y}}<br>Count: %{{y:,.0f}}<extra></extra>"))
    return _apply_base(fig, "\U0001f4ca Care Pipeline Load Over Time")


def intake_discharge_chart(df):
    roll = df.set_index("Date")[["CBP_Apprehensions","HHS_Discharges"]].rolling("7D").mean().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"],y=df["CBP_Apprehensions"],name="Daily Apprehensions",
        mode="lines",line=dict(color=C["coral"],width=1.2),opacity=0.35))
    fig.add_trace(go.Scatter(x=roll["Date"],y=roll["CBP_Apprehensions"],name="7-Day Avg Apprehensions",
        mode="lines",line=dict(color=C["coral"],width=2.5)))
    fig.add_trace(go.Scatter(x=df["Date"],y=df["HHS_Discharges"],name="Daily Discharges",
        mode="lines",line=dict(color=C["green"],width=1.2),opacity=0.35))
    fig.add_trace(go.Scatter(x=roll["Date"],y=roll["HHS_Discharges"],name="7-Day Avg Discharges",
        mode="lines",line=dict(color=C["green"],width=2.5)))
    fig.add_trace(go.Scatter(
        x=list(df["Date"])+list(df["Date"][::-1]),
        y=list(df["CBP_Apprehensions"])+list(df["HHS_Discharges"][::-1]),
        fill="toself",fillcolor="rgba(255,107,107,0.07)",
        line=dict(color="rgba(0,0,0,0)"),name="Gap (Backlog)"))
    fig.update_layout(hovermode="x unified", height=380)
    return _apply_base(fig, "\U0001f4c8 Intake vs Discharge Trends (7-Day Rolling Avg)")


def kpi_trends_chart(df):
    kpis = [
        ("Transfer_Efficiency","Transfer Efficiency",C["cyan"]),
        ("Discharge_Effectiveness","Discharge Effectiveness",C["green"]),
        ("Pipeline_Throughput","Pipeline Throughput",C["gold"]),
    ]
    fig = make_subplots(rows=3,cols=1,shared_xaxes=True,
        subplot_titles=[k[1] for k in kpis],vertical_spacing=0.07)
    for i,(col,label,color) in enumerate(kpis,1):
        roll = df[col].rolling(14,min_periods=2).mean()
        fig.add_trace(go.Scatter(x=df["Date"],y=df[col],name=f"{label} (raw)",
            mode="lines",line=dict(color=color,width=1),opacity=0.3),row=i,col=1)
        fig.add_trace(go.Scatter(x=df["Date"],y=roll,name=f"{label} (14-day avg)",
            mode="lines",line=dict(color=color,width=2.5)),row=i,col=1)
    fig.update_layout(height=600,hovermode="x unified",
        title=dict(text="\U0001f4c9 KPI Trend Lines (14-Day Rolling Average)",font=dict(size=16)),
        **{k:v for k,v in _LAYOUT_BASE.items() if k not in ("xaxis","yaxis")})
    fig.update_xaxes(gridcolor=C["grid"])
    fig.update_yaxes(gridcolor=C["grid"])
    return fig


def backlog_chart(df):
    fig = go.Figure()
    pos = df["Backlog_Rate"] >= 0
    fig.add_trace(go.Bar(x=df.loc[pos,"Date"],y=df.loc[pos,"Backlog_Rate"],
        name="Backlog (Positive)",marker_color=C["coral"],opacity=0.8))
    fig.add_trace(go.Bar(x=df.loc[~pos,"Date"],y=df.loc[~pos,"Backlog_Rate"],
        name="Surplus (Negative)",marker_color=C["green"],opacity=0.8))
    roll = df.set_index("Date")["Backlog_Rate"].rolling("30D").mean().reset_index()
    fig.add_trace(go.Scatter(x=roll["Date"],y=roll["Backlog_Rate"],name="30-Day Trend",
        mode="lines",line=dict(color=C["gold"],width=2.5,dash="dot")))
    fig.add_hline(y=0,line_color=C["subtext"],line_dash="solid",line_width=1)
    fig.update_layout(barmode="overlay",height=360)
    return _apply_base(fig,"\U0001f534 Backlog Accumulation Rate (Apprehensions − Discharges)")


def bottleneck_heatmap(df):
    heat = df.groupby(["Year","Month"])["Severity_Score"].mean().reset_index()
    pivot = heat.pivot(index="Month",columns="Year",values="Severity_Score").fillna(0)
    month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    pivot = pivot.reindex([m for m in range(1,13) if m in pivot.index])
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(c) for c in pivot.columns],
        y=[month_labels[m-1] for m in pivot.index],
        colorscale=[[0,"#1A1D2E"],[0.25,"#2D3150"],[0.5,"#FF922B"],[0.75,"#FF6B6B"],[1,"#C0392B"]],
        colorbar=dict(title="Severity"),
        hovertemplate="Year: %{x}<br>Month: %{y}<br>Avg Severity: %{z:.2f}<extra></extra>",
    ))
    fig.update_layout(height=380)
    return _apply_base(fig,"\U0001f321\ufe0f Bottleneck Severity Heatmap (Monthly Avg)")


def outcome_stability_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"],y=df["Outcome_Stability"],
        name="7-Day Rolling Std Dev",mode="lines",
        line=dict(color=C["purple"],width=2),fill="tozeroy",
        fillcolor="rgba(177,151,252,0.12)"))
    fig.update_layout(height=300)
    return _apply_base(fig,"\U0001f4d0 Outcome Stability Score (7-Day \u03c3 of Discharges)")


def monthly_summary_chart(monthly_df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly_df["YearMonth"],y=monthly_df["CBP_Apprehensions"],
        name="Apprehensions",marker_color=C["coral"]))
    fig.add_trace(go.Bar(x=monthly_df["YearMonth"],y=monthly_df["HHS_Discharges"],
        name="Discharges",marker_color=C["green"]))
    fig.add_trace(go.Bar(x=monthly_df["YearMonth"],y=monthly_df["CBP_Transfers_Out"],
        name="CBP Transfers Out",marker_color=C["cyan"]))
    fig.update_layout(barmode="group",height=380,xaxis_tickangle=-45)
    return _apply_base(fig,"\U0001f4c5 Monthly Summary: Apprehensions vs Transfers vs Discharges")