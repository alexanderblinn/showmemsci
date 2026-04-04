"""
Render annual MSCI World returns by year in the shared editorial theme.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import theme

WORKING_DIR = Path.cwd()
DATA_PATH = WORKING_DIR / "src" / "data" / "raw" / "MSCI_World_daily.csv"
SAVE_HTML_TO = WORKING_DIR / "img" / "returns-two.html"


def load_returns() -> pd.DataFrame:
    """Load year-end MSCI World returns and their log2 transform."""
    df = pd.read_csv(
        DATA_PATH,
        sep=",",
        skiprows=[1, 2],
        header=0,
        index_col=0,
        parse_dates=True,
    ).rename_axis("Date")

    yearly = df.resample("YE").last()
    returns = yearly["Close"].pct_change().dropna().to_frame("pct")
    returns["log2"] = np.log2(1 + returns["pct"])
    returns.index = returns.index.year
    return returns[returns.index < 2026]


def build_figure(returns: pd.DataFrame) -> tuple[go.Figure, dict[str, str]]:
    """Build the yearly returns chart with percent and log2 views."""
    colors_pct = [theme.POSITIVE if value >= 0 else theme.NEGATIVE for value in returns["pct"]]
    colors_log2 = [theme.POSITIVE if value >= 0 else theme.NEGATIVE for value in returns["log2"]]

    pct_min = float(returns["pct"].min())
    pct_max = float(returns["pct"].max())
    log_min = float(returns["log2"].min())
    log_max = float(returns["log2"].max())

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=returns.index.astype(str),
            y=returns["pct"],
            marker=dict(color=colors_pct, line=dict(color="rgba(41, 47, 54, 0.16)", width=1)),
            hovertemplate="<b>%{x}</b><br>Annual return %{y:+.2%}<extra></extra>",
            visible=True,
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Bar(
            x=returns.index.astype(str),
            y=returns["log2"],
            marker=dict(color=colors_log2, line=dict(color="rgba(41, 47, 54, 0.16)", width=1)),
            hovertemplate="<b>%{x}</b><br>Log2 return %{y:+.2f}<extra></extra>",
            visible=False,
            showlegend=False,
        )
    )

    percent_yaxis = dict(
        title=dict(text="Annual return", font=dict(size=12, color=theme.MUTED)),
        hoverformat=".2%",
        tickformat=".0%",
        range=[pct_min - 0.06, pct_max + 0.06],
        fixedrange=True,
        showgrid=True,
        gridcolor=theme.GRID_SOFT,
        zeroline=True,
        zerolinecolor=theme.GRID,
        showline=False,
        tickfont=dict(size=11, color="#4C5660"),
    )
    log_yaxis = dict(
        title=dict(text="Annual log2 return", font=dict(size=12, color=theme.MUTED)),
        hoverformat=".2f",
        tickformat=".2f",
        range=[log_min - 0.08, log_max + 0.08],
        fixedrange=True,
        showgrid=True,
        gridcolor=theme.GRID_SOFT,
        zeroline=True,
        zerolinecolor=theme.GRID,
        showline=False,
        tickfont=dict(size=11, color="#4C5660"),
    )

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                showactive=True,
                buttons=[
                    dict(
                        label="Percent view",
                        method="update",
                        args=[
                            {"visible": [True, False]},
                            {"yaxis": percent_yaxis},
                        ],
                    ),
                    dict(
                        label="Log2 view",
                        method="update",
                        args=[
                            {"visible": [False, True]},
                            {"yaxis": log_yaxis},
                        ],
                    ),
                ],
                x=1,
                xanchor="right",
                y=1.12,
                yanchor="bottom",
            )
        ]
    )

    theme.apply_to_figure(
        fig,
        margin=dict(l=42, r=24, t=30, b=64),
        bargap=0.16,
        xaxis=dict(
            title=dict(text="Calendar year", font=dict(size=12, color=theme.MUTED)),
            hoverformat=".0f",
            tickmode="array",
            tickvals=returns.index.astype(str)[::4],
            ticktext=returns.index.astype(str)[::4],
            tickangle=0,
            fixedrange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(size=11, color="#4C5660"),
        ),
        yaxis=percent_yaxis,
    )

    positive_years = int((returns["pct"] >= 0).sum())
    negative_years = int((returns["pct"] < 0).sum())
    best_year = int(returns["pct"].idxmax())
    worst_year = int(returns["pct"].idxmin())
    summary = {
        "years": f"{len(returns)} yearly bars",
        "split": f"{positive_years} positive / {negative_years} negative",
        "best": f"Best {best_year}: {returns.loc[best_year, 'pct']:+.1%}",
        "worst": f"Worst {worst_year}: {returns.loc[worst_year, 'pct']:+.1%}",
    }
    return fig, summary


def main() -> None:
    """Render the themed Returns II chart."""
    returns = load_returns()
    fig, summary = build_figure(returns)
    theme.render_html(
        fig,
        SAVE_HTML_TO,
        eyebrow="Returns II / Editorial Edition",
        title="Annual Returns by Year",
        deck=(
            "The same annual return history is shown one year at a time instead "
            "of in buckets. This view makes the sequence of crises, rebounds, and "
            "clusters of positive years easier to read across the full timeline."
        ),
        kicker="One bar per year<br />toggle between percent and log2 views",
        meta_items=[
            summary["years"],
            summary["split"],
            summary["best"],
            summary["worst"],
        ],
        footer_left="Bars show the MSCI World return of each completed calendar year.",
        footer_right="Data: MSCI World (^990100-USD-STRD) via Yahoo Finance",
    )


if __name__ == "__main__":
    main()
