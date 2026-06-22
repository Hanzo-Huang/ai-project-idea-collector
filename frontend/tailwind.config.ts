import type { Config } from "tailwindcss";
export default { darkMode: "class", content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"], theme: { extend: { colors: { ink: "#0b1020", panel: "#11182d", brand: { 400: "#8b7cff", 500: "#7263f3", 600: "#5e4ee2" } }, boxShadow: { glow: "0 0 30px rgba(114,99,243,.18)" } } }, plugins: [] } satisfies Config;

