// app/components/ChatInterface.tsx
'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, TrendingUp, Clock, AlertCircle } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

interface Suggestion {
  type: string;
  todo_id: number;
  title: string;
  message: string;
  priority: 'high' | 'medium' | 'low';
}

interface ChatResponse {
  response: string;
  suggestions: Suggestion[];
  context: {
    stats: any;
    user: string;
  };
  processing_time: number;
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m your AI Todo Assistant. How can I help you manage your tasks today?',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [stats, setStats] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message
    const newUserMessage: Message = {
      id: Date.now().toString(),
      content: userMessage,
      isUser: true,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      // Get user email from localStorage or auth context
      const userEmail = localStorage.getItem('userEmail') || 'guest@example.com';
      
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-user-email': userEmail,
        },
        body: JSON.stringify({
          message: userMessage,
        }),
      });

      const data: ChatResponse = await response.json();
      
      // Add bot response
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response,
        isUser: false,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, botMessage]);
      setSuggestions(data.suggestions);
      setStats(data.context.stats);
      
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (action: string) => {
    setInput(action);
    setTimeout(() => handleSend(), 100);
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high': return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'medium': return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'low': return <TrendingUp className="w-4 h-4 text-green-500" />;
      default: return <Sparkles className="w-4 h-4 text-blue-500" />;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header */}
      <div className="bg-white border-b p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Bot className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">AI Todo Assistant</h1>
              <p className="text-sm text-gray-500">Powered by Google Gemini</p>
            </div>
          </div>
          
          {stats && (
            <div className="hidden md:flex items-center space-x-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-800">{stats.total}</div>
                <div className="text-xs text-gray-500">Total Tasks</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats.completion_rate}%</div>
                <div className="text-xs text-gray-500">Done</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{stats.overdue}</div>
                <div className="text-xs text-gray-500">Overdue</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden max-w-4xl mx-auto w-full p-4">
        {/* Chat Messages */}
        <div className="h-[calc(100vh-280px)] overflow-y-auto space-y-4 p-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl p-4 ${
                  message.isUser
                    ? 'bg-blue-500 text-white rounded-br-none'
                    : 'bg-white border rounded-bl-none'
                }`}
              >
                <div className="flex items-center space-x-2 mb-2">
                  {message.isUser ? (
                    <User className="w-4 h-4" />
                  ) : (
                    <Bot className="w-4 h-4" />
                  )}
                  <span className="text-sm font-medium">
                    {message.isUser ? 'You' : 'AI Assistant'}
                  </span>
                  <span className="text-xs opacity-75">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border rounded-2xl rounded-bl-none p-4">
                <div className="flex items-center space-x-2">
                  <Bot className="w-4 h-4" />
                  <span className="text-sm font-medium">AI Assistant</span>
                </div>
                <div className="flex space-x-2 mt-2">
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce delay-150" />
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce delay-300" />
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div className="mt-4 p-4 bg-white rounded-xl border">
            <div className="flex items-center space-x-2 mb-3">
              <Sparkles className="w-5 h-5 text-purple-500" />
              <h3 className="font-semibold text-gray-800">AI Suggestions</h3>
            </div>
            <div className="space-y-2">
              {suggestions.map((suggestion) => (
                <div
                  key={suggestion.todo_id}
                  className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  {getPriorityIcon(suggestion.priority)}
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-800">{suggestion.title}</p>
                    <p className="text-sm text-gray-600">{suggestion.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="max-w-4xl mx-auto w-full px-4 pb-4">
        <div className="flex flex-wrap gap-2 mb-3">
          {[
            'Show my todos',
            'Add a new todo',
            'What\'s overdue?',
            'Show statistics',
            'Help me prioritize',
          ].map((action) => (
            <button
              key={action}
              onClick={() => handleQuickAction(action)}
              className="px-3 py-1.5 bg-white border rounded-full text-sm hover:bg-gray-50 transition-colors"
            >
              {action}
            </button>
          ))}
        </div>

        {/* Input Area */}
        <div className="bg-white border rounded-2xl p-2 shadow-sm">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask me anything about your todos..."
              className="flex-1 p-3 outline-none text-gray-800 placeholder-gray-400"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="p-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;