/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // The warm backgrounds
        parchment: '#f5f4ed',
        ivory: '#faf9f5',
        'warm-sand': '#e8e6dc',

        // The dark surfaces & text
        'near-black': '#141413',
        'dark-surface': '#30302e',
        'charcoal-warm': '#4d4c48',
        'olive-gray': '#5e5d59',
        'stone-gray': '#87867f',
        'warm-silver': '#b0aea5',

        // Brand accents
        'brand-terracotta': '#c96442',

        // Borders
        'border-cream': '#f0eee6',
        'border-warm': '#e8e6dc',
      },
      boxShadow: {
        // Our custom "Ring Shadows" instead of drop shadows
        'ring-warm': '0px 0px 0px 1px #d1cfc5',
        'ring-brand': '0px 0px 0px 1px #c96442',
        'ring-dark': '0px 0px 0px 1px #30302e',
        'whisper': '0px 4px 24px rgba(0, 0, 0, 0.05)',
      },
      fontFamily: {
        // Using Georgia as the fallback for Anthropic Serif
        serif: ['Georgia', 'serif'],
        sans: ['system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}