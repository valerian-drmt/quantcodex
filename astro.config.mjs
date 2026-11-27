// @ts-check
import { defineConfig } from 'astro/config';

// GitHub Pages project site: https://valerian-drmt.github.io/quantcodex/
export default defineConfig({
  site: 'https://valerian-drmt.github.io',
  base: '/quantcodex',
  trailingSlash: 'ignore',
  // CSS is written into each page. A page cached from an earlier deploy then never
  // points to a stylesheet that the next deploy has removed.
  build: { inlineStylesheets: 'always' },
});
