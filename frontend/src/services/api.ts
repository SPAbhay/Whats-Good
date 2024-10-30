import axios, { AxiosError } from 'axios';
import { config } from '../config';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

console.log('API_URL:', API_URL);

// Use config for API_URL
const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

// Add better typing for config in interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add interfaces for better type safety
interface User {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

interface BrandQuestionnaire {
  raw_brand_name: string;
  raw_industry_focus: string;
  raw_target_audience: string;
  raw_unique_value: string;
  raw_social_platforms?: string;
  raw_successful_content?: string;
}

export const auth = {
  signup: async (data: { name: string; email: string; password: string }): Promise<User> => {
    const response = await api.post<AuthResponse>('/auth/signup', data);
    localStorage.setItem('token', response.data.access_token);
    return response.data.user;
  },

  login: async (data: { email: string; password: string }) => {
    const response = await api.post<AuthResponse>('/auth/login', data);
    localStorage.setItem('token', response.data.access_token);

    try {
      const hasBrand = await brand.checkBrandExists();
      return {
        user: response.data.user,
        hasBrand
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {  // Better error checking
        console.error('Error checking brand:', error.response?.data || error.message);
      }
      return {
        user: response.data.user,
        hasBrand: false
      };
    }
  },

  logout: () => {
    localStorage.removeItem('token');
  },

  getProfile: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  }
};

export const brand = {
  submitQuestionnaire: async (data: BrandQuestionnaire) => {
    try {
      const response = await api.post('/auth/brand/questionnaire', data);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('API Error:', error.message);
        if (error.response) {
          console.error('Response:', {
            data: error.response.data,
            status: error.response.status,
            headers: error.response.headers
          });
        }
        throw new Error(error.response?.data?.detail || error.message);
      }
      throw error;
    }
  },

  checkBrandExists: async (): Promise<boolean> => {
    try {
      await api.get('/auth/brand/profile');
      return true;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return false;
      }
      throw error;
    }
  },

  getProfile: async () => {
    try {
      console.log('Fetching brand profile...');
      const response = await api.get('/auth/brand/profile');
      console.log('Brand profile response:', response.data);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Error in getProfile:', error.message);
        if (error.response?.status === 404) {
          return null;
        }
        throw new Error(error.response?.data?.detail || error.message);
      }
      throw error;
    }
  }
};

// Add error handler to api instance
api.interceptors.response.use(
  response => response,
  error => {
    if (axios.isAxiosError(error)) {
      // Handle token expiration
      if (error.response?.status === 401) {
        auth.logout();
        window.location.href = '/login';
      }
      // Log errors in development
      if (config.ENV === 'development') {
        console.error('API Error:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        });
      }
    }
    return Promise.reject(error);
  }
);

export { api as default };