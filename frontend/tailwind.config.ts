import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Financial dashboard dark theme
        surface: {
          DEFAULT: "#0a0e17",
          card: "#111827",
          elevated: "#1a1d2e",
          border: "#1f2937",
        },
        financial: {
          green: "#26a69a",
          red: "#ef5350",
          yellow: "#ffa726",
          blue: "#1a73e8",
          text: "#e2e8f0",
          muted: "#7c8db5",
          accent: "#3b82f6",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Menlo", "monospace"],
        sans: ["Inter", "Noto Sans SC", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
