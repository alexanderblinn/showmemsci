"""Render MSCI World return distributions for daily, monthly, and yearly horizons."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import theme

WORKING_DIR = Path.cwd()
DATA_PATH = WORKING_DIR / "src" / "data" / "raw" / "MSCI_World_daily.csv"
SAVE_HTML_TO = WORKING_DIR / "img" / "dist.html"

FREQUENCY_ORDER = ("days", "months", "years")

FREQUENCY_CONFIG: dict[str, dict[str, str | float]] = {
    "days": {
        "button_label": "Days",
        "series_label": "Daily return",
        "bin_method": "fixed",
        "bin_size": 0.001,
        "tickformat": ".1%",
        "color": theme.POSITIVE,
    },
    "months": {
        "button_label": "Months",
        "series_label": "Monthly return",
        "bin_method": "fixed",
        "bin_size": 0.005,
        "tickformat": ".0%",
        "color": theme.NEUTRAL,
    },
    "years": {
        "button_label": "Years",
        "series_label": "Annual return",
        "bin_method": "doane",
        "tickformat": ".0%",
        "color": theme.NEGATIVE_SOFT,
    },
}


def load_close_series() -> pd.Series:
    """Load the MSCI World close series."""
    df = pd.read_csv(
        DATA_PATH,
        sep=",",
        skiprows=[1, 2],
        header=0,
        index_col=0,
        parse_dates=True,
    ).rename_axis("Date")

    return df.iloc[:, 0].rename("Close")


def trim_incomplete_periods(
    series: pd.Series, last_observation: pd.Timestamp, frequency: str
) -> pd.Series:
    """Drop the final resampled point if the current period is still incomplete."""
    if series.empty:
        return series

    normalized_observation = last_observation.normalize()

    if frequency == "ME":
        expected_period_end = (
            normalized_observation + pd.offsets.MonthEnd(0)
        ).normalize()
    elif frequency == "YE":
        expected_period_end = (
            normalized_observation + pd.offsets.YearEnd(0)
        ).normalize()
    else:
        return series

    if normalized_observation == expected_period_end:
        return series
    return series.iloc[:-1]


def load_return_sets() -> dict[str, pd.Series]:
    """Compute return series for multiple observation horizons."""
    close = load_close_series()
    last_observation = close.index.max()

    monthly_close = trim_incomplete_periods(
        close.resample("ME").last().dropna(),
        last_observation,
        "ME",
    )
    yearly_close = trim_incomplete_periods(
        close.resample("YE").last().dropna(),
        last_observation,
        "YE",
    )

    return {
        "days": close.pct_change().dropna(),
        "months": monthly_close.pct_change().dropna(),
        "years": yearly_close.pct_change().dropna(),
    }


def symmetric_axis_range(returns: pd.Series, bin_size: float) -> list[float]:
    """Derive a symmetric x-axis range wide enough to contain all observations."""
    max_abs_move = max(
        abs(float(returns.min())), abs(float(returns.max())), bin_size * 6
    )
    bound = float(np.ceil((max_abs_move + bin_size) / bin_size) * bin_size)
    return [-bound, bound]


def build_xaxis(axis_title: str, tickformat: str, axis_range: list[float]) -> dict:
    """Build the shared x-axis config for a return histogram."""
    return dict(
        title=dict(text=axis_title, font=dict(size=12, color=theme.MUTED)),
        tickformat=tickformat,
        range=axis_range,
        fixedrange=True,
        showgrid=False,
        zeroline=True,
        zerolinecolor=theme.GRID,
        showline=False,
        tickfont=dict(size=11, color="#4C5660"),
    )


def resolve_bins(
    returns: pd.Series, config: dict[str, str | float]
) -> tuple[dict[str, float], list[float], str]:
    """Resolve histogram bin settings and the corresponding width label."""
    bin_method = str(config["bin_method"])

    if bin_method == "fixed":
        bin_size = float(config["bin_size"])
        axis_range = symmetric_axis_range(returns, bin_size)
        return (
            dict(start=axis_range[0], end=axis_range[1], size=bin_size),
            axis_range,
            f"h = {bin_size:.2%}",
        )

    if bin_method in {"sturges", "doane", "fd", "auto", "sqrt", "rice", "scott"}:
        edges = np.histogram_bin_edges(returns.to_numpy(), bins=bin_method)
        bin_size = float(edges[1] - edges[0])
        axis_range = [float(edges[0]), float(edges[-1])]
        bin_count = len(edges) - 1
        return (
            dict(start=axis_range[0], end=axis_range[1], size=bin_size),
            axis_range,
            f"h = {bin_size:.2%} ({bin_method.title()}, k = {bin_count})",
        )

    raise ValueError(f"Unsupported bin_method: {bin_method}")


def build_mean_shape(mean_return: float) -> dict:
    """Build a vertical mean-reference line on the return axis."""
    return dict(
        type="line",
        xref="x",
        yref="paper",
        x0=mean_return,
        x1=mean_return,
        y0=0,
        y1=1,
        line=dict(color=theme.INK, width=2, dash="dot"),
    )


def build_stats_payload(return_sets: dict[str, pd.Series]) -> dict[str, dict[str, str]]:
    """Build formatted sample statistics for the floating HTML panel."""
    payload: dict[str, dict[str, str]] = {}

    for frequency in FREQUENCY_ORDER:
        returns = return_sets[frequency]
        config = FREQUENCY_CONFIG[frequency]
        _, _, bin_label = resolve_bins(returns, config)
        payload[frequency] = {
            "title": str(config["series_label"]),
            "sample_size": f"{len(returns):,}",
            "bin_label": bin_label,
            "sample_mean": f"{float(returns.mean()):+.2%}",
            "sample_variance": f"{float(returns.var(ddof=1)):.6f}",
        }

    return payload


def build_stats_overlay_script(stats_payload: dict[str, dict[str, str]]) -> str:
    """Build the HTML/CSS/JS overlay used for the in-chart statistics box."""
    stats_json = json.dumps(stats_payload, ensure_ascii=False)

    return f"""
