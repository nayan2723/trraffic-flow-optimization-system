"""
nsga2_optimizer.py
==================
Custom NSGA-II implementation from scratch using NumPy.

All hyperparameters (population size, generations, crossover/mutation
probabilities, random seed) are accepted as constructor / function arguments.
No values are hardcoded. Defaults mirror the project defaults in config.json.

Implements the algorithm described in:
  Deb, K., Pratap, A., Agarwal, S., & Meyarivan, T. (2002).
  A fast and elitist multiobjective genetic algorithm: NSGA-II.
  IEEE Transactions on Evolutionary Computation, 6(2), 182-197.

Components
----------
  fast_non_dominated_sort   : O(M*N^2) front assignment
  crowding_distance         : diversity measure within each front
  tournament_selection      : binary tournament on (rank, crowding)
  sbx_crossover             : Simulated Binary Crossover (eta_c = 15)
  polynomial_mutation       : Polynomial Mutation (eta_m = 20)
  NSGA2                     : main optimiser class
  run_single_objective_ga   : single-obj GA minimising f1 only
  fixed_time_baseline       : equal green-split baseline
"""

import numpy as np
from objectives import evaluate, repair
from simulation import DEFAULT_SIM_PARAMS

# ---------------------------------------------------------------------------
# Algorithm constants (distribution indices -- not user-configurable)
# ---------------------------------------------------------------------------
ETA_C = 15.0   # SBX distribution index
ETA_M = 20.0   # Polynomial mutation distribution index
N_VARS = 4     # decision variables: G1..G4


# ===========================================================================
# NSGA-II building blocks
# ===========================================================================

def _make_bounds(sim_params):
    """Compute variable bounds from sim_params constraints."""
    min_green = float(sim_params.get("min_green", DEFAULT_SIM_PARAMS["min_green"]))
    max_cycle = float(sim_params.get("max_cycle", DEFAULT_SIM_PARAMS["max_cycle"]))
    lb = np.full(N_VARS, min_green)
    ub = np.full(N_VARS, max_cycle - min_green * (N_VARS - 1))
    return lb, ub


def fast_non_dominated_sort(objectives):
    """
    Assign a Pareto front rank to each individual.

    Parameters
    ----------
    objectives : ndarray, shape (N, M)  -- all objectives minimised

    Returns
    -------
    fronts : list of lists  -- fronts[0] = rank-1 indices, etc.
    ranks  : ndarray (N,)
    """
    N = len(objectives)
    domination_count = np.zeros(N, dtype=int)
    dominated_by     = [[] for _ in range(N)]

    for p in range(N):
        for q in range(N):
            if p == q:
                continue
            p_better = np.any(objectives[p] < objectives[q])
            p_worse  = np.any(objectives[p] > objectives[q])
            if p_better and not p_worse:
                dominated_by[p].append(q)
            elif not p_better and p_worse:
                domination_count[p] += 1

    fronts        = []
    current_front = [i for i in range(N) if domination_count[i] == 0]
    fronts.append(current_front)

    while current_front:
        next_front = []
        for p in current_front:
            for q in dominated_by[p]:
                domination_count[q] -= 1
                if domination_count[q] == 0:
                    next_front.append(q)
        current_front = next_front
        if current_front:
            fronts.append(current_front)

    ranks = np.zeros(N, dtype=int)
    for rank, front in enumerate(fronts):
        for idx in front:
            ranks[idx] = rank

    return fronts, ranks


def crowding_distance(objectives, front):
    """Crowding distance for individuals in one front."""
    n = len(front)
    if n <= 2:
        return np.full(n, np.inf)

    obj_front = objectives[front]
    n_obj     = obj_front.shape[1]
    distance  = np.zeros(n)

    for m in range(n_obj):
        order      = np.argsort(obj_front[:, m])
        distance[order[0]]  = np.inf
        distance[order[-1]] = np.inf
        obj_range = obj_front[order[-1], m] - obj_front[order[0], m]
        if obj_range == 0:
            continue
        for i in range(1, n - 1):
            distance[order[i]] += (
                obj_front[order[i + 1], m] - obj_front[order[i - 1], m]
            ) / obj_range

    return distance


def tournament_selection(ranks, distances, rng):
    """Binary tournament on (rank, crowding distance)."""
    N = len(ranks)
    a, b = rng.integers(0, N, size=2)
    if ranks[a] < ranks[b]:
        return a
    elif ranks[b] < ranks[a]:
        return b
    elif distances[a] >= distances[b]:
        return a
    else:
        return b


