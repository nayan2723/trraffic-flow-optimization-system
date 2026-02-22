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
from ui import print_header, print_info, print_success, print_error, print_warning, ask_user, print_sub_header
from nsga2_optimizer import (
    NSGA2,
    run_single_objective_ga,
    fixed_time_baseline,
)
from visualization import (
    plot_pareto_2d,
    plot_pareto_3d,
    plot_convergence,
    plot_pareto_interactive,
    plot_pareto_annotated,
    plot_before_after,
    plot_green_heatmap,
    PLOTLY_AVAILABLE
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _timestamp():
    return time.strftime("%Y%m%d_%H%M%S")


def _make_results_dir(scenario_name="run"):
    """Create and return a timestamped results subdirectory."""
    base = os.path.join(os.path.dirname(__file__), "results")
    folder = os.path.join(base, f"{scenario_name}_{_timestamp()}")
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

    print_header("PARAMETER SUMMARY")
    print_info(f"  Traffic  | Arrival N={ar['north']} S={ar['south']} E={ar['east']} W={ar['west']} veh/min")
    print_info(f"           | Service rate = {cfg['traffic']['service_rate']} veh/sec")
    print_info(f"           | Sim duration = {cfg['traffic']['simulation_time']} s")
    print_info(f"  Signal   | min_green = {sc['min_green']}s  |  max_cycle = {sc['max_cycle']}s")
    print_info(f"  Environ  | fuel_rate={ev['fuel_rate_idle']}  emit_idle={ev['emission_idle']}  emit_stop={ev['emission_stop']}")
    print_info(f"  Optim.   | pop={op['population_size']}  gen={op['generations']}  pc={op['crossover_prob']}  pm={op['mutation_prob']}  seed={op['seed']}")
    print_info("-" * 40)


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
    print_success(f"Parameters saved \u2192 {path}")


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
    parser.add_argument("--export-csv", action="store_true", help="Export Pareto solutions to CSV")
    parser.add_argument("--export-json", action="store_true", help="Export Pareto solutions to JSON")
    parser.add_argument("--explain", action="store_true", help="Print an automated explanation string based on the best tradeoff")
    parser.add_argument("--sensitivity", type=str, metavar="PARAM", help="Run a sensitivity analysis on a parameter (e.g. arrival_rate)")
    
    # Plotly Visuals
    parser.add_argument("--static", action="store_true", help="Generate PNGs instead of HTML")
    parser.add_argument("--open", action="store_true", help="Automatically open HTML files in browser")
    parser.add_argument("--visual", type=str, choices=["interactive", "static"], default="interactive", help="Default visualization mode")
    
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Sensitivity Analysis
# ---------------------------------------------------------------------------

def run_sensitivity_analysis(base_cfg):
    """Run NSGA-II for base, -20%, and +20% arrival rates to compare Pareto fronts."""
    print_header("SENSITIVITY ANALYSIS: ARRIVAL RATES (+/- 20%)")
    
    variations = [
        ("Base", 1.0),
        ("-20% Traffic", 0.8),
        ("+20% Traffic", 1.2)
    ]
    
    results = {}
    import copy
    
    for label, multiplier in variations:
        cfg = copy.deepcopy(base_cfg)
        for k in cfg["traffic"]["arrival_rates"]:
            cfg["traffic"]["arrival_rates"][k] *= multiplier
            
        print_info(f"\nRunning {label} scenario (Multiplier: x{multiplier:.1f}) ...")
        
        sim_params = build_sim_params(cfg, seed=int(cfg["optimization"]["seed"]))
        opt = cfg["optimization"]
        
        nsga = NSGA2(
            sim_params    = sim_params,
            pop_size      = int(opt["population_size"]),
            n_generations = int(opt["generations"]),
            p_cross       = float(opt["crossover_prob"]),
            p_mut         = float(opt["mutation_prob"]),
            seed          = int(opt["seed"]),
        )
        
        pareto_front, pareto_obj, _ = nsga.run()
        results[label] = pareto_obj
        
    print_header("SENSITIVITY ANALYSIS RESULTS")
    print_info(f"{'Scenario':<15} | {'Wait (Min/Max)':<15} | {'Fuel (Min/Max)':<15} | {'Emiss (Min/Max)':<15}")
    print_info("-" * 70)
    for label, obj in results.items():
        wait_min, wait_max = np.min(obj[:, 0]), np.max(obj[:, 0])
        fuel_min, fuel_max = np.min(obj[:, 1]), np.max(obj[:, 1])
        emis_min, emis_max = np.min(obj[:, 2]), np.max(obj[:, 2])
        print_info(f"{label:<15} | {wait_min:.1f} / {wait_max:.1f} | {fuel_min:.2f} / {fuel_max:.2f} | {emis_min:.2f} / {emis_max:.2f}")
    
    print_success("\nSensitivity analysis complete. Note how Pareto boundaries shift with density.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # ------------------------------------------------------------------
    # 1. Load configuration
    # ------------------------------------------------------------------
    scenario_name = "default"
    if args.interactive:
        print_info("\n[Mode 3] Interactive configuration")
        base_cfg = load_config()          # load file first as defaults
        cfg      = interactive_config(base_cfg)
        scenario_name = cfg.get("scenario_name", "interactive")
    elif args.config:
        print_info(f"\n[Mode 2] Loading config from: {args.config}")
        cfg = load_config(args.config)
        scenario_name = "custom"
    else:
        print_info("\n[Mode 1] Loading default config.json")
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

    if args.sensitivity:
        run_sensitivity_analysis(cfg)
        return

    # Summarise
    print_param_summary(cfg)

    # Create timestamped results directory
    results_dir = _make_results_dir(scenario_name)
    print_info(f"\n  Results will be saved to: {results_dir}\n")
    print_header("Optimization Workflow Started")

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
    print_success(f"NSGA-II Done in {elapsed:.1f}s  | Pareto front size = {len(pareto_front)}")

    print_sub_header("Pareto Front Ranges")
    print_info(f"  min(f1) = {np.min(pareto_obj[:, 0]):.4f}, max(f1) = {np.max(pareto_obj[:, 0]):.4f}")
    print_info(f"  min(f2) = {np.min(pareto_obj[:, 1]):.4f}, max(f2) = {np.max(pareto_obj[:, 1]):.4f}")
    print_info(f"  min(f3) = {np.min(pareto_obj[:, 2]):.4f}, max(f3) = {np.max(pareto_obj[:, 2]):.4f}")

    # ------------------------------------------------------------------
    # 5. Best trade-off
    # ------------------------------------------------------------------
    best_idx      = select_best_tradeoff(pareto_obj)
    best_ind      = pareto_front[best_idx]
    best_nsga_obj = tuple(pareto_obj[best_idx])

    min_g = sim_params["min_green"]
    max_c = sim_params["max_cycle"]

    print_sub_header("Best Trade-off Solution (NSGA-II)")
    print_info(f"  G = {best_ind.round(2).tolist()}")
    print_info(f"  f1 (Avg Wait)  = {best_nsga_obj[0]:.4f} s/veh")
    print_info(f"  f2 (Fuel)      = {best_nsga_obj[1]:.6f}")
    print_info(f"  f3 (Emission)  = {best_nsga_obj[2]:.6f}")

    # ------------------------------------------------------------------
    # 6. Constraint validation
    # ------------------------------------------------------------------
    print_sub_header("Constraint Validation")
    assert all(g >= min_g - 1e-6 for g in best_ind), \
        f"VIOLATION: Gi < {min_g}  -> {best_ind}"
    assert best_ind.sum() <= max_c + 1e-6, \
        f"VIOLATION: sum(Gi)={best_ind.sum():.2f} > {max_c}"
    print_success(f"OK  All Gi >= {min_g}s  (min observed = {best_ind.min():.2f}s)")
    print_success(f"OK  Sum(Gi) = {best_ind.sum():.2f}s <= {max_c}s")

    for i, sol in enumerate(pareto_front):
        assert all(g >= min_g - 1e-6 for g in sol), f"Pareto[{i}] violates Gi>={min_g}"
        assert sol.sum() <= max_c + 1e-6,            f"Pareto[{i}] violates sum<={max_c}"
    print_success(f"OK  All {len(pareto_front)} Pareto solutions are feasible")

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
    is_static = args.static or (args.visual == "static") or not PLOTLY_AVAILABLE
    
    if is_static:
        if not PLOTLY_AVAILABLE and not args.static and args.visual != "static":
            print_warning("Plotly not found. Falling back to static PNG plots. Run `pip install plotly pandas` for interactive HTML.")
        
        print_info("\nGenerating static PNG plots (saved to results directory)...")
        plot_pareto_2d(pareto_obj, so_obj, fixed_obj, out_dir=results_dir)
        plot_pareto_3d(pareto_obj, so_obj, fixed_obj, out_dir=results_dir)
        plot_convergence(nsga_history, so_history,     out_dir=results_dir)
    else:
        print_info("\nGenerating Interactive HTML outputs (saved to results directory)...")
        import pandas as pd
        
        # Build DataFrame payload
        pareto_df = pd.DataFrame(pareto_front, columns=['G_North', 'G_South', 'G_East', 'G_West'])
        pareto_df['f1_wait'] = pareto_obj[:, 0]
        pareto_df['f2_fuel'] = pareto_obj[:, 1]
        pareto_df['f3_emission'] = pareto_obj[:, 2]
        pareto_df['index'] = pareto_df.index
        
        paths = []
        paths.append(plot_pareto_interactive(pareto_df, out_dir=results_dir))
        paths.append(plot_pareto_annotated(pareto_df, out_dir=results_dir))
        paths.append(plot_before_after(fixed_obj, so_obj, best_nsga_obj, out_dir=results_dir))
        paths.append(plot_green_heatmap(pareto_df, out_dir=results_dir))
        plot_convergence(nsga_history, so_history, out_dir=results_dir) # Keep PNG convergence as standard trace
        
        if args.open:
            import webbrowser
            for p in paths:
                if p: webbrowser.open(f"file://{os.path.abspath(p)}")

    # ------------------------------------------------------------------
    # 10. Exports & Explain
    # ------------------------------------------------------------------
    if args.export_csv:
        import csv
        csv_path = os.path.join(results_dir, "pareto_front.csv")
        with open(csv_path, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["G_North", "G_South", "G_East", "G_West", "f1_Wait", "f2_Fuel", "f3_Emission"])
            for g, obj in zip(pareto_front, pareto_obj):
                writer.writerow([*g.round(2), *obj])
        print_success(f"Exported Pareto front -> {csv_path}")

    if args.export_json:
        json_path = os.path.join(results_dir, "pareto_front.json")
        payload = [
            {"G": g.round(2).tolist(), "objectives": {"f1_wait": obj[0], "f2_fuel": obj[1], "f3_emission": obj[2]}}
            for g, obj in zip(pareto_front, pareto_obj)
        ]
        with open(json_path, "w") as f:
            json.dump(payload, f, indent=2)
        print_success(f"Exported Pareto front -> {json_path}")

    if args.explain:
        print_header("AUTOMATED EXPLANATION")
        f1b, f2b, f3b = fixed_obj
        f1n, f2n, f3n = best_nsga_obj
        imp_wait = 100*(f1b-f1n)/max(abs(f1b), 1e-9)
        
        print_info("Based on the NSGA-II optimization, the system identified a set of non-dominated solutions (Pareto front) illustrating the trade-offs between Waiting Time, Fuel Consumption, and Emissions.")
        print_info(f"The 'Balanced Trade-off' (knee-point) solution improves average waiting time by {imp_wait:+.1f}% compared to a standard fixed-time signal, while balancing environmental impacts.")
        print_info("To fully minimize Wait Time, shorter cycle lengths favoring heavy flow directions are necessary, but this typically increases stop-and-go events, thereby increasing Emissions.\n")

    # ------------------------------------------------------------------
    # 11. Interactive Decision Support Mode
    # ------------------------------------------------------------------
    if args.interactive:
        while True:
            print_header("DECISION SUPPORT MODE")
            print_info("  1 \u2192 Minimize Wait Time  (f1)")
            print_info("  2 \u2192 Minimize Fuel      (f2)")
            print_info("  3 \u2192 Minimize Emissions (f3)")
            print_info("  4 \u2192 Balanced Tradeoff  (Knee-point)")
            print_info("  5 \u2192 Inspect Specific Solution ID")
            print_info("  q \u2192 Continue to exit")
            
            choice = ask_user("\n  Select an option: ")
            if choice.lower() == 'q':
                break
                
            idx = -1
            if choice == '1':
                idx = int(np.argmin(pareto_obj[:, 0]))
            elif choice == '2':
                idx = int(np.argmin(pareto_obj[:, 1]))
            elif choice == '3':
                idx = int(np.argmin(pareto_obj[:, 2]))
            elif choice == '4':
                idx = best_idx
            elif choice == '5':
                print_sub_header("Pareto Solutions")
                for i, (g, obj) in enumerate(zip(pareto_front, pareto_obj)):
                    print_info(f"  ID {i:3d} | Wait: {obj[0]:.2f}s | Fuel: {obj[1]:.4f} | Emiss: {obj[2]:.4f}")
                
                insp_id = ask_user(f"\n  Enter Solution ID (0-{len(pareto_front)-1}): ")
                try:
                    idx = int(insp_id)
                    if not (0 <= idx < len(pareto_front)):
                        print_error("Invalid ID.")
                        idx = -1
                except ValueError:
                    print_error("Invalid input.")
                    idx = -1
            else:
                print_error("Invalid choice.")
                
            if idx != -1:
                g = pareto_front[idx].round(2)
                obj = pareto_obj[idx]
                print_success(f"\n  Selected Solution ID: {idx}")
                print_info(f"  Green Times (N,S,E,W): {g.tolist()}")
                print_info(f"  Wait Time            : {obj[0]:.4f} s/veh")
                print_info(f"  Fuel Consumption     : {obj[1]:.6f}")
                print_info(f"  Emissions            : {obj[2]:.6f}")

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    total_time = time.time() - total_start
    print_header("EXECUTION COMPLETE")
    print_info(f"  All outputs saved to: {results_dir}")
    print_info(f"  Total execution time: {total_time:.1f}s")


if __name__ == "__main__":
    main()
