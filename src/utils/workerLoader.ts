export function createClusteringWorker(): Worker {
  // Check if we're in development or production
  const isProduction = import.meta.env.PROD;
  
  if (isProduction) {
    // In production, the worker is copied to the assets folder
    return new Worker('/assets/h3ClusteringWorker.ts', { type: 'module' });
  } else {
    // In development, we need to use the source file directly
    // Note: This might need adjustment based on your dev server setup
    return new Worker(new URL('../utils/h3ClusteringWorker.ts', import.meta.url), { type: 'module' });
  }
}

export function createDataLoaderWorker(): Worker {
  // Check if we're in development or production
  const isProduction = import.meta.env.PROD;
  
  if (isProduction) {
    // In production, the worker is copied to the assets folder
    return new Worker('/assets/dataLoaderWorker.ts', { type: 'module' });
  } else {
    // In development, we need to use the source file directly
    // Note: This might need adjustment based on your dev server setup
    return new Worker(new URL('../utils/dataLoaderWorker.ts', import.meta.url), { type: 'module' });
  }
}

interface ClusterWorkerMessage {
  type: 'cluster';
  features: any[];
  resolution: number;
}

interface ClusterWorkerResponse {
  type: 'cluster_result';
  data: GeoJSON.FeatureCollection<GeoJSON.Polygon, any>;
}

interface DataLoaderMessage {
  type: 'load_geojson';
  month: string;
}

interface DataLoaderResponse {
  type: 'geojson_loaded';
  data: GeoJSON.FeatureCollection | null;
  error: string | null;
}

export function computeClustersInWorker(
  worker: Worker,
  features: any[],
  resolution: number
): Promise<GeoJSON.FeatureCollection<GeoJSON.Polygon, any>> {
  return new Promise((resolve, reject) => {
    // Set up message handler
    const messageHandler = (e: MessageEvent<ClusterWorkerResponse>) => {
      if (e.data.type === 'cluster_result') {
        worker.removeEventListener('message', messageHandler);
        worker.removeEventListener('error', errorHandler);
        resolve(e.data.data);
      }
    };
    
    const errorHandler = (e: ErrorEvent) => {
      worker.removeEventListener('message', messageHandler);
      worker.removeEventListener('error', errorHandler);
      reject(e.error);
    };
    
    worker.addEventListener('message', messageHandler);
    worker.addEventListener('error', errorHandler);
    
    // Send the clustering request
    const message: ClusterWorkerMessage = {
      type: 'cluster',
      features,
      resolution
    };
    worker.postMessage(message);
  });
}

export function loadGeoJSONInWorker(
  worker: Worker,
  month: string
): Promise<{ data: GeoJSON.FeatureCollection | null; error: string | null }> {
  return new Promise((resolve, reject) => {
    // Set up message handler
    const messageHandler = (e: MessageEvent<DataLoaderResponse>) => {
      if (e.data.type === 'geojson_loaded') {
        worker.removeEventListener('message', messageHandler);
        worker.removeEventListener('error', errorHandler);
        resolve({ data: e.data.data, error: e.data.error });
      }
    };
    
    const errorHandler = (e: ErrorEvent) => {
      worker.removeEventListener('message', messageHandler);
      worker.removeEventListener('error', errorHandler);
      reject(e.error);
    };
    
    worker.addEventListener('message', messageHandler);
    worker.addEventListener('error', errorHandler);
    
    // Send the data loading request
    const message: DataLoaderMessage = {
      type: 'load_geojson',
      month
    };
    worker.postMessage(message);
  });
}