import axios from 'axios';

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

    // Check if brand exists and store the result
    try {
      const hasBrand = await brand.checkBrandExists();
      return {
        user: response.data.user,
        hasBrand
      };
    } catch (error) {
      console.error('Error checking brand:', error);
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
      console.log(data)
      const response = await api.post('/auth/brand/questionnaire', data);
      return response.data;
    } catch (error: any) {
      console.error('API Error:', error);

      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error('Response data:', error.response.data);
        console.error('Response status:', error.response.status);
        console.error('Response headers:', error.response.headers);
      } else if (error.request) {
        // The request was made but no response was received
        console.error('Request error:', error.request);
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error('Error message:', error.message);
      }

      throw error;
    }
  },

  checkBrandExists: async (): Promise<boolean> => {
    try {
      await api.get('/auth/brand/profile');
      return true;
    } catch (error) {
      if (error.response?.status === 404) {
        return false;
      }
      throw error;
    }
  },


  getProfile: async () => {
    try {
      console.log('Calling brand profile endpoint');
      const response = await api.get('/auth/brand/profile');
      console.log('Brand profile response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error in getProfile:', error);
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }
};
