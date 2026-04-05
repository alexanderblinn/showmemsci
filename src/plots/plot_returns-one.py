"""Stacked bars represent calendar years grouped into annual-return intervals."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import theme

WORKING_DIR = Path.cwd()
DATA_PATH = WORKING_DIR / "src" / "data" / "raw" / "MSCI_World_daily.csv"
SAVE_HTML_TO = WORKING_DIR / "img" / "returns-one.html"

INTERVAL_BINS = [
    # -np.inf,
    -0.5,
    -0.4,
    -0.3,
    -0.2,
    -0.1,
    0,
    0.1,
    0.2,
    0.3,
    0.4,
    # 0.5,
    # np.inf,
]

NEUTRAL_ZONE = (-0.1, 0.1)

ZONE_STYLES = {
    "loss": {
        "label": "Loss Years",
        "fill": "rgba(92, 70, 80, 0.06)",
        "line": "rgba(31, 35, 42, 0.10)",
        "text": "rgba(61,69,77,0.66)",
    },
    "neutral": {
        "label": "Near Flat",
        "fill": "rgba(164, 143, 109, 0.08)",
        "line": "rgba(31, 35, 42, 0.10)",
        "text": "rgba(61,69,77,0.66)",
    },
    "gain": {
        "label": "Strong Gains",
        "fill": "rgba(93, 122, 129, 0.07)",
        "line": "rgba(31, 35, 42, 0.10)",
        "text": "rgba(61,69,77,0.66)",
    },
}

YEAR_NOTES = {
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
    2025: "Strong gains fueled by solid earnings, cooling inflation, and persistent AI‑driven momentum",
}


def load_returns() -> pd.DataFrame:
    """Load year-end MSCI World returns."""
    df = pd.read_csv(
        DATA_PATH,
        sep=",",
        skiprows=[1, 2],
        header=0,
        index_col=0,
        parse_dates=True,
    ).rename_axis("Date")

    yearly = df.resample("YE").last()
    returns = yearly["Close"].pct_change().dropna().to_frame("Return")
    returns.index = returns.index.year
    return returns[returns.index < 2026]


def interval_label(interval: pd.Interval) -> str:
    """Format interval labels for the x-axis."""
    if np.isneginf(interval.left):
        return f"<br>{interval.right:.0%}"
    if np.isposinf(interval.right):
        return f">=<br>{interval.left:.0%}"
    return f"{interval.left:.0%}<br>to {interval.right:.0%}"


def interval_hover_label(interval: pd.Interval) -> str:
    """Format interval labels for the hover card."""
    if np.isneginf(interval.left):
        return f"Below {interval.right:.0%}"
    if np.isposinf(interval.right):
        return f"{interval.left:.0%} and above"
    return f"{interval.left:.0%} to {interval.right:.0%}"


def classify_zone(interval: pd.Interval) -> str:
    """Assign an interval to loss, neutral, or gain territory."""
    neutral_left, neutral_right = NEUTRAL_ZONE
    overlaps_neutral = interval.right > neutral_left and interval.left < neutral_right
    if overlaps_neutral:
        return "neutral"
    if interval.right <= neutral_left:
        return "loss"
    return "gain"


def zone_segments(intervals: list[pd.Interval]) -> list[tuple[str, int, int]]:
    """Collapse contiguous intervals into visual background segments."""
    if not intervals:
        return []

    zones = [classify_zone(interval) for interval in intervals]
    segments: list[tuple[str, int, int]] = []
    start = 0
    current = zones[0]

    for index, zone in enumerate(zones[1:], start=1):
        if zone != current:
            segments.append((current, start, index - 1))
            start = index
            current = zone

    segments.append((current, start, len(zones) - 1))
    return segments


def build_figure(returns: pd.DataFrame) -> tuple[go.Figure, dict[str, str]]:
    """Build the editorial chart."""
    returns = returns.copy()
    returns["Interval"] = pd.cut(returns["Return"], bins=INTERVAL_BINS, right=False)

    intervals = list(returns["Interval"].cat.categories)
    visible_returns = returns[returns["Interval"].notna()].copy()
    if visible_returns.empty:
        raise ValueError("INTERVAL_BINS exclude all return observations.")

    palette = theme.sample_palette(theme.INTERVAL_COLORS, len(intervals))
    band_counts = (
        visible_returns.groupby("Interval", observed=False)
        .size()
        .reindex(intervals, fill_value=0)
    )

    fig = go.Figure()
    stacked_heights = {interval: 0 for interval in intervals}

    for band_index, interval in enumerate(intervals):
        band_df = visible_returns[visible_returns["Interval"] == interval].sort_index()
        base_color = palette[band_index]
        block_count = len(band_df)

        for stack_index, (year, row) in enumerate(band_df.iterrows()):
            tint = 0.04 + (0.12 * stack_index / max(block_count - 1, 1))
            tile_color = theme.mix_hex(base_color, "#F6F2E9", tint)
            note = YEAR_NOTES.get(year, "-")

            fig.add_trace(
                go.Bar(
                    x=[band_index],
                    y=[1],
                    base=[stacked_heights[interval]],
                    width=0.78,
                    marker=dict(
                        color=tile_color,
                        line=dict(color="rgba(41, 47, 54, 0.24)", width=1),
                    ),
                    text=[f"<b>{year}</b><br>{row['Return']:+.0%}"],
                    textposition="inside",
                    textangle=0,
                    insidetextanchor="middle",
                    textfont=dict(size=10, color="#F8F5EE"),
                    customdata=[
                        [
                            interval_hover_label(interval),
                            int(year),
                            float(row["Return"]),
                            note,
                        ]
                    ],
                    hovertemplate=(
                        "<b>%{customdata[1]}</b><br>"
                        # "Return band: %{customdata[0]}<br>"
                        "Annual return: %{customdata[2]:+.2%}<br>"
                        "%{customdata[3]}<extra></extra>"
                    ),
                    showlegend=False,
                )
            )
            stacked_heights[interval] += 1

    max_count = int(band_counts.max())
    y_max = max(max_count + 1.6, 3)

    segments = zone_segments(intervals)
    for zone_name, start_idx, end_idx in segments:
        style = ZONE_STYLES[zone_name]
        fig.add_vrect(
            x0=start_idx - 0.5,
            x1=end_idx + 0.5,
            fillcolor=style["fill"],
            line_width=0,
            layer="below",
        )
        fig.add_annotation(
            x=(start_idx + end_idx) / 2,
            y=y_max - 0.24,
            text=style["label"],
            showarrow=False,
            font=dict(
                size=12,
                color=style["text"],
                family="Aptos, Segoe UI, sans-serif",
            ),
        )

    for _, start_idx, _ in segments[1:]:
        fig.add_vline(
            x=start_idx - 0.5,
            line_width=1,
            line_color="rgba(31, 35, 42, 0.10)",
        )

    for band_index, count in enumerate(band_counts.tolist()):
        if count == 0:
            continue
        fig.add_annotation(
            x=band_index,
            y=count + 0.52,
            text=f"{count} yrs",
            showarrow=False,
            font=dict(
                size=10,
                color="#3D454D",
                family="Aptos, Segoe UI, sans-serif",
            ),
            bgcolor="rgba(248,245,238,0.92)",
            bordercolor="rgba(61,69,77,0.14)",
            borderwidth=1,
            borderpad=4,
        )

    theme.apply_to_figure(
        fig,
        barmode="stack",
        bargap=0.18,
        margin=dict(l=28, r=24, t=22, b=52),
        hovermode="closest",
        uniformtext=dict(minsize=9, mode="show"),
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(len(intervals))),
            ticktext=[interval_label(interval) for interval in intervals],
            range=[-0.5, len(intervals) - 0.5],
            tickfont=dict(size=11, color="#4C5660"),
            fixedrange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
        ),
        yaxis=dict(
            range=[0, y_max],
            fixedrange=True,
            showgrid=False,
            zeroline=False,
            showticklabels=False,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        dragmode=False,
    )

    hidden_years = int(returns["Interval"].isna().sum())
    positive_years = int((visible_returns["Return"] >= 0).sum())
    negative_years = int((visible_returns["Return"] < 0).sum())
    mean_return = float(visible_returns["Return"].mean())
    median_return = float(visible_returns["Return"].median())
    best_year = int(visible_returns["Return"].idxmax())
    best_return = float(visible_returns.loc[best_year, "Return"])

    summary = {
        "years": (
            f"{len(visible_returns)} shown / {len(returns)} total"
            if hidden_years
            else f"{len(visible_returns)} yearly blocks"
        ),
        "bands": f"{len(intervals)} interval bands",
        "split": f"{positive_years} positive / {negative_years} negative",
        "median": f"Median year {median_return:+.1%}",
        "mean": f"Mean year {mean_return:+.1%}",
        "best": f"Best {best_year}: {best_return:+.1%}",
    }
    return fig, summary


def main() -> None:
    """Render the editorial chart as a standalone HTML asset."""
    returns = load_returns()
    fig, summary = build_figure(returns)
    theme.render_html(
        fig,
        SAVE_HTML_TO,
        eyebrow="MSCI World Index",
        title="MSCI World Return Bands",
        deck=(
            "Each block represents a specific year, showing its annual return "
            "alongwith a brief contextual description. "
            "The years are grouped into bands, each spanning a width of 10%."
        ),
        kicker="",
        meta_items=[
            summary["years"],
            # summary["bands"],
            summary["split"],
            summary["median"],
            summary["mean"],
            summary["best"],
        ],
        footer_left="www.ShowMeMSCI.com | @Alexander Blinn",
        footer_right="Data: MSCI World (^990100-USD-STRD) via Yahoo Finance",
    )


if __name__ == "__main__":
    main()
