import vue from "@vitejs/plugin-vue";
import vueJsx from "@vitejs/plugin-vue-jsx";
import frappeui from "frappe-ui/vite";
import path from "path";
import IconsResolver from "unplugin-icons/resolver";
import Components from "unplugin-vue-components/vite";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      buildConfig: {
        outDir: `../helpdesk/public/desk`,
        emptyOutDir: true,
        indexHtmlPath: "../helpdesk/www/helpdesk/index.html",
      },
      frappeTypes: {
        input: {
          helpdesk: ["hd_ticket_status", "hd_ticket"],
        },
      },
    }),

    vue(),
    vueJsx(),
    Components({
      resolvers: IconsResolver({
        prefix: false,
        enabledCollections: ["lucide"],
      }),
    }),
    VitePWA({
      registerType: "autoUpdate",
      devOptions: {
        enabled: true,
      },
      workbox: {
        cleanupOutdatedCaches: true,
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
      },
      manifest: {
        display: "standalone",
        name: "Frappe Helpdesk",
        short_name: "Helpdesk",
        start_url: "/helpdesk",
        description:
          "Modern, Streamlined, Free and Open Source Customer Service Software",
        icons: [
          {
            src: "/assets/helpdesk/desk/manifest/manifest-icon-192.maskable.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "/assets/helpdesk/desk/manifest/manifest-icon-192.maskable.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "maskable",
          },
          {
            src: "/assets/helpdesk/desk/manifest/manifest-icon-512.maskable.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "/assets/helpdesk/desk/manifest/manifest-icon-512.maskable.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "tailwind.config.js": path.resolve(__dirname, "tailwind.config.js"),
    },
  },
  optimizeDeps: {
    include: [
      "feather-icons",
      "tailwind.config.js",
      "prosemirror-state",
      "prosemirror-view",
      "lowlight",
    ],
  },
});
