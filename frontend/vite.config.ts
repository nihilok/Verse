import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";
import path from "node:path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const env = loadEnv(mode, process.cwd(), "");

  // Parse allowedHosts from env (can be comma-separated string)
  const allowedHosts = env.ALLOWED_HOSTS
    ? env.ALLOWED_HOSTS.split(",").map((host: string) => host.trim())
    : undefined;

  return {
    plugins: [
      react(),
      tailwindcss(),
      VitePWA({
        registerType: "prompt",
        includeAssets: ["vite.svg", "icons/*.png"],
        manifest: {
          name: "Verse - Interactive Bible Reader",
          short_name: "Verse",
          description:
            "An interactive Bible reader with AI-powered insights. Highlight any passage to explore its historical context, theological significance, and practical application.",
          theme_color: "#4f46e5",
          background_color: "#ffffff",
          display: "standalone",
          start_url: "/",
          icons: [
            {
              src: "/icons/icon-192x192.png",
              sizes: "192x192",
              type: "image/svg+xml",
              purpose: "any",
            },
            {
              src: "/icons/icon-512x512.png",
              sizes: "512x512",
              type: "image/svg+xml",
              purpose: "any",
            },
            {
              src: "/icons/icon-maskable-192x192.png",
              sizes: "192x192",
              type: "image/svg+xml",
              purpose: "maskable",
            },
            {
              src: "/icons/icon-maskable-512x512.png",
              sizes: "512x512",
              type: "image/svg+xml",
              purpose: "maskable",
            },
          ],
        },
        workbox: {
          globPatterns: ["**/*.{js,css,html,ico,png,svg,woff,woff2}"],
          skipWaiting: false,
          clientsClaim: false,
          runtimeCaching: [
            {
              urlPattern: /^https:\/\/api\.*/i,
              handler: "NetworkFirst",
              options: {
                cacheName: "api-cache",
                expiration: {
                  maxEntries: 100,
                  maxAgeSeconds: 60 * 60 * 24, // 24 hours
                },
                cacheableResponse: {
                  statuses: [0, 200],
                },
              },
            },
          ],
        },
        devOptions: {
          enabled: false, // Disable in development for easier debugging
        },
      }),
    ],
    resolve: {
      alias: {
        "@": path.resolve(new URL("./src", import.meta.url).pathname),
      },
    },
    server: {
      host: true,
      port: 5173,
      proxy: {
        "/api": {
          target: "http://backend:8000",
          changeOrigin: true,
        },
      },
      // Add allowedHosts if defined in environment
      ...(allowedHosts && { allowedHosts }),
    },
    test: {
      environment: "jsdom",
      globals: true,
    },
  };
});
