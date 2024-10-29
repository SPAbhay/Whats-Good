import axios, { AxiosError } from 'axios'; // Import AxiosError

const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const auth = {
  signup: async (data: { name: string; email: string; password: string }) => {
    const response = await api.post('/auth/signup', data);
    localStorage.setItem('token', response.data.access_token);
    return response.data.user;
  },

  login: async (data: { email: string; password: string }) => {
    const response = await api.post('/auth/login', data);
    localStorage.setItem('token', response.data.access_token);

    try {
      const hasBrand = await brand.checkBrandExists();
      return {
        user: response.data.user,
        hasBrand
      };
    } catch (error: unknown) { // Change to unknown
      const axiosError = error as AxiosError; // Cast to AxiosError
      console.error('Error checking brand:', axiosError);
      return {
        user: response.data.user,
        hasBrand: false
      };
    }
  },

  logout: () => {
    localStorage.removeItem('token');
  },

  getProfile: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  }
};

export const brand = {
  submitQuestionnaire: async (data: {
    raw_brand_name: string;
    raw_industry_focus: string;
    raw_target_audience: string;
    raw_unique_value: string;
    raw_social_platforms?: string;
    raw_successful_content?: string;
  }) => {
    try {
      const response = await api.post('/auth/brand/questionnaire', data);
      return response.data;
    } catch (error: unknown) { // Change to unknown
      const axiosError = error as AxiosError; // Cast to AxiosError

      console.error('API Error:', axiosError);
      if (axiosError.response) {
        console.error('Response data:', axiosError.response.data);
        console.error('Response status:', axiosError.response.status);
        console.error('Response headers:', axiosError.response.headers);
      } else if (axiosError.request) {
        console.error('Request error:', axiosError.request);
      } else {
        console.error('Error message:', axiosError.message);
      }

      throw error; // Optionally, you might want to throw a specific error type here
    }
  },

  checkBrandExists: async (): Promise<boolean> => {
    try {
      await api.get('/auth/brand/profile');
      return true;
    } catch (error: unknown) { // Change to unknown
      const axiosError = error as AxiosError; // Cast to AxiosError

      if (axiosError.response?.status === 404) {
        return false;
      }
      throw error;
    }
  },

  getProfile: async () => {
    try {
      const response = await api.get('/auth/brand/profile');
      return response.data;
    } catch (error: unknown) { // Change to unknown
      const axiosError = error as AxiosError; // Cast to AxiosError

      console.error('Error in getProfile:', axiosError);
      if (axiosError.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }
};
