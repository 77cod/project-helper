import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          rendering: ["markdown-it", "dompurify"],
        },
      },
    },
  },
  test: {
    environment: "jsdom",
  },
});
