/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0F19',
        surface: '#151C2C',
        surfaceHighlight: '#1A233A',
        primary: '#4F46E5',
        primaryHover: '#4338CA',
        textMain: '#F8FAFC',
        textMuted: '#94A3B8',
        borderMain: '#1E293B',
      }
    },
  },
  plugins: [],
}
