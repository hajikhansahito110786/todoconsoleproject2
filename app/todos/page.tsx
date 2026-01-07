"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';  // ✅ Added missing import

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

export default function TodosPage() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<'all' | 'todo' | 'in_progress' | 'done'>('all');
  const [selectedStudent, setSelectedStudent] = useState<number | 'all'>('all');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [todosRes, studentsRes] = await Promise.all([
        fetch('http://localhost:8000/todos/'),
        fetch('http://localhost:8000/students/')
      ]);
      
      if (!todosRes.ok) throw new Error('Failed to fetch todos');
      if (!studentsRes.ok) throw new Error('Failed to fetch students');
      
      const todosData = await todosRes.json();
      const studentsData = await studentsRes.json();
      
      setTodos(todosData);
      setStudents(studentsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this todo?')) return;
    
    try {
      const response = await fetch(`http://localhost:8000/todos/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) throw new Error('Failed to delete todo');
      
      fetchData(); // Refresh list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete todo');
    }
  };

  const handleMarkComplete = async (id: number) => {
    try {
      const response = await fetch(`http://localhost:8000/todos/${id}/complete`, {
        method: 'PUT',
      });
      
      if (!response.ok) throw new Error('Failed to mark todo as complete');
      
      fetchData(); // Refresh list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update todo');
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'done': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'todo': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredTodos = todos.filter(todo => {
    if (filter !== 'all' && todo.status !== filter) return false;
    if (selectedStudent !== 'all' && todo.student_id !== selectedStudent) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading todos...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Todo Management</h1>
            <p className="text-gray-600 mt-2">
              Manage all tasks ({filteredTodos.length} of {todos.length} shown)
            </p>
          </div>
          <div className="space-x-4">
            <Link
              href="/todos/new"
              className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition duration-200"
            >
              + Add New Todo
            </Link>
            <Link
              href="/students"
              className="px-6 py-3 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300 transition duration-200"
            >
              View Students
            </Link>
          </div>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-xl shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Status
              </label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Statuses</option>
                <option value="todo">Todo</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Student
              </label>
              <select
                value={selectedStudent}
                onChange={(e) => setSelectedStudent(e.target.value === 'all' ? 'all' : parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Students</option>
                {students.map(student => (
                  <option key={student.id} value={student.id}>
                    {student.name} ({student.email})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Todo List */}
        {filteredTodos.length === 0 ? (
          <div className="bg-white rounded-xl shadow p-8 text-center">
            <p className="text-gray-500 text-lg mb-4">No todos found.</p>
            <Link
              href="/todos/new"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create Your First Todo
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTodos.map(todo => (
              <div key={todo.id} className="bg-white rounded-xl shadow hover:shadow-lg transition duration-200">
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-semibold text-gray-800 truncate">
                      {todo.title}
                    </h3>
                    <div className="flex space-x-2">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(todo.priority)}`}>
                        {todo.priority}
                      </span>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(todo.status)}`}>
                        {todo.status.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  
                  {todo.description && (
                    <p className="text-gray-600 mb-4 line-clamp-2">
                      {todo.description}
                    </p>
                  )}
                  
                  <div className="space-y-2 mb-6">
                    {todo.student_id && (
                      <div className="flex items-center text-sm text-gray-500">
                        <span className="font-medium mr-2">Student:</span>
                        <span>
                          {students.find(s => s.id === todo.student_id)?.name || `Student #${todo.student_id}`}
                        </span>
                      </div>
                    )}
                    
                    {todo.due_date && (
                      <div className="flex items-center text-sm text-gray-500">
                        <span className="font-medium mr-2">Due:</span>
                        <span>{new Date(todo.due_date).toLocaleDateString()}</span>
                      </div>
                    )}
                    
                    <div className="flex items-center text-sm text-gray-500">
                      <span className="font-medium mr-2">Created:</span>
                      <span>{new Date(todo.created_at).toLocaleDateString()}</span>
                    </div>
                    
                    {todo.completed_at && (
                      <div className="flex items-center text-sm text-green-600">
                        <span className="font-medium mr-2">Completed:</span>
                        <span>{new Date(todo.completed_at).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex space-x-2 pt-4 border-t">
                    <Link
                      href={`/todos/${todo.id}/edit`}
                      className="flex-1 px-4 py-2 bg-blue-50 text-blue-700 text-sm font-medium rounded-lg hover:bg-blue-100 text-center"
                    >
                      Edit
                    </Link>
                    
                    {todo.status !== 'done' && (
                      <button
                        onClick={() => handleMarkComplete(todo.id)}
                        className="flex-1 px-4 py-2 bg-green-50 text-green-700 text-sm font-medium rounded-lg hover:bg-green-100"
                      >
                        Complete
                      </button>
                    )}
                    
                    <button
                      onClick={() => handleDelete(todo.id)}
                      className="flex-1 px-4 py-2 bg-red-50 text-red-700 text-sm font-medium rounded-lg hover:bg-red-100"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-8">
          <Link
            href="/"
            className="text-blue-600 hover:text-blue-800"
          >
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}