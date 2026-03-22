/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: {
    extend: {
      colors: {
        apple: {
          text: "#1d1d1f",
          secondary: "#86868b",
          tertiary: "#a1a1a6",
          bg: "#f5f5f7",
          blue: "#0071e3",
          bluehover: "#0077ED",
          green: "#28c840",
        },
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.8s ease-out forwards",
        "fade-up-d1": "fade-up 0.8s ease-out 0.15s forwards",
        "fade-up-d2": "fade-up 0.8s ease-out 0.3s forwards",
        "fade-up-d3": "fade-up 0.8s ease-out 0.45s forwards",
      },
    },
  },
  plugins: [],
};
