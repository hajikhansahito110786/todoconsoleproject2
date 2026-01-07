'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { classApi, StudentClass } from '@/lib/api';
import Link from 'next/link';

// Define the interface for updating a class
interface ClassUpdatePayload {
  class_name?: string;
  class_code?: string;
  semester?: string;
  status?: string;
  priority?: string;
  description?: string | null;
  due_date?: string | null;
}

export default function EditClassPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const classId = parseInt(params.id, 10);

  const [formData, setFormData] = useState<ClassUpdatePayload>({
    class_name: '',
    class_code: '',
    semester: '',
    status: '',
    priority: '',
    description: '',
    due_date: '',
  });

  const { data: cls, isLoading, error } = useQuery<StudentClass>({
    queryKey: ['class', classId],
    queryFn: () => classApi.getOne(classId),
    enabled: !!classId, // Only run query if classId is valid
  });

  const updateClassMutation = useMutation({
    mutationFn: (updateData: ClassUpdatePayload) => classApi.update(classId, updateData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['classes'] }); // Invalidate all classes list
      queryClient.invalidateQueries({ queryKey: ['class', classId] }); // Invalidate this specific class
      alert('Class updated successfully!');
      router.push('/classes');
    },
    onError: (err: any) => {
      alert(`Error updating class: ${err.response?.data?.detail || err.message}`);
    }
  });

  useEffect(() => {
    if (cls) {
      setFormData({
        class_name: cls.class_name,
        class_code: cls.class_code,
        semester: cls.semester,
        status: cls.status,
        priority: cls.priority,
        description: cls.description,
        due_date: cls.due_date,
      });
    }
  }, [cls]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateClassMutation.mutate(formData);
  };

  if (isLoading) return <p>Loading class data...</p>;
  if (error) return <p className="text-red-500">Error loading class: {error.message}</p>;
  if (!cls) return <p>Class not found.</p>

  return (
    <div>
      <div className="mb-6">
          <Link href="/classes" className="text-blue-600 hover:text-blue-800">
              ← Back to Classes
          </Link>
          <h1 className="text-3xl font-bold mt-2">Edit Class: {cls.class_name}</h1>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label htmlFor="class_name" className="block text-sm font-medium text-gray-700">Class Name</label>
                <input
                    type="text"
                    id="class_name"
                    name="class_name"
                    value={formData.class_name}
                    onChange={handleChange}
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                    disabled={updateClassMutation.isPending}
                />
            </div>
            <div>
                <label htmlFor="class_code" className="block text-sm font-medium text-gray-700">Class Code</label>
                <input
                    type="text"
                    id="class_code"
                    name="class_code"
                    value={formData.class_code}
                    onChange={handleChange}
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                    disabled={updateClassMutation.isPending}
                />
            </div>
            <div>
                <label htmlFor="semester" className="block text-sm font-medium text-gray-700">Semester</label>
                <input
                    type="text"
                    id="semester"
                    name="semester"
                    value={formData.semester}
                    onChange={handleChange}
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                    disabled={updateClassMutation.isPending}
                />
            </div>
            <div>
                <label htmlFor="status" className="block text-sm font-medium text-gray-700">Status</label>
                <select
                    id="status"
                    name="status"
                    value={formData.status}
                    onChange={handleChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                    disabled={updateClassMutation.isPending}
                >
                    <option value="pending">Pending</option>
                    <option value="in-progress">In Progress</option>
                    <option value="completed">Completed</option>
                </select>
            </div>
            <div>
                <label htmlFor="priority" className="block text-sm font-medium text-gray-700">Priority</label>
                <select
                    id="priority"
                    name="priority"
                    value={formData.priority}
                    onChange={handleChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                    disabled={updateClassMutation.isPending}
                >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                </select>
            </div>
            <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                    id="description"
                    name="description"
                    value={formData.description || ''}
                    onChange={handleChange}
                    rows={3}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                    disabled={updateClassMutation.isPending}
                />
            </div>
            {/* You might want a due_date picker here, but for now it's a simple text field */}
            <div>
                <label htmlFor="due_date" className="block text-sm font-medium text-gray-700">Due Date</label>
                <input
                    type="datetime-local" // Changed to datetime-local for better UX
                    id="due_date"
                    name="due_date"
                    value={formData.due_date ? new Date(formData.due_date).toISOString().slice(0, 16) : ''}
                    onChange={handleChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                    disabled={updateClassMutation.isPending}
                />
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
                <button
                    type="button"
                    onClick={() => router.push('/classes')}
                    className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={updateClassMutation.isPending}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                    {updateClassMutation.isPending ? 'Saving...' : 'Save Changes'}
                </button>
            </div>
        </form>
      </div>
    </div>
  );
}
