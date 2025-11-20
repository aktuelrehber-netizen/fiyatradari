'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { healthAPI } from '@/utils/api-client'
import { CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react'

interface ServiceStatus {
  status: string
  uptime?: string
  last_run?: string
}

export default function HealthPage() {
  const [services, setServices] = useState<Record<string, ServiceStatus>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadHealth()
  }, [])

  const loadHealth = async () => {
    try {
      setError('')
      const data = await healthAPI.services()
      setServices(data.services || {})
    } catch (err) {
      setError('Sistem durumu yüklenemedi')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-600" />
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-600" />
      default:
        return <AlertCircle className="h-5 w-5 text-gray-600" />
    }
  }

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      healthy: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      unhealthy: 'bg-red-100 text-red-800',
      unknown: 'bg-gray-100 text-gray-800',
      completed: 'bg-green-100 text-green-800',
      running: 'bg-blue-100 text-blue-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-gray-100 text-gray-800',
    }

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status] || colors.unknown}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  // Calculate stats
  const healthyCount = Object.values(services).filter(s => s.status === 'healthy').length
  const warningCount = Object.values(services).filter(s => s.status === 'warning').length
  const unhealthyCount = Object.values(services).filter(s => s.status === 'unhealthy').length
  const totalServices = Object.keys(services).length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sistem Sağlığı</h1>
          <p className="text-gray-500 mt-1">
            Tüm servislerin durumunu izleyin
          </p>
        </div>
        <Button onClick={() => loadHealth()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Yenile
        </Button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
          <XCircle className="h-5 w-5" />
          {error}
        </div>
      )}

      {/* System Status Banner */}
      {totalServices > 0 && (
        <Card className={`
          ${healthyCount === totalServices ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-200' : ''}
          ${unhealthyCount > 0 ? 'bg-gradient-to-r from-red-50 to-rose-50 border-red-200' : ''}
          ${warningCount > 0 && unhealthyCount === 0 ? 'bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-200' : ''}
        `}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {healthyCount === totalServices ? (
                  <CheckCircle className="w-12 h-12 text-green-600" />
                ) : unhealthyCount > 0 ? (
                  <XCircle className="w-12 h-12 text-red-600" />
                ) : (
                  <AlertCircle className="w-12 h-12 text-yellow-600" />
                )}
                <div>
                  <h2 className="text-2xl font-bold">
                    {healthyCount === totalServices && 'Tüm Sistemler Çalışıyor'}
                    {unhealthyCount > 0 && 'Sistem Hatası Tespit Edildi'}
                    {warningCount > 0 && unhealthyCount === 0 && 'Sistem Uyarısı'}
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    {healthyCount} / {totalServices} servis sağlıklı
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">Son kontrol</div>
                <div className="text-sm font-medium">{new Date().toLocaleTimeString('tr-TR')}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {Object.entries(services).map(([name, service]) => {
          const isHealthy = service.status === 'healthy'
          const isWarning = service.status === 'warning'
          const isUnhealthy = service.status === 'unhealthy'
          
          return (
            <Card 
              key={name}
              className={`
                ${isHealthy ? 'border-green-200 bg-green-50/50' : ''}
                ${isWarning ? 'border-yellow-200 bg-yellow-50/50' : ''}
                ${isUnhealthy ? 'border-red-200 bg-red-50/50' : ''}
              `}
            >
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold capitalize text-lg">{name}</h3>
                  {getStatusIcon(service.status)}
                </div>
                <p className="text-sm text-gray-600">
                  {isHealthy && 'Çalışıyor'}
                  {isWarning && 'Uyarı var'}
                  {isUnhealthy && 'Hata var'}
                  {!isHealthy && !isWarning && !isUnhealthy && 'Bilinmiyor'}
                </p>
                {service.uptime && (
                  <p className="text-xs text-gray-500 mt-2">
                    Uptime: {service.uptime}
                  </p>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Info Card */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <CheckCircle className="w-10 h-10 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-2">Sistem İzleme</h3>
              <p className="text-sm text-gray-600 mb-4">
                Tüm servisler otomatik olarak izlenmektedir. Herhangi bir sorun tespit edildiğinde
                ilgili servis kartı renk değiştirecektir.
              </p>
              <div className="flex gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>Sağlıklı - Sorunsuz çalışıyor</span>
                </div>
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-yellow-600" />
                  <span>Uyarı - Dikkat gerekiyor</span>
                </div>
                <div className="flex items-center gap-2">
                  <XCircle className="w-4 h-4 text-red-600" />
                  <span>Sorunlu - Hata var</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
