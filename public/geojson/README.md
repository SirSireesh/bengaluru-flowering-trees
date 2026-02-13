# GeoJSON Data Files

This directory contains the H3 hexagon grid data for flowering trees in Bengaluru, organized by month. These files are **generated** using the script in `scripts/tree_census_h3_generator.py`.

## File Structure

- `h3_tree_distribution_${MONTH}_resolution_10.geojson` - GeoJSON files for each month

## File Format

Each GeoJSON file contains:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "h3_index": "8b123456789abcdef",
        "colour_hex": "#ff69b4",
        "color_name": "pink",
        "prominence": "blended",
        "month": "Feb",
        "resolution": 10,
        "tree_species": ["Tabebuia rosea", "Delonix regia"]
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lng, lat], [lng, lat], ...]]
      }
    }
  ]
}
```

## Generation Process

These files are generated using the Python script:

```bash
python scripts/tree_census_h3_generator.py \
  --tree-census-path data/tree_census.geojson \
  --tree-species-data data/tree_species.parquet \
  --resolution 10 \
  --output-format geojson
```

The script:
1. Reads tree census data and species information
2. Creates H3 hexagon grids at the specified resolution
3. Blends flower colors based on prominence weights
4. Groups trees by flowering month
5. Outputs GeoJSON files for each month

## Requirements

Install dependencies:
```bash
uv sync
```

## Usage in Code

Files are fetched dynamically based on user selection:

```javascript
const filename = `h3_tree_distribution_${month}_resolution_10.geojson`;
const response = await fetch(`/geojson/${filename}`);
```

## Deployment

These files are automatically copied to the `dist/geojson/` directory during the build process via the Vite copy plugin.
