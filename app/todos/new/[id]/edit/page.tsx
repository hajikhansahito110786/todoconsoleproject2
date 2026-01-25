// app/todos/[id]/edit/page.tsx
"use client";

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useUser } from '../../context/UserContext';

export default function EditTodoPage() {
  const router = useRouter();
  const params = useParams();
  const todoId = params.id as string;
  const { userEmail } = useUser();
  
  const [students, setStudents] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    status: 'todo',
    due_date: '',
    student_id: 0
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  // Fetch todo details and students
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch todo
        const todoResponse = await fetch(`http://localhost:8000/todos/${todoId}`);
        if (todoResponse.ok) {
          const todoData = await todoResponse.json();
          setFormData({
            title: todoData.title || '',
            description: todoData.description || '',
            priority: todoData.priority || 'medium',
            status: todoData.status || 'todo',
            due_date: todoData.due_date ? todoData.due_date.split('T')[0] : '',
            student_id: todoData.student_id || 0
          });
        } else {
          throw new Error('Todo not found');
        }

        // Fetch students
        const studentsResponse = await fetch('http://localhost:8000/students/');
        if (studentsResponse.ok) {
          const studentsData = await studentsResponse.json();
          setStudents(studentsData);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [todoId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      // Prepare data
      const todoData = {
        title: formData.title,
        description: formData.description,
        priority: formData.priority,
        status: formData.status,
        due_date: formData.due_date || null,
        student_id: formData.student_id === 0 ? null : formData.student_id
      };

      const response = await fetch(`http://localhost:8000/todos/${todoId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'x-user-email': userEmail || '',
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
      [name]: name === 'student_id' ? parseInt(value) || 0 : value
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading todo...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Edit Todo</h1>
          <p className="text-gray-600 mt-2">Update todo #{todoId}</p>
          
          {userEmail ? (
            <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-700">
                📧 Updating as: <span className="font-semibold">{userEmail}</span>
              </p>
              <p className="text-xs text-green-600 mt-1">
                This email will be recorded as the updater
              </p>
            </div>
          ) : (
            <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-700">
                ⚠️ Not logged in. Please <a href="/login" className="underline">login</a> first.
              </p>
            </div>
          )}
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
                placeholder="Enter todo title"
                required
                disabled={!userEmail}
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter todo description"
                rows={3}
                disabled={!userEmail}
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority
                </label>
                <select
                  name="priority"
                  value={formData.priority}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={!userEmail}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={!userEmail}
                >
                  <option value="todo">Todo</option>
                  <option value="in_progress">In Progress</option>
                  <option value="done">Done</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Due Date
                </label>
                <input
                  type="date"
                  name="due_date"
                  value={formData.due_date}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={!userEmail}
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Assign to Student (Optional)
              </label>
              <select
                name="student_id"
                value={formData.student_id}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={!userEmail}
              >
                <option value="0">-- Unassigned --</option>
                {students.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.name} ({student.email})
                  </option>
                ))}
              </select>
            </div>
            
            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={submitting || !userEmail}
                className="flex-1 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Updating...' : 'Update Todo'}
              </button>
              
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