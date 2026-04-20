/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#10E580',
          hover: '#0CBA68',
          soft: 'rgba(16, 229, 128, 0.12)',
        },
        dark: {
          base: '#212523',
        },
        surface: {
          DEFAULT: 'rgba(255, 255, 255, 0.08)',
          hover: 'rgba(255, 255, 255, 0.12)',
        },
        txt: {
          primary: '#FFFFFF',
          secondary: '#D1D6D3',
        },
        brd: {
          light: 'rgba(255, 255, 255, 0.15)',
        },
      },
      fontFamily: {
        sans: ['"Inter"', '"Helvetica Neue"', 'sans-serif'],
      },
      borderRadius: {
        pill: '9999px',
      },
    },
  },
  plugins: [],
}
