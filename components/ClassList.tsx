'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { classApi, StudentClass } from '@/lib/api'
import { Trash2, Book, CheckCircle, Clock, AlertCircle } from 'lucide-react'

const StatusBadge = ({ status }: { status: string }) => {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    'in-progress': 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
  }
  
  const icons: Record<string, any> = {
    pending: Clock,
    'in-progress': AlertCircle,
    completed: CheckCircle,
  }
  
  const Icon = icons[status] || Book
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
      <Icon className="h-3 w-3" />
      {status}
    </span>
  )
}

export default function ClassList({ limit }: { limit?: number }) {
  const queryClient = useQueryClient()
  
  const { data: classes, isLoading, error } = useQuery({
    queryKey: ['classes'],
    queryFn: classApi.getAll,
  })

  const deleteMutation = useMutation({
    mutationFn: classApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['classes'] })
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
        <p className="text-red-600">Failed to load classes</p>
      </div>
    )
  }

  if (!classes?.length) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8 text-center">
        <Book className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-600 mb-2">No Classes Yet</h3>
        <p className="text-gray-500">Add your first class to get started</p>
      </div>
    )
  }

  const displayedClasses = limit ? classes.slice(0, limit) : classes

  return (
    <div className="space-y-4">
      {displayedClasses.map((cls: StudentClass) => (
        <div key={cls.id} className="bg-white rounded-xl shadow p-4 flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-800">
                {cls.class_name} <span className="text-gray-500">({cls.class_code})</span>
              </h3>
              <StatusBadge status={cls.status} />
            </div>
            <p className="text-gray-600 text-sm">Semester: {cls.semester}</p>
            <p className="text-gray-600 text-sm">Priority: <span className="font-medium">{cls.priority}</span></p>
            {cls.description && (
              <p className="text-gray-500 text-sm mt-1">{cls.description}</p>
            )}
          </div>
          <button
            onClick={() => {
              if (confirm(`Delete class "${cls.class_name}"?`)) {
                deleteMutation.mutate(cls.id)
              }
            }}
            disabled={deleteMutation.isPending}
            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 ml-4"
          >
            <Trash2 className="h-5 w-5" />
          </button>
        </div>
      ))}
    </div>
  )
}