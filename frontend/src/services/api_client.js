// API Client for Todo AI Chatbot
// Handles communication with the backend API

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Chat endpoint
  async sendMessage(message, conversationId = null) {
    const body = {
      message: message,
    };
    
    if (conversationId) {
      body.conversation_id = conversationId;
    }
    
    return this.request('/chat', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // Task endpoints
  async getTasks(status = null) {
    let url = '/tasks';
    if (status) {
      url += `?status=${status}`;
    }
    return this.request(url, {
      method: 'GET',
    });
  }

  async createTask(title, description = null) {
    const body = {
      title: title,
    };
    
    if (description) {
      body.description = description;
    }
    
    return this.request('/tasks', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async updateTask(taskId, updates) {
    return this.request(`/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteTask(taskId) {
    return this.request(`/tasks/${taskId}`, {
      method: 'DELETE',
    });
  }

  async completeTask(taskId) {
    return this.request(`/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify({ status: 'completed' }),
    });
  }

  // Authentication endpoints
  async login(username, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async register(username, email, password) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  }
}

export default new ApiClient();