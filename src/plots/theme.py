"""
Shared editorial theme for standalone Plotly chart pages.

This module centralizes:
- reusable color helpers
- the base editorial palette
- common Plotly layout defaults
- the shared HTML shell used by standalone chart pages
"""

from __future__ import annotations

from html import escape
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

INK = "#28313A"
MUTED = "#5C6770"
GRID = "rgba(35, 48, 59, 0.12)"
GRID_SOFT = "rgba(35, 48, 59, 0.07)"
PAPER = "#F6F2E9"
PAPER_SOFT = "rgba(248, 245, 238, 0.84)"
NEGATIVE = "#73515E"
NEGATIVE_SOFT = "#A07A72"
NEUTRAL = "#B59B74"
POSITIVE_SOFT = "#8AA8A8"
POSITIVE = "#587A86"
POSITIVE_DARK = "#456674"
SITE_URL = "https://showmemsci.com"

INTERVAL_COLORS = [
    "#60434F",
    "#6C4B57",
    "#79535F",
    "#876068",
    "#9A716F",
    "#AF8777",
    "#B59B74",
    "#98ACA1",
    "#7E9EA0",
    "#678E98",
    "#507884",
    "#3E6170",
]

PLOTLY_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["toImage", "select2d", "lasso2d"],
    "scrollZoom": False,
    "doubleClick": "reset",
    "responsive": True,
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """Convert a hex string into RGB components."""
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def mix_hex(base: str, target: str, factor: float) -> str:
    """Mix two colors by a factor between 0 and 1."""
    factor = max(0.0, min(1.0, factor))
    base_rgb = hex_to_rgb(base)
    target_rgb = hex_to_rgb(target)
    mixed = tuple(
        round(base_component + (target_component - base_component) * factor)
        for base_component, target_component in zip(base_rgb, target_rgb)
    )
    return "#{:02X}{:02X}{:02X}".format(*mixed)


