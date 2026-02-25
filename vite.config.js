import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import { copy } from 'vite-plugin-copy'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    svelte(),
    copy({
      targets: [
        { src: 'public/geojson/*.geojson', dest: 'dist/geojson' },
        { src: 'public/geojson/*.geojson.gz', dest: 'dist/geojson' },
        { src: 'public/tree_species.parquet', dest: 'dist' },
        { src: 'public/tree_species_colors.json', dest: 'dist' },
        { src: 'public/vite.svg', dest: 'dist' },
        { src: 'src/utils/h3ClusteringWorker.ts', dest: 'dist/assets' },
        { src: 'src/utils/dataLoaderWorker.ts', dest: 'dist/assets' }
      ],
      hook: 'writeBundle'
    })
  ],
  resolve: {
    alias: {
      '@': '/src'
    }
  },
  build: {
    // Ensure all public assets are copied
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        assetFileNames: 'assets/[name]-[hash][extname]',
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js'
      }
    }
  }
})
