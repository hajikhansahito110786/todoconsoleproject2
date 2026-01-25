"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Home() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [showLogin, setShowLogin] = useState(true);

  // Check if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem('session_token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setIsLoggedIn(true);
      setUser(JSON.parse(userData));
      setShowLogin(false);
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessage(`✅ Login successful!`);
        localStorage.setItem('session_token', data.session_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        setIsLoggedIn(true);
        setUser(data.user);
        setShowLogin(false);
      } else {
        setMessage(`❌ ${data.detail || 'Login failed'}`);
      }
    } catch (err) {
      setMessage(`❌ Cannot connect to backend. Make sure "python app.py" is running.`);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('session_token');
    localStorage.removeItem('user');
    setIsLoggedIn(false);
    setUser(null);
    setShowLogin(true);
    setMessage('✅ Logged out successfully');
    setEmail('');
    setPassword('');
  };

  const testBackend = async () => {
    try {
      const response = await fetch('http://localhost:8000/test');
      const data = await response.json();
      alert(`✅ Backend is running!\n\n${data.message}`);
    } catch (err) {
      alert('❌ Backend not running. Please run: python app.py');
    }
  };

  // If not logged in, show login form with beautiful styling
  if (showLogin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 p-4 sm:p-6 md:p-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <header className="mb-12 text-center">
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-800 mb-4">
              Student Todo Management System
            </h1>
            <p className="text-lg sm:text-xl text-gray-600 max-w-3xl mx-auto">
              Complete system for managing students and their tasks with Next.js, FastAPI, and Neon PostgreSQL
            </p>
          </header>

          {/* Main Content with Login Form */}
          <div className="flex flex-col lg:flex-row gap-8 items-center">
            {/* Left Side - Features */}
            <div className="lg:w-1/2">
              <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8 mb-8">
                <h2 className="text-3xl font-bold text-gray-800 mb-6">
                  🔐 Secure Login
                </h2>
                <p className="text-gray-600 mb-6">
                  Access your student management dashboard with secure authentication
                </p>
                
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 font-bold">✓</span>
                      </div>
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">Secure Authentication</p>
                      <p className="text-gray-600 text-sm">Protected with session tokens</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                        <span className="text-green-600 font-bold">✓</span>
                      </div>
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">Neon PostgreSQL</p>
                      <p className="text-gray-600 text-sm">Cloud-native database backend</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                        <span className="text-purple-600 font-bold">✓</span>
                      </div>
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">FastAPI Backend</p>
                      <p className="text-gray-600 text-sm">High-performance REST API</p>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Connection Test */}
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
                <h3 className="text-xl font-bold mb-4">System Status</h3>
                <button 
                  onClick={testBackend}
                  className="w-full py-3 bg-white text-blue-600 font-medium rounded-lg hover:bg-gray-100 transition duration-200 mb-3"
                >
                  Test Backend Connection
                </button>
                <p className="text-white/80 text-sm">
                  Backend URL: <code className="bg-white/20 px-2 py-1 rounded">http://localhost:8000</code>
                </p>
              </div>
            </div>

            {/* Right Side - Login Form */}
            <div className="lg:w-1/2">
              <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8">
                <div className="text-center mb-8">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-3xl">🔐</span>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-800">Welcome Back</h2>
                  <p className="text-gray-600">Sign in to your account</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                      placeholder="you@example.com"
                      required
                      disabled={loading}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Password
                    </label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                      placeholder="Enter your password"
                      required
                      disabled={loading}
                    />
                  </div>
                  
                  {message && (
                    <div className={`p-4 rounded-lg ${
                      message.includes('✅') 
                        ? 'bg-green-50 border border-green-200 text-green-700'
                        : 'bg-red-50 border border-red-200 text-red-700'
                    }`}>
                      {message}
                    </div>
                  )}
                  
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
                  >
                    {loading ? (
                      <span className="flex items-center justify-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Signing in...
                      </span>
                    ) : (
                      'Sign In to Dashboard'
                    )}
                  </button>
                </form>

                <div className="mt-8 pt-6 border-t border-gray-200">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="font-medium text-blue-800 mb-2">💡 Need help?</p>
                    <ul className="text-sm text-blue-600 space-y-1 ml-4 list-disc">
                      <li>Make sure backend is running: <code className="bg-blue-100 px-2 py-1 rounded">python app.py</code></li>
                      <li>Use credentials from your <code className="bg-blue-100 px-2 py-1 rounded">usertable</code></li>
                      <li>Test connection with the button on the left</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-12 text-center text-gray-500 text-sm">
            <p>Student Management System • {new Date().getFullYear()}</p>
            <div className="flex justify-center space-x-4 mt-2">
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800"
              >
                API Documentation
              </a>
              <span>•</span>
              <a
                href="https://nextjs.org"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800"
              >
                Next.js
              </a>
              <span>•</span>
              <a
                href="https://fastapi.tiangolo.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800"
              >
                FastAPI
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // If logged in, show the original beautiful dashboard
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
      title: "🤖 AI Chat Assistant",
      description: "Interactive assistant to help manage your tasks",
      link: "/chat",
      color: "from-purple-500 to-indigo-600"
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-4 sm:p-6 md:p-8">
      {/* Welcome Header with Logout */}
      <div className="max-w-6xl mx-auto mb-8">
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold mb-2">
                Welcome back, {user?.email || 'User'}! 👋
              </h1>
              <p className="text-white/80">
                You are now logged into the Student Management System
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="px-6 py-3 bg-white text-blue-600 font-medium rounded-lg hover:bg-gray-100 transition duration-200 whitespace-nowrap"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

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
            <Link
              href="/chat"
              className="px-6 py-4 bg-white text-purple-600 font-medium rounded-lg hover:bg-gray-100 transition duration-200 text-center"
            >
              Open AI Assistant
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