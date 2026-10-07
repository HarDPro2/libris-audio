import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";
import { VitePWA } from "vite-plugin-pwa";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  base: '/',

  server: {
    host: "::",
    port: 8080,
    hmr: {
      overlay: false,
    },
  },
  plugins: [
    react(),
    mode === 'development' && componentTagger(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      devOptions: { enabled: true }, // Ensure PWA works in dev mode for testing
      manifest: {
        name: 'LibrisAudio',
        short_name: 'Libris',
        description: 'Lector inteligente de audiolibros offline',
        theme_color: '#ffffff',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: '/pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        // La entrada de la SPA pasa a ser app.html: sin esto el service worker
        // seguiria devolviendo /index.html, que ya no se genera.
        navigateFallback: '/app.html',
        // Y la raiz no cae al fallback: ahi vive la landing, que es un fichero
        // propio y la sirve el servidor.
        navigateFallbackDenylist: [/^\/$/, /^\/landing\.html$/],
        // La landing fuera del precache: son 846 KB de pagina de marketing que
        // se tragaba quien abre la APLICACION y no la va a ver. El fichero
        // sigue estando en el servidor; lo que deja de hacer el service worker
        // es guardarselo.
        globIgnores: ['**/landing.html'],
        runtimeCaching: [
          {
            urlPattern: /^http:\/\/localhost:8000\/api\/audio\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'audio-cache',
              expiration: { maxEntries: 500, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200, 206] } // Accept opaque responses
            }
          },
          {
            urlPattern: /^http:\/\/localhost:8000\/static\/books\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200] }
            }
          }
        ]
      }
    })
  ].filter(Boolean),
  build: {
    rollupOptions: {
      // La entrada de la SPA ya no se llama index.html, y Vite no la busca
      // sola: la entrada por defecto esta fijada a ese nombre. Al declararla
      // aqui, la salida se llama igual que la entrada —dist/app.html— y la
      // raiz queda libre para la landing.
      input: path.resolve(__dirname, "app.html"),
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
