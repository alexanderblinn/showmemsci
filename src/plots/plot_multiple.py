"""
Render yearly MSCI World return profiles in the shared editorial theme.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import theme

WORKING_DIR = Path.cwd()
DATA_PATH = WORKING_DIR / "src" / "data" / "raw" / "MSCI_World_daily.csv"
SAVE_HTML_TO = WORKING_DIR / "img" / "multiple.html"

BASE_LINE_WIDTH = 2.2
HIGHLIGHT_WIDTH = 4.2
BASE_LINE_COLOR = theme.mix_hex(theme.POSITIVE_DARK, theme.PAPER, 0.22)
HIGHLIGHT_COLOR = theme.INK
BASE_LINE_OPACITY = 0.18
HIGHLIGHT_OPACITY = 0.96


def load_profiles() -> pd.DataFrame:
    """Load daily MSCI World data and derive per-year normalized profiles."""
    df = pd.read_csv(
        DATA_PATH,
        sep=",",
        skiprows=[1, 2],
        header=0,
        index_col=0,
        parse_dates=True,
    ).rename_axis("Date")

    close = df.iloc[:, 0].rename("Value").to_frame()
    close["Year"] = close.index.year
    close["Normalized"] = close.groupby("Year")["Value"].transform(
        lambda series: (series - series.iloc[0]) / series.iloc[0] * 100
    )
    close["Normalized_log"] = close.groupby("Year")["Value"].transform(
        lambda series: np.log2(series / series.iloc[0])
    )
    return close[["Normalized", "Normalized_log"]]


def build_figure(profiles: pd.DataFrame) -> tuple[go.Figure, dict[str, str], str]:
    """Build the themed yearly-profile figure and hover-persistence script."""
    profiles = profiles.copy().sort_index()
    years = sorted(profiles.index.year.unique())
    total_traces = len(years) * 2

    fig = go.Figure()

    for column, visible, hover_label in [
        ("Normalized", True, "Cumulative change"),
        ("Normalized_log", False, "Log2 change"),
    ]:
        for year in years:
            year_slice = profiles[profiles.index.year == year]
            fig.add_trace(
                go.Scatter(
                    x=year_slice.index.dayofyear,
                    y=year_slice[column].round(2),
                    mode="lines",
                    line=dict(color=BASE_LINE_COLOR, width=BASE_LINE_WIDTH),
                    opacity=BASE_LINE_OPACITY,
                    visible=visible,
                    name=str(year),
                    customdata=year_slice.index.strftime("%Y-%m-%d"),
                    hovertemplate=(
                        "<b>%{fullData.name}</b><br>"
                        "%{customdata}<br>"
                        f"{hover_label} "
                        + ("%{y:+.2f}%" if column == "Normalized" else "%{y:+.2f}")
                        + "<extra></extra>"
                    ),
                    showlegend=False,
                )
            )

    linear_yaxis = dict(
        title=dict(
            text="Cumulative change from Jan 1",
            font=dict(size=12, color=theme.MUTED),
        ),
        hoverformat=".2f",
        ticksuffix="%",
        range=[-110, 60],
        fixedrange=True,
        showgrid=True,
        gridcolor=theme.GRID_SOFT,
        zeroline=True,
        zerolinecolor=theme.GRID,
        showline=False,
        tickfont=dict(size=11, color="#4C5660"),
    )
    log_yaxis = dict(
        title=dict(
            text="Log2 change from Jan 1",
            font=dict(size=12, color=theme.MUTED),
        ),
        hoverformat=".2f",
        range=[-1.1, 0.6],
        fixedrange=True,
        showgrid=True,
        gridcolor=theme.GRID_SOFT,
        zeroline=True,
        zerolinecolor=theme.GRID,
        showline=False,
        tickfont=dict(size=11, color="#4C5660"),
    )

    steps = []
    for year_index, year in enumerate(years):
        highlight_indices = [year_index, year_index + len(years)]
        steps.append(
            dict(
                method="restyle",
                label=str(year),
                args=[
                    {
                        "line.width": [
                            HIGHLIGHT_WIDTH
                            if index in highlight_indices
                            else BASE_LINE_WIDTH
                            for index in range(total_traces)
                        ],
                        "line.color": [
                            HIGHLIGHT_COLOR
                            if index in highlight_indices
                            else BASE_LINE_COLOR
                            for index in range(total_traces)
                        ],
                        "opacity": [
                            HIGHLIGHT_OPACITY
                            if index in highlight_indices
                            else BASE_LINE_OPACITY
                            for index in range(total_traces)
                        ],
                    },
                    list(range(total_traces)),
                ],
            )
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
                            {"visible": [True] * len(years) + [False] * len(years)},
                            {"yaxis": linear_yaxis},
                        ],
                    ),
                    dict(
                        label="Log₂ View",
                        method="update",
                        args=[
                            {"visible": [False] * len(years) + [True] * len(years)},
                            {"yaxis": log_yaxis},
                        ],
                    ),
                ],
                x=1,
                xanchor="right",
                y=1.12,
                yanchor="bottom",
            )
        ],
        sliders=[
            dict(
                active=len(years) - 1,
                currentvalue={"prefix": "Highlighted year: "},
                steps=steps,
            )
        ],
    )

    fig.add_hline(y=0, line_width=1, line_color=theme.GRID)

    theme.apply_to_figure(
        fig,
        margin=dict(l=42, r=22, t=36, b=64),
        hovermode="closest",
        xaxis=dict(
            hoverformat=".0f",
            range=[1, 366],
            tickmode="array",
            tickvals=[1, 61, 122, 183, 244, 305, 366],
            ticktext=["Jan", "Mar", "May", "Jul", "Sep", "Nov", "Dec"],
            fixedrange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(size=11, color="#4C5660"),
        ),
        yaxis=linear_yaxis,
    )

    latest_year = years[-1]
    latest_return = float(
        profiles[profiles.index.year == latest_year]["Normalized"].iloc[-1]
    )
    best_yearly_return = float(
        profiles.groupby(profiles.index.year)["Normalized"].last().max()
    )

    summary = {
        "span": f"{years[0]} to {years[-1]}",
        "years": f"{len(years)} yearly paths",
        "latest": f"{latest_year} ended {latest_return:+.1f}%",
        "best": f"Best year closed {best_yearly_return:+.1f}%",
    }

    extra_script = f"""
  <script>
    window.addEventListener("load", function () {{
      const chart = document.getElementById("chart");
      const traceIndices = Array.from({{ length: chart && chart.data ? chart.data.length : 0 }}, function (_, index) {{ return index; }});
      const yearCount = {len(years)};
      let hoveredIndex = null;
      if (!chart || !chart.on || !window.Plotly) return;

      const activeYearIndex = function () {{
        const slider = chart.layout.sliders && chart.layout.sliders[0];
        return slider && typeof slider.active === "number" ? slider.active : 0;
      }};

      const syncHighlightState = function () {{
        const activeIndex = activeYearIndex();
        const widths = traceIndices.map(function (index) {{
          return index === activeIndex || index === activeIndex + yearCount || index === hoveredIndex
            ? {HIGHLIGHT_WIDTH}
            : {BASE_LINE_WIDTH};
        }});
        const colors = traceIndices.map(function (index) {{
          return index === activeIndex || index === activeIndex + yearCount || index === hoveredIndex
            ? "{HIGHLIGHT_COLOR}"
            : "{BASE_LINE_COLOR}";
        }});
        const opacities = traceIndices.map(function (index) {{
          return index === activeIndex || index === activeIndex + yearCount || index === hoveredIndex
            ? {HIGHLIGHT_OPACITY}
            : {BASE_LINE_OPACITY};
        }});

        return Plotly.restyle(
          chart,
          {{
            "line.width": widths,
            "line.color": colors,
            "opacity": opacities
          }},
          traceIndices
        );
      }};

      syncHighlightState();
      chart.on("plotly_sliderchange", function () {{
        hoveredIndex = null;
      }});
      chart.on("plotly_hover", function (eventData) {{
        if (!eventData || !eventData.points || !eventData.points.length) return;
        const nextHoveredIndex = eventData.points[0].curveNumber;
        if (hoveredIndex === nextHoveredIndex) return;
        hoveredIndex = nextHoveredIndex;
        syncHighlightState();
      }});
      chart.on("plotly_unhover", function () {{
        if (hoveredIndex === null) return;
        hoveredIndex = null;
        syncHighlightState();
      }});
    }});
  </script>
"""

    return fig, summary, extra_script


def main() -> None:
    """Render the themed yearly-profile HTML asset."""
    profiles = load_profiles()
    fig, summary, extra_script = build_figure(profiles)
    theme.render_html(
        fig,
        SAVE_HTML_TO,
        eyebrow="Yearly returns are highly dispersed; the long-run average is rarely a typical one-year outcome.",
        title="MSCI World Yearly Trends",
        deck=(
            "Each line resets to the first trading day of its calendar year. "
            "This makes seasonality, crisis paths, and late-year recoveries "
            "comparable across decades without flattening everything into one path."
        ),
        kicker="",
        meta_items=[
            summary["span"],
            summary["years"],
            summary["latest"],
            summary["best"],
        ],
        footer_left="www.ShowMeMSCI.com | @Alexander Blinn",
        footer_right="Data: MSCI World (^990100-USD-STRD) via Yahoo Finance",
        extra_script=extra_script,
    )


if __name__ == "__main__":
    main()
