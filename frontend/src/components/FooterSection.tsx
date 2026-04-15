import { motion } from 'framer-motion';

const algorithmSteps = [
  {
    step: '01',
    title: 'Population Initialization',
    desc: 'Generate 80 random signal plans (G₁..G₄) within [min_green, max_cycle] constraints. Repair infeasible solutions via proportional scaling.',
    icon: '🧬',
  },
  {
    step: '02',
    title: 'Fitness Evaluation',
    desc: 'Simulate each plan through a discrete-time queue model with Poisson arrivals. Compute f₁(wait), f₂(fuel), f₃(emission) objectives.',
    icon: '📊',
  },
  {
    step: '03',
    title: 'Non-Dominated Sort',
    desc: 'Assign Pareto front ranks using fast_non_dominated_sort — O(MN²). Rank 0 = non-dominated solutions forming the Pareto frontier.',
    icon: '📐',
  },
  {
    step: '04',
    title: 'Crowding Distance',
    desc: 'Calculate diversity measure within each front. Boundary solutions receive ∞ distance. Prevents solution clustering on the Pareto front.',
    icon: '🔬',
  },
  {
    step: '05',
    title: 'Selection & Crossover',
    desc: 'Binary tournament on (rank, crowding). SBX crossover (η_c=15) produces offspring. Polynomial mutation (η_m=20) adds exploration.',
    icon: '🔀',
  },
  {
    step: '06',
    title: 'Elitist Merge',
    desc: 'Combine parent + offspring (2N). Re-sort and select top N by rank then crowding distance. Guarantees Pareto front preservation.',
    icon: '⚡',
  },
];

export default function FooterSection() {
  return (
    <footer className="relative z-10 border-t border-white/[0.04]">
      {/* Algorithm Explainer */}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-10%' }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="section-label justify-center">How It Works</h2>
          <h3 className="text-3xl md:text-4xl font-bold tracking-tight mt-3">
            NSGA-II <span className="gradient-text">Pipeline</span>
          </h3>
          <p className="text-zinc-500 mt-4 max-w-xl mx-auto text-sm leading-relaxed">
            Deb et al. (2002) — A fast and elitist multi-objective genetic algorithm.
            60 generations × 80 population = 9,600 evaluations per optimization cycle.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {algorithmSteps.map((step, i) => (
            <motion.div
              key={step.step}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-5%' }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="glass-panel rounded-xl p-6 group hover:border-primary/20 transition-colors duration-300"
            >
              <div className="flex items-start gap-4">
                <div className="text-2xl">{step.icon}</div>
                <div>
                  <div className="font-mono text-[10px] text-primary/60 tracking-widest mb-1">
                    STEP {step.step}
                  </div>
                  <h4 className="text-sm font-semibold text-white mb-2 tracking-tight">
                    {step.title}
                  </h4>
                  <p className="text-[11px] text-zinc-500 leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Technical Specs */}
      <section className="border-t border-white/[0.04]">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {[
              { val: '3', label: 'Objective Functions', sub: 'f₁ f₂ f₃' },
              { val: '4', label: 'Decision Variables', sub: 'G₁ G₂ G₃ G₄' },
              { val: '~40%', label: 'Wait Reduction', sub: 'vs Fixed Timing' },
              { val: '60fps', label: 'Render Performance', sub: 'Canvas + RAF' },
            ].map((spec, i) => (
              <motion.div
                key={spec.label}
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <div className="text-3xl font-bold text-white font-mono">{spec.val}</div>
                <div className="text-[11px] text-zinc-400 mt-1">{spec.label}</div>
                <div className="text-[9px] text-zinc-600 mt-0.5 font-mono">{spec.sub}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom Bar */}
      <div className="border-t border-white/[0.04] py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-primary rounded-full" style={{ boxShadow: '0 0 8px #00f0ff' }} />
            <span className="text-sm font-bold tracking-tight">UrbanFlow AI</span>
          </div>
          <div className="text-[10px] text-zinc-600 font-mono tracking-wider text-center">
            Multi-Objective Traffic Signal Optimization using NSGA-II · Deb et al. 2002
          </div>
          <a
            href="https://github.com/nayan2723/trraffic-flow-optimization-system"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-zinc-500 hover:text-primary transition-colors font-mono"
          >
            GitHub →
          </a>
        </div>
      </div>
    </footer>
  );
}
