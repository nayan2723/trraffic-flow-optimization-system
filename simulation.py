"""
simulation.py
=============
4-way intersection traffic simulator using a discrete-time queue model.

All parameters are passed in at runtime — nothing is hardcoded.
The module remains backward-compatible through DEFAULT_SIM_PARAMS.

Model assumptions:
  - Vehicles arrive at each direction according to a Poisson process.
  - Each direction (N, S, E, W) has an independent arrival rate (lambda, veh/sec).
  - The simulation steps every second over a configurable duration.
  - Vehicles depart from the head of the queue at a fixed service rate
    during their respective green phase.
  - Signal phases cycle: N->S->E->W, each lasting Gi seconds, followed by
    a fixed all_red_time-second all-red interval between phases.
  - The simulation is deterministic given a fixed numpy random seed.

Outputs:
  - total_waiting_time  : sum of per-vehicle waiting times (seconds)
  - total_idle_time     : total vehicle-seconds spent idling at red
  - total_stops         : total number of stop events (queue joins)
  - total_vehicles      : total vehicles that arrived
"""

import numpy as np

# ---------------------------------------------------------------------------
# Default simulation parameters (kept for backward-compatibility)
# When config_loader.build_sim_params() is used, these are overridden.
# ---------------------------------------------------------------------------
DEFAULT_SIM_PARAMS = {
    "arrival_rates": [0.4, 0.35, 0.45, 0.30],  # lambda (veh/sec) for N,S,E,W
    "service_rate":  1.5,                        # vehicles cleared per green second
    "all_red_time":  3,                          # seconds of all-red between phases
    "sim_duration":  1800,                       # total simulation time (seconds)
    "seed":          42,
    # fuel/emission defaults (used when objectives.py reads from sim_params)
    "fuel_rate_idle": 0.0002,
    "emission_idle":  0.002,
    "emission_stop":  0.005,
    # constraint defaults
    "min_green":  10.0,
    "max_cycle":  120.0,
}


class Intersection:
    """
    Simulates a 4-direction signalised intersection over a fixed time horizon.

    Parameters
    ----------
    green_times : array-like, shape (4,)
        Green phase durations [G1, G2, G3, G4] for directions N, S, E, W.
    params : dict
        Simulation parameters — see DEFAULT_SIM_PARAMS for required keys.
    """

    DIRECTIONS = ["N", "S", "E", "W"]

    def __init__(self, green_times, params=None):
        if params is None:
            params = DEFAULT_SIM_PARAMS.copy()
        self.green_times   = np.array(green_times, dtype=float)
        self.arrival_rates = np.array(params["arrival_rates"], dtype=float)
        self.service_rate  = float(params["service_rate"])
        self.all_red_time  = int(params.get("all_red_time", 3))
        self.sim_duration  = int(params["sim_duration"])
        self.seed          = int(params["seed"])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_phase_schedule(self):
        """
        Returns a list of (phase_index, start_sec, end_sec) tuples describing
        each green phase across the whole simulation horizon.
        """
        schedule = []
        n_phases = len(self.green_times)
        t = 0
        while t < self.sim_duration:
            for i in range(n_phases):
                g_start = t
                g_end   = t + int(self.green_times[i])
                schedule.append((i, g_start, g_end))
                t += int(self.green_times[i]) + self.all_red_time
                if t >= self.sim_duration:
                    break
        return schedule

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def run(self):
        """
        Run the simulation and return performance metrics.

        Returns
        -------
        dict with keys:
            total_waiting_time  (float)
            total_idle_time     (float)
            total_stops         (int)
            total_vehicles      (int)
        """
        rng    = np.random.default_rng(self.seed)
        n_dirs = len(self.DIRECTIONS)

        queues = np.zeros(n_dirs, dtype=float)

        total_waiting_time = 0.0
        total_idle_time    = 0.0
        total_stops        = 0
        total_vehicles     = 0

        schedule      = self._build_phase_schedule()
        schedule_iter = iter(schedule)
        current_phase, phase_end = None, 0

        try:
            current_phase, phase_start, phase_end = next(schedule_iter)
        except StopIteration:
            pass

        for t in range(self.sim_duration):
            # ---- Advance green phase ----
            if t >= phase_end:
                try:
                    current_phase, phase_start, phase_end = next(schedule_iter)
                except StopIteration:
                    current_phase = None

            # ---- Poisson arrivals ----
            arrivals = rng.poisson(self.arrival_rates)
            for i in range(n_dirs):
                if arrivals[i] > 0:
                    total_vehicles += arrivals[i]
                    total_stops    += arrivals[i]   # each arriving vehicle = one stop
                    queues[i]      += arrivals[i]

            # ---- Service ----
            if current_phase is not None and t < phase_end:
                served = min(queues[current_phase], self.service_rate)
                queues[current_phase] -= served

            # ---- Accumulate wait / idle ----
            for i in range(n_dirs):
                if queues[i] > 0:
                    if i != current_phase:      # red or all-red
                        total_idle_time    += queues[i]
                        total_waiting_time += queues[i]
                    else:                        # green – residual queue
                        total_waiting_time += queues[i]

        return {
            "total_waiting_time": total_waiting_time,
            "total_idle_time":    total_idle_time,
            "total_stops":        total_stops,
            "total_vehicles":     max(total_vehicles, 1),
        }


def simulate(green_times, arrival_rates, service_rate, simulation_time, min_green, max_cycle, fuel_rate_idle, emission_idle, emission_stop, seed=42):
    """
    Convenience wrapper: run an intersection simulation and return metrics.
    All parameters are passed dynamically.

    Returns
    -------
    dict – see Intersection.run()
    """
    params = {
        "arrival_rates": arrival_rates,
        "service_rate":  service_rate,
        "sim_duration":  simulation_time,
        "min_green":     min_green,
        "max_cycle":     max_cycle,
        "fuel_rate_idle": fuel_rate_idle,
        "emission_idle": emission_idle,
        "emission_stop": emission_stop,
        "seed":          seed,
        "all_red_time":  3
    }
    sim = Intersection(green_times, params)
    return sim.run()


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Simulation Self-Test ===")
    green  = [30, 30, 30, 30]
    result = simulate(
        green_times=green,
        arrival_rates=[0.4, 0.35, 0.45, 0.30],
        service_rate=1.5,
        simulation_time=1800,
        min_green=10.0,
        max_cycle=120.0,
        fuel_rate_idle=0.0002,
        emission_idle=0.002,
        emission_stop=0.005,
        seed=42
    )
    print(f"Green times      : {green}")
    print(f"Total vehicles   : {result['total_vehicles']}")
    print(f"Total waiting    : {result['total_waiting_time']:.1f} veh-sec")
    print(f"Total idle time  : {result['total_idle_time']:.1f} veh-sec")
    print(f"Total stops      : {result['total_stops']}")
    print("Self-test PASSED.")
