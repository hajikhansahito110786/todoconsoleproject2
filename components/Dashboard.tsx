'use client'

import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/lib/api'
import { Users, BookOpen, Clock, CheckCircle } from 'lucide-react'

const StatCard = ({ 
  title, 
  value, 
  icon: Icon, 
  color 
}: { 
  title: string; 
  value: number; 
  icon: any; 
  color: string 
}) => (
  <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
    <div className="flex items-center space-x-3 mb-4">
      <div className={`p-2 ${color} rounded-lg`}>
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="text-gray-600 font-medium">{title}</h3>
    </div>
    <p className="text-3xl font-bold text-gray-800">{value}</p>
  </div>
)

export default function Dashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.getStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <p className="text-red-600">Failed to load dashboard data</p>
        <p className="text-red-500 text-sm mt-2">Make sure backend is running on localhost:8000</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        title="Total Students"
        value={stats?.total_students || 0}
        icon={Users}
        color="bg-blue-100 text-blue-600"
      />
      <StatCard
        title="Total Classes"
        value={stats?.total_classes || 0}
        icon={BookOpen}
        color="bg-purple-100 text-purple-600"
      />
      <StatCard
        title="Pending"
        value={stats?.by_status?.pending || 0}
        icon={Clock}
        color="bg-yellow-100 text-yellow-600"
      />
      <StatCard
        title="Completed"
        value={stats?.by_status?.completed || 0}
        icon={CheckCircle}
        color="bg-green-100 text-green-600"
      />
    </div>
  )
}