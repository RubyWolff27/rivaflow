/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary maps to Combat Red (matches --accent)
        primary: {
          50: '#FFF0ED',
          100: '#FFE1DB',
          200: '#FFC3B7',
          300: '#FFA593',
          400: '#FF7960',
          500: '#FF4D2D',  // Matches --accent
          600: '#E63F24',
          700: '#B3301C',
          800: '#802214',
          900: '#4D140C',
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
  darkMode: ['selector', '[data-theme="dark"]'],
}
