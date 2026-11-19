import { defineConfig } from 'vite'

// Resolve the plugin's `@hermes/plugin-sdk` import to the local stub, so the
// REAL plugin.js file runs unmodified in the demo and in tests.
export default defineConfig({
  resolve: {
    alias: {
      '@hermes/plugin-sdk': new URL('./test/sdk-stub.js', import.meta.url).pathname,
    },
  },
  test: {
    environment: 'jsdom',
    include: ['test/**/*.test.jsx'],
  },
})
