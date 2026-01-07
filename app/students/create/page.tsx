'use client';

import { useState } from 'react'; // ADD THIS IMPORT
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function CreateStudentPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    // Removed age and grade since student table only has nameplz and email
  });

  // Form validation (simplified - no age/grade validation)
  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (formData.name.length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    setErrors({});
    
    try {
      console.log('Submitting student data to "student" table:', formData);
      
      const response = await fetch('/api/students', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name.trim(),
          email: formData.email.trim(),
          // No age or grade - student table doesn't have these columns
        }),
      });

      const data = await response.json();
      console.log('API Response:', data);
      
      if (response.ok) {
        // Success - show message and reset form
        alert(`✅ Student saved to "student" table!\n\nID: ${data.student.id}\nName: ${data.student.name}\nEmail: ${data.student.email}`);
        
        // Reset form
        setFormData({ name: '', email: '' });
        
        // Optionally redirect or refresh
        setTimeout(() => {
          router.refresh();
        }, 100);
        
      } else {
        // API returned an error
        setErrors(prev => ({ 
          ...prev, 
          form: data.message || `Error: ${response.status}` 
        }));
        alert(`❌ ${data.message || 'Failed to create student'}`);
      }
    } catch (error) {
      console.error('Network error:', error);
      setErrors(prev => ({ 
        ...prev, 
        form: 'Network error. Please check your connection.' 
      }));
      alert('❌ Network error. Please check your connection and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-2xl">
        {/* Header with navigation */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <Link 
              href="/"
              className="text-blue-600 hover:text-blue-800 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
              </svg>
              Back to Home
            </Link>
            <Link
              href="/students"
              className="text-gray-600 hover:text-gray-800"
            >
              View All Students →
            </Link>
          </div>
          
          <h1 className="text-3xl font-bold text-gray-900">Create New Student</h1>
          <p className="text-gray-600 mt-2">
            Add a new student record to your "student" table in Neon PostgreSQL
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Note: Using existing "student" table (columns: id, nameplz, email, created_at)
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Form error */}
            {errors.form && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {errors.form}
              </div>
            )}

            {/* Name Field */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Full Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.name ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Enter student's full name"
                disabled={isSubmitting}
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Will be saved as "nameplz" column in database
              </p>
            </div>

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email Address <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.email ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="student@example.com"
                disabled={isSubmitting}
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email}</p>
              )}
            </div>

            {/* Note about missing fields */}
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.998-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm">
                    <strong>Note:</strong> Age and Grade fields are not available because the "student" table only stores name and email.
                  </p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 pt-6 border-t border-gray-200">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200 font-medium"
              >
                {isSubmitting ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Saving to Database...
                  </span>
                ) : (
                  'Save Student to "student" Table'
                )}
              </button>
              
              <button
                type="button"
                onClick={() => {
                  if (window.confirm('Are you sure? All unsaved changes will be lost.')) {
                    router.push('/');
                  }
                }}
                disabled={isSubmitting}
                className="flex-1 bg-gray-100 text-gray-800 py-3 px-6 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 transition duration-200 font-medium"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>

        {/* Information Card */}
        <div className="bg-blue-50 rounded-xl border border-blue-200 p-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-semibold text-blue-800 mb-2">About This Form</h3>
              <ul className="text-blue-700 space-y-2">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Data is saved to the existing <strong>"student"</strong> table</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Table columns: <code className="bg-blue-100 px-1 rounded">id</code>, <code className="bg-blue-100 px-1 rounded">nameplz</code>, <code className="bg-blue-100 px-1 rounded">email</code>, <code className="bg-blue-100 px-1 rounded">created_at</code></span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Email addresses must be unique</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>View all students: <Link href="/students" className="text-blue-800 font-medium underline">Students List</Link></span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}