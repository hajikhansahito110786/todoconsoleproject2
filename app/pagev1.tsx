"use client";

import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            Student Management System
          </h1>
          <p className="text-lg text-gray-600">
            Manage student records with ease using Next.js and FastAPI
          </p>
        </header>
        
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6">
            Features
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-blue-50 p-6 rounded-lg">
              <h3 className="text-xl font-semibold text-blue-700 mb-3">
                👥 Student Management
              </h3>
              <p className="text-gray-600">
                Create, read, update, and delete student records
              </p>
            </div>
            
            <div className="bg-green-50 p-6 rounded-lg">
              <h3 className="text-xl font-semibold text-green-700 mb-3">
                🚀 FastAPI Backend
              </h3>
              <p className="text-gray-600">
                Powered by FastAPI with Neon PostgreSQL database
              </p>
            </div>
            
            <div className="bg-purple-50 p-6 rounded-lg">
              <h3 className="text-xl font-semibold text-purple-700 mb-3">
                ⚡ Next.js Frontend
              </h3>
              <p className="text-gray-600">
                Modern React framework with server-side rendering
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6">
            Get Started
          </h2>
          <div className="space-y-4">
            <Link
              href="/students"
              className="inline-flex items-center justify-center w-full md:w-auto px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition duration-200"
            >
              📋 View All Students
            </Link>
            
            <div className="text-center text-gray-500 mt-4">
              <p>API running on: http://localhost:8000</p>
              <p>Check out the API documentation:</p>
              <div className="flex justify-center space-x-4 mt-2">
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  Swagger UI
                </a>
                <a
                  href="http://localhost:8000/redoc"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  ReDoc
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}