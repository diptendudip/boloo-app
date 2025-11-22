/**
 * API client for Boloo backend
 */

import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  requestOTP: async (email: string) => {
    const response = await api.post('/v1/auth/otp/request', { email });
    return response.data;
  },
  verifyOTP: async (email: string, otp_code: string) => {
    const response = await api.post('/v1/auth/otp/verify', { email, otp_code });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
  getUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },
};

// Cases API
export const casesAPI = {
  list: async (filters?: any) => {
    const response = await api.get('/v1/cases', { params: filters });
    return response.data;
  },
  get: async (id: string) => {
    const response = await api.get(`/v1/cases/${id}`);
    return response.data;
  },
  create: async (data: any) => {
    const response = await api.post('/v1/cases', data);
    return response.data;
  },
  update: async (id: string, data: any) => {
    const response = await api.patch(`/v1/cases/${id}`, data);
    return response.data;
  },
};

// Entities API
export const entitiesAPI = {
  list: async () => {
    const response = await api.get('/v1/entities');
    return response.data;
  },
  get: async (id: string) => {
    const response = await api.get(`/v1/entities/${id}`);
    return response.data;
  },
};

// Taxonomies API
export const taxonomiesAPI = {
  list: async (type?: string) => {
    const params = type ? { type } : {};
    const response = await api.get('/v1/taxonomies', { params });
    return response.data;
  },
};

// Admin API
export const adminAPI = {
  getStats: async () => {
    const response = await api.get('/v1/admin/stats');
    return response.data;
  },
};

// Monitoring API
export const monitoringAPI = {
  health: async () => {
    const response = await api.get('/v1/monitoring/health');
    return response.data;
  },
  metrics: async () => {
    const response = await api.get('/v1/monitoring/metrics');
    return response.data;
  },
};

// Health check (no auth required)
export const healthCheck = async () => {
  const response = await axios.get(`${API_URL}/health`);
  return response.data;
};
