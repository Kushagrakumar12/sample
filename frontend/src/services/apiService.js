import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Train Management
  getTrains: (params = {}) => api.get('/trains', { params }),
  getTrain: (id) => api.get(`/trains/${id}`),
  createTrain: (data) => api.post('/trains', data),
  updateTrain: (id, data) => api.put(`/trains/${id}`, data),
  deleteTrain: (id) => api.delete(`/trains/${id}`),
  getTrainStatus: (id) => api.get(`/trains/${id}/status`),
  getTrainPositions: (id, limit = 10) => api.get(`/trains/${id}/position`, { params: { limit } }),

  // Track Management
  getTracks: (params = {}) => api.get('/tracks', { params }),
  getTrack: (id) => api.get(`/tracks/${id}`),
  createTrack: (data) => api.post('/tracks', data),
  getTrackSignals: (id) => api.get(`/tracks/${id}/signals`),
  getTrackCapacity: (id) => api.get(`/tracks/${id}/capacity`),
  createSignal: (data) => api.post('/tracks/signals', data),
  updateSignalState: (id, state) => api.put(`/tracks/signals/${id}/state`, { new_state: state }),

  // Schedule Management
  getSchedules: (params = {}) => api.get('/schedules', { params }),
  getSchedule: (id) => api.get(`/schedules/${id}`),
  createSchedule: (data) => api.post('/schedules', data),
  recordDeparture: (id, time) => api.put(`/schedules/${id}/departure`, { departure_time: time }),
  recordArrival: (id, time) => api.put(`/schedules/${id}/arrival`, { arrival_time: time }),
  getPerformanceAnalytics: (params = {}) => api.get('/schedules/analytics/performance', { params }),

  // Optimization
  optimizeSchedule: (data) => api.post('/optimization/schedule', data),
  detectConflicts: (timeHorizon = 4) => api.post('/optimization/conflicts/detect', { time_horizon_hours: timeHorizon }),
  resolveConflicts: (conflicts) => api.post('/optimization/conflicts/resolve', { conflicts }),
  optimizeRoutes: (trainIds) => api.post('/optimization/routes/optimize', { train_ids: trainIds }),
  getRecommendations: (params = {}) => api.get('/optimization/recommendations', { params }),
  getOptimizationResults: (params = {}) => api.get('/optimization/results', { params }),

  // System Health
  getSystemHealth: () => api.get('/health'),
  getSystemInfo: () => api.get('/'),

  // WebSocket connection info
  getWebSocketUrl: () => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = process.env.REACT_APP_WS_URL || 'localhost:8000';
    return `${wsProtocol}//${wsHost}/ws`;
  },
};

// Utility functions
export const apiUtils = {
  // Format error messages for display
  formatError: (error) => {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.message) {
      return error.message;
    }
    return 'An unexpected error occurred';
  },

  // Check if API is available
  checkHealth: async () => {
    try {
      await apiService.getSystemHealth();
      return true;
    } catch (error) {
      return false;
    }
  },

  // Generate mock data for development
  generateMockTrains: (count = 5) => {
    const trainTypes = ['passenger', 'freight', 'express', 'local'];
    const priorities = ['low', 'medium', 'high', 'critical'];
    const operators = ['National Rail', 'Express Line', 'Freight Corp', 'Metro Transit'];
    
    return Array.from({ length: count }, (_, i) => ({
      id: i + 1,
      number: `T${String(i + 1).padStart(3, '0')}`,
      name: `Train ${i + 1}`,
      train_type: trainTypes[Math.floor(Math.random() * trainTypes.length)],
      priority: priorities[Math.floor(Math.random() * priorities.length)],
      max_speed_kmh: 80 + Math.floor(Math.random() * 80),
      length_meters: 150 + Math.floor(Math.random() * 150),
      capacity_passengers: Math.floor(Math.random() * 500),
      weight_tons: 50 + Math.floor(Math.random() * 200),
      operator: operators[Math.floor(Math.random() * operators.length)],
      is_active: Math.random() > 0.2,
      created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
    }));
  },

  generateMockTracks: (count = 3) => {
    const stations = ['Station A', 'Station B', 'Station C', 'Station D', 'Central Hub'];
    
    return Array.from({ length: count }, (_, i) => ({
      id: i + 1,
      name: `Track ${String.fromCharCode(65 + i)}`,
      start_station: stations[Math.floor(Math.random() * stations.length)],
      end_station: stations[Math.floor(Math.random() * stations.length)],
      length_km: 20 + Math.floor(Math.random() * 80),
      gradient: Math.random() * 3,
      max_speed_kmh: 80 + Math.floor(Math.random() * 80),
      capacity: 1 + Math.floor(Math.random() * 3),
      is_electrified: Math.random() > 0.3,
      maintenance_schedule: Math.random() > 0.5 ? 'Weekly maintenance on Sundays' : null,
      created_at: new Date().toISOString()
    }));
  },

  generateMockSchedules: (count = 10) => {
    const statuses = ['scheduled', 'running', 'delayed', 'completed', 'cancelled'];
    
    return Array.from({ length: count }, (_, i) => {
      const departureTime = new Date(Date.now() + (i - 5) * 2 * 60 * 60 * 1000);
      const arrivalTime = new Date(departureTime.getTime() + (1 + Math.random() * 3) * 60 * 60 * 1000);
      const status = statuses[Math.floor(Math.random() * statuses.length)];
      
      return {
        id: i + 1,
        train_id: Math.floor(Math.random() * 5) + 1,
        track_id: Math.floor(Math.random() * 3) + 1,
        scheduled_departure: departureTime.toISOString(),
        scheduled_arrival: arrivalTime.toISOString(),
        actual_departure: status === 'running' || status === 'completed' ? 
          new Date(departureTime.getTime() + (Math.random() - 0.5) * 30 * 60 * 1000).toISOString() : null,
        actual_arrival: status === 'completed' ? 
          new Date(arrivalTime.getTime() + (Math.random() - 0.5) * 30 * 60 * 1000).toISOString() : null,
        status: status,
        delay_minutes: Math.floor((Math.random() - 0.7) * 30),
        notes: Math.random() > 0.7 ? 'Weather delay' : null,
        created_at: new Date().toISOString()
      };
    });
  }
};

export default apiService;