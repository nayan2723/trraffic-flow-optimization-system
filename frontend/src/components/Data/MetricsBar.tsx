import { motion } from 'framer-motion';
import { useAnimatedValue, useAnimatedInteger } from '../../hooks/useAnimatedValue';
import type { SystemMetrics, TrafficState } from '../../hooks/useSimulation';

interface Props {
  history: SystemMetrics[];
  trafficState: TrafficState;
  isRunning: boolean;
  aiMode: boolean;
}

function MetricTile({
  label,
  value,
  unit,
  color = 'text-white',
  trend,
}: {
  label: string;
  value: string;
  unit?: string;
  color?: string;
  trend?: 'up' | 'down' | 'neutral';
}) {
  return (
    <div className="metric-card flex-1 min-w-0">
      <div className="metric-label">{label}</div>
      <div className={`text-base font-bold font-mono mt-1 tabular-nums ${color}`}>
        {value}
        {unit && <span className="text-[10px] text-zinc-500 ml-0.5">{unit}</span>}
      </div>
      {trend && trend !== 'neutral' && (
        <div className={`text-[9px] mt-0.5 ${trend === 'down' ? 'text-semantic-safe' : 'text-semantic-danger'}`}>
          {trend === 'down' ? '↓' : '↑'}
        </div>
      )}
    </div>
  );
}

export default function MetricsBar({ history, trafficState, isRunning, aiMode }: Props) {
  const latest = history.length > 0 ? history[history.length - 1] : null;
  const prev = history.length > 1 ? history[history.length - 2] : null;

  const currentWait = useAnimatedValue(latest?.aiWait ?? 0, 300);
  const currentEmissions = useAnimatedValue(latest?.aiEmissions ?? 0, 300);
  const throughput = useAnimatedInteger(latest?.throughput ?? 0, 300);

  const totalQueued = useAnimatedInteger(
    Object.values(trafficState.queueLengths).reduce((a, b) => a + b, 0),
    300
  );

  const waitTrend = prev && latest
    ? (latest.aiWait < prev.aiWait ? 'down' : latest.aiWait > prev.aiWait ? 'up' : 'neutral')
    : 'neutral';

  if (!isRunning && history.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel rounded-xl p-4 flex items-center justify-center"
      >
        <span className="text-xs font-mono text-zinc-600 tracking-widest uppercase">
          System metrics will appear when simulation is active
        </span>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-panel rounded-xl p-4"
      id="metrics-bar"
    >
      <div className="flex gap-3 overflow-x-auto">
        <MetricTile
          label="Avg Wait"
          value={currentWait.toFixed(1)}
          unit="s/veh"
          color={currentWait > 50 ? 'text-semantic-danger' : currentWait > 25 ? 'text-semantic-warning' : 'text-semantic-safe'}
          trend={waitTrend as 'up' | 'down' | 'neutral'}
        />
        <MetricTile
          label="Emissions"
          value={currentEmissions.toFixed(1)}
          unit="idx"
          color={currentEmissions > 80 ? 'text-semantic-danger' : 'text-primary'}
        />
        <MetricTile
          label="Throughput"
          value={`${throughput}`}
          unit="veh/h"
          color="text-white"
        />
        <MetricTile
          label="Queued"
          value={`${totalQueued}`}
          unit="veh"
          color={totalQueued > 30 ? 'text-semantic-danger' : 'text-zinc-300'}
        />
        <MetricTile
          label="Mode"
          value={aiMode ? 'NSGA-II' : 'Fixed'}
          color={aiMode ? 'text-primary' : 'text-zinc-500'}
        />
      </div>
    </motion.div>
  );
}
