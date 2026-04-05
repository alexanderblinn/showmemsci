"""
Render long-horizon MSCI World return ranges in the shared editorial theme.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import theme

WORKING_DIR = Path.cwd()
DATA_PATH = WORKING_DIR / "src" / "data" / "raw" / "MSCI_World_daily.csv"
SAVE_HTML_TO = WORKING_DIR / "img" / "long-term.html"


def load_holding_period_returns() -> pd.DataFrame:
    """Load yearly MSCI returns and compute rolling annualized holding periods."""
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
    returns = returns[returns.index < 2026]

    max_horizon = returns.index.max() - returns.index.min() + 1
    one_plus = returns["Return"] + 1

    for horizon in range(max_horizon):
        window = horizon + 1
        returns[f"Return_{horizon}"] = (
            one_plus.rolling(window=window, min_periods=window)
            .apply(lambda values: values.prod() ** (1 / window), raw=True)
            .shift(-horizon)
            .sub(1)
        )

    return returns.drop(columns=["Return"])


def build_figure(returns: pd.DataFrame) -> tuple[go.Figure, dict[str, str]]:
    """Build the long-horizon return envelope figure."""
    horizons = list(range(1, len(returns.columns) + 1))
    lower = returns.min(axis=0).mul(100).round(2)
    upper = returns.max(axis=0).mul(100).round(2)
    average = returns.mean(axis=0).mul(100).round(2)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=horizons,
            y=upper,
            mode="lines",
            line=dict(color=theme.POSITIVE, width=2.8),
            hovertemplate="<b>Upper bound</b><br>%{y:+.2f}%<extra></extra>",
            name="Upper bound",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=horizons,
            y=lower,
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(88, 122, 134, 0.08)",
            line=dict(color=theme.NEGATIVE_SOFT, width=2.4),
            hovertemplate="<b>Lower bound</b><br>%{y:+.2f}%<extra></extra>",
            name="Lower bound",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=horizons,
            y=average,
            mode="lines",
            line=dict(color=theme.NEUTRAL, width=3.6),
            hovertemplate="<b>Average</b><br>%{y:+.2f}%<extra></extra>",
            name="Average",
            showlegend=False,
        )
    )

    theme.apply_to_figure(
        fig,
        margin=dict(l=44, r=22, t=26, b=54),
        hovermode="x unified",
        xaxis=dict(
            title=dict(
                text="Holding period in years",
                font=dict(size=12, color=theme.MUTED),
            ),
            hoverformat=".0f",
            ticksuffix=" years",
            showticksuffix="all",
            range=[1, horizons[-1]],
            tick0=1,
            dtick=5,
            fixedrange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(size=11, color="#4C5660"),
        ),
        yaxis=dict(
            title=dict(
                text="Annualized return",
                font=dict(size=12, color=theme.MUTED),
            ),
            hoverformat=".2f",
            ticksuffix="%",
            fixedrange=True,
            showgrid=True,
            gridcolor=theme.GRID_SOFT,
            zeroline=True,
            zerolinecolor=theme.GRID,
            showline=False,
            tickfont=dict(size=11, color="#4C5660"),
        ),
    )

    summary = {
        "horizon": f"Up to {horizons[-1]} years",
        "start": f"Start year {int(returns.index.min())}",
        "one_year": f"1Y avg {average.iloc[0]:+.1f}%",
        "ten_year": (
            f"10Y avg {average.iloc[9]:+.1f}%"
            if len(average) >= 10
            else f"{len(average)}Y avg {average.iloc[-1]:+.1f}%"
        ),
    }
    return fig, summary


def main() -> None:
    """Render the themed long-term HTML asset."""
    returns = load_holding_period_returns()
    fig, summary = build_figure(returns)
    theme.render_html(
        fig,
        SAVE_HTML_TO,
        eyebrow="MSCI World Index",
        title="Long-Horizon Return Envelope",
        deck=(
            "The chart compresses every rolling holding period into three lines: "
            "the best annualized outcome, the worst, and the average. The spread "
            "narrows as the holding period extends and short-term noise fades."
        ),
        kicker="",
        meta_items=[
            summary["horizon"],
            summary["start"],
            summary["one_year"],
            summary["ten_year"],
        ],
        footer_left="www.ShowMeMSCI.com | @Alexander Blinn",
        footer_right="Data: MSCI World (^990100-USD-STRD) via Yahoo Finance",
    )


if __name__ == "__main__":
    main()
