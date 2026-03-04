interface PrecomputedClusterProperties {
  h3_index: string;
  month: string;
  resolution: number;
  species_counts: Record<string, number>;
}

interface PrecomputedClusterFeature extends GeoJSON.Feature<GeoJSON.Polygon, PrecomputedClusterProperties> {}

let treeSpeciesColors: Record<string, string> = {};
let colorsLoaded = false;

// Export the tree species colors so they can be used by other components
export function getTreeSpeciesColors(): Record<string, string> {
  return { ...treeSpeciesColors }; // Return a copy to prevent external modification
}

export async function loadTreeSpeciesColors(): Promise<void> {
  if (colorsLoaded) return;
  
  try {
    // Load parquet file directly using hyparquet
    const { asyncBufferFromUrl, parquetReadObjects } = await import('hyparquet');
    
    // Create file object from the parquet file
    const file = await asyncBufferFromUrl({ 
      url: '/tree_species.parquet',
      fetchOptions: {
        method: 'GET'
      }
    });
    
    // Read all objects from the parquet file
    const data = await parquetReadObjects({
      file,
      columns: ['TreeName', 'colour'] // Only read the columns we need
    });
    
    // Create color mapping from the data
    for (const row of data) {
      const treeName = row.TreeName;
      const colour = row.colour;
      
      // Skip if colour is null/undefined or tree is 'Others'
      if (colour && treeName !== 'Others') {
        treeSpeciesColors[treeName] = colour;
      }
    }
    
    colorsLoaded = true;
    console.log(`Loaded ${Object.keys(treeSpeciesColors).length} tree species colors from parquet`);
    
  } catch (error) {
    console.error('Error loading tree species colors from parquet:', error);
    throw error; // Re-throw to make it clear this is required
  }
}

interface ClusterFeatureWithColor extends GeoJSON.Feature<GeoJSON.Polygon, PrecomputedClusterProperties & { dominantColor: string }> {}

export async function loadPrecomputedClusters(
  month: string,
  resolution: number
): Promise<GeoJSON.FeatureCollection<GeoJSON.Polygon, PrecomputedClusterProperties & { dominantColor: string }>> {
  // Ensure colors are loaded first
  await loadTreeSpeciesColors();
  
  try {
    // Month is already in 3-letter abbreviation format (Jan, Feb, etc.)
    // Just ensure first letter is capitalized and rest are lowercase
    const monthCapitalized = month.charAt(0).toUpperCase() + month.slice(1).toLowerCase();
    
    const filename = `h3_tree_distribution_${monthCapitalized}_resolution_${resolution}.geojson`;
    const response = await fetch(`/geojson/${filename}`);
    
    if (!response.ok) {
      throw new Error(`Failed to load precomputed clusters: ${response.status} ${response.statusText}`);
    }
    
    const featureCollection = await response.json();
    
    // Add dominantColor property to each feature
    const featuresWithColor = featureCollection.features.map(feature => {
      const clusterFeature = feature as ClusterFeatureWithColor;
      const dominantColor = getDominantColor(clusterFeature);
      
      return {
        ...feature,
        properties: {
          ...feature.properties,
          dominantColor: dominantColor
        }
      };
    });
    
    return {
      ...featureCollection,
      features: featuresWithColor
    };
  } catch (error) {
    console.error(`Error loading precomputed clusters for ${month} at resolution ${resolution}:`, error);
    throw error; // Re-throw to indicate failure
  }
}

// Function to get the dominant species color for a cluster
export function getDominantColor(feature: PrecomputedClusterFeature): string {
  const speciesCounts = feature.properties.species_counts;
  
  if (!speciesCounts || Object.keys(speciesCounts).length === 0) {
    return '#cccccc'; // Default gray color for empty clusters
  }
  
  // Find the species with the highest count
  let dominantSpecies = '';
  let maxCount = 0;
  
  for (const [species, count] of Object.entries(speciesCounts)) {
    if (count > maxCount) {
      maxCount = count;
      dominantSpecies = species;
    }
  }
  
  // Return the color for the dominant species
  // If not found in our mapping, use gray
  return treeSpeciesColors[dominantSpecies] || '#cccccc';
}

// Function to get a style function for MapLibre GL
export function getClusterStyleFunction(resolution: number): (feature: PrecomputedClusterFeature) => any {
  return function(feature: PrecomputedClusterFeature) {
    const dominantColor = getDominantColor(feature);
    
    return {
      'fill-color': dominantColor,
      'fill-opacity': 0.6,
      'fill-antialias': true
    };
  };
}