<script lang="ts">
  import { onMount } from 'svelte';
  import Sidebar from './lib/components/Sidebar.svelte';
  import MapView from './lib/components/MapView.svelte';
  import LegendComponent from './lib/components/LegendComponent.svelte';
  
  let geojsonData: GeoJSON.FeatureCollection | null = null;
  let isLoading: boolean = true;
  let error: string | null = null;
  let selectedMonth: string = 'Feb';
  let treeSpeciesColors: Map<string, string> = new Map();
  let isMobile: boolean = false;
  let showLegend: boolean = false;
  
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
  
  onMount(async () => {
    // Check if we're on a mobile device
    function checkMobile() {
      isMobile = window.innerWidth <= 768;
    }
    
    // Initial check
    checkMobile();
    
    // Add resize listener
    window.addEventListener('resize', checkMobile);
    
    await loadTreeSpeciesColors();
    await loadGeoJSONData(selectedMonth);
  });
  
  let mapViewRef;
  
  async function loadTreeSpeciesColors() {
    try {
      console.log('Loading tree species colors from JSON file...');
      
      // Load the pre-converted JSON file
      const response = await fetch('/tree_species_colors.json');
      if (!response.ok) {
        throw new Error(`Failed to load JSON file: ${response.status} ${response.statusText}`);
      }
      
      const speciesColorsData = await response.json();
      
      // Convert the JSON object to a Map
      const colorsMap = new Map<string, string>();
      for (const [species, color] of Object.entries(speciesColorsData)) {
        if (species && color && species !== 'Others') {
          colorsMap.set(species, color);
        }
      }
      
      treeSpeciesColors = colorsMap;
      console.log(`Loaded ${colorsMap.size} tree species colors from JSON file`);
      console.log('Sample colors:', Array.from(colorsMap.entries()).slice(0, 10));
      
      // Debug: Log all the species names we loaded
      console.log('All loaded species names:', Array.from(colorsMap.keys()));
      
    } catch (err) {
      console.error('Error loading tree species colors:', err);
      // If we can't load the JSON file, we'll fall back to default colors
      // Set up some default colors for common species
      const defaultColors = new Map<string, string>();
      defaultColors.set('Pink', '#ff69b4');
      defaultColors.set('Yellow', '#fff000');
      defaultColors.set('White', '#f8f8ff');
      defaultColors.set('Red', '#800000');
      defaultColors.set('Orange', '#ffa500');
      treeSpeciesColors = defaultColors;
    }
  }

  async function loadGeoJSONData(month: string) {
    isLoading = true;
    error = null;
    
    try {
      // Load the GeoJSON file for the selected month
      const filename = `h3_tree_distribution_${month}_resolution_10.geojson`;
      const response = await fetch(`/geojson/${filename}`);
      
      if (!response.ok) {
        throw new Error(`Failed to load ${month} GeoJSON: ${response.status} ${response.statusText}`);
      }
      
      const data: GeoJSON.FeatureCollection<GeoJSON.Geometry, GeoJSONFeatureProperties> = await response.json();
      console.log(`Loaded ${month} data with ${data.features?.length || 0} features`);
      if (data.features && data.features.length > 0) {
        const sampleColors = data.features.slice(0, 5).map(f => f.properties?.colour_hex);
        console.log(`Sample colors: ${sampleColors.join(', ')}`);
      }
      
      // Update the map view with the new data
      if (mapViewRef && typeof mapViewRef.updateData === 'function') {
        mapViewRef.updateData(data);
      }
      
      // Only update geojsonData if it actually changed to prevent unnecessary re-renders
      const dataString = JSON.stringify(data);
      const currentDataString = JSON.stringify(geojsonData);
      if (dataString !== currentDataString) {
        geojsonData = data;
      }
      
    } catch (err) {
      console.error('Error loading GeoJSON:', err);
      error = `Failed to load ${month} data. Please make sure the GeoJSON file exists.`;
      
      // Create a mock GeoJSON for demonstration purposes
      const mockData = createMockGeoJSON();
      
      // Update the map view with mock data
      if (mapViewRef && typeof mapViewRef.updateData === 'function') {
        mapViewRef.updateData(mockData);
      }
      
      // Only update geojsonData if it actually changed to prevent unnecessary re-renders
      const mockDataString = JSON.stringify(mockData);
      const currentDataString = JSON.stringify(geojsonData);
      if (mockDataString !== currentDataString) {
        geojsonData = mockData;
      }
    } finally {
      isLoading = false;
    }
  }
  
  function handleMonthChange(event: CustomEvent<{ month: string }>) {
    selectedMonth = event.detail.month;
    loadGeoJSONData(selectedMonth);
  }
  
  function createMockGeoJSON(): GeoJSON.FeatureCollection<GeoJSON.Polygon, GeoJSONFeatureProperties> {
    // Create a simple mock GeoJSON with some sample data around Bangalore
    return {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {
            "h3_index": "8b123456789abcdef",
            "colour_hex": "#ff69b4",
            "color_name": "pink",
            "prominence": "blended",
            "month": selectedMonth,
            "resolution": 10
          },
          "geometry": {
            "type": "Polygon",
            "coordinates": [[
              [77.59, 12.97],
              [77.60, 12.97],
              [77.60, 12.98],
              [77.59, 12.98],
              [77.59, 12.97]
            ]]
          }
        },
        {
          "type": "Feature",
          "properties": {
            "h3_index": "8b123456789abcdef",
            "colour_hex": "#fff000",
            "color_name": "yellow",
            "prominence": "blended",
            "month": selectedMonth,
            "resolution": 10
          },
          "geometry": {
            "type": "Polygon",
            "coordinates": [[
              [77.58, 12.96],
              [77.59, 12.96],
              [77.59, 12.97],
              [77.58, 12.97],
              [77.58, 12.96]
            ]]
          }
        }
      ]
    };
  }
