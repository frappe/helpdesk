import resolveConfig from "tailwindcss/resolveConfig";
import tailwindConfig from "tailwind.config.js";

const config = resolveConfig(tailwindConfig);
const ignore = ["slate", "gray", "zinc", "neutral", "stone"];
const color = Object.entries(config.theme.colors)
	.filter((color) => !ignore.includes(color[0]))
	.map((color) => color[1][400])
	.filter((color) => color);

export const theme = {
	color,
};
