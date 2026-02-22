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
# Plot 1: 2D Pareto fronts
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
