'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { studentApi, Student } from '@/lib/api';
import { Trash2, Pencil } from 'lucide-react';

async function fetchStudents(): Promise<Student[]> {
  // The API returns the list directly
  return studentApi.getAll();
}

export default function StudentsPage() {
  const queryClient = useQueryClient();
  const { data: students = [], isLoading, error, refetch } = useQuery<Student[]>({
    queryKey: ['students'],
    queryFn: fetchStudents,
  });

  const deleteStudentMutation = useMutation({
    mutationFn: studentApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
    onError: (err: any) => {
        alert(`Error deleting student: ${err.response?.data?.detail || err.message}`);
    }
  });

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this student? This will also delete all their associated classes.')) {
      deleteStudentMutation.mutate(id);
    }
  };

  if (isLoading) return <div className="p-4">Loading...</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error.message}</div>;

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Students</h1>
        <div className="flex gap-3">
          <Link href="/students/create" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2">
            + New Student
          </Link>
          <button onClick={() => refetch()} className="bg-gray-200 px-4 py-2 rounded-lg hover:bg-gray-300">
            Refresh
          </button>
        </div>
      </div>

      {students.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed rounded-lg">
          <p className="text-gray-500 mb-4">No students found.</p>
          <Link href="/students/create" className="text-blue-600 font-semibold">
            Create your first student →
          </Link>
        </div>
      ) : (
        <div className="bg-white shadow-md rounded-lg overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name (nameplz)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {students.map((student) => (
                <tr key={student.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{student.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{student.nameplz}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{student.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {student.created_at ? new Date(student.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-4">
                      <Link href={`/students/${student.id}/edit`} className="text-blue-600 hover:text-blue-900" title="Edit">
                        <Pencil className="w-5 h-5"/>
                      </Link>
                      <button
                        onClick={() => handleDelete(student.id)}
                        disabled={deleteStudentMutation.isPending && deleteStudentMutation.variables === student.id}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Delete"
                      >
                        <Trash2 className="w-5 h-5"/>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="mt-4 text-sm text-gray-500">
        Total: {students.length} student{students.length !== 1 ? 's' : ''}
      </div>
    </>
  );
}