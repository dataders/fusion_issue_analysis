import {defineConfig} from 'vite';

export default defineConfig({
  build: {outDir: 'dist'},
  optimizeDeps: {exclude: ['@duckdb/duckdb-wasm']},
  server: {
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    },
  },
});