<style>
  .dist-stats-card {{
    position: absolute;
    top: 30px;
    left: 100px;
    width: min(200px, 26%);
    padding: 12px 14px 11px;
    border-radius: 16px;
    border: 1px solid rgba(61, 69, 77, 0.14);
    background: rgba(248, 245, 238, 0.90);
    box-shadow: 0 12px 28px rgba(18, 24, 30, 0.08);
    color: #31404B;
    z-index: 4;
    pointer-events: none;
  }}

  .dist-stats-title {{
    margin-bottom: 5px;
    font-size: 12px;
    font-weight: 700;
    line-height: 1.2;
  }}

  .dist-stats-line {{
    font-size: 10px;
    line-height: 1.28;
  }}

  .dist-stats-block {{
    margin-top: 9px;
  }}

  .dist-stats-formula-row {{
    display: flex;
    align-items: flex-start;
    gap: 6px;
    white-space: nowrap;
  }}

  .dist-stats-formula,
  .dist-stats-value-inline {{
    font-size: 10px;
    line-height: 1.15;
  }}

  .dist-stats-value-inline {{
    padding-top: 1px;
  }}

  .dist-stats-formula .MathJax {{
    font-size: 0.95em !important;
  }}

  .dist-stats-formula .mjx-container {{
    margin: 0 !important;
  }}

  @media (max-width: 760px) {{
    .dist-stats-card {{
      width: min(250px, 52%);
      top: 12px;
      left: 12px;
      padding: 10px 11px;
    }}
  }}
</style>
<script>
  window.addEventListener("load", function () {{
    const chart = document.getElementById("chart");
    const shell = document.querySelector(".chart-shell");
    if (!chart || !shell) return;

    const statsPayload = {stats_json};
    const labelToKey = {{
      Days: "days",
      Months: "months",
      Years: "years"
    }};

    let card = shell.querySelector(".dist-stats-card");
    if (!card) {{
      card = document.createElement("div");
      card.className = "dist-stats-card";
      shell.appendChild(card);
    }}

    const typesetCard = function () {{
      if (!window.MathJax) return;
      if (typeof MathJax.typesetClear === "function") {{
        MathJax.typesetClear([card]);
      }}
      if (typeof MathJax.typesetPromise === "function") {{
        MathJax.typesetPromise([card]);
        return;
      }}
      if (MathJax.Hub && typeof MathJax.Hub.Queue === "function") {{
        MathJax.Hub.Queue(["Typeset", MathJax.Hub, card]);
      }}
    }};

    const renderStats = function (key) {{
      const stats = statsPayload[key];
      if (!stats) return;

      card.innerHTML =
        '<div class="dist-stats-title">' + stats.title + "</div>" +
        '<div class="dist-stats-line">n = ' + stats.sample_size + "</div>" +
        '<div class="dist-stats-line">' + stats.bin_label + "</div>" +
        '<div class="dist-stats-block">' +
          '<div class="dist-stats-formula-row">' +
            '<div class="dist-stats-formula">\\\\( \\\\hat{{\\\\mu}} = \\\\frac{{1}}{{n}} \\\\sum_{{i=1}}^{{n}} x_i \\\\)</div>' +
            '<div class="dist-stats-value-inline">= ' + stats.sample_mean + "</div>" +
          "</div>" +
        "</div>" +
        '<div class="dist-stats-block">' +
          '<div class="dist-stats-formula-row">' +
            '<div class="dist-stats-formula">\\\\( \\\\hat{{\\\\sigma}}^{{2}} = \\\\frac{{1}}{{n-1}} \\\\sum_{{i=1}}^{{n}} (x_i - \\\\hat{{\\\\mu}})^2 \\\\)</div>' +
            '<div class="dist-stats-value-inline">= ' + stats.sample_variance + "</div>" +
          "</div>" +
        "</div>";

      typesetCard();
    }};

    renderStats("days");

    if (chart.on) {{
      chart.on("plotly_buttonclicked", function (eventData) {{
        const label = eventData && eventData.button ? eventData.button.label : "";
        renderStats(labelToKey[label] || "days");
      }});
    }}
  }});
