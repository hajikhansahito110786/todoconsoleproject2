'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { classApi } from '@/lib/api'; // Assuming your api functions are here

export default function CreateClassPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formData, setFormData] = useState({
    class_name: '',
    class_code: '',
    semester: '',
    student_id: '1', // Defaulting to student 1, adjust as needed
    description: '',
  });

  const createClassMutation = useMutation({
    mutationFn: classApi.create,
    onSuccess: (data) => {
      // Invalidate and refetch the classes query
      queryClient.invalidateQueries({ queryKey: ['classes'] });
      
      alert(`✅ Class created successfully!\n\nClass: ${data.class_name}`);
      router.push('/classes');
    },
    onError: (error: any) => {
      alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
      setErrors(prev => ({...prev, form: 'Failed to create class.'}))
    }
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Simple validation
    if (!formData.class_name || !formData.class_code || !formData.semester) {
        alert("Please fill in all required fields.");
        return;
    }
    createClassMutation.mutate(formData);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-2xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Create New Class</h1>
          <p className="text-gray-600 mt-2">Add a new class to the system</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Form fields */}
            <div>
              <label htmlFor="class_name" className="block text-sm font-medium text-gray-700 mb-1">Class Name</label>
              <input
                type="text"
                id="class_name"
                name="class_name"
                value={formData.class_name}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                disabled={createClassMutation.isPending}
              />
            </div>
            
            <div>
              <label htmlFor="class_code" className="block text-sm font-medium text-gray-700 mb-1">Class Code</label>
              <input
                type="text"
                id="class_code"
                name="class_code"
                value={formData.class_code}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                disabled={createClassMutation.isPending}
              />
            </div>

            <div>
              <label htmlFor="semester" className="block text-sm font-medium text-gray-700 mb-1">Semester</label>
              <input
                type="text"
                id="semester"
                name="semester"
                value={formData.semester}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                disabled={createClassMutation.isPending}
              />
            </div>

            <div>
              <label htmlFor="student_id" className="block text-sm font-medium text-gray-700 mb-1">Student ID</label>
              <input
                type="number"
                id="student_id"
                name="student_id"
                value={formData.student_id}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                disabled={createClassMutation.isPending}
              />
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                disabled={createClassMutation.isPending}
              />
            </div>

            {/* Buttons */}
            <div className="flex gap-3 pt-6 border-t border-gray-200">
              <button
                type="submit"
                disabled={createClassMutation.isPending}
                className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {createClassMutation.isPending ? 'Creating...' : 'Create Class'}
              </button>
              <button
                type="button"
                onClick={() => router.push('/classes')}
                className="flex-1 bg-gray-100 text-gray-800 py-3 px-6 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}