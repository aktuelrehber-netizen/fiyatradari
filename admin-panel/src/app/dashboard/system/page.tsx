'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { 
  Activity, Server, CheckCircle, XCircle, AlertTriangle, 
  Play, Pause, RefreshCw, Loader2, TrendingUp, Database,
  Clock, Zap, BarChart3, Settings, ExternalLink
} from 'lucide-react'
import { workersAPI, healthAPI } from '@/utils/api-client'
import { useToast } from '@/hooks/use-toast'

interface SystemHealth {
  status: 'healthy' | 'warning' | 'error'
  services: Record<string, { status: string; uptime?: string }>
}

interface WorkerControl {
  scheduler_enabled: boolean
  jobs: Record<string, { enabled: boolean }>
}

interface Metrics {
  [key: string]: Array<{ value: number; labels?: string }>
}

export default function SystemDashboard() {
  const { toast } = useToast()
  
  // State
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [workerControl, setWorkerControl] = useState<WorkerControl | null>(null)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  // Load data from unified system API
  const loadData = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/system/overview')
      const data = await response.json()
      
      // Transform data for state
      setHealth({
        status: data.health.status,
        services: {
          database: { status: data.health.database },
          redis: { status: data.health.redis },
          workers: { status: data.health.workers_online > 0 ? 'healthy' : 'unhealthy' }
        }
      })
      
      // Get worker control status separately (if exists)
      try {
        const controlData = await workersAPI.getControlStatus()
        setWorkerControl(controlData)
      } catch {
        setWorkerControl(null)
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Failed to load system data:', error)
      setLoading(false)
    }
  }, [])

  // Load metrics
  const loadMetrics = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/metrics')
      const text = await response.text()
      const parsed = parsePrometheusMetrics(text)
      setMetrics(parsed)
    } catch (error) {
      console.error('Failed to load metrics:', error)
    }
  }, [])

  // Parse Prometheus metrics
  const parsePrometheusMetrics = (text: string): Metrics => {
    const lines = text.split('\n')
    const parsed: Metrics = {}

    lines.forEach(line => {
      if (line.startsWith('#') || !line.trim()) return
      
      const match = line.match(/^([a-zA-Z_][a-zA-Z0-9_:]*)\{?(.*?)\}?\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)/)
      if (match) {
        const [, name, labels, value] = match
        if (!parsed[name]) parsed[name] = []
        parsed[name].push({ labels: labels || '', value: parseFloat(value) })
      }
    })

    return parsed
  }

  // Initial load
  useEffect(() => {
    loadData()
    loadMetrics()

    // Refresh every 10 seconds
    const interval = setInterval(() => {
      loadMetrics()
    }, 10000)

    return () => clearInterval(interval)
  }, [loadData, loadMetrics])

  // Worker control actions
  const handleSchedulerToggle = async () => {
    if (!workerControl) return
    
    try {
      setActionLoading(true)
      
      if (workerControl.scheduler_enabled) {
        await workersAPI.pauseScheduler()
        toast({ title: '✅ Scheduler Durduruldu', description: 'Otomatik görevler artık çalışmayacak.' })
      } else {
        await workersAPI.resumeScheduler()
        toast({ title: '✅ Scheduler Başlatıldı', description: 'Otomatik görevler tekrar çalışacak.' })
      }
      
      await loadData()
    } catch (error) {
      toast({
        title: '❌ Hata',
        description: 'Scheduler durumu değiştirilemedi.',
        variant: 'destructive'
      })
    } finally {
      setActionLoading(false)
    }
  }

  const handleJobToggle = async (jobType: string) => {
    if (!workerControl) return
    
    try {
      setActionLoading(true)
      const currentStatus = workerControl.jobs[jobType]?.enabled
      
      if (currentStatus) {
        await workersAPI.disableJob(jobType)
        toast({ title: '⏸️ Job Kapatıldı', description: `${getJobDisplayName(jobType)} artık çalışmayacak.` })
      } else {
        await workersAPI.enableJob(jobType)
        toast({ title: '▶️ Job Açıldı', description: `${getJobDisplayName(jobType)} tekrar çalışacak.` })
      }
      
      await loadData()
    } catch (error) {
      toast({
        title: '❌ Hata',
        description: 'Job durumu değiştirilemedi.',
        variant: 'destructive'
      })
    } finally {
      setActionLoading(false)
    }
  }

  const getJobDisplayName = (jobType: string): string => {
    const names: Record<string, string> = {
      fetch_products: 'Ürün Çekme',
      check_prices: 'Fiyat Kontrol',
      send_telegram: 'Telegram'
    }
    return names[jobType] || jobType
  }

  // Calculate stats
  const healthyCount = health ? Object.values(health.services).filter(s => s.status === 'healthy').length : 0
  const totalServices = health ? Object.keys(health.services).length : 0
  const systemStatus = healthyCount === totalServices ? 'healthy' : healthyCount > 0 ? 'warning' : 'error'

  const totalProducts = metrics?.fiyatradari_products_total?.[0]?.value || 0
  const totalDeals = metrics?.fiyatradari_deals_total?.[0]?.value || 0
  const totalRequests = metrics?.fiyatradari_requests_total
    ? Math.round(metrics.fiyatradari_requests_total.reduce((sum: number, m: any) => sum + m.value, 0))
    : 0

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-12 h-12 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Server className="w-8 h-8 text-blue-600" />
            Sistem Yönetimi
          </h1>
          <p className="text-muted-foreground mt-1">
            Sistem sağlığı, worker kontrolü ve performans metrikleri
          </p>
        </div>
        <Button onClick={() => { loadData(); loadMetrics() }} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Yenile
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className={
          systemStatus === 'healthy' ? 'border-green-200 bg-green-50/50' :
          systemStatus === 'warning' ? 'border-yellow-200 bg-yellow-50/50' :
          'border-red-200 bg-red-50/50'
        }>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sistem Durumu</CardTitle>
            {systemStatus === 'healthy' ? (
              <CheckCircle className="h-5 w-5 text-green-600" />
            ) : systemStatus === 'warning' ? (
              <AlertTriangle className="h-5 w-5 text-yellow-600" />
            ) : (
              <XCircle className="h-5 w-5 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemStatus === 'healthy' ? '✅ Sağlıklı' : 
               systemStatus === 'warning' ? '⚠️ Uyarı' : '❌ Hata'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {healthyCount} / {totalServices} servis aktif
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Worker Durumu</CardTitle>
            <Activity className="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-2">
              {workerControl?.scheduler_enabled ? (
                <><span className="text-green-600">▶️ Aktif</span></>
              ) : (
                <><span className="text-gray-600">⏸️ Durduruldu</span></>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Scheduler durumu
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Aktif Ürünler</CardTitle>
            <Database className="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(totalProducts).toLocaleString('tr-TR')}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Veritabanında
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Aktif Fırsatlar</CardTitle>
            <Zap className="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {Math.round(totalDeals).toLocaleString('tr-TR')}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Şu anda
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="control" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="control">
            <Settings className="w-4 h-4 mr-2" />
            Kontrol
          </TabsTrigger>
          <TabsTrigger value="health">
            <Activity className="w-4 h-4 mr-2" />
            Sağlık
          </TabsTrigger>
          <TabsTrigger value="workers">
            <Server className="w-4 h-4 mr-2" />
            Worker'lar
          </TabsTrigger>
          <TabsTrigger value="metrics">
            <BarChart3 className="w-4 h-4 mr-2" />
            Metrikler
          </TabsTrigger>
        </TabsList>

        {/* CONTROL TAB */}
        <TabsContent value="control" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Scheduler Kontrolü
              </CardTitle>
              <CardDescription>
                Otomatik görevleri durdur veya başlat
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-4">
                  <Badge variant={workerControl?.scheduler_enabled ? "default" : "secondary"} className="px-4 py-2">
                    {workerControl?.scheduler_enabled ? (
                      <><Play className="w-4 h-4 mr-2" /> Çalışıyor</>
                    ) : (
                      <><Pause className="w-4 h-4 mr-2" /> Durduruldu</>
                    )}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {workerControl?.scheduler_enabled 
                      ? 'Tüm otomatik görevler çalışıyor' 
                      : 'Otomatik görevler durduruldu'}
                  </span>
                </div>
                <Button
                  onClick={handleSchedulerToggle}
                  disabled={actionLoading}
                  variant={workerControl?.scheduler_enabled ? "destructive" : "default"}
                  className={!workerControl?.scheduler_enabled ? 'bg-green-600 hover:bg-green-700' : ''}
                >
                  {actionLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : workerControl?.scheduler_enabled ? (
                    <Pause className="w-4 h-4 mr-2" />
                  ) : (
                    <Play className="w-4 h-4 mr-2" />
                  )}
                  {workerControl?.scheduler_enabled ? 'Durdur' : 'Başlat'}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Job Kontrolü
              </CardTitle>
              <CardDescription>
                Bireysel görevleri aç/kapat
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {workerControl?.jobs && Object.entries(workerControl.jobs).map(([jobType, job]) => (
                  <div
                    key={jobType}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      job.enabled
                        ? 'bg-green-50 border-green-200'
                        : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="font-semibold">{getJobDisplayName(jobType)}</div>
                      <Badge variant={job.enabled ? "default" : "secondary"}>
                        {job.enabled ? '✓ Aktif' : '✗ Kapalı'}
                      </Badge>
                    </div>
                    <Button
                      onClick={() => handleJobToggle(jobType)}
                      disabled={actionLoading}
                      variant={job.enabled ? "destructive" : "default"}
                      size="sm"
                      className={`w-full ${!job.enabled && 'bg-green-600 hover:bg-green-700'}`}
                    >
                      {actionLoading ? (
                        <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                      ) : job.enabled ? (
                        <Pause className="w-3 h-3 mr-2" />
                      ) : (
                        <Play className="w-3 h-3 mr-2" />
                      )}
                      {job.enabled ? 'Kapat' : 'Aç'}
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* HEALTH TAB */}
        <TabsContent value="health" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Servis Durumu
              </CardTitle>
              <CardDescription>
                Tüm servislerin sağlık durumu
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {health && Object.entries(health.services).map(([name, service]) => {
                  const isHealthy = service.status === 'healthy'
                  const isWarning = service.status === 'warning'
                  
                  return (
                    <div
                      key={name}
                      className={`p-4 rounded-lg border-2 ${
                        isHealthy ? 'bg-green-50 border-green-200' :
                        isWarning ? 'bg-yellow-50 border-yellow-200' :
                        'bg-red-50 border-red-200'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold capitalize">{name}</h3>
                        {isHealthy ? (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        ) : isWarning ? (
                          <AlertTriangle className="w-5 h-5 text-yellow-600" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-600" />
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {isHealthy && 'Çalışıyor'}
                        {isWarning && 'Uyarı var'}
                        {!isHealthy && !isWarning && 'Hata var'}
                      </p>
                      {service.uptime && (
                        <p className="text-xs text-muted-foreground mt-2">
                          Uptime: {service.uptime}
                        </p>
                      )}
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* WORKERS TAB */}
        <TabsContent value="workers" className="space-y-4">
          <Card className="overflow-hidden">
            <CardHeader className="bg-gradient-to-r from-pink-50 to-purple-50 border-b">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Server className="w-5 h-5" />
                    Celery Flower Monitor
                  </CardTitle>
                  <CardDescription>
                    Worker durumu, task geçmişi ve broker bilgileri
                  </CardDescription>
                </div>
                <Button
                  onClick={() => window.open('http://localhost:5555', '_blank')}
                  variant="outline"
                  size="sm"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Flower'ı Aç
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="relative w-full" style={{ height: 'calc(100vh - 360px)', minHeight: '600px' }}>
                <iframe
                  src="http://localhost:5555"
                  className="w-full h-full border-0"
                  title="Flower Dashboard"
                  sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* METRICS TAB */}
        <TabsContent value="metrics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Toplam İstekler</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{totalRequests.toLocaleString('tr-TR')}</div>
                <p className="text-xs text-muted-foreground">Tüm endpoint'ler</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Yanıt Süresi</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {metrics?.fiyatradari_request_duration_seconds_sum
                    ? Math.round((metrics.fiyatradari_request_duration_seconds_sum[0]?.value || 0) * 1000)
                    : '0'}ms
                </div>
                <p className="text-xs text-muted-foreground">Ortalama gecikme</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">İşlenen Task</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {metrics?.fiyatradari_worker_tasks_total?.[0]?.value || '0'}
                </div>
                <p className="text-xs text-muted-foreground">Celery task'ları</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Harici Monitoring</CardTitle>
              <CardDescription>Detaylı metrikler için Grafana ve Prometheus</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <a
                href="http://localhost:3002"
                target="_blank"
                rel="noopener noreferrer"
                className="block p-4 border-2 rounded-lg hover:bg-gray-50 transition hover:border-blue-300"
              >
                <div className="flex items-center space-x-4">
                  <BarChart3 className="h-8 w-8 text-blue-600" />
                  <div>
                    <h3 className="font-semibold">Grafana Dashboard</h3>
                    <p className="text-sm text-muted-foreground">Görsel metrik ve grafik arayüzü</p>
                  </div>
                  <ExternalLink className="h-5 w-5 text-muted-foreground ml-auto" />
                </div>
              </a>

              <a
                href="http://localhost:9090"
                target="_blank"
                rel="noopener noreferrer"
                className="block p-4 border-2 rounded-lg hover:bg-gray-50 transition hover:border-orange-300"
              >
                <div className="flex items-center space-x-4">
                  <Activity className="h-8 w-8 text-orange-600" />
                  <div>
                    <h3 className="font-semibold">Prometheus</h3>
                    <p className="text-sm text-muted-foreground">Ham metrikler ve sorgulama arayüzü</p>
                  </div>
                  <ExternalLink className="h-5 w-5 text-muted-foreground ml-auto" />
                </div>
              </a>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