</script>
"""


def build_figure(
    return_sets: dict[str, pd.Series],
) -> tuple[go.Figure, dict[str, str], dict[str, dict[str, str]]]:
    """Build the multi-horizon return histogram."""
    fig = go.Figure()
    xaxis_states: dict[str, dict] = {}
    shape_states: dict[str, list[dict]] = {}
    annotation_states: dict[str, list[dict]] = {}
    stats_payload = build_stats_payload(return_sets)

    for index, frequency in enumerate(FREQUENCY_ORDER):
        config = FREQUENCY_CONFIG[frequency]
        returns = return_sets[frequency]
        xbins, axis_range, _ = resolve_bins(returns, config)
        mean_return = float(returns.mean())
        xaxis_states[frequency] = build_xaxis(
            axis_title=str(config["series_label"]),
            tickformat=str(config["tickformat"]),
            axis_range=axis_range,
        )
        shape_states[frequency] = [build_mean_shape(mean_return)]
        annotation_states[frequency] = []

        fig.add_trace(
            go.Histogram(
                x=returns,
                xbins=xbins,
                marker=dict(
                    color=str(config["color"]),
                    line=dict(color="rgba(41, 47, 54, 0.16)", width=1),
                ),
                opacity=0.9,
                hovertemplate=("<b>%{x:+.2%}</b><br>%{y} observations<extra></extra>"),
                showlegend=False,
                visible=index == 0,
            )
        )

    buttons = []
    for button_index, frequency in enumerate(FREQUENCY_ORDER):
        buttons.append(
            dict(
                label=str(FREQUENCY_CONFIG[frequency]["button_label"]),
                method="update",
                args=[
                    {
                        "visible": [
                            index == button_index
                            for index in range(len(FREQUENCY_ORDER))
                        ]
                    },
                    {
                        "xaxis": xaxis_states[frequency],
                        "shapes": shape_states[frequency],
                        "annotations": annotation_states[frequency],
                    },
                ],
            )
        )

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=True,
                direction="right",
                buttons=buttons,
                x=1,
                xanchor="right",
                y=1.12,
                yanchor="bottom",
            )
        ]
    )

    theme.apply_to_figure(
        fig,
        bargap=0.04,
        margin=dict(l=44, r=24, t=30, b=56),
        hovermode="closest",
        xaxis=xaxis_states["days"],
        shapes=shape_states["days"],
        annotations=annotation_states["days"],
        yaxis=dict(
            title=dict(text="Observations", font=dict(size=12, color=theme.MUTED)),
            fixedrange=True,
            showgrid=True,
            gridcolor=theme.GRID_SOFT,
            zeroline=False,
            showline=False,
            tickfont=dict(size=11, color="#4C5660"),
        ),
    )

    daily = return_sets["days"]
    monthly = return_sets["months"]
    yearly = return_sets["years"]

    summary = {
        "days": f"{len(daily):,} daily moves",
        "months": f"{len(monthly):,} monthly moves",
        "years": f"{len(yearly):,} yearly moves",
        "best_day": f"Best day {daily.max():+.1%}",
        "worst_day": f"Worst day {daily.min():+.1%}",
    }
    return fig, summary, stats_payload


def main() -> None:
    """Render the themed distribution chart."""
    return_sets = load_return_sets()
    fig, summary, stats_payload = build_figure(return_sets)
    theme.render_html(
        fig,
        SAVE_HTML_TO,
        eyebrow="The small but positive daily return is large enough to offset the volatility drag from symmetric fluctuations, leaving a net gain that compounds into clearly positive monthly and yearly returns.",
        title="MSCI World Return Distribution",
        deck=(
            "This histogram view shows how often returns landed in specific "
            "ranges. The buttons switch between daily, monthly, and annual "
            "observations so the distribution can be compared across horizons "
            "without leaving the chart."
        ),
        kicker="",
        meta_items=[
            summary["days"],
            summary["months"],
            summary["years"],
            # summary["worst_day"],
        ],
        footer_left="www.ShowMeMSCI.com | @Alexander Blinn",
        footer_right="Data: MSCI World (^990100-USD-STRD) via Yahoo Finance",
        include_mathjax="cdn",
        extra_script=build_stats_overlay_script(stats_payload),
    )


if __name__ == "__main__":
    main()
