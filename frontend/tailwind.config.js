/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'obsidian': '#111111',  // Deep background
        'charcoal': '#1a1a1a',  // Card background
        'subtle': '#333333',    // Borders
        'accent': '#10b981',    // Emerald Green
      }
    },
  },
  plugins: [],
}