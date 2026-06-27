import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "bg-0": "var(--bg-0)",
        "bg-1": "var(--bg-1)",
        "bg-2": "var(--bg-2)",
        "bg-3": "var(--bg-3)",
        stroke: "var(--stroke)",
        "stroke-strong": "var(--stroke-strong)",
        "fg-0": "var(--fg-0)",
        "fg-1": "var(--fg-1)",
        "fg-2": "var(--fg-2)",
        accent: "var(--accent)",
        "accent-hover": "var(--accent-hover)",
        "accent-soft": "var(--accent-soft)",
        ok: "var(--ok)",
        warn: "var(--warn)",
        err: "var(--err)",
        info: "var(--info)",
      },
      borderRadius: {
        sm: "var(--r-sm)",
        md: "var(--r-md)",
        card: "var(--r-card)",
        lg: "var(--r-lg)",
        pill: "var(--r-pill)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        "shadow-1": "var(--shadow-1)",
        "shadow-2": "var(--shadow-2)",
        glow: "var(--shadow-glow)",
      },
      keyframes: {
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
        "halo-pulse": {
          "0%, 100%": { transform: "scale(1)", opacity: "0.6" },
          "50%": { transform: "scale(1.04)", opacity: "0.9" },
        },
      },
      animation: {
        pulse: "pulse 2s ease-in-out infinite",
        shimmer: "shimmer 2s linear infinite",
        blink: "blink 1s steps(2) infinite",
        "halo-pulse": "halo-pulse 2.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
