/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#050505",
        surface: "#0a0a0c",
        surface2: "#121214",
        border: "#27272a",
        primary: {
          DEFAULT: "#00f0ff", // Neon Cyan
          hover: "#00c8d4",
          glow: "rgba(0, 240, 255, 0.4)",
        },
        accent: {
          magenta: "#ff00ff",
          lime: "#39ff14",
        },
        semantic: {
          safe: "#39ff14",     // Green
          warning: "#ffea00",  // Yellow
          danger: "#ff1414",   // Red
        }
      },
      fontFamily: {
        sans: ['Inter', 'Satoshi', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      transitionTimingFunction: {
        'in-out-circ': 'cubic-bezier(0.785, 0.135, 0.15, 0.86)',
        'out-expo': 'cubic-bezier(0.19, 1, 0.22, 1)',
      },
      animation: {
        "float": "float 8s ease-in-out infinite",
        "pulse-glow": "pulse-glow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "shimmer": "shimmer 2.5s linear infinite",
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0) scale(1)' },
          '50%': { transform: 'translateY(-15px) scale(1.02)' },
        },
        "pulse-glow": {
          '0%, 100%': { opacity: '0.4', filter: 'blur(10px)' },
          '50%': { opacity: '0.8', filter: 'blur(20px)' },
        },
        shimmer: {
          from: { backgroundPosition: "0 0" },
          to: { backgroundPosition: "-200% 0" },
        }
      }
    },
  },
  plugins: [],
}
