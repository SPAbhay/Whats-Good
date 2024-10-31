import axios from 'axios';
import { config } from '../config';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

console.log('API_URL:', API_URL);

// Create Axios instance
const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

// Request interceptor to attach Authorization token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interfaces for type safety
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

// Auth functions
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
      if (axios.isAxiosError(error)) {
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

// Brand functions
export const brand = {
  submitQuestionnaire: async (data: BrandQuestionnaire) => {
  try {
    console.log('Submitting questionnaire with data:', data);
    const response = await api.post('/auth/brand/questionnaire', data);
    console.log('Questionnaire submission response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Questionnaire submission error:', error);
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
    console.log('Raw brand data:', response.data);
    // Check if processed fields exist
    const hasProcessedFields = response.data.processed_brand_name ||
                             response.data.processed_industry ||
                             response.data.processed_target_audience;
    console.log('Has processed fields:', hasProcessedFields);
    return response.data;
  } catch (error) {
    console.error('Brand profile error:', error);
    throw error;
  }
}
};

// Response interceptor for error handling
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

export interface RecommendedArticle {
  article_id: string;
  title: string;
  summarized_content: string;
  category: string;
  topic_1?: string;
  topic_2?: string;
  topic_3?: string;
  topic_4?: string;
  topic_5?: string;
  score: number;
  retrieval_strategy: string;
  matched_aspects: string[];
}

export interface ArticleFeedback {
  article_id: string;
  brand_id: number;
  is_relevant: boolean;
  feedback_type: string;
}

export const getRecommendedArticles = async (brandId: number, limit: number = 5): Promise<RecommendedArticle[]> => {
  try {
    const response = await fetch(`/api/articles/recommended/${brandId}?limit=${limit}`);
    const data = await response.json();
    return data.articles;
  } catch (error) {
    console.error('Error fetching recommended articles:', error);
    return [];
  }
};

export const submitArticleFeedback = async (feedback: ArticleFeedback): Promise<boolean> => {
  try {
    const response = await fetch('/api/articles/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(feedback),
    });
    return response.ok;
  } catch (error) {
    console.error('Error submitting feedback:', error);
    return false;
  }
};