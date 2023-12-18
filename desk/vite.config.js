import path from "path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import frappeui from "frappe-ui/vite";
import Icons from "unplugin-icons/vite";
import Components from "unplugin-vue-components/vite";
import IconsResolver from "unplugin-icons/resolver";
import { FileSystemIconLoader } from "unplugin-icons/loaders";
import { SVG, cleanupSVG, parseColors } from "@iconify/tools";
import LucideIcons from "./lucide";

export default defineConfig({
  plugins: [
    frappeui(),
    vue(),
    Components({
      resolvers: IconsResolver({
        prefix: false,
        enabledCollections: ["lucide"],
      }),
    }),
    Icons({
      compiler: "vue3",
      customCollections: {
        lucide: LucideIcons,
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
    sourcemap: true,
    commonjsOptions: {
      include: [/tailwind.config.js/, /node_modules/],
    },
  },
  optimizeDeps: {
    include: ["feather-icons", "showdown", "tailwind.config.js"],
  },
});
