import { resolve } from 'path';
import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';

export default defineConfig({
  plugins: [
      viteStaticCopy({
        targets: [
          { src: 'explorer/src/images/*', dest: 'images' },
        ]
    })
  ],
  root: resolve(__dirname, './'),
  base: '',
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    open: false,
    watch: {
      usePolling: true,
      disableGlobbing: false,
    },
  },
  resolve: {
    extensions: ['.js', '.json'],
    alias: {
      '~bootstrap': resolve(__dirname, './node_modules/bootstrap'),
      '~bootstrap-icons': resolve(__dirname, './node_modules/bootstrap-icons'),
    },
  },
  build: {
    outDir: resolve(__dirname, './explorer/static/explorer'),
    assetsDir: '',
    emptyOutDir: true,
    // The vite_asset template tag reads the hashed entry filename from here.
    manifest: 'manifest.json',
    target: 'es2015',
    rollupOptions: {
      input: {
        main: resolve(__dirname, './explorer/src/js/main.js'),
        // Some magic here; Vite always builds to styles.css, we named our entrypoint SCSS file the same thing
        // so that in the base template HTML file we can include 'styles.scss', and rename just the extension
        // in the vite template tag, and get both the dev and prod builds to work.
        styles: resolve(__dirname, '/explorer/src/scss/styles.scss'),
      },
      output: {
        // Entry and chunks are content-hashed so a changed bundle gets a new URL
        // even when the package version does not change. The entry must be
        // versioned by its filename, not a query string: chunks import the
        // entry by bare filename, and a URL that differs from the <script> src
        // makes the browser evaluate the entry (and Bootstrap) a second time.
        entryFileNames: `[name].[hash].js`,
        chunkFileNames: `[name].[hash].js`,
        assetFileNames: `[name].[ext]`
      },
    },
  },
});