def sample_palette(colors: list[str], count: int) -> list[str]:
    """Resample a palette so it fits any number of intervals."""
    if count <= 0:
        return []
    if count == 1:
        return [colors[len(colors) // 2]]

    sampled = []
    positions = np.linspace(0, len(colors) - 1, count)
    for position in positions:
        low = int(np.floor(position))
        high = int(np.ceil(position))
        if low == high:
            sampled.append(colors[low])
            continue
        sampled.append(mix_hex(colors[low], colors[high], position - low))
    return sampled


def merge_dicts(base: dict, override: dict) -> dict:
    """Recursively merge two dictionaries."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def style_updatemenus(updatemenus: list) -> list[dict]:
    """Apply shared editorial defaults to Plotly button groups."""
    defaults = {
        "bgcolor": "rgba(248,245,238,0.96)",
        "bordercolor": "rgba(61,69,77,0.14)",
        "borderwidth": 1,
        "font": {
            "family": "Aptos, Segoe UI, sans-serif",
            "size": 11,
            "color": "#31404B",
        },
        "pad": {"r": 10, "t": 0, "b": 10, "l": 0},
    }

    styled = []
    for menu in updatemenus:
        menu_dict = (
            menu.to_plotly_json() if hasattr(menu, "to_plotly_json") else dict(menu)
        )
        styled.append(merge_dicts(defaults, menu_dict))
    return styled


def canonical_url_for_path(output_path: Path) -> str:
    """Resolve a site-relative output path to its public canonical URL."""
    try:
        relative_path = output_path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        relative_path = Path(output_path.name)

    relative_url = relative_path.as_posix()
    if relative_url in {"", ".", "index.html"}:
        return f"{SITE_URL}/"
    return f"{SITE_URL}/{relative_url}"


def style_sliders(sliders: list) -> list[dict]:
    """Apply shared editorial defaults to Plotly sliders."""
    defaults = {
        "bgcolor": "rgba(248,245,238,0.78)",
        "bordercolor": "rgba(61,69,77,0.12)",
        "borderwidth": 1,
        "tickcolor": "rgba(61,69,77,0.28)",
        "font": {
            "family": "Aptos, Segoe UI, sans-serif",
            "size": 10,
            "color": "#31404B",
        },
        "currentvalue": {
            "font": {
                "family": "Aptos, Segoe UI, sans-serif",
                "size": 11,
                "color": "#31404B",
            }
        },
        "pad": {"t": 22, "b": 0},
    }

    styled = []
    for slider in sliders:
        slider_dict = (
            slider.to_plotly_json()
            if hasattr(slider, "to_plotly_json")
            else dict(slider)
        )
        styled.append(merge_dicts(defaults, slider_dict))
    return styled


def apply_to_figure(
    fig: go.Figure,
    *,
    xaxis: dict | None = None,
    yaxis: dict | None = None,
    **layout_overrides,
) -> None:
    """Apply the shared editorial Plotly defaults to a figure."""
    layout = {
        "autosize": True,
        "font": {"family": "Aptos, Segoe UI, sans-serif", "color": INK},
        "hoverlabel": {
            "bgcolor": PAPER,
            "bordercolor": "#65737F",
            "font": {
                "color": INK,
                "family": "Aptos, Segoe UI, sans-serif",
                "size": 12,
            },
        },
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "dragmode": False,
    }
    if xaxis is not None:
        layout["xaxis"] = xaxis
    if yaxis is not None:
        layout["yaxis"] = yaxis
    layout.update(layout_overrides)
    fig.update_layout(**layout)

    if fig.layout.updatemenus:
        fig.update_layout(updatemenus=style_updatemenus(list(fig.layout.updatemenus)))

    if fig.layout.sliders:
        fig.update_layout(sliders=style_sliders(list(fig.layout.sliders)))

    if fig.layout.legend:
        fig.update_layout(
            legend=merge_dicts(
                {
                    "bgcolor": PAPER_SOFT,
                    "bordercolor": "rgba(61,69,77,0.10)",
                    "borderwidth": 1,
                    "font": {
                        "family": "Aptos, Segoe UI, sans-serif",
                        "size": 11,
                        "color": "#31404B",
                    },
                },
                fig.layout.legend.to_plotly_json(),
            )
        )


def render_html(
    fig: go.Figure,
    save_to: Path,
    *,
    eyebrow: str,
    title: str,
    deck: str,
    kicker: str,
    meta_items: list[str],
    footer_left: str,
    footer_right: str,
    config: dict | None = None,
    chart_shell_height: int = 620,
    chart_shell_height_mobile: int = 620,
    include_mathjax: bool | str = False,
    responsive_bar_text_breakpoint: int | None = None,
    extra_script: str | None = None,
) -> None:
    """Render a standalone HTML page around a Plotly figure using the shared theme."""
    plot_fragment = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs=False,
        include_mathjax=include_mathjax,
        config=config or PLOTLY_CONFIG,
        div_id="chart",
    )

    meta_html = "".join(
        f'<span class="meta-pill">{label}</span>' for label in meta_items if label
    )
    page_title = f"{title} | ShowMeMSCI"
    description = " ".join(deck.split()) or f"Interactive MSCI World chart: {title}."
    canonical_url = canonical_url_for_path(save_to)
    page_title_html = escape(page_title, quote=True)
    description_html = escape(description, quote=True)
    canonical_url_html = escape(canonical_url, quote=True)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page_title_html}</title>
  <meta name="description" content="{description_html}" />
  <meta name="robots" content="index,follow,max-image-preview:large" />
  <link rel="canonical" href="{canonical_url_html}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="ShowMeMSCI" />
  <meta property="og:title" content="{page_title_html}" />
  <meta property="og:description" content="{description_html}" />
  <meta property="og:url" content="{canonical_url_html}" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{page_title_html}" />
  <meta name="twitter:description" content="{description_html}" />
  <script src="https://cdn.plot.ly/plotly-3.0.1.min.js"></script>
  <style>
    :root {{
      --paper: #F2EEE6;
      --paper-2: #ECE6DC;
      --ink: #23303B;
      --muted: rgba(35, 48, 59, 0.68);
      --line: rgba(35, 48, 59, 0.12);
      --shadow: 0 20px 48px rgba(18, 24, 30, 0.16);
      --chart-shell-height: {chart_shell_height}px;
      --chart-shell-height-mobile: {chart_shell_height_mobile}px;
    }}

    * {{
      box-sizing: border-box;
    }}

    html,
    body {{
      width: 100%;
      height: auto;
      min-height: 100%;
      margin: 0;
      overflow: visible;
      color: var(--ink);
      background:
        radial-gradient(110% 90% at 100% 0%, rgba(104, 132, 138, 0.10), transparent 46%),
        radial-gradient(80% 70% at 0% 100%, rgba(133, 98, 109, 0.08), transparent 42%),
        linear-gradient(180deg, var(--paper) 0%, var(--paper-2) 100%);
      font-family: Aptos, "Segoe UI", sans-serif;
    }}

    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      opacity: 0.08;
      background-image:
        linear-gradient(rgba(35, 48, 59, 0.28) 1px, transparent 1px),
        linear-gradient(90deg, rgba(35, 48, 59, 0.20) 1px, transparent 1px);
      background-size: 34px 34px;
      mask-image: linear-gradient(180deg, black, transparent 88%);
    }}

    .sheet {{
      height: auto;
      min-height: 100%;
      padding: 16px 18px 14px;
      display: grid;
      grid-template-rows: auto auto auto auto;
      gap: 10px;
    }}

    .eyebrow {{
      margin: 0;
      color: rgba(35, 48, 59, 0.56);
      text-transform: uppercase;
      letter-spacing: 0.18em;
      font-size: 10px;
      font-weight: 700;
    }}

    .hero {{
      display: grid;
      gap: 8px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 10px;
    }}

    .title-row {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: end;
    }}

    .title {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(28px, 3.8vw, 40px);
      line-height: 0.98;
      letter-spacing: -0.03em;
    }}

    .deck {{
      margin: 0;
      max-width: 84ch;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }}

    .kicker {{
      margin: 0;
      min-width: 170px;
      text-align: right;
      font-size: 11px;
      line-height: 1.35;
      color: rgba(35, 48, 59, 0.58);
    }}

    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}

    .meta-pill {{
      display: inline-flex;
      align-items: center;
      padding: 7px 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.42);
      font-size: 11px;
      line-height: 1;
      color: #31404B;
    }}

    .chart-shell {{
      height: var(--chart-shell-height);
      min-height: var(--chart-shell-height);
      overflow: hidden;
      border-radius: 20px;
      border: 1px solid rgba(35, 48, 59, 0.10);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.42), rgba(255,255,255,0.22)),
        linear-gradient(180deg, #F8F5EE, #F1ECE1);
      box-shadow: var(--shadow);
      position: relative;
    }}

    .chart-shell::before {{
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.48), transparent 22%),
        linear-gradient(90deg, rgba(35,48,59,0.03), transparent 16%, transparent 84%, rgba(35,48,59,0.03));
    }}

    #chart,
    #chart > div,
    #chart .js-plotly-plot,
    #chart .plot-container {{
      width: 100% !important;
      height: 100% !important;
    }}

    .footnote {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      border-top: 1px solid var(--line);
      padding-top: 8px;
      color: rgba(35, 48, 59, 0.58);
      font-size: 11px;
      line-height: 1.35;
    }}

    .footnote span:last-child {{
      text-align: right;
    }}

    .js-plotly-plot .plotly .modebar {{
      display: none !important;
    }}

    @media (max-width: 760px) {{
      .chart-shell {{
        height: var(--chart-shell-height-mobile);
        min-height: var(--chart-shell-height-mobile);
      }}

      .title-row {{
        display: grid;
        gap: 8px;
      }}

      .kicker {{
        text-align: left;
      }}

      .footnote {{
        font-size: 10px;
      }}
    }}
  </style>
</head>
<body>
  <div class="sheet">
    <p class="eyebrow">{eyebrow}</p>

    <header class="hero">
      <div class="title-row">
        <div>
          <h1 class="title">{title}</h1>
          <p class="deck">{deck}</p>
        </div>
        <p class="kicker">{kicker}</p>
      </div>
      <div class="meta">{meta_html}</div>
    </header>

    <section class="chart-shell">
      {plot_fragment}
    </section>

    <footer class="footnote">
      <span>{footer_left}</span>
      <span>{footer_right}</span>
    </footer>
  </div>

  <script>
    window.addEventListener("load", function () {{
      const chart = document.getElementById("chart");
      const shell = document.querySelector(".chart-shell");
      const barTextBreakpoint = {responsive_bar_text_breakpoint if responsive_bar_text_breakpoint is not None else "null"};
      let frameReadySent = false;
      if (!chart) return;

      const applyFinish = function () {{
        chart.querySelectorAll(".barlayer .trace path").forEach(function (bar) {{
          bar.style.filter = "drop-shadow(0 8px 12px rgba(18, 24, 30, 0.10))";
        }});
      }};

      const reportFrameHeight = function () {{
        if (window.self === window.top) return;
        const sheet = document.querySelector(".sheet");
        let height = 0;

        if (sheet) {{
          const sheetRect = sheet.getBoundingClientRect();
          const sheetStyle = window.getComputedStyle(sheet);
          const paddingBottom = Number.parseFloat(sheetStyle.paddingBottom) || 0;
          const contentBottom = Array.from(sheet.children).reduce(function (maxBottom, child) {{
            return Math.max(maxBottom, child.getBoundingClientRect().bottom);
          }}, sheetRect.top);
          height = Math.ceil(contentBottom - sheetRect.top + paddingBottom);
        }}

        if (!height) {{
          const docEl = document.documentElement;
          const body = document.body;
          height = Math.max(
            docEl ? docEl.scrollHeight : 0,
            body ? body.scrollHeight : 0
          );
        }}

        if (height > 0) {{
          window.parent.postMessage({{
            type: "showmemsci:frame-height",
            height: height
          }}, "*");
        }}
      }};

      const reportFrameReady = function () {{
        if (frameReadySent || window.self === window.top) return;
        frameReadySent = true;
        window.parent.postMessage({{
          type: "showmemsci:frame-ready"
        }}, "*");
      }};

      const syncBarText = function () {{
        if (!window.Plotly || barTextBreakpoint === null) return Promise.resolve();
        const barIndices = chart.data
          .map(function (trace, index) {{ return trace.type === "bar" ? index : -1; }})
          .filter(function (index) {{ return index >= 0; }});

        if (!barIndices.length) return Promise.resolve();
        const showText = shell && shell.clientWidth >= barTextBreakpoint;
        return Plotly.restyle(
          chart,
          {{
            textposition: showText ? "inside" : "none",
            textangle: 0
          }},
          barIndices
        );
      }};

      const syncPlotSize = function () {{
        if (!shell || !window.Plotly) {{
          reportFrameHeight();
          reportFrameReady();
          return;
        }}
        Plotly.relayout(chart, {{
          width: Math.max(320, shell.clientWidth - 2),
          height: Math.max(320, shell.clientHeight - 2)
        }})
          .then(syncBarText)
          .then(applyFinish)
          .then(reportFrameHeight)
          .then(reportFrameReady);
      }};

      syncPlotSize();
      window.addEventListener("resize", syncPlotSize);
      window.addEventListener("load", reportFrameHeight);
      window.setTimeout(reportFrameHeight, 160);
      window.setTimeout(reportFrameHeight, 700);

      if (window.ResizeObserver) {{
        const resizeObserver = new ResizeObserver(reportFrameHeight);
        resizeObserver.observe(document.documentElement);
        if (document.body) {{
          resizeObserver.observe(document.body);
        }}
        if (shell) {{
          resizeObserver.observe(shell);
        }}
      }}

      if (chart.on) {{
        chart.on("plotly_afterplot", applyFinish);
        chart.on("plotly_hover", applyFinish);
        chart.on("plotly_unhover", applyFinish);
      }}
    }});
  </script>
  {extra_script or ""}
</body>
</html>
"""
    save_to.write_text(html, encoding="utf-8")
