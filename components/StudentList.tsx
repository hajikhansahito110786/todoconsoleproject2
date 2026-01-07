'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { studentApi, Student } from '@/lib/api'
import { Trash2, Mail, User } from 'lucide-react'

export default function StudentList({ limit }: { limit?: number }) {
  const queryClient = useQueryClient()
  
  const { data: students, isLoading, error } = useQuery({
    queryKey: ['students'],
    queryFn: studentApi.getAll,
  })

  const deleteMutation = useMutation({
    mutationFn: studentApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(limit || 3)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl shadow p-4 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <p className="text-red-600">Failed to load students</p>
      </div>
    )
  }

  if (!students?.length) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8 text-center">
        <User className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-600 mb-2">No Students Yet</h3>
        <p className="text-gray-500">Add your first student to get started</p>
      </div>
    )
  }

  const displayedStudents = limit ? students.slice(0, limit) : students

  return (
    <div className="space-y-4">
      {displayedStudents.map((student: Student) => (
        <div key={student.id} className="bg-white rounded-xl shadow p-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-800">{student.name}</h3>
              <div className="flex items-center text-gray-500 text-sm mt-1">
                <Mail className="h-4 w-4 mr-1" />
                {student.email || 'No email'}
              </div>
            </div>
          </div>
          <button
            onClick={() => {
              if (confirm(`Delete student "${student.name}"?`)) {
                deleteMutation.mutate(student.id)
              }
            }}
            disabled={deleteMutation.isPending}
            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
          >
            <Trash2 className="h-5 w-5" />
          </button>
        </div>
      ))}
    </div>
  )
}