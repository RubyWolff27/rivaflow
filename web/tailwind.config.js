/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Combat Red - Primary Brand Color (Performance)
        combat: {
          DEFAULT: '#E63946',
          50: '#FDECEE',
          100: '#FBD9DC',
          200: '#F7B3B9',
          300: '#F38D96',
          400: '#EF6773',
          500: '#E63946',  // Primary Combat Red
          600: '#D11E2C',
          700: '#9E1721',
          800: '#6B0F16',
          900: '#38080B',
        },
        // Energy Orange - Secondary Accent (Achievements)
        energy: {
          DEFAULT: '#FF6B35',
          50: '#FFEDE7',
          100: '#FFDCCF',
          200: '#FFB99F',
          300: '#FF966F',
          400: '#FF733F',
          500: '#FF6B35',  // Primary Energy Orange
          600: '#E6501C',
          700: '#B33D15',
          800: '#80290E',
          900: '#4D1607',
        },
        // Recovery Teal - Tertiary (Readiness/Recovery)
        recovery: {
          DEFAULT: '#00F5D4',
          50: '#CCFFF7',
          100: '#B3FFF3',
          200: '#80FFEB',
          300: '#4DFFE3',
          400: '#1AFFDB',
          500: '#00F5D4',  // Recovery Teal
          600: '#00C2A8',
          700: '#008F7C',
          800: '#005C50',
          900: '#002924',
        },
        // Primary maps to Combat Red (new default)
        primary: {
          50: '#FDECEE',
          100: '#FBD9DC',
          200: '#F7B3B9',
          300: '#F38D96',
          400: '#EF6773',
          500: '#E63946',  // Combat Red
          600: '#D11E2C',
          700: '#9E1721',
          800: '#6B0F16',
          900: '#38080B',
        },
        // Mat Black - Dark mode foundation
        mat: {
          50: '#F4F7F5',
          100: '#E2E8F0',
          200: '#CBD5E1',
          300: '#94A3B8',
          400: '#64748B',
          500: '#475569',
          600: '#334155',
          700: '#1E293B',
          800: '#1A1A1A',  // Elevated Black - cards
          900: '#0A0A0A',  // Mat Black - background
        },
        // Override default grays to use Mat Black colors
        gray: {
          50: '#F4F7F5',   // Light mode surface
          100: '#E2E8F0',
          200: '#CBD5E1',
          300: '#94A3B8',
          400: '#64748B',
          500: '#475569',
          600: '#334155',
          700: '#1E293B',
          800: '#1A1A1A',  // Mat-800 (dark mode card)
          900: '#0A0A0A',  // Mat-900 (dark mode bg)
        },
        // Success - Victory Green
        success: {
          DEFAULT: '#06D6A0',
          50: '#D4FFF3',
          100: '#B3FFE9',
          200: '#80FFD9',
          300: '#4DFFC9',
          400: '#1AFFB9',
          500: '#06D6A0',
          600: '#05A87F',
          700: '#047A5E',
          800: '#034C3D',
          900: '#021E1C',
        },
      },
      borderRadius: {
        'button': '8px',
        'card': '12px',
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}
