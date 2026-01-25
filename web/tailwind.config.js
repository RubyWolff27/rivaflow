/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Kinetic Teal - RivaFlow Brand Accent
        kinetic: {
          DEFAULT: '#00F5D4',
          50: '#CCFFF7',
          100: '#B3FFF3',
          200: '#80FFEB',
          300: '#4DFFE3',
          400: '#1AFFDB',
          500: '#00F5D4',  // Primary Kinetic Teal
          600: '#00C2A8',
          700: '#008F7C',
          800: '#005C50',
          900: '#002924',
        },
        // Primary remains for backward compatibility, maps to Kinetic Teal
        primary: {
          50: '#CCFFF7',
          100: '#B3FFF3',
          200: '#80FFEB',
          300: '#4DFFE3',
          400: '#1AFFDB',
          500: '#00F5D4',
          600: '#00C2A8',
          700: '#008F7C',
          800: '#005C50',
          900: '#002924',
        },
        // Vault colors for dark mode emphasis
        vault: {
          50: '#F4F7F5',
          100: '#E2E8F0',
          200: '#CBD5E1',
          300: '#94A3B8',
          400: '#64748B',
          500: '#475569',
          600: '#334155',
          700: '#1E293B',
          800: '#1A1E26',
          900: '#0A0C10',
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
