import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import Hero from './components/Hero/Hero';
import SimulationEngine from './components/Simulation/SimulationEngine';
import ControlPanel from './components/Controls/ControlPanel';
import AIDecisionPanel from './components/Controls/AIDecisionPanel';
import AnalyticsChart from './components/Data/AnalyticsChart';
import ParetoChart from './components/Data/ParetoChart';
import MetricsBar from './components/Data/MetricsBar';
import FooterSection from './components/FooterSection';
import { useSimulation } from './hooks/useSimulation';

// ─── Sticky Navigation Bar ────────────────────────────────────────
function NavBar({ isRunning, aiMode }: { isRunning: boolean; aiMode: boolean }) {
  return (
    <motion.nav
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.19, 1, 0.22, 1] }}
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4"
      style={{
        background: 'rgba(5,5,5,0.8)',
        backdropFilter: 'blur(24px)',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
      }}
    >
      <div className="flex items-center gap-2.5">
        <div
          className="w-2 h-2 bg-primary rounded-full"
          style={{ boxShadow: '0 0 8px #00f0ff' }}
        />
        <span className="text-sm font-bold tracking-tight">
          UrbanFlow <span className="text-primary">AI</span>
        </span>
      </div>

      {/* Nav links — each anchored to distinct sections */}
      <div className="hidden md:flex items-center gap-8 text-[11px] font-mono text-zinc-500 tracking-wider uppercase">
        <a href="#engine"    className="hover:text-primary transition-colors duration-200">Simulation</a>
        <a href="#analytics" className="hover:text-primary transition-colors duration-200">Pareto / Analytics</a>
        <span className="text-zinc-700">NSGA-II</span>
      </div>

      <div className="flex items-center gap-3">
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-mono transition-all duration-300 border ${
            isRunning
              ? 'bg-primary/10 text-primary border-primary/20'
              : 'bg-surface2/60 text-zinc-500 border-white/[0.04]'
          }`}
        >
          <div
            className={`w-1.5 h-1.5 rounded-full ${isRunning ? 'bg-primary' : 'bg-zinc-600'}`}
            style={isRunning ? { boxShadow: '0 0 6px #00f0ff' } : {}}
          />
          {isRunning ? (aiMode ? 'NSGA-II LIVE' : 'FIXED TIMING') : 'STANDBY'}
        </div>
        <a
          href="https://github.com/nayan2723/trraffic-flow-optimization-system"
          target="_blank"
          rel="noopener noreferrer"
          className="text-zinc-600 hover:text-zinc-300 transition-colors"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
          </svg>
        </a>
      </div>
    </motion.nav>
  );
}

// ─── Main App ─────────────────────────────────────────────────────
export default function App() {
  const sim = useSimulation();

  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start end', 'end start'],
  });

  const bgY = useTransform(scrollYProgress, [0, 1], ['0%', '15%']);

  return (
    <div className="bg-background min-h-screen text-slate-200" ref={containerRef}>
      <NavBar isRunning={sim.isRunning} aiMode={sim.aiMode} />

      {/* Ambient parallax grid */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <motion.div
          style={{
            y: bgY,
            backgroundImage:
              'linear-gradient(to right,rgba(0,240,255,0.018) 1px,transparent 1px),linear-gradient(to bottom,rgba(0,240,255,0.018) 1px,transparent 1px)',
            backgroundSize: '40px 40px',
          }}
          className="absolute inset-0 opacity-30 mix-blend-screen"
        />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,#050505_100%)]" />
      </div>

      <main className="relative z-10 flex flex-col">
        {/* ── HERO ── */}
        <Hero
          onCTA={() => {
            document.getElementById('engine')?.scrollIntoView({ behavior: 'smooth' });
            if (!sim.isRunning) sim.setIsRunning(true);
          }}
        />

        {/* ── LIVE METRICS BAR ── */}
        <section className="max-w-7xl mx-auto px-6 w-full -mt-8 relative z-20">
          <MetricsBar
            history={sim.history}
            trafficState={sim.trafficState}
            isRunning={sim.isRunning}
            aiMode={sim.aiMode}
          />
        </section>

        {/* ── ENGINE SECTION ── */}
        <section id="engine" className="relative max-w-7xl mx-auto px-6 w-full pt-16 pb-8">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-10%' }}
            transition={{ duration: 0.6 }}
            className="mb-10"
          >
            <h2 className="section-label">Live Simulation Engine</h2>
            <h3 className="text-2xl md:text-[2rem] font-extrabold tracking-tight mt-1">
              Digital Twin <span className="gradient-text">Render</span>
            </h3>
            <p className="text-zinc-500 mt-2 text-sm max-w-xl leading-relaxed">
              Real-time 4-way intersection — Poisson arrivals, queue-based
              car-following model, congestion heatmap, and NSGA-II adaptive
              signal control.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Sticky simulation canvas */}
            <div className="lg:col-span-7 lg:sticky lg:top-24 z-20">
              <motion.div
                initial={{ opacity: 0, x: -40 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: '-8%' }}
                transition={{ duration: 0.7, ease: [0.19, 1, 0.22, 1] }}
              >
                <SimulationEngine
                  density={sim.density}
                  activePhase={sim.activePhase}
                  aiMode={sim.aiMode}
                  isRunning={sim.isRunning}
                  nightMode={sim.nightMode}
                  heatmapEnabled={sim.heatmapEnabled}
                  timeLapseSpeed={sim.timeLapseSpeed}
                />
              </motion.div>
            </div>

            {/* Scrolling right panels */}
            <div className="lg:col-span-5 flex flex-col gap-5 pb-8 z-10">
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-8%' }}
                transition={{ duration: 0.6, delay: 0.1 }}
              >
                <ControlPanel
                  density={sim.density}
                  setDensity={sim.setDensity}
                  aiMode={sim.aiMode}
                  setAiMode={sim.setAiMode}
                  isRunning={sim.isRunning}
                  setIsRunning={sim.setIsRunning}
                  nightMode={sim.nightMode}
                  setNightMode={sim.setNightMode}
                  heatmapEnabled={sim.heatmapEnabled}
                  setHeatmapEnabled={sim.setHeatmapEnabled}
                  timeLapseSpeed={sim.timeLapseSpeed}
                  setTimeLapseSpeed={sim.setTimeLapseSpeed}
                  onReset={sim.resetSimulation}
                />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-8%' }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <AIDecisionPanel
                  decisions={sim.decisions}
                  isOptimizing={sim.aiMode && sim.isRunning}
                  kneeSolution={sim.kneeSolution}
                  improvementPct={sim.improvementPct}
                />
              </motion.div>
            </div>
          </div>
        </section>

        {/* ── ANALYTICS & PARETO SECTION ─────────────────────────────── */}
        {/* Dedicated full-width section so it's always clearly visible
            and the nav "Pareto / Analytics" link scrolls here correctly. */}
        <section id="analytics" className="relative max-w-7xl mx-auto px-6 w-full py-16">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-10%' }}
            transition={{ duration: 0.6 }}
            className="mb-10"
          >
            <h2 className="section-label">Multi-Objective Analysis</h2>
            <h3 className="text-2xl md:text-[2rem] font-extrabold tracking-tight mt-1">
              Pareto Front &amp; <span className="gradient-text">Metrics</span>
            </h3>
            <p className="text-zinc-500 mt-2 text-sm max-w-xl leading-relaxed">
              NSGA-II discovers the full Pareto front — no weighted sum, no bias.
              Each scatter point is a non-dominated signal plan trade-off between f₁, f₂, and f₃.
            </p>
          </motion.div>

          {/* 2-column: Pareto chart (wider) + Analytics chart */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: '-5%' }}
              transition={{ duration: 0.6, delay: 0.05 }}
            >
              <ParetoChart
                paretoFront={sim.paretoFront}
                kneeSolution={sim.kneeSolution}
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: '-5%' }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <AnalyticsChart data={sim.history} />
            </motion.div>
          </div>
        </section>

        {/* ── FOOTER ── */}
        <FooterSection />
      </main>
    </div>
  );
}
