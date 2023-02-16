module.exports = {
	env: {
		browser: true,
		es2021: true,
		node: true,
	},
	extends: [
		"eslint:recommended",
		"plugin:json/recommended",
		"plugin:vue/vue3-recommended",
		"plugin:tailwindcss/recommended",
		"prettier",
	],
	parserOptions: {
		ecmaVersion: "latest",
		sourceType: "module",
	},
};
