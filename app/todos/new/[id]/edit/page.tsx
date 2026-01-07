"use client";

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';

interface Todo {
  id: number;
  title: string;
  description: string | null;
  priority: 'low' | 'medium' | 'high';
  status: 'todo' | 'in_progress' | 'done';
  due_date: string | null;
  student_id: number | null;
  created_at: string;
  completed_at: string | null;
}

interface Student {
  id: number;
  name: string;
  email: string;
}

export default function EditTodoPage() {
  const router = useRouter();
  const params = useParams();
  const todoId = params.id;
  
  const [todo, setTodo] = useState<Todo | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high',
    status: 'todo' as 'todo' | 'in_progress' | 'done',
    due_date: '',
    student_id: '' as string | number
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (todoId) {
      fetchData();
    }
  }, [todoId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [todoRes, studentsRes] = await Promise.all([
        fetch(`http://localhost:8000/todos/${todoId}`),
        fetch('http://localhost:8000/students/')
      ]);
      
      if (!todoRes.ok) throw new Error('Todo not found');
      if (!studentsRes.ok) throw new Error('Failed to fetch students');
      
      const todoData: Todo = await todoRes.json();
      const studentsData = await studentsRes.json();
      
      setTodo(todoData);
      setStudents(studentsData);
      
      // Format data for form
      setFormData({
        title: todoData.title,
        description: todoData.description || '',
        priority: todoData.priority,
        status: todoData.status,
        due_date: todoData.due_date ? todoData.due_date.split('T')[0] + 'T' + todoData.due_date.split('T')[1].substring(0, 5) : '',
        student_id: todoData.student_id || ''
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      const todoData = {
        ...formData,
        student_id: formData.student_id ? parseInt(formData.student_id as string) : null,
        due_date: formData.due_date || null
      };

      const response = await fetch(`http://localhost:8000/todos/${todoId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(todoData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update todo');
      }

      router.push('/todos');
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update todo');
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleMarkComplete = async () => {
    if (!confirm('Mark this todo as complete?')) return;
    
    try {
      const response = await fetch(`http://localhost:8000/todos/${todoId}/complete`, {
        method: 'PUT',
      });
      
      if (!response.ok) throw new Error('Failed to mark todo as complete');
      
      router.push('/todos');
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update todo');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-2xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading todo data...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Edit Todo</h1>
          <p className="text-gray-600 mt-2">Update task information</p>
        </div>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}
        
        <div className="bg-white rounded-xl shadow p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority *
                </label>
                <select
                  name="priority"
                  value={formData.priority}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status *
                </label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="todo">Todo</option>
                  <option value="in_progress">In Progress</option>
                  <option value="done">Done</option>
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Due Date
                </label>
                <input
                  type="datetime-local"
                  name="due_date"
                  value={formData.due_date}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Assign to Student
                </label>
                <select
                  name="student_id"
                  value={formData.student_id}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">No student assigned</option>
                  {students.map(student => (
                    <option key={student.id} value={student.id}>
                      {student.name} ({student.email})
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            {todo && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-700 mb-2">Todo Information</h3>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>Created: {new Date(todo.created_at).toLocaleString()}</p>
                  {todo.completed_at && (
                    <p>Completed: {new Date(todo.completed_at).toLocaleString()}</p>
                  )}
                  <p>Todo ID: {todo.id}</p>
                </div>
              </div>
            )}
            
            <div className="flex space-x-4 pt-6">
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50"
              >
                {submitting ? 'Updating...' : 'Update Todo'}
              </button>
              
              {todo?.status !== 'done' && (
                <button
                  type="button"
                  onClick={handleMarkComplete}
                  className="px-6 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition duration-200"
                >
                  Mark Complete
                </button>
              )}
              
              <button
                type="button"
                onClick={() => router.push('/todos')}
                className="px-6 py-3 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300 transition duration-200"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
        
        <div className="mt-8">
          <button
            onClick={() => router.back()}
            className="text-blue-600 hover:text-blue-800"
          >
            ← Back to Todos List
          </button>
        </div>
      </div>
    </div>
  );
}