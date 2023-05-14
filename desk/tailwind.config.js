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
			fontSize: {
				xs: "12px",
				sm: "13px",
				base: "14px",
				lg: "16px",
				xl: "18px",
				"2xl": "20px",
			},
			height: {
				18: "68px",
			},
			margin: {
				3.5: "14px",
			},
			padding: {
				2.5: "10px",
				3.5: "14px",
			},
			zIndex: {
				5: "5",
			},
		},
	},
	plugins: [
		require("@tailwindcss/line-clamp"),
		require("@tailwindcss/typography"),
	],
};