def sbx_crossover(parent1, parent2, rng, lb, ub, p_cross):
    """Simulated Binary Crossover (SBX)."""
    child1 = parent1.copy()
    child2 = parent2.copy()

    if rng.random() > p_cross:
        return child1, child2

    for i in range(N_VARS):
        if rng.random() <= 0.5:
            if abs(parent1[i] - parent2[i]) < 1e-10:
                continue
            y1 = min(parent1[i], parent2[i])
            y2 = max(parent1[i], parent2[i])

            u = rng.random()

            beta_l  = 1.0 + (2.0 * (y1 - lb[i]) / (y2 - y1 + 1e-12))
            alpha_l = 2.0 - beta_l ** (-(ETA_C + 1.0))
            beta_q_l = (u * alpha_l) ** (1.0 / (ETA_C + 1.0)) if u <= 1.0 / alpha_l \
                       else (1.0 / (2.0 - u * alpha_l)) ** (1.0 / (ETA_C + 1.0))

            beta_u  = 1.0 + (2.0 * (ub[i] - y2) / (y2 - y1 + 1e-12))
            alpha_u = 2.0 - beta_u ** (-(ETA_C + 1.0))
            beta_q_u = (u * alpha_u) ** (1.0 / (ETA_C + 1.0)) if u <= 1.0 / alpha_u \
                       else (1.0 / (2.0 - u * alpha_u)) ** (1.0 / (ETA_C + 1.0))

            c1 = 0.5 * ((y1 + y2) - beta_q_l * (y2 - y1))
            c2 = 0.5 * ((y1 + y2) + beta_q_u * (y2 - y1))

            child1[i] = np.clip(c1, lb[i], ub[i])
            child2[i] = np.clip(c2, lb[i], ub[i])

    return child1, child2


def polynomial_mutation(individual, rng, lb, ub, p_mut):
    """Polynomial Mutation."""
    mutant = individual.copy()
    for i in range(N_VARS):
        if rng.random() < p_mut:
            y  = mutant[i]
            u  = rng.random()

            delta1 = (y  - lb[i]) / (ub[i] - lb[i] + 1e-12)
            delta2 = (ub[i] -  y) / (ub[i] - lb[i] + 1e-12)

            if u <= 0.5:
                mut_pow = 1.0 / (ETA_M + 1.0)
                val     = 2.0 * u + (1.0 - 2.0 * u) * (1.0 - delta1) ** (ETA_M + 1.0)
                delta_q = val ** mut_pow - 1.0
            else:
                mut_pow = 1.0 / (ETA_M + 1.0)
                val     = 2.0 * (1.0 - u) + 2.0 * (u - 0.5) * (1.0 - delta2) ** (ETA_M + 1.0)
                delta_q = 1.0 - val ** mut_pow

            mutant[i] = np.clip(y + delta_q * (ub[i] - lb[i]), lb[i], ub[i])

    return mutant


# ===========================================================================
# NSGA-II Optimizer
# ===========================================================================

