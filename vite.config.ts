import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');

  return {
    plugins: [react(), tailwindcss()],
    define: {
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // Allow specific hosts
      allowedHosts: [
        'limelight.karthikeyathota.page',
        'solana.karthikeyathota.page'
      ],

      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      // Do not modify—file watching is disabled to prevent flickering during agent edits.
      hmr: process.env.DISABLE_HMR !== 'true',

      proxy: {
        '/api': {
          target: 'https://gl8wkexgui.execute-api.us-east-2.amazonaws.com',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
        '/tts': {
          target: 'https://ceexnffhr5wbwd4gny4hzo65k40zgutx.lambda-url.us-east-2.on.aws',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/tts/, ''),
        },
      },
    },
  };
});
