/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0a0d14',
        surface: '#121824',
        'surface-hover': '#1a2333',
        border: '#1f293d',
        'border-light': '#2d3b54',
        primary: {
          DEFAULT: '#00d4ff',
          hover: '#00b8e6',
          light: '#33deff',
          muted: 'rgba(0, 212, 255, 0.15)',
        },
        accent: {
          purple: '#7c3aed',
          pink: '#ec4899',
          green: '#10b981',
          amber: '#f59e0b',
        },
        text: {
          primary: '#f9fafb',
          secondary: '#9ca3af',
          muted: '#6b7280',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 25px rgba(0, 212, 255, 0.25)',
        'glow-purple': '0 0 25px rgba(124, 58, 237, 0.25)',
        glass: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
