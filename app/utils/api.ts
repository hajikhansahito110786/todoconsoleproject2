// app/utils/api.ts
"use client";

// Helper function to make API calls with user email
export async function fetchWithUserEmail(
  url: string,
  options: RequestInit = {},
  userEmail: string = ''
): Promise<Response> {
  const headers = {
    ...options.headers,
    'Content-Type': 'application/json',
    ...(userEmail && { 'x-user-email': userEmail }),
  };

  return fetch(url, {
    ...options,
    headers,
  });
}

// Specific API functions
export const api = {
  // Students
  createStudent: (data: any, userEmail: string) =>
    fetchWithUserEmail('http://localhost:8000/students/', {
      method: 'POST',
      body: JSON.stringify(data),
    }, userEmail),
  
  updateStudent: (id: number, data: any, userEmail: string) =>
    fetchWithUserEmail(`http://localhost:8000/students/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, userEmail),
  
  // Todos
  createTodo: (data: any, userEmail: string) =>
    fetchWithUserEmail('http://localhost:8000/todos/', {
      method: 'POST',
      body: JSON.stringify(data),
    }, userEmail),
  
  updateTodo: (id: number, data: any, userEmail: string) =>
    fetchWithUserEmail(`http://localhost:8000/todos/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, userEmail),
  
  deleteTodo: (id: number, userEmail: string) =>
    fetchWithUserEmail(`http://localhost:8000/todos/${id}`, {
      method: 'DELETE',
    }, userEmail),
  
  // Get data (no email needed for GET)
  getStudents: () => fetch('http://localhost:8000/students/'),
  getTodos: () => fetch('http://localhost:8000/todos/'),
};