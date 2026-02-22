"""
config_loader.py
================
Loads, validates, and serves configuration parameters for the
Multi-Objective Traffic Optimization system.

Supports three modes (decided by main.py / argparse):
  1. Default mode   – loads config.json from the project directory
  2. Custom mode    – loads a user-specified JSON file (--config path)
  3. Interactive    – prompts the user on the terminal (--interactive)

Public API
----------
  load_config(filepath)            -> dict
  validate_config(cfg)             -> None   (raises ValueError if invalid)
  interactive_config(defaults)     -> dict
  build_sim_params(cfg, seed)      -> dict   (ready for simulation.py)
"""

import json
import os
import sys
import random
from ui import print_header, print_error, print_info, ask_user, print_sub_header

# ---------------------------------------------------------------------------
# Schema with types, bounds, and human-readable labels
# ---------------------------------------------------------------------------
_SCHEMA = {
    "traffic.arrival_rates.north": {"type": float, "lo": 0.0,     "hi": 100.0,  "label": "Arrival rate – North (veh/min)"},
    "traffic.arrival_rates.south": {"type": float, "lo": 0.0,     "hi": 100.0,  "label": "Arrival rate – South (veh/min)"},
    "traffic.arrival_rates.east":  {"type": float, "lo": 0.0,     "hi": 100.0,  "label": "Arrival rate – East  (veh/min)"},
    "traffic.arrival_rates.west":  {"type": float, "lo": 0.0,     "hi": 100.0,  "label": "Arrival rate – West  (veh/min)"},
    "traffic.service_rate":        {"type": float, "lo": 0.1,     "hi": 5.0,    "label": "Service rate (veh/sec during green)"},
    "traffic.simulation_time":     {"type": int,   "lo": 60,      "hi": 3600,   "label": "Simulation duration (seconds)"},
    "signal_constraints.min_green":{"type": int,   "lo": 5,       "hi": 60,     "label": "Min green time per phase (seconds)"},
    "signal_constraints.max_cycle":{"type": int,   "lo": 40,      "hi": 300,    "label": "Max total cycle time (seconds)"},
    "environment.fuel_rate_idle":  {"type": float, "lo": 1e-6,    "hi": 1.0,    "label": "Fuel rate per idle veh-sec"},
    "environment.emission_idle":   {"type": float, "lo": 1e-6,    "hi": 1.0,    "label": "Emission coeff – idle (per veh-sec)"},
    "environment.emission_stop":   {"type": float, "lo": 1e-6,    "hi": 10.0,   "label": "Emission coeff – stop event"},
    "optimization.population_size":{"type": int,   "lo": 20,      "hi": 500,    "label": "Population size"},
    "optimization.generations":    {"type": int,   "lo": 10,      "hi": 500,    "label": "Number of generations"},
    "optimization.mutation_prob":  {"type": float, "lo": 1e-9,    "hi": 1.0,    "label": "Mutation probability"},
    "optimization.crossover_prob": {"type": float, "lo": 1e-9,    "hi": 1.0,    "label": "Crossover probability"},
    "optimization.seed":           {"type": int,   "lo": 0,       "hi": 2**31,  "label": "Random seed"},
}

