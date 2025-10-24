/**
 * API client for Starlit Stories backend
 */

import axios from 'axios';

// Base URL for the API - defaults to local development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for story generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface StoryRequest {
  user_input: string;
  length_tier?: 'short' | 'medium' | 'long';
  thread_id?: string; // For maintaining conversation history
}

export interface StoryResponse {
  success: boolean;
  story: string;
  title: string;
  moral: string;
  error?: string;
  thread_id: string; // Thread ID returned from backend
}

/**
 * Generate a story from the backend
 * @param request - Story request with user input
 * @returns Promise with story response
 */
export const generateStory = async (request: StoryRequest): Promise<StoryResponse> => {
  try {
    const response = await apiClient.post<StoryResponse>('/generate_story', request);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      // Network error or API error
      const errorMessage = error.response?.data?.detail || error.message;
      throw new Error(`Failed to generate story: ${errorMessage}`);
    }
    throw error;
  }
};

/**
 * Get example story prompts
 * @returns Promise with array of example prompts
 */
export const getExamples = async (): Promise<string[]> => {
  try {
    const response = await apiClient.get<{ examples: string[] }>('/examples');
    return response.data.examples;
  } catch (error) {
    console.error('Failed to fetch examples:', error);
    return [
      "Tell me a story about a brave little mouse",
      "I want to hear about a friendly dragon who loves to bake",
      "Create a story about a curious star exploring the night sky"
    ];
  }
};

/**
 * Health check for the API
 * @returns Promise with health status
 */
export const healthCheck = async (): Promise<boolean> => {
  try {
    const response = await apiClient.get('/health');
    return response.data.status === 'healthy';
  } catch (error) {
    return false;
  }
};
