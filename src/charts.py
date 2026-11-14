"""Plotly charts for Earth Trend Detective (owner: C).

Colour encodes trend direction (orange = increasing, blue = decreasing,
grey = not significant), an orange/blue pair that stays distinguishable for
common colour-vision deficiencies. Meaning is never carried by colour alone:
every trend trace and title also states it in words.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

COLOR_INCREASING = "#D55E00"   # vermilion / orange
COLOR_DECREASING = "#0072B2"   # blue
COLOR_NOT_SIGNIFICANT = "#8C8C8C"
COLOR_RAW = "rgba(140, 140, 140, 0.45)"
COLOR_SMOOTH = "#7A7A7A"        # mid grey: readable on both light and dark themes
COLOR_ANOMALY = "rgba(140, 140, 140, 0.45)"  # neutral, so only the trend carries colour


def trend_color(result: dict) -> str:
    if not result["significant"]:
        return COLOR_NOT_SIGNIFICANT
    return COLOR_INCREASING if result["direction"] == "increasing" else COLOR_DECREASING


def trend_label(result: dict) -> str:
    """Plain-text description of the trend, so colour is never the only cue."""
    arrow = "▲" if result["direction"] == "increasing" else "▼"
    sig = "significant" if result["significant"] else "not significant"
    return f"{arrow} {result['direction']} ({sig})"


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def _decimal_years(index: pd.DatetimeIndex) -> np.ndarray:
    return (index.year + (index.month - 1) / 12).to_numpy(dtype=float)


def _ci_fan(result: dict) -> tuple[pd.Series, pd.Series]:
    """Band that opens like a fan around the trend line's midpoint.

    Lines through the trend line's midpoint with the CI's low/high slopes;
    at each time the band spans min/max of the two.
    """
    trend = result["trend_line"].dropna()
    t = _decimal_years(trend.index)
    t_mid = (t[0] + t[-1]) / 2
    y_mid = float(np.interp(t_mid, t, trend.to_numpy()))
    low = y_mid + result["ci_low"] / 10 * (t - t_mid)
    high = y_mid + result["ci_high"] / 10 * (t - t_mid)
    return (pd.Series(np.minimum(low, high), index=trend.index),
            pd.Series(np.maximum(low, high), index=trend.index))


def time_series_chart(series: pd.Series, result: dict, variable: dict, region: dict) -> go.Figure:
    unit = variable["unit"]
    color = trend_color(result)

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.09,
        row_heights=[0.55, 0.45],
        subplot_titles=("Monthly values", f"Anomalies and trend: {trend_label(result)}"),
    )

    # Top panel: raw monthly series + 12-month moving average
    fig.add_trace(go.Scatter(
        x=series.index, y=series, mode="lines", name="Monthly value",
        line=dict(color=COLOR_RAW, width=1),
        hovertemplate=f"%{{x|%b %Y}}: %{{y:.2f}} {unit}<extra></extra>",
    ), row=1, col=1)
    smooth = series.rolling(12, center=True, min_periods=6).mean()
    fig.add_trace(go.Scatter(
        x=smooth.index, y=smooth, mode="lines", name="12-month moving average",
        line=dict(color=COLOR_SMOOTH, width=3),
        hovertemplate=f"%{{x|%b %Y}}: %{{y:.2f}} {unit} (12-mo avg)<extra></extra>",
    ), row=1, col=1)

    # Bottom panel: anomalies, CI fan, trend line
    anomalies = result["anomalies"]
    fig.add_trace(go.Bar(
        x=anomalies.index, y=anomalies, name="Anomaly",
        marker_color=COLOR_ANOMALY,
        hovertemplate=f"%{{x|%b %Y}}: %{{y:+.2f}} {unit} vs normal<extra></extra>",
    ), row=2, col=1)

    low, high = _ci_fan(result)
    fig.add_trace(go.Scatter(
        x=high.index, y=high, mode="lines", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=low.index, y=low, mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor=_rgba(color, 0.28),
        name="95% confidence band", hoverinfo="skip",
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=result["trend_line"].index, y=result["trend_line"], mode="lines",
        name=f"Trend: {result['slope_per_decade']:+.2f} {unit}/decade, {trend_label(result)}",
        line=dict(color=color, width=4, dash="dash"),
        hovertemplate=f"Trend: %{{y:+.2f}} {unit}<extra></extra>",
    ), row=2, col=1)

    fig.update_yaxes(title_text=f"{variable['name']} ({unit})", row=1, col=1)
    fig.update_yaxes(title_text=f"Anomaly ({unit})", zeroline=True, row=2, col=1)
    fig.update_xaxes(title_text="Year", row=2, col=1)
    fig.update_layout(
        title=dict(text=f"{region['name']} · {variable['name']}", x=0, xanchor="left"),
        height=620, bargap=0, hovermode="x unified",
        margin=dict(l=10, r=10, t=70, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0),
    )
    return fig
