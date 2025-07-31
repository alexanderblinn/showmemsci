"""
MSCI World Daily Yearly Profiles Visualization

This script loads daily MSCI World Index data, normalizes returns per calendar year,
and produces an interactive Plotly HTML chart with both additive and multiplicative
(log2) return scales. A slider highlights a selected year's trace, and hover interactions
enhance readability.

Author: Alexander Blinn
"""

# --- Imports & Locale Setup -----------------------------------------------
import locale
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# Ensure US locale for full month names
locale.setlocale(locale.LC_TIME, "us_US.UTF-8")

# --- Highlight & Default Style Settings ----------------------------------
HIGHLIGHT_WIDTH = 4  # Line width when highlighted
HIGHLIGHT_COLOR = "#000000"  # Color when highlighted
HIGHLIGHT_OPACITY = 1.0  # Opacity when highlighted

LINE_COLOR = "#000000"  # Base line color
LINE_WIDTH = 10  # Base line width
LINE_OPACITY = 0.15  # Base opacity for non-highlighted lines

# --- Paths & Data Loading ------------------------------------------------
WORKING_DIR = Path.cwd()
DATA_PATH = WORKING_DIR / "src" / "data" / "raw" / "MSCI_World_daily.csv"
SAVE_HTML_TO = WORKING_DIR / "img" / "multiple.html"

try:
    # Skip metadata rows and parse dates
    df = pd.read_csv(
        DATA_PATH, sep=",", skiprows=[1, 2], header=0, index_col=0, parse_dates=True
    )
except FileNotFoundError:
    raise FileNotFoundError(f"Data file not found: {DATA_PATH}")

# Rename index for clarity
df = df.rename_axis("Date")

# Keep only the first column as 'Value'
if df.shape[1] > 1:
    df = df.iloc[:, [0]]
df.columns = ["Value"]

# --- Data Normalization per Calendar Year -------------------------------
# Extract year for grouping
df["Year"] = df.index.year

# Percent change from first trading day of each year
df["Normalized"] = df.groupby("Year")["Value"].transform(
    lambda x: (x - x.iloc[0]) / x.iloc[0] * 100
)

# Log2 fold change for multiplicative comparison
df["Normalized_log"] = df.groupby("Year")["Value"].transform(
    lambda x: np.log2(x / x.iloc[0])
)

# Keep only normalized columns
df = df[["Normalized", "Normalized_log"]]


