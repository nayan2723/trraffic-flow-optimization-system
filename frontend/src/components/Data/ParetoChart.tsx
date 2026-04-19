/**
 * ParetoChart.tsx
 * ================
 * Interactive Pareto front scatter chart matching the backend Plotly outputs.
 *
 * Axis modes:
 *   f1vf3 → Wait (s/veh) vs Emission index  [default — matches PPT]
 *   f1vf2 → Wait (s/veh) vs Fuel index
 *   f2vf3 → Fuel index vs Emission index
 *
 * Knee-point (best trade-off) is highlighted in magenta, matching
 * the backend select_best_tradeoff() knee-point calculation.
 */
import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import type { ParetoSolution } from '../../hooks/useSimulation';

type AxisMode = 'f1vf3' | 'f1vf2' | 'f2vf3';

const AXIS_CONFIG: Record<AxisMode, { x: string; y: string; xKey: keyof ParetoSolution; yKey: keyof ParetoSolution }> = {
  f1vf3: { x: 'f₁ Wait (s/veh)', y: 'f₃ Emission idx', xKey: 'f1Wait', yKey: 'f3Emission' },
  f1vf2: { x: 'f₁ Wait (s/veh)', y: 'f₂ Fuel idx',     xKey: 'f1Wait', yKey: 'f2Fuel'     },
  f2vf3: { x: 'f₂ Fuel idx',     y: 'f₃ Emission idx', xKey: 'f2Fuel', yKey: 'f3Emission' },
};

/* Custom tooltip for the scatter points */
const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: { payload: { f1Wait: number; f2Fuel: number; f3Emission: number; rank: number; isKnee: boolean } }[] }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: '#0a0a0c',
      border: '1px solid #27272a',
      borderRadius: 6,
      padding: '8px 12px',
      fontFamily: '"JetBrains Mono", monospace',
      fontSize: 10,
    }}>
      {d.isKnee && (
        <div style={{ color: '#ff00ff', marginBottom: 4, fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          ★ Knee-point (Best Trade-off)
        </div>
      )}
      <div style={{ color: '#00f0ff' }}>f₁ Wait: {d.f1Wait.toFixed(3)} s/veh</div>
      <div style={{ color: '#39ff14' }}>f₂ Fuel: {d.f2Fuel.toFixed(5)}</div>
      <div style={{ color: '#ff9900' }}>f₃ Emit: {d.f3Emission.toFixed(5)}</div>
      <div style={{ color: '#52525b', fontSize: 9, marginTop: 4 }}>Pareto rank: {d.rank}</div>
    </div>
  );
};

