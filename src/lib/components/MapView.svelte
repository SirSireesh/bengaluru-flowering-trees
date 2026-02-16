<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Map, NavigationControl, Popup, LngLatBounds } from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  
  export let geojsonData: GeoJSON.FeatureCollection | null = null;
  
  let map: Map | null = null;
  let mapContainer: HTMLDivElement;
  let sourceId: string = 'tree-data-source';
  let layerId: string = 'tree-data-layer';
  
  interface GeoJSONFeatureProperties {
    h3_index: string;
    colour_hex: string;
    color_name: string;
    prominence: string;
    month: string;
    resolution: number;
    tree_species?: string[];
  }
  
  // Create the initial layer
  function createInitialLayer() {
    if (map && map.getSource(sourceId)) {
      // Add the layers
      try {
        map.addLayer({
          id: layerId,
          type: 'fill',
          source: sourceId,
          layout: {
            visibility: 'visible'
          },
          paint: {
            'fill-color': [
              'case',
              ['has', 'colour_hex'],
              ['get', 'colour_hex'],
              '#cccccc'
            ],
            'fill-opacity': 0.8,
            'fill-outline-color': '#ffffff'
          }
        });
      } catch (error) {
        console.error(`MapView: Failed to add fill layer:`, error);
      }
      
      map.addLayer({
        id: `${layerId}-outline`,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#ffffff',
          'line-width': 0.5
        }
      });
      
      // Add event handlers only if they haven't been added yet
      if (!map._popupHandlerAdded) {
        map.on('click', layerId, (e) => {
          const features = map.queryRenderedFeatures(e.point, {
            layers: [layerId, `${layerId}-outline`]
          });
          
          if (features.length > 0) {
            const feature = features[0];
            const coordinates = e.lngLat;
            
            const popupContent = `
              <b>Species: ${feature.properties.tree_species || 'Unknown'}</b>
            `;
            
            new Popup()
              .setLngLat(coordinates)
              .setHTML(popupContent)
              .addTo(map);
          }
        });
        
        // Change cursor to pointer when hovering over features
        map.on('mouseenter', layerId, () => {
          map.getCanvas().style.cursor = 'pointer';
        });
        map.on('mouseenter', `${layerId}-outline`, () => {
          map.getCanvas().style.cursor = 'pointer';
        });
        
        map.on('mouseleave', layerId, () => {
          map.getCanvas().style.cursor = '';
        });
        map.on('mouseleave', `${layerId}-outline`, () => {
          map.getCanvas().style.cursor = '';
        });
        
        map._popupHandlerAdded = true;
      }
      
      // Fit map to the bounds of the GeoJSON data if features exist
      if (geojsonData && geojsonData.features && geojsonData.features.length > 0) {
        const bounds = new LngLatBounds();
        geojsonData.features.forEach(feature => {
          if (feature.geometry.type === 'Polygon') {
            feature.geometry.coordinates[0].forEach(coord => {
              bounds.extend([coord[0], coord[1]]);
            });
          }
        });
        map.fitBounds(bounds, { padding: 50 });
      }
    }
  }
  
  onMount(() => {
    console.log('MapView: onMount called');
    
    // Initialize MapLibre GL map with OpenFreeMap positron style
    map = new Map({
      container: mapContainer,
      style: 'https://tiles.openfreemap.org/styles/positron',
      center: [77.5946, 12.9716], // Bengaluru coordinates [lng, lat]
      zoom: 12
    });
    
    console.log('MapView: Map initialized');
    
    // Add navigation controls
    map.addControl(new NavigationControl(), 'top-right');
    
    // Wait for the map to be idle (style loaded and ready)
    map.on('idle', () => {
      // Only add source if it doesn't already exist
      if (!map.getSource(sourceId)) {
        map.addSource(sourceId, {
          type: 'geojson',
          data: geojsonData || { type: 'FeatureCollection', features: [] }
        });
        
        // Create the initial layer immediately after adding the source
        createInitialLayer();
      } else {
        // Just update the data if source already exists
        if (geojsonData) {
          map.getSource(sourceId).setData(geojsonData);
        }
      }
    });
  });
  
  // Update the layer when data changes
  function updateGeoJSONLayer() {
    if (map && map.isStyleLoaded()) {
      // Simple approach: just update the source data if it exists
      if (map.getSource(sourceId)) {
        try {
          map.getSource(sourceId).setData(geojsonData || { type: 'FeatureCollection', features: [] });
          
          // Fit map to the bounds of the GeoJSON data if features exist
          if (geojsonData && geojsonData.features && geojsonData.features.length > 0) {
            const bounds = new LngLatBounds();
            geojsonData.features.forEach(feature => {
              if (feature.geometry.type === 'Polygon') {
                feature.geometry.coordinates[0].forEach(coord => {
                  bounds.extend([coord[0], coord[1]]);
                });
              }
            });
            map.fitBounds(bounds, { padding: 50 });
          }
        } catch (error) {
          console.error(`MapView: Error updating source data:`, error);
        }
      }
    }
  }
  
  // Track previous data to prevent unnecessary updates
  let previousDataString: string | null = null;
  
  // Expose update function to parent
  export function updateData(newData: GeoJSON.FeatureCollection | null) {
    console.log('MapView: updateData called with', newData?.features?.length || 0, 'features');
    
    // Only update if data actually changed
    const newDataString = JSON.stringify(newData);
    if (newDataString !== previousDataString) {
      console.log('MapView: Data changed, updating map');
      geojsonData = newData;
      previousDataString = newDataString;
      updateGeoJSONLayer();
    } else {
      console.log('MapView: Data unchanged, skipping update');
    }
  }
  
  onDestroy(() => {
    if (map) {
      map.remove();
    }
  });
</script>

<div bind:this={mapContainer} style="width: 100%; height: 100%;"></div>

<style>
  @import 'maplibre-gl/dist/maplibre-gl.css';
</style>
