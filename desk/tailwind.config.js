import frappeUIPreset, { content as frappeUIContent } from "frappe-ui/tailwind";

export default {
  presets: [frappeUIPreset],
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    ...frappeUIContent,
    // frappe-ui's own content list leaves experimental/ListView out; helpdesk
    // still renders it, so its classes have to be scanned here.
    "./node_modules/frappe-ui/experimental/ListView/**/*.{vue,js,ts,jsx,tsx}",
    "../../frappe/ui/src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  plugins: [
    require("@tailwindcss/typography"),
    require("tailwindcss-rtl"),
    function ({ addUtilities }) {
      addUtilities({
        ".hide-scrollbar": {
          "scrollbar-width": "none",
          "-ms-overflow-style": "none",
          "&::-webkit-scrollbar": {
            display: "none",
          },
        },
      });
    },
  ],
};
