import { useEffect, useRef, memo } from 'react';
import { motion } from 'framer-motion';

interface Props {
  density: number;
  activePhase: number;
  aiMode: boolean;
  isRunning: boolean;
  nightMode: boolean;
  heatmapEnabled: boolean;
  timeLapseSpeed: number;
}

interface Car {
  id: number;
  axis: 'x' | 'y';
  dir: 1 | -1;
  x: number;
  y: number;
  speed: number;
  maxSpeed: number;
  waiting: boolean;
  lane: number;
  hue: number;
}

/**
 * SimulationEngine — Full Canvas-based intersection digital twin.
 * 
 * Features:
 *  - Multi-lane roads with lane markings
 *  - Continuous vehicle motion (requestAnimationFrame)
 *  - Realistic signal light gantries with glow effects
 *  - Congestion heatmap overlay
 *  - Night mode with headlights
 *  - Queue-based braking / car-following model
 */
function SimulationEngineInner({ density, activePhase, aiMode, isRunning, nightMode, heatmapEnabled, timeLapseSpeed }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const carsRef = useRef<Car[]>([]);
  const carCountRef = useRef(0);
  const propsRef = useRef({ density, activePhase, aiMode, isRunning, nightMode, heatmapEnabled, timeLapseSpeed });

  // Keep a ref to latest props to avoid effect re-triggers
  useEffect(() => {
    propsRef.current = { density, activePhase, aiMode, isRunning, nightMode, heatmapEnabled, timeLapseSpeed };
  }, [density, activePhase, aiMode, isRunning, nightMode, heatmapEnabled, timeLapseSpeed]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;
    let animId: number;
    let lastTime = performance.now();
    let nsSpawner = 0;
    let ewSpawner = 0;

    const W = 900;
    const H = 900;
    const CX = W / 2;
    const CY = H / 2;
    const RW = 160;  // Total road width
    const LANE_W = RW / 4; // 4 lanes (2 each direction)
    const STOP_DIST = RW / 2 + 25;

    canvas.width = W;
    canvas.height = H;

    // ─── Draw Functions ────────────────────────────────────────

    const drawBackground = (night: boolean) => {
      // Fill
      ctx.fillStyle = night ? '#020204' : '#080810';
      ctx.fillRect(0, 0, W, H);

      // Subtle grid
      ctx.strokeStyle = night ? 'rgba(255,255,255,0.015)' : 'rgba(255,255,255,0.025)';
      ctx.lineWidth = 0.5;
      for (let i = 0; i < W; i += 40) {
        ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, H); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(W, i); ctx.stroke();
      }

      // Building blocks (context around intersection)
      const blockColor = night ? '#06060a' : '#0c0c12';
      ctx.fillStyle = blockColor;
      // Top-left
      ctx.fillRect(0, 0, CX - RW / 2 - 10, CY - RW / 2 - 10);
      // Top-right
      ctx.fillRect(CX + RW / 2 + 10, 0, W, CY - RW / 2 - 10);
      // Bottom-left
      ctx.fillRect(0, CY + RW / 2 + 10, CX - RW / 2 - 10, H);
      // Bottom-right
      ctx.fillRect(CX + RW / 2 + 10, CY + RW / 2 + 10, W, H);

      // Block outlines
      ctx.strokeStyle = night ? 'rgba(0,240,255,0.04)' : 'rgba(0,240,255,0.06)';
      ctx.lineWidth = 1;
      ctx.strokeRect(10, 10, CX - RW / 2 - 25, CY - RW / 2 - 25);
      ctx.strokeRect(CX + RW / 2 + 15, 10, CX - RW / 2 - 25, CY - RW / 2 - 25);
      ctx.strokeRect(10, CY + RW / 2 + 15, CX - RW / 2 - 25, CY - RW / 2 - 25);
      ctx.strokeRect(CX + RW / 2 + 15, CY + RW / 2 + 15, CX - RW / 2 - 25, CY - RW / 2 - 25);
    };

    const drawRoads = () => {
      // Road surface
      ctx.fillStyle = '#0e0e14';
      ctx.fillRect(CX - RW / 2, 0, RW, H);  // NS road
      ctx.fillRect(0, CY - RW / 2, W, RW);  // EW road

      // Intersection center
      ctx.fillStyle = '#0a0a10';
      ctx.fillRect(CX - RW / 2, CY - RW / 2, RW, RW);

      // Road edges
      ctx.strokeStyle = 'rgba(0,240,255,0.12)';
      ctx.lineWidth = 1.5;
      // NS edges
      ctx.beginPath(); ctx.moveTo(CX - RW / 2, 0); ctx.lineTo(CX - RW / 2, CY - RW / 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(CX + RW / 2, 0); ctx.lineTo(CX + RW / 2, CY - RW / 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(CX - RW / 2, CY + RW / 2); ctx.lineTo(CX - RW / 2, H); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(CX + RW / 2, CY + RW / 2); ctx.lineTo(CX + RW / 2, H); ctx.stroke();
      // EW edges
      ctx.beginPath(); ctx.moveTo(0, CY - RW / 2); ctx.lineTo(CX - RW / 2, CY - RW / 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, CY + RW / 2); ctx.lineTo(CX - RW / 2, CY + RW / 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(CX + RW / 2, CY - RW / 2); ctx.lineTo(W, CY - RW / 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(CX + RW / 2, CY + RW / 2); ctx.lineTo(W, CY + RW / 2); ctx.stroke();

      // Center line (dashed)
      ctx.strokeStyle = '#333';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([12, 12]);
      // NS center
      ctx.beginPath(); ctx.moveTo(CX, 0); ctx.lineTo(CX, CY - RW / 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(CX, CY + RW / 2); ctx.lineTo(CX, H); ctx.stroke();
      // EW center
      ctx.beginPath(); ctx.moveTo(0, CY); ctx.lineTo(CX - RW / 2, CY); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(CX + RW / 2, CY); ctx.lineTo(W, CY); ctx.stroke();
      ctx.setLineDash([]);

      // Lane markings (subtle)
      ctx.strokeStyle = 'rgba(255,255,255,0.04)';
      ctx.lineWidth = 1;
      ctx.setLineDash([8, 16]);
      // NS lanes
      for (let l = 1; l < 4; l++) {
        if (l === 2) continue;
        const lx = CX - RW / 2 + l * LANE_W;
        ctx.beginPath(); ctx.moveTo(lx, 0); ctx.lineTo(lx, CY - RW / 2); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(lx, CY + RW / 2); ctx.lineTo(lx, H); ctx.stroke();
      }
      // EW lanes
      for (let l = 1; l < 4; l++) {
        if (l === 2) continue;
        const ly = CY - RW / 2 + l * LANE_W;
        ctx.beginPath(); ctx.moveTo(0, ly); ctx.lineTo(CX - RW / 2, ly); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(CX + RW / 2, ly); ctx.lineTo(W, ly); ctx.stroke();
      }
      ctx.setLineDash([]);

      // Stop lines
      ctx.strokeStyle = 'rgba(255,255,255,0.15)';
      ctx.lineWidth = 2;
      // N approach
      ctx.beginPath(); ctx.moveTo(CX - RW / 2, CY - RW / 2 - 4); ctx.lineTo(CX, CY - RW / 2 - 4); ctx.stroke();
      // S approach
      ctx.beginPath(); ctx.moveTo(CX, CY + RW / 2 + 4); ctx.lineTo(CX + RW / 2, CY + RW / 2 + 4); ctx.stroke();
      // W approach
      ctx.beginPath(); ctx.moveTo(CX - RW / 2 - 4, CY); ctx.lineTo(CX - RW / 2 - 4, CY + RW / 2); ctx.stroke();
      // E approach
      ctx.beginPath(); ctx.moveTo(CX + RW / 2 + 4, CY - RW / 2); ctx.lineTo(CX + RW / 2 + 4, CY); ctx.stroke();
    };

    const drawSignalLights = (phase: number) => {
      const nsColor = phase === 0 ? '#00f0ff' : phase === 1 ? '#ffea00' : '#ff1414';
      const ewColor = phase === 2 ? '#00f0ff' : phase === 3 ? '#ffea00' : '#ff1414';

      const drawLight = (x: number, y: number, color: string, size: number = 6) => {
        // Housing
        ctx.fillStyle = '#050508';
        ctx.strokeStyle = 'rgba(255,255,255,0.1)';
        ctx.lineWidth = 1;
        const hw = size * 2.5;
        ctx.beginPath();
        ctx.roundRect(x - hw / 2, y - hw / 2, hw, hw, 3);
        ctx.fill();
        ctx.stroke();

        // Light
        const isGreen = color === '#00f0ff';
        ctx.shadowBlur = isGreen ? 20 : (color === '#ffea00' ? 12 : 6);
        ctx.shadowColor = color;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // Glow halo
        if (isGreen) {
          const grd = ctx.createRadialGradient(x, y, size, x, y, size * 6);
          grd.addColorStop(0, `${color}20`);
          grd.addColorStop(1, 'transparent');
          ctx.fillStyle = grd;
          ctx.fillRect(x - size * 6, y - size * 6, size * 12, size * 12);
        }
      };

      // Position lights near intersection corners
      drawLight(CX - RW / 2 - 20, CY - RW / 2 - 20, nsColor, 5);
      drawLight(CX + RW / 2 + 20, CY + RW / 2 + 20, nsColor, 5);
      drawLight(CX + RW / 2 + 20, CY - RW / 2 - 20, ewColor, 5);
      drawLight(CX - RW / 2 - 20, CY + RW / 2 + 20, ewColor, 5);
    };

    const drawHeatmap = (dens: number, enabled: boolean) => {
      if (!enabled || dens <= 3) return;
      const intensity = Math.min(1, (dens - 3) / 7);

      // Center congestion
      const grd = ctx.createRadialGradient(CX, CY, 30, CX, CY, 250);
      grd.addColorStop(0, `rgba(255, 20, 20, ${0.12 * intensity})`);
      grd.addColorStop(0.5, `rgba(255, 234, 0, ${0.06 * intensity})`);
      grd.addColorStop(1, 'transparent');
      ctx.fillStyle = grd;
      ctx.fillRect(0, 0, W, H);

      // Approach heat trails
      const trailAlpha = 0.04 * intensity;
      // North approach
      const ngrd = ctx.createLinearGradient(CX, 0, CX, CY);
      ngrd.addColorStop(0, 'transparent');
      ngrd.addColorStop(1, `rgba(255, 100, 20, ${trailAlpha})`);
      ctx.fillStyle = ngrd;
      ctx.fillRect(CX - RW / 2, 0, RW, CY);
      // South
      const sgrd = ctx.createLinearGradient(CX, H, CX, CY);
      sgrd.addColorStop(0, 'transparent');
      sgrd.addColorStop(1, `rgba(255, 100, 20, ${trailAlpha})`);
      ctx.fillStyle = sgrd;
      ctx.fillRect(CX - RW / 2, CY, RW, CY);
      // East
      const egrd = ctx.createLinearGradient(W, CY, CX, CY);
      egrd.addColorStop(0, 'transparent');
      egrd.addColorStop(1, `rgba(255, 100, 20, ${trailAlpha})`);
      ctx.fillStyle = egrd;
      ctx.fillRect(CX, CY - RW / 2, CX, RW);
      // West
      const wgrd = ctx.createLinearGradient(0, CY, CX, CY);
      wgrd.addColorStop(0, 'transparent');
      wgrd.addColorStop(1, `rgba(255, 100, 20, ${trailAlpha})`);
      ctx.fillStyle = wgrd;
      ctx.fillRect(0, CY - RW / 2, CX, RW);
    };

    const drawCar = (car: Car, night: boolean, ai: boolean) => {
      const isVertical = car.axis === 'y';
      const carW = isVertical ? 14 : 26;
      const carH = isVertical ? 26 : 14;

      // Body color
      let bodyColor: string;
      if (car.waiting) {
        bodyColor = '#ff3333';
      } else if (ai) {
        bodyColor = `hsl(${car.hue}, 70%, 55%)`;
      } else {
        bodyColor = '#8888aa';
      }

      // Shadow
      if (!night) {
        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.fillRect(car.x - carW / 2 + 2, car.y - carH / 2 + 2, carW, carH);
      }

      // Body
      ctx.fillStyle = bodyColor;
      if (ai && !car.waiting) {
        ctx.shadowBlur = 6;
        ctx.shadowColor = bodyColor;
      }
      ctx.beginPath();
      ctx.roundRect(car.x - carW / 2, car.y - carH / 2, carW, carH, 3);
      ctx.fill();
      ctx.shadowBlur = 0;

      // Headlights (night mode)
      if (night) {
        ctx.fillStyle = 'rgba(255,255,200,0.8)';
        if (isVertical) {
          const hy = car.dir === 1 ? car.y + carH / 2 : car.y - carH / 2;
          ctx.beginPath();
          ctx.arc(car.x - 3, hy, 1.5, 0, Math.PI * 2);
          ctx.arc(car.x + 3, hy, 1.5, 0, Math.PI * 2);
          ctx.fill();

          // Beam
          const beamGrd = ctx.createRadialGradient(car.x, hy, 2, car.x, hy + car.dir * 50, 50);
          beamGrd.addColorStop(0, 'rgba(255,255,200,0.08)');
          beamGrd.addColorStop(1, 'transparent');
          ctx.fillStyle = beamGrd;
          ctx.fillRect(car.x - 20, hy - 20, 40, 70);
        } else {
          const hx = car.dir === 1 ? car.x + carW / 2 : car.x - carW / 2;
          ctx.beginPath();
          ctx.arc(hx, car.y - 3, 1.5, 0, Math.PI * 2);
          ctx.arc(hx, car.y + 3, 1.5, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // Windshield
      ctx.fillStyle = 'rgba(0,240,255,0.15)';
      if (isVertical) {
        const wy = car.dir === 1 ? car.y - carH / 2 + 4 : car.y + carH / 2 - 8;
        ctx.fillRect(car.x - carW / 2 + 3, wy, carW - 6, 4);
      } else {
        const wx = car.dir === 1 ? car.x - carW / 2 + 4 : car.x + carW / 2 - 8;
        ctx.fillRect(wx, car.y - carH / 2 + 3, 4, carH - 6);
      }
    };

    // ─── Simulation Update ─────────────────────────────────────

    const updateCars = (dt: number) => {
      const p = propsRef.current;
      if (!p.isRunning) return;

      const speed = p.timeLapseSpeed;
      const spawnRate = Math.max(120, 900 - p.density * 85);

      nsSpawner += dt * speed;
      ewSpawner += dt * speed;

      // Spawn NS cars
      if (nsSpawner > spawnRate) {
        nsSpawner = 0;
        const dir = (Math.random() > 0.5 ? 1 : -1) as 1 | -1;
        const lane = Math.random() > 0.5 ? 0 : 1;
        const laneOffset = dir === 1
          ? CX - RW / 2 + LANE_W * (0.5 + lane)
          : CX + LANE_W * (0.5 + lane);

        carsRef.current.push({
          id: carCountRef.current++,
          axis: 'y', dir,
          x: laneOffset,
          y: dir === 1 ? -30 : H + 30,
          speed: 0,
          maxSpeed: 0.18 + Math.random() * 0.08,
          waiting: false,
          lane,
          hue: Math.random() * 360,
        });
      }

      // Spawn EW cars
      if (ewSpawner > spawnRate) {
        ewSpawner = 0;
        const dir = (Math.random() > 0.5 ? 1 : -1) as 1 | -1;
        const lane = Math.random() > 0.5 ? 0 : 1;
        const laneOffset = dir === 1
          ? CY + LANE_W * (0.5 + lane)
          : CY - RW / 2 + LANE_W * (0.5 + lane);

        carsRef.current.push({
          id: carCountRef.current++,
          axis: 'x', dir,
          x: dir === 1 ? -30 : W + 30,
          y: laneOffset,
          speed: 0,
          maxSpeed: 0.18 + Math.random() * 0.08,
          waiting: false,
          lane,
          hue: Math.random() * 360,
        });
      }

      // Physics update
      const phase = p.activePhase;
      const nsGreen = phase === 0;
      const ewGreen = phase === 2;
      const cars = carsRef.current;

      for (let i = 0; i < cars.length; i++) {
        const car = cars[i];
        const distToCenter = car.axis === 'y'
          ? Math.abs(car.y - CY) : Math.abs(car.x - CX);

        // Is car approaching the intersection?
        const isApproaching = car.dir === 1
          ? (car.axis === 'y' ? car.y < CY - STOP_DIST : car.x < CX - STOP_DIST)
          : (car.axis === 'y' ? car.y > CY + STOP_DIST : car.x > CX + STOP_DIST);

        // Car-following: find closest car ahead
        let frontDist = 999;
        for (let j = 0; j < cars.length; j++) {
          if (i === j) continue;
          const other = cars[j];
          if (other.axis !== car.axis || other.dir !== car.dir) continue;

          const dist = car.axis === 'y'
            ? Math.abs(car.y - other.y) : Math.abs(car.x - other.x);

          // Check if other is ahead
          const isAhead = car.dir === 1
            ? (car.axis === 'y' ? other.y > car.y : other.x > car.x)
            : (car.axis === 'y' ? other.y < car.y : other.x < car.x);

          if (isAhead && dist < frontDist) frontDist = dist;
        }

        // Should stop for red/yellow?
        let shouldStop = false;
        if (isApproaching) {
          if (car.axis === 'y' && !nsGreen) shouldStop = true;
          if (car.axis === 'x' && !ewGreen) shouldStop = true;
        }

        let targetSpeed = car.maxSpeed;
        if (frontDist < 38) {
          targetSpeed = 0;
        } else if (frontDist < 60) {
          targetSpeed = car.maxSpeed * 0.3;
        } else if (shouldStop && distToCenter < STOP_DIST + 50 && distToCenter > STOP_DIST - 10) {
          targetSpeed = 0;
        }

        // Smooth acceleration / deceleration
        const accel = 0.0004 * dt * speed;
        const decel = 0.0008 * dt * speed;
        if (car.speed < targetSpeed) car.speed = Math.min(targetSpeed, car.speed + accel);
        if (car.speed > targetSpeed) car.speed = Math.max(targetSpeed, car.speed - decel);
        if (car.speed < 0.001) car.speed = 0;

        car.waiting = car.speed < 0.005;

        // Move
        const move = car.speed * car.dir * dt * speed;
        if (car.axis === 'y') car.y += move;
        if (car.axis === 'x') car.x += move;
      }

      // Remove out-of-bounds cars
      carsRef.current = cars.filter(c =>
        c.x > -80 && c.x < W + 80 && c.y > -80 && c.y < H + 80
      );
    };

    // ─── Main Render Loop ──────────────────────────────────────

    const loop = (time: number) => {
      const dt = Math.min(time - lastTime, 50); // Cap delta
      lastTime = time;
      const p = propsRef.current;

      updateCars(dt);

      drawBackground(p.nightMode);
      drawRoads();
      drawHeatmap(p.density, p.heatmapEnabled);
      drawSignalLights(p.activePhase);

      // Draw cars
      carsRef.current.forEach(car => drawCar(car, p.nightMode, p.aiMode));

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);

    return () => cancelAnimationFrame(animId);
  }, []); // Single mount — reads from propsRef

  return (
    <div className="relative w-full aspect-square rounded-xl overflow-hidden glass-panel" id="simulation-canvas">
      <canvas
        ref={canvasRef}
        className="w-full h-full object-contain"
      />
      {/* HUD Overlay */}
      <div className="absolute top-4 left-4 flex gap-2 z-10">
        {aiMode && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card px-3 py-1.5 rounded-full flex items-center gap-2 border-primary/30"
          >
            <div className="w-2 h-2 bg-primary rounded-full" style={{ boxShadow: '0 0 8px #00f0ff', animation: 'pulse 2s infinite' }} />
            <span className="text-[10px] font-mono text-primary uppercase tracking-wider">NSGA-II Active</span>
          </motion.div>
        )}
        <div className="glass-card px-3 py-1.5 rounded-full">
          <span className="text-[10px] font-mono text-zinc-400">
            Actors: {carsRef.current.length}
          </span>
        </div>
      </div>

      {/* Phase indicator */}
      <div className="absolute bottom-4 left-4 right-4 flex justify-between items-center z-10">
        <div className="glass-card px-3 py-1.5 rounded-full">
          <span className="text-[10px] font-mono text-zinc-500">
            Phase: <span className={activePhase === 0 || activePhase === 2 ? 'text-primary' : activePhase === 1 || activePhase === 3 ? 'text-semantic-warning' : 'text-semantic-danger'}>
              {['NS-GREEN', 'NS-YELLOW', 'EW-GREEN', 'EW-YELLOW'][activePhase]}
            </span>
          </span>
        </div>
        {nightMode && (
          <div className="glass-card px-3 py-1.5 rounded-full">
            <span className="text-[10px] font-mono text-zinc-500">🌙 Night</span>
          </div>
        )}
      </div>
    </div>
  );
}

const SimulationEngine = memo(SimulationEngineInner);
export default SimulationEngine;
