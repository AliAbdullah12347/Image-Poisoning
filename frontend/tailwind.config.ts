import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0a', // Deep Void
        foreground: '#ededed',
        primary: {
          DEFAULT: '#ffff00', // Cyber Yellow
          hover: '#e6e600',
        },
        secondary: {
          DEFAULT: '#3b82f6', // Electric Blue
          hover: '#2563eb',
        },
        surface: {
          DEFAULT: 'rgba(23, 23, 23, 0.7)',
          hover: 'rgba(38, 38, 38, 0.7)',
        },
        accent: '#22c55e', // Success Green
      },
      animation: {
        'spin-slow': 'spin 3s linear infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        glow: {
          'from': { boxShadow: '0 0 10px rgba(255, 255, 0, 0.1)' },
          'to': { boxShadow: '0 0 20px rgba(255, 255, 0, 0.3)' },
        }
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(to right, #1f1f1f 1px, transparent 1px), linear-gradient(to bottom, #1f1f1f 1px, transparent 1px)",
      }
    },
  },
  plugins: [],
}
export default config
