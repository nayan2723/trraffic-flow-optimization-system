# Multi-Objective Traffic Flow Optimization & Dashboard

An academic mini-project implementing **NSGA-II** — a fast elitist multi-objective genetic algorithm — to find Pareto-optimal signal timing plans for a 4-way traffic intersection, complete with a **modern interactive React dashboard**.

---

## 🎯 Objectives

| Symbol | Objective | Description |
|--------|-----------|-------------|
| f₁ | Avg Waiting Time | Average time a vehicle waits at the intersection (s/veh) |
| f₂ | Fuel Consumption | Total fuel wasted due to idling (index) |
| f₃ | Emission Index | CO₂-equivalent emissions from stop-and-go traffic |

> No weighted sum is used. NSGA-II discovers the full **Pareto front**.

---

## ✨ Features

- **NSGA-II Backend**: Custom implementation using pure NumPy.
- **Interactive Visualizations**: Generates rich interactive Plotly HTML reports (2D/3D Pareto fronts, convergence, before/after, green heatmaps).
- **Data Export & Analysis**: Integrated CSV and JSON export capabilities for the generated Pareto front.
- **Interactive Terminal Workflow**: Step-by-step CLI decision support mode to choose exact trade-offs.
- **Sensitivity Analysis**: Built-in methods to test algorithm robustness under ±20% variable traffic density scenarios.
- **Modern React Frontend**: A cutting-edge dashboard featuring dark mode aesthetics, Framer Motion animations, interactive graphical data, and React Bits components.

---

## 🗂 Project Structure

```
traffic_nsga2/
├── frontend/             # 🚀 NEW: React + Vite + Tailwind + Framer Motion Dashboard
├── results/              # Auto-generated timestamped outputs (.json, .html, .csv)
├── simulation.py         # 4-way Poisson intersection simulator
├── objectives.py         # 3-objective evaluation + constraint repair
├── nsga2_optimizer.py    # NSGA-II (from scratch) + baselines
├── visualization.py      # Plotly interactive 2D/3D Pareto plots + convergence
├── config_loader.py      # Configuration parsing and setup
├── main.py               # Main CLI entry point
├── config.json           # Traffic and algorithm configuration
└── README.md
```

---

## ⚙️ Installation

### 1. Python Backend

Requires **Python 3.9+**. Install the required packages (standard scientific stack + Plotly for interactive visuals):

```bash
pip install numpy matplotlib scipy plotly pandas
```

> **DEAP is NOT required.** NSGA-II is implemented from scratch using NumPy.

### 2. React Frontend

Requires **Node.js 18+**. Navigate to the frontend directory and install the required dependencies:

```bash
cd frontend
npm install
```

---

## 🚀 How to Run

### Running the Optimizer Engine

You can run the optimizer from the root directory (`traffic_nsga2`). It provides multiple modes:

```bash
# 1. Default Run (loads config.json and outputs HTML/PNG)
python main.py

# 2. Interactive CLI Mode
python main.py --interactive

# 3. Auto-Open Generated HTML Visuals in Browser
python main.py --open

# 4. Generate & Export Pareto Front Data
python main.py --export-csv --export-json

# 5. Run Sensitivity Analysis (Arrival Rates)
python main.py --sensitivity arrival_rate
```

New results (plots, JSON dumps, summaries) will be outputted to a timestamped subfolder inside `results/` matching the current run.

### Running the Dashboard

Launch the immersive front-end dashboard to visualize the flow analytics visually:

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` (or the port specified by Vite) in your browser.

---

## 🧠 Algorithm Details

### NSGA-II (Deb et al., 2002)
- **Fast non-dominated sorting** — assigns a Pareto rank to every individual in O(M·N²)
- **Crowding distance** — diversity preservation within each front
- **Binary tournament selection** — selects on (rank, crowding distance)
- **SBX crossover** — Simulated Binary Crossover with η_c = 15
- **Polynomial mutation** — η_m = 20, P_mut = 1/N_vars
