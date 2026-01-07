'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentApi, StudentUpdate } from '@/lib/api';
import Link from 'next/link';

export default function EditStudentPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [studentId, setStudentId] = useState<number | null>(null); // State to hold parsed studentId

  useEffect(() => {
    // Ensure params.id is available and is a string before parsing
    if (params && typeof params.id === 'string') {
      const parsedId = parseInt(params.id, 10);
      if (!isNaN(parsedId)) { // Ensure it's a valid number
        setStudentId(parsedId);
      }
    }
  }, [params]); // Depend on params to re-run if it changes

  const [formData, setFormData] = useState({ nameplz: '', email: '' });

  const { data: student, isLoading, error } = useQuery({
    queryKey: ['student', studentId],
    queryFn: () => studentApi.getOne(studentId!), // Use non-null assertion as enabled will check
    enabled: studentId !== null, // Only run query if studentId is parsed
  });

  const updateStudentMutation = useMutation({
    mutationFn: (updateData: StudentUpdate) => studentApi.update(studentId, updateData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      queryClient.invalidateQueries({ queryKey: ['student', studentId] });
      alert('Student updated successfully!');
      router.push('/students');
    },
    onError: (err: any) => {
      alert(`Error updating student: ${err.response?.data?.detail || err.message}`);
    }
  });

  useEffect(() => {
    if (student) {
      setFormData({
        nameplz: student.nameplz || '',
        email: student.email || '',
      });
    }
  }, [student]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.nameplz || !formData.email) {
      alert('Name (nameplz) and email cannot be empty.');
      return;
    }
    updateStudentMutation.mutate(formData);
  };

  if (isLoading) return <p>Loading student data...</p>;
  if (error) return <p className="text-red-500">Error loading student: {error.message}</p>;
  if (!student) return <p>Student not found.</p>

  return (
    <div>
      <div className="mb-6">
          <Link href="/students" className="text-blue-600 hover:text-blue-800">
              ← Back to Students
          </Link>
          <h1 className="text-3xl font-bold mt-2">Edit Student: {student.nameplz}</h1>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label htmlFor="nameplz" className="block text-sm font-medium text-gray-700">Name (nameplz)</label>
                <input
                    type="text"
                    id="nameplz"
                    name="nameplz"
                    value={formData.nameplz}
                    onChange={handleChange}
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                    disabled={updateStudentMutation.isPending}
                />
            </div>
            <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
                <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
                    disabled={updateStudentMutation.isPending}
                />
            </div>
            <div className="flex justify-end gap-3 pt-4">
                <button
                    type="button"
                    onClick={() => router.push('/students')}
                    className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={updateStudentMutation.isPending}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                    {updateStudentMutation.isPending ? 'Saving...' : 'Save Changes'}
                </button>
            </div>
        </form>
      </div>
    </div>
  );
}
