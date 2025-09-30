import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        surface: "var(--surface)",
        surfaceMuted: "var(--surface-muted)",
        border: "var(--border)",
        muted: "var(--muted)",
        positive: "#22c55e",
        negative: "#ef4444",
      },
    },
  },
  plugins: [],
};

export default config;
