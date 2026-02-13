<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let selectedMonth: string = 'Feb';
  export let geojsonData: GeoJSON.FeatureCollection | null = null;
  
  // Debug: Log when geojsonData changes
  $: console.log('Sidebar: geojsonData changed to:', geojsonData);
  
  const dispatch = createEventDispatcher();
  
  // Declare treeSpeciesLegend as a variable
  let treeSpeciesLegend: Array<{ species: string; color: string }> = [];
  
  interface GeoJSONFeatureProperties {
    h3_index: string;
    colour_hex: string;
    color_name: string;
    prominence: string;
    month: string;
    resolution: number;
    tree_species?: string[];
  }
  
  const months = [
    { value: 'Jan', label: 'January' },
    { value: 'Feb', label: 'February' },
    { value: 'Mar', label: 'March' },
    { value: 'Apr', label: 'April' },
    { value: 'May', label: 'May' },
    { value: 'Jun', label: 'June' },
    { value: 'Jul', label: 'July' },
    { value: 'Aug', label: 'August' },
    { value: 'Sep', label: 'September' },
    { value: 'Oct', label: 'October' },
    { value: 'Nov', label: 'November' },
    { value: 'Dec', label: 'December' }
  ];
  
  function handleMonthChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    const newMonth = target.value;
    dispatch('monthChange', { month: newMonth });
  }
  
  // Extract unique tree species and their colors from geojsonData
  function getTreeSpeciesLegend(): Array<{ species: string; color: string }> {
    console.log('Sidebar: getTreeSpeciesLegend called with geojsonData:', geojsonData);
    
    if (!geojsonData || !geojsonData.features || geojsonData.features.length === 0) {
      console.log('Sidebar: No geojsonData, no features, or empty features array');
      return [];
    }
    
    console.log(`Sidebar: Processing ${geojsonData.features.length} features`);
    
    const speciesMap = new Map<string, string>();
    let validFeatures = 0;
    
    geojsonData.features.forEach((feature, index) => {
      if (feature && feature.properties) {
        const properties = feature.properties as GeoJSONFeatureProperties;
        
        // Check if tree_species exists and is an array with at least one element
        if (properties.tree_species && Array.isArray(properties.tree_species) && properties.tree_species.length > 0 && properties.colour_hex) {
          validFeatures++;
          const speciesArray = properties.tree_species;
          const color = properties.colour_hex;
          
          speciesArray.forEach(species => {
            if (species && typeof species === 'string' && species.trim()) {
              if (!speciesMap.has(species)) {
                speciesMap.set(species, color);
              }
            }
          });
        } else {
          console.log(`Sidebar: Feature ${index} missing required properties`, properties);
        }
      }
    });
    
    console.log(`Sidebar: Found ${speciesMap.size} unique species from ${validFeatures} valid features`);
    
    if (speciesMap.size === 0) {
      console.log('Sidebar: No species found, returning empty array');
      return [];
    }
    
    // Convert map to array of objects and sort by species name
    const speciesList = Array.from(speciesMap.entries()).map(([species, color]) => ({
      species,
      color
    }));
    
    speciesList.sort((a, b) => a.species.localeCompare(b.species));
    
    console.log('Sidebar: Final species list:', speciesList);
    
    return speciesList;
  }
  
  // Reactive statement to update legend when geojsonData changes
  $: {
    console.log('Sidebar: Reactive statement triggered, geojsonData:', geojsonData);
    treeSpeciesLegend = getTreeSpeciesLegend();
    console.log('Sidebar: Updated treeSpeciesLegend:', treeSpeciesLegend);
  }
</script>

<div class="sidebar">
  <h2>Flowering Trees of Bengaluru</h2>
  
  <div class="month-selector">
    <label for="month-dropdown">Select Month:</label>
    <select id="month-dropdown" value={selectedMonth} on:change={handleMonthChange}>
      {#each months as month}
        <option value={month.value}>{month.label}</option>
      {/each}
    </select>
  </div>
  
  <div class="info-panel">
    <h3>Legend</h3>
    {#if treeSpeciesLegend.length > 0}
      <div style="font-size: 0.8em; color: #666; margin-bottom: 8px;">
        Showing {treeSpeciesLegend.length} tree species
      </div>
      {#each treeSpeciesLegend as item}
        <div class="legend-item">
          <div class="color-box" style="background-color: {item.color};"></div>
          <span>{item.species}</span>
        </div>
      {/each}
    {:else}
      <div style="font-size: 0.8em; color: #666; margin-bottom: 8px;">
        No tree species data available - showing default colors
      </div>
      <div class="legend-item">
        <div class="color-box" style="background-color: #ff69b4;"></div>
        <span>Pink</span>
      </div>
      <div class="legend-item">
        <div class="color-box" style="background-color: #fff000;"></div>
        <span>Yellow</span>
      </div>
      <div class="legend-item">
        <div class="color-box" style="background-color: #f8f8ff;"></div>
        <span>White</span>
      </div>
      <div class="legend-item">
        <div class="color-box" style="background-color: #800000;"></div>
        <span>Red</span>
      </div>
      <div class="legend-item">
        <div class="color-box" style="background-color: #ffa500;"></div>
        <span>Orange</span>
      </div>
    {/if}
  </div>

  <div class="info-panel sources-panel">
    <h3>Sources</h3>
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
    </div>
  </div>
</div>

<style>
  .sidebar {
    width: 250px;
    background-color: #f5f5f5;
    padding: 20px;
    height: 100vh;
    overflow-y: auto;
    box-shadow: 2px 0 5px rgba(0,0,0,0.1);
    color: #333;
  }
  
  h2 {
    color: #333;
    font-size: 1.5rem;
    margin-bottom: 20px;
    border-bottom: 2px solid #4CAF50;
    padding-bottom: 10px;
  }
  
  .info-panel {
    margin-top: 20px;
    padding: 15px;
    background-color: white;
    border-radius: 5px;
    border: 1px solid #eee;
  }

  .sources-panel {
    margin-top: 25px;
  }

  .source-list {
    font-size: 0.85rem;
    line-height: 1.5;
  }

  .source-item {
    margin-bottom: 10px;
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
  
  h3 {
    color: #444;
    font-size: 1.1rem;
    margin-bottom: 15px;
  }
  

  
  .color-box {
    width: 20px;
    height: 20px;
    margin-right: 10px;
    border: 1px solid #ccc;
    border-radius: 3px;
  }

  .legend-item span {
    color: #444;
    font-size: 0.85rem;
    line-height: 1.3;
    max-width: 180px;
    word-wrap: break-word;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    min-height: 24px;
  }

  .month-selector {
    margin-bottom: 20px;
    padding: 10px;
    background-color: white;
    border-radius: 5px;
    border: 1px solid #eee;
  }

  .month-selector label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #444;
    font-size: 0.9rem;
  }

  .month-selector select {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
    background-color: white;
    cursor: pointer;
    transition: border-color 0.2s;
    color: #333;
  }

  .month-selector select:hover {
    border-color: #ccc;
  }

  .month-selector select:focus {
    outline: none;
    border-color: #4CAF50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
  }

  .month-selector option {
    color: #333;
    background-color: white;
  }
</style>