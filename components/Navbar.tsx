import Link from 'next/link'
import { GraduationCap } from 'lucide-react'

export default function Navbar() {
  return (
    <nav className="bg-white shadow-lg border-b">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-2 rounded-lg">
              <GraduationCap className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800">Student Todo App</h1>
          </Link>
          
          <div className="flex space-x-6">
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
      </div>
    </nav>
  )
}