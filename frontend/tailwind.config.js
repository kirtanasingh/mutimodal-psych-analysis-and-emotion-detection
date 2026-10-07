export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        slate: {
          950: '#0a0f1a',
        },
        teal: { 600: '#0d9488', 700: '#0f766e' },
        clinical: { anger: '#c2524a', disgust: '#7a9e3f', fear: '#6b5b95', joy: '#d4a24c', neutral: '#8a94a6', sadness: '#5b7fa6', surprise: '#c77dbb' },
      },
    },
  },
  plugins: [],
}