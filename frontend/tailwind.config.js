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
        'surface-ground': '#111318',
        'surface-card': '#181B22',
        'surface-elevated': '#222630',
        'surface-border': '#2D323E',
        'text-primary': '#F1EFEA',
        'text-secondary': '#9DA3B4',
        'text-tertiary': '#636B7E',
        'accent-magenta': '#D62978',
        'accent-lime': '#B9D66C',
        'status-negative': '#E05D52',
        'status-warning': '#E5A83B',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Manrope', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'DEFAULT': '4px',
        'md': '6px',
        'lg': '8px',
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.35)',
        'elevated': '0 4px 12px 0 rgba(0, 0, 0, 0.45)',
      }
    },
  },
  plugins: [],
}
