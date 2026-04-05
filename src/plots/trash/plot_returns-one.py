from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# %%
MSCI_WORLD_CONTEXT = {
    1970: "Entering the year in recession after the late‑'60s slowdown, leading to a weak stock market",
    1971: "Aggressive monetary easing under President Nixon fuels a strong global rebound",
    1972: "Economic boom peaks – low unemployment and surging earnings drive exuberant gains",
    1973: "Bretton Woods collapse and OPEC embargo trigger stagflation fears and market downturn",
    1974: "Deep stagflation; double‑digit inflation and steep equity losses dominate the year",
    1975: "Post‑crisis rebound as the 1973‑75 recession ends and economies begin recovering",
    1976: "Continued recovery despite persistent inflation; expansion resumes amid price pressures",
    1977: "Growth slows under renewed stagflation concerns, keeping equity gains modest",
    1978: "Brief market resurgence as global economies stabilize ahead of the second oil shock",
    1979: "Second oil crisis (Iran) drives energy prices higher, stoking worldwide inflation",
    1980: "Volcker’s tight policy battles inflation; stocks hold as expectations peak",
    1981: "Deepening 'Volcker recession' and record rates weigh on global markets",
    1982: "Inflation breaks, recession ends, and a new bull market dawns as pressures ease",
    1983: "Robust recovery – falling inflation and global growth boost investor confidence",
    1984: "Expansion persists, but rising rates and deficit worries temper enthusiasm",
    1985: "Disinflation and weaker dollar ignite a mid‑'80s bull surge in global equities",
    1986: "Oil price collapse plus Japan’s asset boom fuel another year of outsized gains",
    1987: "'Black Monday' crash jolts markets, though earlier strength keeps year positive",
    1988: "Markets rebound from 1987 shock as global growth resumes and fears subside",
    1989: "Cold War ends, Berlin Wall falls, and Japan’s bubble lifts equities to new highs",
    1990: "Iraq–Kuwait conflict and oil spike spark global sell‑off and recession fears",
    1991: "Gulf War victory and recession end trigger relief rally in global equities",
    1992: "Jobless U.S. recovery and Europe’s ERM crisis keep markets subdued",
    1993: "Low rates and reviving global economy push stocks higher again",
    1994: "Aggressive Fed hikes cause bond‑market 'massacre' and cap equity advances",
    1995: "Soft‑landing economy and tech profit boom power a strong rally",
    1996: "Greenspan warns of 'irrational exuberance' amid accelerating market ascent",
    1997: "Asian Financial Crisis hits EM stocks; Western markets stay largely resilient",
    1998: "Russia default and LTCM near‑collapse roil markets until Fed interventions",
    1999: "Dot‑com frenzy drives technology stocks and indices to record peaks",
    2000: "Dot‑com bubble bursts, marking the start of a global downturn",
    2001: "Global recession and 9/11 attacks cause sharp plunge and disruption",
    2002: "Accounting scandals and sluggish recovery prolong the bear market",
    2003: "Swift Iraq War end and ultra‑low rates spark a powerful rebound",
    2004: "Steady growth in low‑rate environment sustains rally amid rising commodities",
    2005: "Record oil prices and continued Fed hikes limit market gains",
    2006: "Global boom led by emerging giants drives equities higher",
    2007: "Credit‑fueled optimism peaks; housing strains surface late in year",
    2008: "Global Financial Crisis – bank failures trigger worldwide market collapse",
    2009: "Massive fiscal and monetary stimulus spurs sharp rebound from crisis lows",
    2010: "Recovery continues, but Europe’s debt crisis injects volatility",
    2011: "Eurozone turmoil and U.S. credit downgrade ignite market swings",
    2012: "ECB 'whatever it takes' pledge calms euro crisis and restores confidence",
    2013: "QE and synchronized growth power an exceptional year for equities",
    2014: "Modest gains as Fed ends QE and oil prices collapse late in year",
    2015: "China growth scare and first Fed hike in decade leave equities flat",
    2016: "Brexit and U.S. election shocks raise volatility, but markets grind higher",
    2017: "Global expansion with low inflation and volatility produces strong gains",
    2018: "U.S.–China trade war and Fed tightening drive broad sell‑off",
    2019: "Central banks pivot to easing, trade tensions cool, fueling robust rally",
    2020: "COVID‑19 crash met by unprecedented stimulus; markets rebound rapidly",
    2021: "Vaccine‑driven reopening and record profits lift markets to new highs",
    2022: "Inflation surge, aggressive hikes, and Ukraine war spark steep downturn",
    2023: "Easing inflation and AI‑led tech boom drive strong rebound despite high rates",
    2024: "Global easing cycle begins; AI mega‑caps propel gains as rate cuts offset election risks",
}

