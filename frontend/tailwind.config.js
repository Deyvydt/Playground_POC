/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        ink: {
          950: "#0A0A0B",
          900: "#141416",
          800: "#1F1F23",
          700: "#2C2C31",
          600: "#3F3F46",
        },
        mist: {
          50: "#FAFAFA",
          100: "#F4F4F5",
          200: "#E4E4E7",
          300: "#D4D4D8",
          400: "#A1A1AA",
          500: "#71717A",
        },
        tcs: {
          DEFAULT: "#5F68C3",
          light: "#8288D6",
          dark: "#454DA0",
          50: "#F1F2FB",
          100: "#E4E6F7",
        },
      },
      boxShadow: {
        soft: "0 1px 2px rgba(10,10,11,0.04), 0 4px 16px rgba(10,10,11,0.06)",
        card: "0 1px 3px rgba(10,10,11,0.06), 0 8px 24px -8px rgba(10,10,11,0.10)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: 0, transform: "translateY(6px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: 0.4 },
          "50%": { opacity: 1 },
        },
      },
      animation: {
        fadeUp: "fadeUp .35s ease-out both",
        pulseSoft: "pulseSoft 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
