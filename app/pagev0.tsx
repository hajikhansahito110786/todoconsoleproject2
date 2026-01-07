import Link from 'next/link';

export default function Home() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Student Management System</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Link 
          href="/students/create"
          className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
        >
          <h2 className="text-xl font-semibold text-blue-600 mb-2">Create Student</h2>
          <p className="text-gray-600">Add a new student to the system</p>
          <div className="mt-4 text-blue-500 font-medium">Go →</div>
        </Link>
        
        <Link 
          href="/classes/create"
          className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
        >
          <h2 className="text-xl font-semibold text-green-600 mb-2">Create Class</h2>
          <p className="text-gray-600">Add a new class to the system</p>
          <div className="mt-4 text-green-500 font-medium">Go →</div>
        </Link>
        
        <Link 
          href="/students"
          className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
        >
          <h2 className="text-xl font-semibold text-purple-600 mb-2">View Students</h2>
          <p className="text-gray-600">Browse all registered students</p>
          <div className="mt-4 text-purple-500 font-medium">View →</div>
        </Link>
        
        <Link 
          href="/classes"
          className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
        >
          <h2 className="text-xl font-semibold text-orange-600 mb-2">View Classes</h2>
          <p className="text-gray-600">Browse all available classes</p>
          <div className="mt-4 text-orange-500 font-medium">View →</div>
        </Link>
      </div>
    </div>
  );
}