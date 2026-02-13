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
    console.log('MapView: createInitialLayer called');
    console.log('MapView: map.getSource(sourceId):', map?.getSource(sourceId));
    
    if (map && map.getSource(sourceId)) {
      console.log(`Creating initial layer with ${geojsonData?.features?.length || 0} features`);
      console.log('GeoJSON data sample:', geojsonData?.features?.slice(0, 3));
      
      // Validate GeoJSON structure
      if (geojsonData && geojsonData.features) {
        geojsonData.features.forEach((feature, index) => {
          if (!feature.properties || !feature.properties.colour_hex) {
            console.warn(`Feature at index ${index} missing colour_hex property`, feature);
          }
          if (!feature.geometry || !feature.geometry.coordinates) {
            console.warn(`Feature at index ${index} missing geometry coordinates`, feature);
          }
        });
      }
      
      // Add the layers
      try {
        console.log(`MapView: Adding fill layer with source ${sourceId}`);
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
        console.log(`MapView: Fill layer ${layerId} added successfully`);
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
      console.log(`MapView: Outline layer ${layerId}-outline added successfully`);
      
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
      console.log('MapView: Map idle event fired (style loaded)');
      console.log('MapView: geojsonData at idle time:', geojsonData);
      
      // Only add source if it doesn't already exist
      if (!map.getSource(sourceId)) {
        console.log('MapView: Adding source (first time)');
        map.addSource(sourceId, {
          type: 'geojson',
          data: geojsonData || { type: 'FeatureCollection', features: [] }
        });
        
        console.log('MapView: Source added:', sourceId);
        console.log('MapView: Source data:', map.getSource(sourceId).serialize().data);
        
        // Create the initial layer immediately after adding the source
        createInitialLayer();
      } else {
        console.log('MapView: Source already exists, skipping initial setup');
        
        // Just update the data if source already exists
        if (geojsonData) {
          map.getSource(sourceId).setData(geojsonData);
          console.log('MapView: Updated existing source data');
        }
      }
      
      // Event handlers will be added after layer creation
    });
  });
  
  // Update the layer when data changes
  function updateGeoJSONLayer() {
    console.log('MapView: updateGeoJSONLayer called');
    console.log('MapView: map.isStyleLoaded():', map?.isStyleLoaded());
    console.log('MapView: map.getSource(sourceId):', map?.getSource(sourceId));
    
    if (map && map.isStyleLoaded()) {
      console.log(`Updating layer with ${geojsonData?.features?.length || 0} features`);
      
      // Simple approach: just update the source data if it exists
      if (map.getSource(sourceId)) {
        console.log('MapView: Source exists, updating data');
        try {
          map.getSource(sourceId).setData(geojsonData || { type: 'FeatureCollection', features: [] });
          console.log('MapView: Source data updated successfully');
          
          // Fit map to the bounds of the GeoJSON data if features exist
          if (geojsonData && geojsonData.features && geojsonData.features.length > 0) {
            console.log('MapView: Fitting bounds to data');
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
      } else {
        console.log('MapView: Source does not exist, will be created when map is ready');
      }
    } else {
      console.log('MapView: Cannot update layer - map not ready');
    }
  }
  
  // Expose update function to parent
  export function updateData(newData: GeoJSON.FeatureCollection | null) {
    console.log('MapView: updateData called with', newData?.features?.length || 0, 'features');
    geojsonData = newData;
    updateGeoJSONLayer();
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
