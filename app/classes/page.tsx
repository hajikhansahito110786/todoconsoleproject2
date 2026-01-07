'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import Link from 'next/link';

import { Trash2, Pencil } from 'lucide-react'; // Import icons

import { classApi } from '@/lib/api'; // Import classApi



// Define the interface for a class object

interface StudentClass {

  id: number;

  student_id: number;

  class_name: string;

  class_code: string;

  semester: string;

  status: string;

  priority: string;

  description: string | null;

  due_date: string | null;

  created_at: string;

  instructor?: string; // Optional field seen in usage

  maxStudents?: number; // Optional field seen in usage

}



// API function to fetch all classes

async function fetchClasses(): Promise<StudentClass[]> {

  const response = await fetch('http://localhost:8000/classes/');

  if (!response.ok) throw new Error('Failed to fetch classes');

  return response.json();

}



export default function ClassesPage() {

  const queryClient = useQueryClient();



  const { data: classes = [], isLoading, error, refetch } = useQuery<StudentClass[]>({

    queryKey: ['classes'],

    queryFn: fetchClasses,

  });



  // Removed updateStatusMutation as per instructions to replace dropdown with edit/delete buttons

  // const updateStatusMutation = useMutation({ ... });



  const deleteClassMutation = useMutation({

    mutationFn: classApi.delete,

    onSuccess: () => {

      queryClient.invalidateQueries({ queryKey: ['classes'] });

    },

    onError: (err: any) => {

        alert(`Error deleting class: ${err.response?.data?.detail || err.message}`);

    }

  });



  const handleDelete = (id: number) => {

    if (window.confirm('Are you sure you want to delete this class?')) {

      deleteClassMutation.mutate(id);

    }

  };



  if (isLoading) {

    return (

      <div className="container mx-auto p-4">

        <div className="flex justify-center items-center h-64">

          <div className="text-lg">Loading classes...</div>

        </div>

      </div>

    );

  }



  if (error) {

    return (

      <div className="container mx-auto p-4">

        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">

          Error: {error.message}

        </div>

      </div>

    );

  }



  return (

    <div className="min-h-screen bg-gray-50 py-8">

      <div className="container mx-auto px-4">

        {/* Header */}

        <div className="mb-8">

            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">

                <div>

                    <h1 className="text-3xl font-bold text-gray-900">Classes Management</h1>

                    <p className="text-gray-600 mt-2">Manage all classes in the system</p>

                </div>

                <div className="flex flex-wrap gap-3">

                    <Link href="/classes/create" className="inline-flex items-center bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors">

                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>

                        Create New Class

                    </Link>

                    <button onClick={() => refetch()} className="inline-flex items-center bg-gray-200 text-gray-800 px-5 py-2.5 rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors">

                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>

                        Refresh

                    </button>

                    <Link href="/" className="inline-flex items-center text-gray-700 hover:text-gray-900 px-3 py-2.5">

                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>

                        Home

                    </Link>

                </div>

            </div>

        </div>



        {/* Classes Grid */}

        {classes.length === 0 ? (

          <div className="text-center py-16 bg-white rounded-xl shadow-lg border-2 border-dashed border-gray-300">

            {/* No classes state */}

          </div>

        ) : (

          <>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

              {classes.map((cls: StudentClass) => (

                <div key={cls.id} className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200 hover:shadow-xl transition-shadow duration-300">

                  <div className="p-6">

                    {/* Class Header */}

                    <div className="flex justify-between items-start mb-4">

                      <div>

                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mb-2">

                          ID: {cls.id}

                        </span>

                        <h3 className="text-xl font-bold text-gray-900">{cls.class_name}</h3>

                      </div>

                      <div className="flex-shrink-0">

                        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>

                      </div>

                    </div>



                    {/* Description */}

                    <p className="text-gray-600 mb-6 line-clamp-2">

                      {cls.description || 'No description available'}

                    </p>



                    {/* Class Details */}

                    <div className="space-y-3 mb-6">

                       <div className="flex items-center text-gray-700">

                        <svg className="w-5 h-5 mr-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path></svg>

                        <span className="font-medium">Status:</span>

                        <span className={`ml-2 px-2.5 py-1 rounded-full text-xs font-semibold ${

                          cls.status === 'completed' ? 'bg-green-100 text-green-800' :

                          cls.status === 'in-progress' ? 'bg-yellow-100 text-yellow-800' :

                          'bg-gray-100 text-gray-800'

                        }`}>

                          {cls.status}

                        </span>

                      </div>

                       <div className="flex items-center text-gray-700">

                         <svg className="w-5 h-5 mr-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>

                         <span className="font-medium">Instructor:</span>

                         <span className="ml-2">{cls.instructor || 'N/A'}</span>

                       </div>

                    </div>



                    {/* Action Buttons */}

                    <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">

                      <Link href={`/classes/${cls.id}/edit`} className="text-blue-600 hover:text-blue-900" title="Edit">

                        <Pencil className="w-5 h-5"/>

                      </Link>

                      <button

                        onClick={() => handleDelete(cls.id)}

                        disabled={deleteClassMutation.isPending && deleteClassMutation.variables === cls.id}

                        className="text-red-600 hover:text-red-900 disabled:opacity-50 disabled:cursor-not-allowed"

                        title="Delete"

                      >

                        <Trash2 className="w-5 h-5"/>

                      </button>

                    </div>

                  </div>

                </div>

              ))}

            </div>

          </>

        )}

      </div>

    </div>

  );

}