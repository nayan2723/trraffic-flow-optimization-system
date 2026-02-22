"""
visualization.py
================
Generates and saves all plots for the NSGA-II traffic optimisation project.

Outputs (saved in ./plots/):
  - pareto_2d.png    : 2-panel 2D Pareto plots
  - pareto_3d.png    : 3D scatter of Pareto front
  - convergence.png  : convergence curve across generations

Uses the non-interactive Agg backend – no display required.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")                        # headless backend (no display needed)
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D      # noqa: F401 (needed for 3D projection)

from ui import print_success, print_warning

try:
    import plotly.graph_objs as go
    import plotly.express as px
    import pandas as pd
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
PLOT_DIR = os.path.join(os.path.dirname(__file__), "plots")
os.makedirs(PLOT_DIR, exist_ok=True)


def _save(fig, filename, out_dir=None):
    directory = out_dir if out_dir else PLOT_DIR
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved -> {path}")
    return path


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
NSGA_COLOR    = "#2563eb"   # blue
SOGA_COLOR    = "#16a34a"   # green
FIXED_COLOR   = "#dc2626"   # red
BG_COLOR      = "#0f172a"   # dark slate
GRID_COLOR    = "#334155"
TEXT_COLOR    = "#e2e8f0"


def _apply_dark_style(ax, title, xlabel, ylabel, zlabel=None):
    """Apply a consistent dark-theme style to an axis."""
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.set_title(title, color=TEXT_COLOR, fontsize=11, pad=8)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    if zlabel:
        ax.zaxis.label.set_color(TEXT_COLOR)
        ax.set_zlabel(zlabel, fontsize=9)
    ax.grid(True, color=GRID_COLOR, linewidth=0.5, linestyle="--")

# ===========================================================================
# Plotly HTML Renderers
# ===========================================================================

def plot_pareto_interactive(pareto_df, out_dir=None):
    """
    3-D interactive scatter plot of the Pareto front using Plotly.
    Saves as pareto_interactive.html
    """
    if not PLOTLY_AVAILABLE:
        print_warning("Plotly not available. Skipping interactive 3D plot.")
        return None

    path = os.path.join(out_dir or PLOT_DIR, "pareto_interactive.html")
    
    hover_template = (
        "<b>Solution %{customdata[0]}</b><br>" +
        "G_North: %{customdata[1]:.1f}s<br>" +
        "G_South: %{customdata[2]:.1f}s<br>" +
        "G_East: %{customdata[3]:.1f}s<br>" +
        "G_West: %{customdata[4]:.1f}s<br><br>" +
        "Wait Time: %{x:.2f} s/veh<br>" +
        "Fuel: %{y:.2f}<br>" +
        "Emissions: %{z:.2f}<extra></extra>"
    )

    fig = go.Figure(data=[go.Scatter3d(
        x=pareto_df['f1_wait'],
        y=pareto_df['f2_fuel'],
        z=pareto_df['f3_emission'],
        mode='markers',
        customdata=pareto_df[['index', 'G_North', 'G_South', 'G_East', 'G_West']].values,
        hovertemplate=hover_template,
        marker=dict(
            size=6,
            color=pareto_df['f1_wait'],
            colorscale='Viridis',
            colorbar=dict(title="f1 (Wait Time)"),
            opacity=0.8
        )
    )])

    fig.update_layout(
        title="Interactive 3D Pareto Front",
        scene=dict(
            xaxis_title="f1 (Wait Time)",
            yaxis_title="f2 (Fuel)",
            zaxis_title="f3 (Emissions)"
        ),
        template="plotly_dark",
        margin=dict(l=0, r=0, b=0, t=40)
    )

    fig.write_html(path, include_plotlyjs='cdn')
    print_success(f"Saved interactive 3D -> {path}")
    return path


def plot_pareto_annotated(pareto_df, out_dir=None):
    """
    2-D annotated scatter plot (Wait vs Fuel) using Plotly.
    Highlights extreme points dynamically. Saves as pareto_annotated.html
    """
    if not PLOTLY_AVAILABLE:
        print_warning("Plotly not available. Skipping annotated 2D plot.")
        return None

    path = os.path.join(out_dir or PLOT_DIR, "pareto_annotated.html")
    
    # Identify extremes
    idx_min_wait = pareto_df['f1_wait'].idxmin()
    idx_min_fuel = pareto_df['f2_fuel'].idxmin()
    idx_min_emis = pareto_df['f3_emission'].idxmin()

    # Assign markers
    sizes = [10] * len(pareto_df)
    symbols = ['circle'] * len(pareto_df)
    texts = [''] * len(pareto_df)
    
    sizes[idx_min_wait] = 16
    sizes[idx_min_fuel] = 16
    sizes[idx_min_emis] = 16
    
    symbols[idx_min_wait] = 'star'
    symbols[idx_min_fuel] = 'diamond'
    symbols[idx_min_emis] = 'square'
    
    texts[idx_min_wait] = 'Min Waiting'
    texts[idx_min_fuel] = 'Min Fuel'
    texts[idx_min_emis] = 'Min Emission'

    pareto_df_copy = pareto_df.copy()
    pareto_df_copy['Size'] = sizes
    pareto_df_copy['Symbol'] = symbols
    pareto_df_copy['Annotation'] = texts

    fig = px.scatter(
        pareto_df_copy,
        x='f1_wait', 
        y='f2_fuel',
        hover_data=['index', 'G_North', 'G_South', 'G_East', 'G_West', 'f3_emission'],
        text='Annotation',
        size='Size',
        size_max=16,
        symbol='Symbol',
        color='f1_wait',
        color_continuous_scale="Viridis",
        title="Annotated Pareto Extremes (Wait Time vs Fuel)"
    )

    fig.update_traces(textposition='top center', textfont=dict(size=14, color='white'))
    fig.update_layout(template="plotly_dark")

    fig.write_html(path, include_plotlyjs='cdn')
    print_success(f"Saved annotated 2D -> {path}")
    return path


def plot_before_after(fixed_stats, single_ga_stats, nsga_stats, out_dir=None):
    """
    Grouped bar chart comparing Fixed-Time, Single-Objective GA, and NSGA-II.
    Saves as before_after.html
    """
    if not PLOTLY_AVAILABLE:
        print_warning("Plotly not available. Skipping before/after chart.")
        return None

    path = os.path.join(out_dir or PLOT_DIR, "before_after.html")

    methods = ['Fixed-Time', 'Single-Obj GA', 'NSGA-II (Balanced)']
    wait_times = [fixed_stats[0], single_ga_stats[0], nsga_stats[0]]
    fuels      = [fixed_stats[1], single_ga_stats[1], nsga_stats[1]]
    emissions  = [fixed_stats[2], single_ga_stats[2], nsga_stats[2]]

    fig = go.Figure(data=[
        go.Bar(name='Wait (s/veh)', x=methods, y=wait_times, text=[f"{val:.1f}" for val in wait_times], textposition='auto'),
        go.Bar(name='Fuel Index', x=methods, y=fuels, text=[f"{val:.1f}" for val in fuels], textposition='auto'),
        go.Bar(name='Emissions', x=methods, y=emissions, text=[f"{val:.1f}" for val in emissions], textposition='auto')
    ])

    fig.update_layout(
        barmode='group',
        title="Before vs After: Optimization Performance Comparison",
        xaxis_title="Optimization Method",
        yaxis_title="Metric Value",
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.write_html(path, include_plotlyjs='cdn')
    print_success(f"Saved before/after comparison -> {path}")
    return path


def plot_green_heatmap(pareto_df, out_dir=None):
    """
    Heatmap of green time distributions across all Pareto solutions.
    Saves as green_times_heatmap.html
    """
    if not PLOTLY_AVAILABLE:
        print_warning("Plotly not available. Skipping heatmap.")
        return None

    path = os.path.join(out_dir or PLOT_DIR, "green_times_heatmap.html")

    # Extract green times matrix
    g_cols = ['G_North', 'G_South', 'G_East', 'G_West']
    z_data = pareto_df[g_cols].values

    fig = px.imshow(
        z_data,
        labels=dict(x="Direction", y="Pareto Solution Index", color="Green Time (s)"),
        x=['North', 'South', 'East', 'West'],
        y=pareto_df['index'].astype(str),
        color_continuous_scale="Viridis",
        aspect="auto"
    )

    fig.update_traces(
        hovertemplate="Solution %{y}<br>Direction: %{x}<br>Green Time: %{z:.1f}s<extra></extra>"
    )

    fig.update_layout(
        title="Green Time Distribution across Pareto Solutions",
        template="plotly_dark"
    )

    fig.write_html(path, include_plotlyjs='cdn')
    print_success(f"Saved green times heatmap -> {path}")
    return path


# ===========================================================================
# Plot 1: 2D Pareto fronts (Static Fallback)
# ===========================================================================

def plot_pareto_2d(pareto_obj,
                   so_obj=None,
                   fixed_obj=None,
                   out_dir=None):
    """
    Plot two 2-D projections of the Pareto front.

    Parameters
    ----------
    pareto_obj : ndarray, shape (K, 3)  – NSGA-II Pareto front objectives
    so_obj     : tuple (f1, f2, f3)     – single-obj GA best solution
    fixed_obj  : tuple (f1, f2, f3)     – fixed-time baseline objectives
    """
    print("Generating pareto_2d.png …")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor(BG_COLOR)

    # Sort Pareto front by f1 for a cleaner line
    order    = np.argsort(pareto_obj[:, 0])
    pf       = pareto_obj[order]

    # ---- Panel A: f1 vs f2 ----
    ax = axes[0]
    ax.set_facecolor(BG_COLOR)
    ax.scatter(pf[:, 0], pf[:, 1],
               c=NSGA_COLOR, s=60, zorder=3, label="NSGA-II Pareto front")
    ax.plot   (pf[:, 0], pf[:, 1],
               color=NSGA_COLOR, linewidth=1.2, alpha=0.6, zorder=2)

    if so_obj is not None:
        ax.scatter(so_obj[0], so_obj[1], c=SOGA_COLOR, s=120,
                   marker="*", zorder=4, label="Single-obj GA")
    if fixed_obj is not None:
        ax.scatter(fixed_obj[0], fixed_obj[1], c=FIXED_COLOR, s=120,
                   marker="D", zorder=4, label="Fixed-time baseline")

    _apply_dark_style(ax, "Pareto Front: Waiting Time vs Fuel",
                      "f₁ – Avg Wait Time (s/veh)",
                      "f₂ – Fuel Consumption Index")
    ax.legend(facecolor="#1e293b", edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, fontsize=8)

    # ---- Panel B: f1 vs f3 ----
    ax = axes[1]
    ax.set_facecolor(BG_COLOR)
    ax.scatter(pf[:, 0], pf[:, 2],
               c="#7c3aed", s=60, zorder=3, label="NSGA-II Pareto front")
    ax.plot   (pf[:, 0], pf[:, 2],
               color="#7c3aed", linewidth=1.2, alpha=0.6, zorder=2)

    if so_obj is not None:
        ax.scatter(so_obj[0], so_obj[2], c=SOGA_COLOR, s=120,
                   marker="*", zorder=4, label="Single-obj GA")
    if fixed_obj is not None:
        ax.scatter(fixed_obj[0], fixed_obj[2], c=FIXED_COLOR, s=120,
                   marker="D", zorder=4, label="Fixed-time baseline")

    _apply_dark_style(ax, "Pareto Front: Waiting Time vs Emission",
                      "f₁ – Avg Wait Time (s/veh)",
                      "f₃ – Emission Index (g CO₂-eq)")
    ax.legend(facecolor="#1e293b", edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, fontsize=8)

    fig.suptitle("NSGA-II Multi-Objective Traffic Optimisation – 2D Pareto Fronts",
                 color=TEXT_COLOR, fontsize=13, y=1.02)
    return _save(fig, "pareto_2d.png", out_dir)


# ===========================================================================
# Plot 2: 3D Pareto scatter
# ===========================================================================

def plot_pareto_3d(pareto_obj,
                   so_obj=None,
                   fixed_obj=None,
                   out_dir=None):
    """
    3-D scatter plot of the full Pareto front.
    """
    print("Generating pareto_3d.png …")
    fig = plt.figure(figsize=(9, 7))
    fig.patch.set_facecolor(BG_COLOR)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(BG_COLOR)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor(GRID_COLOR)
    ax.yaxis.pane.set_edgecolor(GRID_COLOR)
    ax.zaxis.pane.set_edgecolor(GRID_COLOR)

    # Colour-map the Pareto points by f1
    sc = ax.scatter(pareto_obj[:, 0],
                    pareto_obj[:, 1],
                    pareto_obj[:, 2],
                    c=pareto_obj[:, 0], cmap="plasma",
                    s=60, alpha=0.85, label="NSGA-II Pareto front", zorder=3)

    cbar = fig.colorbar(sc, ax=ax, pad=0.1, shrink=0.6)
    cbar.set_label("f₁ – Avg Wait (s/veh)", color=TEXT_COLOR, fontsize=9)
    cbar.ax.tick_params(colors=TEXT_COLOR)

    if so_obj is not None:
        ax.scatter(*so_obj, c=SOGA_COLOR, s=180, marker="*",
                   zorder=5, label="Single-obj GA")
    if fixed_obj is not None:
        ax.scatter(*fixed_obj, c=FIXED_COLOR, s=180, marker="D",
                   zorder=5, label="Fixed-time baseline")

    ax.set_xlabel("f₁ – Avg Wait (s/veh)", color=TEXT_COLOR, fontsize=8, labelpad=8)
    ax.set_ylabel("f₂ – Fuel Index",        color=TEXT_COLOR, fontsize=8, labelpad=8)
    ax.set_zlabel("f₃ – Emission Index",    color=TEXT_COLOR, fontsize=8, labelpad=8)
    ax.set_title("NSGA-II 3D Pareto Front",  color=TEXT_COLOR, fontsize=12, pad=12)
    ax.tick_params(colors=TEXT_COLOR, labelsize=8)
    ax.legend(facecolor="#1e293b", edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, fontsize=8)

    return _save(fig, "pareto_3d.png", out_dir)


# ===========================================================================
# Plot 3: Convergence curve
# ===========================================================================

def plot_convergence(nsga_history,
                     so_history=None,
                     out_dir=None):
    """
    Plot the best f1 value per generation for NSGA-II (and optionally
    for the single-objective GA).

    Parameters
    ----------
    nsga_history : list of float
    so_history   : list of float (optional)
    """
    print("Generating convergence.png …")
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    gens_nsga = list(range(1, len(nsga_history) + 1))
    ax.plot(gens_nsga, nsga_history,
            color=NSGA_COLOR, linewidth=2.0,
            label="NSGA-II (best f₁ per gen)", zorder=3)
    ax.fill_between(gens_nsga, nsga_history,
                    min(nsga_history), alpha=0.15, color=NSGA_COLOR)

    if so_history is not None:
        gens_so = list(range(1, len(so_history) + 1))
        ax.plot(gens_so, so_history,
                color=SOGA_COLOR, linewidth=2.0,
                linestyle="--", label="Single-obj GA (best f₁)", zorder=3)

    _apply_dark_style(ax,
                      "Convergence Curve – Best f₁ per Generation",
                      "Generation",
                      "Best f₁ – Avg Wait Time (s/veh)")
    ax.legend(facecolor="#1e293b", edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, fontsize=9)

    # Annotate final best
    ax.annotate(f"  Final: {nsga_history[-1]:.3f}",
                xy=(gens_nsga[-1], nsga_history[-1]),
                color=TEXT_COLOR, fontsize=9)

    return _save(fig, "convergence.png", out_dir)


# ===========================================================================
# Quick self-test
# ===========================================================================
if __name__ == "__main__":
    print("=== Visualization Self-Test ===")
    rng = np.random.default_rng(0)
    # Dummy Pareto front (20 synthetic solutions)
    f1 = np.linspace(50, 200, 20) + rng.normal(0, 5, 20)
    f2 = 1200 - f1 * 4 + rng.normal(0, 20, 20)
    f3 = 3000 - f1 * 10 + rng.normal(0, 50, 20)
    pf_obj = np.column_stack([f1, f2, f3])

    so_obj    = (80.0, 1000.0, 2200.0)
    fixed_obj = (160.0, 700.0, 1600.0)

    p1 = plot_pareto_2d(pf_obj, so_obj, fixed_obj)
    p2 = plot_pareto_3d(pf_obj, so_obj, fixed_obj)
    history = list(np.linspace(180, 80, 60) + rng.normal(0, 3, 60))
    p3 = plot_convergence(history)
    print("Self-test PASSED.")
