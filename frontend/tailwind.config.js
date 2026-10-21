/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Geist Variable", "Geist", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["Geist Mono Variable", "Geist Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        serif: ["Instrument Serif", "ui-serif", "Georgia", "serif"],
      },
      colors: {
        ink: {
          950: "#141413",
          900: "#1C1B19",
          800: "#2A2926",
          700: "#3A3935",
          600: "#5A5852",
        },
        mist: {
          50: "#FAF9F7",
          100: "#F4F3EF",
          200: "#E9E7E1",
          300: "#D9D6CD",
          400: "#A3A097",
          500: "#75726A",
        },
        accent: {
          DEFAULT: "#E3622E",
          light: "#F28A5C",
          dark: "#B94A1C",
          50: "#FEF4EE",
          100: "#FCE4D6",
        },
      },
      boxShadow: {
        soft: "0 1px 2px rgba(20,20,19,0.04), 0 2px 8px rgba(20,20,19,0.04)",
        card: "0 1px 2px rgba(20,20,19,0.05), 0 12px 32px -12px rgba(20,20,19,0.14)",
        pop: "0 2px 4px rgba(20,20,19,0.06), 0 24px 48px -16px rgba(20,20,19,0.28)",
        glow: "0 0 0 4px rgba(227,98,46,0.14)",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: 0, transform: "translateY(6px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: 0.35 },
          "50%": { opacity: 1 },
        },
        shake: {
          "0%, 100%": { transform: "translateX(0)" },
          "20%, 60%": { transform: "translateX(-6px)" },
          "40%, 80%": { transform: "translateX(6px)" },
        },
      },
      animation: {
        fadeUp: "fadeUp .35s ease-out both",
        pulseSoft: "pulseSoft 1.4s ease-in-out infinite",
        shake: "shake .4s ease-in-out",
      },
    },
  },
  plugins: [],
};