# %%
# --- 1) Daten laden und vorbereiten ---
WORKING_DIR = Path.cwd()
FILE_PATH = Path(WORKING_DIR, "src", "data", "raw", "MSCI_World_daily.csv")
SAVE_HTML_TO = WORKING_DIR / "img" / "returns-one.html"


df = pd.read_csv(
    FILE_PATH, sep=",", skiprows=[1, 2], header=0, index_col=0, parse_dates=True
)
df = df.rename_axis("Date")

# Jahresendkurse und Renditen
last = df.resample("YE").last()
returns = last["Close"].pct_change().dropna().to_frame("Return")
returns.index = returns.index.year
returns = returns[returns.index < 2025]

# Intervalle definieren und zuordnen
bins = [-np.inf, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, np.inf]
returns["Interval"] = pd.cut(returns["Return"], bins=bins, right=False)

# Dict: Interval → Liste von (Jahr, Return)
return_dict = {
    iv: list(
        zip(
            returns[returns["Interval"] == iv].index,
            returns.loc[returns["Interval"] == iv, "Return"],
        )
    )
    for iv in returns["Interval"].cat.categories
}

# --- 2) Farbenliste und assert ---
intervals = list(return_dict.keys())

color_list = [
    "#581845",  # < -0.5
    "#581845",  # -0.5 bis -0.4
    "#581845",  # -0.4 bis -0.3
    "#900C3F",  # -0.3 bis -0.2
    "#CD5C5C",  # -0.2 bis -0.1
    "#E9967A",  # -0.1 bis 0
    "#124C4C",  # 0 bis 0.1
    "#8ACBB7",  # 0.1 bis 0.2
    "#0C888A",  # 0.2 bis 0.3
    "#124C4C",  # 0.3 bis 0.4
    "#186C6C",  # 0.4 bis 0.5
    "#186C6C",  # > 0.5
]
# Prüfen, dass wir genau so viele Farben wie Intervalle haben
assert len(color_list) == len(intervals), (
    f"Anzahl Farben ({len(color_list)}) ≠ Anzahl Intervalle ({len(intervals)})"
)

# --- 3) Mapping via Schleife ---
COLORS = {}
for iv, col in zip(intervals, color_list):
    COLORS[iv] = col

# --- 4) Plotly-Figur aufbauen mit dem neuen COLORS-Mapping ---
fig = go.Figure()
base_tracker = {iv: 0 for iv in intervals}

for iv, entries in return_dict.items():
    for year, ret in entries:
        fig.add_trace(
            go.Bar(
                x=[str(iv)],
                y=[1],
                base=[base_tracker[iv]],
                text=[f"{year}<br><b>{ret:.1%}</b>"],
                hoverinfo="text",
                hovertext=MSCI_WORLD_CONTEXT.get(year, ""),
                marker=dict(
                    color=COLORS[iv],
                    line=dict(color="white", width=2),
                ),
                marker_color=COLORS[iv],
                showlegend=False,
                # offset=0,
                textposition="inside",
                insidetextanchor="middle",  # Center text vertically
            )
        )
        base_tracker[iv] += 1

# Create better x labels for intervals
interval_labels = [
    f"{iv.left:.0%} to {iv.right:.0%}"
    if np.isfinite(iv.left) and np.isfinite(iv.right)
    else (f"< {iv.right:.0%}" if np.isneginf(iv.left) else f">= {iv.left:.0%}")
    for iv in intervals
]

fig.update_layout(
    barmode="stack",
    yaxis=dict(
        showticklabels=False,
        fixedrange=True,
        showgrid=False,
    ),
    xaxis=dict(
        showline=True,
        linewidth=2,
        linecolor="black",
        layer="above traces",
        tickangle=0,
        tickmode="array",
        tickvals=[str(iv) for iv in intervals],
        ticktext=interval_labels,
        fixedrange=True,
        showgrid=False,
    ),
    # hovermode="closest",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    dragmode=False,
    title="Annual Returns of the MSCI World Index by Return Interval",
)

fig.add_annotation(
    x=0,
    y=1,
    xref="paper",
    yref="paper",
    text="Annual return of investments in the MSCI World Index,<br>"
    "categorized by calendar year and grouped into return intervals.<br>"
    "Returns are calculated as the percentage change between<br>"
    "the closing values of the final trading days of consecutive years.<br>"
    "Data source: MSCI World Index via Yahoo Finance (Ticker: ^990100-USD-STRD)<br>"
    "Visualization by Alexander Blinn",
    showarrow=False,
    font=dict(size=12, color="black"),
    xanchor="left",
    yanchor="top",
    align="left",
    bordercolor="black",
    borderwidth=1,
    borderpad=4,
    bgcolor="white",
    opacity=0.8,
)

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
