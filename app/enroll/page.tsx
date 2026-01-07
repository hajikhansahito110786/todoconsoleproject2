'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function EnrollPage() {
  const router = useRouter();
  const [students, setStudents] = useState<any[]>([]);
  const [classes, setClasses] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState('');
  const [selectedClassName, setSelectedClassName] = useState('');
  const [selectedClassCode, setSelectedClassCode] = useState('');
  const [enrollments, setEnrollments] = useState<any[]>([]);

  // Fetch data
  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch students
        const studentsRes = await fetch('/api/students');
        const studentsData = await studentsRes.json();
        if (studentsData.success) {
          setStudents(studentsData.data?.students || []);
        }

        // Fetch classes for dropdown
        const classesRes = await fetch('/api/classes');
        const classesData = await classesRes.json();
        if (classesData.success) {
          setClasses(classesData.data?.classes || []);
        }

        // Fetch existing enrollments
        const enrollRes = await fetch('/api/enroll');
        const enrollData = await enrollRes.json();
        if (enrollData.success) {
          setEnrollments(enrollData.data?.enrollments || []);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleEnroll = async () => {
    if (!selectedStudent || !selectedClassName) {
      alert('Please select student and enter class name');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const response = await fetch('/api/enroll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          studentId: parseInt(selectedStudent),
          className: selectedClassName,
          classCode: selectedClassCode
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        alert(`✅ ${data.message}`);
        setSelectedStudent('');
        setSelectedClassName('');
        setSelectedClassCode('');
        
        // Refresh enrollments
        const enrollRes = await fetch('/api/enroll');
        const enrollData = await enrollRes.json();
        if (enrollData.success) {
          setEnrollments(enrollData.data?.enrollments || []);
        }
      } else {
        alert(`❌ ${data.message}`);
      }
    } catch (error) {
      alert('Failed to enroll student');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUnenroll = async (enrollmentId: number) => {
    if (!confirm('Are you sure you want to remove this enrollment?')) return;
    
    try {
      const response = await fetch(`/api/enroll/${enrollmentId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      if (response.ok) {
        alert(data.message);
        // Refresh enrollments
        const enrollRes = await fetch('/api/enroll');
        const enrollData = await enrollRes.json();
        if (enrollData.success) {
          setEnrollments(enrollData.data?.enrollments || []);
        }
      } else {
        alert(`Error: ${data.message}`);
      }
    } catch (error) {
      alert('Failed to remove enrollment');
    }
  };

  // Get unique class names from existing classes or enrollments
  const uniqueClassNames = [...new Set([
    ...classes.map(c => c.className),
    ...enrollments.map(e => e.class_name)
  ])].filter(Boolean);

  if (isLoading) {
    return (
      <div className="container mx-auto p-4">
        <div className="text-center py-12">Loading enrollment data...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <Link href="/" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
          ← Back to Home
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Student Enrollment</h1>
        <p className="text-gray-600 mt-2">Connect students with classes using your studentclass table</p>
        <p className="text-sm text-gray-500 mt-1">
          Table structure: studentclass(id, studentid, class_name, class_code)
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Enrollment Form */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-6">Enroll Student</h2>
            
            <div className="space-y-6">
              {/* Student Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Select Student *
                </label>
                <select
                  value={selectedStudent}
                  onChange={(e) => setSelectedStudent(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Choose a student...</option>
                  {students.map(student => (
                    <option key={student.id} value={student.id}>
                      {student.name} ({student.email})
                    </option>
                  ))}
                </select>
                {students.length === 0 && (
                  <p className="text-sm text-gray-500 mt-2">
                    No students found. <Link href="/students/create" className="text-blue-600">Create a student first</Link>
                  </p>
                )}
              </div>

              {/* Class Name */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Class Name *
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={selectedClassName}
                    onChange={(e) => setSelectedClassName(e.target.value)}
                    placeholder="Enter class name"
                    list="classNames"
                    className="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <datalist id="classNames">
                    {uniqueClassNames.map(name => (
                      <option key={name} value={name} />
                    ))}
                  </datalist>
                  <select
                    value={selectedClassName}
                    onChange={(e) => setSelectedClassName(e.target.value)}
                    className="border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Or select...</option>
                    {uniqueClassNames.map(name => (
                      <option key={name} value={name}>{name}</option>
                    ))}
                  </select>
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  Enter class name or select from existing
                </p>
              </div>

              {/* Class Code (Optional) */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Class Code (Optional)
                </label>
                <input
                  type="text"
                  value={selectedClassCode}
                  onChange={(e) => setSelectedClassCode(e.target.value)}
                  placeholder="e.g., MAT101, CS201"
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Enroll Button */}
              <div>
                <button
                  onClick={handleEnroll}
                  disabled={isSubmitting || !selectedStudent || !selectedClassName}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {isSubmitting ? 'Enrolling...' : 'Enroll Student'}
                </button>
              </div>
            </div>
          </div>

          {/* Current Enrollments */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Current Enrollments</h2>
              <span className="text-sm text-gray-500">
                {enrollments.length} enrollment{enrollments.length !== 1 ? 's' : ''}
              </span>
            </div>

            {enrollments.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5 1.5a2.5 2.5 0 01-2.5 2.5"></path>
                </svg>
                No enrollments yet. Enroll a student to see them here.
              </div>
            ) : (
              <div className="space-y-4">
                {enrollments.map(enrollment => (
                  <div key={enrollment.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="font-medium">{enrollment.student_name}</div>
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            Student ID: {enrollment.studentid}
                          </span>
                        </div>
                        <div className="text-sm text-gray-500 mb-3">{enrollment.student_email}</div>
                        
                        <div className="flex items-center gap-4">
                          <div>
                            <span className="text-sm font-medium">Class:</span>
                            <div className="text-lg font-semibold text-gray-800">{enrollment.class_name}</div>
                          </div>
                          {enrollment.class_code && (
                            <div>
                              <span className="text-sm font-medium">Code:</span>
                              <div className="text-lg font-semibold text-gray-800">{enrollment.class_code}</div>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="text-sm text-gray-500 mb-2">
                          Enrollment ID: {enrollment.id}
                        </div>
                        <button
                          onClick={() => handleUnenroll(enrollment.id)}
                          className="text-red-600 hover:text-red-800 text-sm bg-red-50 hover:bg-red-100 px-3 py-1 rounded"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Info Panel */}
        <div>
          <div className="bg-blue-50 rounded-xl border border-blue-200 p-6 mb-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-4">Your Table Structure</h3>
            <div className="space-y-3">
              <div className="bg-white p-3 rounded border">
                <div className="font-mono text-sm">
                  <div className="text-blue-600">studentclass</div>
                  <div className="ml-4">
                    <div>• id <span className="text-green-600">(primary key)</span></div>
                    <div>• studentid <span className="text-orange-600">(foreign key to student.id)</span></div>
                    <div>• class_name <span className="text-gray-600">(string)</span></div>
                    <div>• class_code <span className="text-gray-600">(string, optional)</span></div>
                  </div>
                </div>
              </div>
              
              <ul className="space-y-2 text-blue-700 text-sm">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Links <code className="bg-blue-100 px-1">student.id</code> to class name</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Stores class name directly (not foreign key)</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Optional class code for additional reference</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-white rounded-xl shadow p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">Quick Stats</h3>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-500">Total Students</div>
                <div className="text-2xl font-bold">{students.length}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Unique Classes</div>
                <div className="text-2xl font-bold">
                  {[...new Set(enrollments.map(e => e.class_name))].length}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Active Enrollments</div>
                <div className="text-2xl font-bold">{enrollments.length}</div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-gray-50 rounded-xl border p-6">
            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <Link
                href="/students/create"
                className="block w-full text-center bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700"
              >
                + Create New Student
              </Link>
              <Link
                href="/classes/create"
                className="block w-full text-center bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700"
              >
                + Create New Class
              </Link>
              <button
                onClick={() => window.location.reload()}
                className="block w-full text-center bg-gray-600 text-white py-2 px-4 rounded hover:bg-gray-700"
              >
                ↻ Refresh Data
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}