# Default config (mirrors config.json)
_DEFAULTS = {
    "traffic": {
        "arrival_rates": {"north": 8, "south": 10, "east": 6, "west": 7},
        "service_rate":  1.2,
        "simulation_time": 600,
    },
    "signal_constraints": {
        "min_green": 10,
        "max_cycle": 120,
    },
    "environment": {
        "fuel_rate_idle": 0.0002,
        "emission_idle":  0.002,
        "emission_stop":  0.005,
    },
    "optimization": {
        "population_size": 80,
        "generations":     60,
        "mutation_prob":   0.1,
        "crossover_prob":  0.8,
        "seed":            42,
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _deep_get(d, dotted_key):
    """Traverse nested dict using a dot-separated key string."""
    keys = dotted_key.split(".")
    for k in keys:
        d = d[k]
    return d


def _deep_merge(base, override):
    """Recursively merge `override` into `base` (in-place on `base`)."""
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_config(filepath=None):
    """
    Load configuration from a JSON file.

    Parameters
    ----------
    filepath : str or None
        Path to config JSON. If None, tries 'config.json' in the same
        directory as this script.

    Returns
    -------
    dict – merged configuration (defaults overridden by file values)
    """
    import copy
    cfg = copy.deepcopy(_DEFAULTS)

    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), "config.json")

    if not os.path.isfile(filepath):
        print(f"[config_loader] WARNING: '{filepath}' not found. Using built-in defaults.")
        return cfg

    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            file_cfg = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{filepath}': {exc}") from exc

    _deep_merge(cfg, file_cfg)
    return cfg


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def validate_config(cfg):
    """
    Validate all required fields in the config dictionary.

    Raises
    ------
    ValueError – with a descriptive message on the first invalid field.
    """
    errors = []
    for dotted_key, spec in _SCHEMA.items():
        try:
            raw = _deep_get(cfg, dotted_key)
        except (KeyError, TypeError):
            errors.append(f"  Missing field: '{dotted_key}'")
            continue

        try:
            val = spec["type"](raw)
        except (ValueError, TypeError):
            errors.append(f"  '{dotted_key}': expected {spec['type'].__name__}, got {type(raw).__name__}")
            continue

        lo, hi = spec["lo"], spec["hi"]
        if not (lo <= val <= hi):
            errors.append(
                f"  '{dotted_key}': value {val} out of range [{lo}, {hi}]"
            )

    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))

    # Cross-field check
    min_g = float(cfg["signal_constraints"]["min_green"])
    max_c = float(cfg["signal_constraints"]["max_cycle"])
    if min_g * 4 > max_c:
        raise ValueError(
            f"Infeasible constraints: min_green={min_g} * 4 = {min_g*4} > max_cycle={max_c}. "
            "No feasible signal plan exists."
        )


# ---------------------------------------------------------------------------
# Interactive prompt
# ---------------------------------------------------------------------------

def get_valid_input(prompt, type_cast, min_val=None, max_val=None, custom_validator=None, custom_error="Custom constraint violated.", default=None):
    """
    Prompt the user for a single value with strict validation.
    Empty inputs are rejected and the user is asked to enter a value.
    """
    default_str = f" [{default}]" if default is not None else ""
    full_prompt = f"  {prompt}{default_str}: "
    
    while True:
        raw = ask_user(full_prompt)

        if raw == "":
            print_error("Please enter a value.")
            continue

        try:
            value = type_cast(raw)
        except ValueError:
            print_error("Invalid type. Please enter a valid number.")
            continue

        if min_val is not None and value < min_val:
            print_error(f"Value must be >= {min_val}")
            continue

        if max_val is not None and value > max_val:
            print_error(f"Value must be <= {max_val}")
            continue

        if custom_validator is not None:
            if not custom_validator(value):
                print_error(f"{custom_error}")
                continue

        return value


