import locale
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# set US locale for month names if needed
locale.setlocale(locale.LC_TIME, "us_US.UTF-8")

# Highlight settings (unused for bars but kept for consistency)
HIGHLIGHT_WIDTH = 4
HIGHLIGHT_COLOR = "#000000"
HIGHLIGHT_OPACITY = 1.0

# Default (standard) settings
LINE_COLOR = "#000000"
LINE_WIDTH = 10
LINE_OPACITY = 0.15

# --- 1) Daten laden ---
WORKING_DIR = Path.cwd()
FILE_PATH = Path(WORKING_DIR, "src", "data", "raw", "MSCI_World_daily.csv")
SAVE_HTML_TO = WORKING_DIR / "img" / "returns-two.html"


df = pd.read_csv(
    FILE_PATH, sep=",", skiprows=[1, 2], header=0, index_col=0, parse_dates=True
)
df = df.rename_axis("Date")

# Jahresendkurse und Renditen
df_yearly = df.resample("YE").last()
returns = df_yearly["Close"].pct_change().dropna().to_frame("pct")
returns["log2"] = np.log2(1 + returns["pct"])
returns.index = returns.index.year
returns = returns[returns.index < 2025]

# Farben pro Modus
colors_pct = ["#124C4C" if v >= 0 else "#581845" for v in returns["pct"]]
colors_log2 = ["#124C4C" if v >= 0 else "#581845" for v in returns["log2"]]

# Gemeinsame y-Range
ymin = -0.85
ymax = 0.60

# --- 3) Bar-Plot mit Buttons ---
fig = go.Figure()

# 0) Null-Linie als Shape unter den Bars
fig.add_shape(
    dict(
        type="line",
        xref="paper",
        x0=0,
        x1=1,
        yref="y",
        y0=0,
        y1=0,
        line=dict(color="black", width=1),
        layer="below",
    )
)

# Additive (pct) bars
fig.add_trace(
    go.Bar(
        x=returns.index.astype(str),
        y=returns["pct"],
        marker_color=colors_pct,
        visible=True,
        name="Additive Change",
        hovertemplate="Year: %{x}<br>Return: %{y:.2%}<extra></extra>",
    )
)
# Multiplicative (log₂) bars
fig.add_trace(
    go.Bar(
        x=returns.index.astype(str),
        y=returns["log2"],
        marker_color=colors_log2,
        visible=False,
        name="Multiplicative Change",
        hovertemplate="Year: %{x}<br>Log₂ Return: %{y:.2f}<extra></extra>",
    )
)

# Buttons
buttons = [
    dict(
        label="Additive Change (Linear Scale)",
        method="update",
        args=[
            {"visible": [True, False]},
            {
                "yaxis": {
                    "title": {"text": "Annual Return (%)"},
                    "tickformat": ".0%",
                    "showline": True,
                    "linewidth": 0.5,
                    "linecolor": "black",
                    "zeroline": False,
                    "showgrid": True,
                    "gridcolor": "lightgrey",
                    "range": [ymin, ymax],
                    "fixedrange": True,
                }
            },
        ],
    ),
    dict(
        label="Multiplicative Change (Log₂ Scale)",
        method="update",
        args=[
            {"visible": [False, True]},
            {
                "yaxis": {
                    "title": {"text": "Annual Log₂ Return"},
                    "tickformat": ".2f",
                    "showline": True,
                    "linewidth": 0.5,
                    "linecolor": "black",
                    "zeroline": False,
                    "showgrid": True,
                    "gridcolor": "lightgrey",
                    "range": [ymin, ymax],
                    "fixedrange": True,
                }
            },
        ],
    ),
]

fig.update_layout(
    title="Annual Returns of the MSCI World Index",
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            showactive=True,
            buttons=buttons,
            pad=dict(r=10, b=10),
            x=1,
            xanchor="right",
            y=1,
            yanchor="bottom",
        )
    ],
    xaxis=dict(
        title="Year",
        tickangle=-90,
        tickmode="array",
        showline=True,
        linewidth=0.5,
        linecolor="black",
        zeroline=False,
        fixedrange=True,
    ),
    yaxis=dict(
        title="Annual Return (%)",
        tickformat=".0%",
        showline=True,
        linewidth=0.5,
        linecolor="black",
        zeroline=False,
        showgrid=True,
        gridcolor="lightgrey",
        range=[ymin, ymax],
        fixedrange=True,
    ),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)

# Annotation (wie zuvor)
fig.add_annotation(
    x=1,
    y=1,
    xref="paper",
    yref="paper",
    text=(
        "Annual returns of the MSCI World Index per calendar year.<br>"
        "Data source: MSCI World Index via Yahoo Finance (Ticker: ^990100-USD-STRD)<br>"
        "Visualization by Alexander Blinn"
    ),
    showarrow=False,
    font=dict(size=8, color="black"),
    xanchor="right",
    yanchor="top",
    align="right",
)

# Export to HTML
fig.write_html(
    SAVE_HTML_TO,
    config={
        "displayModeBar": True,  # set to False to hide the toolbar completely
        "modeBarButtonsToRemove": ["select2d", "lasso2d"],  # remove selection tools
        "scrollZoom": False,  # disable scroll-to-zoom
        "doubleClick": "reset",  # customize double-click behavior (e.g., reset axes)
        "displaylogo": False,  # hide the Plotly logo
    },
)
