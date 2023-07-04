import resolveConfig from "tailwindcss/resolveConfig";
import tailwindConfig from "tailwind.config.js";

const config = resolveConfig(tailwindConfig);
const accent = "cyan";
const range = [600, 500, 400, 300, 200];
const color = range.map((n) => config.theme.colors[accent][n]);

export const theme = {
  color,
};
