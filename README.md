# Multi-Objective Traffic Flow Optimization using NSGA-II

An academic mini-project implementing **NSGA-II** — a fast elitist multi-objective genetic algorithm — to find Pareto-optimal signal timing plans for a 4-way traffic intersection.

---

## 🎯 Objectives

| Symbol | Objective | Description |
|--------|-----------|-------------|
| f₁ | Avg Waiting Time | Average time a vehicle waits at the intersection (s/veh) |
| f₂ | Fuel Consumption | Total fuel wasted due to idling (index) |
| f₃ | Emission Index | CO₂-equivalent emissions from stop-and-go traffic |

> No weighted sum is used. NSGA-II discovers the full **Pareto front**.

---

## 🗂 Project Structure

```
traffic_nsga2/
├── simulation.py        # 4-way Poisson intersection simulator
├── objectives.py        # 3-objective evaluation + constraint repair
├── nsga2_optimizer.py   # NSGA-II (from scratch) + baselines
├── visualization.py     # 2D/3D Pareto plots + convergence graph
├── main.py              # Main entry point
├── plots/               # Generated PNG plots (created automatically)
│   ├── pareto_2d.png
│   ├── pareto_3d.png
│   └── convergence.png
└── README.md
```

---

## ⚙️ Installation

Requires **Python 3.9+** and the following packages (all standard scientific stack):

```bash
pip install numpy matplotlib scipy
```

> **DEAP is NOT required.** NSGA-II is implemented from scratch using NumPy.

---

## 🚀 How to Run

```bash
cd traffic_nsga2
python main.py
```

Expected runtime: **~30–90 seconds** depending on CPU speed.

---

## 🔧 Configuration

All key parameters can be modified in the respective modules:

| Parameter | Default | Location |
|-----------|---------|----------|
| Population size | 80 | `nsga2_optimizer.py` → `POP_SIZE` |
| Generations | 60 | `nsga2_optimizer.py` → `N_GENERATIONS` |
| Min green time | 10 s | `objectives.py` → `G_MIN` |
| Max total green | 120 s | `objectives.py` → `G_TOTAL_MAX` |
| Arrival rates λ | [0.4, 0.35, 0.45, 0.30] | `simulation.py` → `DEFAULT_SIM_PARAMS` |
| Simulation horizon | 1800 s | `simulation.py` → `DEFAULT_SIM_PARAMS` |
| Random seed | 42 | `main.py` → `GLOBAL_SEED` |

---

## 📊 Output

Running `main.py` produces:

1. **Console Output** — Performance comparison table:

```
┌──────────────────────────────────────────────────────────────┐
│               PERFORMANCE COMPARISON TABLE                   │
├──────────────────────────────────────────────────────────────┤
│  Method                 f1 Wait(s/veh)    f2 Fuel   f3 Emiss│
├──────────────────────────────────────────────────────────────┤
│  Fixed-time Baseline          …              …          …   │
│  Single-obj GA                …              …          …   │
│  NSGA-II Best Tradeoff        …              …          …   │
└──────────────────────────────────────────────────────────────┘
```

2. **plots/pareto_2d.png** — 2D Pareto projections (f1 vs f2, f1 vs f3)
3. **plots/pareto_3d.png** — 3D Pareto scatter coloured by f1
4. **plots/convergence.png** — Best f1 per generation for both algorithms

---

## 🧠 Algorithm Details

### NSGA-II (Deb et al., 2002)
- **Fast non-dominated sorting** — assigns a Pareto rank to every individual in O(M·N²)
- **Crowding distance** — diversity preservation within each front
- **Binary tournament selection** — selects on (rank, crowding distance)
- **SBX crossover** — Simulated Binary Crossover with η_c = 15
- **Polynomial mutation** — η_m = 20, P_mut = 1/N_vars
