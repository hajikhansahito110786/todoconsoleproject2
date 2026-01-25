// app/students/new/page.tsx
"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '../../context/UserContext'; // Add this

export default function NewStudentPage() {
  const router = useRouter();
  const { userEmail } = useUser(); // Get logged-in user email
  const [formData, setFormData] = useState({
    name: '',
    email: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      // Get user email from context
      const currentUserEmail = userEmail || '';
      
      const response = await fetch('http://localhost:8000/students/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-user-email': currentUserEmail, // Send user email in header
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create student');
      }

      router.push('/students');
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create student');
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-md mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Add New Student</h1>
          <p className="text-gray-600 mt-2">Create a new student record</p>
          
          {/* Show logged-in user info */}
          {userEmail ? (
            <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-700">
                📧 Creating as: <span className="font-semibold">{userEmail}</span>
              </p>
              <p className="text-xs text-green-600 mt-1">
                This email will be recorded as the creator
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
                Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter student name"
                required
                disabled={!userEmail} // Disable if not logged in
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email *
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter student email"
                required
                disabled={!userEmail} // Disable if not logged in
              />
            </div>
            
            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={submitting || !userEmail}
                className="flex-1 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Creating...' : 'Create Student'}
              </button>
              
              <button
                type="button"
                onClick={() => router.push('/students')}
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
            ← Back to Students List
          </button>
        </div>
      </div>
    </div>
  );
}