import { Extension } from "@tiptap/core";

// Tiptap drops any attribute its schema does not declare.
export const ComponentUtils: Extension = Extension.create({
  name: "ComponentUtils",
  addGlobalAttributes() {
    return [
      {
        types: ["video"],
        attributes: {
          controls: {
            default: true,
            parseHTML: (element) => element.getAttribute("controls"),
            renderHTML: () => {
              return { controls: true };
            },
          },
        },
      },
      {
        types: ["image"],
        attributes: {
          height: {
            default: null,
            parseHTML: (element) => element.getAttribute("height"),
            renderHTML: (attributes) => {
              if (!attributes.height) return {};
              return { height: attributes.height };
            },
          },
          width: {
            default: null,
            parseHTML: (element) => element.getAttribute("width"),
            renderHTML: (attributes) => {
              if (!attributes.width) return {};
              return { width: attributes.width };
            },
          },
        },
      },
      {
        types: ["heading"],
        attributes: {
          id: {
            default: null,
            parseHTML: (element) => element.getAttribute("id"),
            renderHTML: (attributes) => {
              if (!attributes.id) {
                return {};
              }
              return { id: attributes.id };
            },
          },
        },
      },
      {
        types: ["paragraph"],
        attributes: {
          class: {
            default: null,
            parseHTML: (element) => element.getAttribute("class"),
            renderHTML: (attributes) => {
              if (!attributes.class) return {};
              return { class: attributes.class };
            },
          },
        },
      },
      {
        types: ["table"],
        attributes: {
          style: {
            default: null,
            parseHTML: (el) => el.getAttribute("style"),
            renderHTML: () => ({
              style:
                "border-collapse: collapse; width: 100%; border: 1px solid var(--outline-gray-2, #d1d5db);",
            }),
          },
        },
      },

      {
        types: ["tableRow"],
        attributes: {
          style: {
            default: null,
            parseHTML: (el) => el.getAttribute("style"),
            renderHTML: () => ({
              style: "border: 1px solid var(--outline-gray-2, #d1d5db);",
            }),
          },
        },
      },

      {
        types: ["tableCell", "tableHeader"],
        attributes: {
          style: {
            default: null,
            parseHTML: (el) => el.getAttribute("style"),
            renderHTML: () => ({
              style:
                "border: 1px solid var(--outline-gray-2, #d1d5db); padding: 6px 8px; vertical-align: top; text-align: left;",
            }),
          },
        },
      },
    ];
  },
});
