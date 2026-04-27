import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        appBg: "#F7F8FC",
        card: "#FFFFFF",
        cardSoft: "#F9FAFB",
        primary: "#4F7CFF",
        accent: "#FF6A1A",
        up: "#EF4444",
        down: "#2563EB",
        safe: "#22C55E",
        warning: "#F59E0B",
        danger: "#EF4444",
        text: "#111827",
        subText: "#6B7280",
        border: "#E5E7EB"
      },
      boxShadow: {
        soft: "0 12px 32px rgba(17, 24, 39, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
