"""
Single Weekly Profile of MSCI World Index

Loads weekly-sampled MSCI World Index data, computes normalized returns,
and renders an interactive Plotly chart with additive and multiplicative modes.
Author: Alexander Blinn
"""

import locale
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# --- Locale & Style Settings ---------------------------------------------
locale.setlocale(locale.LC_TIME, "us_US.UTF-8")  # Ensure US month names

LINE_COLOR = "#000000"  # Default line color
LINE_WIDTH = 4  # Default line width
LINE_OPACITY = 1  # Default opacity

# --- File Paths -----------------------------------------------------------
WORKING_DIR = Path.cwd()
DATA_PATH = WORKING_DIR / "src" / "data" / "raw" / "MSCI_World_daily.csv"
SAVE_HTML_TO = WORKING_DIR / "img" / "single.html"

# --- Data Loading & Preparation ------------------------------------------
try:
    # Skip first two metadata rows, parse dates, set index
    df = pd.read_csv(
        DATA_PATH, sep=",", skiprows=[1, 2], header=0, index_col=0, parse_dates=True
    )
except FileNotFoundError:
    raise FileNotFoundError(f"Data file not found: {DATA_PATH}")

# Rename index for clarity and select first column only
df = df.rename_axis("Date")
if df.shape[1] > 1:
    df = df.iloc[:, [0]]
df.columns = ["Value"]

# Resample weekly and take the first value of each week
df = df.resample("W").first()

# Y-axis limits for consistency
ymin, ymax = 0, 4400


# --- Plotting Function ---------------------------------------------------
def main(df: pd.DataFrame):
    """
    Renders an interactive Plotly chart with two modes:
      1. Additive Change
      2. Multiplicative Change (log2 scale)

    Mode toggles via buttons above the chart.
    """
    fig = go.Figure()

    # Add two traces: additive and multiplicative
    for mode, col, visible in [
        ("Additive Change", "Value", True),
        ("Multiplicative Change", "Value", False),
    ]:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col],
                mode="lines",
                line=dict(color=LINE_COLOR, width=LINE_WIDTH),
                opacity=LINE_OPACITY,
                visible=visible,
                name=mode,
                hoverinfo="text",
                showlegend=False,
            )
        )

    # Define buttons for mode switching
    buttons = [
        dict(
            label="Additive Change",
            method="update",
            args=[
                {"visible": [True, False]},
                {
                    "yaxis": {
                        "title": {"text": "Absolute Return in USD"},
                        "tickprefix": "$",
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
            label="Multiplicative Change",
            method="update",
            args=[
                {"visible": [False, True]},
                {
                    "yaxis": {
                        "title": {"text": "Absolute Return in USD (log₂ scale)"},
                        "tickprefix": "$",
                        "type": "log",
                        "base": 2,
                        "showline": True,
                        "linewidth": 0.5,
                        "linecolor": "black",
                        "zeroline": False,
                        "showgrid": True,
                        "gridcolor": "lightgrey",
                        "fixedrange": True,
                        "minor": {"showgrid": True, "dtick": 0.5},
                    }
                },
            ],
        ),
    ]

    # Apply layout with buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=True,
                buttons=buttons,
                direction="right",
                pad={"r": 10, "b": 10},
                x=1,
                xanchor="right",
                y=1,
                yanchor="bottom",
            )
        ],
        xaxis=dict(
            showline=True,
            zeroline=False,
            showgrid=False,
            linewidth=0.5,
            linecolor="black",
            fixedrange=True,
        ),
        yaxis=dict(
            title="Absolute Return in USD",
            tickprefix="$",
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
        title="MSCI World Index: Weekly Profile",
    )

    # Add annotation with data source and author
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=1,
        y=1,
        xanchor="right",
        yanchor="top",
        text=(
            "Weekly closing values of the MSCI World Index, sampled weekly.<br>"
            "Additive trace shows raw index values; Multiplicative uses log₂ transformation. "
            "Switch modes with the buttons above.<br>"
            "Data source: Yahoo Finance (^990100-USD-STRD). "
            "Author: Alexander Blinn"
        ),
        showarrow=False,
        font=dict(size=8, color="black"),
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


if __name__ == "__main__":
    main(df)
