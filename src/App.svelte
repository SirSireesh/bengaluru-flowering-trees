<script lang="ts">
  import { onMount } from 'svelte';
  import Sidebar from './lib/components/Sidebar.svelte';
  import MapView from './lib/components/MapView.svelte';
  
  let geojsonData: GeoJSON.FeatureCollection | null = null;
  let isLoading: boolean = true;
  let error: string | null = null;
  let selectedMonth: string = 'Feb';
  
  interface GeoJSONFeatureProperties {
    h3_index: string;
    colour_hex: string;
    color_name: string;
    prominence: string;
    month: string;
    resolution: number;
    tree_species?: string[];
  }
  
  onMount(async () => {
    await loadGeoJSONData(selectedMonth);
  });
  
  let mapViewRef;
  
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
      geojsonData = data;
      console.log(`App.svelte: Successfully loaded ${month} GeoJSON data with`, data.features?.length || 0, 'features');
      console.log('App.svelte: Sample feature properties:', data.features?.[0]?.properties);
      
      // Update the map view with the new data
      if (mapViewRef && typeof mapViewRef.updateData === 'function') {
        mapViewRef.updateData(data);
      }
      
    } catch (err) {
      console.error('Error loading GeoJSON:', err);
      error = `Failed to load ${month} data. Please make sure the GeoJSON file exists.`;
      
      // Create a mock GeoJSON for demonstration purposes
      const mockData = createMockGeoJSON();
      geojsonData = mockData;
      
      // Update the map view with mock data
      if (mapViewRef && typeof mapViewRef.updateData === 'function') {
        mapViewRef.updateData(mockData);
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
  <Sidebar selectedMonth={selectedMonth} geojsonData={geojsonData} on:monthChange={handleMonthChange} />
  
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
</style>
