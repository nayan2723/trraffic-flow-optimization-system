"""
main.py
=======
Entry point for the Multi-Objective Traffic Flow Optimisation project.

Execution modes (controlled via argparse):
  Mode 1 – Default       : python main.py
  Mode 2 – Custom config : python main.py --config custom.json
  Mode 3 – Interactive   : python main.py --interactive

For each run, a timestamped results/ subfolder is created:
  results/YYYYMMDD_HHMMSS/
      pareto_2d.png
      pareto_3d.png
      convergence.png
      parameters_used.json
      summary.txt
"""

import argparse
import json
import os
import sys
import time

import numpy as np

from config_loader  import load_config, validate_config, interactive_config, build_sim_params
from nsga2_optimizer import (
    NSGA2,
    run_single_objective_ga,
    fixed_time_baseline,
)
from visualization import (
    plot_pareto_2d,
    plot_pareto_3d,
    plot_convergence,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _timestamp():
    return time.strftime("%Y%m%d_%H%M%S")


def _make_results_dir():
    """Create and return a timestamped results subdirectory."""
    base = os.path.join(os.path.dirname(__file__), "results")
    folder = os.path.join(base, _timestamp())
    os.makedirs(folder, exist_ok=True)
    return folder


def select_best_tradeoff(pareto_obj):
    """Knee-point: minimum sum of normalised objectives."""
    pf    = np.array(pareto_obj)
    ideal = pf.min(axis=0)
    nadir = pf.max(axis=0)
    rng   = nadir - ideal
    rng[rng == 0] = 1.0
    scores = ((pf - ideal) / rng).sum(axis=1)
    return int(np.argmin(scores))


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_param_summary(cfg):
    """Print a formatted summary of the parameters being used."""
    ar = cfg["traffic"]["arrival_rates"]
    op = cfg["optimization"]
    sc = cfg["signal_constraints"]
    ev = cfg["environment"]

    sep = "-" * 58
    print("\n" + sep)
    print(f"  {'PARAMETER SUMMARY':^56}")
    print(sep)
    print(f"  Traffic  | Arrival N={ar['north']} S={ar['south']} "
          f"E={ar['east']} W={ar['west']} veh/min")
    print(f"           | Service rate = {cfg['traffic']['service_rate']} veh/sec")
    print(f"           | Sim duration = {cfg['traffic']['simulation_time']} s")
    print(f"  Signal   | min_green = {sc['min_green']}s  |  max_cycle = {sc['max_cycle']}s")
    print(f"  Environ  | fuel_rate={ev['fuel_rate_idle']}  "
          f"emit_idle={ev['emission_idle']}  emit_stop={ev['emission_stop']}")
    print(f"  Optim.   | pop={op['population_size']}  gen={op['generations']}  "
          f"pc={op['crossover_prob']}  pm={op['mutation_prob']}  seed={op['seed']}")
    print(sep)


def print_comparison_table(fixed_obj, so_obj, best_nsga_obj, results_dir):
    sep = "-" * 62
    lines = []
    lines.append("")
    lines.append("+" + "=" * 62 + "+")
    lines.append(f"|{'  PERFORMANCE COMPARISON TABLE':^62}|")
    lines.append("+" + "=" * 62 + "+")
    lines.append(f"|  {'Method':<24} {'f1 Wait(s/veh)':>13} {'f2 Fuel':>9} {'f3 Emiss':>9}|")
    lines.append("|" + sep + "|")

    rows = [
        ("Fixed-time Baseline",    fixed_obj),
        ("Single-obj GA",          so_obj),
        ("NSGA-II Best Tradeoff",  best_nsga_obj),
    ]
    for name, obj in rows:
        f1, f2, f3 = obj
        lines.append(f"|  {name:<24} {f1:>13.4f} {f2:>9.5f} {f3:>9.5f}|")

    lines.append("+" + "=" * 62 + "+")

    f1b, f2b, f3b = fixed_obj
    f1n, f2n, f3n = best_nsga_obj
    lines.append("\n  Improvement of NSGA-II best tradeoff vs fixed baseline:")
    lines.append(f"    Delta-f1 (Wait)     : {100*(f1b-f1n)/max(abs(f1b),1e-9):+.1f}%")
    lines.append(f"    Delta-f2 (Fuel)     : {100*(f2b-f2n)/max(abs(f2b),1e-9):+.1f}%")
    lines.append(f"    Delta-f3 (Emission) : {100*(f3b-f3n)/max(abs(f3b),1e-9):+.1f}%")

    table_str = "\n".join(lines)
    print(table_str)

    # Save as summary.txt
    summary_path = os.path.join(results_dir, "summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("Multi-Objective Traffic Flow Optimization using NSGA-II\n")
        fh.write(f"Run timestamp: {_timestamp()}\n\n")
        fh.write(table_str)
    print(f"\n  Summary saved -> {summary_path}")


def save_parameters(cfg, sim_params, results_dir):
    """Save the effective parameters used in this run to parameters_used.json."""
    payload = {
        "config":     cfg,
        "sim_params": {k: (v.tolist() if hasattr(v, "tolist") else v)
                       for k, v in sim_params.items()},
    }
    path = os.path.join(results_dir, "parameters_used.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"  Parameters saved -> {path}")


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Multi-Objective Traffic Signal Optimization using NSGA-II",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                         # Mode 1: use config.json
  python main.py --config my.json        # Mode 2: custom JSON config
  python main.py --interactive           # Mode 3: interactive prompts
        """,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--config", metavar="FILE",
        help="Path to a JSON configuration file (default: config.json)",
    )
    group.add_argument(
        "--interactive", action="store_true",
        help="Interactively enter all parameters from the terminal",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # ------------------------------------------------------------------
    # 1. Load configuration
    # ------------------------------------------------------------------
    if args.interactive:
        print("\n[Mode 3] Interactive configuration")
        base_cfg = load_config()          # load file first as defaults
        cfg      = interactive_config(base_cfg)
    elif args.config:
        print(f"\n[Mode 2] Loading config from: {args.config}")
        cfg = load_config(args.config)
    else:
        print("\n[Mode 1] Loading default config.json")
        cfg = load_config()

    # Validate
    try:
        validate_config(cfg)
    except ValueError as exc:
        print(f"\n[ERROR] {exc}")
        sys.exit(1)

    # Build sim_params
    seed       = int(cfg["optimization"]["seed"])
    sim_params = build_sim_params(cfg, seed=seed)
    np.random.seed(seed)

    # Summarise
    print_param_summary(cfg)

    # Create timestamped results directory
    results_dir = _make_results_dir()
    print(f"\n  Results will be saved to: {results_dir}\n")
    print("=" * 65)
    print("  Multi-Objective Traffic Flow Optimization using NSGA-II")
    print("=" * 65)

    total_start = time.time()

    # ------------------------------------------------------------------
    # 2. Fixed-time baseline
    # ------------------------------------------------------------------
    print("\n[1/3] Evaluating fixed-time baseline ...")
    t0 = time.time()
    g_fixed, fixed_obj = fixed_time_baseline(sim_params)
    print(f"  Done in {time.time()-t0:.1f}s")
    print(f"  G       = {g_fixed.round(1).tolist()}")
    print(f"  f1={fixed_obj[0]:.4f}  f2={fixed_obj[1]:.6f}  f3={fixed_obj[2]:.6f}")

    # ------------------------------------------------------------------
    # 3. Single-objective GA
    # ------------------------------------------------------------------
    print("\n[2/3] Running single-objective GA ...")
    opt = cfg["optimization"]
    t0  = time.time()
    so_ind, so_obj, so_history = run_single_objective_ga(
        sim_params    = sim_params,
        pop_size      = int(opt["population_size"]),
        n_generations = int(opt["generations"]),
        p_cross       = float(opt["crossover_prob"]),
        p_mut         = float(opt["mutation_prob"]),
        seed          = seed + 1,
    )
    print(f"  Done in {time.time()-t0:.1f}s")
    print(f"  Best G  = {so_ind.round(1).tolist()}")
    print(f"  f1={so_obj[0]:.4f}  f2={so_obj[1]:.6f}  f3={so_obj[2]:.6f}")

    # ------------------------------------------------------------------
    # 4. NSGA-II
    # ------------------------------------------------------------------
    print("\n[3/3] Running NSGA-II ...")
    t0 = time.time()
    nsga = NSGA2(
        sim_params    = sim_params,
        pop_size      = int(opt["population_size"]),
        n_generations = int(opt["generations"]),
        p_cross       = float(opt["crossover_prob"]),
        p_mut         = float(opt["mutation_prob"]),
        seed          = seed,
    )
    pareto_front, pareto_obj, nsga_history = nsga.run()
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s  | Pareto front size = {len(pareto_front)}")

    print("\n-- Pareto Front Ranges " + "-" * 38)
    print(f"  min(f1) = {np.min(pareto_obj[:, 0]):.4f}, max(f1) = {np.max(pareto_obj[:, 0]):.4f}")
    print(f"  min(f2) = {np.min(pareto_obj[:, 1]):.4f}, max(f2) = {np.max(pareto_obj[:, 1]):.4f}")
    print(f"  min(f3) = {np.min(pareto_obj[:, 2]):.4f}, max(f3) = {np.max(pareto_obj[:, 2]):.4f}")

    # ------------------------------------------------------------------
    # 5. Best trade-off
    # ------------------------------------------------------------------
    best_idx      = select_best_tradeoff(pareto_obj)
    best_ind      = pareto_front[best_idx]
    best_nsga_obj = tuple(pareto_obj[best_idx])

    min_g = sim_params["min_green"]
    max_c = sim_params["max_cycle"]

    print("\n-- Best Trade-off Solution (NSGA-II) " + "-" * 26)
    print(f"  G = {best_ind.round(2).tolist()}")
    print(f"  f1 (Avg Wait)  = {best_nsga_obj[0]:.4f} s/veh")
    print(f"  f2 (Fuel)      = {best_nsga_obj[1]:.6f}")
    print(f"  f3 (Emission)  = {best_nsga_obj[2]:.6f}")

    # ------------------------------------------------------------------
    # 6. Constraint validation
    # ------------------------------------------------------------------
    print("\n-- Constraint Validation " + "-" * 38)
    assert all(g >= min_g - 1e-6 for g in best_ind), \
        f"VIOLATION: Gi < {min_g}  -> {best_ind}"
    assert best_ind.sum() <= max_c + 1e-6, \
        f"VIOLATION: sum(Gi)={best_ind.sum():.2f} > {max_c}"
    print(f"  OK  All Gi >= {min_g}s  (min observed = {best_ind.min():.2f}s)")
    print(f"  OK  Sum(Gi) = {best_ind.sum():.2f}s <= {max_c}s")

    for i, sol in enumerate(pareto_front):
        assert all(g >= min_g - 1e-6 for g in sol), f"Pareto[{i}] violates Gi>={min_g}"
        assert sol.sum() <= max_c + 1e-6,            f"Pareto[{i}] violates sum<={max_c}"
    print(f"  OK  All {len(pareto_front)} Pareto solutions are feasible")

    # ------------------------------------------------------------------
    # 7. Comparison table + save summary
    # ------------------------------------------------------------------
    print_comparison_table(fixed_obj, so_obj, best_nsga_obj, results_dir)

    # ------------------------------------------------------------------
    # 8. Save parameters
    # ------------------------------------------------------------------
    save_parameters(cfg, sim_params, results_dir)

    # ------------------------------------------------------------------
    # 9. Generate plots  (save to results_dir)
    # ------------------------------------------------------------------
    print("\nGenerating plots ...")
    plot_pareto_2d(pareto_obj, so_obj, fixed_obj, out_dir=results_dir)
    plot_pareto_3d(pareto_obj, so_obj, fixed_obj, out_dir=results_dir)
    plot_convergence(nsga_history, so_history,     out_dir=results_dir)

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    total_time = time.time() - total_start
    print("\n" + "=" * 65)
    print(f"  All outputs saved to: {results_dir}")
    print(f"  Total execution time: {total_time:.1f}s")
    print("=" * 65)


if __name__ == "__main__":
    main()
