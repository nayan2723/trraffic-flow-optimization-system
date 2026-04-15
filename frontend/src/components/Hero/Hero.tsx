import { useEffect, useRef, useCallback } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

// ─── Animated Network Background (Canvas) ────────────────────────
function NetworkCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let w = (canvas.width = window.innerWidth);
    let h = (canvas.height = window.innerHeight);
    let animId: number;

    // Nodes representing traffic network intersections
    const nodes = Array.from({ length: 60 }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      size: Math.random() * 2.5 + 1,
      pulse: Math.random() * Math.PI * 2,
    }));

    // Data packets flowing between nodes
    const packets: { x: number; y: number; tx: number; ty: number; progress: number; speed: number }[] = [];

    const render = (time: number) => {
      ctx.clearRect(0, 0, w, h);

      // Update nodes
      nodes.forEach(n => {
        n.x += n.vx;
        n.y += n.vy;
        n.pulse += 0.02;
        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;
      });

      // Connections
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const d = Math.hypot(nodes[i].x - nodes[j].x, nodes[i].y - nodes[j].y);
          if (d < 150) {
            const alpha = (1 - d / 150) * 0.12;
            ctx.strokeStyle = `rgba(0, 240, 255, ${alpha})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }

      // Spawn packets occasionally
      if (Math.random() < 0.03 && packets.length < 15) {
        const src = nodes[Math.floor(Math.random() * nodes.length)];
        const tgt = nodes[Math.floor(Math.random() * nodes.length)];
        packets.push({
          x: src.x, y: src.y,
          tx: tgt.x, ty: tgt.y,
          progress: 0,
          speed: 0.005 + Math.random() * 0.01,
        });
      }

      // Update and draw packets
      for (let i = packets.length - 1; i >= 0; i--) {
        const p = packets[i];
        p.progress += p.speed;
        if (p.progress >= 1) {
          packets.splice(i, 1);
          continue;
        }
        const px = p.x + (p.tx - p.x) * p.progress;
        const py = p.y + (p.ty - p.y) * p.progress;
        const alpha = Math.sin(p.progress * Math.PI) * 0.8;
        ctx.fillStyle = `rgba(0, 240, 255, ${alpha})`;
        ctx.shadowBlur = 6;
        ctx.shadowColor = 'rgba(0, 240, 255, 0.5)';
        ctx.beginPath();
        ctx.arc(px, py, 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      // Draw nodes
      nodes.forEach(n => {
        const pulseAlpha = 0.3 + Math.sin(n.pulse) * 0.2;
        ctx.fillStyle = `rgba(0, 240, 255, ${pulseAlpha})`;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.size, 0, Math.PI * 2);
        ctx.fill();
      });

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);

    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', resize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 z-0 opacity-50" />;
}

// ─── Stats Counter ───────────────────────────────────────────────
function StatBadge({ value, label, delay }: { value: string; label: string; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay, ease: [0.19, 1, 0.22, 1] }}
      className="text-center"
    >
      <div className="text-2xl md:text-3xl font-bold text-white font-mono">{value}</div>
      <div className="text-[10px] text-zinc-500 uppercase tracking-[0.15em] mt-1">{label}</div>
    </motion.div>
  );
}

// ─── Hero Component ──────────────────────────────────────────────
export default function Hero({ onCTA }: { onCTA: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end start'],
  });

  const y1 = useTransform(scrollYProgress, [0, 1], [0, 250]);
  const opacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.95]);

  return (
    <div
      ref={containerRef}
      className="relative h-screen flex items-center justify-center overflow-hidden bg-background"
    >
      {/* Network Background */}
      <NetworkCanvas />

      {/* Glow Orbs */}
      <div className="absolute top-1/4 -left-32 w-[500px] h-[500px] bg-primary/15 rounded-full blur-[150px] mix-blend-screen animate-float" />
      <div className="absolute bottom-1/4 -right-32 w-[600px] h-[600px] bg-accent-magenta/8 rounded-full blur-[180px] mix-blend-screen" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[200px]" />

      {/* Content */}
      <motion.div
        style={{ y: y1, opacity, scale }}
        className="relative z-10 flex flex-col items-center text-center max-w-6xl px-6"
      >
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: [0.19, 1, 0.22, 1] }}
          className="inline-flex items-center gap-2 px-5 py-2 rounded-full glass-card border-primary/20 text-primary mb-10 font-mono text-[11px] uppercase tracking-[0.2em]"
        >
          <span className="w-2 h-2 rounded-full bg-primary" style={{ boxShadow: '0 0 8px #00f0ff' }} />
          Multi-Objective Evolutionary Optimization
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, delay: 0.15, ease: [0.19, 1, 0.22, 1] }}
          className="text-[clamp(3rem,8vw,7rem)] font-sans font-black tracking-[-0.04em] text-white leading-[0.92] mb-8"
        >
          Urban{' '}
          <span className="gradient-text">Intelligence</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.35, ease: 'easeOut' }}
          className="text-lg md:text-xl text-zinc-400 max-w-2xl font-light leading-relaxed mb-14"
        >
          Dynamic traffic orchestration powered by NSGA-II. Minimizing wait times,
          reducing emissions, and mapping Pareto efficiency across four dimensions — in real-time.
        </motion.p>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.55 }}
          className="flex gap-4 items-center"
        >
          <button onClick={onCTA} className="btn-primary group" id="hero-cta">
            <div className="absolute inset-0 bg-white translate-y-[100%] group-hover:translate-y-0 transition-transform duration-300 ease-[cubic-bezier(0.19,1,0.22,1)]" />
            <span className="relative z-10 group-hover:text-background transition-colors duration-300 flex items-center gap-3">
              Initialize Engine
              <svg className="w-5 h-5 -rotate-45 group-hover:rotate-0 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </span>
          </button>
          
          <a href="https://github.com/nayan2723/trraffic-flow-optimization-system" 
             target="_blank" rel="noopener noreferrer"
             className="btn-ghost flex items-center gap-2" id="hero-github">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            Source
          </a>
        </motion.div>

        {/* Stats Bar */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 1 }}
          className="mt-20 flex gap-12 md:gap-16"
        >
          <StatBadge value="3" label="Objectives" delay={1.1} />
          <StatBadge value="4" label="Decision Vars" delay={1.2} />
          <StatBadge value="80" label="Population" delay={1.3} />
          <StatBadge value="60" label="Generations" delay={1.4} />
        </motion.div>
      </motion.div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
      >
        <span className="text-[10px] text-zinc-600 uppercase tracking-[0.2em] font-mono">Scroll</span>
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className="w-5 h-8 rounded-full border border-zinc-700 flex justify-center pt-1.5"
        >
          <div className="w-1 h-1.5 bg-zinc-500 rounded-full" />
        </motion.div>
      </motion.div>
    </div>
  );
}
