module.exports = {
	mode: "jit",
	presets: [require("frappe-ui/src/utils/tailwind.config")],
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts,jsx,tsx}",
		"./node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
		"../node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
	],
	theme: {
		extend: {
			zIndex: {
				5: "5",
			},
			fontSize: {
				xs: "12px",
				sm: "13px",
				base: "14px",
				"2xl": "20px",
			},
		},
	},
	plugins: [
		require("@tailwindcss/line-clamp"),
		require("@tailwindcss/typography"),
	],
};
