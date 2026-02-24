<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { getCurrentMonthAbbreviation } from '../../utils/dateUtils';
  
  export let selectedMonth: string = getCurrentMonthAbbreviation();
  export let geojsonData: GeoJSON.FeatureCollection | null = null;
  export let treeSpeciesColors: Map<string, string> = new Map();
  
  // Debug: Log when geojsonData changes (disabled for performance)
  // $: console.log('Sidebar: geojsonData changed to:', geojsonData);
  
  const dispatch = createEventDispatcher();
  
  // Declare treeSpeciesLegend as a variable
  let treeSpeciesLegend: Array<{ species: string; color: string }> = [];
  
  interface GeoJSONFeatureProperties {
    TreeName: string;
    months: string;
    colour: string;
    prominence: string;
    months_flowering: Record<string, boolean>;
    [month: string]: boolean | string | Record<string, boolean>; // Dynamic month properties
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
    // Performance optimization: Early return if no data
    if (!geojsonData || !geojsonData.features || geojsonData.features.length === 0) {
      return [];
    }
    
    const speciesSet = new Set<string>();
    
    // Optimized: Single pass to collect species names
    for (let i = 0; i < geojsonData.features.length; i++) {
      const feature = geojsonData.features[i];
      if (feature && feature.properties) {
        const properties = feature.properties as GeoJSONFeatureProperties;
        if (properties.TreeName && typeof properties.TreeName === 'string' && properties.TreeName.trim()) {
          speciesSet.add(properties.TreeName);
        }
      }
    }
    
    if (speciesSet.size === 0) {
      return [];
    }
    
    // Optimized: Pre-create genus map for faster lookup
    const genusColorMap = new Map<string, string>();
    treeSpeciesColors.forEach((color, speciesName) => {
      const genusName = speciesName.split(' ')[0].toLowerCase();
      if (genusName && !genusColorMap.has(genusName)) {
        genusColorMap.set(genusName, color);
      }
    });
    
    // Convert set to sorted array
    const sortedSpecies = Array.from(speciesSet).sort((a, b) => a.localeCompare(b));
    
    // Optimized: Single pass with efficient color lookup
    const speciesList: Array<{ species: string; color: string }> = [];
    
    for (let i = 0; i < sortedSpecies.length; i++) {
      const species = sortedSpecies[i];
      let color = '#cccccc'; // Default gray
      
      // 1. Exact match (fastest)
      if (treeSpeciesColors.has(species)) {
        color = treeSpeciesColors.get(species) || '#cccccc';
      }
      // 2. Genus match (using pre-built map)
      else {
        const genusName = species.split(' ')[0].toLowerCase();
        if (genusName && genusColorMap.has(genusName)) {
          color = genusColorMap.get(genusName) || '#cccccc';
        }
        // 3. Partial match (fallback, but limited to avoid performance issues)
        else if (treeSpeciesColors.size < 50) { // Only do expensive search if color map is small
          for (const [speciesName, speciesColor] of treeSpeciesColors) {
            if (species.toLowerCase().includes(speciesName.toLowerCase()) || 
                speciesName.toLowerCase().includes(species.toLowerCase())) {
              color = speciesColor;
              break;
            }
          }
        }
      }
      
      speciesList.push({ species, color });
    }
    
    return speciesList;
  }
  
  // Reactive statement to update legend when geojsonData changes
  $: {
    // Only update if we have data and it's significantly different
    if (geojsonData && (!treeSpeciesLegend.length || 
        (geojsonData.features && geojsonData.features.length > treeSpeciesLegend.length * 2))) {
      treeSpeciesLegend = getTreeSpeciesLegend();
    }
  }
</script>

<div class="sidebar">
  <h2>Flowering Trees of Bengaluru</h2>
  
  <div class="month-selector">
    <label for="month-dropdown">Month:</label>
    <select id="month-dropdown" value={selectedMonth} on:change={handleMonthChange}>
      {#each months as month}
        <option value={month.value}>{month.label}</option>
      {/each}
    </select>
  </div>
  
  <div class="info-panel">
    <h3>Legend</h3>
    {#if treeSpeciesLegend.length > 0}
      <div style="font-size: 0.8em; color: #666; margin-bottom: 4px;">
        Showing {treeSpeciesLegend.length} tree species
      </div>
      <div class="legend-table-container">
        <table class="legend-table">
          <thead>
            <tr>
              <th scope="col">Color</th>
              <th scope="col">Species</th>
            </tr>
          </thead>
          <tbody>
            {#each treeSpeciesLegend as item}
              <tr>
                <td>
                  <div class="color-box" style="background-color: {item.color};"></div>
                </td>
                <td>{item.species}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else}
      <div style="font-size: 0.8em; color: #666; margin-bottom: 8px;">
        No tree species data available
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
      <div class="source-item">
        <a href="https://github.com/SirSireesh/bengaluru-flowering-trees" target="_blank" rel="noopener noreferrer">Source Code</a>
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
    margin-top: 0;
    padding: 8px;
    background-color: white;
    border-radius: 5px;
    border: 1px solid #eee;
  }

  .sources-panel {
    margin-top: 25px;
  }

  .source-list {
    font-size: 0.75rem;
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
    font-size: 1rem;
    margin-bottom: 6px;
  }
  

  
  .color-box {
    width: 20px;
    height: 20px;
    margin-right: 10px;
    border: 1px solid #ccc;
    border-radius: 3px;
  }

  .legend-table-container {
    max-height: 400px;
    overflow-y: auto;
    margin-top: 4px;
  }

  .legend-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }

  .legend-table th {
    text-align: left;
    padding: 4px 3px;
    background-color: #f9f9f9;
    border-bottom: 1px solid #ddd;
    font-weight: 600;
    color: #333;
  }

  .legend-table td {
    padding: 3px 3px;
    border-bottom: 1px solid #eee;
    vertical-align: middle;
  }

  .legend-table tr:hover {
    background-color: #f5f5f5;
  }

  .legend-table tr:last-child td {
    border-bottom: none;
  }

  .legend-table .color-box {
    width: 16px;
    height: 16px;
    margin: 0 auto;
    border: 1px solid #ccc;
    border-radius: 2px;
  }

  .legend-table td:last-child {
    color: #444;
    line-height: 1.3;
    word-wrap: break-word;
  }

  .month-selector {
    margin-bottom: 20px;
    padding: 10px;
    background-color: white;
    border-radius: 5px;
    border: 1px solid #eee;
    display: flex;
    align-items: center;
  }

  .month-selector label {
    display: inline-block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #444;
    font-size: 0.9rem;
    margin-right: 8px;
  }

  .month-selector select {
    flex: 1;
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