import path from "path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import Icons from "unplugin-icons/vite";
import { FileSystemIconLoader } from "unplugin-icons/loaders";
import { SVG, cleanupSVG, parseColors } from "@iconify/tools";
import frappeui from "frappe-ui/vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    frappeui(),
    vue(),
    Icons({
      compiler: "vue3",
      customCollections: {
        espresso: FileSystemIconLoader("./src/assets/icons", async (svg) => {
          const r = new SVG(svg);

          await cleanupSVG(r);
          await parseColors(r, {
            callback: () => "currentColor",
          });

          return r.toMinifiedString();
        }),
        logos: FileSystemIconLoader("./src/assets/logos", async (svg) => {
          const r = new SVG(svg);
          await cleanupSVG(r);
          return r.toMinifiedString();
        }),
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "tailwind.config.js": path.resolve(__dirname, "tailwind.config.js"),
    },
  },
  build: {
    outDir: `../helpdesk/public/desk`,
    emptyOutDir: true,
    target: "es2021",
    commonjsOptions: {
      include: [/tailwind.config.js/, /node_modules/],
    },
  },
  optimizeDeps: {
    include: ["feather-icons", "showdown", "tailwind.config.js"],
  },
});