export default function ParetoChart({
  paretoFront,
  kneeSolution,
}: {
  paretoFront: ParetoSolution[];
  kneeSolution: ParetoSolution | null;
}) {
  const [axis, setAxis] = useState<AxisMode>('f1vf3');
  const cfg = AXIS_CONFIG[axis];

  /* Build scatter data — split knee-point from the rest */
  const baseData = paretoFront
    .filter(s => !(kneeSolution && Math.abs(s.f1Wait - kneeSolution.f1Wait) < 0.01 && Math.abs(s.f3Emission - kneeSolution.f3Emission) < 0.01))
    .map(s => ({
      x: s[cfg.xKey] as number,
      y: s[cfg.yKey] as number,
      f1Wait: s.f1Wait,
      f2Fuel: s.f2Fuel,
      f3Emission: s.f3Emission,
      rank: s.rank,
      isKnee: false,
    }));

  const kneeData = kneeSolution
    ? [{
        x: kneeSolution[cfg.xKey] as number,
        y: kneeSolution[cfg.yKey] as number,
        f1Wait: kneeSolution.f1Wait,
        f2Fuel: kneeSolution.f2Fuel,
        f3Emission: kneeSolution.f3Emission,
        rank: kneeSolution.rank,
        isKnee: true,
      }]
    : [];

  if (paretoFront.length === 0) {
    return (
      <div className="glass-panel p-6 rounded-xl" id="pareto-chart">
        <h3 className="section-label">Pareto Front</h3>
        <div className="h-[220px] flex items-center justify-center">
          <span className="text-zinc-600 text-[11px] font-mono tracking-widest">
            Start simulation to generate Pareto front
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-panel p-6 rounded-xl border border-white/[0.04]" id="pareto-chart">
      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="section-label !mb-0.5">Pareto Front</h3>
          <p className="text-[10px] text-zinc-600 font-mono">
            {paretoFront.length} non-dominated solutions · NSGA-II (Deb et al. 2002)
          </p>
        </div>

        {/* Axis projection switcher */}
        <div className="flex gap-1 bg-surface2/50 rounded-lg p-0.5 border border-white/[0.04]">
          {(Object.keys(AXIS_CONFIG) as AxisMode[]).map(m => (
            <button
              key={m}
              onClick={() => setAxis(m)}
              className={`px-2.5 py-1 rounded text-[9px] font-mono uppercase tracking-wider transition-all duration-200 ${
                axis === m
                  ? 'bg-primary/15 text-primary'
                  : 'text-zinc-600 hover:text-zinc-400'
              }`}
            >
              {m === 'f1vf3' ? 'f₁/f₃' : m === 'f1vf2' ? 'f₁/f₂' : 'f₂/f₃'}
            </button>
          ))}
        </div>
      </div>

      {/* ── Legend ── */}
      <div className="flex items-center gap-5 mb-3 text-[10px] font-mono">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: 'rgba(0,240,255,0.7)', boxShadow: '0 0 6px rgba(0,240,255,0.4)' }} />
          <span className="text-zinc-500">Non-dominated solution</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: '#ff00ff', boxShadow: '0 0 8px #ff00ff' }} />
          <span className="text-zinc-400">Knee-point (balanced trade-off)</span>
        </div>
      </div>

      {/* ── Scatter Chart ── */}
      <motion.div
        key={axis}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full"
        style={{ height: 220, minHeight: 220 }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 8, right: 16, left: 0, bottom: 28 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1e" />
            <XAxis
              dataKey="x"
              type="number"
              name={cfg.x}
              domain={['auto', 'auto']}
              stroke="#27272a"
              fontSize={9}
              tickLine={false}
              tickFormatter={(v: number) => v.toFixed(2)}
              label={{
                value: cfg.x,
                position: 'insideBottom',
                offset: -16,
                fill: '#52525b',
                fontSize: 9,
                fontFamily: '"JetBrains Mono", monospace',
              }}
            />
            <YAxis
              dataKey="y"
              type="number"
              name={cfg.y}
              domain={['auto', 'auto']}
              stroke="#27272a"
              fontSize={9}
              tickLine={false}
              width={52}
              tickFormatter={(v: number) => v.toFixed(3)}
              label={{
                value: cfg.y,
                angle: -90,
                position: 'insideLeft',
                offset: 16,
                fill: '#52525b',
                fontSize: 9,
                fontFamily: '"JetBrains Mono", monospace',
              }}
            />
            <ZAxis range={[40, 40]} />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3', stroke: 'rgba(0,240,255,0.2)' }} />

            {/* Pareto solutions */}
            <Scatter
              data={baseData}
              fill="#00f0ff"
              fillOpacity={0.55}
              stroke="#00f0ff"
              strokeWidth={0.5}
              strokeOpacity={0.4}
              name="Pareto Solution"
            />

            {/* Knee-point */}
            {kneeData.length > 0 && (
              <Scatter
                data={kneeData}
                fill="#ff00ff"
                fillOpacity={1}
                stroke="#ff00ff"
                strokeWidth={2}
                name="Knee-point"
              />
            )}
          </ScatterChart>
        </ResponsiveContainer>
      </motion.div>

      {/* ── Knee-point summary stats ── */}
      {kneeSolution && (
        <div className="mt-4 grid grid-cols-3 gap-2 text-center">
          <div className="metric-card">
            <div className="metric-label">Knee f₁</div>
            <div className="text-xs font-bold font-mono text-primary mt-1">
              {kneeSolution.f1Wait.toFixed(2)}
              <span className="text-[9px] text-zinc-500 ml-0.5">s/veh</span>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Knee f₂</div>
            <div className="text-xs font-bold font-mono text-primary mt-1">
              {kneeSolution.f2Fuel.toFixed(5)}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Knee f₃</div>
            <div className="text-xs font-bold font-mono text-primary mt-1">
              {kneeSolution.f3Emission.toFixed(5)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
