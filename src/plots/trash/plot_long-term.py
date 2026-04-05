from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

WORKING_DIR = Path.cwd()
FILE_PATH = WORKING_DIR / "src" / "data" / "raw" / "MSCI_World_daily.csv"
SAVE_HTML_TO = WORKING_DIR / "img" / "long-term.html"

df = pd.read_csv(
    FILE_PATH, sep=",", skiprows=[1, 2], header=0, index_col=0, parse_dates=True
).rename_axis("Date")

last = df.resample("YE").last()
returns = last["Close"].pct_change().dropna().to_frame("Return")
returns.index = returns.index.year
returns = returns[returns.index < 2025]

# Number of holding periods possible
N_YEARS = returns.index.max() - returns.index.min() + 1

for h in range(N_YEARS):
    window = h + 1
    # Annualized (geometric mean)
    returns[f"Return_{h}"] = (
        (returns["Return"] + 1)
        .rolling(window=window, min_periods=window)
        .apply(lambda x: x.prod() ** (1 / window), raw=True)
        .shift(-h)
        .sub(1)
    )

returns = returns.drop(columns=["Return"])
print(returns.head())

idx = list(range(1, len(returns.columns) + 1))
returns_lower = returns.min(axis=0).values * 100
returns_upper = returns.max(axis=0).values * 100
returns_avg = returns.mean(axis=0).values * 100
assert len(idx) == len(returns_lower) == len(returns_upper) == len(returns_avg)


# %%
fig = go.Figure()

# PARAMETERS
LINE_WIDTH = 5
hovertemplate = "%{y:.2f}%"

fig.add_trace(
    go.Scatter(
        x=idx,
        y=returns_lower,
        mode="lines",
        line=dict(color="#581845", width=LINE_WIDTH),
        opacity=1,
        name="Lower Bound",
        hoverinfo="text",
        hovertemplate=hovertemplate,
        showlegend=False,
    )
)

fig.add_trace(
    go.Scatter(
        x=idx,
        y=returns_upper,
        mode="lines",
        line=dict(color="#186C6C", width=LINE_WIDTH),
        opacity=1,
        name="Upper Bound",
        hoverinfo="text",
        hovertemplate=hovertemplate,
        showlegend=False,
    )
)

fig.add_trace(
    go.Scatter(
        x=idx,
        y=returns_avg,
        mode="lines",
        line=dict(color="#E4D39D", width=LINE_WIDTH),
        opacity=1,
        name="Average Return",
        hoverinfo="text",
        hovertemplate=hovertemplate,
        showlegend=False,
    )
)

fig.update_layout(
    title="Long‑Term Saving Harnesses Regression Toward the Mean",
    xaxis=dict(
        title="Holding Period in Years",
        range=[1, idx[-1]],
        tick0=0,
        dtick=5,
        ticksuffix=" years",
        showline=True,
        linewidth=0.5,
        linecolor="black",
        zeroline=True,
        zerolinecolor="black",
        fixedrange=True,
        showgrid=False,
    ),
    yaxis=dict(
        title="Average Return (nominal) in Percent",
        ticksuffix="%",
        tickformat=".0f%",
        showline=True,
        linewidth=0.5,
        linecolor="black",
        zeroline=True,
        zerolinecolor="black",
        showgrid=True,
        gridcolor="lightgrey",
        # range=[ymin, ymax],
        fixedrange=True,
    ),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white"),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)

fig.add_annotation(
    x=1,
    y=1,
    xref="paper",
    yref="paper",
    text="Beschreibung fehlt noch<br>"
    "Data source: MSCI World Index via Yahoo Finance (Ticker: ^990100-USD-STRD)<br>"
    "Visualization by Alexander Blinn",
    showarrow=False,
    font=dict(size=8, color="black"),
    xanchor="right",
    yanchor="top",
    align="right",
    # bordercolor="black",
    # borderwidth=1,
    # borderpad=4,
    # bgcolor="white",
    # opacity=0.8,
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