def interactive_config(defaults=None):
    """
    Collect all parameters interactively from the terminal.
    Validates per field and won't proceed until a valid number is entered.
    """
    import copy
    while True:
        cfg = copy.deepcopy(defaults or _DEFAULTS)

        print_info("\n" + "=" * 58)
        print_info("  Interactive Configuration \u2014 type 'q' to quit at any time")
        print_info("=" * 58)

        print_sub_header("\nSelect Traffic Scenario:")
        print_info("  1 \u2192 Low Density (3-5 veh/min)")
        print_info("  2 \u2192 Medium Density (8-12 veh/min)")
        print_info("  3 \u2192 High Density (18-25 veh/min)")
        print_info("  4 \u2192 Custom Input")
        
        while True:
            choice = ask_user("\n  Enter choice (1-4): ")
            if choice in ['1', '2', '3', '4']:
                break
            print_error("Invalid choice. Enter 1, 2, 3, or 4.")
        
        scenario_name = "custom"
        if choice == '1':
            for k in ["north", "south", "east", "west"]:
                cfg["traffic"]["arrival_rates"][k] = round(random.uniform(3.0, 5.0), 1)
            scenario_name = "low"
        elif choice == '2':
            for k in ["north", "south", "east", "west"]:
                cfg["traffic"]["arrival_rates"][k] = round(random.uniform(8.0, 12.0), 1)
            scenario_name = "medium"
        elif choice == '3':
            for k in ["north", "south", "east", "west"]:
                cfg["traffic"]["arrival_rates"][k] = round(random.uniform(18.0, 25.0), 1)
            scenario_name = "high"

        cfg["scenario_name"] = scenario_name

        print_header("TRAFFIC PARAMETERS")
        if choice == '4':
            cfg["traffic"]["arrival_rates"]["north"] = get_valid_input("Arrival rate \u2013 North (veh/min)", float, min_val=0.0, max_val=100.0, default=cfg["traffic"]["arrival_rates"]["north"])
            cfg["traffic"]["arrival_rates"]["south"] = get_valid_input("Arrival rate \u2013 South (veh/min)", float, min_val=0.0, max_val=100.0, default=cfg["traffic"]["arrival_rates"]["south"])
            cfg["traffic"]["arrival_rates"]["east"]  = get_valid_input("Arrival rate \u2013 East (veh/min)",  float, min_val=0.0, max_val=100.0, default=cfg["traffic"]["arrival_rates"]["east"])
            cfg["traffic"]["arrival_rates"]["west"]  = get_valid_input("Arrival rate \u2013 West (veh/min)",  float, min_val=0.0, max_val=100.0, default=cfg["traffic"]["arrival_rates"]["west"])
        else:
            print_info(f"  Using '{scenario_name}' density preset for arrival rates:")
            for k, v in cfg["traffic"]["arrival_rates"].items():
                print_info(f"    {k.capitalize():<5}: {v} veh/min")

        cfg["traffic"]["service_rate"] = get_valid_input("Service rate (veh/sec during green)", float, min_val=0.1, max_val=5.0, default=cfg["traffic"]["service_rate"])
        cfg["traffic"]["simulation_time"] = get_valid_input("Simulation duration (seconds)", int, min_val=60, max_val=3600, default=cfg["traffic"]["simulation_time"])

        print_header("SIGNAL CONSTRAINTS")
        mg = get_valid_input("Min green time per phase (seconds)", int, min_val=5, max_val=60, default=int(cfg["signal_constraints"]["min_green"]))
        cfg["signal_constraints"]["min_green"] = mg
        cfg["signal_constraints"]["max_cycle"] = get_valid_input("Max total cycle time (seconds)", int, min_val=40, max_val=300, custom_validator=lambda x: x >= 4 * mg, custom_error="max_cycle must be at least 4 \u00d7 min_green", default=int(cfg["signal_constraints"]["max_cycle"]))

        print_header("ENVIRONMENT PARAMETERS")
        cfg["environment"]["fuel_rate_idle"] = get_valid_input("Fuel rate per idle veh-sec", float, min_val=1e-6, max_val=1.0, default=cfg["environment"]["fuel_rate_idle"])
        cfg["environment"]["emission_idle"]  = get_valid_input("Emission coeff \u2013 idle (per veh-sec)", float, min_val=1e-6, max_val=1.0, default=cfg["environment"]["emission_idle"])
        cfg["environment"]["emission_stop"]  = get_valid_input("Emission coeff \u2013 stop event", float, min_val=1e-6, max_val=10.0, default=cfg["environment"]["emission_stop"])

        print_header("OPTIMIZATION PARAMETERS")
        cfg["optimization"]["population_size"] = get_valid_input("Population size", int, min_val=20, max_val=500, default=cfg["optimization"]["population_size"])
        cfg["optimization"]["generations"]     = get_valid_input("Number of generations", int, min_val=10, max_val=500, default=cfg["optimization"]["generations"])
        cfg["optimization"]["mutation_prob"]   = get_valid_input("Mutation probability", float, max_val=1.0, custom_validator=lambda x: x > 0.0, custom_error="Value must be > 0.0", default=cfg["optimization"]["mutation_prob"])
        cfg["optimization"]["crossover_prob"]  = get_valid_input("Crossover probability", float, max_val=1.0, custom_validator=lambda x: x > 0.0, custom_error="Value must be > 0.0", default=cfg["optimization"]["crossover_prob"])
        cfg["optimization"]["seed"]            = get_valid_input("Random seed", int, min_val=0, default=cfg["optimization"]["seed"])

        print_header("RUN SUMMARY")
        ar = cfg['traffic']['arrival_rates']
        print_info(f"  Arrival Rates   : N={ar['north']} S={ar['south']} E={ar['east']} W={ar['west']} (veh/min)")
        print_info(f"  Service Rate    : {cfg['traffic']['service_rate']} veh/sec")
        print_info(f"  Simulation Time : {cfg['traffic']['simulation_time']} s")
        print_info(f"  Min Green       : {cfg['signal_constraints']['min_green']} s")
        print_info(f"  Max Cycle       : {cfg['signal_constraints']['max_cycle']} s")
        print_info(f"  Population      : {cfg['optimization']['population_size']}")
        print_info(f"  Generations     : {cfg['optimization']['generations']}")
        print_info("-" * 40)

        while True:
            confirm = ask_user("\n  Proceed with optimization? (y/n): ").lower()
            if confirm in ['y', 'yes', 'n', 'no']:
                break
        
        if confirm in ['y', 'yes']:
            print_info("\nStarting optimization...")
            return cfg
        else:
            print_error("\nRestarting configuration...")


