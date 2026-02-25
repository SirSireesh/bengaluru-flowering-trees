// Data loading worker - handles fetching and processing GeoJSON data
interface DataLoaderMessage {
  type: 'load_geojson';
  month: string;
}

interface DataLoaderResponse {
  type: 'geojson_loaded';
  data: GeoJSON.FeatureCollection | null;
  error: string | null;
}

self.onmessage = async function(e: MessageEvent<DataLoaderMessage>) {
  if (e.data.type === 'load_geojson') {
    try {
      const { month } = e.data;
      const monthUpper = month.toUpperCase();
      const filename = `trees_${monthUpper}.geojson`;
      
      // Fetch the GeoJSON file
      const response = await fetch(`/geojson/${filename}`);
      
      if (!response.ok) {
        throw new Error(`Failed to load ${month} GeoJSON: ${response.status} ${response.statusText}`);
      }
      
      const data: GeoJSON.FeatureCollection = await response.json();
      
      const responseMessage: DataLoaderResponse = {
        type: 'geojson_loaded',
        data: data,
        error: null
      };
      self.postMessage(responseMessage);
      
    } catch (error) {
      const responseMessage: DataLoaderResponse = {
        type: 'geojson_loaded',
        data: null,
        error: error instanceof Error ? error.message : 'Unknown error loading GeoJSON'
      };
      self.postMessage(responseMessage);
    }
  }
};