'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '@/components/layout/sidebar'
import { authAPI } from '@/utils/api-client'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token')
      
      if (!token) {
        router.push('/login')
        return
      }

      try {
        await authAPI.getCurrentUser()
        setLoading(false)
      } catch (error) {
        localStorage.removeItem('token')
        router.push('/login')
      }
    }

    checkAuth()
  }, [router])

  if (loading) {
    return (
      <div className="flex h-full min-h-screen items-center justify-center overflow-auto">
        <div className="text-center">
          <div className="h-32 w-32 animate-spin rounded-full border-b-2 border-t-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <div className="container mx-auto p-6">
          {children}
        </div>
      </main>
    </div>
  )
}
