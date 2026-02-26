import { latLngToCell, cellToBoundary, getResolution } from 'h3-js';

interface TreeFeatureProperties {
  TreeName: string;
  months: string;
  colour: string;
  prominence: string;
  months_flowering: Record<string, boolean>;
  [month: string]: boolean | string | Record<string, boolean>;
}

interface ClusterFeatureProperties {
  cluster_id: string;
  count: number;
  resolution: number;
  treeTypes: Record<string, number>;
  dominantType?: string;
  dominantColor?: string;
}

export function createTreeClusters(
  features: GeoJSON.Feature<GeoJSON.Point, TreeFeatureProperties>[],
  resolution: number = 10
): GeoJSON.FeatureCollection<GeoJSON.Polygon, ClusterFeatureProperties> {
  const clusters: Map<string, { 
    count: number; 
    treeTypes: Record<string, number>; 
    properties: TreeFeatureProperties[] 
  }> = new Map();

  // Group features by H3 index
  features.forEach(feature => {
    if (feature.geometry.type === 'Point') {
      const [longitude, latitude] = feature.geometry.coordinates;
      const h3Index = latLngToCell(latitude, longitude, resolution);
      
      if (h3Index) {
        if (!clusters.has(h3Index)) {
          clusters.set(h3Index, { 
            count: 0, 
            treeTypes: {}, 
            properties: [] 
          });
        }
        
        const cluster = clusters.get(h3Index)!;
        cluster.count++;
        
        // Track tree types for this cluster
        const treeName = feature.properties.TreeName || 'Unknown';
        cluster.treeTypes[treeName] = (cluster.treeTypes[treeName] || 0) + 1;
        
        // Store properties for calculating dominant color/type
        cluster.properties.push(feature.properties);
      }
    }
  });

  // Convert clusters to GeoJSON features
  const clusterFeatures: GeoJSON.Feature<GeoJSON.Polygon, ClusterFeatureProperties>[] = [];

  clusters.forEach((clusterData, h3Index) => {
    // Get the boundary of the H3 cell
    const boundary = cellToBoundary(h3Index, false); // Returns [lat, lng] pairs
    
    if (boundary && boundary.length > 0) {
      // Close the polygon by adding the first point at the end
      const polygonCoordinates = [...boundary, boundary[0]];
      
      // Convert [lat, lng] to [lng, lat] for GeoJSON
      const geoJsonCoordinates = polygonCoordinates.map(coord => [coord[1], coord[0]]);
      
      // Find dominant tree type and color
      let dominantType = 'Mixed';
      let dominantColor = '#cccccc';
      let maxCount = 0;
      
      for (const [treeType, count] of Object.entries(clusterData.treeTypes)) {
        if (count > maxCount) {
          maxCount = count;
          dominantType = treeType;
          // Find the color from the first occurrence of this tree type
          const matchingFeature = clusterData.properties.find(p => p.TreeName === treeType);
          if (matchingFeature?.colour) {
            dominantColor = matchingFeature.colour;
          }
        }
      }
      
      clusterFeatures.push({
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [geoJsonCoordinates]
        },
        properties: {
          cluster_id: h3Index,
          count: clusterData.count,
          resolution: getResolution(h3Index),
          treeTypes: clusterData.treeTypes,
          dominantType,
          dominantColor
        }
      });
    }
  });

  return {
    type: 'FeatureCollection',
    features: clusterFeatures
  };
}

export function getOptimalResolution(zoomLevel: number): number {
  // Use a fixed resolution of 8 for visible H3 cells
  return 8;
}

export function shouldUseClusters(zoomLevel: number): boolean {
  // Show clusters at lower zoom levels, switch to individual trees at higher zoom levels
  return zoomLevel <= 15;
}



