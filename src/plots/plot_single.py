"""
Render the single-line weekly MSCI World profile in the shared editorial theme.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import theme

WORKING_DIR = Path.cwd()
DATA_PATH = WORKING_DIR / "src" / "data" / "raw" / "MSCI_World_daily.csv"
SAVE_HTML_TO = WORKING_DIR / "img" / "single.html"


def load_weekly_profile() -> pd.DataFrame:
    """Load the MSCI World close series and sample it weekly."""
    df = pd.read_csv(
        DATA_PATH,
        sep=",",
        skiprows=[1, 2],
        header=0,
        index_col=0,
        parse_dates=True,
    ).rename_axis("Date")

    close = df.iloc[:, 0].rename("Value")
    weekly = close.resample("W").first().dropna().to_frame()
    return weekly


def build_figure(profile: pd.DataFrame) -> tuple[go.Figure, dict[str, str]]:
    """Build the weekly profile figure with linear and log views."""
    latest_value = float(profile["Value"].iloc[-1])
    high_value = float(profile["Value"].max())
    low_value = float(profile["Value"].min())

    fig = go.Figure()
    for visible in (True, False):
        fig.add_trace(
            go.Scatter(
                x=profile.index,
                y=profile["Value"],
                mode="lines",
                line=dict(color=theme.POSITIVE_DARK, width=3.5),
                hovertemplate=("%{x|%Y-%m-%d}<br>Index level %{y:,.2f}<extra></extra>"),
                showlegend=False,
                visible=visible,
            )
        )

    linear_yaxis = dict(
        title=dict(text="Index level", font=dict(size=12, color=theme.MUTED)),
        hoverformat=",.2f",
        range=[low_value * 0.95, high_value * 1.05],
        fixedrange=True,
        showgrid=True,
        gridcolor=theme.GRID_SOFT,
        zeroline=False,
        showline=False,
        tickfont=dict(size=11, color="#4C5660"),
    )
    log_yaxis = dict(
        title=dict(
            text="Index level (log scale)",
            font=dict(size=12, color=theme.MUTED),
        ),
        type="log",
        hoverformat=",.2f",
        fixedrange=True,
        showgrid=True,
        gridcolor=theme.GRID_SOFT,
        zeroline=False,
        showline=False,
        tickfont=dict(size=11, color="#4C5660"),
    )

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=True,
                direction="right",
                buttons=[
                    dict(
                        label="Linear View",
                        method="update",
                        args=[
                            {"visible": [True, False]},
                            {"yaxis": linear_yaxis},
                        ],
                    ),
                    dict(
                        label="Log₂ View",
                        method="update",
                        args=[
                            {"visible": [False, True]},
                            {"yaxis": log_yaxis},
                        ],
                    ),
                ],
                x=1,
                xanchor="right",
                y=1.11,
                yanchor="bottom",
            )
        ]
    )

    theme.apply_to_figure(
        fig,
        margin=dict(l=38, r=20, t=30, b=48),
        hovermode="x unified",
        xaxis=dict(
            hoverformat="%Y-%m-%d",
            fixedrange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(size=11, color="#4C5660"),
            tickformat="%Y",
        ),
        yaxis=linear_yaxis,
    )

    summary = {
        "span": (f"{profile.index.min():%Y} to {profile.index.max():%Y}"),
        "weeks": f"{len(profile)} weekly observations",
        "latest": f"Latest {latest_value:,.0f}",
        "high": f"Peak {high_value:,.0f}",
    }
    return fig, summary


def main() -> None:
    """Render the themed weekly profile HTML asset."""
    profile = load_weekly_profile()
    fig, summary = build_figure(profile)
    theme.render_html(
        fig,
        SAVE_HTML_TO,
        eyebrow="MSCI World Index",
        title="MSCI World Long-Term Trend",
        deck=(
            "A stripped-back view of the MSCI World path over time. The same "
            "series can be read in a standard linear scale or compressed into "
            "a log view to compare earlier and later decades more evenly. "
            "Daily closing prices have been averaged over each weekly period."
        ),
        kicker="",
        meta_items=[
            summary["span"],
            summary["weeks"],
            # summary["latest"],
            # summary["high"],
        ],
        footer_left="www.ShowMeMSCI.com | @Alexander Blinn",
        footer_right="Data: MSCI World (^990100-USD-STRD) via Yahoo Finance",
    )


if __name__ == "__main__":
    main()
