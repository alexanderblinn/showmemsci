from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- 1) Define color scales (renamed for clarity) ---
COLOR_LIST = [
    "#581845",
    "#900C3F",
    "#CD5C5C",
    "#E9967A",
    "#E4D39D",
    "#8ACBB7",
    "#0C888A",
    "#124C4C",
]

# Linear interpolation for average returns
positions_avg = np.linspace(0, 1, len(COLOR_LIST))
COLORSCALE_AVG = list(zip(positions_avg, COLOR_LIST))

# Exponential interpolation for total returns
positions_tot = np.geomspace(1, 100, len(COLOR_LIST))
positions_tot = (positions_tot - positions_tot.min()) / (
    positions_tot.max() - positions_tot.min()
)
COLORSCALE_TOT = list(zip(positions_tot, COLOR_LIST))

# --- 2) Load & prepare data ---
WORKING_DIR = Path.cwd()
FILE_PATH = WORKING_DIR / "src" / "data" / "raw" / "MSCI_World_daily.csv"
SAVE_HTML_TO = WORKING_DIR / "img" / "heatmap.html"

df = pd.read_csv(
    FILE_PATH, sep=",", skiprows=[1, 2], header=0, index_col=0, parse_dates=True
).rename_axis("Date")

last = df.resample("YE").last()
returns = last["Close"].pct_change().dropna().to_frame("Return")
returns.index = returns.index.year
returns = returns[returns.index < 2025]

# Number of holding periods possible
N_YEARS = returns.index.max() - returns.index.min() + 1

# --- 3) Compute average (annualized) & total returns ---
returns_avg = returns.copy()
returns_tot = returns.copy()
one_plus = returns["Return"] + 1

for h in range(N_YEARS):
    window = h + 1
    # Annualized (geometric mean)
    returns_avg[f"Return_{h}"] = (
        one_plus.rolling(window=window, min_periods=window)
        .apply(lambda x: x.prod() ** (1 / window), raw=True)
        .shift(-h)
        .sub(1)
    )
    # Total cumulative return
    returns_tot[f"Return_{h}"] = (
        one_plus.rolling(window=window, min_periods=window)
        .apply(lambda x: x.prod(), raw=True)
        .shift(-h)
        .sub(1)
    )

# --- 4) Build axes & text matrices ---
holding_cols = [c for c in returns_avg.columns if c.startswith("Return_")]
x_years = [int(c.split("_")[1]) + 1 for c in holding_cols]
y_years = returns_avg.index.tolist()[::-1]  # newest at top

# Z and text for average returns
z_avg = returns_avg[holding_cols].values[::-1, :]
text_avg = np.where(np.isnan(z_avg), "", (z_avg * 100).round(1).astype(str) + "%")

# Z and text for total returns
z_tot = returns_tot[holding_cols].values[::-1, :]
text_tot = np.where(np.isnan(z_tot), "", (z_tot * 100).round(1).astype(str) + "%")

# --- 5) Create heatmap traces ---
trace_avg = go.Heatmap(
    z=z_avg,
    x=x_years,
    y=y_years,
    colorscale=COLORSCALE_AVG,
    zmin=np.nanmin(z_avg),
    zmax=np.nanmax(z_avg),
    zmid=0,
    text=text_avg,
    texttemplate="%{text}",
    hovertemplate="Year %{y}<br>Holding %{x} yr<br>Avg Return %{z:.2%}<extra></extra>",
    visible=True,
    showscale=False,
)
trace_tot = go.Heatmap(
    z=z_tot,
    x=x_years,
    y=y_years,
    colorscale=COLORSCALE_TOT,
    zmin=np.nanmin(z_tot),
    zmax=np.nanmax(z_tot),
    zmid=0,
    text=text_tot,
    texttemplate="%{text}",
    hovertemplate="Year %{y}<br>Holding %{x} yr<br>Total Return %{z:.2%}<extra></extra>",
    visible=False,
    showscale=False,
)

# --- 6) Figure with updatemenus ---
fig = go.Figure(data=[trace_avg, trace_tot])

(
    fig.update_layout(
        title="MSCI World: Returns Heatmap by Holding Period",
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=1,
                xanchor="right",
                y=1,
                yanchor="bottom",
                pad=dict(r=10, b=10),
                showactive=True,
                buttons=[
                    dict(
                        label="Average Return",
                        method="update",
                        args=[
                            {"visible": [True, False]},
                        ],
                    ),
                    dict(
                        label="Total Return",
                        method="update",
                        args=[
                            {"visible": [False, True]},
                        ],
                    ),
                ],
            )
        ],
        xaxis=dict(
            title="Holding Period in Years",
            tickmode="linear",
            dtick=1,
            tick0=min(x_years),
            showgrid=False,
            ticks="outside",
            tickson="boundaries",
            ticklen=8,
        ),
        yaxis=dict(
            title="Year of Initial Investment",
            tickmode="linear",
            dtick=1,
            tick0=min(y_years),
            showgrid=False,
            ticks="outside",
            tickson="boundaries",
            ticklen=8,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    ),
)
# Annotation (wie zuvor)
fig.add_annotation(
    x=1,
    y=1,
    xref="paper",
    yref="paper",
    text=(
        "Return triangle of MSCI World Index by start year and holding span in years;<br>"
        "toggle between average annualized and total returns;<br>"
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
        # "modeBarButtonsToRemove": ["select2d", "lasso2d"],  # remove selection tools
        "scrollZoom": False,  # disable scroll-to-zoom
        "doubleClick": "reset",  # customize double-click behavior (e.g., reset axes)
        "displaylogo": False,  # hide the Plotly logo
    },
)
