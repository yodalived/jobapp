// API client utilities for frontend-backend integration

export interface User {
  id: number;
  email: string;
  email_verified: boolean;
  subscription_tier: string;
  applications_count: number;
  resumes_generated_count: number;
  created_at: string;
}

export interface JobApplication {
  id: number;
  company: string;
  position: string;
  url: string;
  status: string;
  location?: string;
  remote: boolean;
  salary_min?: number;
  salary_max?: number;
  job_description?: string;
  created_at: string;
  updated_at: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface JobAnalysis {
  requirements: string[];
  skills: string[];
  company_info: Record<string, string>;
  match_score?: number;
}

export interface ResumeGenerationResponse {
  pdf_url?: string;
  latex_source?: string;
  job_id: number;
  template: string;
  status: string;
}

class ApiClient {
  private baseUrl = '/api/v1';
  private token: string | null = null;

  constructor() {
    // Get token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return { error: data.detail || 'Request failed' };
      }

      return { data };
    } catch (error) {
      console.error('API request failed:', error);
      return { error: 'Network error' };
    }
  }

  // Authentication
  async login(email: string, password: string): Promise<ApiResponse<{ access_token: string }>> {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (response.ok) {
      this.token = data.access_token;
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', this.token!);
      }
      return { data };
    }

    return { error: data.detail || 'Login failed' };
  }

  async register(email: string, password: string): Promise<ApiResponse<User>> {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request('/auth/me');
  }

  async logout() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  // Job Applications
  async getApplications(): Promise<ApiResponse<JobApplication[]>> {
    return this.request('/applications/');
  }

  async createApplication(application: Partial<JobApplication>): Promise<ApiResponse<JobApplication>> {
    return this.request('/applications/', {
      method: 'POST',
      body: JSON.stringify(application),
    });
  }

  async updateApplication(id: number, updates: Partial<JobApplication>): Promise<ApiResponse<JobApplication>> {
    return this.request(`/applications/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deleteApplication(id: number): Promise<ApiResponse<void>> {
    return this.request(`/applications/${id}`, {
      method: 'DELETE',
    });
  }

  // Generator/AI
  async getAvailableProviders(): Promise<ApiResponse<{ available_providers: string[]; default_provider: string; configured: Record<string, boolean> }>> {
    return this.request('/generator/llm-providers');
  }

  async analyzeJob(jobDescription: string): Promise<ApiResponse<JobAnalysis>> {
    return this.request(`/generator/analyze-job?job_description=${encodeURIComponent(jobDescription)}`, {
      method: 'POST',
    });
  }

  async generateResume(jobId: number, template: string = 'modern_professional'): Promise<ApiResponse<ResumeGenerationResponse>> {
    return this.request(`/generator/generate-resume?job_id=${jobId}&template=${template}`, {
      method: 'POST',
    });
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; services: Record<string, string> }>> {
    const response = await fetch('/health');
    if (response.ok) {
      const data = await response.json();
      return { data };
    }
    return { error: 'Health check failed' };
  }

  // Test user deletion
  async deleteTestUser(email: string): Promise<ApiResponse<{ message: string }>> {
    return this.request(`/auth/delete-test-user?email=${encodeURIComponent(email)}`, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient();