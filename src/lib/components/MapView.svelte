<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Map, NavigationControl, Popup, LngLatBounds } from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import { getOptimalResolution, shouldUseClusters } from '../../utils/h3Clustering';
  import { createClusteringWorker, computeClustersInWorker } from '../../utils/workerLoader';

  let clusteringWorker: Worker | null = null;
  
  export let geojsonData: GeoJSON.FeatureCollection | null = null;
  
  let currentZoomLevel: number = 12;
  let clusterData: GeoJSON.FeatureCollection | null = null;
  
  let map: Map | null = null;
  let mapContainer: HTMLDivElement;
  let sourceId: string = 'tree-data-source';
  let layerId: string = 'tree-data-layer';
  let clusterSourceId: string = 'tree-cluster-source';
  let clusterLayerId: string = 'tree-cluster-layer';
  
  interface GeoJSONFeatureProperties {
    TreeName: string;
    months: string;
    colour: string;
    prominence: string;
    months_flowering: Record<string, boolean>;
    [month: string]: boolean | string | Record<string, boolean>; // Dynamic month properties
  }
  
  // Create the cluster layer
  function createClusterLayer() {
    if (map && map.getSource(clusterSourceId)) {
      // Add the cluster layer
      try {
        // Use fill layer for H3 cell polygons
        map.addLayer({
          id: clusterLayerId,
          type: 'fill',
          source: clusterSourceId,
          layout: {
            visibility: 'visible'
          },
          paint: {
            'fill-color': [
              'case',
              ['has', 'dominantColor'],
              ['get', 'dominantColor'],
              '#81c784'  // Default green color
            ],
            'fill-opacity': 0.6,
            'fill-antialias': true
          }
        });
        
        // Add outline for better visibility
        map.addLayer({
          id: `${clusterLayerId}-outline`,
          type: 'line',
          source: clusterSourceId,
          layout: {
            visibility: 'visible'
          },
          paint: {
            'line-color': '#ffffff',
            'line-width': 1,
            'line-opacity': 0.8
          }
        });
        

        
        // Add event handlers for cluster popups
        if (!map._clusterPopupHandlerAdded) {
          map.on('click', clusterLayerId, (e) => {
            const features = map.queryRenderedFeatures(e.point, {
              layers: [clusterLayerId]
            });
            
            if (features.length > 0) {
              const feature = features[0];
              const coordinates = e.lngLat;
              
              const count = feature.properties.count || 0;
              const dominantType = feature.properties.dominantType || 'Unknown';
              const treeTypes = feature.properties.treeTypes || {};
              
              // Create a summary of tree types
              const typeSummary = Object.entries(treeTypes)
                .slice(0, 5) // Show top 5 types
                .map(([type, count]) => `${type}: ${count}`)
                .join('<br>');
              
              const popupContent = `
                <div style="color: #333; background: #fff; padding: 8px; border-radius: 4px;">
                  <b>${count} trees in this area</b><br>
                  <small>Dominant: ${dominantType}</small><br>
                  ${typeSummary}
                </div>
              `;
              
              new Popup()
                .setLngLat(coordinates)
                .setHTML(popupContent)
                .addTo(map);
            }
          });
          
          // Change cursor to pointer when hovering over cluster features
          map.on('mouseenter', clusterLayerId, () => {
            map.getCanvas().style.cursor = 'pointer';
          });
          
          map.on('mouseleave', clusterLayerId, () => {
            map.getCanvas().style.cursor = '';
          });
          
          map._clusterPopupHandlerAdded = true;
        }
      } catch (error) {
        console.error(`MapView: Failed to add cluster layer:`, error);
      }
    }
  }
  
  // Create the initial layer
  function createInitialLayer() {
    if (map && map.getSource(sourceId)) {
      // Add the layers
      try {
        map.addLayer({
          id: layerId,
          type: 'circle',
          source: sourceId,
          layout: {
            visibility: 'visible'
          },
          paint: {
            'circle-color': [
              'case',
              ['has', 'colour'],
              ['get', 'colour'],
              '#cccccc'
            ],
            'circle-radius': 6,
            'circle-opacity': 0.8,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#ffffff'
          }
        });
      } catch (error) {
        console.error(`MapView: Failed to add circle layer:`, error);
      }
      
      // Add event handlers only if they haven't been added yet
      if (!map._popupHandlerAdded) {
        map.on('click', layerId, (e) => {
          const features = map.queryRenderedFeatures(e.point, {
            layers: [layerId]
          });
          
          if (features.length > 0) {
            const feature = features[0];
            const coordinates = e.lngLat;
            
            const popupContent = `
              <div style="color: #333; background: #fff; padding: 8px; border-radius: 4px;">
                <b>Species: ${feature.properties.TreeName || 'Unknown'}</b><br>
                <small>Flowering: ${feature.properties.months || 'Unknown'}</small>
              </div>
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
        
        map.on('mouseleave', layerId, () => {
          map.getCanvas().style.cursor = '';
        });
        
        map._popupHandlerAdded = true;
      }
      
      // Fit map to the bounds of the GeoJSON data if features exist
      if (geojsonData && geojsonData.features && geojsonData.features.length > 0) {
        const bounds = new LngLatBounds();
        geojsonData.features.forEach(feature => {
          if (feature.geometry.type === 'Point') {
            const coordinates = feature.geometry.coordinates;
            bounds.extend([coordinates[0], coordinates[1]]);
          }
        });
        map.fitBounds(bounds, { padding: 50 });
      }
    }
  }
  
  onMount(() => {
    // Initialize clustering worker
    clusteringWorker = createClusteringWorker();
    
    const bengaluruBounds = new LngLatBounds(
      [77.45, 12.80], // Southwest corner
      [77.80, 13.15]  // Northeast corner
    );

    // Initialize MapLibre GL map with OpenFreeMap
    map = new Map({
      container: mapContainer,
      style: 'https://tiles.openfreemap.org/styles/positron',
      center: [77.5946, 12.9716], // Bengaluru coordinates [lng, lat]
      zoom: 12,
      maxBounds: bengaluruBounds, // Restrict viewport to Bengaluru
      maxZoom: 18,
      minZoom: 10
    });
    
    // Add navigation controls
    map.addControl(new NavigationControl(), 'top-right');
    
    // Handle window resize events to ensure map resizes properly
    const handleResize = () => {
      if (map) {
        map.resize();
      }
    };
    
    window.addEventListener('resize', handleResize);
    
    onDestroy(() => {
      window.removeEventListener('resize', handleResize);
    });
    
    // Wait for the map to be idle (style loaded and ready)
    map.on('idle', async () => {
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
      
      // Add cluster source if it doesn't exist
      if (!map.getSource(clusterSourceId)) {
        map.addSource(clusterSourceId, {
          type: 'geojson',
          data: clusterData || { type: 'FeatureCollection', features: [] }
        });
        
        // Create the cluster layer
        createClusterLayer();
      }
      
      // Initialize clusters if we have data
      if (geojsonData && geojsonData.features && geojsonData.features.length > 0) {
        // Wrap in async function to avoid Svelte compiler issues
        (async () => {
          await updateClusters();
          updateClusterLayer();
          updateLayerVisibility();
        })();
      }
    });
    
    // Handle zoom events to update clusters
    map.on('zoom', async () => {
      if (map) {
        const newZoomLevel = Math.round(map.getZoom());
        if (newZoomLevel !== currentZoomLevel) {
          currentZoomLevel = newZoomLevel;
          await updateClusters();
          updateClusterLayer();
          updateLayerVisibility();
        }
      }
    });
  });
  
  // Update the cluster layer when data changes
  function updateClusterLayer() {
    if (map && map.isStyleLoaded()) {
      // Simple approach: just update the source data if it exists
      if (map.getSource(clusterSourceId)) {
        try {
          const dataToSet = clusterData || { type: 'FeatureCollection', features: [] };
          map.getSource(clusterSourceId).setData(dataToSet);
        } catch (error) {
          console.error(`MapView: Error updating cluster source data:`, error);
        }
      }
    }
  }
  
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
              if (feature.geometry.type === 'Point') {
                const coordinates = feature.geometry.coordinates;
                bounds.extend([coordinates[0], coordinates[1]]);
              }
            });
            map.fitBounds(bounds, { padding: 50 });
          }
        } catch (error) {
          console.error(`MapView: Error updating source data:`, error);
        }
      }
      
      // Also update cluster data
      updateClusterLayer();
      updateLayerVisibility();
    }
  }
  
  // Track previous data to prevent unnecessary updates
  let previousDataString: string | null = null;
  let previousZoomLevel: number | null = null;
  
  async function updateClusters() {
    if (!geojsonData || !geojsonData.features || geojsonData.features.length === 0) {
      clusterData = null;
      return;
    }
    
    // Create clusters based on current zoom level using worker
    const resolution = getOptimalResolution(currentZoomLevel);
    
    if (clusteringWorker) {
      try {
        clusterData = await computeClustersInWorker(clusteringWorker, geojsonData.features as any, resolution);
      } catch (error) {
        console.error('Error computing clusters in worker:', error);
        // Fallback to synchronous clustering if worker fails
        const { createTreeClusters } = await import('../../utils/h3Clustering');
        clusterData = createTreeClusters(geojsonData.features as any, resolution);
      }
    } else {
      // Fallback to synchronous clustering if worker not available
      const { createTreeClusters } = await import('../../utils/h3Clustering');
      clusterData = createTreeClusters(geojsonData.features as any, resolution);
    }
    

  }
  
  // Expose update function to parent
  export async function updateData(newData: GeoJSON.FeatureCollection | null) {
    // Performance optimization: Quick check for null/undefined
    if (!newData) {
      if (geojsonData !== null) {
        geojsonData = null;
        updateGeoJSONLayer();
      }
      return;
    }
    
    // Performance optimization: Quick length check first
    const newLength = newData.features?.length || 0;
    const currentLength = geojsonData?.features?.length || 0;
    
    // Only do expensive comparison if lengths are different or we don't have previous data
    if (newLength !== currentLength || !previousDataString) {
      geojsonData = newData;
      previousDataString = `length:${newLength}`; // Simple cache key
      updateGeoJSONLayer();
    }
    // For same length, do a lightweight check on first feature
    else if (newLength > 0 && geojsonData?.features?.[0] !== newData.features?.[0]) {
      geojsonData = newData;
      previousDataString = `length:${newLength}:${Date.now()}`; // Simple cache key with timestamp
      updateGeoJSONLayer();
    }
    
    // Update clusters after data changes
    await updateClusters();
  }
  
  // Update layer visibility based on zoom level
  function updateLayerVisibility() {
    if (!map) return;
    
    const useClusters = shouldUseClusters(currentZoomLevel);
    // Show clusters and hide individual trees at lower zoom levels
    if (useClusters) {
      if (map.getLayer(clusterLayerId)) {
        map.setLayoutProperty(clusterLayerId, 'visibility', 'visible');
      }
      if (map.getLayer(`${clusterLayerId}-outline`)) {
        map.setLayoutProperty(`${clusterLayerId}-outline`, 'visibility', 'visible');
      }
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, 'visibility', 'none');
      }
    } else {
      // Show individual trees and hide clusters at higher zoom levels

      if (map.getLayer(clusterLayerId)) {
        map.setLayoutProperty(clusterLayerId, 'visibility', 'none');
      }
      if (map.getLayer(`${clusterLayerId}-outline`)) {
        map.setLayoutProperty(`${clusterLayerId}-outline`, 'visibility', 'none');
      }
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, 'visibility', 'visible');
      }
    }
  }
  
  // Expose resize function to parent
  export function resizeMap() {
    if (map) {
      map.resize();
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
