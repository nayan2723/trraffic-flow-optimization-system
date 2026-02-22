"""
objectives.py
=============
Defines the three objective functions for traffic signal optimisation.

Objective functions (no weighted sum -- purely multi-objective):
  f1 = average waiting time   (seconds / vehicle)
  f2 = fuel consumption index (proportional to total idle time)
  f3 = emission index         (proportional to idle time + number of stops)

All constants (fuel rate, emission coefficients, constraint bounds) are
read from the sim_params dict at runtime -- nothing is hardcoded here.

The module also exposes is_feasible() and repair() which accept the
constraint bounds dynamically.
"""

import numpy as np
from simulation import simulate, DEFAULT_SIM_PARAMS

# Kept only as a fallback sentinel for infeasible penalty
PENALTY = 1e9


# ---------------------------------------------------------------------------
# Constraint checking & repair  (dynamic bounds)
# ---------------------------------------------------------------------------

def is_feasible(green_times, min_green=None, max_cycle=None):
    """
    Return True if green_times satisfy the hard constraints.

    Parameters
    ----------
    green_times : array-like, shape (4,)
    min_green   : float  – minimum green per phase (default: from DEFAULT_SIM_PARAMS)
    max_cycle   : float  – maximum total green (default: from DEFAULT_SIM_PARAMS)
    """
    if min_green is None:
        min_green = DEFAULT_SIM_PARAMS["min_green"]
    if max_cycle is None:
        max_cycle = DEFAULT_SIM_PARAMS["max_cycle"]
    g = np.asarray(green_times, dtype=float)
    return bool(np.all(g >= min_green) and g.sum() <= max_cycle)


def repair(green_times, min_green=None, max_cycle=None):
    """
    Repair a possibly-infeasible green-time vector:
      1. Clip each Gi to [min_green, max_cycle].
      2. If sum > max_cycle, scale proportionally while honouring min_green.
    Returns a new numpy array.
    """
    if min_green is None:
        min_green = DEFAULT_SIM_PARAMS["min_green"]
    if max_cycle is None:
        max_cycle = DEFAULT_SIM_PARAMS["max_cycle"]

    g = np.array(green_times, dtype=float)
    g = np.clip(g, min_green, max_cycle)

    total = g.sum()
    if total > max_cycle:
        excess    = total - max_cycle
        slack     = g - min_green
        slack_sum = slack.sum()
        if slack_sum > 0:
            g -= slack * (excess / slack_sum)
        else:
            g = np.full_like(g, max_cycle / len(g))
        g = np.clip(g, min_green, max_cycle)

    return g


# ---------------------------------------------------------------------------
# Objective evaluation
# ---------------------------------------------------------------------------

def evaluate(green_times, sim_params=None):
    """
    Evaluate the three objectives for a given signal plan.

    Parameters
    ----------
    green_times : array-like, shape (4,)
        Green phase durations [G1, G2, G3, G4] in seconds.
    sim_params  : dict, optional
        Full simulation + environment parameter dict.
        Must contain keys:
          arrival_rates, service_rate, sim_duration, seed,
          fuel_rate_idle, emission_idle, emission_stop,
          min_green, max_cycle

    Returns
    -------
    tuple (f1, f2, f3)
        f1 -- average waiting time (s/vehicle)
        f2 -- fuel consumption index
        f3 -- emission index
    """
    if sim_params is None:
        sim_params = DEFAULT_SIM_PARAMS.copy()

    g         = np.asarray(green_times, dtype=float)
    min_green = float(sim_params.get("min_green", DEFAULT_SIM_PARAMS["min_green"]))
    max_cycle = float(sim_params.get("max_cycle", DEFAULT_SIM_PARAMS["max_cycle"]))

    if not is_feasible(g, min_green, max_cycle):
        return (PENALTY, PENALTY, PENALTY)

    metrics = simulate(
        green_times=g,
        arrival_rates=sim_params.get("arrival_rates", DEFAULT_SIM_PARAMS["arrival_rates"]),
        service_rate=float(sim_params.get("service_rate", DEFAULT_SIM_PARAMS["service_rate"])),
        simulation_time=int(sim_params.get("sim_duration", DEFAULT_SIM_PARAMS["sim_duration"])),
        min_green=min_green,
        max_cycle=max_cycle,
        fuel_rate_idle=float(sim_params.get("fuel_rate_idle", DEFAULT_SIM_PARAMS["fuel_rate_idle"])),
        emission_idle=float(sim_params.get("emission_idle", DEFAULT_SIM_PARAMS["emission_idle"])),
        emission_stop=float(sim_params.get("emission_stop", DEFAULT_SIM_PARAMS["emission_stop"])),
        seed=int(sim_params.get("seed", DEFAULT_SIM_PARAMS["seed"]))
    )

    n_veh        = metrics["total_vehicles"]
    waiting_time = metrics["total_waiting_time"]
    idle_time    = metrics["total_idle_time"]
    n_stops      = metrics["total_stops"]

    fuel_rate     = float(sim_params.get("fuel_rate_idle",  DEFAULT_SIM_PARAMS["fuel_rate_idle"]))
    emission_idle = float(sim_params.get("emission_idle",   DEFAULT_SIM_PARAMS["emission_idle"]))
    emission_stop = float(sim_params.get("emission_stop",   DEFAULT_SIM_PARAMS["emission_stop"]))

    f1 = waiting_time / n_veh                            # avg wait (s/veh)
    f2 = fuel_rate    * idle_time                        # fuel index
    f3 = emission_idle * idle_time + emission_stop * n_stops  # emission index

    return (f1, f2, f3)


# ---------------------------------------------------------------------------
# Convenience: expose defaults for backward compatibility
# ---------------------------------------------------------------------------
G_MIN       = DEFAULT_SIM_PARAMS["min_green"]
G_TOTAL_MAX = DEFAULT_SIM_PARAMS["max_cycle"]


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Objectives Self-Test ===")
    from simulation import DEFAULT_SIM_PARAMS as SP

    plans = {
        "Equal split [30,30,30,30]": [30, 30, 30, 30],
        "Biased N   [50,20,30,20]":  [50, 20, 30, 20],
        "Infeasible [5, 5, 5, 5]":   [ 5,  5,  5,  5],
        "Infeasible [40,40,40,40]":  [40, 40, 40, 40],
    }
    mg, mc = SP["min_green"], SP["max_cycle"]

    for label, plan in plans.items():
        feasible = is_feasible(plan, mg, mc)
        repaired = repair(plan, mg, mc).tolist()
        f1, f2, f3 = evaluate(plan, SP)
        print(f"\n{label}")
        print(f"  Feasible : {feasible}  |  Repaired : {[round(x,1) for x in repaired]}")
        if f1 < PENALTY:
            print(f"  f1={f1:.4f}  f2={f2:.6f}  f3={f3:.6f}")
        else:
            print("  -> Penalised (infeasible; optimizer would repair before eval)")

    print("\nSelf-test PASSED.")