</script>

<div class="app-container">
  {#if !isMobile}
    <!-- Desktop: Sidebar layout -->
    <Sidebar 
      selectedMonth={selectedMonth} 
      geojsonData={geojsonData} 
      treeSpeciesColors={treeSpeciesColors} 
      on:monthChange={handleMonthChange}
    />
  {/if}
  
  <div class="main-content">
    <div class="map-container">
      {#if isLoading}
        <div class="loading-overlay">
          <div class="loading-spinner"></div>
          <p>Loading {selectedMonth === 'Jan' ? 'January' : 
                     selectedMonth === 'Feb' ? 'February' : 
                     selectedMonth === 'Mar' ? 'March' : 
                     selectedMonth === 'Apr' ? 'April' : 
                     selectedMonth === 'May' ? 'May' : 
                     selectedMonth === 'Jun' ? 'June' : 
                     selectedMonth === 'Jul' ? 'July' : 
                     selectedMonth === 'Aug' ? 'August' : 
                     selectedMonth === 'Sep' ? 'September' : 
                     selectedMonth === 'Oct' ? 'October' : 
                     selectedMonth === 'Nov' ? 'November' : 'December'} data...</p>
        </div>
      {/if}
      
      {#if error}
        <div class="error-message">
          <p>{error}</p>
          <p>Displaying mock data for demonstration.</p>
        </div>
      {/if}
      
      <MapView bind:this={mapViewRef} geojsonData={geojsonData} />
    </div>
    
    {#if isMobile}
      <!-- Mobile: Bottom bar layout -->
      <div class="bottom-bar">
        <div class="month-selector">
          <label for="month-dropdown">Month:</label>
          <select id="month-dropdown" value={selectedMonth} on:change={handleMonthChange}>
            {#each months as month}
              <option value={month.value}>{month.label}</option>
            {/each}
          </select>
        </div>
        
        <button class="legend-toggle" on:click={() => showLegend = !showLegend}>
          {showLegend ? 'Hide Legend' : 'Show Legend'}
        </button>
        
        {#if showLegend}
          <div class="legend-overlay">
            <div class="legend-content">
              <h3>Tree Species Legend</h3>
              <div class="legend-scrollable">
                {#if geojsonData}
                  <LegendComponent geojsonData={geojsonData} treeSpeciesColors={treeSpeciesColors} />
                {:else}
                  <div class="loading-legend">Loading legend data...</div>
                {/if}
              </div>
              <button class="close-legend" on:click={() => showLegend = false}>Close</button>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  
  body, html {
    height: 100%;
    width: 100%;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    margin: 0;
    padding: 0;
    background-color: transparent;
  }
  
  .app-container {
    display: flex;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
    margin: 0;
    padding: 0;
  }
  
  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  
  .map-container {
    flex: 1;
    position: relative;
    overflow: hidden;
  }
  
  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(255, 255, 255, 0.8);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .loading-spinner {
    width: 50px;
    height: 50px;
    border: 5px solid #f3f3f3;
    border-top: 5px solid #4CAF50;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 15px;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .error-message {
    position: absolute;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background-color: #ffdddd;
    padding: 15px 25px;
    border-radius: 5px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    z-index: 1000;
    max-width: 80%;
    text-align: center;
  }
  
  .error-message p {
    margin: 5px 0;
    color: #d32f2f;
  }
  
  .error-message p:last-child {
    font-size: 0.9em;
    color: #666;
  }
  
  /* Bottom bar styles */
  .bottom-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: #f5f5f5;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
    z-index: 1000;
    box-sizing: border-box;
  }
  
  .month-selector {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 150px;
    max-width: 250px;
  }
  
  .month-selector label {
    font-weight: 600;
    color: #444;
    font-size: 0.9rem;
    white-space: nowrap;
  }
  
  .month-selector select {
    padding: 6px 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 0.9rem;
    background-color: white;
    cursor: pointer;
    transition: border-color 0.2s;
    color: #333;
    flex: 1;
  }
  
  .month-selector select:hover {
    border-color: #ccc;
  }
  
  .month-selector select:focus {
    outline: none;
    border-color: #4CAF50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
  }
  
  .legend-toggle {
    padding: 6px 12px;
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
  }
  
  .legend-toggle:hover {
    background-color: #f9f9f9;
    border-color: #ccc;
  }
  
  .legend-toggle:active {
    transform: scale(0.98);
  }
  
  /* Legend overlay styles */
  .legend-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 60px; /* Height of bottom bar */
    background-color: rgba(255, 255, 255, 0.95);
    z-index: 2000;
    overflow-y: auto;
    padding: 20px;
    box-sizing: border-box;
  }
  
  .legend-content {
    max-width: 800px;
    margin: 0 auto;
    background-color: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }
  
  .legend-content h3 {
    color: #333;
    font-size: 1.2rem;
    margin-bottom: 15px;
    border-bottom: 2px solid #4CAF50;
    padding-bottom: 8px;
  }
  
  .legend-scrollable {
    max-height: calc(100vh - 200px);
    overflow-y: auto;
    padding-right: 8px;
  }
  
  .close-legend {
    display: block;
    margin: 15px auto 0;
    padding: 8px 16px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    transition: background-color 0.2s;
  }
  
  .close-legend:hover {
    background-color: #45a049;
  }
  
  /* Adjust map container based on layout */
  .map-container {
    height: 100vh;
  }
  
  @media (max-width: 768px) {
    .map-container {
      height: calc(100vh - 60px); /* Subtract bottom bar height on mobile */
    }
  }
  
  /* Responsive adjustments */
  @media (max-width: 480px) {
    .bottom-bar {
      flex-direction: column;
      align-items: stretch;
      padding: 8px 12px;
    }
    
    .month-selector {
      max-width: none;
      width: 100%;
    }
    
    .legend-toggle {
      width: 100%;
      justify-content: center;
    }
    
    .legend-overlay {
      bottom: 80px; /* Adjust for potentially taller bottom bar */
      padding: 15px;
    }
    
    .legend-content {
      padding: 15px;
    }
  }
</style>
