"use client";

import { useState } from 'react';
import Link from 'next/link';
import { GraduationCap, Menu, X } from 'lucide-react';

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className="bg-white shadow-lg border-b">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-2 rounded-lg">
              <GraduationCap className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-gray-800">Student Todo App</h1>
          </Link>
          
          <div className="hidden md:flex space-x-6">
            <Link href="/dashboard" className="text-gray-600 hover:text-blue-600 font-medium">
              Dashboard
            </Link>
            <Link href="/students" className="text-gray-600 hover:text-blue-600 font-medium">
              Students
            </Link>
            <Link href="/classes" className="text-gray-600 hover:text-blue-600 font-medium">
              Classes
            </Link>
          </div>

          <div className="md:hidden">
            {/* Mobile menu button */}
            <button 
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-600 hover:text-blue-600"
            >
              {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden bg-white border-t">
          <div className="container mx-auto px-4 py-4 flex flex-col space-y-4">
            <Link href="/dashboard" className="text-gray-600 hover:text-blue-600 font-medium">
              Dashboard
            </Link>
            <Link href="/students" className="text-gray-600 hover:text-blue-600 font-medium">
              Students
            </Link>
            <Link href="/classes" className="text-gray-600 hover:text-blue-600 font-medium">
              Classes
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}