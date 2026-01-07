'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';

interface ClassDetails {
  id: number;
  className: string;
  description: string;
  instructor: string;
  maxStudents: number | null;
  created_at: string;
}

export default function ClassDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [classData, setClassData] = useState<ClassDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const classId = params.id as string;

  useEffect(() => {
    async function fetchClassDetails() {
      try {
        setIsLoading(true);
        const response = await fetch(`/api/classes/${classId}`);
        
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Class not found');
          }
          throw new Error('Failed to fetch class details');
        }
        
        const data = await response.json();
        if (data.success) {
          setClassData(data.data);
        } else {
          throw new Error(data.message || 'Failed to load class');
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    }

    if (classId) {
      fetchClassDetails();
    }
  }, [classId]);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this class?')) {
      return;
    }

    try {
      const response = await fetch(`/api/classes/${classId}`, {
        method: 'DELETE',
      });

      const data = await response.json();
      
      if (response.ok) {
        alert('Class deleted successfully!');
        router.push('/classes');
      } else {
        alert(`Error: ${data.message}`);
      }
    } catch (error) {
      alert('Failed to delete class');
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-4">
        <div className="flex justify-center items-center h-64">
          <div className="text-lg">Loading class details...</div>
        </div>
      </div>
    );
  }

  if (error || !classData) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Error: {error || 'Class not found'}
        </div>
        <Link href="/classes" className="mt-4 inline-block text-blue-600 hover:text-blue-800">
          ← Back to Classes
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      {/* Navigation */}
      <div className="mb-6">
        <Link 
          href="/classes" 
          className="text-blue-600 hover:text-blue-800 flex items-center gap-2 mb-4"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
          </svg>
          Back to Classes
        </Link>
        
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{classData.className}</h1>
            <p className="text-gray-600 mt-1">Class ID: {classData.id}</p>
          </div>
          <div className="flex gap-3">
            <Link
              href={`/classes/${classId}/edit`}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Edit Class
            </Link>
            <button
              onClick={handleDelete}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Delete Class
            </button>
          </div>
        </div>
      </div>

      {/* Class Details Card */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Class Information */}
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Class Information</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-500">Class Name</label>
                <p className="mt-1 text-lg font-medium">{classData.className}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500">Instructor</label>
                <p className="mt-1 text-lg font-medium">{classData.instructor}</p>
              </div>
              
              {classData.maxStudents && (
                <div>
                  <label className="block text-sm font-medium text-gray-500">Maximum Students</label>
                  <p className="mt-1 text-lg font-medium">{classData.maxStudents}</p>
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-gray-500">Created Date</label>
                <p className="mt-1">
                  {new Date(classData.created_at).toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Description</h2>
            <div className="bg-gray-50 rounded-lg p-4 min-h-[150px]">
              {classData.description ? (
                <p className="text-gray-700 whitespace-pre-wrap">{classData.description}</p>
              ) : (
                <p className="text-gray-500 italic">No description provided</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Students Enrolled Section */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-800">Students Enrolled</h2>
          <button className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
            Enroll Student
          </button>
        </div>
        
        <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5 1.5a2.5 2.5 0 01-2.5 2.5"></path>
          </svg>
          <p className="text-gray-500 mb-2">No students enrolled yet</p>
          <p className="text-sm text-gray-400">Enroll students to see them here</p>
        </div>
        
        <div className="mt-6 text-sm text-gray-500">
          <p>You can enroll students to this class from the students management page.</p>
        </div>
      </div>
    </div>
  );
}