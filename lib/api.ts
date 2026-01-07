import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface Student {
  id: number
  nameplz: string // Changed from 'name' to 'nameplz'
  email: string | null
  created_at: string | null
}

export interface StudentUpdate {
    nameplz?: string; // Changed from 'name' to 'nameplz'
    email?: string;
}

export interface StudentClass {
  id: number
  student_id: number
  class_name: string
  class_code: string
  semester: string
  status: 'pending' | 'in-progress' | 'completed'
  priority: 'low' | 'medium' | 'high'
  description: string | null
  due_date: string | null
  created_at: string
}

export interface DashboardStats {
  total_students: number
  total_classes: number
  by_status: {
    pending: number
    in_progress: number
    completed: number
  }
}

// API Functions
export const studentApi = {
  getAll: () => api.get<Student[]>('/students/').then(res => res.data),
  getOne: (id: number) => api.get<Student>(`/students/${id}`).then(res => res.data),
  create: (data: { nameplz: string; email: string }) => // Changed from 'name' to 'nameplz'
    api.post<Student>('/students/', data).then(res => res.data),
  update: (id: number, data: StudentUpdate) => 
    api.patch<Student>(`/students/${id}`, data).then(res => res.data),
  delete: (id: number) => api.delete(`/students/${id}`),
}

export const classApi = {
  getAll: () => api.get<StudentClass[]>('/classes/').then(res => res.data),
  getOne: (id: number) => api.get<StudentClass>(`/classes/${id}`).then(res => res.data),
  create: (data: any) => api.post<StudentClass>('/classes/', data).then(res => res.data),
  update: (id: number, data: any) => 
    api.patch<StudentClass>(`/classes/${id}`, data).then(res => res.data),
  delete: (id: number) => api.delete(`/classes/${id}`),
}

export const dashboardApi = {
  getStats: () => api.get<DashboardStats>('/dashboard').then(res => res.data),
  getHealth: () => api.get('/health').then(res => res.data),
}