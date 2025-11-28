'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Activity, 
  CheckCircle2, 
  Clock, 
  Play, 
  RefreshCw,
  Server,
  Zap,
  AlertCircle
} from 'lucide-react'
import { apiClient } from '@/utils/api-client'

interface CeleryStatus {
  workers_online: number
  active_tasks: Record<string, any[]>
  registered_tasks: Record<string, string[]>
  stats: Record<string, any>
}

interface ScheduledTask {
  name: string
  task: string
  schedule: string
  options: Record<string, any>
}

interface RecentTask {
  task_id: string
  status: string
  name: string | null
  ready: boolean
  successful: boolean | null
  result?: any
  error?: string
  timestamp?: string
  date_done?: string
}

export default function MonitoringPage() {
  const [celeryStatus, setCeleryStatus] = useState<CeleryStatus | null>(null)
  const [scheduledTasks, setScheduledTasks] = useState<ScheduledTask[]>([])
  const [recentTasks, setRecentTasks] = useState<RecentTask[]>([])
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState<string | null>(null)

  useEffect(() => {
    loadMonitoringData()
    // Auto-refresh her 2 saniyede
    const interval = setInterval(loadMonitoringData, 2000)
    return () => clearInterval(interval)
  }, [])

  const loadMonitoringData = async () => {
    try {
      const [statusData, scheduledData, recentData] = await Promise.all([
        apiClient.get('/monitoring/celery/status'),
        apiClient.get('/monitoring/celery/scheduled'),
        apiClient.get('/monitoring/celery/recent-tasks?limit=20')
      ])
      
      setCeleryStatus(statusData.data)
      setScheduledTasks(scheduledData.data.tasks || [])
      setRecentTasks(recentData.data.tasks || [])
      setLoading(false)
    } catch (error) {
      console.error('Error loading monitoring data:', error)
      setLoading(false)
    }
  }

  const triggerTask = async (taskName: string) => {
    try {
      setTriggering(taskName)
      await apiClient.post(`/monitoring/celery/tasks/${taskName}/trigger`)
      alert(`Task "${taskName}" tetiklendi!`)
      setTimeout(loadMonitoringData, 2000)
    } catch (error: any) {
      alert('Hata: ' + (error.response?.data?.detail || error.message))
    } finally {
      setTriggering(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    )
  }

  const activeTasksCount = Object.values(celeryStatus?.active_tasks || {}).flat().length

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Sistem Monitoring</h1>
        <p className="text-gray-600 mt-2">Celery background task'ları ve worker durumu</p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Workers Online
            </CardTitle>
            <Server className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {celeryStatus?.workers_online || 0}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Aktif worker sayısı
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Aktif Task'lar
            </CardTitle>
            <Activity className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {activeTasksCount}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Şu anda çalışan
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Zamanlanmış
            </CardTitle>
            <Clock className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {scheduledTasks.length}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Otomatik task
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Durum
            </CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {celeryStatus?.workers_online ? 'Aktif' : 'Pasif'}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Sistem durumu
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Scheduled Tasks */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Zamanlanmış Task'lar
            </CardTitle>
            <CardDescription>
              Celery Beat tarafından otomatik çalışan task'lar
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {scheduledTasks.map((task) => (
                <div 
                  key={task.name}
                  className="flex items-start justify-between p-4 border rounded-lg bg-gray-50"
                >
                  <div className="flex-1">
                    <div className="font-medium text-sm">{task.name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {task.task}
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline" className="text-xs">
                        <Clock className="h-3 w-3 mr-1" />
                        {task.schedule}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Active Tasks */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Aktif Task'lar
            </CardTitle>
            <CardDescription>
              Şu anda çalışmakta olan background task'lar
            </CardDescription>
          </CardHeader>
          <CardContent>
            {activeTasksCount === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <AlertCircle className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                <p>Şu anda çalışan task yok</p>
              </div>
            ) : (
              <div className="space-y-2">
                {Object.entries(celeryStatus?.active_tasks || {}).map(([worker, tasks]) => (
                  <div key={worker}>
                    <div className="text-xs text-gray-500 mb-2">{worker}</div>
                    {tasks.map((task: any, idx: number) => (
                      <div key={idx} className="flex items-center gap-2 p-2 bg-blue-50 rounded text-sm">
                        <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                        <span className="flex-1">{task.name}</span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Manuel Triggers */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Manuel Task Tetikleme
          </CardTitle>
          <CardDescription>
            Debug ve test için task'ları manuel olarak çalıştırabilirsiniz
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border rounded-lg p-4">
              <h3 className="font-medium mb-2">Kategori Kontrolü</h3>
              <p className="text-sm text-gray-600 mb-4">
                Tüm kategorileri kontrol eder ve güncellenecekleri tespit eder
              </p>
              <Button
                onClick={() => triggerTask('check_categories')}
                disabled={triggering === 'check_categories'}
                className="w-full"
              >
                {triggering === 'check_categories' ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Çalıştırılıyor...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Kategori Kontrolü Başlat
                  </>
                )}
              </Button>
            </div>

            <div className="border rounded-lg p-4">
              <h3 className="font-medium mb-2">İstatistik Güncelleme</h3>
              <p className="text-sm text-gray-600 mb-4">
                Sistem istatistiklerini yeniden hesaplar ve günceller
              </p>
              <Button
                onClick={() => triggerTask('update_statistics')}
                disabled={triggering === 'update_statistics'}
                className="w-full"
                variant="outline"
              >
                {triggering === 'update_statistics' ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Çalıştırılıyor...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    İstatistik Güncelle
                  </>
                )}
              </Button>
            </div>

            <div className="border rounded-lg p-4">
              <h3 className="font-medium mb-2">Deal Temizliği</h3>
              <p className="text-sm text-gray-600 mb-4">
                30 günden eski ve pasif deal'leri siler
              </p>
              <Button
                onClick={() => triggerTask('cleanup_deals')}
                disabled={triggering === 'cleanup_deals'}
                className="w-full"
                variant="outline"
              >
                {triggering === 'cleanup_deals' ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Çalıştırılıyor...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Eski Deal'leri Temizle
                  </>
                )}
              </Button>
            </div>

            <div className="border rounded-lg p-4">
              <h3 className="font-medium mb-2">Deal Fiyat Kontrolü</h3>
              <p className="text-sm text-gray-600 mb-4">
                Aktif deal'lerin fiyatlarını kontrol eder
              </p>
              <Button
                onClick={() => triggerTask('check_deal_prices')}
                disabled={triggering === 'check_deal_prices'}
                className="w-full"
                variant="outline"
              >
                {triggering === 'check_deal_prices' ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Çalıştırılıyor...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Deal Fiyatları Kontrol Et
                  </>
                )}
              </Button>
            </div>

            <div className="border rounded-lg p-4 bg-blue-50">
              <h3 className="font-medium mb-2">Toplu Ürün Güncelleme</h3>
              <p className="text-sm text-gray-600 mb-4">
                Son 2 saat içinde güncellenmemiş ürünlerin fiyat, stok, rating bilgilerini günceller (max 500 ürün/çalışma)
              </p>
              <Button
                onClick={() => triggerTask('update_product_prices_batch')}
                disabled={triggering === 'update_product_prices_batch'}
                className="w-full"
                variant="outline"
              >
                {triggering === 'update_product_prices_batch' ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Çalıştırılıyor...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Ürün Fiyatlarını Güncelle (Batch)
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Tasks History */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Son Task'lar
          </CardTitle>
          <CardDescription>
            Son çalışan task'ların durumu ve sonuçları (son 20)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left p-2 w-32">Durum</th>
                  <th className="text-left p-2 w-40">Task</th>
                  <th className="text-left p-2 w-48">Tarih/Saat</th>
                  <th className="text-left p-2 w-32">Task ID</th>
                  <th className="text-left p-2">Detaylar</th>
                </tr>
              </thead>
              <tbody>
                {recentTasks.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-gray-500">
                      <AlertCircle className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                      <p>Henüz task kaydı yok</p>
                    </td>
                  </tr>
                ) : (
                  recentTasks.map((task) => {
                    // Task adını düzenle
                    const getTaskName = (name: string | null) => {
                      if (!name) return 'Unknown'
                      const parts = name.split('.')
                      const taskName = parts[parts.length - 1]
                      
                      // Türkçe isimlere çevir
                      const taskNames: Record<string, string> = {
                        'check_categories_for_update': 'Kategori Kontrolü',
                        'update_statistics': 'İstatistik Güncelleme',
                        'cleanup_old_deals': 'Deal Temizliği',
                        'check_deal_prices': 'Deal Fiyat Kontrolü',
                        'fetch_category_products_async': 'Ürün Çekme',
                        'update_product_prices_batch': 'Toplu Ürün Güncelleme'
                      }
                      
                      return taskNames[taskName] || taskName
                    }

                    // Tarih formatla (UTC'den İstanbul saatine çevir)
                    const formatDate = (timestamp: string | undefined) => {
                      if (!timestamp) return '-'
                      try {
                        const date = new Date(timestamp)
                        return date.toLocaleString('tr-TR', {
                          timeZone: 'Europe/Istanbul',
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit'
                        })
                      } catch {
                        return '-'
                      }
                    }

                    return (
                      <tr key={task.task_id} className="border-b hover:bg-gray-50">
                        <td className="p-2">
                          {task.status === 'SUCCESS' && (
                            <Badge className="bg-green-500">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              Başarılı
                            </Badge>
                          )}
                          {task.status === 'FAILURE' && (
                            <Badge variant="destructive">
                              <AlertCircle className="h-3 w-3 mr-1" />
                              Hata
                            </Badge>
                          )}
                          {task.status === 'PENDING' && (
                            <Badge variant="outline">
                              <Clock className="h-3 w-3 mr-1" />
                              Bekliyor
                            </Badge>
                          )}
                          {task.status === 'STARTED' && (
                            <Badge className="bg-blue-500">
                              <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                              Çalışıyor
                            </Badge>
                          )}
                        </td>
                        <td className="p-2">
                          <div className="text-xs font-medium text-gray-700">
                            {getTaskName(task.name)}
                          </div>
                        </td>
                        <td className="p-2">
                          <div className="text-xs text-gray-600">
                            {formatDate(task.timestamp || task.date_done)}
                          </div>
                        </td>
                        <td className="p-2">
                          <code className="text-xs bg-gray-100 px-1 rounded">
                            {task.task_id.substring(0, 8)}...
                          </code>
                        </td>
                        <td className="p-2">
                          {task.successful && task.result && (
                            <div className="text-xs text-green-600">
                              {typeof task.result === 'object' ? (
                                <div className="space-y-1">
                                  {/* Kategori Kontrolü */}
                                  {task.result.checked_categories !== undefined && (
                                    <div>
                                      <span className="font-semibold">{task.result.checked_categories}</span> kategori kontrol edildi
                                      {task.result.started_tasks !== undefined && (
                                        <span className="text-blue-600"> → {task.result.started_tasks} task başlatıldı</span>
                                      )}
                                    </div>
                                  )}
                                  
                                  {/* Ürün Çekme */}
                                  {task.result.category_name && (
                                    <div className="border-l-2 border-green-500 pl-2">
                                      <div className="font-semibold text-gray-700">{task.result.category_name}</div>
                                      {task.result.products_created !== undefined && (
                                        <div>🆕 <span className="font-semibold">{task.result.products_created}</span> ürün eklendi</div>
                                      )}
                                      {task.result.products_updated !== undefined && (
                                        <div>🔄 <span className="font-semibold">{task.result.products_updated}</span> ürün güncellendi</div>
                                      )}
                                      {task.result.deals_created !== undefined && task.result.deals_created > 0 && (
                                        <div className="text-orange-600">🎉 <span className="font-semibold">{task.result.deals_created}</span> deal oluşturuldu</div>
                                      )}
                                      {task.result.deals_updated !== undefined && task.result.deals_updated > 0 && (
                                        <div className="text-orange-600">📝 <span className="font-semibold">{task.result.deals_updated}</span> deal güncellendi</div>
                                      )}
                                      {task.result.total_found !== undefined && (
                                        <div className="text-gray-500">📊 {task.result.total_found} toplam ürün bulundu</div>
                                      )}
                                      {task.result.duration_seconds !== undefined && (
                                        <div className="text-gray-500">⏱️ {task.result.duration_seconds.toFixed(1)}s</div>
                                      )}
                                    </div>
                                  )}
                                  
                                  {/* İstatistikler */}
                                  {task.result.total_products !== undefined && (
                                    <div>
                                      <span className="font-semibold">{task.result.total_products}</span> toplam ürün
                                      {task.result.active_deals !== undefined && (
                                        <span> • <span className="font-semibold">{task.result.active_deals}</span> aktif deal</span>
                                      )}
                                    </div>
                                  )}
                                  
                                  {/* Deal Temizliği */}
                                  {task.result.deleted_deals !== undefined && (
                                    <div>🗑️ <span className="font-semibold">{task.result.deleted_deals}</span> eski deal temizlendi</div>
                                  )}
                                  
                                  {/* Deal Fiyat Kontrolü */}
                                  {task.result.checked_deals !== undefined && (
                                    <div>
                                      <span className="font-semibold">{task.result.checked_deals}</span> deal kontrol edildi
                                      {task.result.deactivated_deals !== undefined && (
                                        <span> • <span className="font-semibold text-red-600">{task.result.deactivated_deals}</span> devre dışı</span>
                                      )}
                                    </div>
                                  )}
                                  
                                  {/* Toplu Ürün Güncelleme */}
                                  {task.result.updated_products !== undefined && (
                                    <div className="border-l-2 border-blue-500 pl-2">
                                      <div className="font-semibold text-blue-700">Toplu Ürün Güncelleme</div>
                                      <div>✅ <span className="font-semibold">{task.result.updated_products}</span> / {task.result.total_products} ürün güncellendi</div>
                                      {task.result.deals_created > 0 && (
                                        <div className="text-orange-600">🎉 <span className="font-semibold">{task.result.deals_created}</span> yeni deal</div>
                                      )}
                                      {task.result.deals_updated > 0 && (
                                        <div className="text-orange-600">📝 <span className="font-semibold">{task.result.deals_updated}</span> deal güncellendi</div>
                                      )}
                                      {task.result.failed_products > 0 && (
                                        <div className="text-red-600">❌ <span className="font-semibold">{task.result.failed_products}</span> başarısız</div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <span>✓ Başarılı</span>
                              )}
                            </div>
                          )}
                          {task.status === 'FAILURE' && task.error && (
                            <div className="text-xs text-red-600 max-w-md truncate">
                              ✗ {task.error}
                            </div>
                          )}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Auto Refresh Info */}
      <div className="mt-6 text-center text-sm text-gray-500">
        <RefreshCw className="h-4 w-4 inline mr-1" />
        Sayfa otomatik olarak her 2 saniyede yenileniyor
      </div>
    </div>
  )
}
