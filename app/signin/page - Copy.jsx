"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SignInPage() {
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      console.log('Attempting login to /login endpoint...');
      
      // ✅ CORRECT: Your backend has /login endpoint
      const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Login successful:', data);
        
        // Store session token
        localStorage.setItem('session_token', data.session_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Redirect to home page
        router.push('/');
        router.refresh();
        
        alert('✅ Login successful! Session valid for 5 minutes.');
      } else {
        const errorText = await response.text();
        console.error('Login failed. Response:', errorText);
        console.error('Response status:', response.status);
        
        try {
          const errorData = JSON.parse(errorText);
          setError(`Error: ${errorData.detail || 'Login failed'}`);
        } catch {
          setError(`Login failed with status ${response.status}: ${errorText}`);
        }
      }
    } catch (err) {
      console.error('Network error:', err);
      setError(`Cannot connect to server: ${err.message}`);
      
      // Show more detailed error
      alert(`Connection error: ${err.message}\n\nMake sure:\n1. Backend is running: python app.py\n2. Backend URL: http://localhost:8000\n3. Check browser console for details`);
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      console.log('Testing connection to http://localhost:8000...');
      const response = await fetch('http://localhost:8000/health', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      
      const data = await response.json();
      console.log('Health check response:', data);
      
      if (response.ok) {
        // Also test if /login endpoint exists
        const loginTest = await fetch('http://localhost:8000/docs');
        alert(`✅ Backend is running!\nStatus: ${data.status}\nDatabase: ${data.database}\n\nGo to http://localhost:8000/docs to see all endpoints.`);
      } else {
        alert(`❌ Backend error: ${data.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Connection test error:', err);
      alert(`❌ Cannot connect to backend at http://localhost:8000\n\nError: ${err.message}\n\nMake sure to run: python app.py`);
    }
  };

  const testLoginDirectly = async () => {
    // Test login with curl-like approach
    const testData = {
      email: 'admin@example.com',
      password: 'admin123'
    };
    
    console.log('Testing login with:', testData);
    
    try {
      const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testData),
      });
      
      console.log('Direct test response:', response);
      
      if (response.ok) {
        const data = await response.json();
        alert(`✅ Direct test successful!\n\nResponse: ${JSON.stringify(data, null, 2)}`);
      } else {
        const errorText = await response.text();
        alert(`❌ Direct test failed (${response.status}): ${errorText}`);
      }
    } catch (err) {
      alert(`❌ Direct test error: ${err.message}`);
    }
  };

  const createTestUser = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'test123',
          name: 'Test User'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setEmail(data.user.email);
        setPassword('test123');
        alert(`✅ User created!\nEmail: ${data.user.email}\nPassword: test123\n\nNow try logging in.`);
      } else {
        const errorData = await response.json();
        if (errorData.detail?.includes('already registered')) {
          setEmail('test@example.com');
          setPassword('test123');
          alert('✅ User already exists!\nEmail: test@example.com\nPassword: test123\n\nNow click "Login".');
        } else {
          alert(`❌ Failed to create user: ${errorData.detail}`);
        }
      }
    } catch (err) {
      alert(`❌ Cannot create user: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const quickTestLogin = () => {
    // Quick test without backend
    localStorage.setItem('session_token', 'test-token-' + Date.now());
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      email: 'test@example.com',
      name: 'Test User'
    }));
    alert('✅ Quick login successful (test mode)');
    router.push('/');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50 p-4">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Student Management System</h1>
          <p className="text-gray-600">Login to continue</p>
          <div className="mt-2 text-sm text-gray-500">
            <code className="bg-gray-100 px-2 py-1 rounded">Endpoint: POST http://localhost:8000/login</code>
          </div>
        </div>

        {/* Connection Tests */}
        <div className="mb-6 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={testConnection}
              className="py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
            >
              Test Connection
            </button>
            <button
              onClick={testLoginDirectly}
              className="py-2 bg-green-500 text-white rounded hover:bg-green-600 transition"
            >
              Test Login API
            </button>
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={createTestUser}
              disabled={loading}
              className="py-2 bg-purple-500 text-white rounded hover:bg-purple-600 transition disabled:opacity-50"
            >
              Create Test User
            </button>
            <button
              onClick={quickTestLogin}
              className="py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 transition"
            >
              Quick Test Login
            </button>
          </div>
        </div>

        {/* Login Form */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Login Form</h2>
          
          <form onSubmit={handleSubmit}>
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                  placeholder="admin@example.com"
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
                  placeholder="admin123"
                  required
                  disabled={loading}
                />
              </div>
              
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-red-800">Login Error</p>
                      <p className="mt-1 text-sm text-red-600">{error}</p>
                    </div>
                  </div>
                </div>
              )}
              
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Logging in...
                  </span>
                ) : (
                  'Login to System'
                )}
              </button>
            </div>
          </form>
          
          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="font-medium text-gray-800 mb-2">Test Credentials:</p>
              <div className="space-y-1 text-sm">
                <p><span className="font-medium">Email:</span> <code className="bg-gray-100 px-2 py-1 rounded">admin@example.com</code></p>
                <p><span className="font-medium">Password:</span> <code className="bg-gray-100 px-2 py-1 rounded">admin123</code></p>
              </div>
              <p className="text-xs text-gray-500 mt-3">
                ⚠️ If login fails, check browser Console (F12) for detailed errors
              </p>
            </div>
          </div>
        </div>

        {/* Debug Info */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Backend running on: <code className="bg-gray-100 px-2 py-1 rounded">http://localhost:8000</code></p>
          <p className="mt-1">Check <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">http://localhost:8000/docs</a> for API documentation</p>
        </div>
      </div>
    </div>
  );
}