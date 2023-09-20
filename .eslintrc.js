module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:json/recommended",
    "plugin:vue/vue3-recommended",
    "plugin:tailwindcss/recommended",
    "plugin:prettier/recommended",
  ],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    parser: "@typescript-eslint/parser",
  },
  rules: {
    "tailwindcss/no-custom-classname": "off",
    "vue/multi-word-component-names": "off",
  },
};
