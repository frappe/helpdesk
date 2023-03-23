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
			boxShadow: {
				around: "0px 0px 20px 5px #e2e8f0",
			},
			font: {
				sans: ["Inter", "sans-serif"],
			},
			zIndex: {
				"5": "5",
			},
			width: {
				"1/24": "4.1666666667%",
				"2/24": "8.3333333333%",
				"3/24": "12.5%",
				"4/24": "16.6666666667%",
				"5/24": "20.8333333333%",
				"6/24": "25%",
				"7/24": "29.1666666667%",
				"8/24": "33.3333333333%",
				"9/24": "37.5%",
				"10/24": "41.6666666667%",
				"11/24": "45.8333333333%",
				"12/24": "50%",
				"13/24": "54.1666666667%",
				"14/24": "58.3333333333%",
				"15/24": "62.5%",
				"16/24": "66.6666666667%",
				"17/24": "70.8333333333%",
				"18/24": "75%",
				"19/24": "79.1666666667%",
				"20/24": "83.3333333333%",
				"21/24": "87.5%",
				"22/24": "91.6666666667%",
				"23/24": "95.8333333333%",
			},
		},
	},
	plugins: [require("@tailwindcss/line-clamp")],
}