# --- Plotting Function --------------------------------------------------
def main(df: pd.DataFrame):
    """
    Generate an interactive Plotly chart showing yearly return profiles.

    - Additive Change: Percent change from Jan 1 (visible by default)
    - Multiplicative Change: Log2 fold change (hidden by default)
    - Slider highlights a single year across both modes.
    """
    # Work on a copy and sort by date
    df = df.copy()
    df.sort_index(inplace=True)

    years = sorted(df.index.year.unique())
    n_years = len(years)
    total_traces = 2 * n_years

    # Y-axis limits for consistency
    ymin, ymax = -110, 60

    fig = go.Figure()

    # Add trace for each year in both additive & multiplicative modes
    for mode, col, visible in [
        ("Additive Change", "Normalized", True),
        ("Multiplicative Change", "Normalized_log", False),
    ]:
        for year in years:
            df_year = df[df.index.year == year]
            x_vals = df_year.index.dayofyear  # Actual day of year
            y_vals = df_year[col]

            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines",
                    line=dict(color=LINE_COLOR, width=LINE_WIDTH),
                    opacity=LINE_OPACITY,
                    visible=visible,
                    name=str(year),
                    text=[
                        f"Date: {d.strftime('%d %B %Y')}<br>"
                        + (
                            f"{mode}: {v:.2f}%"
                            if mode == "Additive Change"
                            else f"{mode}: {v:.2f}"
                        )
                        for d, v in zip(df_year.index, y_vals)
                    ],
                    hoverinfo="text",
                    showlegend=False,
                )
            )

    # --- Toggle Buttons ----------------------------------------------------
    buttons = [
        dict(
            label="Additive Change (Linear Scale)",
            method="update",
            args=[
                {"visible": [True] * n_years + [False] * n_years},
                {
                    "yaxis": {
                        "title": {"text": "Percent Change from January 1"},
                        "ticksuffix": "%",
                        "range": [ymin, ymax],
                        "fixedrange": True,
                        "showgrid": True,
                        "gridcolor": "lightgrey",
                        "zeroline": True,
                        "zerolinecolor": "black",
                        "showline": True,
                        "linecolor": "black",
                        "linewidth": 0.5,
                    }
                },
            ],
        ),
        dict(
            label="Multiplicative Change (Log₂ Scale)",
            method="update",
            args=[
                {"visible": [False] * n_years + [True] * n_years},
                {
                    "yaxis": {
                        "title": {"text": "Log₂ Fold Change from January 1"},
                        "range": [ymin / 100, ymax / 100],
                        "fixedrange": True,
                        "showgrid": True,
                        "gridcolor": "lightgrey",
                        "zeroline": True,
                        "zerolinecolor": "black",
                        "showline": True,
                        "linecolor": "black",
                        "linewidth": 0.5,
                    }
                },
            ],
        ),
    ]

    # --- Slider Steps to Highlight Year -----------------------------------
    steps = []
    for i, year in enumerate(years):
        highlight_idxs = [i, i + n_years]
        widths = [
            HIGHLIGHT_WIDTH if j in highlight_idxs else LINE_WIDTH
            for j in range(total_traces)
        ]
        colors = [
            HIGHLIGHT_COLOR if j in highlight_idxs else LINE_COLOR
            for j in range(total_traces)
        ]
        opacities = [
            HIGHLIGHT_OPACITY if j in highlight_idxs else LINE_OPACITY
            for j in range(total_traces)
        ]

        steps.append(
            dict(
                method="restyle",
                label=str(year),
                args=[
                    {"line.width": widths, "line.color": colors, "opacity": opacities},
                    list(range(total_traces)),
                ],
            )
        )

    slider = dict(
        active=0,
        currentvalue={"prefix": "Highlighted year: "},
        pad={"t": 50},
        steps=steps,
    )

    # --- Final Layout & Interactivity -------------------------------------
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
        sliders=[slider],
        xaxis=dict(
            range=[1, 366],
            tick0=0,
            dtick=30,
            ticksuffix=" days",
            fixedrange=True,
            showline=True,
            linewidth=0.5,
            linecolor="black",
            zeroline=True,
            zerolinecolor="black",
            showgrid=False,
        ),
        yaxis=dict(
            title="Percent Change from January 1",  # default y-axis label
            ticksuffix="%",
            tickformat=".0f%",
            fixedrange=True,
            showgrid=True,
            gridcolor="lightgrey",
            zeroline=True,
            zerolinecolor="black",
            showline=True,
            linecolor="black",
            linewidth=0.5,
            range=[ymin, ymax],
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title="MSCI World Daily Yearly Profiles",
    )

    # Annotation: data source & credits
    fig.add_annotation(
        x=1,
        y=1,
        xref="paper",
        yref="paper",
        text=(
            "Daily return profiles of the MSCI World Index by calendar year, "
            "showing both cumulative percent change and log₂ fold change.<br>"
            "Toggle between linear and log₂ scales with the buttons above, "
            "and use the slider to highlight a specific year's performance.<br>"
            "Data: MSCI World Index (^990100-USD-STRD) from Yahoo Finance. "
            "Author: Alexander Blinn"
        ),
        showarrow=False,
        font=dict(size=8, color="black"),
        xanchor="right",
        yanchor="top",
        align="right",
    )

    # Generate HTML and inject custom JS for hover persistence
    html_str = pio.to_html(fig, full_html=True, include_plotlyjs="cdn", div_id="myPlot")
    DIV_ID = "myPlot"

    hover_js = f"""
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        var plotDiv = document.getElementById('{DIV_ID}');

        // initial highlight of slider’s default year
        var slider = plotDiv.layout.sliders[0];
        var activeIdx = slider.active;
        var activeYear = slider.steps[activeIdx].label;
        plotDiv.data.forEach(function(trace, idx) {{
            if (trace.name === activeYear) {{
                Plotly.restyle(plotDiv, {{
                    'line.width': {HIGHLIGHT_WIDTH},
                    'line.color': '{HIGHLIGHT_COLOR}',
                    'opacity': {HIGHLIGHT_OPACITY}
                }}, [idx]);
            }}
        }});

        // on hover: always highlight
        plotDiv.on('plotly_hover', function(eventData) {{
            var i = eventData.points[0].curveNumber;
            Plotly.restyle(plotDiv, {{
                'line.width': {HIGHLIGHT_WIDTH},
                'line.color': '{HIGHLIGHT_COLOR}',
                'opacity': {HIGHLIGHT_OPACITY}
            }}, [i]);
        }});

        // on unhover: reset only if not slider-selected
        plotDiv.on('plotly_unhover', function(eventData) {{
            var i = eventData.points[0].curveNumber;
            var slider = plotDiv.layout.sliders[0];
            var activeYear = slider.steps[slider.active].label;
            var traceYear = plotDiv.data[i].name;
            if (traceYear === activeYear) return;  // keep highlighted
            Plotly.restyle(plotDiv, {{
                'line.width': {LINE_WIDTH},
                'line.color': '{LINE_COLOR}',
                'opacity': {LINE_OPACITY}
            }}, [i]);
        }});
    }});
    </script>
    """

    html_out = html_str.replace("</body>", hover_js + "\n</body>")
    SAVE_HTML_TO.write_text(html_out, encoding="utf-8")

    # # Export to HTML
    # fig.write_html(
    #     SAVE_HTML_TO,
    #     config={
    #         "displayModeBar": True,  # set to False to hide the toolbar completely
    #         "modeBarButtonsToRemove": ["select2d", "lasso2d"],  # remove selection tools
    #         "scrollZoom": False,  # disable scroll-to-zoom
    #         "doubleClick": "reset",  # customize double-click behavior (e.g., reset axes)
    #         "displaylogo": False,  # hide the Plotly logo
    #     },
    # )


if __name__ == "__main__":
    main(df)
