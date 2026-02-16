<script lang="ts">
  export let geojsonData: GeoJSON.FeatureCollection | null = null;
  export let treeSpeciesColors: Map<string, string> = new Map();

  interface GeoJSONFeatureProperties {
    h3_index: string;
    colour_hex: string;
    color_name: string;
    prominence: string;
    month: string;
    resolution: number;
    tree_species?: string[];
  }

  function getTreeSpeciesLegend(): Array<{ species: string; color: string }> {
    if (!geojsonData || !geojsonData.features || geojsonData.features.length === 0) {
      return [];
    }

    const speciesSet = new Set<string>();

    // Collect all unique species names from the GeoJSON
    geojsonData.features.forEach((feature) => {
      if (feature && feature.properties) {
        const properties = feature.properties as GeoJSONFeatureProperties;

        // Check if tree_species exists and is an array with at least one element
        if (properties.tree_species && Array.isArray(properties.tree_species) && properties.tree_species.length > 0) {
          properties.tree_species.forEach(species => {
            if (species && typeof species === 'string' && species.trim()) {
              speciesSet.add(species);
            }
          });
        }
      }
    });

    if (speciesSet.size === 0) {
      return [];
    }

    // Convert set to array and sort by species name
    const sortedSpecies = Array.from(speciesSet).sort((a, b) => a.localeCompare(b));

    // Create the legend items, looking up colors from treeSpeciesColors
    const speciesList = sortedSpecies.map(species => {
      // Try to find the color for this species
      let color = '#cccccc'; // Default gray color if not found

      // Check if we have a color for this exact species name
      if (treeSpeciesColors.has(species)) {
        color = treeSpeciesColors.get(species) || '#cccccc';
      } else {
        // Try different matching strategies
        const speciesWords = species.split(' ');
        const genusName = speciesWords[0];

        for (const [speciesName, speciesColor] of treeSpeciesColors) {
          const speciesNameWords = speciesName.split(' ');
          const speciesNameGenus = speciesNameWords[0];

          // Check if genus names match
          if (genusName && speciesNameGenus && genusName.toLowerCase() === speciesNameGenus.toLowerCase()) {
            color = speciesColor;
            break;
          }
        }
      }

      return {
        species,
        color
      };
    });

    return speciesList;
  }

  $: treeSpeciesLegend = getTreeSpeciesLegend();
</script>

<div class="legend-component">
  {#if treeSpeciesLegend.length > 0}
    <div class="legend-info">
      Showing {treeSpeciesLegend.length} tree species
    </div>
    {#each treeSpeciesLegend as item}
      <div class="legend-item">
        <div class="color-box" style="background-color: {item.color};"></div>
        <span class="species-name">{item.species}</span>
      </div>
    {/each}
  {:else}
    <div class="legend-info">
      No tree species data available - showing default colors
    </div>
    <div class="legend-item">
      <div class="color-box" style="background-color: #ff69b4;"></div>
      <span class="species-name">Pink</span>
    </div>
    <div class="legend-item">
      <div class="color-box" style="background-color: #fff000;"></div>
      <span class="species-name">Yellow</span>
    </div>
    <div class="legend-item">
      <div class="color-box" style="background-color: #f8f8ff;"></div>
      <span class="species-name">White</span>
    </div>
    <div class="legend-item">
      <div class="color-box" style="background-color: #800000;"></div>
      <span class="species-name">Red</span>
    </div>
    <div class="legend-item">
      <div class="color-box" style="background-color: #ffa500;"></div>
      <span class="species-name">Orange</span>
    </div>
  {/if}

  <div class="sources-section">
    <h4>Sources</h4>
    <div class="source-list">
      <div class="source-item">
        <a href="https://opencity.in/" target="_blank" rel="noopener noreferrer">BBMP Tree Census (via opencity.in)</a>
      </div>
      <div class="source-item">
        <a href="https://cubbonpark.in/tree-info/tree-species.html" target="_blank" rel="noopener noreferrer">Cubbon Park Tree Species</a>
      </div>
      <div class="source-item">
        <a href="https://www.wildwanderer.com/flowering-trees/" target="_blank" rel="noopener noreferrer">Wild Wanderer</a>
      </div>
      <div class="source-item">
        <a href="https://github.com/SirSireesh/bengaluru-flowering-trees" target="_blank" rel="noopener noreferrer">Source Code</a>
      </div>
    </div>
  </div>
</div>

<style>
  .legend-component {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    color: #333;
  }

  .legend-info {
    font-size: 0.8em;
    color: #666;
    margin-bottom: 8px;
    font-style: italic;
  }

  .legend-item {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    min-height: 24px;
  }

  .color-box {
    width: 20px;
    height: 20px;
    margin-right: 10px;
    border: 1px solid #ccc;
    border-radius: 3px;
    flex-shrink: 0;
  }

  .species-name {
    color: #444;
    font-size: 0.85rem;
    line-height: 1.3;
    word-wrap: break-word;
    flex: 1;
  }

  .sources-section {
    margin-top: 20px;
    padding-top: 15px;
    border-top: 1px solid #eee;
  }

  .sources-section h4 {
    color: #444;
    font-size: 1rem;
    margin-bottom: 10px;
  }

  .source-list {
    font-size: 0.75rem;
    line-height: 1.5;
  }

  .source-item {
    margin-bottom: 8px;
  }

  .source-item a {
    color: #4CAF50;
    text-decoration: none;
    transition: color 0.2s;
    word-wrap: break-word;
  }

  .source-item a:hover {
    color: #45a049;
    text-decoration: underline;
  }
</style>