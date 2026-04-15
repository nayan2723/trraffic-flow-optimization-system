import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useRef } from 'react';
import type { Decision } from '../../hooks/useSimulation';

// ─── Streaming Text Effect ───────────────────────────────────────
function StreamingText({ text, speed = 30 }: { text: string; speed?: number }) {
  const [displayed, setDisplayed] = useState('');
  const indexRef = useRef(0);

  useEffect(() => {
    indexRef.current = 0;
    setDisplayed('');
    const interval = setInterval(() => {
      indexRef.current += 1;
      setDisplayed(text.slice(0, indexRef.current));
      if (indexRef.current >= text.length) clearInterval(interval);
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);

  return (
    <span>
      {displayed}
      {displayed.length < text.length && <span className="cursor-blink text-primary">▌</span>}
    </span>
  );
}

// ─── "AI Thinking" Animation ─────────────────────────────────────
function AIThinkingIndicator() {
  return (
    <motion.div
      className="flex items-center gap-2 px-3 py-2 rounded bg-primary/5 border border-primary/10"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="flex gap-1">
        {[0, 1, 2].map(i => (
          <motion.div
            key={i}
            className="w-1.5 h-1.5 bg-primary rounded-full"
            animate={{ scale: [1, 1.5, 1], opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }}
          />
        ))}
      </div>
      <span className="text-[10px] font-mono text-primary/70 tracking-wider">
        OPTIMIZING SIGNAL PLAN...
      </span>
    </motion.div>
  );
}

// ─── Main Component ──────────────────────────────────────────────
export default function AIDecisionPanel({
  decisions,
  isOptimizing,
  kneeSolution,
  improvementPct,
}: {
  decisions: Decision[];
  isOptimizing: boolean;
  kneeSolution: { f1Wait: number; f2Fuel: number; f3Emission: number; greenTimes: number[] } | null;
  improvementPct: { wait: number; fuel: number; emission: number };
}) {
  const latestDecision = decisions[0];

  return (
    <div className="glass-panel p-6 rounded-xl border border-primary/10" id="ai-decision-panel">
      {/* Header */}
      <div className="flex items-center justify-between mb-5 pb-4 border-b border-primary/10">
        <h3 className="section-label !mb-0">NSGA-II Engine Feed</h3>
        <div className="flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full ${isOptimizing ? 'bg-primary' : 'bg-zinc-600'}`}
               style={isOptimizing ? { boxShadow: '0 0 8px #00f0ff', animation: 'pulse 2s infinite' } : {}} />
          <span className="text-[10px] text-zinc-500 font-mono tracking-wider">
            {isOptimizing ? 'ACTIVE' : 'STANDBY'}
          </span>
        </div>
      </div>

      {/* Thinking indicator */}
      <AnimatePresence>
        {isOptimizing && <AIThinkingIndicator />}
      </AnimatePresence>

      {/* Decision Log */}
      <div className="mt-4 relative overflow-hidden bg-black/40 rounded-lg border border-white/[0.04] p-4 font-mono text-[11px] min-h-[180px] max-h-[220px] overflow-y-auto">
        <AnimatePresence>
          {decisions.map((d, i) => (
            <motion.div
              key={d.id}
              initial={{ opacity: 0, x: -15, filter: 'blur(4px)' }}
              animate={{ opacity: Math.max(0.2, 1 - i * 0.15), x: 0, filter: 'blur(0px)' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.35, ease: [0.19, 1, 0.22, 1] }}
              className="mb-3 border-l-[2px] border-primary/40 pl-3"
            >
              <div className="text-zinc-600 mb-0.5 flex items-center gap-2">
                <span>{d.timestamp}</span>
                <span className="text-accent-magenta/70">
                  {i === 0 ? <StreamingText text={d.action} speed={20} /> : d.action}
                </span>
              </div>
              <div className="text-primary/80 flex gap-2">
                <span className="text-zinc-600">›</span>
                <span>{d.reason}</span>
              </div>
              {i === 0 && d.deltaWait && (
                <div className="mt-1 flex gap-3 text-[9px]">
                  <span className="text-semantic-safe">Δwait {d.deltaWait.toFixed(1)}s</span>
                  <span className="text-semantic-safe">Δemit {d.deltaEmissions?.toFixed(1)}</span>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Blinking cursor at bottom */}
        {isOptimizing && decisions.length > 0 && (
          <motion.div
            animate={{ opacity: [1, 0, 1] }}
            transition={{ duration: 0.8, repeat: Infinity }}
            className="text-primary mt-1"
          >
            ▌
          </motion.div>
        )}

        {decisions.length === 0 && (
          <div className="text-zinc-600 text-center py-8">
            <div className="mb-2">Awaiting simulation start...</div>
            <div className="text-[9px] text-zinc-700">Engine will produce decisions on phase transitions</div>
          </div>
        )}
      </div>

      {/* Signal Timing Breakdown */}
      {kneeSolution && (
        <div className="mt-5 space-y-3">
          <div className="text-[10px] text-zinc-500 uppercase tracking-[0.15em] font-mono">
            Optimal Signal Timing (Knee-point)
          </div>
          <div className="grid grid-cols-4 gap-2">
            {(['N', 'S', 'E', 'W'] as const).map((dir, i) => (
              <motion.div
                key={dir}
                className="metric-card text-center"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <div className="metric-label">{dir}</div>
                <div className="text-sm font-bold text-primary font-mono mt-1">
                  {kneeSolution.greenTimes[i].toFixed(1)}s
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Improvement Metrics */}
      <div className="mt-4 grid grid-cols-3 gap-2">
        <div className="metric-card">
          <div className="metric-label">Wait Δ</div>
          <div className={`text-sm font-bold font-mono mt-1 ${improvementPct.wait > 0 ? 'text-semantic-safe text-glow-safe' : 'text-zinc-400'}`}>
            {improvementPct.wait > 0 ? '+' : ''}{improvementPct.wait.toFixed(1)}%
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Fuel Δ</div>
          <div className={`text-sm font-bold font-mono mt-1 ${improvementPct.fuel > 0 ? 'text-semantic-safe text-glow-safe' : 'text-zinc-400'}`}>
            {improvementPct.fuel > 0 ? '+' : ''}{improvementPct.fuel.toFixed(1)}%
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Emiss Δ</div>
          <div className={`text-sm font-bold font-mono mt-1 ${improvementPct.emission > 0 ? 'text-semantic-safe text-glow-safe' : 'text-zinc-400'}`}>
            {improvementPct.emission > 0 ? '+' : ''}{improvementPct.emission.toFixed(1)}%
          </div>
        </div>
      </div>
    </div>
  );
}
