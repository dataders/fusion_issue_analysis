import { defineConfig } from 'vite';

// Relative assets work at both tanstack/dist/ and a nested PR preview path.
export default defineConfig({ base: './' });
