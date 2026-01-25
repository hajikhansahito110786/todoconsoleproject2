// pages/index.js
import Head from 'next/head';
import { useState, useEffect } from 'react';

export default function Home() {
  const [todos, setTodos] = useState([]);
  const [students, setStudents] = useState([]);
  const [newTodo, setNewTodo] = useState({ title: '', description: '', priority: 'medium', student_id: '' });
  const [newStudent, setNewStudent] = useState({ name: '', email: '' });
  const [chatMessage, setChatMessage] = useState('');
  const [chatResponse, setChatResponse] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginData, setLoginData] = useState({ email: '', password: '' });

  // Check session on component mount
  useEffect(() => {
    checkSession();
  }, []);

  const checkSession = async () => {
    try {
      const response = await fetch('http://localhost:8000/check-session');
      const data = await response.json();
      setIsLoggedIn(data.authenticated);
    } catch (error) {
      console.error('Error checking session:', error);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData),
      });
      const data = await response.json();
      if (data.success) {
        setIsLoggedIn(true);
        alert('Login successful!');
      } else {
        alert('Login failed: ' + data.message);
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login error: ' + error.message);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:8000/logout', {
        method: 'POST',
      });
      setIsLoggedIn(false);
      alert('Logged out successfully');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const fetchTodos = async () => {
    try {
      const response = await fetch('http://localhost:8000/todos/');
      const data = await response.json();
      setTodos(data);
    } catch (error) {
      console.error('Error fetching todos:', error);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await fetch('http://localhost:8000/students/');
      const data = await response.json();
      setStudents(data);
    } catch (error) {
      console.error('Error fetching students:', error);
    }
  };

  const addTodo = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/todos/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTodo),
      });
      if (response.ok) {
        setNewTodo({ title: '', description: '', priority: 'medium', student_id: '' });
        fetchTodos(); // Refresh the list
      } else {
        alert('Failed to add todo');
      }
    } catch (error) {
      console.error('Error adding todo:', error);
    }
  };

  const addStudent = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/students/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newStudent),
      });
      if (response.ok) {
        setNewStudent({ name: '', email: '' });
        fetchStudents(); // Refresh the list
      } else {
        alert('Failed to add student');
      }
    } catch (error) {
      console.error('Error adding student:', error);
    }
  };

  const sendMessage = async () => {
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: chatMessage }),
      });
      const data = await response.json();
      setChatResponse(data.response);
      setChatMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      setChatResponse('Error: ' + error.message);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <Head>
        <title>Student Management System</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="bg-gray-100 min-h-screen">
        <header className="bg-blue-600 text-white p-4">
          <h1 className="text-2xl font-bold">Student Management System</h1>
          {isLoggedIn ? (
            <button 
              onClick={handleLogout}
              className="mt-2 bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
            >
              Logout
            </button>
          ) : (
            <form onSubmit={handleLogin} className="mt-2 flex space-x-2">
              <input
                type="email"
                placeholder="Email"
                value={loginData.email}
                onChange={(e) => setLoginData({...loginData, email: e.target.value})}
                className="flex-grow p-2 border rounded text-black"
                required
              />
              <input
                type="password"
                placeholder="Password"
                value={loginData.password}
                onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                className="flex-grow p-2 border rounded text-black"
                required
              />
              <button 
                type="submit"
                className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
              >
                Login
              </button>
            </form>
          )}
        </header>

        {isLoggedIn ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4">
            {/* Todos Section */}
            <div className="bg-white p-4 rounded shadow">
              <h2 className="text-xl font-bold mb-4">Todos</h2>
              
              <form onSubmit={addTodo} className="mb-4 p-4 bg-gray-50 rounded">
                <h3 className="font-semibold mb-2">Add New Todo</h3>
                <input
                  type="text"
                  placeholder="Title"
                  value={newTodo.title}
                  onChange={(e) => setNewTodo({...newTodo, title: e.target.value})}
                  className="w-full p-2 border rounded mb-2 text-black"
                  required
                />
                <textarea
                  placeholder="Description"
                  value={newTodo.description}
                  onChange={(e) => setNewTodo({...newTodo, description: e.target.value})}
                  className="w-full p-2 border rounded mb-2 text-black"
                />
                <select
                  value={newTodo.priority}
                  onChange={(e) => setNewTodo({...newTodo, priority: e.target.value})}
                  className="w-full p-2 border rounded mb-2 text-black"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
                <select
                  value={newTodo.student_id}
                  onChange={(e) => setNewTodo({...newTodo, student_id: parseInt(e.target.value) || null})}
                  className="w-full p-2 border rounded mb-2 text-black"
                >
                  <option value="">Assign to...</option>
                  {students.map(student => (
                    <option key={student.id} value={student.id}>{student.name}</option>
                  ))}
                </select>
                <button 
                  type="submit"
                  className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                >
                  Add Todo
                </button>
              </form>
              
              <button 
                onClick={fetchTodos}
                className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded mb-4"
              >
                Refresh Todos
              </button>
              
              <div className="space-y-2">
                {todos.map(todo => (
                  <div key={todo.id} className="p-3 border rounded bg-gray-50">
                    <h4 className="font-bold">{todo.title}</h4>
                    <p>{todo.description}</p>
                    <div className="flex justify-between mt-2">
                      <span className={`px-2 py-1 rounded ${todo.priority === 'high' ? 'bg-red-200' : todo.priority === 'medium' ? 'bg-yellow-200' : 'bg-green-200'}`}>
                        {todo.priority}
                      </span>
                      <span>By: {todo.created_by}</span>
                    </div>
                    {todo.student_id && (
                      <p className="text-sm text-gray-600">
                        Assigned to: {students.find(s => s.id === todo.student_id)?.name}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
            
            {/* Students Section */}
            <div className="bg-white p-4 rounded shadow">
              <h2 className="text-xl font-bold mb-4">Students</h2>
              
              <form onSubmit={addStudent} className="mb-4 p-4 bg-gray-50 rounded">
                <h3 className="font-semibold mb-2">Add New Student</h3>
                <input
                  type="text"
                  placeholder="Name"
                  value={newStudent.name}
                  onChange={(e) => setNewStudent({...newStudent, name: e.target.value})}
                  className="w-full p-2 border rounded mb-2 text-black"
                  required
                />
                <input
                  type="email"
                  placeholder="Email"
                  value={newStudent.email}
                  onChange={(e) => setNewStudent({...newStudent, email: e.target.value})}
                  className="w-full p-2 border rounded mb-2 text-black"
                  required
                />
                <button 
                  type="submit"
                  className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                >
                  Add Student
                </button>
              </form>
              
              <button 
                onClick={fetchStudents}
                className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded mb-4"
              >
                Refresh Students
              </button>
              
              <div className="space-y-2">
                {students.map(student => (
                  <div key={student.id} className="p-3 border rounded bg-gray-50">
                    <h4 className="font-bold">{student.name}</h4>
                    <p>{student.email}</p>
                    <p className="text-sm text-gray-600">Added by: {student.created_by}</p>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Chatbot Section */}
            <div className="md:col-span-2 bg-white p-4 rounded shadow">
              <h2 className="text-xl font-bold mb-4">AI Assistant</h2>
              <div className="mb-4 p-4 bg-gray-100 rounded min-h-24">
                <p><strong>Bot:</strong> {chatResponse || 'Ask me anything about managing students and todos!'}</p>
              </div>
              <div className="flex space-x-2">
                <input
                  type="text"
                  placeholder="Ask the AI assistant..."
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  className="flex-grow p-2 border rounded text-black"
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                />
                <button 
                  onClick={sendMessage}
                  className="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-96">
            <h2 className="text-xl font-bold mb-4">Please log in to access the system</h2>
            <p>You need to authenticate to manage students and todos.</p>
          </div>
        )}
      </main>
    </div>
  );
}