"use client";

import Link from 'next/link';

const features = [
  {
    title: "📋 Student Management",
    description: "Create, read, update, and delete student records",
    link: "/students",
    color: "from-blue-500 to-blue-600"
  },
  {
    title: "✅ Todo Management",
    description: "Full-featured todo system with priorities and statuses",
    link: "/todos",
    color: "from-green-500 to-green-600"
  },
  {
    title: "🚀 FastAPI Backend",
    description: "High-performance API with Neon PostgreSQL",
    link: "http://localhost:8000/docs",
    external: true,
    color: "from-purple-500 to-purple-600"
  },
  {
    title: "⚡ Next.js Frontend",
    description: "Modern React framework with Tailwind CSS",
    link: "https://nextjs.org",
    external: true,
    color: "from-gray-700 to-gray-800"
  }
];

const todoFeatures = [
  "Add Task – Create new todo items",
  "Delete Task – Remove tasks from the list",
  "Update Task – Modify existing task details",
  "View Task List – Display all tasks with filters",
  "Mark as Complete – Toggle task completion status"
];

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-4 sm:p-6 md:p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-800 mb-4">
            Student Todo Management System
          </h1>
          <p className="text-lg sm:text-xl text-gray-600 max-w-3xl mx-auto">
            Complete system for managing students and their tasks with Next.js, FastAPI, and Neon PostgreSQL
          </p>
        </header>
        
        {/* Features Grid */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">
            Core Features
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <div key={index} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition duration-300">
                <div className={`h-2 bg-gradient-to-r ${feature.color}`}></div>
                <div className="p-6">
                  <h3 className="text-xl font-semibold text-gray-800 mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 mb-4">
                    {feature.description}
                  </p>
                  {feature.external ? (
                    <a
                      href={feature.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Learn more →
                    </a>
                  ) : (
                    <Link
                      href={feature.link}
                      className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Get started →
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Todo Features Section */}
        <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8 mb-8">
          <div className="flex flex-wrap items-center justify-between mb-6 gap-4">
            <div>
              <h2 className="text-3xl font-bold text-gray-800">
                Todo App Features
              </h2>
              <p className="text-gray-600 mt-2">
                All 5 essential todo features implemented
              </p>
            </div>
            <Link
              href="/todos"
              className="px-6 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition duration-200"
            >
              Explore Todos
            </Link>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {todoFeatures.map((feature, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-bold">✓</span>
                  </div>
                </div>
                <p className="text-gray-700">{feature}</p>
              </div>
            ))}
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-bold">+</span>
                </div>
              </div>
              <p className="text-gray-700">
                <span className="font-semibold">Bonus:</span> Priority levels, student assignment, due dates, and filtering
              </p>
            </div>
          </div>
        </div>
        
        {/* Quick Actions */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-6 sm:p-8 text-white">
          <h2 className="text-3xl font-bold mb-6">Quick Start</h2>
          <div className="flex flex-col md:flex-row gap-4">
            <Link
              href="/students/new"
              className="px-6 py-4 bg-white text-blue-600 font-medium rounded-lg hover:bg-gray-100 transition duration-200 text-center"
            >
              + Add New Student
            </Link>
            <Link
              href="/todos/new"
              className="px-6 py-4 bg-white text-green-600 font-medium rounded-lg hover:bg-gray-100 transition duration-200 text-center"
            >
              + Add New Todo
            </Link>
            <Link
              href="/students"
              className="px-6 py-4 bg-transparent border-2 border-white font-medium rounded-lg hover:bg-white/10 transition duration-200 text-center"
            >
              View All Students
            </Link>
            <Link
              href="/todos"
              className="px-6 py-4 bg-transparent border-2 border-white font-medium rounded-lg hover:bg-white/10 transition duration-200 text-center"
            >
              View All Todos
            </Link>
          </div>
          
          <div className="mt-8 pt-6 border-t border-white/20">
            <p className="text-white/80">
              Backend API running on: <span className="font-mono">http://localhost:8000</span>
            </p>
            <div className="flex space-x-4 mt-2">
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-white hover:text-white/80 underline"
              >
                Swagger UI
              </a>
              <a
                href="http://localhost:8000/redoc"
                target="_blank"
                rel="noopener noreferrer"
                className="text-white hover:text-white/80 underline"
              >
                ReDoc
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}