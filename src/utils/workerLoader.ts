export function createClusteringWorker(): Worker {
  // Use Vite's worker import syntax - this will be handled correctly in both dev and prod
  const worker = new Worker(new URL('../utils/h3ClusteringWorker.ts?worker', import.meta.url), { type: 'module' });
  return worker;
}

export function createDataLoaderWorker(): Worker {
  // Use Vite's worker import syntax - this will be handled correctly in both dev and prod
  const worker = new Worker(new URL('../utils/dataLoaderWorker.ts?worker', import.meta.url), { type: 'module' });
  return worker;
}

interface ClusterWorkerMessage {
  type: 'cluster';
  features: any[];
  resolutions: number[];
}

interface ClusterWorkerResponse {
  type: 'cluster_result';
  data: Record<number, GeoJSON.FeatureCollection<GeoJSON.Polygon, any>>;
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
  resolutions: number[]
): Promise<Record<number, GeoJSON.FeatureCollection<GeoJSON.Polygon, any>>> {
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
      resolutions
    };
    worker.postMessage(message);
  });
}

// Backward compatibility function for single resolution
export function computeClustersInWorkerSingle(
  worker: Worker,
  features: any[],
  resolution: number
): Promise<GeoJSON.FeatureCollection<GeoJSON.Polygon, any>> {
  return computeClustersInWorker(worker, features, [resolution])
    .then(results => results[resolution]);
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