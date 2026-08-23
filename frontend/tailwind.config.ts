import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#071027",
        mist: "#334155",
        ember: "#ff9a3c",
        sky: "#2563eb",
        panel: "#ffffff",
        sand: "#f8fafc",
      },
      fontFamily: {
        sans: ["\"Space Grotesk\"", "sans-serif"],
        mono: ["\"IBM Plex Mono\"", "monospace"],
      },
      boxShadow: {
        glow: "0 24px 80px rgba(15, 23, 42, 0.12)",
      },
      backgroundImage: {
        "mesh-radial":
          "radial-gradient(circle at top left, rgba(37,99,235,0.10), transparent 30%), radial-gradient(circle at top right, rgba(16,185,129,0.12), transparent 28%), linear-gradient(180deg, #f8fbff 0%, #eef5ff 46%, #ffffff 100%)",
      },
    },
  },
  plugins: [],
} satisfies Config;
