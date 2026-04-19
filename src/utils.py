"""
src/utils.py
------------
Shared helper utilities used across the project.
"""

import pandas as pd
import numpy as np
import os


def ensure_dir(path: str) -> str:
    """Create directory if it does not exist and return the path."""
    os.makedirs(path, exist_ok=True)
    return path


def pct_change_label(current: float, previous: float) -> str:
    """Return an up/down percentage change string."""
    if previous == 0 or pd.isna(previous):
        return "N/A"

    delta = (current - previous) / abs(previous) * 100
    arrow = "up" if delta >= 0 else "down"

    return f"{arrow} {abs(delta):.1f}%"


def color_severity(val: float) -> str:
    """Return a hex colour string based on severity 0-10."""
    if val >= 7:
        return "#FF6B6B"
    elif val >= 4:
        return "#FF922B"
    elif val >= 2:
        return "#FFD93D"
    return "#6BCB77"


def safe_pct(val, decimals=1):
    """Safely format percentages."""
    if val is None or pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}%}"


def generate_insights(stats: dict, bn_stats: dict) -> list:
    insights = []

    te = stats.get("avg_transfer_eff")
    de = stats.get("avg_discharge_eff")
    cb = stats.get("current_backlog", 0)
    pk = stats.get("peak_backlog", 0)

    # Transfer Efficiency Insights
    if te is None or pd.isna(te):
        insights.append(
            "Transfer Efficiency could not be calculated for the selected period due to insufficient valid CBP transfer/custody data."
        )
    elif te < 0.5:
        insights.append(
            f"Transfer Efficiency is critically low ({safe_pct(te)}). CBP is apprehending children significantly faster than they can be transferred to HHS care."
        )
    elif te < 0.8:
        insights.append(
            f"Transfer Efficiency ({safe_pct(te)}) is below the 80% target. Periodic surges are stressing the CBP-to-HHS transfer pipeline."
        )
    else:
        insights.append(
            f"Transfer Efficiency ({safe_pct(te)}) meets the >=80% benchmark. CBP-to-HHS handoffs are operating well."
        )

    # Discharge Effectiveness Insights
    if de is None or pd.isna(de):
        insights.append(
            "Discharge Effectiveness could not be calculated for the selected period due to insufficient valid HHS care/discharge data."
        )
    elif de < 0.05:
        insights.append(
            f"Discharge Effectiveness is very low ({safe_pct(de, 2)}). Only a small fraction of children in HHS care are being discharged daily."
        )
    elif de < 0.10:
        insights.append(
            f"Discharge Effectiveness ({safe_pct(de, 2)}) is below 10%. HHS care capacity is accumulating faster than sponsor placements are finalised."
        )
    else:
        insights.append(
            f"Discharge Effectiveness ({safe_pct(de, 2)}) is healthy. Sponsor placement processes are operating at an acceptable rate."
        )

    # Backlog Insights
    if cb > 500:
        insights.append(
            f"Current backlog is {cb:,}. Peak backlog reached {pk:,} on {stats.get('peak_backlog_date', 'N/A')}. Immediate operational intervention is recommended."
        )
    elif cb > 0:
        insights.append(
            f"Active backlog of {cb:,} children. Monitor daily to prevent escalation."
        )
    else:
        insights.append(
            f"Backlog is neutral or negative ({cb:,}), indicating throughput is keeping pace with intake."
        )

    # Bottleneck Insights
    pct_cbp = bn_stats.get("pct_cbp_bottleneck", 0)
    pct_hhs = bn_stats.get("pct_hhs_bottleneck", 0)
    n_sus = bn_stats.get("n_sustained_periods", 0)
    n_crit = bn_stats.get("n_critical_alerts", 0)

    insights.append(
        f"CBP bottlenecks occurred on {pct_cbp:.1f}% of days; HHS bottlenecks on {pct_hhs:.1f}% of days."
    )

    if n_sus > 30:
        insights.append(
            f"{n_sus} days had sustained (>3-day) bottlenecks, pointing to systemic rather than episodic pressure."
        )

    if n_crit > 0:
        insights.append(
            f"{n_crit} days triggered critical backlog alerts (top 10th percentile)."
        )

    return insights


def generate_recommendations(stats: dict, bn_stats: dict) -> list:
    recs = []

    te = stats.get("avg_transfer_eff")
    de = stats.get("avg_discharge_eff")
    tp = stats.get("avg_throughput")
    cb = stats.get("current_backlog", 0)

    if te is not None and not pd.isna(te) and te < 0.7:
        recs.append({
            "priority": "High",
            "area": "CBP to HHS Transfer",
            "action": "Increase transfer staffing and streamline inter-agency handoff protocols. Consider establishing a dedicated rapid-transfer team for surge periods."
        })

    if de is not None and not pd.isna(de) and de < 0.08:
        recs.append({
            "priority": "High",
            "area": "HHS Discharge / Sponsor Placement",
            "action": "Expand sponsor vetting capacity. Introduce concurrent background-check processing and recruit additional case managers."
        })

    if cb > 200:
        recs.append({
            "priority": "High",
            "area": "Backlog Management",
            "action": "Activate emergency bed capacity and temporary shelter agreements. Implement real-time backlog dashboards for field supervisors."
        })

    if tp is not None and not pd.isna(tp) and tp < 0.4:
        recs.append({
            "priority": "Medium",
            "area": "Pipeline Throughput",
            "action": "Audit end-to-end pipeline delays. Identify the single largest lag between CBP intake and final discharge."
        })

    if bn_stats.get("pct_cbp_bottleneck", 0) > 40:
        recs.append({
            "priority": "Medium",
            "area": "CBP Capacity Planning",
            "action": "Introduce predictive demand modelling for CBP intake. Pre-position HHS intake capacity ahead of seasonal surge periods."
        })

    recs.append({
        "priority": "Low",
        "area": "Data Quality",
        "action": "Ensure daily data submissions from CBP and HHS field offices are complete and timely."
    })

    recs.append({
        "priority": "Low",
        "area": "Monitoring",
        "action": "Implement weekly KPI review meetings with field leadership using this dashboard as the operational record of truth."
    })

    return recs