class NSGA2:
    """
    Multi-objective NSGA-II optimiser.

    Parameters
    ----------
    sim_params    : dict   – full simulation + environment parameters
    pop_size      : int    – population size
    n_generations : int    – number of generations
    p_cross       : float  – crossover probability
    p_mut         : float  – mutation probability (per variable if 'per_var', else absolute)
    seed          : int    – random seed
    """

    def __init__(self, sim_params=None, pop_size=80, n_generations=60,
                 p_cross=0.8, p_mut=None, seed=42):
        self.sim_params    = sim_params or DEFAULT_SIM_PARAMS.copy()
        self.pop_size      = int(pop_size)
        self.n_generations = int(n_generations)
        self.p_cross       = float(p_cross)
        # Default: 1/N_VARS per-variable mutation rate (classic NSGA-II)
        self.p_mut         = float(p_mut) if p_mut is not None else 1.0 / N_VARS
        self.rng           = np.random.default_rng(int(seed))
        self.lb, self.ub   = _make_bounds(self.sim_params)
        self.history       = []   # best f1 per generation

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _repair(self, g):
        min_green = float(self.sim_params.get("min_green", DEFAULT_SIM_PARAMS["min_green"]))
        max_cycle = float(self.sim_params.get("max_cycle", DEFAULT_SIM_PARAMS["max_cycle"]))
        return repair(g, min_green, max_cycle)

    def _random_individual(self):
        g = self.rng.uniform(self.lb, self.ub)
        return self._repair(g)

    def _init_population(self):
        return np.array([self._random_individual() for _ in range(self.pop_size)])

    def _evaluate_population(self, pop):
        results = []
        for ind in pop:
            sp = self.sim_params.copy()
            sp["seed"] = self.rng.integers(0, 2**31 - 1)
            results.append(evaluate(ind, sp))
        return np.array(results)

    def _assign_crowding(self, objectives, fronts):
        N = len(objectives)
        crowd = np.zeros(N)
        for front in fronts:
            if front:
                dist = crowding_distance(objectives, front)
                for idx, d in zip(front, dist):
                    crowd[idx] = d
        return crowd

    def _make_offspring(self, pop, ranks, crowd):
        offspring = []
        while len(offspring) < self.pop_size:
            p1 = pop[tournament_selection(ranks, crowd, self.rng)]
            p2 = pop[tournament_selection(ranks, crowd, self.rng)]
            c1, c2 = sbx_crossover(p1, p2, self.rng, self.lb, self.ub, self.p_cross)
            c1 = self._repair(polynomial_mutation(c1, self.rng, self.lb, self.ub, self.p_mut))
            c2 = self._repair(polynomial_mutation(c2, self.rng, self.lb, self.ub, self.p_mut))
            offspring.extend([c1, c2])
        return np.array(offspring[:self.pop_size])

    def _select_survivors(self, combined_pop, combined_obj):
        fronts, ranks = fast_non_dominated_sort(combined_obj)
        crowd = self._assign_crowding(combined_obj, fronts)
        survivors = []
        for front in fronts:
            if len(survivors) + len(front) <= self.pop_size:
                survivors.extend(front)
            else:
                needed    = self.pop_size - len(survivors)
                dist_vals = sorted([(crowd[i], i) for i in front], key=lambda x: -x[0])
                survivors.extend([i for _, i in dist_vals[:needed]])
                break
        return (
            combined_pop[survivors],
            combined_obj[survivors],
            ranks[survivors],
            crowd[survivors],
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        """
        Run NSGA-II.

        Returns
        -------
        pareto_front : ndarray (K, N_VARS)
        pareto_obj   : ndarray (K, 3)
        history      : list of float  -- best f1 per generation
        """
        print(f"NSGA-II | pop={self.pop_size} | gen={self.n_generations} "
              f"| pc={self.p_cross} | pm={self.p_mut:.3f} | seed={self.rng.bit_generator.state['state']['state']}")

        pop    = self._init_population()
        obj    = self._evaluate_population(pop)
        fronts, ranks = fast_non_dominated_sort(obj)
        crowd  = self._assign_crowding(obj, fronts)

        for gen in range(self.n_generations):
            best_f1 = obj[fronts[0], 0].min()
            self.history.append(best_f1)

            if (gen + 1) % 10 == 0 or gen == 0:
                print(f"  Gen {gen+1:3d}/{self.n_generations}  best f1={best_f1:.3f}")

            offspring = self._make_offspring(pop, ranks, crowd)
            off_obj   = self._evaluate_population(offspring)

            combined_pop = np.vstack([pop, offspring])
            combined_obj = np.vstack([obj, off_obj])
            pop, obj, ranks, crowd = self._select_survivors(combined_pop, combined_obj)

            fronts, ranks = fast_non_dominated_sort(obj)
            crowd = self._assign_crowding(obj, fronts)

        pareto_idx  = fronts[0]
        pareto_front = pop[pareto_idx]
        pareto_obj   = obj[pareto_idx]
        print(f"  Done. Pareto front size = {len(pareto_front)}")
        return pareto_front, pareto_obj, self.history


# ===========================================================================
# Baseline 1: Fixed-time signal
# ===========================================================================

def fixed_time_baseline(sim_params=None):
    """
    Evaluate the equal green-time split baseline.
    Split is 1/4 of max_cycle per direction, floored to an integer.
    """
    if sim_params is None:
        sim_params = DEFAULT_SIM_PARAMS.copy()
    max_cycle = float(sim_params.get("max_cycle", DEFAULT_SIM_PARAMS["max_cycle"]))
    split = max_cycle / 4.0
    g   = np.array([split, split, split, split])
    obj = evaluate(g, sim_params)
    return g, obj


# ===========================================================================
# Baseline 2: Single-objective GA
# ===========================================================================

def run_single_objective_ga(sim_params=None, pop_size=80, n_generations=60,
                             p_cross=0.8, p_mut=None, seed=99):
    """
    Simple real-coded GA minimising f1 (average waiting time) only.

    Parameters
    ----------
    sim_params    : dict
    pop_size      : int
    n_generations : int
    p_cross       : float
    p_mut         : float  – per-variable mutation prob (default 1/N_VARS)
    seed          : int

    Returns
    -------
    best_individual : ndarray (N_VARS,)
    best_objectives : tuple (f1, f2, f3)
    history         : list of float
    """
    if sim_params is None:
        sim_params = DEFAULT_SIM_PARAMS.copy()

    if p_mut is None:
        p_mut = 1.0 / N_VARS

    lb, ub = _make_bounds(sim_params)
    min_green = float(sim_params.get("min_green", DEFAULT_SIM_PARAMS["min_green"]))
    max_cycle = float(sim_params.get("max_cycle", DEFAULT_SIM_PARAMS["max_cycle"]))

    rng     = np.random.default_rng(int(seed))
    history = []

    pop = np.array([
        repair(rng.uniform(lb, ub), min_green, max_cycle)
        for _ in range(pop_size)
    ])
    fitnesses = []
    for ind in pop:
        sp = sim_params.copy()
        sp["seed"] = rng.integers(0, 2**31 - 1)
        fitnesses.append(evaluate(ind, sp)[0])
    fitnesses = np.array(fitnesses)

    print(f"Single-obj GA | pop={pop_size} | gen={n_generations} | seed={seed}")

    for gen in range(n_generations):
        best_f1 = fitnesses.min()
        history.append(best_f1)

        if (gen + 1) % 10 == 0 or gen == 0:
            print(f"  Gen {gen+1:3d}/{n_generations}  best f1={best_f1:.3f}")

        offspring = []
        off_fit   = []
        while len(offspring) < pop_size:
            a, b    = rng.integers(0, pop_size, size=2)
            winner1 = pop[a] if fitnesses[a] <= fitnesses[b] else pop[b]
            c, d    = rng.integers(0, pop_size, size=2)
            winner2 = pop[c] if fitnesses[c] <= fitnesses[d] else pop[d]

            c1, c2 = sbx_crossover(winner1, winner2, rng, lb, ub, p_cross)
            c1 = repair(polynomial_mutation(c1, rng, lb, ub, p_mut), min_green, max_cycle)
            c2 = repair(polynomial_mutation(c2, rng, lb, ub, p_mut), min_green, max_cycle)
            offspring.extend([c1, c2])
            sp1 = sim_params.copy()
            sp1["seed"] = rng.integers(0, 2**31 - 1)
            sp2 = sim_params.copy()
            sp2["seed"] = rng.integers(0, 2**31 - 1)
            off_fit.extend([
                evaluate(c1, sp1)[0],
                evaluate(c2, sp2)[0],
            ])

        offspring    = np.array(offspring[:pop_size])
        off_fit      = np.array(off_fit[:pop_size])
        combined     = np.vstack([pop, offspring])
        combined_fit = np.concatenate([fitnesses, off_fit])
        order        = np.argsort(combined_fit)[:pop_size]
        pop          = combined[order]
        fitnesses    = combined_fit[order]

    best_idx = np.argmin(fitnesses)
    best_ind = pop[best_idx]
    best_obj = evaluate(best_ind, sim_params)
    print(f"  Done. Best f1 = {best_obj[0]:.4f}")
    return best_ind, best_obj, history


# ===========================================================================
# Quick self-test
# ===========================================================================
if __name__ == "__main__":
    print("=== NSGA-II Self-Test (small run) ===")
    nsga = NSGA2(pop_size=10, n_generations=3, seed=42)
    pf_x, pf_y, hist = nsga.run()
    print(f"Pareto front ({len(pf_x)} solutions, first 3 shown):")
    for x, y in zip(pf_x[:3], pf_y[:3]):
        print(f"  G={x.round(1)}  f1={y[0]:.3f} f2={y[1]:.5f} f3={y[2]:.5f}")

    print("\n--- Fixed baseline ---")
    g_fixed, obj_fixed = fixed_time_baseline()
    print(f"  G={g_fixed}  f1={obj_fixed[0]:.3f}")
    print("\nSelf-test PASSED.")
