/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        aws: {
          navy: '#232F3E',
          'navy-deep': '#1A1A2E',
          orange: '#FF9900',
          'orange-hover': '#EC7211',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      fontSize: {
        'code': '13px',
        'meta': '12px',
      },
    },
  },
  plugins: [],
}
