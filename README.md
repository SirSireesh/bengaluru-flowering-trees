# Bengaluru Flowering Trees Visualization

A map for visualizing flowering trees in Bengaluru

## Project Overview

This application displays the distribution of flowering trees in Bengaluru, India, organized by month

## Development

- Install dependencies with pnpm install (or npm install)
- Start local dev server with pnpm run dev (or npm run dev)
- Build site deployment assets with pnpm run build (or npm run build)

## Data

Data is generated using `scripts/tree_census_h3_generator.py`.


### Data Sources

- BBMP Tree Census (via opencity.in)
- [Cubbon Park Tree Species](https://cubbonpark.in/tree-info/tree-species.html)
- [Wild Wanderer](https://www.wildwanderer.com/flowering-trees/)


## Project Structure

```
src/
├── main.ts                  # Entry point
├── App.svelte               # Main application component
├── lib/
│   ├── components/          # Reusable components
│   │   ├── MapView.svelte   # Interactive map component
│   │   └── Sidebar.svelte   # Sidebar with controls and legend
│   └── ...

public/
├── geojson/                 # Generated GeoJSON data files
│   ├── h3_tree_distribution_*.geojson  # Monthly data
│   └── README.md            # Data documentation
├── tree_species.parquet     # Tree species data
└── vite.svg                 # Logo

scripts/
└── tree_census_h3_generator.py  # Data generation script

dist/                       # Built static site (created by npm run build)
```
