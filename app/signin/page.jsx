"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Define available users
const AVAILABLE_USERS = [
  { email: 'email@email.com', password: 'password123', label: 'User 1' },
  { email: 'admin@example.com', password: 'admin123', label: 'Admin User' }
];

export default function SignInPage() {
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [availableUsers, setAvailableUsers] = useState(AVAILABLE_USERS);
  const router = useRouter();

  // Fetch actual users from backend on mount
  useEffect(() => {
    fetchAvailableUsers();
  }, []);

  const fetchAvailableUsers = async () => {
    try {
      const response = await fetch('http://localhost:8000/debug/users');
      if (response.ok) {
        const data = await response.json();
        console.log('Available users from backend:', data.users);
        
        // You might want to map these to known passwords or show without passwords
        const users = data.users.map((user: any, index: number) => ({
          email: user.email,
          password: index === 0 ? 'password123' : 'admin123', // Default passwords
          label: user.email === 'admin@example.com' ? 'Admin' : `User ${user.id}`
        }));
        
        setAvailableUsers(users);
      }
    } catch (err) {
      console.error('Failed to fetch users:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      console.log(`Attempting login: ${email}`);
      
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
      
      if (response.ok) {
        const data = await response.json();
        console.log('Login successful:', data);
        
        // Store session token
        localStorage.setItem('session_token', data.session_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Redirect to home page
        router.push('/');
        router.refresh();
        
        alert(`✅ Login successful as ${data.user.email}!`);
      } else {
        const errorText = await response.text();
        console.error('Login failed:', errorText);
        
        try {
          const errorData = JSON.parse(errorText);
          setError(`Error: ${errorData.detail || 'Login failed'}`);
        } catch {
          setError(`Login failed with status ${response.status}: ${errorText}`);
        }
      }
    } catch (err: any) {
      console.error('Network error:', err);
      setError(`Cannot connect to server: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Quick login with selected user
  const quickLogin = (userEmail: string, userPassword: string) => {
    setEmail(userEmail);
    setPassword(userPassword);
    
    // Auto-submit after short delay
    setTimeout(() => {
      const form = document.querySelector('form');
      if (form) {
        const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
        form.dispatchEvent(submitEvent);
      }
    }, 100);
  };

  // Test all users
  const testAllUsers = async () => {
    setLoading(true);
    const results = [];
    
    for (const user of availableUsers) {
      try {
        console.log(`Testing login for: ${user.email}`);
        
        const response = await fetch('http://localhost:8000/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: user.email,
            password: user.password,
          }),
        });
        
        const result = {
          email: user.email,
          status: response.status,
          success: response.ok,
          message: response.ok ? '✅ Success' : `❌ Failed (${response.status})`
        };
        
        results.push(result);
        
        if (response.ok) {
          const data = await response.json();
          console.log(`✅ ${user.email} can login! Session: ${data.session_token}`);
        }
      } catch (err) {
        results.push({
          email: user.email,
          status: 0,
          success: false,
          message: `❌ Error: ${err instanceof Error ? err.message : 'Unknown'}`
        });
      }
      
      // Small delay between requests
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    setLoading(false);
    
    // Show results
    const resultText = results.map(r => 
      `${r.message} - ${r.email}`
    ).join('\n');
    
    alert(`Login Test Results:\n\n${resultText}`);
  };

  // Create test user if needed
  const createTestUser = async (userEmail: string, userPassword: string) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/register', {
        method: 'POST',
        headers: { 'Content-Type: 'application/json' },
        body: JSON.stringify({
          email: userEmail,
          password: userPassword,
        }),
      });

      if (response.ok) {
        alert(`✅ User ${userEmail} created successfully!`);
        fetchAvailableUsers(); // Refresh list
      } else {
        const errorData = await response.json();
        alert(`ℹ️ ${errorData.detail || 'User may already exist'}`);
      }
    } catch (err: any) {
      alert(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50 p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Student Management System</h1>
          <p className="text-gray-600">Login with any available user account</p>
          <div className="mt-2 text-sm text-gray-500">
            <code className="bg-gray-100 px-2 py-1 rounded">2 users available in database</code>
          </div>
        </div>

        {/* Connection & Test Buttons */}
        <div className="mb-6 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={() => testAllUsers()}
              disabled={loading}
              className="py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition disabled:opacity-50"
            >
              Test All Users
            </button>
            <button
              onClick={() => createTestUser('newuser@example.com', 'password123')}
              disabled={loading}
              className="py-2 bg-green-500 text-white rounded hover:bg-green-600 transition disabled:opacity-50"
            >
              Create New User
            </button>
            <button
              onClick={() => router.push('/')}
              className="py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition"
            >
              Skip to Dashboard
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Column - Quick Login Buttons */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Quick Login</h2>
              <p className="text-sm text-gray-600 mb-4">Click any user to login instantly:</p>
              
              <div className="space-y-3">
                {availableUsers.map((user, index) => (
                  <button
                    key={index}
                    onClick={() => quickLogin(user.email, user.password)}
                    disabled={loading}
                    className="w-full py-3 px-4 bg-gradient-to-r from-gray-100 to-gray-50 border border-gray-200 text-gray-800 font-medium rounded-lg hover:from-gray-200 hover:to-gray-100 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition text-left"
                  >
                    <div className="flex items-center">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                        <span className="text-blue-600 font-bold">{index + 1}</span>
                      </div>
                      <div>
                        <p className="font-medium">{user.label}</p>
                        <p className="text-sm text-gray-500 truncate">{user.email}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
              
              <div className="mt-6 pt-6 border-t border-gray-200">
                <p className="text-sm text-gray-600 mb-3">Don't know passwords?</p>
                <button
                  onClick={testAllUsers}
                  disabled={loading}
                  className="w-full py-2 bg-yellow-500 text-white text-sm rounded hover:bg-yellow-600 transition disabled:opacity-50"
                >
                  Auto-test All Passwords
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - Login Form */}
          <div className="md:col-span-2">
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
                      placeholder="Enter your email"
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
                      `Login as ${email}`
                    )}
                  </button>
                </div>
              </form>
              
              <div className="mt-8 pt-6 border-t border-gray-200">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="font-medium text-gray-800 mb-2">Available Users:</p>
                  <div className="space-y-2 text-sm">
                    {availableUsers.map((user, index) => (
                      <div key={index} className="flex justify-between items-center">
                        <div>
                          <span className="font-medium">{user.label}:</span>
                          <code className="bg-gray-100 px-2 py-1 rounded ml-2">{user.email}</code>
                        </div>
                        <button
                          onClick={() => {
                            setEmail(user.email);
                            setPassword(user.password);
                          }}
                          className="text-blue-600 hover:text-blue-800 text-xs"
                        >
                          Fill
                        </button>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-3">
                    💡 Try different users by clicking "Quick Login" buttons or changing the email above
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Debug Info */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Backend: <code className="bg-gray-100 px-2 py-1 rounded">http://localhost:8000</code></p>
          <p className="mt-1">
            API Docs: <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">http://localhost:8000/docs</a> | 
            Users Endpoint: <a href="http://localhost:8000/debug/users" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">/debug/users</a>
          </p>
        </div>
      </div>
    </div>
  );
}