# ---------------------------------------------------------------------------
# Build sim_params dict (used by simulation.py / objectives.py)
# ---------------------------------------------------------------------------

def build_sim_params(cfg, seed=None):
    """
    Convert a validated config dict into the `sim_params` dictionary
    expected by simulation.run_simulation() and objectives.evaluate().

    Parameters
    ----------
    cfg  : dict   – validated configuration
    seed : int    – overrides cfg seed if provided

    Returns
    -------
    dict with keys: arrival_rates, service_rate, sim_duration,
                    all_red_time, seed, fuel_rate_idle,
                    emission_idle, emission_stop,
                    min_green, max_cycle
    """
    ar = cfg["traffic"]["arrival_rates"]
    # Convert from veh/min to veh/sec
    arrival_rates_per_sec = [
        ar["north"] / 60.0,
        ar["south"] / 60.0,
        ar["east"]  / 60.0,
        ar["west"]  / 60.0,
    ]

    return {
        "arrival_rates":   arrival_rates_per_sec,
        "service_rate":    float(cfg["traffic"]["service_rate"]),
        "sim_duration":    int(cfg["traffic"]["simulation_time"]),
        "all_red_time":    3,            # fixed inter-phase all-red (seconds)
        "seed":            int(seed if seed is not None else cfg["optimization"]["seed"]),
        # Fuel & emission (passed through to objectives.py)
        "fuel_rate_idle":  float(cfg["environment"]["fuel_rate_idle"]),
        "emission_idle":   float(cfg["environment"]["emission_idle"]),
        "emission_stop":   float(cfg["environment"]["emission_stop"]),
        # Constraint bounds (passed through to objectives.py / nsga2)
        "min_green":       float(cfg["signal_constraints"]["min_green"]),
        "max_cycle":       float(cfg["signal_constraints"]["max_cycle"]),
    }


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== config_loader Self-Test ===")
    cfg = load_config()
    validate_config(cfg)
    sp  = build_sim_params(cfg)
    print(f"  arrival_rates (veh/sec) : {sp['arrival_rates']}")
    print(f"  service_rate            : {sp['service_rate']}")
    print(f"  sim_duration            : {sp['sim_duration']} s")
    print(f"  min_green={sp['min_green']}  max_cycle={sp['max_cycle']}")
    print(f"  fuel_rate={sp['fuel_rate_idle']}  emit_idle={sp['emission_idle']}  emit_stop={sp['emission_stop']}")
    print("Self-test PASSED.")
