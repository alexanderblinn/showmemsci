"""
Render the MSCI World return heatmap in the shared editorial theme.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import theme

WORKING_DIR = Path.cwd()
DATA_PATH = WORKING_DIR / "src" / "data" / "raw" / "MSCI_World_daily.csv"
SAVE_HTML_TO = WORKING_DIR / "img" / "heatmap.html"


def build_colorscale(
    colors: list[str], pivot_index: int | None = None, pivot_position: float = 0.5
) -> list[tuple[float, str]]:
    """Convert a discrete palette into a Plotly colorscale."""
    if pivot_index is None:
        positions = np.linspace(0, 1, len(colors))
    else:
        pivot_index = max(0, min(len(colors) - 1, pivot_index))
        pivot_position = max(0.0, min(1.0, pivot_position))
        left = np.linspace(0, pivot_position, pivot_index + 1)
        right = np.linspace(pivot_position, 1, len(colors) - pivot_index)
        positions = np.concatenate([left, right[1:]])
    return list(zip(positions, colors))


def signed_log1p(values: np.ndarray) -> np.ndarray:
    """Compress wide return ranges while keeping zero-centered direction."""
    return np.sign(values) * np.log1p(np.abs(values))


def load_return_triangle() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute annualized and total return triangles."""
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

    annualized = returns.copy()
    total = returns.copy()
    one_plus = returns["Return"] + 1
    max_horizon = returns.index.max() - returns.index.min() + 1

    for horizon in range(max_horizon):
        window = horizon + 1
        annualized[f"Return_{horizon}"] = (
            one_plus.rolling(window=window, min_periods=window)
            .apply(lambda values: values.prod() ** (1 / window), raw=True)
            .shift(-horizon)
            .sub(1)
        )
        total[f"Return_{horizon}"] = (
            one_plus.rolling(window=window, min_periods=window)
            .apply(lambda values: values.prod(), raw=True)
            .shift(-horizon)
            .sub(1)
        )

    return annualized, total


def build_figure(
    annualized: pd.DataFrame, total: pd.DataFrame
) -> tuple[go.Figure, dict[str, str]]:
    """Build the themed return-triangle heatmap."""
    holding_columns = [
        column for column in annualized.columns if column.startswith("Return_")
    ]
    x_years = [int(column.split("_")[1]) + 1 for column in holding_columns]
    y_years = annualized.index.tolist()[::-1]

    z_annualized = annualized[holding_columns].values[::-1, :]
    z_total = total[holding_columns].values[::-1, :]
    z_total_scaled = signed_log1p(z_total)
    total_hover_text = np.empty(z_total.shape, dtype=object)
    total_hover_text[:] = ""
    finite_mask = np.isfinite(z_total)
    total_hover_text[finite_mask] = [f"{value:+.2%}" for value in z_total[finite_mask]]

    colorscale = build_colorscale(theme.INTERVAL_COLORS)
    total_colorscale = build_colorscale(
        theme.INTERVAL_COLORS,
        pivot_index=theme.INTERVAL_COLORS.index(theme.NEUTRAL),
        pivot_position=0.14,
    )

    fig = go.Figure(
        data=[
            go.Heatmap(
                z=z_annualized,
                x=x_years,
                y=y_years,
                colorscale=colorscale,
                zmin=float(np.nanmin(z_annualized)),
                zmax=float(np.nanmax(z_annualized)),
                zmid=0,
                xgap=1.2,
                ygap=1.2,
                hoverongaps=False,
                hovertemplate=(
                    "<b>Start %{y}</b><br>Holding period %{x} years<br>"
                    "Annualized return %{z:+.2%}<extra></extra>"
                ),
                visible=True,
                showscale=False,
            ),
            go.Heatmap(
                z=z_total_scaled,
                x=x_years,
                y=y_years,
                text=total_hover_text,
                colorscale=total_colorscale,
                zmin=float(np.nanmin(z_total_scaled)),
                zmax=float(np.nanmax(z_total_scaled)),
                zmid=0,
                xgap=1.2,
                ygap=1.2,
                hoverongaps=False,
                hovertemplate=(
                    "<b>Start %{y}</b><br>Holding period %{x} years<br>"
                    "Total return %{text}<extra></extra>"
                ),
                visible=False,
                showscale=False,
            ),
        ]
    )

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=1,
                xanchor="right",
                y=1.04,
                yanchor="bottom",
                showactive=True,
                buttons=[
                    dict(
                        label="Annualized",
                        method="update",
                        args=[{"visible": [True, False]}],
                    ),
                    dict(
                        label="Total",
                        method="update",
                        args=[{"visible": [False, True]}],
                    ),
                ],
            )
        ]
    )

    theme.apply_to_figure(
        fig,
        margin=dict(l=50, r=22, t=12, b=54),
        plot_bgcolor="rgba(35, 48, 59, 0.055)",
        xaxis=dict(
            title=dict(
                text="Holding period in years", font=dict(size=12, color=theme.MUTED)
            ),
            hoverformat=".0f",
            range=[0.5, max(x_years) + 0.5],
            tickmode="linear",
            dtick=5,
            tick0=1,
            fixedrange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(size=11, color="#4C5660"),
        ),
        yaxis=dict(
            title=dict(text="Start year", font=dict(size=12, color=theme.MUTED)),
            hoverformat=".0f",
            range=[max(y_years) + 0.5, min(y_years) - 0.5],
            tickmode="linear",
            dtick=4,
            tick0=min(y_years),
            fixedrange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(size=11, color="#4C5660"),
        ),
    )

    best_annualized = float(np.nanmax(z_annualized))
    best_total = float(np.nanmax(z_total))
    summary = {
        "span": f"{min(y_years)} to {max(y_years)} starts",
        "horizon": f"Up to {max(x_years)} years",
        "annualized": f"Best annualized {best_annualized:+.1%}",
        "total": f"Best total {best_total:+.0%}",
    }
    return fig, summary


def main() -> None:
    """Render the themed heatmap HTML asset."""
    annualized, total = load_return_triangle()
    fig, summary = build_figure(annualized, total)
    theme.render_html(
        fig,
        SAVE_HTML_TO,
        eyebrow="MSCI World Index",
        title="Return Triangle",
        deck=(
            "Every cell represents an investment window defined by its start year "
            "and holding period. The heatmap reveals how quickly weak entry years "
            "recover, and how strongly long holding periods smooth the range of outcomes."
        ),
        kicker="",
        meta_items=[
            summary["span"],
            summary["horizon"],
            summary["annualized"],
            summary["total"],
        ],
        footer_left="www.ShowMeMSCI.com | @Alexander Blinn",
        footer_right="Data: MSCI World (^990100-USD-STRD) via Yahoo Finance",
    )


if __name__ == "__main__":
    main()
