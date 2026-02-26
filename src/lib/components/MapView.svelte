<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Map, NavigationControl, Popup, LngLatBounds } from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import { shouldUseClusters } from '../../utils/h3Clustering';
  import { createClusteringWorker, computeClustersInWorker } from '../../utils/workerLoader';
  import { createTreeClusters } from '../../utils/h3Clustering';

  let clusteringWorker: Worker | null = null;
  
  export let geojsonData: GeoJSON.FeatureCollection | null = null;
  
  let currentZoomLevel: number = 12;
  let clusterData10: GeoJSON.FeatureCollection | null = null;
  let clusterData9: GeoJSON.FeatureCollection | null = null;
  let clusterData8: GeoJSON.FeatureCollection | null = null;
  
  let map: Map | null = null;
  let mapContainer: HTMLDivElement;
  let sourceId: string = 'tree-data-source';
  let layerId: string = 'tree-data-layer';
  let clusterSourceId10: string = 'tree-cluster-source-10';
  let clusterLayerId10: string = 'tree-cluster-layer-10';
  let clusterSourceId9: string = 'tree-cluster-source-9';
  let clusterLayerId9: string = 'tree-cluster-layer-9';
  let clusterSourceId8: string = 'tree-cluster-source-8';
  let clusterLayerId8: string = 'tree-cluster-layer-8';
  
  interface GeoJSONFeatureProperties {
    TreeName: string;
    months: string;
    colour: string;
    prominence: string;
    months_flowering: Record<string, boolean>;
    [month: string]: boolean | string | Record<string, boolean>; // Dynamic month properties
  }
  
  // Create cluster layers for different resolutions
  function createClusterLayers() {
    if (map) {
      try {
        if (map.getSource(clusterSourceId10) && !map.getLayer(clusterLayerId10)) {
          map.addLayer({
            id: clusterLayerId10,
            type: 'fill',
            source: clusterSourceId10,
            minzoom: 14,
            maxzoom: 16,
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
        }

        if (map.getSource(clusterSourceId9) && !map.getLayer(clusterLayerId9)) {
          map.addLayer({
            id: clusterLayerId9,
            type: 'fill',
            source: clusterSourceId9,
            minzoom: 12,
            maxzoom: 14,
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
        }

        if (map.getSource(clusterSourceId8) && !map.getLayer(clusterLayerId8)) {
          map.addLayer({
            id: clusterLayerId8,
            type: 'fill',
            source: clusterSourceId8,
            minzoom: 10,
            maxzoom: 12,
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
        }

      } catch (error) {
        console.error(`MapView: Failed to add cluster layers:`, error);
        console.error('This might be due to invalid style properties or other map errors');
      }
    }
  }

  // Set up event handlers for cluster layers
  function setupClusterEventHandlers() {
    if (!map || map._clusterPopupHandlerAdded) {
      return;
    }
    
    try {
      // Check if at least one cluster layer exists
      const hasClusterLayers = map.getLayer(clusterLayerId10) || map.getLayer(clusterLayerId9) || map.getLayer(clusterLayerId8);
      
      if (hasClusterLayers) {
        const handleClusterClick = (e, layerId) => {
          const features = map.queryRenderedFeatures(e.point, {
            layers: [layerId]
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
        };
        
        // Add click handlers for all cluster layers that exist
        if (map.getLayer(clusterLayerId10)) {
          map.on('click', clusterLayerId10, (e) => handleClusterClick(e, clusterLayerId10));
        }
        if (map.getLayer(clusterLayerId9)) {
          map.on('click', clusterLayerId9, (e) => handleClusterClick(e, clusterLayerId9));
        }
        if (map.getLayer(clusterLayerId8)) {
          map.on('click', clusterLayerId8, (e) => handleClusterClick(e, clusterLayerId8));
        }
        
        // Change cursor to pointer when hovering over cluster features (mouse devices)
        const clusterLayers = [clusterLayerId10, clusterLayerId9, clusterLayerId8];
        clusterLayers.forEach(layerId => {
          if (map.getLayer(layerId)) {
            map.on('mouseenter', layerId, () => {
              map.getCanvas().style.cursor = 'pointer';
            });
            
            map.on('mouseleave', layerId, () => {
              map.getCanvas().style.cursor = '';
            });
          }
        });
        
        map._clusterPopupHandlerAdded = true;
        console.log('Cluster event handlers set up successfully');
      }
    } catch (error) {
      console.error('Error setting up cluster event handlers:', error);
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
          minzoom: 16,  // Only show individual points at zoom 16+
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
      
      // Add cluster sources if they don't exist
      if (!map.getSource(clusterSourceId10)) {
        map.addSource(clusterSourceId10, {
          type: 'geojson',
          data: clusterData10 || { type: 'FeatureCollection', features: [] }
        });
      }

      if (!map.getSource(clusterSourceId9)) {
        map.addSource(clusterSourceId9, {
          type: 'geojson',
          data: clusterData9 || { type: 'FeatureCollection', features: [] }
        });
      }

      if (!map.getSource(clusterSourceId8)) {
        map.addSource(clusterSourceId8, {
          type: 'geojson',
          data: clusterData8 || { type: 'FeatureCollection', features: [] }
        });
      }
      
      // Create the cluster layers
      createClusterLayers();
      
      // Ensure event handlers are set up for all cluster layers
      setupClusterEventHandlers();
      

      

      
      // Initialize clusters if we have data
      if (geojsonData && geojsonData.features && geojsonData.features.length > 0) {
        // Wrap in async function to avoid Svelte compiler issues
        (async () => {
          await updateClusters();
        })();
      }
    });
    
  });
  
  // Update the cluster layers when data changes
  function updateClusterLayers() {
    if (!map) {
      return;
    }
    
    if (!map.isStyleLoaded()) {
      // Try again after a short delay if style isn't loaded
      setTimeout(() => {
        updateClusterLayers();
      }, 500);
      return;
    }
    
    // Performance optimization: Only update sources if they exist and data has changed
    const source10 = map.getSource(clusterSourceId10);
    const source9 = map.getSource(clusterSourceId9);
    const source8 = map.getSource(clusterSourceId8);
    
    if (!source10 && !source9 && !source8) {
      return;
    }
  
    // Update resolution 10 cluster source
    if (source10) {
      try {
        const dataToSet = clusterData10 || { type: 'FeatureCollection', features: [] };
        source10.setData(dataToSet);
      } catch (error) {
        console.error(`MapView: Error updating cluster source 10 data:`, error);
      }
    }

    if (source9) {
      try {
        const dataToSet = clusterData9 || { type: 'FeatureCollection', features: [] };
        source9.setData(dataToSet);
      } catch (error) {
        console.error(`MapView: Error updating cluster source 9 data:`, error);
      }
    }

    // Update resolution 8 cluster source
    if (source8) {
      try {
        const dataToSet = clusterData8 || { type: 'FeatureCollection', features: [] };
        source8.setData(dataToSet);
      } catch (error) {
        console.error(`MapView: Error updating cluster source 8 data:`, error);
      }
    }
  }
  
  // Update the layer when data changes
  function updateGeoJSONLayer() {
    if (!map || !map.isStyleLoaded()) {
      return;
    }
    
    const source = map.getSource(sourceId);
    if (!source) {
      return;
    }
    
    try {
      const dataToSet = geojsonData || { type: 'FeatureCollection', features: [] };
      
      // Only update if data has actually changed
      const currentSourceData = (source as any)._data;
      if (currentSourceData !== dataToSet) {
        source.setData(dataToSet);
      }
      
    } catch (error) {
      console.error(`MapView: Error updating source data:`, error);
    }
    
    // Also update cluster data
    updateClusterLayers();
  }
  
  // Track previous data to prevent unnecessary updates
  let clustersComputedForData: string | null = null;
  
  async function updateClusters() {
    if (!geojsonData || !geojsonData.features || geojsonData.features.length === 0) {
      clusterData10 = null;
      clusterData9 = null;
      clusterData8 = null;
      clustersComputedForData = null;
      return;
    }
    
    // Performance optimization: Only recompute clusters if data has actually changed
    // Since clusters only change when month selection changes, we can use a simple cache key
    const currentDataKey = `${geojsonData.features.length}-${geojsonData.features[0]?.properties?.TreeName || 'unknown'}`;
    
    if (currentDataKey === clustersComputedForData) {
      // Clusters already computed for this data, no need to recompute
      return;
    }
    
    // Create clusters at both resolutions
    try {
      const features = geojsonData.features as any;
      
      // Always use worker if available for better performance
      if (clusteringWorker) {
        try {
          const clusterResults = await computeClustersInWorker(clusteringWorker, features, [10, 9, 8]);
          
          clusterData10 = clusterResults[10];
          clusterData9 = clusterResults[9];
          clusterData8 = clusterResults[8];
          
          // Check if worker produced valid results
          const hasValidResults = (clusterResults[10]?.features?.length || 0) > 0 ||
                                 (clusterResults[9]?.features?.length || 0) > 0 ||
                                 (clusterResults[8]?.features?.length || 0) > 0;
          
          if (!hasValidResults) {
            console.warn('Worker clustering produced empty results, falling back to main thread');
            // Fallback to main thread if worker produced empty results
            clusterData10 = createTreeClusters(features, 10);
            clusterData9 = createTreeClusters(features, 9);
            clusterData8 = createTreeClusters(features, 8);
          }
        } catch (workerError) {
          console.error('Worker clustering failed, falling back to main thread:', workerError);
          // Fallback to main thread if worker fails
          clusterData10 = createTreeClusters(features, 10);
          clusterData9 = createTreeClusters(features, 9);
          clusterData8 = createTreeClusters(features, 8);
        }
      } else {
        // Fallback to main thread if worker not available
        console.log('Using main thread for clustering');
        clusterData10 = createTreeClusters(features, 10);
        clusterData9 = createTreeClusters(features, 9);
        clusterData8 = createTreeClusters(features, 8);
      }
      
      // Mark that we've computed clusters for this data
      clustersComputedForData = currentDataKey;
      
      // Update the cluster layers with the new data
      updateClusterLayers();
      
      // Ensure event handlers are set up after cluster data is updated
      setupClusterEventHandlers();
      

    } catch (error) {
      console.error('Error computing clusters:', error);
    }
  }
  
  // Expose update function to parent
  export async function updateData(newData: GeoJSON.FeatureCollection | null) {
    // Performance optimization: Quick check for null/undefined
    if (!newData) {
      if (geojsonData !== null) {
        geojsonData = null;
        clustersComputedForData = null;
        updateGeoJSONLayer();
      }
      return;
    }
    
    // Performance optimization: Quick reference check first
    if (geojsonData === newData) {
      // Same data object reference, no need to update
      return;
    }

    // For data changes, update immediately and recompute clusters
    geojsonData = newData;
    clustersComputedForData = null; // Reset cluster cache since data changed
    updateGeoJSONLayer();

    // Update clusters after data changes
    await updateClusters();
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
