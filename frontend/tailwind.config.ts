import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        border: '#000000',
        accent: '#00E0FF', // Updated for new design, was '#000000'
        // New colors from reference
        bg: '#FFFDF5',
        primary: '#FFD600',
        secondary: '#FF90E8',
        ink: '#000000',
        success: '#22C55E',
        danger: '#EF4444',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'], // Updated
        sans: ['"Noto Sans SC"', 'sans-serif'], // Added
        display: ['"Space Grotesk"', 'sans-serif'], // Added
        glass: ['"Inter"', 'sans-serif'], // Added
        glassHeader: ['"Outfit"', 'sans-serif'], // Added
      },
      // Added new extensions
      boxShadow: {
        'hard': '4px 4px 0px 0px #000000',
        'hard-sm': '2px 2px 0px 0px #000000',
        'hard-lg': '8px 8px 0px 0px #000000',
        'reverse': '-4px 4px 0px 0px #000000',
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
        'glass-sm': '0 4px 16px 0 rgba(31, 38, 135, 0.1)',
      },
      animation: {
        ticker: 'ticker 30s linear infinite',
        bounce: 'bounce 2s infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        ticker: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-100%)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      }
    },
  },
  plugins: [],
}

export default config
