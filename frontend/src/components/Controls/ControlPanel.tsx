import { motion } from 'framer-motion';
import { useAnimatedValue } from '../../hooks/useAnimatedValue';

interface Props {
  density: number;
  setDensity: (v: number) => void;
  aiMode: boolean;
  setAiMode: (v: boolean) => void;
  isRunning: boolean;
  setIsRunning: (v: boolean) => void;
  nightMode: boolean;
  setNightMode: (v: boolean) => void;
  heatmapEnabled: boolean;
  setHeatmapEnabled: (v: boolean) => void;
  timeLapseSpeed: number;
  setTimeLapseSpeed: (v: number) => void;
  onReset: () => void;
}

function Toggle({ label, value, onChange, id }: { label: string; value: boolean; onChange: (v: boolean) => void; id: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="font-mono text-[11px] text-zinc-400 tracking-wide">{label}</span>
      <button
        id={id}
        onClick={() => onChange(!value)}
        className={`toggle-switch ${value ? 'bg-primary' : 'bg-surface2 border border-border'}`}
      >
        <span className={`toggle-dot ${value ? 'translate-x-[22px]' : 'translate-x-1'}`} />
      </button>
    </div>
  );
}

export default function ControlPanel({
  density, setDensity,
  aiMode, setAiMode,
  isRunning, setIsRunning,
  nightMode, setNightMode,
  heatmapEnabled, setHeatmapEnabled,
  timeLapseSpeed, setTimeLapseSpeed,
  onReset,
}: Props) {
  const animatedDensity = useAnimatedValue(density, 200);

  const densityLevel = density > 7 ? 'CRITICAL' : density > 4 ? 'MODERATE' : 'LOW';
  const densityColor = density > 7 ? 'text-semantic-danger' : density > 4 ? 'text-semantic-warning' : 'text-semantic-safe';

  return (
    <div className="glass-panel p-6 rounded-xl border border-white/[0.04]" id="control-panel">
      <div className="flex items-center justify-between mb-6">
        <h3 className="section-label !mb-0">Traffic Parameters</h3>
        <span className={`text-[10px] font-mono ${densityColor} tracking-wider`}>
          {densityLevel}
        </span>
      </div>

      <div className="space-y-5">
        {/* ─── Density Slider ─── */}
        <div>
          <div className="flex justify-between items-end mb-3 font-mono text-[11px]">
            <span className="text-zinc-500">City Load Factor</span>
            <motion.span
              key={density}
              initial={{ scale: 1.2, opacity: 0.5 }}
              animate={{ scale: 1, opacity: 1 }}
              className={`tabular-nums ${density > 7 ? 'text-semantic-danger text-glow-danger' : 'text-primary text-glow'}`}
            >
              {animatedDensity.toFixed(1)}x
            </motion.span>
          </div>
          <input
            type="range" min="1" max="10" step="0.5"
            value={density}
            onChange={(e) => setDensity(Number(e.target.value))}
            className={`slider-track ${density > 7 ? 'danger' : ''}`}
            id="density-slider"
            style={{
              background: `linear-gradient(to right, ${density > 7 ? '#ff1414' : '#00f0ff'} ${(density / 10) * 100}%, #121214 ${(density / 10) * 100}%)`
            }}
          />
          <div className="flex justify-between mt-1.5 text-[9px] font-mono text-zinc-600">
            <span>1x</span><span>5x</span><span>10x</span>
          </div>
        </div>

        <div className="h-px w-full bg-white/[0.04]" />

        {/* ─── Toggles ─── */}
        <Toggle label="NSGA-II Override" value={aiMode} onChange={setAiMode} id="ai-toggle" />
        <Toggle label="Heatmap Overlay" value={heatmapEnabled} onChange={setHeatmapEnabled} id="heatmap-toggle" />
        <Toggle label="Night Mode" value={nightMode} onChange={setNightMode} id="night-toggle" />

        <div className="h-px w-full bg-white/[0.04]" />

        {/* ─── Time-Lapse Speed ─── */}
        <div>
          <span className="font-mono text-[11px] text-zinc-400 tracking-wide block mb-3">Time-Lapse Speed</span>
          <div className="grid grid-cols-4 gap-2">
            {[1, 2, 4, 8].map(s => (
              <button
                key={s}
                onClick={() => setTimeLapseSpeed(s)}
                className={`py-2 rounded text-[11px] font-mono tracking-wider transition-all duration-200 border ${
                  timeLapseSpeed === s
                    ? 'bg-primary/15 text-primary border-primary/40 shadow-[0_0_12px_rgba(0,240,255,0.15)]'
                    : 'bg-surface2/30 text-zinc-500 border-white/[0.04] hover:border-white/10 hover:text-zinc-300'
                }`}
                id={`speed-${s}x`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ─── Action Buttons ─── */}
      <div className="mt-8 grid grid-cols-2 gap-3">
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={() => setIsRunning(!isRunning)}
          className={`py-3 rounded text-[11px] font-mono tracking-widest uppercase transition-all duration-300 border ${
            isRunning
              ? 'bg-transparent text-semantic-danger border-semantic-danger/40 hover:bg-semantic-danger/10'
              : 'bg-primary/10 text-primary border-primary/50 hover:bg-primary/20 shadow-[0_0_20px_rgba(0,240,255,0.1)]'
          }`}
          id="run-button"
        >
          {isRunning ? '⏹ HALT' : '▶ ENGAGE'}
        </motion.button>

        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={onReset}
          className="py-3 rounded text-[11px] font-mono tracking-widest uppercase border bg-surface2/30 text-zinc-400 border-white/[0.04] hover:border-white/10 hover:text-zinc-300 transition-all duration-300"
          id="reset-button"
        >
          ↺ RESET
        </motion.button>
      </div>
    </div>
  );
}
