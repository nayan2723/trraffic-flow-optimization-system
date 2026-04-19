import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import type { SystemMetrics } from '../../hooks/useSimulation';

type ChartMode = 'wait' | 'emissions' | 'fuel';

const chartConfigs: Record<ChartMode, {
  title: string;
  baseKey: keyof SystemMetrics;
  aiKey: keyof SystemMetrics;
  baseLabel: string;
  aiLabel: string;
  gradientId: string;
  color: string;
  yUnit: string;
}> = {
  wait: {
    title: 'Average Wait Time',
    baseKey: 'baselineWait',
    aiKey: 'aiWait',
    baseLabel: 'Fixed Timing (s/veh)',
    aiLabel: 'NSGA-II Optimized (s/veh)',
    gradientId: 'waitGradient',
    color: '#00f0ff',
    yUnit: 's/veh',
  },
  emissions: {
    title: 'Emission Index',
    baseKey: 'baselineEmissions',
    aiKey: 'aiEmissions',
    baseLabel: 'Fixed Timing',
    aiLabel: 'NSGA-II Optimized',
    gradientId: 'emissionGradient',
    color: '#39ff14',
    yUnit: 'idx',
  },
  fuel: {
    title: 'Fuel Consumption',
    baseKey: 'baselineFuel',
    aiKey: 'aiFuel',
    baseLabel: 'Fixed Timing',
    aiLabel: 'NSGA-II Optimized',
    gradientId: 'fuelGradient',
    color: '#ff00ff',
    yUnit: 'idx',
  },
};

export default function AnalyticsChart({ data }: { data: SystemMetrics[] }) {
  const [mode, setMode] = useState<ChartMode>('wait');
  const config = chartConfigs[mode];

  return (
    <div className="glass-panel p-6 rounded-xl" id="analytics-chart">
      {/* Header with mode switcher */}
      <div className="flex items-center justify-between mb-5">
        <h3 className="section-label !mb-0">{config.title}</h3>
        <div className="flex gap-1 bg-surface2/50 rounded-lg p-0.5 border border-white/[0.04]">
          {(Object.keys(chartConfigs) as ChartMode[]).map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1 rounded text-[10px] font-mono uppercase tracking-wider transition-all duration-200 ${
                mode === m
                  ? 'bg-primary/15 text-primary'
                  : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              {m === 'wait' ? 'Wait' : m === 'emissions' ? 'CO₂' : 'Fuel'}
            </button>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex gap-5 mb-4 text-[10px] font-mono">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-[2px] rounded bg-zinc-500" />
          <span className="text-zinc-500">{config.baseLabel}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-[2px] rounded" style={{ background: config.color }} />
          <span style={{ color: config.color }}>{config.aiLabel}</span>
        </div>
      </div>

      {/* Chart */}
      <AnimatePresence mode="wait">
        <motion.div
          key={mode}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
          className="w-full h-[220px]"
          style={{ minHeight: 220 }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 0 }}>
              <defs>
                <linearGradient id={`${config.gradientId}AI`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={config.color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={config.color} stopOpacity={0} />
                </linearGradient>
                <linearGradient id={`${config.gradientId}Base`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6b7280" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#6b7280" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1e" vertical={false} />
              <XAxis
                dataKey="time"
                stroke="#27272a"
                fontSize={9}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => `${v}s`}
                interval="preserveStartEnd"
                tick={{ fill: '#52525b', fontFamily: '"JetBrains Mono", monospace' }}
              />
              <YAxis
                stroke="#27272a"
                fontSize={9}
                tickLine={false}
                axisLine={false}
                width={42}
                tick={{ fill: '#52525b', fontFamily: '"JetBrains Mono", monospace' }}
                label={{
                  value: config.yUnit,
                  angle: -90,
                  position: 'insideLeft',
                  offset: 14,
                  fill: '#52525b',
                  fontSize: 9,
                  fontFamily: '"JetBrains Mono", monospace',
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0a0a0c',
                  border: '1px solid #27272a',
                  borderRadius: '6px',
                  fontFamily: '"JetBrains Mono", monospace',
                  fontSize: '11px',
                  boxShadow: '0 8px 32px rgba(0,0,0,0.5)'
                }}
                itemStyle={{ color: '#e4e4e7' }}
                cursor={{ stroke: 'rgba(0,240,255,0.2)' }}
              />
              <Area
                type="monotone"
                dataKey={config.baseKey as string}
                name={config.baseLabel}
                stroke="#6b7280"
                strokeWidth={1}
                fillOpacity={1}
                fill={`url(#${config.gradientId}Base)`}
                isAnimationActive={false}
              />
              <Area
                type="monotone"
                dataKey={config.aiKey as string}
                name={config.aiLabel}
                stroke={config.color}
                strokeWidth={2}
                fillOpacity={1}
                fill={`url(#${config.gradientId}AI)`}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      </AnimatePresence>

      {/* Summary stats */}
      {data.length > 0 && (
        <div className="mt-4 grid grid-cols-3 gap-2 text-center">
          <div className="metric-card">
            <div className="metric-label">Baseline Avg</div>
            <div className="text-xs font-mono text-zinc-400 mt-1">
              {(data.reduce((s, d) => s + (d[config.baseKey] as number), 0) / data.length).toFixed(1)}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">AI Avg</div>
            <div className="text-xs font-mono mt-1" style={{ color: config.color }}>
              {(data.reduce((s, d) => s + (d[config.aiKey] as number), 0) / data.length).toFixed(1)}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Reduction</div>
            <div className="text-xs font-mono text-semantic-safe mt-1">
              {(() => {
                const baseAvg = data.reduce((s, d) => s + (d[config.baseKey] as number), 0) / data.length;
                const aiAvg = data.reduce((s, d) => s + (d[config.aiKey] as number), 0) / data.length;
                const pct = ((baseAvg - aiAvg) / (baseAvg || 1)) * 100;
                return `${pct.toFixed(0)}%`;
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
